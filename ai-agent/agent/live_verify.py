"""Live deployment verification — prove a deployed site really works.

The deploy connectors used to report ``status: "live"`` as soon as the CLI exited
0 or a URL string appeared, sometimes with an empty URL. That is not evidence: a
DNS entry, a Vercel login wall, an empty project or a missing JS bundle all look
"deployed" from the outside.

This module is the single source of truth for "is it live?". It is deliberately
stdlib-only and offline-safe:
  1. poll the URL until it answers (deployments propagate for a few seconds),
  2. reject platform error/login pages,
  3. require a non-empty title and the app shell,
  4. fetch the hashed JS/CSS assets referenced by index.html,
  5. fetch every expected SPA route,
  6. optionally require a marker string and an API health endpoint.

Every check returns evidence (status codes, failures, timings), so a caller can
never mistake "unverified" for "live".
"""
from __future__ import annotations

import json
import queue
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional

USER_AGENT = "lumicorepro-factory/1.0 (+live-verify)"
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
ASSET_RE = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+\.(?:js|css)(?:\?[^"']*)?)["']""", re.IGNORECASE)
SHELL_RE = re.compile(r"""<div[^>]+id=["'](?:root|app)["']""", re.IGNORECASE)
# A POSIX shell on Windows (Git Bash/MSYS) rewrites a leading-slash argument such
# as /api/v1/health into <msys-root>/api/v1/health, and urljoin then reads the
# drive letter as a scheme. Nothing in this module may try to fetch such a value.
LOCAL_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\")

# Pages that mean "the request reached the platform, not the app".
_PLATFORM_ERROR_MARKERS = (
    "DEPLOYMENT_NOT_FOUND",
    "This deployment cannot be found",
    "The deployment could not be found",
    "Application error: a client-side exception has occurred",
    "404: NOT_FOUND",
)
_LOGIN_MARKERS = ("vercel.com/login", "sso-protection", "Authentication Required",
                  "Protected by Vercel Authentication", '"code":"UNAUTHENTICATED"')


class _Fetch:
    """One HTTP GET result with the fields verification cares about."""

    __slots__ = ("ok", "status", "url", "body", "error", "elapsed_ms")

    def __init__(self, ok: bool, status: int = 0, url: str = "", body: str = "",
                 error: str = "", elapsed_ms: int = 0):
        self.ok = ok
        self.status = status
        self.url = url
        self.body = body
        self.error = error
        self.elapsed_ms = elapsed_ms

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": self.ok, "status": self.status, "url": self.url}
        if self.error:
            out["error"] = self.error
        return out


def _fetch(url: str, timeout: int = 20, token: str = "") -> _Fetch:
    if LOCAL_PATH_RE.match(url or "") or urllib.parse.urlsplit(url).scheme.lower() not in {"http", "https"}:
        return _Fetch(False, 0, url, "", f"refused: {url!r} is not an http(s) URL")
    start = time.perf_counter()
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(300_000)
            body = raw.decode("utf-8", "replace")
            final_url = response.geturl()
            status = getattr(response, "status", 200)
            elapsed = int((time.perf_counter() - start) * 1000)
            if status >= 400:
                return _Fetch(False, status, final_url, body, f"HTTP {status}", elapsed)
            return _Fetch(True, status, final_url, body, "", elapsed)
    except urllib.error.HTTPError as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        try:
            body = exc.read(100_000).decode("utf-8", "replace")
        except Exception:
            body = ""
        return _Fetch(False, exc.code, getattr(exc, "url", url), body, f"HTTP {exc.code}", elapsed)
    except Exception as exc:  # DNS, TLS, timeout, connection reset
        elapsed = int((time.perf_counter() - start) * 1000)
        return _Fetch(False, 0, url, "", f"{type(exc).__name__}: {exc}", elapsed)


def normalize_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urllib.parse.urlsplit(value)
    if not parsed.netloc:
        return ""
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


def _login_wall(result: _Fetch) -> Optional[str]:
    """A Vercel Authentication wall is a deterministic answer, unlike a cold start."""
    low = f"{result.url}\n{result.body[:20000]}".lower()
    for marker in _LOGIN_MARKERS:
        if marker.lower() in low:
            return f"platform login wall ({marker})"
    return None


def _page_problem(result: _Fetch) -> Optional[str]:
    """Return a reason when a response is a platform page instead of the app."""
    wall = _login_wall(result)
    if wall:
        return wall
    haystack = f"{result.url}\n{result.body[:20000]}".lower()
    for marker in _PLATFORM_ERROR_MARKERS:
        if marker.lower() in haystack:
            return f"platform error page ({marker})"
    return None


def _title(body: str) -> str:
    match = TITLE_RE.search(body or "")
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def _asset_urls(base_url: str, body: str, limit: int = 12) -> List[str]:
    urls: List[str] = []
    for raw in ASSET_RE.findall(body or ""):
        candidate = urllib.parse.urljoin(base_url, raw)
        if urllib.parse.urlsplit(candidate).netloc == urllib.parse.urlsplit(base_url).netloc:
            if candidate not in urls:
                urls.append(candidate)
        if len(urls) >= limit:
            break
    return urls


def _poll(url: str, timeout: int, interval: float = 3.0) -> tuple[_Fetch, int]:
    deadline = time.time() + max(1, timeout)
    attempts = 0
    last = _Fetch(False, 0, url, "", "not attempted")
    while True:
        attempts += 1
        last = _fetch(url)
        if last.ok and not _page_problem(last) and "<html" in last.body.lower():
            return last, attempts
        if time.time() + interval >= deadline:
            return last, attempts
        time.sleep(interval)


def verify_site(
    url: str,
    *,
    routes: Optional[Iterable[str]] = None,
    marker: Optional[str] = None,
    api_health: Optional[str] = None,
    api_origin: Optional[str] = None,
    timeout: int = 90,
    poll_interval: float = 3.0,
) -> Dict[str, Any]:
    """Verify a deployed site and return evidence, never a bare boolean.

    ``verified`` is true only when every configured check passed. ``status`` is
    one of ``verified``, ``unreachable``, ``platform-page``, ``broken-assets``,
    ``missing-routes``, ``api-not-baked``, ``api-health-target-invalid``,
    ``marker-missing`` or ``degraded`` so callers can report the real reason
    instead of "deploy failed". ``api_origin`` demands that the deployed bundle
    actually reference that API host.
    """
    start = time.perf_counter()
    target = normalize_url(url)
    failures: List[str] = []
    checks: Dict[str, Any] = {}
    if not target:
        return {
            "verified": False,
            "status": "unreachable",
            "url": "",
            "title": "",
            "attempts": 0,
            "elapsed_ms": 0,
            "checks": {},
            "failures": ["empty or invalid URL — nothing was deployed"],
        }

    home, attempts = _poll(target, timeout, poll_interval)
    checks["home"] = {**home.as_dict(), "title": _title(home.body)}
    if not home.ok:
        return {
            "verified": False,
            "status": "unreachable",
            "url": target,
            "title": "",
            "attempts": attempts,
            "elapsed_ms": int((time.perf_counter() - start) * 1000),
            "checks": checks,
            "failures": [f"home did not answer: {home.error or f'HTTP {home.status}'}"],
        }

    problem = _page_problem(home)
    if problem:
        return {
            "verified": False,
            "status": "platform-page",
            "url": target,
            "title": _title(home.body),
            "attempts": attempts,
            "elapsed_ms": int((time.perf_counter() - start) * 1000),
            "checks": checks,
            "failures": [problem],
        }

    title = _title(home.body)
    if not title:
        failures.append("home page has no <title>")
    if not SHELL_RE.search(home.body):
        failures.append("home page has no React/Vue app shell (#root/#app)")
    checks["shell"] = {"ok": bool(title) and bool(SHELL_RE.search(home.body)), "title": title}

    assets = _asset_urls(home.url or target, home.body)
    asset_failures: List[Dict[str, Any]] = []
    unprocessed_css: List[str] = []
    # A frontend built without VITE_API_URL still renders perfectly while every
    # form posts to the visitor's own localhost, so the deployed bundle has to
    # carry the API host we asked for — a 200 on the pages proves nothing here.
    origin_host = (urllib.parse.urlsplit(api_origin or "").netloc or "").lower()
    api_baked = bool(origin_host) and origin_host in (home.body or "").lower()
    for asset in assets:
        result = _fetch(asset, timeout=15)
        if not result.ok:
            asset_failures.append({**result.as_dict(), "asset": asset})
        elif asset.split("?")[0].endswith(".css") and "@tailwind" in result.body:
            # A CSS file that still contains the directives means PostCSS did not
            # run in the deploy — the site ships unstyled while returning 200.
            unprocessed_css.append(asset)
        elif origin_host and asset.split("?")[0].endswith(".js") and origin_host in result.body.lower():
            api_baked = True
    checks["assets"] = {"checked": len(assets), "ok": len(assets) - len(asset_failures), "failed": asset_failures}
    checks["css"] = {"checked": sum(1 for a in assets if a.split("?")[0].endswith(".css")),
                     "unprocessed": unprocessed_css}
    if api_origin:
        checks["api_baked"] = {"expected": api_origin, "ok": bool(api_baked)}
        if not api_baked:
            failures.append(
                f"deployed bundle never references {api_origin} — it was built "
                "without VITE_API_URL, so every form posts to the visitor's localhost"
            )
    if assets and asset_failures:
        failures.append(f"{len(asset_failures)}/{len(assets)} bundle assets failed to load")
    if unprocessed_css:
        failures.append(f"unprocessed Tailwind CSS in {len(unprocessed_css)} asset(s)")
    if not assets:
        failures.append("index.html references no JS/CSS assets")

    route_results: Dict[str, Any] = {}
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(target))
    for route in routes or []:
        route_url = urllib.parse.urljoin(origin + "/", str(route).lstrip("/"))
        result = _fetch(route_url, timeout=15)
        ok = result.ok and not _page_problem(result) and (SHELL_RE.search(result.body) is not None or "<html" in result.body.lower())
        route_results[route] = {**result.as_dict(), "ok": bool(ok)}
        if not ok:
            failures.append(f"route {route} did not render (HTTP {result.status or 'error'})")
    if route_results:
        checks["routes"] = route_results

    if marker:
        found = marker in home.body
        checks["marker"] = {"ok": found, "expected": marker}
        if not found:
            failures.append(f"expected marker '{marker}' not present")

    if api_health:
        if LOCAL_PATH_RE.match(api_health):
            checks["api"] = {"ok": False, "status": 0, "url": api_health, "body": "",
                             "error": "local path, not a URL"}
            failures.append(
                f"API health target {api_health!r} is a filesystem path, not a URL — a Git "
                "Bash/MSYS shell rewrote a leading-slash argument. Pass it without the slash "
                "(api/v1/health) or as a full https:// URL."
            )
        else:
            health_url = urllib.parse.urljoin(origin + "/", api_health.lstrip("/"))
            health = _fetch(health_url, timeout=20)
            health_ok = health.ok
            health_body: Any = health.body[:500]
            if health.ok:
                try:
                    parsed = json.loads(health.body)
                    health_body = parsed
                    status = str(parsed.get("status", "")).lower()
                    if status in {"unhealthy", "degraded", "down", "error"}:
                        health_ok = False
                except ValueError:
                    pass
            checks["api"] = {"ok": health_ok, "status": health.status, "url": health_url,
                             "body": health_body}
            if not health_ok:
                failures.append(f"API health check failed at {health_url}")

    verified = not failures
    if verified:
        status = "verified"
    elif any("unprocessed Tailwind" in item for item in failures):
        status = "unprocessed-css"
    elif any("built without VITE_API_URL" in item for item in failures):
        status = "api-not-baked"
    elif any("is a filesystem path, not a URL" in item for item in failures):
        status = "api-health-target-invalid"
    elif any(item.startswith("route ") for item in failures):
        status = "missing-routes"
    elif any("assets" in item for item in failures):
        status = "broken-assets"
    elif any("marker" in item for item in failures):
        status = "marker-missing"
    else:
        status = "degraded"

    return {
        "verified": verified,
        "status": status,
        "url": home.url or target,
        "title": title,
        "attempts": attempts,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
        "checks": checks,
        "failures": failures,
    }


def _is_health_envelope(payload: Any) -> bool:
    """True for a JSON object shaped like the generated health response."""
    return isinstance(payload, dict) and "status" in payload


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 20, *,
               token: str = "", method: str = "POST") -> _Fetch:
    """Send a JSON body and capture the response with the same evidence shape.

    ``method`` covers PUT/DELETE because the generated routes that need proving
    are not only creates; ``token`` is what the authenticated dashboard sends.
    """
    if LOCAL_PATH_RE.match(url or "") or urllib.parse.urlsplit(url).scheme.lower() not in {"http", "https"}:
        return _Fetch(False, 0, url, "", f"refused: {url!r} is not an http(s) URL")
    body = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(100_000)
            status = getattr(response, "status", 200)
            elapsed = int((time.perf_counter() - start) * 1000)
            return _Fetch(status < 400, status, response.geturl(),
                          raw.decode("utf-8", "replace"),
                          f"HTTP {status}" if status >= 400 else "", elapsed)
    except urllib.error.HTTPError as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        try:
            raw = exc.read(100_000).decode("utf-8", "replace")
        except Exception:
            raw = ""
        return _Fetch(False, exc.code, getattr(exc, "url", url), raw, f"HTTP {exc.code}", elapsed)
    except Exception as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return _Fetch(False, 0, url, "", f"{type(exc).__name__}: {exc}", elapsed)


def _health_payload(body: str) -> Any:
    """The JSON object a health endpoint answered with, or None."""
    if not body:
        return None
    try:
        payload = json.loads(body)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def _db_is_down(payload: Any) -> bool:
    """True when a health payload explicitly reports the database unreachable."""
    if not isinstance(payload, dict):
        return False
    return str(payload.get("db", "")).lower() == "disconnected" or str(payload.get("status", "")).lower() in {
        "unhealthy", "degraded", "down", "error"
    }


def verify_api_health(
    health_url: str,
    *,
    timeout: int = 90,
    poll_interval: float = 3.0,
    require_database: bool = True,
) -> Dict[str, Any]:
    """Poll a hosted API's health endpoint and prove the database answers.

    A 200 here is not proof either. The first generated health route returned a
    static ``{status: healthy, uptime}`` while Postgres was unreachable, so the
    run certified a broken deployment as live; the contract is now ``db:
    connected``, which only a real ``SELECT 1`` can produce. Cold starts and DNS
    propagation are waited out, and a target a shell rewrote into a filesystem
    path is named instead of fetched.

    ``status`` is one of ``verified``, ``target-invalid``, ``unreachable``,
    ``not-json``, ``platform-page``, ``db-disconnected`` or ``db-not-proven``.
    """
    start = time.perf_counter()
    failures: List[str] = []
    if LOCAL_PATH_RE.match(health_url or "") or urllib.parse.urlsplit(health_url).scheme.lower() not in {"http", "https"}:
        return {
            "ok": False,
            "status": "target-invalid",
            "url": health_url,
            "body": "",
            "attempts": 0,
            "elapsed_ms": 0,
            "failures": [f"health target {health_url!r} is not an http(s) URL — a Git Bash/MSYS "
                         "shell rewrote a leading-slash path"],
        }

    deadline = time.time() + max(1, timeout)
    attempts = 0
    result = _Fetch(False, 0, health_url, "", "not attempted")
    parsed: Any = None
    while True:
        attempts += 1
        result = _fetch(health_url, timeout=20)
        parsed = _health_payload(result.body)
        # A payload that names the database as down is a deterministic answer,
        # not a cold-start race — polling it again would burn the whole timeout
        # on a deployment that can never recover.
        if parsed is not None and (_is_health_envelope(parsed) or _db_is_down(parsed)):
            break
        # A login wall does not lift on its own: polling it again would burn the
        # whole budget on a deployment nobody can reach.
        if _login_wall(result):
            break
        if time.time() + poll_interval >= deadline:
            break
        time.sleep(poll_interval)

    elapsed = int((time.perf_counter() - start) * 1000)
    base = {"url": result.url or health_url, "attempts": attempts, "elapsed_ms": elapsed,
            "body": parsed if parsed is not None else result.body[:400]}

    if _db_is_down(parsed):
        return {**base, "ok": False, "status": "db-disconnected",
                "failures": ["the hosted API is up but its database is not reachable "
                             f"(status={str(parsed.get('status', '?')).lower()}, "
                             f"db={str(parsed.get('db', '?')).lower()})"]}
    if not result.ok:
        problem = _page_problem(result)
        status = "platform-page" if problem else "unreachable"
        reason = problem or (result.error or f"HTTP {result.status}")
        return {**base, "ok": False, "status": status,
                "failures": [f"hosted API health did not answer: {reason}"]}

    if not isinstance(parsed, dict):
        problem = _page_problem(result)
        if problem:
            return {**base, "ok": False, "status": "platform-page",
                    "failures": [f"the API host answered with a platform page instead of the health "
                                 f"endpoint ({problem}) — the deployment is not publicly reachable"]}
        return {**base, "ok": False, "status": "not-json",
                "failures": ["the health endpoint answered but not with JSON — "
                             "the API host is serving something that is not the generated backend"]}

    declared = str(parsed.get("status", "")).lower()
    db = str(parsed.get("db", "")).lower()
    if db == "disconnected" or declared in {"unhealthy", "degraded", "down", "error"}:
        return {**base, "ok": False, "status": "db-disconnected",
                "failures": [f"the hosted API is up but its database is not reachable (status={declared or '?'}, db={db or '?'})"]}
    if require_database and not db:
        return {**base, "ok": False, "status": "db-not-proven",
                "failures": ["the health payload never reports a `db` field, so nothing proves the "
                             "database was queried — a static {status: healthy} response is not evidence"]}
    return {**base, "ok": True, "status": "verified", "failures": failures}


CONTACT_PROBE_PATH = "api/v1/contact"
# The probe row is deliberate: a delivery is only demonstrable to a client when a
# real submission has been stored, so the proof leaves one clearly-labelled
# inquiry behind instead of pretending the write happened.
CONTACT_PROBE_PAYLOAD = {
    "name": "LumicorePro delivery probe",
    "email": "delivery-probe@lumicorepro.app",
    "message": "Automated full-stack delivery verification. This inquiry was written by the "
               "LumicorePro website factory to prove the contact form stores rows in the "
               "hosted database. Safe to delete.",
}
CONTACT_PROBE_REJECTED = {
    "name": "",
    "email": "not-an-address",
    "message": "short",
}


def verify_contact_write(
    api_url: str,
    *,
    path: str = CONTACT_PROBE_PATH,
    timeout: int = 60,
    poll_interval: float = 4.0,
) -> Dict[str, Any]:
    """Write a real inquiry through the hosted API and require the row id back.

    ``db: connected`` only proves the process can reach Postgres. The claim a
    client cares about — "the form works" — needs an INSERT that returns an id,
    plus the validation layer rejecting a malformed submission rather than
    storing it. Cold starts are polled out; a target a shell rewrote into a
    filesystem path is named, never posted to.

    ``status`` is one of ``verified``, ``target-invalid``, ``write-failed``,
    ``write-unconfirmed`` or ``validation-not-enforced``.
    """
    start = time.perf_counter()
    base_api = normalize_url(api_url)
    if LOCAL_PATH_RE.match(api_url or "") or not base_api:
        return {"ok": False, "status": "target-invalid", "url": api_url, "id": "",
                "attempts": 0, "elapsed_ms": 0,
                "failures": [f"API target {api_url!r} is not an http(s) URL — a Git Bash/MSYS "
                             "shell rewrote a leading-slash path"]}

    suffix = "" if base_api.rstrip("/").endswith("/contact") else "/" + path.strip("/")
    url = base_api.rstrip("/") + suffix

    deadline = time.time() + max(1, timeout)
    attempts = 0
    written = _PostResult()
    while True:
        attempts += 1
        written = _submit(url, CONTACT_PROBE_PAYLOAD)
        if written.record_id:
            break
        if time.time() + poll_interval >= deadline:
            break
        time.sleep(poll_interval)

    elapsed = int((time.perf_counter() - start) * 1000)
    base = {"url": url, "attempts": attempts, "elapsed_ms": elapsed,
            "status_code": written.status, "id": written.record_id}

    if not written.record_id:
        reason = written.error or f"HTTP {written.status}" or "no response"
        status = "write-unconfirmed" if written.status in {200, 201} else "write-failed"
        detail = ("the contact form returned a success code but no row id, so nothing proves the "
                  "inquiry was stored" if status == "write-unconfirmed"
                  else f"the hosted contact form did not accept a real submission ({reason})")
        return {**base, "ok": False, "status": status, "failures": [detail]}

    rejected = _submit(url, CONTACT_PROBE_REJECTED)
    if rejected.ok:
        return {**base, "ok": False, "status": "validation-not-enforced",
                "failures": ["the hosted API stored a submission with an empty name, a malformed "
                             "email and a 5-character message — the form is live but its validation "
                             "is not, which is not something to hand a client"]}
    return {**base, "ok": True, "status": "verified", "failures": []}


API_PREFIX = "/api/v1"
PROBE_PASSWORD = "FactoryProbe!2026"
# One probe identity per delivered product: two projects sharing a database
# cluster must never share the user whose rows the verifier reads back.
PROBE_RECORD = {
    "title": "LumicorePro delivery probe (safe to delete)",
    "body": "Written by the website factory to prove this product's API can create, read, "
            "update and delete a row in its own database. Safe to delete.",
    "status": "draft",
}
PROBE_BLANK_RECORD = {"title": "   ", "body": ""}
# Codes that mean "not up yet" rather than "broken": a propagating deployment or
# a cold function answers these and recovers.
_COLD_STATUSES = {0, 404, 408, 425, 429}


def probe_email_for(api_url: str, tag: str = "owner") -> str:
    """The probe account this product's verification signs in with."""
    host = urllib.parse.urlsplit(normalize_url(api_url)).hostname or "app"
    label = re.sub(r"[^a-z0-9-]+", "-", host.split(".")[0].lower()).strip("-") or "app"
    return f"factory-probe.{tag}@{label}.lumicorepro.app"


def _json_dict(body: str) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(body or "")
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def _token_of(result: _Fetch) -> str:
    payload = _json_dict(result.body)
    return str(payload.get("token") or "") if payload else ""


def _data_of(result: _Fetch) -> Any:
    payload = _json_dict(result.body)
    return payload.get("data") if payload else None


def _data_id(result: _Fetch) -> str:
    data = _data_of(result)
    if isinstance(data, dict):
        return str(data.get("id") or "")
    return ""


def _row_ids(payload: Any) -> List[str]:
    rows = payload if isinstance(payload, list) else []
    return [str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")]


def _is_cold(result: _Fetch) -> bool:
    """A response that means "not reachable yet", so polling is the right answer."""
    return result.status in _COLD_STATUSES or result.status >= 500


def verify_api_surface(
    api_url: str,
    *,
    timeout: int = 90,
    poll_interval: float = 3.0,
) -> Dict[str, Any]:
    """Drive every generated endpoint the way a signed-in client would.

    ``db: connected`` proves the process opened a connection and the contact
    probe proves one INSERT. Neither proves the dashboard works: sign-in, list,
    create, read-back, edit, delete and the two guardrails (an anonymous caller
    must not read rows, a second tenant must not see the first one's) are
    separate routes that have each shipped broken on their own. A delivery that
    cannot answer all of them is not something a client can be demoed.

    The probe row is deleted again, so nothing is left in the buyer's database.

    ``status`` is ``verified`` or the first step that failed: ``target-invalid``,
    ``auth-failed``, ``list-failed``, ``create-failed``, ``read-back-failed``,
    ``update-failed``, ``validation-not-enforced``, ``auth-not-enforced``,
    ``tenant-isolation-broken``, ``tenant-isolation-unproven`` or ``delete-failed``.
    """
    start = time.perf_counter()
    root = normalize_url(api_url)
    proven: List[str] = []
    failures: List[str] = []
    leftovers: List[str] = []
    attempts = 0
    if LOCAL_PATH_RE.match(api_url or "") or not root:
        return {"ok": False, "status": "target-invalid", "url": api_url, "token": "",
                "proven": proven, "leftovers": leftovers, "probe": {}, "attempts": 0,
                "elapsed_ms": 0,
                "failures": [f"API target {api_url!r} is not an http(s) URL — a Git Bash/MSYS "
                             "shell rewrote a leading-slash path"]}

    api = root.rstrip("/") + API_PREFIX
    owner = probe_email_for(root)
    other = probe_email_for(root, tag="other")
    deadline = time.time() + max(1, timeout)

    def outcome(status: str, *, ok: bool = False, token: str = "") -> Dict[str, Any]:
        return {"ok": ok, "status": status, "url": api, "token": token, "proven": proven,
                "leftovers": leftovers, "probe": {"email": owner}, "attempts": attempts,
                "elapsed_ms": int((time.perf_counter() - start) * 1000), "failures": failures}

    def retrying(send, *, limit: int = 2):
        """Poll a cold deployment out, then stop: a 404 twice is a missing route."""
        nonlocal attempts
        result = send()
        attempts += 1
        while _is_cold(result) and attempts <= limit and time.time() + poll_interval < deadline:
            time.sleep(poll_interval)
            result = send()
            attempts += 1
        return result

    registered = retrying(lambda: _post_json(
        f"{api}/auth/register",
        {"name": "LumicorePro delivery probe", "email": owner, "password": PROBE_PASSWORD}))
    if registered.status not in {200, 201, 409}:
        failures.append("the hosted sign-up route did not answer "
                        f"({registered.error or f'HTTP {registered.status}'}), so the API is not a "
                        "product a client can be shown")
        return outcome("auth-failed")
    proven.append("POST /api/v1/auth/register")

    logged_in = retrying(lambda: _post_json(f"{api}/auth/login",
                                            {"email": owner, "password": PROBE_PASSWORD}))
    token = _token_of(logged_in) or _token_of(registered)
    if not token:
        failures.append("sign-up answered but sign-in returned no session token, so the dashboard "
                        f"cannot be opened (login: {logged_in.error or f'HTTP {logged_in.status}'})")
        return outcome("auth-failed")
    proven.append("POST /api/v1/auth/login")

    listed = _fetch(f"{api}/records", token=token)
    if not listed.ok or not isinstance(_data_of(listed), list):
        failures.append("the records list did not answer for a signed-in client "
                        f"({listed.error or f'HTTP {listed.status}'}) — the dashboard would show an "
                        "error instead of its content")
        return outcome("list-failed")
    proven.append("GET /api/v1/records")

    created = _post_json(f"{api}/records", PROBE_RECORD, token=token)
    row_id = _data_id(created)
    if not created.ok or not row_id:
        failures.append(f"creating a row failed for a signed-in client "
                        f"({created.error or f'HTTP {created.status}'})")
        return outcome("create-failed")
    proven.append("POST /api/v1/records")
    leftovers = [row_id]

    # A 201 with an id proves the process answered. Reading the row back out of
    # Postgres is what proves the save is real.
    refetched = _fetch(f"{api}/records", token=token)
    single = _fetch(f"{api}/records/{row_id}", token=token)
    if row_id not in _row_ids(_data_of(refetched)) or not single.ok:
        failures.append(f"the row it created (id `{row_id}`) came back missing from the list or the "
                        f"single-read ({single.error or f'HTTP {single.status}'}) — writes are not "
                        "reaching the database the client is shown")
        return outcome("read-back-failed")
    proven.append("GET /api/v1/records/:id")
    proven.append("row read back from the database")

    updated = _post_json(f"{api}/records/{row_id}", {**PROBE_RECORD, "status": "published"},
                         token=token, method="PUT")
    updated_row = _data_of(updated) if isinstance(_data_of(updated), dict) else {}
    if not updated.ok or str(updated_row.get("status")) != "published":
        failures.append(f"editing a row did not stick ({updated.error or f'HTTP {updated.status}'})"
                        if not updated.ok else
                        "the edit route answered 200 but returned the row still in draft")
        return outcome("update-failed")
    proven.append("PUT /api/v1/records/:id")

    blank = _post_json(f"{api}/records", PROBE_BLANK_RECORD, token=token)
    if blank.ok:
        failures.append("the API stored a record with a blank title, so the form's validation is "
                        "only in the browser")
        blank_id = _data_id(blank)
        if blank_id:
            leftovers.append(blank_id)
            if _post_json(f"{api}/records/{blank_id}", None, token=token, method="DELETE").ok:
                leftovers.remove(blank_id)
        return outcome("validation-not-enforced")
    proven.append("blank title is rejected")

    second = _post_json(f"{api}/auth/register",
                        {"name": "LumicorePro second tenant", "email": other,
                         "password": PROBE_PASSWORD})
    other_token = _token_of(second) or _token_of(
        _post_json(f"{api}/auth/login", {"email": other, "password": PROBE_PASSWORD}))
    if not other_token:
        failures.append("a second signed-in account could not be created, so cross-tenant isolation "
                        "is unproven — and an unproven guardrail is not one to ship")
        return outcome("tenant-isolation-unproven")
    foreign_read = _fetch(f"{api}/records/{row_id}", token=other_token)
    foreign_list = _fetch(f"{api}/records", token=other_token)
    foreign_delete = _post_json(f"{api}/records/{row_id}", None, token=other_token, method="DELETE")
    if foreign_read.ok or row_id in _row_ids(_data_of(foreign_list)) or foreign_delete.ok:
        failures.append(f"the row belonging to `{owner}` was readable or deletable by a different "
                        "signed-in account — every listing of that tenant's data is exposed")
        return outcome("tenant-isolation-broken")
    proven.append("second tenant cannot read the row")

    anonymous = _fetch(f"{api}/records")
    if anonymous.ok:
        failures.append("the records list answered without a token, so the API is world-readable")
        return outcome("auth-not-enforced")
    proven.append("records are unreachable without a token")

    deleted = _post_json(f"{api}/records/{row_id}", None, token=token, method="DELETE")
    still_there = _fetch(f"{api}/records/{row_id}", token=token)
    if not deleted.ok or still_there.ok:
        failures.append(f"the probe row could not be removed again "
                        f"({deleted.error or f'HTTP {deleted.status}'}"
                        f"{', and it is still readable' if still_there.ok else ''}) — the delivery "
                        "would leave demo data in the client's database")
        return outcome("delete-failed")
    proven.append("DELETE /api/v1/records/:id")
    leftovers = []
    return outcome("verified", ok=True, token=token)


def _abort_stream(response) -> None:
    """Drop the connection without letting the caller wait for the server.

    A shutdown ends the stream at once on POSIX. On Windows a receive that is
    already blocked is not interrupted by it, so closing there waits for that
    read to return — up to the feed's own self-close limit, which is a minute in
    production. The close therefore runs on a daemon thread the caller joins
    briefly and abandons; the proof is already in hand by this point.
    """
    try:
        sock = _stream_socket(response)
        if sock is not None:
            sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    dropper = threading.Thread(target=_close_quietly, args=(response,),
                               daemon=True, name="live-verify-close")
    dropper.start()
    dropper.join(1.0)


def _close_quietly(response) -> None:
    try:
        response.close()
    except Exception:
        pass


def _stream_socket(response):
    return getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)


def _block_until_data(response) -> None:
    """Drop the connect timeout once the stream is open.

    The worker thread's own deadline decides how long a frame may take, and a
    socket that times out mid-read is not readable again on Windows.
    """
    try:
        _stream_socket(response).settimeout(None)
    except Exception:
        pass


class _SseReader:
    """Reads an event stream on a daemon thread so a deadline can be honoured.

    A socket read timeout is not usable here: on Windows it poisons the socket
    ("cannot read from timed out object"), and select is blind to the bytes
    http.client already buffered while it parsed the headers — which is where the
    first frames of a fast local stream usually are. A blocking read on a worker
    thread, with the caller waiting on a queue, gets both right.
    """

    def __init__(self, response):
        self._lines: "queue.Queue[Any]" = queue.Queue()
        self._response = response
        _block_until_data(response)
        threading.Thread(target=self._pump, daemon=True, name="live-verify-sse").start()

    def _pump(self):
        try:
            while True:
                line = self._response.readline()
                if not line:
                    self._lines.put(None)  # the server closed the stream
                    return
                self._lines.put(line)
        except Exception as exc:  # a reset, or the caller closing under us
            self._lines.put(exc)

    def line(self, seconds: float):
        try:
            item = self._lines.get(timeout=max(0.0, seconds))
        except queue.Empty:
            return "timeout", None
        if item is None:
            return "eof", None
        if isinstance(item, BaseException):
            return "error", item
        return "line", item


def _sse_frames(reader, deadline_at):
    """Yield (kind, fields) for a server-sent-event stream: frame|eof|timeout|error.

    A generator, so a caller can read a frame, do the thing that should cause the
    next one, and resume reading with the buffer state intact. ``deadline_at`` is
    callable because the second wait has a different, much tighter budget: the
    frame for a write must arrive in about one poll, not in the stream's lifetime.
    """
    fields: Dict[str, str] = {}
    while True:
        remaining = deadline_at() - time.monotonic()
        if remaining <= 0:
            yield ("timeout", {})
            return
        kind, item = reader.line(min(remaining, 5.0))
        if kind == "timeout":
            continue
        if kind == "eof":
            yield ("eof", {})
            return
        if kind == "error":
            yield ("error", {"reason": f"{type(item).__name__}: {item}"})
            return
        line = item.decode("utf-8", "replace").rstrip("\r\n")
        if line == "":
            if fields:
                yield ("frame", fields)
                fields = {}
            continue
        if line.startswith(":"):
            continue  # a keep-alive comment carries no claim
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()


PII_IN_FEED_KEYS = {"email", "name", "message", "body", "phone"}
REALTIME_FEED_EVENTS = {"record:changed", "contact:created"}


def verify_realtime_feed(
    api_url: str,
    token: str,
    *,
    timeout: int = 45,
    event_timeout: float = 8.0,
) -> Dict[str, Any]:
    """Prove the live push really pushes: write a row, watch the open stream fire.

    The dashboard badge says "Live updates". Only a frame arriving on a stream
    that was open *before* the write makes that true — a broken feed still leaves
    the polling fallback, so the page looks alive while the push is dead. The
    token travels in the query string because EventSource cannot set headers,
    which is the same transport the shipped client uses.

    ``status`` is ``verified``, ``target-invalid``, ``unauthorized``, ``no-stream``,
    ``not-event-stream``, ``no-ready``, ``write-failed``, ``no-event``,
    ``pii-in-feed`` or ``cleanup-failed``.
    """
    start = time.perf_counter()
    root = normalize_url(api_url)
    events: List[str] = []
    latency_ms = 0

    def outcome(status: str, *, ok: bool = False, detail: str = "", row_id: str = "",
                leftovers: Optional[List[str]] = None) -> Dict[str, Any]:
        return {"ok": ok, "status": status, "events": events, "latency_ms": latency_ms,
                "id": row_id, "leftovers": list(leftovers or []), "attempts": 1,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "failures": [detail] if detail else []}

    if LOCAL_PATH_RE.match(api_url or "") or not root:
        return outcome("target-invalid",
                       detail=f"API target {api_url!r} is not an http(s) URL — a Git Bash/MSYS "
                              "shell rewrote a leading-slash path")
    if not str(token or "").strip():
        return outcome("target-invalid",
                       detail="no token to open the change feed with — the feed is authenticated, so "
                              "an unauthenticated probe would only prove a 401")

    api = root.rstrip("/") + API_PREFIX
    stream_url = f"{api}/events?token={urllib.parse.quote(str(token).strip(), safe='')}"
    request = urllib.request.Request(
        stream_url, headers={"User-Agent": USER_AGENT, "Accept": "text/event-stream",
                             "Cache-Control": "no-cache"})
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return outcome("unauthorized",
                           detail="the change feed refused the session token it was given, so the "
                                  "client's dashboard could never connect")
        return outcome("no-stream", detail=f"the change feed did not open ({exc.code})")
    except Exception as exc:
        return outcome("no-stream",
                       detail=f"the change feed did not open ({type(exc).__name__}: {exc})")

    try:
        content_type = str(response.headers.get("Content-Type") or "")
        if "text/event-stream" not in content_type.lower():
            return outcome("not-event-stream",
                           detail=f"the feed endpoint answered with a {content_type or 'missing'} "
                                  "content type instead of an event stream — that route is not the "
                                  "generated change feed")
        stream_deadline = time.monotonic() + max(1, timeout)
        event_limit = None

        def deadline_at():
            return min(stream_deadline, event_limit) if event_limit is not None else stream_deadline

        frames = _sse_frames(_SseReader(response), deadline_at)
        for kind, fields in frames:
            if kind != "frame":
                return outcome("no-stream" if kind in {"eof", "error"} else "no-ready",
                               detail=("the stream closed before the feed said ready"
                                       if kind != "timeout" else
                                       "the stream never said ready — a feed that opens but does not "
                                       "announce itself is not a live feed"))
            if (fields.get("event") or "message") == "ready":
                events.append("ready")
                break

        written = _post_json(f"{api}/records", {**PROBE_RECORD, "title": "LumicorePro live-feed probe"},
                             token=token)
        row_id = _data_id(written)
        if not written.ok or not row_id:
            return outcome("write-failed",
                           detail=f"the feed probe could not create a row "
                                  f"({written.error or f'HTTP {written.status}'})")
        write_done = time.perf_counter()
        event_limit = time.monotonic() + max(0.5, event_timeout)

        def abandon(detail: str, status: str) -> Dict[str, Any]:
            """A failed feed proof still must not leave a row in the demo."""
            left = [row_id]
            if _post_json(f"{api}/records/{row_id}", None, token=token, method="DELETE").ok:
                left = []
            return outcome(status, detail=detail, row_id=row_id, leftovers=left)

        for kind, fields in frames:
            if kind != "frame":
                break
            name = fields.get("event") or "message"
            events.append(name)
            if name not in REALTIME_FEED_EVENTS:
                continue
            payload = _json_dict(fields.get("data", "")) or {}
            leaked = sorted(PII_IN_FEED_KEYS & {str(key).lower() for key in payload})
            if leaked:
                return abandon(f"the change feed put {', '.join(leaked)} in a frame — the signal is an "
                               "id and a timestamp; broadcasting the inquiry text leaks customer data "
                               "to every open dashboard", "pii-in-feed")
            if str(payload.get("id")) != row_id:
                continue
            latency_ms = int((time.perf_counter() - write_done) * 1000)
            cleaned = _post_json(f"{api}/records/{row_id}", None, token=token, method="DELETE")
            if not cleaned.ok:
                return outcome("cleanup-failed", row_id=row_id, leftovers=[row_id],
                               detail=f"the feed fired but the probe row could not be removed "
                                      f"({cleaned.error or f'HTTP {cleaned.status}'}) — the delivery "
                                      "would leave demo data behind")
            events.append("cleaned")
            return outcome("verified", ok=True, row_id=row_id)
        return abandon("no `record:changed` frame for the row written while the stream was open "
                       f"(budget {int(event_timeout * 1000)} ms, saw: "
                       f"{', '.join(events) or 'nothing'})", "no-event")
    finally:
        _abort_stream(response)


class _PostResult:
    __slots__ = ("ok", "status", "error", "record_id")

    def __init__(self, ok=False, status=0, error="", record_id=""):
        self.ok = ok
        self.status = status
        self.error = error
        self.record_id = record_id


def _submit(url: str, payload: Dict[str, Any]) -> _PostResult:
    result = _post_json(url, payload)
    record_id = ""
    if result.ok:
        try:
            body = json.loads(result.body)
        except ValueError:
            body = None
        if isinstance(body, dict):
            data = body.get("data")
            if isinstance(data, dict):
                record_id = str(data.get("id") or "")
            else:
                record_id = str(body.get("id") or "")
    return _PostResult(result.ok, result.status, result.error, record_id)


def expected_routes(project_dir: str) -> List[str]:
    """SPA routes worth probing for a generated project (only if they exist)."""
    from pathlib import Path

    base = Path(project_dir)
    if (base / "frontend").is_dir():
        base = base / "frontend"
    pages = base / "src" / "pages"
    if not pages.is_dir():
        return ["/"]
    mapping = {
        "Features.jsx": "/features",
        "Pricing.jsx": "/pricing",
        "About.jsx": "/about",
        "Contact.jsx": "/contact",
        "Login.jsx": "/login",
        "Register.jsx": "/register",
    }
    routes = ["/"]
    for filename, route in mapping.items():
        if (pages / filename).is_file():
            routes.append(route)
    return routes


def save_report(report: Dict[str, Any], path: str) -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


__all__ = ["verify_site", "expected_routes", "normalize_url", "save_report",
           "verify_api_health", "verify_contact_write", "verify_api_surface",
           "verify_realtime_feed", "probe_email_for"]
