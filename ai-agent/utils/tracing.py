"""Distributed tracing — W3C Trace Context for the FastAPI agent.

The Express backend forwards ``traceparent`` (00-<32hex>-<16hex>-01) on every
agent call. This module parses it, keeps the current trace in a contextvar for
the whole request, and exposes helpers so provider HTTP calls can continue the
same trace. ``X-Trace-Id`` is echoed on every response.

Dependency-free on purpose: the format is 55 ASCII characters, and a contextvar
gives us async-safe propagation without middleware plumbing.
"""
from __future__ import annotations

import os
import re
import secrets
from contextvars import ContextVar
from typing import Optional, Tuple

_TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")

_current_trace: ContextVar[Optional[str]] = ContextVar("current_trace_id", default=None)
_current_span: ContextVar[Optional[str]] = ContextVar("current_span_id", default=None)


def new_span_id() -> str:
    return secrets.token_hex(8)


def new_trace_id() -> str:
    return secrets.token_hex(16)


def parse_traceparent(value: Optional[str]) -> Optional[Tuple[str, str, str]]:
    """Return (trace_id, span_id, flags) or None when malformed/absent."""
    if not value or not isinstance(value, str):
        return None
    match = _TRACEPARENT_RE.match(value.strip().lower())
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def format_traceparent(trace_id: str, span_id: str, flags: str = "01") -> str:
    return f"00-{trace_id}-{span_id}-{flags}"


def set_current_trace(trace_id: str, span_id: str) -> None:
    _current_trace.set(trace_id)
    _current_span.set(span_id)


def current_trace_id() -> Optional[str]:
    return _current_trace.get()


def trace_headers() -> dict:
    """Headers that continue the current trace on an outbound (provider) call."""
    trace_id = _current_trace.get()
    if not trace_id:
        return {}
    return {
        "traceparent": format_traceparent(trace_id, new_span_id()),
        "x-trace-id": trace_id,
    }


def tracing_enabled() -> bool:
    return os.getenv("TRACING_ENABLED", "true").strip().lower() not in ("0", "false", "no", "off")


def instrument_requests_session() -> bool:
    """Attach traceparent to every outbound `requests` call (all providers).

    Providers build their own headers per call; instead of editing 14 files we
    wrap Session.request once (idempotent) so every provider HTTP hop carries
    the active W3C trace context. Safe no-op when requests is absent.
    """
    if not tracing_enabled():
        return False
    try:
        import requests
        from requests.sessions import Session
    except ImportError:
        return False
    if getattr(Session, "_lumicore_traced", False):
        return True
    original_request = Session.request

    def traced_request(self, method, url, *args, **kwargs):
        headers = dict(kwargs.get("headers") or {})
        for key, value in trace_headers().items():
            headers.setdefault(key, value)
        kwargs["headers"] = headers
        return original_request(self, method, url, *args, **kwargs)

    Session.request = traced_request
    Session._lumicore_traced = True
    return True
