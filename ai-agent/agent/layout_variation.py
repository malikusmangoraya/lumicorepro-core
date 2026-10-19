"""Layout Variation Engine — deterministic anti-sameness for generated projects.

Every generated project used to ship the identical Home skeleton: same cyan
accent, same slate surfaces, same section order (Hero → Features →
Testimonials → Pricing → FAQ → CTA). This module breaks the mirror-image
problem by selecting, per project, a visual profile from 3 independent axes:

  1. Accent palette  — cyan is rotated out in favour of 8 other families
                       (teal, emerald, indigo, violet, fuchsia, rose, amber, sky).
  2. Surface tone    — the neutral dark family (slate) is rotated across
                       zinc / stone / neutral.
  3. Section order   — the Testimonials/Pricing/FAQ band is permuted
                       (6 orders), so scroll rhythm differs page to page.

Selection is a sha256(seed) — stable for a given project slug — but callers
may pass ``avoid_previous=True`` so two projects built back-to-back never
share a profile. The sweep is a post-write string pass over the generated
frontend: no JSX structure is touched, only Tailwind family tokens, so
generated projects stay lint/build-compatible.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# All family names valid in Tailwind (project uses Tailwind 3 tokens).
ACCENT_PALETTES: tuple[str, ...] = (
    "teal", "emerald", "indigo", "violet", "fuchsia", "rose", "amber", "sky",
)

SURFACE_FAMILIES: tuple[str, ...] = ("slate", "zinc", "stone", "neutral")

SECTION_ORDERS: tuple[tuple[str, str, str], ...] = (
    ("testimonials", "pricing", "faq"),      # canonical baseline
    ("pricing", "testimonials", "faq"),
    ("testimonials", "faq", "pricing"),
    ("faq", "testimonials", "pricing"),
    ("pricing", "faq", "testimonials"),
    ("faq", "pricing", "testimonials"),
)

#: Hero gradient chains chosen per palette (from / via / to). The original
#: template hard-coded cyan-400 → teal-300 → violet-500.
GRADIENT_CHAINS: Dict[str, tuple[str, str, str]] = {
    "teal": ("teal-300", "emerald-400", "cyan-500"),
    "emerald": ("emerald-300", "teal-400", "sky-500"),
    "indigo": ("indigo-300", "violet-400", "fuchsia-500"),
    "violet": ("violet-300", "fuchsia-400", "rose-500"),
    "fuchsia": ("fuchsia-300", "rose-400", "orange-500"),
    "rose": ("rose-300", "pink-400", "fuchsia-500"),
    "amber": ("amber-300", "orange-400", "rose-500"),
    "sky": ("sky-300", "blue-400", "indigo-500"),
}

_DEFAULT_GRADIENT = ("cyan-400", "teal-300", "violet-500")

_GRADIENT_RE = re.compile(
    r"from-(?:cyan|teal|sky|indigo)-[3-5]00 via-(?:teal|emerald|blue)-300 to-(?:violet|fuchsia)-500"
)

_HERO_GRADIENT_SEQUENCE = (
    f"from-{_DEFAULT_GRADIENT[0]} via-{_DEFAULT_GRADIENT[1]} to-{_DEFAULT_GRADIENT[2]}",
)

# Tailwind numeric shades that appear in the generated templates.
# Descending so a longer token (cyan-500) is fully replaced before a shorter
# prefix (cyan-50) could corrupt it.
_SHADES = (
    "950", "900", "800", "700", "600", "500", "400", "300", "200", "100", "50",
)

# Module-level anti-repeat memory (per process/session).
_LAST: Dict[str, int] = {}


def _slug(name: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name or "project").lower()).strip("-") or "project"


def _digest(seed: str, offset: int) -> int:
    digest = hashlib.sha256(f"{seed}:{offset}".encode()).hexdigest()
    return int(digest[:8], 16)


def _pick(pool: tuple, seed: str, offset: int, key: str, avoid_previous: bool) -> tuple:
    index = _digest(seed, offset) % len(pool)
    if avoid_previous and _LAST.get(key) is not None:
        # Rotate forward until a different value is found (bounded).
        for _ in range(len(pool) - 1):
            index = (index + 1) % len(pool)
            if index != _LAST[key]:
                break
    _LAST[key] = index
    return pool[index]


def choose_layout_variation(project_name: Any, avoid_previous: bool = False) -> Dict[str, Any]:
    """Resolve the deterministic layout profile for one project."""
    seed = _slug(project_name)
    accent = _pick(ACCENT_PALETTES, seed, 1, "accent", avoid_previous)
    surface = _pick(SURFACE_FAMILIES, seed, 2, "surface", avoid_previous)
    order = _pick(SECTION_ORDERS, seed, 3, "order", avoid_previous)
    chain_from, chain_via, chain_to = GRADIENT_CHAINS[accent]
    return {
        "accent": accent,
        "surface": surface,
        "order": list(order),
        "gradient": {"from": chain_from, "via": chain_via, "to": chain_to},
    }


# ---------------------------------------------------------------------------
# Post-write sweep
# ---------------------------------------------------------------------------
_FRONTEND_EXTS = {".jsx", ".js", ".ts", ".tsx", ".css"}


def _iter_frontend_files(frontend_dir: Path) -> List[Path]:
    src = frontend_dir / "src"
    root = src if src.is_dir() else frontend_dir
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in _FRONTEND_EXTS
        and "node_modules" not in p.parts
    )


def _swap_accent(text: str, accent: str) -> tuple[str, int]:
    count = 0
    for shade in _SHADES:
        for depth in ("", "/20", "/30", "/40", "/10", "/5", "/25"):
            token = f"cyan-{shade}{depth}"
            replacement = f"{accent}-{shade}{depth}"
            hits = text.count(token)
            if hits:
                text = text.replace(token, replacement)
                count += hits
    return text, count


def _swap_gradient(text: str, chain: Dict[str, str]) -> tuple[str, int]:
    old = _HERO_GRADIENT_SEQUENCE[0]
    new = f"from-{chain['from']} via-{chain['via']} to-{chain['to']}"
    count = text.count(old)
    if count:
        text = text.replace(old, new)
    # Any residual legacy chains — but never re-swap the profile's own chain
    # (keeps the sweep idempotent for files already processed).
    if new:
        residual = [found for found in _GRADIENT_RE.findall(text) if found != new]
        if residual:
            for found in set(residual):
                text = text.replace(found, new)
                count += 1
    return text, count


def _swap_surface(text: str, surface: str) -> tuple[str, int]:
    if surface == "slate":
        return text, 0
    count = 0
    for shade in _SHADES:
        token = f"slate-{shade}"
        replacement = f"{surface}-{shade}"
        hits = text.count(token)
        if hits:
            text = text.replace(token, replacement)
            count += hits
    return text, count


def _swap_section_order(text: str, order: List[str]) -> tuple[str, int]:
    blocks = {
        "testimonials": "{/* Testimonials Section */}\n        <TestimonialGrid />",
        "pricing": "{/* Pricing Section */}\n        <PricingTable />",
        "faq": "{/* FAQ Section */}\n        <FAQAccordion />",
    }
    found = [
        key for key in blocks
        if f"<{('TestimonialGrid' if key == 'testimonials' else 'PricingTable' if key == 'pricing' else 'FAQAccordion')} />" in text
    ]
    if len(found) < 3:
        return text, 0
    if order == ["testimonials", "pricing", "faq"]:
        return text, 0
    separator = "\n\n        "
    joined = separator.join(blocks[key] for key in order)
    # Operate on the *generated* JSX (single braces, not the f-string source).
    # `\s+` bridges indentation between section blocks.
    generated = re.compile(
        r"\{/\* Testimonials Section \*/\}\s*<TestimonialGrid />\s+"
        r"\{/\* Pricing Section \*/\}\s*<PricingTable />\s+"
        r"\{/\* FAQ Section \*/\}\s*<FAQAccordion />"
        r"|\{/\* Testimonials Section \*/\}\s*<TestimonialGrid />\s+"
        r"\{/\* FAQ Section \*/\}\s*<FAQAccordion />\s+"
        r"\{/\* Pricing Section \*/\}\s*<PricingTable />"
    )
    match = generated.search(text)
    if not match:
        # Legacy variant missing one of the three — swap the two present.
        return text, 0
    text = text[:match.start()] + joined + text[match.end():]
    return text, 1


def apply_layout_variation(
    frontend_dir: Path | str,
    project_name: str,
    avoid_previous: bool = True,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Sweep the generated frontend with this project's layout profile.

    Returns a report: files touched, token counts per axis, chosen profile.
    Never raises for content-shape surprises — every replacement is bounded.
    """
    root = Path(frontend_dir)
    if not root.is_dir():
        return {"applied": False, "reason": "frontend dir missing"}

    chosen = profile or choose_layout_variation(project_name, avoid_previous=avoid_previous)
    accent = chosen["accent"]
    surface = chosen["surface"]
    order = chosen["order"]
    chain = chosen["gradient"]

    files_touched = 0
    accent_hits = 0
    surface_hits = 0
    gradient_hits = 0
    order_hits = 0

    for path in _iter_frontend_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        original = text
        # Gradient must swap BEFORE the accent pass — the accent sweep rewrites
        # the literal `from-cyan-…` chain, so run it while the template text is
        # still canonical.
        text, n2 = _swap_gradient(text, chain)
        text, n1 = _swap_accent(text, accent)
        text, n3 = _swap_surface(text, surface)
        if path.name in {"Home.jsx", "home.jsx"}:
            text, n4 = _swap_section_order(text, order)
            order_hits += n4
        accent_hits += n1
        gradient_hits += n2
        surface_hits += n3
        if text != original:
            path.write_text(text, encoding="utf-8")
            files_touched += 1

    return {
        "applied": True,
        "project": str(project_name),
        "profile": chosen,
        "files_touched": files_touched,
        "accent_tokens": accent_hits,
        "surface_tokens": surface_hits,
        "gradient_tokens": gradient_hits,
        "order_swaps": order_hits,
    }
