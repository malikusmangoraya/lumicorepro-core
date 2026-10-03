"""Benchmark-First research -- mandatory + deterministic (LumicorePro Part 3).

Before any design decision or code generation, every fresh build must:
  1. decode the industry playbook (deterministic, from ``ai-agent/playbooks``),
  2. decompose international-type reference websites into measurable design
     attributes (inspiration attributes only -- never a template copy),
  3. optionally enrich the profile with a live AI-provider research call,
and merge the merged result into ``spec["reference_spec"]``.

Determinism guarantee: when the provider is unavailable (offline, no key,
rate-limited), a curated international benchmark profile + the on-disk
playbooks always produce a fully-populated ``reference_spec``. The step is
never silently skipped -- identical spec input yields identical output.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lumicorepro.benchmark_first")

try:  # package-relative import (normal runtime)
    from .reference_intelligence import extract_reference_intelligence
    from .design_decision_engine import PlaybookLoader, detect_industry, detect_brand
    from .design_resources import resource_contribution
except Exception:  # pragma: no cover - flat import fallback
    from agent.intelligence.reference_intelligence import extract_reference_intelligence
    from agent.intelligence.design_decision_engine import (
        PlaybookLoader,
        detect_industry,
        detect_brand,
    )
    from agent.intelligence.design_resources import resource_contribution


# ---------------------------------------------------------------------------
# Curated international benchmark peers per industry (attributes, not copies)
# ---------------------------------------------------------------------------
INTERNATIONAL_BENCHMARKS: Dict[str, List[str]] = {
    "ecommerce": [
        "Apple-style product storytelling",
        "Airbnb-style warm marketplace clarity",
        "Shopify-style commerce conversion focus",
    ],
    "marketplace": [
        "Airbnb-style trust-first listings",
        "Etsy-style curated discovery",
    ],
    "saas": [
        "Stripe-style technical clarity",
        "Linear-style restrained futuristic polish",
        "Vercel-style minimal developer trust",
    ],
    "automotive": [
        "Apple-style cinematic product reveal",
        "Porsche-style editorial performance storytelling",
    ],
    "food": [
        "Aesop-style editorial restraint",
        "Airbnb-style warm hospitality imagery",
    ],
    "fintech": [
        "Stripe-style compliance-as-clarity",
        "Revolut-style confident futurism",
    ],
    "portfolio": [
        "Aesop-style editorial whitespace",
        "Apple-style focused product narrative",
    ],
    "education": [
        "Notion-style structured calm",
        "Linear-style outcome-first clarity",
    ],
    "healthcare": [
        "Apple-style calm clarity",
        "Stripe-style trust and legibility",
    ],
    "real-estate": [
        "Airbnb-style lifestyle-led imagery",
        "Aesop-style quiet luxury restraint",
    ],
    "electronics": [
        "Apple-style product-first precision",
        "Samsung-style spec-forward showcase",
    ],
    "industrial": [
        "Stripe-style technical credibility",
        "Vercel-style functional minimalism",
    ],
    "hospitality": [
        "Airbnb-style aspirational imagery",
        "Aesop-style quiet luxury calm",
    ],
    "entertainment": [
        "Spotify-style bold energy",
        "Netflix-style cinematic immersion",
    ],
    "sports": [
        "Nike-style bold motivational energy",
        "Spotify-style vibrant motion",
    ],
    "fashion": [
        "Aesop-style editorial luxury restraint",
        "Supreme-style bold statement minimalism",
    ],
}
_DEFAULT_BENCHMARKS = [
    "Apple-style clarity and restraint",
    "Stripe-style confident usability",
]


def _benchmark_peers(industry: str) -> List[str]:
    return INTERNATIONAL_BENCHMARKS.get(industry, _DEFAULT_BENCHMARKS)


def _normalize(spec: Dict[str, Any]) -> Dict[str, str]:
    """Resolve canonical industry + brand deterministically from a spec."""
    industry = spec.get("industry") or ""
    try:
        industry = detect_industry(spec) if industry not in INTERNATIONAL_BENCHMARKS \
            else industry
    except Exception:
        industry = industry or "saas"
    try:
        brand = spec.get("brand") or detect_brand(spec)
    except Exception:
        brand = spec.get("brand") or "minimal"
    return {"industry": industry, "brand": brand}


def _research_query(spec: Dict[str, Any], industry: str) -> str:
    parts = [
        str(spec.get("project_name") or spec.get("name") or ""),
        str(spec.get("description") or ""),
        str(spec.get("industry") or ""),
    ]
    parts.extend(_benchmark_peers(industry))
    text = " ".join(p for p in parts if p).strip()
    return text or "Apple-style clarity, Stripe-style usability"


def live_research(provider: Any, industry: str, query: str) -> Optional[Dict[str, Any]]:
    """Best-effort live AI research of international-type reference attributes.

    Returns a partial reference-analysis dict on success, else None. Never
    raises -- a failure simply falls back to the deterministic decode.
    """
    if provider is None:
        return None
    prompt = (
        "You are a design researcher. Study current international best-in-class "
        f"websites for the '{industry}' industry. Decompose them into design "
        "attributes only (never copy layouts/branding). Return STRICT JSON with "
        "keys: reference (string), traits (object of 18 attributes in 0..1: "
        "minimalism, whitespace, typography, motion, visual_density, "
        "content_density, image_dominance, color_saturation, warmth, luxury, "
        "cinematic, bold, futuristic, interaction_complexity, craft, "
        "dark_canvas, navigation, cta_focus), hints (array of strings). "
        f"Context: {query[:400]}"
    )
    try:
        # Reference research is a short structured-extraction job, so it goes to
        # the fast tier: it runs before design on every build and must not queue
        # behind a reasoning model. A hand-injected provider still wins.
        try:
            from agent.ai_routing import prefer

            provider, _pname, _ptier = prefer("research", prompt, explicit=provider) or (
                provider,
                "explicit",
                "pinned",
            )
        except Exception:  # pragma: no cover - router is best-effort
            pass
        raw = provider.generate_code(prompt)
        if not isinstance(raw, str):
            return None
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group(0))
        if not isinstance(data, dict) or not data.get("traits"):
            return None
        return data
    except Exception as exc:  # pragma: no cover - network/provider dependent
        logger.warning("Benchmark-First live research skipped (non-blocking): %s", exc)
        return None


def run_benchmark_first(spec: Dict[str, Any],
                        provider: Any = None,
                        live: bool = True) -> Dict[str, Any]:
    """Mandatory, deterministic Benchmark-First step.

    Always returns a populated report and merges ``reference_spec`` into
    ``spec``. Live research (when a provider is available) enriches the
    deterministic decode but can never make the step empty or fail.
    """
    info = _normalize(spec)
    industry, brand = info["industry"], info["brand"]

    loader = PlaybookLoader()
    industry_playbook = loader.industry(industry) or {}
    brand_playbook = loader.brand(brand) or {}

    query = _research_query(spec, industry)
    reference = extract_reference_intelligence(query)

    # Open-source design-resource catalog contribution (deterministic).
    # Matches resource slugs/names/keywords in the query and merges their
    # attribute profiles as inspiration attributes only (never templates).
    resource_spec = resource_contribution(query)

    source = "deterministic"
    live_data = live_research(provider, industry, query) if live else None
    if live_data:
        source = "live+deterministic"
        base_traits = dict(reference.get("traits") or {})
        base_traits.update(live_data.get("traits") or {})
        reference["traits"] = {k: round(float(v), 2) for k, v in base_traits.items()}
        reference["hints"] = sorted(set(
            list(reference.get("hints") or []) + list(live_data.get("hints") or [])
        ))
    if resource_spec.get("count"):
        base_traits = dict(reference.get("traits") or {})
        base_traits.update(resource_spec.get("attributes") or {})
        reference["traits"] = {k: round(float(v), 2) for k, v in base_traits.items()}
        reference["hints"] = sorted(set(
            list(reference.get("hints") or [])
            + [str(m.get("slug")) for m in resource_spec.get("matched") or []]
        ))

    reference_spec = {
        "reference_intelligence": reference,
        "industry_playbook": industry_playbook,
        "brand_playbook": brand_playbook,
        "design_resources": resource_spec,
        "source": source,
    }
    spec.setdefault("reference_spec", {})
    spec["reference_spec"].update(reference_spec)

    report = {
        "source": source,
        "industry": industry,
        "brand": brand,
        "playbook_loaded": bool(industry_playbook),
        "brand_playbook_loaded": bool(brand_playbook),
        "benchmark_peers": _benchmark_peers(industry),
        "research_query": query,
        "reference_spec": reference_spec,
    }
    logger.info(
        "Benchmark-First: source=%s industry=%s playbook=%s peers=%d",
        source, industry, bool(industry_playbook), len(report["benchmark_peers"]),
    )
    return report


__all__ = [
    "INTERNATIONAL_BENCHMARKS",
    "live_research",
    "run_benchmark_first",
]
