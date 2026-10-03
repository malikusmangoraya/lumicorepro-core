"""UI Library Context - stage 1 of the component graph.

Picks the components a requested UI actually needs out of a component registry and
renders them as a compact, model-readable brief. The point is that the model is
told which library components and design tokens exist, so the emitted component
reuses the real library instead of generic `<button>`/`<img>` markup that
duplicates it.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_REGISTRY = os.path.join(REPO_ROOT, "registry", "components.json")

# Words in a UI request that hint at a registry category. Kept small and explicit:
# an over-eager synonym table silently drags in irrelevant components, which is
# worse than asking the model to compose from what is offered.
CATEGORY_HINTS: Dict[str, Sequence[str]] = {
    "auth": ("login", "signin", "sign in", "register", "signup", "sign up", "password", "otp"),
    "ecommerce": ("cart", "product", "checkout", "order", "wishlist", "shop", "store", "price",
                  "pricing", "catalog", "catalog"),
    "dashboard": ("dashboard", "analytics", "kpi", "chart", "metric", "revenue", "admin"),
    "forms": ("form", "input", "field", "validation", "submit", "contact", "newsletter"),
    "navigation": ("nav", "navbar", "menu", "breadcrumb", "sidebar", "header", "footer"),
    "common": ("card", "modal", "badge", "avatar", "tooltip", "accordion", "tabs"),
    # Vertical categories: without these a perfectly ordinary request such as
    # "pricing page" or "hotel booking" inferred no category at all and the
    # emitter lost the library context that made stage 1 worth running.
    "saas": ("saas", "plan", "plans", "subscription", "billing", "trial", "workspace", "b2b"),
    "fintech": ("fintech", "invoice", "wallet", "loan", "invest", "payout", "ledger"),
    "healthcare": ("appointment", "patient", "clinic", "doctor", "dental", "prescription"),
    "real-estate": ("property", "realty", "realtor", "viewing", "villa", "apartment"),
    "hospitality": ("hotel", "booking", "room", "stay", "resort", "guest"),
    "food": ("menu", "recipe", "cuisine", "dish", "reservation", "cafe", "bakery"),
    "fashion": ("apparel", "outfit", "collection", "lookbook", "wardrobe", "boutique"),
    "electronics": ("device", "gadget", "hardware", "specs", "charger", "laptop"),
    "sports": ("workout", "gym", "training", "athlete", "fitness", "match"),
    "education": ("course", "lesson", "curriculum", "student", "tutor", "academy"),
    "entertainment": ("event", "ticket", "concert", "cinema", "gallery"),
}

# Design tokens the emitter is allowed to reference. Anything outside this list
# ends up as a hardcoded hex in the output, which is exactly what the token system
# exists to prevent.
ALLOWED_TOKENS: Sequence[str] = (
    "--t-bg", "--t-surface", "--t-surface-2", "--t-line", "--t-text", "--t-muted",
    "--t-brand", "--t-accent", "--t-ok", "--t-warn", "--t-err", "--t-focus",
    "--t-radius", "--t-radius-sm", "--t-shadow", "--t-font", "--t-mono",
)


def load_registry(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read the component registry, tolerating a missing or corrupt file."""
    target = path or DEFAULT_REGISTRY
    try:
        with open(target, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("components", [])
    return [c for c in data if isinstance(c, dict) and c.get("name")]


def infer_categories(request: str, explicit: Optional[Iterable[str]] = None) -> List[str]:
    """Map a free-text UI request onto registry categories."""
    cats: List[str] = []
    for cat in explicit or ():
        if cat and cat not in cats:
            cats.append(cat)
    text = (request or "").lower()
    for cat, hints in CATEGORY_HINTS.items():
        if cat in cats:
            continue
        if any(h in text for h in hints):
            cats.append(cat)
    return cats


def _score(component: Dict[str, Any], request: str, categories: Sequence[str]) -> int:
    """Rank a component against the request. Higher is better."""
    score = 0
    cat = str(component.get("category", ""))
    if cat in categories:
        score += 5
    tags = [str(t).lower() for t in component.get("tags", []) or []]
    words = set(re.findall(r"[a-z0-9]+", (request or "").lower()))
    if words:
        overlap = sum(1 for t in tags if t in words or any(t in w for w in words))
        score += overlap
    name = str(component.get("name", "")).lower()
    if name and (name in (request or "").lower()):
        score += 3
    feats = component.get("features", []) or []
    score += min(len(feats), 3)
    if component.get("file_path"):
        score += 1
    return score


def select_components(
    registry: Sequence[Dict[str, Any]],
    request: str,
    categories: Sequence[str],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    scored = [(c, _score(c, request, categories)) for c in registry]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda pair: (-pair[1], str(pair[0].get("name", ""))))
    return [c for c, _ in scored[:limit]]


def build_context_prompt(
    request: str,
    components: Sequence[Dict[str, Any]],
    categories: Sequence[str],
    extra: str = "",
) -> str:
    """Render the injected context as a prompt block for the emitting model."""
    lines: List[str] = [
        "UI LIBRARY CONTEXT (reuse these; do not reimplement them)",
        "Categories: " + (", ".join(categories) if categories else "general"),
    ]
    if components:
        lines.append("Available components:")
        for c in components:
            deps = ", ".join(c.get("dependencies", []) or []) or "react"
            feats = ", ".join(c.get("features", []) or []) or "-"
            lines.append(
                "- <{name}> from {path} | props: {feats} | deps: {deps} | {desc}".format(
                    name=c.get("name", "?"),
                    path=c.get("file_path", "?"),
                    feats=feats,
                    deps=deps,
                    desc=str(c.get("description", "")).strip() or "-",
                )
            )
    else:
        lines.append("Available components: (none matched - use semantic HTML with Tailwind)")
    lines.append("")
    lines.append("Design tokens (use var(...), never raw hex): " + ", ".join(ALLOWED_TOKENS))
    if extra:
        lines.append("")
        lines.append(extra)
    lines.append("")
    lines.append("Request: " + (request or "").strip())
    return "\n".join(lines)


def inject_ui_context(
    request: str,
    categories: Optional[Iterable[str]] = None,
    limit: int = 8,
    registry_path: Optional[str] = None,
    extra: str = "",
) -> Dict[str, Any]:
    """Node 1. Returns the selected library context for a requested UI."""
    cats = infer_categories(request, categories)
    registry = load_registry(registry_path)
    components = select_components(registry, request, cats, limit=limit)
    return {
        "request": request,
        "categories": cats,
        "components": components,
        "component_names": [c.get("name") for c in components],
        "tokens": list(ALLOWED_TOKENS),
        "prompt": build_context_prompt(request, components, cats, extra=extra),
        "registry_size": len(registry),
    }
