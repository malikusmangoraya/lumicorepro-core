"""Reference Intelligence — LumicorePro Part 3.

Decomposes user-cited references (e.g. "Apple-style clean product website",
"Aesop-style editorial restraint") into measurable design attributes.

Rule (hard-coded): Reference = inspiration attributes, NOT template extraction.
Copying a reference layout, fonts, or palette is a failure.

Standalone: no AI provider required (heuristic + keyword based), deterministic.
"""
import os
import re
import json
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Attribute lexicon: keyword -> {attribute, value}
# ---------------------------------------------------------------------------
_ATTRIBUTE_LEXICON: Dict[str, Dict[str, Any]] = {
    # ---- density / whitespace ----
    "clean": {"minimalism": 0.85, "whitespace": 0.8},
    "minimal": {"minimalism": 0.92, "whitespace": 0.88},
    "spacious": {"whitespace": 0.9, "visual_density": 0.2},
    "dense": {"visual_density": 0.85},
    "airy": {"whitespace": 0.85, "minimalism": 0.7},
    # ---- product dominance ----
    "product": {"image_dominance": 0.8, "minimalism": 0.6},
    "product-first": {"image_dominance": 0.9, "minimalism": 0.65},
    # ---- typography ----
    "editorial": {"typography": 0.88, "motion": 0.5},
    "big type": {"typography": 0.92},
    "bold type": {"typography": 0.85},
    "precise": {"typography": 0.85, "motion": 0.4},
    # ---- motion ----
    "subtle": {"motion": 0.4},
    "playful": {"motion": 0.8, "visual_density": 0.55},
    "energetic": {"motion": 0.85, "visual_density": 0.5},
    "animated": {"motion": 0.9},
    "calm": {"motion": 0.25, "minimalism": 0.6},
    "restrained": {"motion": 0.3, "minimalism": 0.6},
    "slow": {"motion": 0.2},
    # ---- color ----
    "neutral": {"color_saturation": 0.2, "minimalism": 0.6},
    "monochrome": {"color_saturation": 0.1, "minimalism": 0.55},
    "vibrant": {"color_saturation": 0.9},
    "colorful": {"color_saturation": 0.85},
    "muted": {"color_saturation": 0.3},
    "dark": {"dark_canvas": 0.9},
    "pastel": {"color_saturation": 0.4, "playful": 0.5},
    # ---- warmth / personality ----
    "warm": {"warmth": 0.8},
    "friendly": {"warmth": 0.85, "playful": 0.6},
    "luxury": {"luxury": 0.95, "visual_density": 0.3, "motion": 0.4},
    "premium": {"luxury": 0.8, "visual_density": 0.35},
    "cinematic": {"cinematic": 0.9, "visual_density": 0.3},
    "refined": {"luxury": 0.7, "typography": 0.75},
    "elegant": {"luxury": 0.8, "motion": 0.4},
    "bold": {"bold": 0.9, "visual_density": 0.5},
    "confident": {"bold": 0.7},
    "tech": {"futuristic": 0.75, "minimalism": 0.5},
    "futuristic": {"futuristic": 0.9},
    "modern": {"futuristic": 0.5, "minimalism": 0.4},
    # ---- interaction ----
    "interactive": {"interaction_complexity": 0.8},
    "immersive": {"interaction_complexity": 0.9, "motion": 0.7},
    "simple": {"interaction_complexity": 0.2, "minimalism": 0.7},
    # ---- brand feel ----
    "heritage": {"luxury": 0.5, "editorial": 0.5},
    "artisanal": {"luxury": 0.7, "craft": 0.8},
    "industrial": {"utilitarian": 0.8, "visual_density": 0.6},
}

# Phrase-level hints for two+ word references ("Apple-style urgency", etc.)
_PHRASE_PATTERN = re.compile(
    r"([\w\s&+.-]+?)\s*(?:style|like|esque|-ish)?\s*(?:of|like)?\s*"
    r"(.*)$",
    re.IGNORECASE,
)

# Well-known reference sites -> attribute profile (inspiration only)
_KNOWN_REFERENCES: Dict[str, Dict[str, float]] = {
    "apple": {"minimalism": 0.92, "whitespace": 0.88, "content_density": 0.24,
              "typography": 0.91, "image_dominance": 0.81, "motion": 0.42,
              "color_saturation": 0.3, "navigation": 0.2, "cta_focus": 0.75},
    "aesop": {"minimalism": 0.9, "whitespace": 0.92, "content_density": 0.2,
              "typography": 0.9, "image_dominance": 0.7, "motion": 0.25,
              "color_saturation": 0.15, "navigation": 0.15, "cta_focus": 0.6,
              "craft": 0.9},
    "stripe": {"minimalism": 0.8, "whitespace": 0.7, "content_density": 0.5,
               "typography": 0.85, "image_dominance": 0.5, "motion": 0.5,
               "color_saturation": 0.45, "futuristic": 0.3, "cta_focus": 0.9},
    "notion": {"minimalism": 0.8, "whitespace": 0.7, "content_density": 0.6,
               "typography": 0.8, "motion": 0.4, "color_saturation": 0.35,
               "cta_focus": 0.8},
    "linear": {"minimalism": 0.85, "whitespace": 0.75, "content_density": 0.5,
               "typography": 0.9, "motion": 0.6, "color_saturation": 0.3,
               "futuristic": 0.7, "cta_focus": 0.85},
    "airbnb": {"warmth": 0.7, "motion": 0.5, "image_dominance": 0.75,
               "content_density": 0.55, "color_saturation": 0.45},
    "supreme": {"bold": 0.95, "minimalism": 0.5, "visual_density": 0.4},
    "spotify": {"motion": 0.7, "color_saturation": 0.75, "bold": 0.7,
                "image_dominance": 0.6},
    "figma": {"minimalism": 0.7, "motion": 0.6, "color_saturation": 0.55,
              "interaction_complexity": 0.6, "cta_focus": 0.8},
    "vercel": {"minimalism": 0.9, "whitespace": 0.85, "content_density": 0.35,
               "typography": 0.9, "motion": 0.4, "color_saturation": 0.2,
               "futuristic": 0.6, "cta_focus": 0.85},
    "rayban": {"motion": 0.5, "image_dominance": 0.8, "color_saturation": 0.55,
               "luxury": 0.5, "bold": 0.5},
}

# Open-source design resources (registry/design-resources.json) also decompose
# into the same attribute schema. Merge their slug + name tokens so prompts
# like "shadcn-style clean" or "magic-ui motion" resolve deterministically.
try:  # package-relative import (normal runtime)
    from .design_resources import load_catalog
except Exception:  # pragma: no cover - flat import fallback
    try:
        from agent.intelligence.design_resources import load_catalog
    except Exception:  # pragma: no cover - catalog absent
        load_catalog = None  # type: ignore[assignment]


def _resource_references() -> Dict[str, Dict[str, float]]:
    """Catalog resources -> brand-keyed attribute profiles (inspiration only)."""
    merged: Dict[str, Dict[str, float]] = {}
    if load_catalog is None:
        return merged
    for item in load_catalog():
        slug = str(item.get("slug") or "").strip()
        name = str(item.get("name") or "").strip()
        attrs = {
            k: round(float(v), 2) for k, v in (item.get("attributes") or {}).items()
        }
        if not slug or not attrs:
            continue
        for key in [slug.lower(), name.lower() if name else ""]:
            if key:
                merged.setdefault(key, {}).update(attrs)
            for kw in (item.get("keywords") or []):
                merged.setdefault(str(kw).strip().lower(), {}).update(attrs)
    return merged


_KNOWN_REFERENCES.update(_resource_references())

# Attribute keys ordered as they appear in the reference schema
_ATTRIBUTE_KEYS = [
    "minimalism", "whitespace", "typography", "motion", "visual_density",
    "content_density", "image_dominance", "color_saturation", "warmth",
    "luxury", "cinematic", "bold", "futuristic", "interaction_complexity",
    "craft", "dark_canvas", "navigation", "cta_focus",
]


class ReferenceAnalyzer:
    """Decomposes a user reference into design attribute scores (0.0-1.0)."""

    def __init__(self, lexicon: Optional[Dict[str, Any]] = None):
        self.lexicon = lexicon or _ATTRIBUTE_LEXICON

    def analyze(self, reference: str) -> Dict[str, Any]:
        """Analyze a reference string -> {reference, traits, constraints}."""
        reference = (reference or "").strip()
        traits: Dict[str, float] = {}
        hints: List[str] = []

        if not reference:
            return self._schema(reference, traits, hints)

        text = reference.lower()

        # 1) Known brand reference
        for brand, profile in _KNOWN_REFERENCES.items():
            if brand in text:
                hints.append(brand)
                for key, value in profile.items():
                    traits[key] = max(traits.get(key, 0.0), value)

        # 2) Keyword lexicon
        for keyword, attrs in self.lexicon.items():
            if keyword in text:
                hints.append(keyword)
                for key, value in attrs.items():
                    traits[key] = max(traits.get(key, 0.0), value)

        # 3) Phrase decomposition for composite references
        phrase_match = _PHRASE_PATTERN.match(text)
        if phrase_match and len(text.split()) > 1:
            for part in re.split(r"[\s,;_\-+&]+", text):
                part = part.strip()
                if part and part in self.lexicon:
                    for key, value in self.lexicon[part].items():
                        traits[key] = max(traits.get(key, 0.0), value)

        # Defaults for missing attributes (neutral 0.4 => "moderate")
        for key in _ATTRIBUTE_KEYS:
            traits.setdefault(
                key, _DEFAULT_ATTRIBUTE.get(key, 0.45)
            )

        return self._schema(reference, traits, hints)

    @staticmethod
    def _schema(reference: str, traits: Dict[str, float],
                hints: List[str]) -> Dict[str, Any]:
        return {
            "reference": reference,
            "traits": {k: round(float(v), 2) for k, v in traits.items()},
            "constraints": {
                "copy_style": "do_not_copy",
                "layout": "derive_attributes_only",
                "branding": "fully_original",
            },
            "hints": hints,
        }


_DEFAULT_ATTRIBUTE: Dict[str, float] = {
    "minimalism": 0.45, "whitespace": 0.45, "typography": 0.45,
    "motion": 0.45, "visual_density": 0.45, "content_density": 0.45,
    "image_dominance": 0.45, "color_saturation": 0.45, "warmth": 0.45,
    "luxury": 0.45, "cinematic": 0.45, "bold": 0.45,
    "futuristic": 0.45, "interaction_complexity": 0.45, "craft": 0.45,
    "dark_canvas": 0.45, "navigation": 0.45, "cta_focus": 0.45,
}


class OriginalityGuard:
    """Ensures the design direction stays original, never a copy."""

    # Phrases that indicate risky copy-intent
    _COPY_INDICATORS = [
        "exactly like", "same as", "copy", "clone", "replicate",
        "identical to", "template of", "recreate apple", "clone apple",
    ]

    def guard(self, reference: str) -> Dict[str, Any]:
        """Returns warning labels when the user asks for a clone."""
        text = (reference or "").lower()
        flags = [
            ind for ind in self._COPY_INDICATORS if ind in text
        ]
        return {
            "copy_attempt": bool(flags),
            "flags": flags,
            "action": (
                "convert_to_attributes" if flags
                else "allowed_as_inspiration"
            ),
        }


def extract_reference_intelligence(reference: str) -> Dict[str, Any]:
    """Public helper: one-call reference decomposition."""
    analyzer = ReferenceAnalyzer()
    guard = OriginalityGuard()
    analysis = analyzer.analyze(reference)
    guard_result = guard.guard(reference)
    analysis["originality_guard"] = guard_result
    return analysis


def run_cli(reference: str) -> str:
    """CLI entry: prints the reference schema as JSON."""
    return json.dumps(extract_reference_intelligence(reference), indent=2)


if __name__ == "__main__":
    import sys

    ref = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(run_cli(ref))