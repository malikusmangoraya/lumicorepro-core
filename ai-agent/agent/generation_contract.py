"""Versioned delivery contract shared by generated-project pipelines."""
from typing import Any

from .project_mode_engine import MODE_CLIENT_STATIC, MODE_ENTERPRISE, ProjectModeEngine


CONTRACT_VERSION = 1
_PAYMENT_FEATURES = {
    "payments",
    "stripe_payments",
    "paypal_payments",
    "checkout",
    "subscriptions",
}
_BASELINE_FEATURES = ["jwt_auth", "users", "contact"]


def resolve_generation_contract(spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve delivery defaults and explicit product capabilities from a spec."""
    normalized_spec = dict(spec) if isinstance(spec, dict) else {}
    requested_mode = str(normalized_spec.get("layout_mode") or "").strip().lower()
    if requested_mode in {"client-static", "static", "static-only"}:
        normalized_spec.setdefault("buyer_type", "client-static")
    mode = ProjectModeEngine().select_mode(normalized_spec)
    raw_features = normalized_spec.get("features") or []
    if isinstance(raw_features, str):
        raw_features = [raw_features]
    elif not isinstance(raw_features, (list, tuple, set)):
        raw_features = []

    features = list(dict.fromkeys(
        str(feature).strip().lower()
        for feature in raw_features
        if str(feature).strip()
    ))
    if mode == MODE_ENTERPRISE:
        features = list(dict.fromkeys(_BASELINE_FEATURES + features))
    else:
        features = [feature for feature in features if feature not in _BASELINE_FEATURES]

    requirements = [feature for feature in features if feature in _PAYMENT_FEATURES]
    return {
        "version": CONTRACT_VERSION,
        "layout_mode": mode,
        "database": "postgresql" if mode == MODE_ENTERPRISE else None,
        "auth": mode == MODE_ENTERPRISE,
        "features": features,
        "requirements": requirements,
    }
