"""Layout Base - stage 2 of the component graph.

Produces the structural skeleton a component must fill: which regions exist, in
what order, and what each region's job is. Separating structure from markup means
the layout is deterministic and reviewable, and the model only has to solve the
part that actually needs judgement - the JSX inside known regions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

# Region catalogue. `weight` is the share of vertical space the region is
# expected to take, which the emitter uses to keep proportions honest instead of
# producing a component that is 90% header.
REGION_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "header": {"weight": 15, "a11y": "banner landmark", "job": "identity + primary action"},
    "nav": {"weight": 10, "a11y": "navigation landmark", "job": "wayfinding between sections"},
    "hero": {"weight": 35, "a11y": "single h1", "job": "one promise, one primary CTA"},
    "content": {"weight": 25, "a11y": "main landmark", "job": "the substance"},
    "aside": {"weight": 15, "a11y": "complementary landmark", "job": "supporting or upsell"},
    "footer": {"weight": 12, "a11y": "contentinfo landmark", "job": "secondary links + legal"},
}

LAYOUT_PRESETS: Dict[str, Sequence[str]] = {
    "single": ("hero", "content"),
    "section": ("header", "hero", "content", "footer"),
    "page": ("header", "nav", "hero", "content", "footer"),
    "dashboard": ("header", "nav", "content", "aside"),
    "form": ("header", "content", "footer"),
    "landing": ("header", "nav", "hero", "content", "aside", "footer"),
}


def resolve_regions(layout: str = "auto", request: str = "") -> List[str]:
    """Pick a region list, inferring the preset when the caller said `auto`."""
    key = (layout or "auto").strip().lower()
    if key in LAYOUT_PRESETS:
        return list(LAYOUT_PRESETS[key])
    text = (request or "").lower()
    if any(w in text for w in ("dashboard", "admin", "analytics", "kpi", "chart")):
        return list(LAYOUT_PRESETS["dashboard"])
    if any(w in text for w in ("form", "signup", "login", "contact", "checkout")):
        return list(LAYOUT_PRESETS["form"])
    if any(w in text for w in ("landing", "marketing", "homepage", "home page")):
        return list(LAYOUT_PRESETS["landing"])
    return list(LAYOUT_PRESETS["page"])


def _wireframe(regions: Sequence[str]) -> str:
    """A readable ASCII wireframe, so the structure is reviewable in a diff."""
    total = sum(REGION_CATALOGUE.get(r, {}).get("weight", 10) for r in regions) or 1
    out: List[str] = []
    for region in regions:
        info = REGION_CATALOGUE.get(region, {})
        bars = max(1, round(info.get("weight", 10) / total * 24))
        out.append("  |" + ("-" * bars) + "|  %-7s %s" % (region, info.get("job", "")))
    return "\n".join(out)


def render_layout_base(
    layout: str = "auto",
    request: str = "",
    component_name: str = "GeneratedComponent",
    max_regions: int = 6,
) -> Dict[str, Any]:
    """Node 2. Returns the deterministic layout skeleton."""
    regions = resolve_regions(layout, request)[: max(1, max_regions)]
    described = [
        {
            "name": r,
            "weight": REGION_CATALOGUE.get(r, {}).get("weight", 10),
            "a11y": REGION_CATALOGUE.get(r, {}).get("a11y", ""),
            "job": REGION_CATALOGUE.get(r, {}).get("job", ""),
        }
        for r in regions
    ]
    return {
        "layout": layout,
        "component_name": component_name,
        "regions": regions,
        "region_spec": described,
        "wireframe": _wireframe(regions),
        "guidance": _guidance(described),
    }


def _guidance(regions: Sequence[Dict[str, Any]]) -> str:
    lines = [
        "LAYOUT BASE (fill every region; do not add or drop regions)",
        "Wireframe:",
        "  " + "\n  ".join(
            "%-7s %s" % (r["name"], "- " * max(1, r["weight"] // 4) + " " + r["job"]) for r in regions
        ),
        "",
    ]
    lines.append("Per-region requirements:")
    for r in regions:
        lines.append("- <%s>: %s%s" % (r["name"], r["job"], (" | a11y: " + r["a11y"]) if r["a11y"] else ""))
    lines.append("")
    lines.append(
        "Rules: exactly one h1 in the whole component; every region needs a landmark or "
        "labelled section; keep region weights roughly proportional; no raw hex colours."
    )
    return "\n".join(lines)
