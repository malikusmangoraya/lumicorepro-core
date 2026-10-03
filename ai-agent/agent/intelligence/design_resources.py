"""Design Resources catalog — open-source build blocks for LumicorePro.

Registers an on-disk catalog (``registry/design-resources.json``) of
open-source component libraries, design systems, galleries and curated
lists that Lumicore-generated projects may *reference for inspiration*.

Rule (mirrors Reference Intelligence): a resource is decomposed into design
attributes only — never copied. Profiles follow the same 18-attribute schema
as :mod:`agent.intelligence.reference_intelligence` so results merge cleanly.

Deterministic and offline: catalog lives in the repo, no provider required.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lumicorepro.design_resources")

# Attribute keys understood by the rest of the design pipeline
KNOWN_ATTRIBUTES = frozenset({
    "minimalism", "whitespace", "typography", "motion", "visual_density",
    "content_density", "image_dominance", "color_saturation", "warmth",
    "luxury", "cinematic", "bold", "futuristic", "interaction_complexity",
    "craft", "dark_canvas", "navigation", "cta_focus",
})

_CATALOG_CACHE: Optional[List[Dict[str, Any]]] = None


def _catalog_candidates() -> List[Path]:
    """Locate registry/design-resources.json relative to known roots."""
    here = Path(__file__).resolve()
    roots = [
        here.parents[2],   # ai-agent/  -> ai-agent/registry
        here.parents[3],   # repo root -> registry
        Path.cwd(),
    ]
    seen: List[Path] = []
    for root in roots:
        for rel in ("registry", "ai-agent/registry"):
            p = root / rel / "design-resources.json"
            if p.is_file() and p not in seen:
                seen.append(p)
    return seen


def _catalog_path() -> Optional[Path]:
    paths = _catalog_candidates()
    return paths[0] if paths else None


def load_catalog(refresh: bool = False) -> List[Dict[str, Any]]:
    """Load the design-resources catalog as a JSON array.

    Returns [] (never raises) when the catalog is missing or malformed so the
    pipeline stays nominal — callers may then fall back on built-in profiles.
    """
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not refresh:
        return _CATALOG_CACHE

    path = _catalog_path()
    if path is None:
        logger.warning("design-resources catalog not found; using empty list")
        _CATALOG_CACHE = []
        return _CATALOG_CACHE

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        resources = data.get("resources", []) if isinstance(data, dict) else []
        if not isinstance(resources, list):
            resources = []
        _CATALOG_CACHE = resources
    except Exception as exc:  # pragma: no cover - corrupt local file
        logger.warning("design-resources catalog unreadable: %s", exc)
        _CATALOG_CACHE = []
    return _CATALOG_CACHE


def resource_profiles() -> Dict[str, Dict[str, float]]:
    """Map resource slug -> attribute profile (18-key schema compatible)."""
    profiles: Dict[str, Dict[str, float]] = {}
    for item in load_catalog():
        slug = item.get("slug")
        attrs = item.get("attributes") or {}
        if not slug or not isinstance(attrs, dict):
            continue
        clean = {k: round(float(v), 2) for k, v in attrs.items()
                 if k in KNOWN_ATTRIBUTES}
        if clean:
            profiles[slug] = clean
    return profiles


def _slug_words(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ")


def _tokens(item: Dict[str, Any]) -> List[str]:
    """Lowercased match tokens: slug, name, keywords (hyphens normalized)."""
    tokens = [_slug_words(str(item.get("slug", ""))),
              _slug_words(str(item.get("name", "")))]
    for kw in (item.get("keywords") or []):
        tokens.append(_slug_words(str(kw)))
    return [t for t in tokens if t]


def resolve_references(text: str) -> List[Dict[str, Any]]:
    """Match a prompt string against catalog resources.

    Returns matched resources with their attribute profile, best-match scored
    by longest matched token so "Magic UI" wins over bare "UI".
    """
    if not text:
        return []
    hay = text.lower()
    hay_words = _slug_words(hay).split()
    scored: List[tuple] = []
    for item in load_catalog():
        best = 0.0
        for token in _tokens(item):
            token_words = token.split()
            if token in hay:
                best = max(best, len(token_words))
                continue
            overlap = sum(1 for w in token_words if w in hay_words)
            if overlap and overlap >= min(2, len(token_words)) and not token_words == ["ui"]:
                best = max(best, overlap)
        if not best:
            continue
        attrs = {k: round(float(v), 2) for k, v in
                 (item.get("attributes") or {}).items()
                 if k in KNOWN_ATTRIBUTES}
        scored.append((best, {
            "slug": item.get("slug"),
            "name": item.get("name"),
            "role": item.get("role"),
            "license": item.get("license"),
            "url": item.get("url"),
            "attributes": attrs,
        }))
    scored.sort(key=lambda t: -t[0])
    return [entry for _, entry in scored]


def merge_profiles(matches: List[Dict[str, Any]]) -> Dict[str, float]:
    """Blend matched resource profiles into one max-merged attribute set."""
    merged: Dict[str, float] = {}
    for entry in matches:
        for key, value in (entry.get("attributes") or {}).items():
            merged[key] = max(merged.get(key, 0.0), float(value))
    return {k: round(float(v), 2) for k, v in merged.items()}


def resource_contribution(text: str) -> Dict[str, Any]:
    """Public helper: resources matched by a prompt + merged attributes."""
    matches = resolve_references(text)
    return {
        "matched": [
            {k: v for k, v in m.items() if k != "attributes"} for m in matches
        ],
        "attributes": merge_profiles(matches),
        "count": len(matches),
    }


def verify_catalog() -> Dict[str, Any]:
    """Self-check: report catalog health, slugs, licenses, attribute keys."""
    resources = load_catalog(refresh=True)
    slugs = [r.get("slug") for r in resources if r.get("slug")]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    bad_attrs = [
        (r.get("slug"), sorted(set((r.get("attributes") or {})) - KNOWN_ATTRIBUTES))
        for r in resources if set((r.get("attributes") or {})) - KNOWN_ATTRIBUTES
    ]
    no_url = [r.get("slug") for r in resources if not r.get("url")]
    return {
        "found": bool(_catalog_path() is not None),
        "path": str(_catalog_path() or ""),
        "count": len(resources),
        "roles": {role: sum(1 for r in resources if r.get("role") == role)
                  for role in sorted({r.get("role") for r in resources})},
        "licenses": sorted({str(r.get("license")) for r in resources}),
        "duplicate_slugs": dupes,
        "invalid_attribute_keys": bad_attrs,
        "missing_url": no_url,
        "ok": (
            bool(resources)
            and not dupes
            and not bad_attrs
            and not no_url
        ),
    }


__all__ = [
    "KNOWN_ATTRIBUTES",
    "load_catalog",
    "merge_profiles",
    "resource_contribution",
    "resource_profiles",
    "resolve_references",
    "verify_catalog",
]