"""Versioned delivery contract shared by generated-project pipelines."""
import re
from typing import Any

from .project_mode_engine import MODE_CLIENT_STATIC, MODE_ENTERPRISE, ProjectModeEngine


SCENE_ARCHETYPES = ('floating_crystal', 'cyber_grid', 'particle_cosmos', 'product_viewer')


def resolve_scene_request(prompt: str = '', scene=None) -> dict[str, Any] | None:
    """Normalize optional 3D intent; model paths are for trusted local callers only.

    Asset contents are validated by the scene emitter, not by this pure resolver.
    No input values are included in validation errors.
    """
    if scene is None:
        text = prompt if isinstance(prompt, str) else ''
        intent = re.search(r'\b(?:3[ -]?d|webgl|three\.js|model[ -]viewer)\b', text, re.I)
        if not intent:
            return None
        # Only an explicit showroom/model-viewer asks for a supplied model; a
        # generic "3D hero for our product" must stay procedural.
        showroom = re.search(r'\b(?:showroom|model[ -]viewer)\b', text, re.I)
        scene = {'archetype': 'product_viewer' if showroom else 'floating_crystal'}
    if not isinstance(scene, dict) or set(scene) - {'archetype', 'model_path'}:
        raise ValueError('Scene must contain a supported archetype and optional local model_path.')
    archetype = scene.get('archetype')
    if not isinstance(archetype, str) or archetype.strip().lower() not in SCENE_ARCHETYPES:
        raise ValueError('Unsupported scene archetype; select a supported genuine 3D scene.')
    archetype = archetype.strip().lower()
    result = {'archetype': archetype}
    if archetype == 'product_viewer':
        model = scene.get('model_path')
        if not isinstance(model, str) or not model.strip() or '\x00' in model:
            raise ValueError('Product scene requires a trusted local GLB/GLTF model_path.')
        result['model_path'] = model.strip()
    elif 'model_path' in scene:
        raise ValueError('A model_path is only supported for the product_viewer scene.')
    return result


CONTRACT_VERSION = 1
_PAYMENT_FEATURES = {
    "payments",
    "stripe_payments",
    "paypal_payments",
    "checkout",
    "subscriptions",
}
_BASELINE_FEATURES = ["jwt_auth", "users", "contact"]

APP_WEB_SURFACES = ("website", "web_app", "none")
APP_MOBILE_PLATFORMS = ("android", "ios")
APP_VERIFICATIONS = ("apk_emulator", "none")

_WEB_APP_PHRASES = (
    "web app",
    "internal app",
    "admin app",
    "admin dashboard",
    "management app",
    "management system",
)
_WEB_INTENT_RE = re.compile(
    r"\b(?:website|web site|landing page|storefront|web app|internal app|admin app|"
    r"admin dashboard|management app|management system|web)\b"
)
_MOBILE_INTENT_RE = re.compile(
    r"\b(?:mobile app|android app|ios app|react native|mobile application)\b"
)
# "web and mobile" / "mobile + web" names both surfaces without the word "app".
_BOTH_SURFACES_RE = re.compile(
    r"\b(?:(?:website|web site|web)\s+(?:and|\+|plus)\s+mobile"
    r"|mobile\s+(?:and|\+|plus)\s+(?:website|web site|web))\b"
)
# A standalone "app" is a mobile request; "web app", "internal app", "admin app"
# and "management app" are web surfaces, not mobile requests.
_STANDALONE_APP_RE = re.compile(
    r"(?<!web )(?<!internal )(?<!admin )(?<!management )\bapp\b"
)
_PWA_INTENT_RE = re.compile(r"\b(?:pwa|installable|offline app)\b")
_DASHBOARD_RE = re.compile(r"\bdashboard\b")
_BOTH_CUE_RE = re.compile(r"\bboth\b")


def _app_from_prompt(prompt: str) -> dict[str, Any] | None:
    """Resolve requested surfaces from prompt words; no app block for a website."""
    text = str(prompt or "").lower()
    mobile_intent = bool(
        _MOBILE_INTENT_RE.search(text)
        or _BOTH_SURFACES_RE.search(text)
        or _STANDALONE_APP_RE.search(text)
    )
    web_intent = bool(_WEB_INTENT_RE.search(text))
    web_app_intent = any(phrase in text for phrase in _WEB_APP_PHRASES)
    if not mobile_intent and not web_intent and _BOTH_CUE_RE.search(text):
        # A bare "both" names no surface itself; per the spec table it means
        # the website and the mobile app, never a silent single surface.
        mobile_intent = True
        web_intent = True
    if mobile_intent and not web_intent and _DASHBOARD_RE.search(text):
        # "dashboard and mobile app" names both surfaces; a dashboard is an app
        # shell, not the marketing website lane.
        web_intent = True
        web_app_intent = True
    pwa = bool(_PWA_INTENT_RE.search(text))
    if not mobile_intent and not web_intent:
        return None
    web = "none"
    if web_intent:
        web = "web_app" if web_app_intent else "website"
    mobile = ({"platforms": ["android"], "verification": "apk_emulator"}
              if mobile_intent else None)
    if web == "website" and not pwa and mobile is None:
        # A plain website request is the existing lane, not an app request.
        return None
    return {"web": web, "pwa": pwa, "mobile": mobile}


def resolve_app_request(spec: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize the requested app surfaces; errors never echo the input value."""
    raw = spec.get("app")
    prompt = str(spec.get("prompt") or "")
    if raw is None:
        raw = _app_from_prompt(prompt)
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) - {"web", "pwa", "mobile"}:
        raise ValueError("App request must contain web, pwa or mobile.")
    web = str(raw.get("web") or "none").strip().lower()
    if web not in APP_WEB_SURFACES:
        raise ValueError("Unsupported web surface.")
    pwa = raw.get("pwa", False)
    if not isinstance(pwa, bool):
        raise ValueError("App pwa must be a boolean.")
    if pwa and web == "none":
        raise ValueError("PWA requires a web surface.")
    mobile = raw.get("mobile")
    if mobile is not None:
        if not isinstance(mobile, dict) or set(mobile) - {"platforms", "verification"}:
            raise ValueError("Invalid mobile surface.")
        platforms = mobile.get("platforms") or ["android"]
        if not isinstance(platforms, list) or not platforms:
            raise ValueError("Unsupported mobile platform.")
        try:
            unsupported = set(platforms) - set(APP_MOBILE_PLATFORMS)
        except TypeError:
            raise ValueError("Unsupported mobile platform.") from None
        if unsupported:
            raise ValueError("Unsupported mobile platform.")
        verification = str(mobile.get("verification") or "apk_emulator").lower()
        if verification not in APP_VERIFICATIONS:
            raise ValueError("Unsupported mobile verification.")
        mobile = {"platforms": platforms, "verification": verification}
    if web == "none" and mobile is None:
        raise ValueError("An app request needs a web or mobile surface.")
    return {"web": web, "pwa": pwa, "mobile": mobile}


def resolve_generation_contract(spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve delivery defaults, explicit capabilities and requested app surfaces."""
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
    contract = {
        "version": CONTRACT_VERSION,
        "layout_mode": mode,
        "database": "postgresql" if mode == MODE_ENTERPRISE else None,
        "auth": mode == MODE_ENTERPRISE,
        "features": features,
        "requirements": requirements,
    }
    scene = resolve_scene_request(normalized_spec.get('prompt', ''), normalized_spec.get('scene'))
    if scene is not None:
        contract['scene'] = scene
    app = resolve_app_request(normalized_spec)
    if app is not None:
        contract["app"] = app
    return contract
