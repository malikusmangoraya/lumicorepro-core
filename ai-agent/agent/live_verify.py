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
_LOGIN_MARKERS = ("vercel.com/login", "sso-protection", "Authentication Required")


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


def _page_problem(result: _Fetch) -> Optional[str]:
    """Return a reason when a response is a platform page instead of the app."""
    haystack = f"{result.url}\n{result.body[:20000]}"
    for marker in _LOGIN_MARKERS:
        if marker.lower() in haystack.lower():
            return f"platform login wall ({marker})"
    for marker in _PLATFORM_ERROR_MARKERS:
        if marker.lower() in haystack.lower():
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
