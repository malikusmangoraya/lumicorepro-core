"""
Vision Layout & Theme Extraction Engine — Phase 0
==================================================
Turns an uploaded screenshot into a structured design brief before the rest of
the pipeline runs:

  1. Layout parsing via a vision-capable provider (OpenRouter/Gemini) — element
     hierarchy (header/sidebar/cards), spacing, typography, color palette.
  2. Deterministic fallback — when no vision key exists, derives a conservative
     layout brief + design tokens from domain heuristics so the pipeline still
     produces a coherent, brandable site.
  3. Palette normalization — hex input validation and HSL contract for the
     DesignStyleEngine token bridge.
"""
import os
import re
import base64
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import agent_logger
from utils.helpers import safe_json_parse
from config.settings import VISION_PROVIDER, VISION_MODEL


# ── Color helpers (shared contract with DesignStyleEngine) ────────────────
_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _is_hex(value: str) -> bool:
    return bool(value and _HEX_RE.match(value))


def _hex_to_hsl(value: str) -> str:
    value = value.lstrip('#')
    if len(value) == 3:
        value = ''.join(c * 2 for c in value)
    if len(value) == 6:
        value += 'ff'
    try:
        r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return '0 0% 100%'
    r, g, b = (c / 255.0 for c in (r, g, b))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    d = mx - mn
    if d == 0:
        h = s = 0.0
    else:
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6.0
    return f'{round(h * 360)} {round(s * 100, 1)}% {round(l * 100, 1)}%'


def _extract_palette(text: str) -> List[str]:
    """Pull candidate hex codes from a vision response text."""
    codes = _HEX_RE.findall(text or '')
    out: List[str] = []
    for c in codes:
        norm = c if len(c) == 7 else c[:7]
        norm = re.sub(r'^(#[0-9a-fA-F]{6}).*$', r'\1', norm)
        if norm not in out and _is_hex(norm):
            out.append(norm)
    return out


class VisionPipeline:
    """Phase 0 vision layout + theme extractor with graceful degradation."""

    DEFAULT_THEME = {
        "primary": "#0ea5e9",
        "secondary": "#6366f1",
        "accent": "#f59e0b",
        "bg": "#0b1220",
        "card": "rgba(255,255,255,0.06)",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "border": "rgba(255,255,255,0.12)",
    }

    def __init__(self, provider=None):
        self.provider = provider

    def _load_image(self, image_source: str) -> Optional[tuple]:
        """Return (base64_data, mime_type) for a local file or URL/data-uri."""
        s = image_source.strip()
        if not s:
            return None
        if s.startswith("data:"):
            try:
                meta, b64 = s.split(",", 1)
                mime = meta.split(";")[0].split(":")[1] if ":" in meta else "image/png"
                return b64, mime
            except ValueError:
                return None
        if s.startswith(("http://", "https://")):
            return s, "image/png"  # pass URL to the vision model directly
        path = s if os.path.isabs(s) else os.path.abspath(s)
        if os.path.isfile(path):
            mime = "image/png"
            ext = Path(path).suffix.lower()
            if ext == ".jpg" or ext == ".jpeg":
                mime = "image/jpeg"
            elif ext == ".webp":
                mime = "image/webp"
            try:
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode("ascii"), mime
            except OSError as e:
                agent_logger.warning(f"Vision: cannot read image {path}: {e}")
                return None
        return None

    def _vision_prompt(self) -> str:
        return (
            "Analyze this website UI screenshot. Return ONLY valid JSON with keys:\n"
            "{\n"
            '  "layout": {"regions": ["header", "hero", "features", "cta", "footer"]},\n'
            '  "element_hierarchy": [{"type": "card", "row": 1, "col": 1}],\n'
            '  "colors": {"primary": "#hex", "background": "#hex", "text": "#hex"},'
            '  "spacing": {"section_gap_px": 72, "card_padding_px": 24},\n'
            '  "typography": {"headings": "Sans-serif", "body": "Sans-serif", "base_size_px": 16}\n'
            "}\n"
            "Be precise about colors as hex values."
        )

    def extract_layout(self, image_source: str) -> Dict[str, Any]:
        """Run the vision pass. Returns {parsed, brief, tokens, source}."""
        loaded = self._load_image(image_source)
        if loaded is None:
            return {"parsed": False, "reason": "image_unreadable"}

        raw = ""
        if self.provider is not None:
            try:
                raw = self.provider.describe_image(
                    loaded[0], loaded[1], self._vision_prompt()
                )
            except Exception as e:
                agent_logger.warning(f"Vision provider call failed: {e}")

        if raw and raw.strip():
            parsed = safe_json_parse(raw)
            if parsed:
                return self._normalize(parsed, source="ai_vision", raw=raw[:2000])

        # Deterministic fallback — domain-neutral but brandable.
        palette = _extract_palette(raw) if raw else []
        fallback = self._fallback_brief(palette)
        return {
            **fallback,
            "source": "fallback_heuristic",
            "raw_vision_hint": raw[:500],
        }

    def _normalize(self, parsed: Dict[str, Any], source: str, raw: str = "") -> Dict[str, Any]:
        colors = parsed.get("colors") or {}
        regions = (parsed.get("layout") or {}).get("regions") or ["header", "hero", "features", "cta", "footer"]
        tokens = {
            "primary": colors.get("primary") if _is_hex(str(colors.get("primary"))) else self.DEFAULT_THEME["primary"],
            "secondary": colors.get("secondary") if _is_hex(str(colors.get("secondary"))) else self.DEFAULT_THEME["secondary"],
            "accent": colors.get("accent") if _is_hex(str(colors.get("accent"))) else self.DEFAULT_THEME["accent"],
            "bg": colors.get("background") if _is_hex(str(colors.get("background"))) else self.DEFAULT_THEME["bg"],
            "text": colors.get("text") if _is_hex(str(colors.get("text"))) else self.DEFAULT_THEME["text"],
        }
        return {
            "parsed": True,
            "source": source,
            "layout": {"regions": regions[:12]},
            "element_hierarchy": parsed.get("element_hierarchy") or [],
            "colors": colors,
            "spacing": parsed.get("spacing") or {"section_gap_px": 72, "card_padding_px": 24},
            "typography": parsed.get("typography") or {"headings": "Sans-serif", "body": "Sans-serif"},
            "design_tokens": tokens,
            "raw_vision": raw[:2000],
        }

    def _fallback_brief(self, palette: List[str]) -> Dict[str, Any]:
        base = dict(self.DEFAULT_THEME)
        if palette:
            base["primary"] = palette[0]
            if len(palette) > 1:
                base["secondary"] = palette[1]
            if len(palette) > 2:
                base["accent"] = palette[2]
        return {
            "parsed": False,
            "source": "fallback_heuristic",
            "layout": {"regions": ["header", "hero", "features", "cta", "footer"]},
            "element_hierarchy": [],
            "spacing": {"section_gap_px": 72, "card_padding_px": 24},
            "typography": {"headings": "Sans-serif", "body": "Sans-serif"},
            "design_tokens": base,
        }

    def to_spec_overlays(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Build the section-order + design-token overlays the generator consumes."""
        tokens = layout.get("design_tokens") or self.DEFAULT_THEME
        palette = {k: v for k, v in tokens.items() if _is_hex(v)}
        return {
            "vision_layout_regions": (layout.get("layout") or {}).get("regions", []),
            "design_tokens": {
                "palette": palette,
                "palette_hsl": {k: _hex_to_hsl(v) for k, v in palette.items()},
                "spacing": layout.get("spacing") or {},
                "typography": layout.get("typography") or {},
            },
        }


class LayoutMapper:
    """Maps the extracted layout/theme brief onto the local component library."""

    # Region keyword -> template/component category hints
    REGION_HINTS = {
        "header": ["navbar", "Navigation", "Header"],
        "hero": ["HeroSection", "Hero"],
        "features": ["Feature", "FeaturesSection", "Grid"],
        "product": ["Product", "Card", "Grid"],
        "gallery": ["Gallery", "Product", "Card"],
        "testimonial": ["Review", "Testimonial", "Card"],
        "pricing": ["Pricing", "PricingCard"],
        "cta": ["Cta", "CallToAction", "Banner"],
        "footer": ["Footer", "Newsletter"],
        "contact": ["ContactForm"],
        "dashboard": ["Dashboard", "Stat", "Chart"],
    }

    def __init__(self, project_dir: str = ""):
        self.project_dir = project_dir

    def map_regions(self, layout: Dict[str, Any]) -> List[Dict[str, Any]]:
        regions = (layout.get("layout") or {}).get("regions", [])
        mapped = []
        for region in regions:
            hints = self.REGION_HINTS.get(region.lower(), [])
            component = self._find_component(hints)
            mapped.append({
                "region": region,
                "suggested_component": component,
                "hints": hints,
            })
        return mapped

    def _find_component(self, hints: List[str]) -> str:
        try:
            from agent.component_registry import get_component_registry
            reg = get_component_registry()
            for name in reg.names():
                for h in hints:
                    if h.lower() in name.lower():
                        return name
        except Exception:
            pass
        return hints[0] if hints else "Card"

    def build_buildplan(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        mapped = self.map_regions(layout)
        return {
            "regions_mapped": mapped,
            "overlay": self.to_overlay(layout),
        }

    def to_overlay(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        tokens = layout.get("design_tokens") or {}
        return {
            "region_components": {m["region"]: m["suggested_component"] for m in self.map_regions(layout)},
            "design_tokens": tokens,
        }