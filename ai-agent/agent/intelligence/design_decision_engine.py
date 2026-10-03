"""Design Decision Engine — LumicorePro Part 3.

Merges USER REQUIREMENTS + BUSINESS ANALYSIS + AUDIENCE + BRAND +
REFERENCE ATTRIBUTES + INDUSTRY PLAYBOOK + BRAND PLAYBOOK + CONSTRAINTS
into a single machine-readable design specification.

Inputs:
  - spec (the orchestrator requirement spec)
  - industry / brand detectors (heuristic, deterministic)
  - reference attributes (from reference_intelligence)
  - playbooks (YAML from ai-agent/playbooks/)

Output: a `design_decision` dict that the frontend generator builds against.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Make optional: playbooks may not be loadable -> pure heuristics fallback
try:
    import yaml
    _HAS_YAML = True
except Exception:  # pragma: no cover - yaml missing fallback
    _HAS_YAML = False

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_PLAYBOOKS_DIR = _BASE_DIR / "playbooks"

# ---------------------------------------------------------------------------
# Industry detector
# ---------------------------------------------------------------------------
_INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "ecommerce": ["ecommerce", "e-commerce", "store", "shop", "retail",
                  "products", "order", "cart"],
    "marketplace": ["marketplace", "vendor", "sellers", "buyers",
                    "listings", "multi-seller"],
    "saas": ["saas", "software", "platform", "subscription", "dashboard",
             "app", "tool", "b2b software"],
    "automotive": ["automotive", "car", "cars", "vehicle", "auto dealer",
                   "dealership", "showroom", "truck"],
    "food": ["food", "restaurant", "cafe", "menu", "delivery", "dining",
             "bakery", "culinary"],
    "fintech": ["fintech", "finance", "bank", "payment", "payments",
                "lending", "insurance", "wallet", "money"],
    "portfolio": ["portfolio", "personal brand", "freelancer", "artist",
                  "photographer", "resume", "cv", "designer"],
    "education": ["education", "course", "learning", "academy", "training",
                  "tutor", "school", "university"],
    "healthcare": ["healthcare", "health", "clinic", "hospital", "doctor",
                   "medical", "telemedicine", "pharmacy"],
    "real-estate": ["real estate", "property", "realestate", "housing",
                    "apartments", "commercial space", "homes"],
    "electronics": ["electronics", "gadget", "devices", "smartphone",
                    "laptop", "tech store", "accessories"],
    "industrial": ["industrial", "manufacturing", "machinery", "factory",
                   "b2b", "equipment", "supplier"],
    "hospitality": ["hospitality", "hotel", "resort", "tourism", "spa",
                    "guesthouse", "accommodation"],
    "entertainment": ["entertainment", "events", "movies", "music artist",
                      "concert", "box office", "streaming"],
    "sports": ["sports", "football", "cricket", "club", "athlete", "gym",
               "fitness", "team"],
    "fashion": ["fashion", "clothing", "apparel", "jewelry", "boutique",
                "wear", "style", "outfit"],
}
_INDUSTRY_ALIASES = {
    "car": "automotive", "auto": "automotive", "dealership": "automotive",
    "restaurant": "food", "cafe": "food", "bakery": "food",
    "clinic": "healthcare", "doctor": "healthcare", "medical": "healthcare",
    "hotel": "hospitality", "resort": "hospitality",
    "event": "entertainment", "concert": "entertainment",
    "designer": "portfolio", "photographer": "portfolio",
    "property": "real-estate", "loan": "fintech", "insurance": "fintech",
}


def detect_industry(spec: Dict[str, Any]) -> str:
    """Return best-matching industry id from spec text."""
    text_parts = [
        spec.get("industry", ""),
        spec.get("description", ""),
        spec.get("business_type", ""),
        spec.get("name", ""),
        spec.get("tagline", ""),
    ]
    text = " ".join(str(p) for p in text_parts if p).lower()

    # Direct alias match wins over keyword count
    for alias, industry in _INDUSTRY_ALIASES.items():
        if alias in text:
            return industry

    scores: Dict[str, int] = {}
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score:
            scores[industry] = score
    return max(scores, key=scores.get) if scores else "saas"


# ---------------------------------------------------------------------------
# Brand detector
# ---------------------------------------------------------------------------
_BRAND_KEYWORDS: Dict[str, List[str]] = {
    "luxury": ["luxury", "premium", "high-end", "exclusive", "elegant",
               "refined", "heritage", "sophisticated", "upscale"],
    "minimal": ["minimal", "clean", "simple", "sparse", "understated",
                "stripped", "pared"],
    "futuristic": ["futuristic", "tech", "future", "innovative", "smart",
                   "next-generation", "ai", "digital"],
    "editorial": ["editorial", "magazine", "story", "artistic", "literary",
                  "narrative", "culture"],
    "playful": ["playful", "fun", "colorful", "friendly", "youthful",
                "cheerful", "whimsical"],
    "corporate": ["corporate", "business", "professional", "official",
                  "enterprise", "b2b", "consulting"],
    "bold": ["bold", "strong", "statement", "impactful", "dynamic",
             "edgy", "assertive"],
}
_BRAND_DEFAULTS: Dict[str, float] = {
    "luxury": 0.7, "minimal": 0.6, "futuristic": 0.5, "editorial": 0.4,
    "playful": 0.35, "corporate": 0.4, "bold": 0.45,
}


def detect_brand(spec: Dict[str, Any]) -> str:
    """Return best-matching brand archetype."""
    text = " ".join(
        str(spec.get(k, "")) for k in
        ("description", "design_style", "brand_personality", "name",
         "tagline", "industry")
    ).lower()
    scores: Dict[str, int] = {}
    for brand, keywords in _BRAND_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score:
            scores[brand] = score
    return max(scores, key=scores.get) if scores else "minimal"


# ---------------------------------------------------------------------------
# Playbook loader
# ---------------------------------------------------------------------------
class PlaybookLoader:
    """Loads industry + brand playbooks as dicts (YAML or JSON)."""

    def __init__(self, playbooks_dir: Optional[str] = None):
        self.dir = Path(playbooks_dir or _PLAYBOOKS_DIR)

    def _load(self, subdir: str, name: str) -> Dict[str, Any]:
        if not _HAS_YAML:
            return {}
        candidates = [
            self.dir / subdir / f"{name}.yaml",
            self.dir / subdir / f"{name}.yml",
            self.dir / subdir / f"{name}.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        if path.suffix == ".json":
                            return json.load(fh)
                        return yaml.safe_load(fh) or {}
                except Exception:
                    return {}
        return {}

    def industry(self, industry_id: str) -> Dict[str, Any]:
        return self._load("industries", industry_id)

    def brand(self, brand_id: str) -> Dict[str, Any]:
        return self._load("brands", brand_id)


# ---------------------------------------------------------------------------
# Constraint Resolver
# ---------------------------------------------------------------------------
class ConstraintResolver:
    """Resolves conflicting requirements per device/context."""

    _CONFLICTS: List[Tuple[str, str, str]] = [
        ("motion", "animation", "performance"),
        ("motion", "animated", "fast"),
        ("effects", "rich", "mobile"),
        ("3d", "three", "performance"),
    ]

    def resolve(self, spec: Dict[str, Any],
                reference_traits: Dict[str, float]) -> Dict[str, Any]:
        """Return per-context resolutions recorded in the manifest."""
        text = " ".join(str(spec.get(k, "")) for k in
                        ("description", "requirements", "features")).lower()
        resolutions: Dict[str, Any] = {
            "detected": [],
            "rules": {
                "desktop": {"motion": "rich", "effects": "allowed"},
                "mobile": {"motion": "simplified", "effects": "reduced"},
                "reduced_motion": {"motion": "minimal", "effects": "none"},
            },
        }
        wants_motion = any(k in text for k in
                           ("animation", "animated", "motion", "interactive"))
        wants_fast = any(k in text for k in
                         ("fast", "light", "performance", "speed", "mobile"))
        if wants_motion and wants_fast:
            resolutions["detected"].append({
                "conflict": "rich_motion_vs_performance",
                "resolution": (
                    "desktop: rich motion; mobile: simplified; "
                    "reduced-motion: minimal"
                ),
            })
        if reference_traits.get("visual_density", 0.5) > 0.6 and \
                any(k in text for k in ("minimal", "clean", "simple")):
            resolutions["detected"].append({
                "conflict": "dense_content_vs_minimal_design",
                "resolution": (
                    "reduce visible items; add filtering; "
                    "progressive disclosure"
                ),
            })
        if not resolutions["detected"]:
            resolutions["rules"] = {
                "desktop": {"motion": "default", "effects": "default"},
                "mobile": {"motion": "default", "effects": "default"},
                "reduced_motion": {"motion": "minimal", "effects": "none"},
            }
        return resolutions


# ---------------------------------------------------------------------------
# Design Decision Engine
# ---------------------------------------------------------------------------
# Visual decision mapping: trait -> design spec field
def _trait_to_visual(reference_traits: Dict[str, float],
                     playbook_visual: Dict[str, Any]) -> Dict[str, Any]:
    visual = dict(playbook_visual or {})

    # heights / hero
    density = reference_traits.get("visual_density", 0.45)
    visual["grid"] = (
        "dense_product" if density > 0.6 else
        "asymmetric_editorial" if reference_traits.get("editorial", 0) >= 0.7
        else "balanced"
    )

    # typography
    typo_score = reference_traits.get("typography", 0.45)
    if typo_score >= 0.8:
        visual["typography"] = "display_driven"
    elif reference_traits.get("luxury", 0) >= 0.6:
        visual["typography"] = "refined_serif"
    elif reference_traits.get("futuristic", 0) >= 0.6:
        visual["typography"] = "technical_sans"
    else:
        visual["typography"] = "clean_sans"

    # motion
    motion = reference_traits.get("motion", 0.45)
    visual["motion"] = (
        "subtle" if motion < 0.4 else
        "dynamic" if motion > 0.66 else "balanced"
    )

    # 3d
    visual["3d"] = bool(reference_traits.get("interaction_complexity", 0) > 0.75
                        or playbook_visual.get("3d") is True)
    if visual.get("3d") in ("optional", "conditional", "no"):
        visual["3d"] = (
            reference_traits.get("interaction_complexity", 0) > 0.8
        )

    # cta
    playbook_cta = visual.get("cta_style") if isinstance(
        visual.get("cta_style"), str) else None
    cta_focus = reference_traits.get("cta_focus", 0.6) or 0.6
    if playbook_cta:
        # Industry playbook CTA wins; reference only refines when none given
        visual["cta_style"] = playbook_cta
    elif cta_focus > 0.72:
        visual["cta_style"] = "single_high_contrast"
    elif reference_traits.get("luxury", 0) > 0.6:
        visual["cta_style"] = "distributed_understated"
    else:
        visual["cta_style"] = "clear_primary"

    # surfaces
    if reference_traits.get("luxury", 0) >= 0.6:
        visual["surface_style"] = "flat_premium"
    elif reference_traits.get("futuristic", 0) >= 0.6:
        visual["surface_style"] = "layered_tech"
    elif reference_traits.get("minimalism", 0.45) >= 0.7:
        visual["surface_style"] = "flat"
    else:
        visual["surface_style"] = "subtle_card"

    # image ratio
    img_dominance = reference_traits.get("image_dominance", 0.45)
    visual["image_ratio"] = (
        "21:9" if img_dominance > 0.7 and visual.get("grid") ==
        "asymmetric_editorial" else
        "16:9" if img_dominance > 0.6 else "4:3"
    )

    # card usage
    card_usage = density
    visual["card_usage"] = (
        "minimal" if card_usage < 0.4 else
        "moderate" if card_usage < 0.7 else "heavy"
    )
    return visual


class DesignDecisionEngine:
    """Merges every upstream signal into one design specification."""

    def __init__(self, playbook_loader: Optional[PlaybookLoader] = None,
                 resolver: Optional[ConstraintResolver] = None):
        self.loader = playbook_loader or PlaybookLoader()
        self.resolver = resolver or ConstraintResolver()

    def decide(self, spec: Dict[str, Any],
               reference_analysis: Optional[Dict[str, Any]] = None
               ) -> Dict[str, Any]:
        raw_industry = spec.get("industry") or ""
        detected_industry = detect_industry(spec)
        # Always normalize to a canonical playbook id (raw industry strings
        # like "premium luxury automotive dealership" never match the
        # playbook key directly, but the detector does resolve them).
        industry = detected_industry
        if raw_industry not in _INDUSTRY_KEYWORDS:
            industry = detected_industry
        brand = spec.get("brand") or detect_brand(spec)

        industry_playbook = self.loader.industry(industry)
        brand_playbook = self.loader.brand(brand)

        reference_analysis = reference_analysis or {}
        if not reference_analysis.get("traits"):
            # Self-extract cues from the spec description when no explicit
            # reference was given (keeps hero/motion decisions grounded).
            try:
                from .reference_intelligence import ReferenceAnalyzer
                desc = " ".join(str(spec.get(k, "")) for k in
                                ("description", "design_style", "tagline"))
                if desc.strip():
                    auto = ReferenceAnalyzer().analyze(desc)
                    reference_analysis = auto
            except Exception:
                pass
        reference_traits = reference_analysis.get("traits", {})

        # Merge industry visual + brand visual overrides
        visual = {}
        if industry_playbook.get("visual"):
            visual.update(industry_playbook.get("visual", {}))
        if brand_playbook.get("color"):
            visual["color_behavior"] = brand_playbook.get("color", {})
        if brand_playbook.get("typography"):
            visual["typography_brand"] = brand_playbook.get(
                "typography", {})
        if brand_playbook.get("motion") and "motion" not in visual:
            visual["motion"] = brand_playbook.get("motion", {})
        if brand_playbook.get("interaction"):
            visual["interaction_style"] = brand_playbook.get(
                "interaction", {})

        # Let reference traits refine the decision when present
        if reference_traits:
            visual = _trait_to_visual(reference_traits, visual)

        # Constraint resolution
        resolutions = self.resolver.resolve(spec, reference_traits)

        decision = {
            "industry": industry,
            "brand": brand,
            "hero": self._pick_hero(visual, reference_traits),
            "navigation": visual.get("navigation_mode",
                                     "minimal_sticky"),
            "grid": visual.get("grid", "balanced"),
            "typography": visual.get("typography", "clean_sans"),
            "motion": visual.get("motion", "balanced"),
            "3d": bool(visual.get("3d", False)),
            "image_ratio": visual.get("image_ratio", "16:9"),
            "cta_style": visual.get("cta_style", "clear_primary"),
            "surface_style": visual.get("surface_style", "subtle_card"),
            "card_usage": visual.get("card_usage", "moderate"),
            "playbooks": {
                "industry": industry, "brand": brand,
                "industry_loaded": bool(industry_playbook),
                "brand_loaded": bool(brand_playbook),
            },
            "constraints_resolved": resolutions,
            "reference": reference_analysis.get("reference") or None,
            "reference_hints": reference_analysis.get("hints") or [],
            "pages": industry_playbook.get("pages", []),
            "conversion": {
                "primary_cta": industry_playbook.get("conversion", {}).get(
                    "primary_cta", "get_started"),
                "secondary_cta": industry_playbook.get("conversion", {}).get(
                    "secondary_cta", "learn_more"),
            },
            "avoid": industry_playbook.get("avoid", []),
            "qa": industry_playbook.get("qa", []),
        }
        # Cross-project self-learning seed: prior builds that failed the design
        # gate for this industry/brand feed attention into the new decision so
        # the generator actively counteracts known weak spots.
        prior_attention = list(spec.get("prior_attention") or [])
        if prior_attention:
            avoid = list(decision.get("avoid", []))
            for metric in prior_attention:
                hint = f"learned_gap:{metric}"
                if hint not in avoid:
                    avoid.append(hint)
            decision["avoid"] = avoid
            decision["learned_gaps"] = prior_attention
        decision["design_manifest"] = self._manifest(
            spec, industry, brand, reference_traits, decision)
        return decision

    @staticmethod
    def _pick_hero(visual: Dict[str, Any],
                   traits: Dict[str, float]) -> str:
        typo = traits.get("typography", 0) or 0
        cinematic = traits.get("cinematic", 0) or 0
        lux = traits.get("luxury", 0) or 0
        inter = traits.get("interaction_complexity", 0) or 0
        futuristic = traits.get("futuristic", 0) or 0

        if cinematic >= 0.7:
            return "cinematic_video"
        if typo >= 0.85:
            return "typographic_hero"
        if inter >= 0.75:
            return "interactive_story"
        if futuristic >= 0.7:
            return "product_ui_preview"
        if lux >= 0.6:
            return "editorial_photography"
        return "minimal_composition"

    @staticmethod
    def _reproducibility(spec: Dict[str, Any],
                         industry: str,
                         brand: str,
                         decision: Dict[str, Any]) -> Dict[str, Any]:
        """Seed + inputs behind this decision, so a run can be reproduced.

        Written into `design-manifest.json`. The seed is a sha256 digest of the
        prompt (never `hash()`, which is salted per process): the same spec always
        reproduces the same decision and the same palette.
        """
        prompt = str(spec.get("prompt") or spec.get("description") or "")
        digest = hashlib.sha256(prompt.encode("utf-8", "replace")).hexdigest()[:16]
        return {
            "seed": spec.get("design_seed") or digest,
            "prompt_digest": digest,
            "inputs": {
                "industry": industry,
                "brand": brand,
                "design_style": spec.get("design_style"),
                "website_type": spec.get("website_type"),
                "reference_hints": decision.get("reference_hints") or [],
            },
        }

    @staticmethod
    def _manifest(spec: Dict[str, Any], industry: str, brand: str,
                  traits: Dict[str, float],
                  decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "brand": {
                "archetype": brand,
                "personality": [],  # filled by manifest writer from playbook
            },
            "visual": {
                "density": round(traits.get("visual_density", 0.45), 2),
                "motion": round(traits.get("motion", 0.45), 2),
                "3d": bool(decision.get("3d")),
            },
            "typography": {
                "heading_style": decision.get("typography"),
                "body_style": "modern_sans",
            },
            "colors": {"tokens": {}, "source": "design_tokens.json"},
            "spacing": {"scale": "token_based"},
            "components": {"critical": decision.get("conversion", {})},
            "industry": industry,
            "reference_sources": decision.get("reference_hints") or [],
            "reproducibility": DesignDecisionEngine._reproducibility(
                spec, industry, brand, decision),
        }


def decide_design(spec: Dict[str, Any],
                  reference_analysis: Optional[Dict[str, Any]] = None
                  ) -> Dict[str, Any]:
    """One-call helper: produce the full design decision from a spec."""
    return DesignDecisionEngine().decide(spec, reference_analysis)


if __name__ == "__main__":
    import sys
    sample = {
        "name": "Nexa Motors",
        "industry": "premium luxury automotive dealership",
        "description": "Luxury car showroom with cinematic hero, "
                        "interactive configurator, concierge booking.",
    }
    if len(sys.argv) > 1:
        try:
            sample = json.loads(sys.argv[1])
        except Exception:
            pass
    print(json.dumps(decide_design(sample), indent=1))