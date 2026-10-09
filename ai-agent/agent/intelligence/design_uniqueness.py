"""Deterministic design-signature selection against prior Lumicore projects."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


_VARIANTS = {
    "ui_style": (
        "glassmorphism",
        "minimalist",
        "flat",
        "bento",
        "neobrutalism",
        "neumorphism",
        "claymorphism",
        "skeuomorphism",
        "dark",
    ),
    "hero": (
        "cinematic_video",
        "typographic_hero",
        "interactive_story",
        "product_ui_preview",
        "editorial_photography",
        "minimal_composition",
    ),
    "grid": ("dense_product", "asymmetric_editorial", "balanced"),
    "typography": (
        "display_driven",
        "refined_serif",
        "technical_sans",
        "clean_sans",
    ),
    "motion": ("subtle", "dynamic", "balanced"),
    "image_ratio": ("21:9", "16:9", "4:3"),
    "card_usage": ("minimal", "moderate", "heavy"),
}

_PALETTE_OVERRIDE_KEYS = frozenset({
    "primary", "accent", "heading", "navBg", "footerBg",
    "cardBg", "text", "muted", "border",
})


def normalize_palette_overrides(values: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Keep only supported hex palette values before writing CSS or tokens."""
    if not isinstance(values, dict):
        return {}
    return {
        key: value
        for key, value in values.items()
        if key in _PALETTE_OVERRIDE_KEYS
        and isinstance(value, str)
        and len(value) in (4, 7)
        and value.startswith("#")
        and all(char in "0123456789abcdefABCDEF" for char in value[1:])
    }


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, dict):
        return {
            str(key): _clean(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if item is not None
        }
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value if item is not None]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return str(value).strip().lower()


def extract_design_signature(
    decision: Dict[str, Any],
    design_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a stable fingerprint from design choices actually available."""
    decision = decision if isinstance(decision, dict) else {}
    design_plan = design_plan if isinstance(design_plan, dict) else {}
    manifest = decision.get("design_manifest")
    if not isinstance(manifest, dict):
        manifest = decision

    brand = manifest.get("brand") or {}
    visual = manifest.get("visual") or {}
    typography = manifest.get("typography") or {}
    plan_system = design_plan.get("design_system") or {}
    plan_colors = plan_system.get("colors") or {}
    manifest_colors = manifest.get("colors") or {}
    palette = plan_colors or manifest_colors.get("tokens") or {}
    home_plan = (design_plan.get("page_plans") or {}).get("Home") or {}
    dimensions = {
        "brand_archetype": brand.get("archetype") if isinstance(brand, dict) else brand,
        "visual_direction": decision.get("design_style") or design_plan.get("brand_style"),
        "ui_style": decision.get("ui_style") or visual.get("ui_style"),
        "hero": decision.get("hero") or visual.get("hero"),
        "navigation": decision.get("navigation") or visual.get("navigation"),
        "grid": decision.get("grid") or visual.get("grid"),
        "home_sections": home_plan.get("sections"),
        "typography": decision.get("typography") or typography.get("heading_style"),
        "palette": palette,
        "image_ratio": decision.get("image_ratio") or visual.get("image_ratio"),
        "image_treatment": decision.get("image_treatment") or visual.get("image_treatment"),
        "motion": decision.get("motion") or visual.get("motion"),
        "3d": decision.get("3d") if "3d" in decision else visual.get("3d"),
        "cta_style": decision.get("cta_style") or visual.get("cta_style"),
        "surface_style": decision.get("surface_style") or visual.get("surface_style"),
        "card_usage": decision.get("card_usage") or visual.get("card_usage"),
    }
    normalized = {
        key: _clean(value)
        for key, value in dimensions.items()
        if value is not None and value != ""
    }
    fingerprint = hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"version": 1, "fingerprint": fingerprint, "dimensions": normalized}


def load_portfolio_signatures(
    projects_dir: Path,
    exclude_project: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Read comparable signatures from project manifests without modifying them."""
    root = Path(projects_dir).expanduser()
    if not root.is_dir():
        return []

    excluded = Path(exclude_project).expanduser().resolve() if exclude_project else None
    signatures: List[Dict[str, Any]] = []
    try:
        manifest_paths = root.rglob("design-manifest.json")
        for path in manifest_paths:
            try:
                if excluded is not None and path.parent.resolve() == excluded:
                    continue
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict):
                    continue
                signature = manifest.get("design_signature")
                if not (
                    isinstance(signature, dict)
                    and isinstance(signature.get("dimensions"), dict)
                    and signature["dimensions"]
                ):
                    signature = extract_design_signature(manifest)
                if signature.get("dimensions"):
                    signatures.append(signature)
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                continue
    except OSError:
        raise
    return signatures


def _signature_matches(
    candidate: Dict[str, Any],
    existing: Dict[str, Any],
) -> int:
    candidate_dimensions = candidate.get("dimensions") or {}
    existing_dimensions = existing.get("dimensions") or {}
    shared = set(candidate_dimensions) & set(existing_dimensions)
    return sum(
        candidate_dimensions[key] == existing_dimensions[key]
        for key in shared
    )


def _candidate_decision(
    base: Dict[str, Any],
    constraints: Dict[str, Any],
    seed: str,
    attempt: int,
) -> Dict[str, Any]:
    candidate = copy.deepcopy(base)
    for key, value in constraints.items():
        if key in candidate and value is not None:
            candidate[key] = copy.deepcopy(value)

    for key, allowed in _VARIANTS.items():
        if key in constraints or key not in candidate:
            continue
        options = list(allowed)
        if key == "3d" and candidate.get("industry") in {"healthcare", "fintech", "education"}:
            options = [False]
        digest = hashlib.sha256(f"{seed}:{attempt}:{key}".encode("utf-8")).digest()
        candidate[key] = options[int.from_bytes(digest[:4], "big") % len(options)]
    return candidate


def apply_design_uniqueness(
    decision: Dict[str, Any],
    design_plan: Dict[str, Any],
    prior_signatures: Sequence[Dict[str, Any]],
    seed: str,
    explicit_constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Choose a deterministic, portfolio-distinct decision without mutating inputs."""
    base_decision = copy.deepcopy(decision or {})
    base_plan = copy.deepcopy(design_plan or {})
    constraints = copy.deepcopy(explicit_constraints or {})
    for key, value in constraints.items():
        if key in base_decision and value is not None:
            base_decision[key] = copy.deepcopy(value)
    prior = [
        item for item in prior_signatures
        if isinstance(item, dict) and isinstance(item.get("dimensions"), dict)
    ]

    attempts = 129 if prior else 1
    best_decision = base_decision
    best_signature = extract_design_signature(best_decision, base_plan)
    best_overlap = max((_signature_matches(best_signature, item) for item in prior), default=-1)

    for attempt in range(attempts):
        candidate = _candidate_decision(base_decision, constraints, str(seed), attempt)
        signature = extract_design_signature(candidate, base_plan)
        overlap = max((_signature_matches(signature, item) for item in prior), default=-1)
        if overlap < best_overlap:
            best_decision, best_signature, best_overlap = candidate, signature, overlap
        if best_overlap <= 0:
            break

    manifest = best_decision.get("design_manifest")
    if isinstance(manifest, dict):
        visual = manifest.setdefault("visual", {})
        for key in (
            "ui_style", "hero", "navigation", "grid", "motion", "3d",
            "image_ratio", "image_treatment", "cta_style", "surface_style",
            "card_usage",
        ):
            if key in best_decision:
                visual[key] = copy.deepcopy(best_decision[key])
        typography = manifest.setdefault("typography", {})
        if "typography" in best_decision:
            typography["heading_style"] = copy.deepcopy(best_decision["typography"])
        colors = manifest.setdefault("colors", {"tokens": {}})
        plan_colors = (base_plan.get("design_system") or {}).get("colors") or {}
        if plan_colors:
            colors["tokens"] = copy.deepcopy(plan_colors)
        manifest["design_signature"] = copy.deepcopy(best_signature)
    base_plan["design_signature"] = copy.deepcopy(best_signature)
    base_plan["design_decision"] = copy.deepcopy(best_decision)
    comparison = {
        "compared_projects": len(prior),
        "maximum_matching_dimensions": max(
            (_signature_matches(best_signature, item) for item in prior), default=0
        ),
        "seed": str(seed),
    }
    return {
        "decision": best_decision,
        "design_plan": base_plan,
        "design_signature": best_signature,
        "comparison": comparison,
    }