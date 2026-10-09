"""
LumicorePro Operator Console
============================
A single self-contained control page for the AI agent, served by this stdlib-only
Python backend (no new dependencies).

Why a backend at all, instead of a static HTML file:
  - the agent API does not send CORS headers, so a `file://` page cannot call it
  - API keys must never reach the browser, so they are masked server-side
  - probing a provider's latency needs a server-side request, otherwise the
    browser hits mixed-content/CORS walls

Endpoints (all JSON unless noted):
  GET  /                          the console page
  GET  /assets/<file>             css + js
  GET  /api/console/overview      health, providers (masked), tiers, routing stats,
                                  recent runs  (one round trip)
  POST /api/console/tiers         save tier membership to .router.json
  POST /api/console/launch        start a pipeline run (JSON body)
  GET  /api/console/runs          recent runs (the page polls this for progress;
                                  the agent API has no SSE, so there is no
                                  /api/console/events endpoint)
  POST /api/console/probe         latency probe for one provider
  POST /api/console/probe-all     probe every provider, report which really answer
  POST /api/console/open          open a generated project folder in Explorer

Run it:  python ai-agent/console.py     (then open http://127.0.0.1:8100)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8000").rstrip("/")
CONSOLE_PORT = int(os.getenv("CONSOLE_PORT", "8100"))
ASSET_DIR = os.path.join(HERE, "console")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

def agent_get(path: str, timeout: float = 6.0) -> Tuple[int, Any]:
    """GET the agent API. Returns (status, parsed_or_text)."""
    req = urllib.request.Request(f"{AGENT_URL}{path}", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:
        return 0, str(exc)
    try:
        return status, json.loads(body)
    except ValueError:
        return status, body


def agent_post(path: str, payload: Dict[str, Any], timeout: float = 30.0) -> Tuple[int, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{AGENT_URL}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:
        return 0, str(exc)
    try:
        return status, json.loads(body)
    except ValueError:
        return status, body


def mask_key(value: str) -> str:
    """Never ship a full key to the browser."""
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def build_overview() -> Dict[str, Any]:
    """One round trip that fills the whole page."""
    from agent.ai_routing import get_router, offline, enabled
    from config.providers import FALLBACK_ORDER, PROVIDER_CONFIGS, get_available_providers

    health_status, health = agent_get("/health")
    providers_status, providers = agent_get("/api/providers")
    watchtower_status, watchtower = agent_get("/api/watchtower", timeout=8.0)
    usage_status, usage = agent_get("/api/usage", timeout=8.0)
    runs_status, runs = agent_get("/api/runs", timeout=8.0)

    available = set()
    cards: List[Dict[str, Any]] = []
    if providers_status == 200 and isinstance(providers, dict):
        for item in providers.get("providers", []) or []:
            name = item.get("name") or item.get("provider")
            if not name:
                continue
            ok = bool(item.get("available") or item.get("has_key"))
            if ok:
                available.add(name)
            cards.append({
                "name": name,
                "label": item.get("label") or (PROVIDER_CONFIGS.get(name) or {}).get("label", name),
                "available": ok,
                "key_masked": mask_key(item.get("api_key") or (PROVIDER_CONFIGS.get(name) or {}).get("api_key", "")),
                "base_url": item.get("base_url") or (PROVIDER_CONFIGS.get(name) or {}).get("base_url", ""),
                "model": item.get("model") or (PROVIDER_CONFIGS.get(name) or {}).get("model", ""),
                "open_source": bool((PROVIDER_CONFIGS.get(name) or {}).get("open_source")),
                "needs_key": bool((PROVIDER_CONFIGS.get(name) or {}).get("api_key")),
            })
    if not cards:
        for name in FALLBACK_ORDER:
            cfg = PROVIDER_CONFIGS.get(name) or {}
            cards.append({
                "name": name,
                "label": cfg.get("label", name),
                "available": name in available,
                "key_masked": mask_key(cfg.get("api_key", "")),
                "base_url": cfg.get("base_url", ""),
                "model": cfg.get("model", ""),
                "open_source": bool(cfg.get("open_source")),
                "needs_key": bool(cfg.get("api_key")),
            })

    router = get_router()
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": {
            "url": AGENT_URL,
            "reachable": health_status == 200,
            "health": health if health_status == 200 else {"error": health},
        },
        "router": {
            "enabled": enabled(),
            "offline": offline(),
            "tiers": router.tiers,
            "parallelism": router.parallelism,
            "cache": router.cache_stats(),
            "report": router.routing_report(),
        },
        "providers": cards,
        "fallback_order": list(FALLBACK_ORDER),
        "available_providers": sorted(available or set(get_available_providers())),
        "watchtower": watchtower if watchtower_status == 200 else None,
        "usage": usage if usage_status == 200 else None,
        "runs": (runs if runs_status == 200 else None),
    }


def read_tiers() -> Dict[str, List[str]]:
    from agent.ai_routing import TIERS, get_router

    router = get_router()
    return {tier: router.tier_names(tier) for tier in TIERS}


def write_tiers(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Persist tier membership to .router.json and reload the singleton."""
    from agent.ai_routing import ROUTER_CONFIG_PATH, TIERS, get_router, reset_router

    clean: Dict[str, List[str]] = {}
    for tier in TIERS:
        names = payload.get(tier)
        if not isinstance(names, list):
            continue
        seen: List[str] = []
        for raw in names:
            name = str(raw).strip().lower()
            if name and name not in seen:
                seen.append(name)
        if seen:
            clean[tier] = seen
    if not clean:
        return {"ok": False, "error": "no valid tiers supplied"}
    tmp = f"{ROUTER_CONFIG_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(clean, fh, indent=2)
    os.replace(tmp, ROUTER_CONFIG_PATH)
    reset_router()
    return {"ok": True, "saved": clean, "path": ROUTER_CONFIG_PATH, "active": read_tiers()}


def probe_all() -> Dict[str, Any]:
    """Probe every configured provider and report what actually answers.

    The provider cards show *configuration* state (key present, model set). This
    is the honest second layer: a real measured call per provider, so the operator
    can see which models work right now instead of trusting a green badge.
    """
    from agent.ai_routing import get_router

    router = get_router()
    names: List[str] = []
    for tier in ("fast", "balanced", "reasoning"):
        for name in router.tier_names(tier):
            if name not in names:
                names.append(name)

    results: List[Dict[str, Any]] = []
    for name in names:
        one = probe_provider(name)
        one["name"] = name
        results.append(one)

    working = [r["name"] for r in results if r.get("ok") and r.get("called")]
    return {
        "ok": True,
        "probed": len(results),
        "working": working,
        "results": results,
    }


def open_result_dir(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reveal a generated project folder in Explorer.

    Only paths inside this repository are accepted: the console is bound to
    127.0.0.1, but a path from a model reply is still untrusted input and must
    not be able to launch Explorer anywhere on the machine.
    """
    raw = str(payload.get("path", "")).strip()
    if not raw:
        return {"ok": False, "error": "path is required"}
    target = os.path.abspath(raw)
    root = os.path.abspath(REPO_ROOT)
    try:
        inside = os.path.commonpath([target, root]) == root
    except ValueError:
        inside = False
    if not inside:
        return {"ok": False, "error": "path must be inside the project root"}
    if not os.path.isdir(target):
        return {"ok": False, "error": f"folder does not exist: {target}"}
    try:
        if sys.platform.startswith("win"):
            os.startfile(target)  # noqa: S606 - operator-initiated, path validated
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}
    return {"ok": True, "path": target}


def launch_run(payload: Dict[str, Any]) -> Tuple[int, Any]:
    prompt = str(payload.get("prompt", "")).strip()
    if len(prompt) < 8:
        return 400, {"error": "prompt must be at least 8 characters"}
    body = {
        "prompt": prompt,
        "project_name": payload.get("project_name") or "console-project",
        "industry": payload.get("industry") or "saas",
        "design_style": payload.get("design_style") or "auto",
        "fast_mode": bool(payload.get("fast_mode")),
    }
    status, data = agent_post("/api/generate", body, timeout=120.0)
    return status, data


def probe_provider(name: str) -> Dict[str, Any]:
    """Time one real provider call so the page shows measured latency, not guesses.

    The card the operator clicked is the provider that gets probed. Asking the
    router instead would report whichever provider happens to lead the fast tier
    (typically ninerouter) and leave every other card looking untested.
    """
    from agent.ai_routing import get_router

    requested = (name or "").strip().lower()
    started = time.time()
    router = get_router()

    if requested in ("", "active"):
        try:
            inst, resolved, tier = router.get("classify", "latency probe")
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        if inst is None:
            return {"ok": False, "error": "no provider available"}
    else:
        # Pin the requested provider: explicit wins over tier order.
        inst, resolved, tier = router.provider_by_name(requested)
        if inst is None:
            return {
                "ok": False,
                "provider": requested,
                "called": False,
                "error": f"{requested} is not available (missing key or local gateway down)",
            }

    info = {
        "ok": True,
        "tier": tier,
        "provider": resolved,
        "seconds": round(time.time() - started, 3),
        "called": False,
    }
    try:
        inst.generate_code("Reply with the single word: ok")
        info["called"] = True
        info["seconds"] = round(time.time() - started, 3)
    except Exception as exc:
        info["ok"] = False
        info["error"] = str(exc)[:200]
    return info


class ConsoleHandler(BaseHTTPRequestHandler):
    server_version = "LumicoreConsole/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write(f"[console] {self.address_string()} {fmt % args}\n")

    def _send(self, status: int, body: bytes, ctype: str, extra: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8", "replace") or "{}")
            return data if isinstance(data, dict) else {}
        except (ValueError, OSError):
            return {}

    def _asset(self, name: str) -> None:
        safe = os.path.basename(name)
        path = os.path.join(ASSET_DIR, safe)
        if not os.path.isfile(path):
            self._json({"error": "not found"}, 404)
            return
        with open(path, "rb") as fh:
            body = fh.read()
        ext = os.path.splitext(safe)[1].lower()
        self._send(200, body, CONTENT_TYPES.get(ext, "application/octet-stream"))

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                self._asset("index.html")
            elif path.startswith("/assets/"):
                self._asset(path[len("/assets/"):])
            elif path == "/api/console/overview":
                self._json(build_overview())
            elif path == "/api/console/runs":
                status, data = agent_get("/api/runs", timeout=8.0)
                self._json(data if status == 200 else {"error": data}, 200 if status == 200 else 502)
            elif path == "/api/console/probe":
                self._json(probe_provider(self.path.split("provider=", 1)[-1] if "provider=" in self.path else "active"))
            else:
                self._json({"error": "not found", "path": path}, 404)
        except Exception as exc:  # never leak a stack trace to the page
            self._json({"error": str(exc)[:300]}, 500)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        payload = self._body()
        try:
            if path == "/api/console/tiers":
                self._json(write_tiers(payload))
            elif path == "/api/console/launch":
                status, data = launch_run(payload)
                self._json(data if isinstance(data, (dict, list)) else {"raw": data}, status if status else 502)
            elif path == "/api/console/probe":
                # The page sends `provider`; `name` is accepted as an alias so a
                # caller can reuse the provider objects from /overview as-is.
                wanted = payload.get("provider") or payload.get("name") or "active"
                self._json(probe_provider(str(wanted)))
            elif path == "/api/console/probe-all":
                self._json(probe_all())
            elif path == "/api/console/open":
                self._json(open_result_dir(payload))
            else:
                self._json({"error": "not found", "path": path}, 404)
        except Exception as exc:
            self._json({"error": str(exc)[:300]}, 500)


def main() -> int:
    if not os.path.isdir(ASSET_DIR):
        print(f"error: missing asset directory {ASSET_DIR}", file=sys.stderr)
        return 1
    server = ThreadingHTTPServer(("127.0.0.1", CONSOLE_PORT), ConsoleHandler)
    print(f"LumicorePro Console  ->  http://127.0.0.1:{CONSOLE_PORT}")
    print(f"agent API           ->  {AGENT_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nconsole stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
