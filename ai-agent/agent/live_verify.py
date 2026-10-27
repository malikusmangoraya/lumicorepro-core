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
import re
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


def _fetch(url: str, timeout: int = 20) -> _Fetch:
    if LOCAL_PATH_RE.match(url or "") or urllib.parse.urlsplit(url).scheme.lower() not in {"http", "https"}:
        return _Fetch(False, 0, url, "", f"refused: {url!r} is not an http(s) URL")
    start = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
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


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 20) -> _Fetch:
    """POST a JSON body and capture the response with the same evidence shape."""
    if LOCAL_PATH_RE.match(url or "") or urllib.parse.urlsplit(url).scheme.lower() not in {"http", "https"}:
        return _Fetch(False, 0, url, "", f"refused: {url!r} is not an http(s) URL")
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
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


__all__ = ["verify_site", "expected_routes", "normalize_url", "save_report"]
