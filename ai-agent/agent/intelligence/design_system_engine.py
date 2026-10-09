"""Deterministic, niche-aware design DNA selection for new website builds."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..design_style import DesignStyleEngine


HERO_ARCHETYPES: List[Dict[str, Any]] = [
    {"id": "typographic", "niches": ["saas", "portfolio", "editorial", "finance"]},
    {"id": "editorial_image", "niches": ["portfolio", "real_estate", "travel", "food", "fashion"]},
    {"id": "split_product_preview", "niches": ["saas", "technology", "finance", "education"]},
    {"id": "cinematic_media", "niches": ["entertainment", "travel", "events", "fashion", "automotive"]},
    {"id": "search_led_catalog", "niches": ["ecommerce", "real_estate", "travel", "jobs"]},
    {"id": "product_configurator", "niches": ["ecommerce", "automotive", "fashion", "electronics"]},
    {"id": "dashboard_preview", "niches": ["saas", "finance", "insurance", "healthcare"]},
    {"id": "service_booking", "niches": ["healthcare", "fitness", "hospitality", "local_business"]},
    {"id": "map_local_discovery", "niches": ["hospitality", "food", "travel", "real_estate"]},
    {"id": "story_narrative", "niches": ["nonprofit", "education", "portfolio", "food"]},
    {"id": "event_date", "niches": ["events", "entertainment", "education", "sports"]},
    {"id": "data_metrics", "niches": ["insurance", "finance", "saas", "healthcare", "technology"]},
]

NAVIGATION_PATTERNS: List[Dict[str, Any]] = [
    {"id": "minimal_top", "niches": ["saas", "portfolio", "finance", "technology"]},
    {"id": "editorial_masthead", "niches": ["editorial", "portfolio", "food", "fashion"]},
    {"id": "commerce_category_bar", "niches": ["ecommerce", "fashion", "electronics"]},
    {"id": "workspace_sidebar", "niches": ["saas", "insurance", "finance", "healthcare"]},
    {"id": "centered_brand", "niches": ["hospitality", "travel", "real_estate", "food"]},
    {"id": "utility_dashboard", "niches": ["saas", "insurance", "finance", "healthcare"]},
    {"id": "local_contact", "niches": ["local_business", "food", "fitness", "hospitality"]},
    {"id": "immersive_overlay", "niches": ["events", "entertainment", "fashion", "automotive"]},
]

SECTION_BLOCKS: List[Dict[str, Any]] = [
    {"id": "product_catalog", "niches": ["ecommerce", "electronics", "fashion", "automotive"]},
    {"id": "service_booking", "niches": ["healthcare", "fitness", "hospitality", "local_business"]},
    {"id": "property_listings", "niches": ["real_estate"]},
    {"id": "menu_reservations", "niches": ["food", "hospitality"]},
    {"id": "course_curriculum", "niches": ["education"]},
    {"id": "fitness_program", "niches": ["fitness", "healthcare", "sports"]},
    {"id": "claims_queue", "niches": ["insurance"]},
    {"id": "claims_intake", "niches": ["insurance"]},
    {"id": "coverage_review", "niches": ["insurance"]},
    {"id": "portfolio_cases", "niches": ["portfolio", "creative"]},
    {"id": "event_schedule", "niches": ["events", "entertainment", "education", "sports"]},
    {"id": "travel_itinerary", "niches": ["travel", "hospitality"]},
    {"id": "product_features", "niches": ["saas", "technology", "finance", "education"]},
    {"id": "pricing_options", "niches": ["saas", "ecommerce", "fitness", "education"]},
    {"id": "faq_answers", "niches": ["saas", "insurance", "healthcare", "ecommerce"]},
    {"id": "contact_cta", "niches": ["*"]},
]

_NICHE_ALIASES = {
    "claims": "insurance",
    "insurance claims": "insurance",
    "claim intake": "insurance",
    "real estate": "real_estate",
    "property": "real_estate",
    "restaurant": "food",
    "restaurants": "food",
    "photography": "portfolio",
    "creative studio": "creative",
    "events and ticketing": "events",
    "event ticketing": "events",
    "travel and tourism": "travel",
    "travel tourism": "travel",
    "fitness coaching": "fitness",
    "online learning": "education",
    "e commerce": "ecommerce",
    "e-commerce": "ecommerce",
    "b2b saas": "saas",
    "fintech": "finance",
    "banking": "finance",
    "software": "technology",
    "ai": "technology",
    "automotive commerce": "automotive",
}

_NICHE_RECIPES = {
    "insurance": ["claims_intake", "claims_queue", "coverage_review", "faq_answers", "contact_cta"],
    "real_estate": ["property_listings", "service_booking", "faq_answers", "contact_cta"],
    "food": ["menu_reservations", "service_booking", "contact_cta"],
    "education": ["course_curriculum", "event_schedule", "faq_answers", "contact_cta"],
    "fitness": ["fitness_program", "service_booking", "pricing_options", "contact_cta"],
    "portfolio": ["portfolio_cases", "product_features", "contact_cta"],
    "creative": ["portfolio_cases", "product_features", "contact_cta"],
    "events": ["event_schedule", "product_catalog", "contact_cta"],
    "travel": ["travel_itinerary", "product_catalog", "contact_cta"],
    "ecommerce": ["product_catalog", "pricing_options", "faq_answers", "contact_cta"],
    "electronics": ["product_catalog", "product_features", "faq_answers", "contact_cta"],
    "automotive": ["product_catalog", "service_booking", "contact_cta"],
    "finance": ["product_features", "pricing_options", "faq_answers", "contact_cta"],
    "saas": ["product_features", "pricing_options", "faq_answers", "contact_cta"],
    "technology": ["product_features", "pricing_options", "contact_cta"],
    "healthcare": ["service_booking", "faq_answers", "contact_cta"],
    "hospitality": ["service_booking", "menu_reservations", "contact_cta"],
}


def get_design_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """Return the declarative layout catalog without exposing mutable globals."""
    return {
        "heroes": [dict(item, niches=list(item["niches"])) for item in HERO_ARCHETYPES],
        "navigation": [dict(item, niches=list(item["niches"])) for item in NAVIGATION_PATTERNS],
        "sections": [dict(item, niches=list(item["niches"])) for item in SECTION_BLOCKS],
    }


def normalize_niche(value: Any) -> str:
    """Normalize industry labels and common brief phrases to a niche key."""
    text = re.sub(r"\s+", " ", str(value or "").strip().lower().replace("_", " "))
    if text in _NICHE_ALIASES:
        return _NICHE_ALIASES[text]
    for alias, normalized in sorted(_NICHE_ALIASES.items(), key=lambda pair: len(pair[0]), reverse=True):
        if alias in text:
            return normalized
    if text in {"saas", "insurance", "ecommerce", "electronics", "automotive", "food", "travel", "events", "fitness", "education", "healthcare", "hospitality", "portfolio", "creative", "finance", "technology", "real estate"}:
        return "real_estate" if text == "real estate" else text
    return text.replace(" ", "_") or "business"


def _stable_int(seed: str, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _weighted_choice(
    items: Sequence[Dict[str, Any]],
    niche: str,
    seed: str,
    label: str,
    excluded: Sequence[str] = (),
) -> str:
    weighted: List[str] = []
    for item in items:
        fit = item.get("niches", [])
        weight = 5 if niche in fit else 1 if "*" in fit else 0
        if weight:
            weighted.extend([str(item["id"])] * weight)
    if not weighted:
        weighted = [str(item["id"]) for item in items]
    start = _stable_int(seed, label) % len(weighted)
    for offset in range(len(weighted)):
        candidate = weighted[(start + offset) % len(weighted)]
        if candidate not in excluded:
            return candidate
    return weighted[start]


def _contrast_foreground(background: str) -> str:
    """Use the existing style helper's foreground choice for solid hex colors."""
    if not isinstance(background, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", background):
        return "#111827"
    from ..design_style import _fg_for

    return _fg_for(background)


def _build_tokens(spec: Dict[str, Any], niche: str) -> Dict[str, Any]:
    style_spec = {
        "industry": niche,
        "website_type": spec.get("website_type", ""),
        "design_style": spec.get("design_style", ""),
    }
    style_engine = DesignStyleEngine()
    style = style_engine.resolve_style(style_spec)
    source = style_engine.build_tokens(style, str(spec.get("project_name") or "generated-site"))
    palette = style.get("color", {})
    overrides = spec.get("design_blueprint", {}).get("palette", {})
    if not isinstance(overrides, dict):
        overrides = {}
    palette = {**palette, **overrides}
    return {
        "colors": {
            "canvas": palette.get("bg", "#ffffff"),
            "surface": palette.get("card", "#f8fafc"),
            "primary": palette.get("primary", "#111827"),
            "accent": palette.get("accent", palette.get("secondary", "#0ea5e9")),
            "text": palette.get("text", "#111827"),
            "text_on_primary": _contrast_foreground(palette.get("primary", "#111827")),
            "muted": palette.get("muted", "#64748b"),
            "border": palette.get("border", "#e2e8f0"),
        },
        "typography": source.get("typography", {}),
        "spacing": {"unit": "4px", "scale": [4, 8, 12, 16, 24, 32, 48, 64, 96]},
        "radius": source.get("radius", {}),
        "shadows": source.get("shadow", {}),
        "motion": {
            "intensity": str(spec.get("animation_intensity") or "subtle"),
            "reduced_motion": "disable_nonessential",
        },
        "style_id": style.get("id", "minimalism"),
    }


class DesignSystemEngine:
    """Select reproducible layout and visual DNA before project generation."""

    MAX_ATTEMPTS = 3

    def resolve(
        self,
        spec: Dict[str, Any],
        prior: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        spec = spec if isinstance(spec, dict) else {}
        niche = normalize_niche(spec.get("industry") or spec.get("niche") or spec.get("website_type"))
        project = str(spec.get("project_name") or "generated-site").strip()
        brief = str(spec.get("original_prompt") or spec.get("prompt") or "").strip()
        seed = str(spec.get("design_seed") or spec.get("seed") or hashlib.sha256(
            f"{brief.lower()}|{project.lower()}|{niche}".encode("utf-8")
        ).hexdigest())
        constraints = spec.get("design_constraints") or {}
        if not isinstance(constraints, dict):
            constraints = {}
        explicit = {
            "hero": constraints.get("hero") or constraints.get("hero_archetype"),
            "navigation": constraints.get("navigation") or constraints.get("navigation_pattern") or constraints.get("nav_pattern"),
            "home_sections": constraints.get("home_sections"),
        }
        explicit = {key: value for key, value in explicit.items() if value is not None}
        if explicit.get("hero") and explicit["hero"] not in {item["id"] for item in HERO_ARCHETYPES}:
            raise ValueError(f"Unknown hero archetype: {explicit['hero']}")
        if explicit.get("navigation") and explicit["navigation"] not in {item["id"] for item in NAVIGATION_PATTERNS}:
            raise ValueError(f"Unknown navigation pattern: {explicit['navigation']}")

        prior_dimensions = [
            item.get("dimensions", {}) for item in (prior or [])
            if isinstance(item, dict) and isinstance(item.get("dimensions"), dict)
        ]
        attempts: List[Dict[str, Any]] = []
        best_dna: Optional[Dict[str, Any]] = None
        best_matches = 4
        selected_heroes: List[str] = []
        selected_navigation: List[str] = []
        for attempt_index in range(self.MAX_ATTEMPTS):
            attempt_seed = f"{seed}:{attempt_index}"
            hero = explicit.get("hero") or _weighted_choice(
                HERO_ARCHETYPES,
                niche,
                attempt_seed,
                "hero",
                excluded=selected_heroes,
            )
            navigation = explicit.get("navigation") or _weighted_choice(
                NAVIGATION_PATTERNS,
                niche,
                attempt_seed,
                "navigation",
                excluded=selected_navigation,
            )
            selected_heroes.append(hero)
            selected_navigation.append(navigation)
            section_order = list(explicit.get("home_sections") or _NICHE_RECIPES.get(
                niche, ["product_features", "faq_answers", "contact_cta"]
            ))
            if section_order and section_order[0] == "hero":
                section_order = section_order[1:]
            dimensions = {
                "hero": hero,
                "navigation": navigation,
                "home_sections": ["hero", *section_order],
            }
            matches = max((
                sum(dimensions[key] == previous.get(key) for key in dimensions)
                for previous in prior_dimensions
            ), default=0)
            collided = matches == len(dimensions)
            attempt_record = {
                "number": attempt_index + 1,
                **dimensions,
                "matching_dimensions": matches,
                "collision": collided,
            }
            attempts.append(attempt_record)
            dna = self._make_dna(spec, project, seed, niche, hero, navigation, section_order, attempt_record)
            if matches < best_matches:
                best_dna, best_matches = dna, matches
            if not collided:
                best_dna = dna
                break

        if best_dna is None:
            raise RuntimeError("Design selection produced no candidates")
        unique = best_matches < 3
        best_dna["selection"]["unique"] = unique
        best_dna["selection"]["attempts"] = attempts
        best_dna["selection"]["attempt_count"] = len(attempts)
        return {
            "design_dna": best_dna,
            "attempts": attempts,
            "comparison": {
                "compared_projects": len(prior_dimensions),
                "maximum_matching_dimensions": best_matches,
                "threshold": 3,
                "unique": unique,
            },
        }

    def _make_dna(
        self,
        spec: Dict[str, Any],
        project: str,
        seed: str,
        niche: str,
        hero: str,
        navigation: str,
        section_order: Iterable[str],
        attempt: Dict[str, Any],
    ) -> Dict[str, Any]:
        audience = spec.get("audience") or spec.get("target_audience") or ["people evaluating this product"]
        if isinstance(audience, str):
            audience = [audience]
        tone = spec.get("tone") or spec.get("brand_voice") or "clear, specific, and trustworthy"
        if isinstance(tone, list):
            tone = ", ".join(str(value) for value in tone)
        pages = {
            "Home": {"section_order": ["hero", *list(section_order)]},
        }
        dimensions = {
            "hero": hero,
            "navigation": navigation,
            "home_sections": pages["Home"]["section_order"],
        }
        grid_system = "asymmetric_12_column" if _stable_int(seed, "grid") % 2 else "editorial_2_column"
        density = "compact" if _stable_int(seed, "density") % 2 else "spacious"
        tokens = _build_tokens(spec, niche)
        tokens["layout"] = {
            "container_max": "72rem" if grid_system == "editorial_2_column" else "80rem",
            "hero_columns": (
                "minmax(0, 1fr) minmax(0, 0.82fr)"
                if grid_system == "editorial_2_column"
                else "repeat(12, minmax(0, 1fr))"
            ),
            "tablet_breakpoint": "48rem",
            "sidebar_width": "18rem" if density == "compact" else "20rem",
            "card_min_width": "18rem",
            "heading_measure": "14ch",
            "body_measure": "62ch",
            "section_measure": "48rem",
            "hero_copy_span": 7 if grid_system == "asymmetric_12_column" else 1,
            "hero_visual_span": 5 if grid_system == "asymmetric_12_column" else 1,
            "page_min_height": "100vh",
        }
        tokens["borders"] = {"width": "1px"}
        tokens["typography"]["line_height_heading"] = "1.05"
        tokens["typography"]["line_height_body"] = "1.6"
        tokens["typography"]["weight_strong"] = 700
        tokens["motion"]["reduced_duration"] = "0.01ms"
        canonical = {
            "version": 1,
            "project": project,
            "seed": seed,
            "niche": niche,
            "audience": list(audience),
            "tone": str(tone),
            "tokens": tokens,
            "layout": {
                "navigation_pattern": navigation,
                "hero_archetype": hero,
                "pages": pages,
                "grid_system": grid_system,
                "card_style": "bordered" if _stable_int(seed, "cards") % 2 else "open_surface",
                "footer_type": "sitemap_columns" if _stable_int(seed, "footer") % 2 else "editorial_contact",
                "density": density,
            },
            "content_sources": {
                "brief_sha256": hashlib.sha256(str(spec.get("original_prompt") or spec.get("prompt") or "").encode("utf-8")).hexdigest(),
                "allowed_claims": list(spec.get("verified_claims") or []),
                "logos": list(spec.get("verified_logos") or []),
                "testimonials": list(spec.get("verified_testimonials") or []),
            },
            "selection": {
                "niche_fit_seed": seed,
                "constraints": dict(spec.get("design_constraints") or {}),
                "last_candidate": attempt["number"],
                "unique": not attempt["collision"],
            },
        }
        fingerprint_source = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        canonical["fingerprint"] = {
            "algorithm": "sha256",
            "value": hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest(),
            "dimensions": dimensions,
        }
        return canonical