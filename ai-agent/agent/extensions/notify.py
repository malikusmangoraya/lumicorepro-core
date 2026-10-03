"""Platform outbound webhooks — notify external URLs when agent events happen.

Store is a JSON file next to the agent root (`runtime/webhooks.json`), so
users can plug the agent into Zapier/Make/n8n/Slack without code changes.
Delivery is best-effort: background thread, bounded retries, HMAC-SHA256
signed bodies. Never blocks the pipeline and never raises from the caller.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

DEFAULT_EVENTS = ("run.completed", "deploy.completed", "qa.completed")

_store_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "runtime",
    "webhooks.json",
)


def _ensure_store_dir() -> None:
    os.makedirs(os.path.dirname(_store_path), exist_ok=True)


def get_webhooks() -> List[Dict[str, Any]]:
    try:
        if os.path.isfile(_store_path):
            with open(_store_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                hooks = data.get("webhooks")
                if isinstance(hooks, list):
                    return [h for h in hooks if isinstance(h, dict) and str(h.get("url", "")).startswith(("http://", "https://"))]
        return []
    except Exception as exc:  # noqa: BLE001
        agent_logger.warning(f"Webhook store read failed: {exc}")
        return []


def set_webhooks(urls: List[str]) -> Dict[str, Any]:
    """Replace the webhook list. Accepts raw URLs; normalizes + validates."""
    clean: List[Dict[str, Any]] = []
    for raw in (urls or []):
        url = str(raw or "").strip()
        if url.startswith(("http://", "https://")):
            clean.append({"url": url, "events": list(DEFAULT_EVENTS), "enabled": True})
    try:
        _ensure_store_dir()
        with open(_store_path, "w", encoding="utf-8") as fh:
            json.dump({"webhooks": clean}, fh, indent=2)
        agent_logger.info(f"Webhooks updated: {len(clean)} endpoint(s)")
        return {"status": "ok", "webhooks": [h["url"] for h in clean], "store": _store_path}
    except Exception as exc:  # noqa: BLE001
        agent_logger.error(f"Webhook store write failed: {exc}")
        return {"status": "failed", "message": str(exc)}


def _body_signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _post(url: str, payload: Dict[str, Any], secret: str) -> bool:
    body = json.dumps(payload, default=str).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "LumicorePro-Agent/6.5",
            "X-LumicorePro-Signature": f"sha256={_body_signature(body, secret)}",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 (user-configured URL)
        return 200 <= resp.status < 300


def _deliver(url: str, event: str, payload: Dict[str, Any], secret: str) -> None:
    """Bounded retry delivery (3 attempts, backoff). Runs in a background thread."""
    for attempt in range(1, 4):
        try:
            ok = _post(url, payload, secret)
            agent_logger.info(f"Webhook {event} delivered to {url} (attempt {attempt}): ok={ok}")
            return
        except Exception as exc:  # noqa: BLE001
            agent_logger.warning(f"Webhook {event} → {url} attempt {attempt} failed: {exc}")
            time.sleep(min(2 ** attempt, 5))


def notify(event: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fire `event` to all enabled webhooks (non-blocking, best-effort)."""
    hooks = get_webhooks()
    if not hooks:
        return {"status": "skipped", "reason": "no webhooks configured"}
    enabled = [h for h in hooks if h.get("enabled", True)]
    if not enabled:
        return {"status": "skipped", "reason": "all webhooks disabled"}
    secret = os.environ.get("AI_AGENT_WEBHOOK_SECRET", "lumicorepro-local")
    payload = {
        "event": event,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent": "lumicorepro",
        "data": data or {},
    }
    for hook in enabled:
        t = threading.Thread(
            target=_deliver, args=(hook["url"], event, payload, secret), daemon=True
        )
        t.start()
    return {"status": "queued", "delivered_to": len(enabled), "event": event}


def test_notify(url: Optional[str] = None) -> Dict[str, Any]:
    """Send a test event to the first configured webhook (or the given URL)."""
    if not url:
        hooks = get_webhooks()
        url = hooks[0]["url"] if hooks else None
    if not url:
        return {"status": "failed", "message": "No webhook configured"}
    payload = {"event": "test.ping", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "data": {"message": "ping"}}
    try:
        ok = _post(url, payload, os.environ.get("AI_AGENT_WEBHOOK_SECRET", "lumicorepro-local"))
        return {"status": "ok" if ok else "failed", "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "message": str(exc), "url": url}