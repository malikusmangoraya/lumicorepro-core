"""Generation status vocabulary — one definition shared by pipeline and API.

Why this exists
---------------
A run used to report `succeeded` / `partial` / `failed` and nothing else, so a
build that produced every artifact from deterministic local rules looked exactly
like a build served by a real model. Monitoring could not tell them apart and a
client could not tell whether an AI provider had answered at all.

Every generation response and every run record now carries:

``status``
    one of :data:`GENERATION_STATUSES`
``providers_used``
    names of the providers that actually produced output for this response
``fallback_used``
    True when the output came from a deterministic local path instead of a live
    model (a missing key, an unreachable provider, or an endpoint that is
    deterministic by design)
``reason``
    machine-readable code (one of the ``REASON_*`` constants) explaining a
    fallback / partial status; ``None`` when a live model served the request
``skipped_phases``
    ``[{"phase": …, "reason": …}]`` for every phase that was skipped

Backwards compatibility: `status` keeps its old spellings for the old cases
(`succeeded`, `partial`, `failed`), so a client that reads `status` still works;
`succeeded_with_skips` is the new value for "nothing failed but something was
skipped".
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

STATUS_SUCCEEDED = "succeeded"
STATUS_SUCCEEDED_WITH_SKIPS = "succeeded_with_skips"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"

#: The complete, closed status vocabulary.
GENERATION_STATUSES = (
    STATUS_SUCCEEDED,
    STATUS_SUCCEEDED_WITH_SKIPS,
    STATUS_PARTIAL,
    STATUS_FAILED,
)

# ── machine-readable fallback reasons ───────────────────────────────────────
#: `AI_OFFLINE=1` — the product-level local-first switch.
REASON_AI_OFFLINE = "ai_offline"
#: No provider could be resolved (missing/placeholder keys, empty pool).
REASON_NO_PROVIDER = "no_provider_configured"
#: A provider was resolved but every call to it failed.
REASON_PROVIDER_FAILED = "provider_calls_failed"
#: A provider was resolved; nothing in this run actually needed a model call.
REASON_NO_MODEL_CALL = "no_model_call_made"
#: The endpoint/engine is deterministic by design (no model is involved).
REASON_DETERMINISTIC_ENGINE = "deterministic_engine"
#: Vision fell back to layout heuristics instead of a vision model.
REASON_VISION_FALLBACK = "vision_fallback_heuristic"
#: Generic deterministic local fallback (repair/iterate paths).
REASON_LOCAL_FALLBACK = "deterministic_local_fallback"


def resolve_status(*, failed: bool = False, skipped: bool = False) -> str:
    """Collapse "did anything fail / was anything skipped" into one status value.

    Failure outranks a skip: a run with both a failed phase and a skipped phase
    is `partial`, not `succeeded_with_skips`.
    """
    if failed:
        return STATUS_PARTIAL
    if skipped:
        return STATUS_SUCCEEDED_WITH_SKIPS
    return STATUS_SUCCEEDED


def fallback_reason(
    *,
    offline: bool = False,
    provider_resolved: bool = False,
    calls_succeeded: int = 0,
    calls_failed: int = 0,
) -> Optional[str]:
    """Reason code for the deterministic path, or None when a model answered.

    Precedence is the honest one: an offline switch or a missing provider is a
    configuration fact, a failed call is a runtime fact, and "nothing needed a
    model" is the remaining, non-alarming case.
    """
    if calls_succeeded > 0:
        return None
    if offline:
        return REASON_AI_OFFLINE
    if not provider_resolved:
        return REASON_NO_PROVIDER
    if calls_failed > 0:
        return REASON_PROVIDER_FAILED
    return REASON_NO_MODEL_CALL


def skipped_phase(phase: str, reason: str) -> Dict[str, str]:
    """One `{phase, reason}` entry for the `skipped_phases` list."""
    return {"phase": str(phase), "reason": str(reason)}


def status_block(
    *,
    status: str,
    providers_used: Optional[Iterable[str]] = None,
    fallback_used: bool = False,
    reason: Optional[str] = None,
    skipped_phases: Optional[Iterable[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """The five status fields every generation response/run record must carry.

    `status` is validated against the vocabulary so a new spelling cannot leak
    into the API unnoticed; an unknown value is reported as `partial` (the honest
    "something is off" fallback) rather than being echoed to clients.
    """
    resolved = status if status in GENERATION_STATUSES else STATUS_PARTIAL
    used: List[str] = []
    for name in providers_used or ():
        text = str(name or "").strip()
        if text and text not in used and text not in ("none", "offline"):
            used.append(text)
    return {
        "status": resolved,
        "providers_used": used,
        "fallback_used": bool(fallback_used),
        "reason": reason,
        "skipped_phases": [
            dict(entry) for entry in (skipped_phases or ()) if isinstance(entry, dict)
        ],
    }
