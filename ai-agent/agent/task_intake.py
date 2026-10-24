"""Market-first task intake.

Contract with the operator:
1. ``analyze_demand(prompt)`` - run a real international-market analysis for any
   task BEFORE any building starts: industry benchmark intelligence
   (MarketAnalyzer), optional live community demand signals (Reddit/Twitter via
   agent.reach.market_signals), a demand estimate, and candidate PRICING bands.
   It always returns 2-4 concrete product options, each with demand and price
   evidence, so the operator can choose what actually gets built.
2. ``build_blueprint(intake, option_id)`` - after one option is chosen, produce
   the full real build structure (mode, stack, features, pages, API surface,
   database tables, integrations, legal pages, i18n, QA gates, deployment plan
   and acceptance criteria). Nothing is invented: every feature maps to a
   contract key the pipeline knows how to deliver, and the market guidance is
   carried through so downstream phases consume it.

This module is output-only reasoning over data - it never performs network
calls itself; live signals are provided via ``market_signals_sync``.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agent.market_analyzer import MarketAnalyzer

# ---------------------------------------------------------------------------
# Input understanding: small deterministic keyword map. The requirement
# analyzer refines further downstream; intake only needs the industry class.
# ---------------------------------------------------------------------------
_INDUSTRY_KEYWORDS: List[tuple] = [
    ("fintech", ("fintech", "payments", "banking", "loan", "wallet", "invest", "trading", "invoice")),
    ("healthcare", ("health", "clinic", "doctor", "patient", "appointment", "medical", "telemedicine")),
    ("education", ("school", "course", "coaching", "learning", "tuition", "academy", "student")),
    ("realestate", ("real estate", "property", "rental", "listings", "land", "apartment", "housing")),
    ("restaurant", ("restaurant", "cafe", "food", "catering", "menu", "delivery", "kitchen")),
    ("ecommerce", ("shop", "store", "ecommerce", "product", "sell", "cart", "checkout", "brand")),
    ("saas", ("saas", "dashboard", "b2b", "tool", "platform", "crm", "erp", "analytics", "automation")),
    ("agency", ("agency", "portfolio", "freelance", "studio", "creative", "branding")),
    ("blog", ("blog", "content", "articles", "newsletter", "magazine")),
    ("event", ("event", "wedding", "conference", "ticket", "booking")),
]

# Indicative monthly subscription anchors per market-size class (USD).
# Basis: typical international B2C/B2B SaaS tier ladders by addressable
# market heat. Every emitted price carries `"estimate": True` and the
# competitor list so the operator can verify against live competitor prices.
_SIZE_PRICE_ANCHOR: Dict[str, tuple] = {
    "explosive": (29, 499),
    "volatile": (24, 299),
    "large": (19, 299),
    "growing": (15, 199),
    "medium": (12, 149),
    "small": (9, 79),
}

_OPTION_MULTIPLIER: Dict[str, float] = {
    "lean_mvp": 0.5,
    "full_saas": 1.0,
    "niche_differentiated": 1.3,
    "internal_tool": 0.8,
}

_SIZE_DEMAND_BOOST: Dict[str, int] = {
    "explosive": 20, "large": 15, "growing": 10, "medium": 5, "volatile": 8, "small": 0,
}


def _infer_industry(prompt: str) -> str:
    p = prompt.lower()
    for industry, keys in _INDUSTRY_KEYWORDS:
        if any(k in p for k in keys):
            return industry
    return "general"


_SIZE_ALIAS: Dict[str, str] = {"enterprise": "large", "niche": "small"}


def _size_class(market_profile: Dict[str, Any]) -> str:
    size = str((market_profile or {}).get("market_size", "medium")).lower()
    size = _SIZE_ALIAS.get(size, size)
    return size if size in _SIZE_PRICE_ANCHOR else "medium"


def _apply_growth(anchor: tuple, multiplier: float) -> Dict[str, Any]:
    low = round(anchor[0] * multiplier)
    high = round(anchor[1] * multiplier)
    return {"estimate": True, "currency": "USD", "monthly_low": max(low, 9),
            "monthly_high": max(high, 19),
            "basis": "indicative SaaS tier band for this market-size class; verify against competitor pricing",
           }


def _option_features(option_id: str, spec: Dict[str, Any], analysis: Dict[str, Any], difference_hook: Optional[str]) -> List[str]:
    """Feature keys come from the generation contract the pipeline understands."""
    wa = bool(analysis.get("whatsapp_market"))
    lean = ["landing_page_generation", "contact_form", "seo_pack", "responsive_layout"]
    if wa:
        lean.append("whatsapp_float")
    full = ["authentication", "users", "dashboard", "contact_form", "jwt_auth",
            "email_notifications", "seo_pack", "responsive_layout", "pwa_support",
            "i18n_multilingual", "payments_ready"]
    internal = ["authentication", "dashboard", "role_based_access", "reporting_exports",
                "audit_log", "contact_form", "responsive_layout"]
    niche = list(full)
    if difference_hook:
        niche.append(difference_hook)
    return {"lean_mvp": lean, "full_saas": full, "niche_differentiated": niche,
            "internal_tool": internal}[option_id]


def _option_positions(option_id: str, analysis: Dict[str, Any], difference_hook: Optional[str]) -> str:
    base = analysis.get("recommended_positioning", "Premium international platform")
    if option_id == "lean_mvp":
        return f"{base} - launch-fast marketing site + lead capture (no backend complexity)"
    if option_id == "full_saas":
        return f"{base} - complete subscription product with accounts, dashboard and payments"
    if option_id == "niche_differentiated":
        hook = f' - differentiated hook: {difference_hook}' if difference_hook else ""
        return f"{base}{hook}"
    return f"{base} - internal operations tool for one organization (no public subscriptions)"


def _demand(score: int, evidence: List[str]) -> Dict[str, Any]:
    if score >= 80:
        band = "high"
    elif score >= 60:
        band = "solid"
    elif score >= 40:
        band = "emerging"
    else:
        band = "early"
    return {"score": max(0, min(100, score)), "band": band, "evidence": evidence}


def _price_option(option_id: str, spec: Dict[str, Any], analysis: Dict[str, Any],
                  difference_hook: Optional[str]) -> Dict[str, Any]:
    anchor = _SIZE_PRICE_ANCHOR[_size_class(analysis.get("market_profile"))]
    return _apply_growth(anchor, _OPTION_MULTIPLIER[option_id])


def propose_options(spec: Dict[str, Any], analysis: Dict[str, Any], signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate 3-4 buildable variants with demand + indicative pricing."""
    preferred = [str(p) for p in (signals.get("preferred_features") or []) if str(p).strip()]
    complaints = [str(c) for c in (signals.get("complaints") or []) if str(c).strip()]
    difference_hook = None
    hook_source = None
    if preferred:
        difference_hook = "live_signal_" + re.sub(r"\W+", "_", preferred[0].lower())[:40]
        hook_source = f"live community demand: '{preferred[0]}'"
    elif analysis.get("differentiation_opportunities"):
        first = str(analysis["differentiation_opportunities"][0])
        if "Growth opportunity:" in first:
            difference_hook = first.split("Growth opportunity:", 1)[1].strip().replace(" ", "_").lower()
            hook_source = f"market gap: {first.strip()}"

    fragments = signals.get("fragments") or []
    evidence: List[str] = []
    for f in fragments[:3]:
        if isinstance(f, dict):
            snippet = f.get("snippet") or f.get("title") or f.get("text") or ""
        else:
            snippet = getattr(f, "snippet", "") or getattr(f, "title", "")
        if snippet:
            evidence.append(str(snippet)[:120])
    market_profile = analysis.get("market_profile") or {}
    base_score = 50 + _SIZE_DEMAND_BOOST.get(_size_class(market_profile), 5)
    base_score += min(20, len(fragments) * 4)
    if analysis.get("mobile_priority"):
        base_score += 5
    if analysis.get("pk_market_growth") and analysis["pk_market_growth"] != "N/A":
        base_score += 5
    demand = _demand(base_score, evidence)

    options = []
    for option_id in ("lean_mvp", "full_saas", "niche_differentiated", "internal_tool"):
        options.append({
            "id": option_id,
            "name": {
                "lean_mvp": "Lean MVP - fast public launch",
                "full_saas": "Full SaaS product - accounts + payments",
                "niche_differentiated": "Differentiated SaaS - market-gap edition",
                "internal_tool": "Internal tool - private operations",
            }[option_id],
            "positioning": _option_positions(option_id, analysis, difference_hook),
            "features": _option_features(option_id, spec, analysis, difference_hook),
            "differentiation_hook": hook_source if option_id == "niche_differentiated" else None,
            "buyer_mode": "client_static" if option_id == "lean_mvp" else "enterprise_fullstack",
            "demand": demand if option_id != "lean_mvp" else _demand(max(demand["score"] - 10, 0), demand["evidence"]),
            "monthly_price": None if option_id == "internal_tool" else _price_option(option_id, spec, analysis, difference_hook),
            "estimated_effort_days": {"lean_mvp": "2-4", "full_saas": "5-8",
                                      "niche_differentiated": "5-10", "internal_tool": "3-6"}[option_id],
            "risk": {
                "lean_mvp": "no recurring revenue path until payments are added",
                "full_saas": "must ship legal (refund/privacy/consent) + payment provider to charge",
                "niche_differentiated": "gap must be verified against live competitor pricing before launch",
                "internal_tool": "internal only - no public market monetization",
            }[option_id],
        })
    return options


def analyze_demand(prompt: str, use_live_signals: bool = True,
                   signals_runner=None, timeout: float = 25.0) -> Dict[str, Any]:
    """Phase 1 for an operator task: market demand + pricing + product options.

    ``signals_runner`` is an injectable ``market_signals_sync(prompt_spec,
    timeout)`` for tests/offline use; by default the real Reddit/Twitter sync
    collector is used and degrades silently when channels are unreachable.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt is required")
    prompt = prompt.strip()
    spec: Dict[str, Any] = {
        "prompt": prompt,
        "industry": _infer_industry(prompt),
        "website_type": "saas" if any(k in prompt.lower() for k in ("dashboard", "saas", "platform", "tool")) else "ecommerce",
        "features": [],
        "name": None,
    }
    signals: Dict[str, Any] = {}
    if use_live_signals:
        try:
            if signals_runner is not None:
                signals = signals_runner(spec, timeout) or {}
            else:
                from agent.reach.market_signals import market_signals_sync
                signals = market_signals_sync(spec, timeout=timeout) or {}
        except Exception as exc:  # noqa: BLE001 - signals are optional
            signals = {"error": str(exc)[:200]}
    market_analyzer = MarketAnalyzer()
    analysis = market_analyzer.analyze(spec, signals.get("fragments") and signals or None)
    if not analysis:
        raise RuntimeError("market analysis produced no data")
    intake: Dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "status": "options_ready",
        "prompt": prompt,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec": spec,
        "market": analysis,
        "live_signals": signals if use_live_signals else None,
        "options": propose_options(spec, analysis, signals),
        "selected_option_id": None,
        "blueprint": None,
    }
    return intake


def build_blueprint(intake: Dict[str, Any], option_id: str, product_name: Optional[str] = None,
                    design_style: Optional[str] = None) -> Dict[str, Any]:
    """Chosen option -> concrete real build structure the pipeline executes."""
    if not isinstance(intake, dict) or not intake.get("market") or not intake.get("options"):
        raise ValueError("run analyze_demand() first")
    option = next((o for o in intake["options"] if o["id"] == option_id), None)
    if option is None:
        raise ValueError(f"unknown option_id: {option_id}; available: {[o['id'] for o in intake['options']]}")
    intake["selected_option_id"] = option_id

    analysis = intake["market"]
    features = list(option["features"])
    is_fullstack = option["buyer_mode"] == "enterprise_fullstack"
    db_tables = ["users", "articles"] if analysis["industry"] == "blog" else (["users", "records"] if is_fullstack else [])
    if is_fullstack:
        db_tables = ["users"] + [d for d in db_tables if d != "users"]
        if "payments_ready" in features:
            db_tables.append("credit_ledger")
        if "contact_form" in features:
            db_tables.append("contact_messages")

    blueprint: Dict[str, Any] = {
        "status": "blueprint_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product": product_name or (intake.get("spec", {}).get("name") or "Untitled Product"),
        "market_guidance": {
            "positioning": option["positioning"],
            "must_have_drivers": [g["driver"] for g in
                                  ([{"driver": d} for d in analysis.get("conversion_drivers", [])])][:4],
            "investigations": analysis.get("differentiation_opportunities", [])[:4],
            "mobile_priority": bool(analysis.get("mobile_priority")),
            "target_lighthouse": analysis.get("target_lighthouse_score"),
            "competitors": analysis.get("competitors", [])[:5],
        },
        "selected_option": option,
        "mode": "enterprise_fullstack" if is_fullstack else "client_static",
        "stack": {
            "frontend": "React 19 + Vite + Tailwind 3 (design tokens, dark mode, i18n/RTL, reduced-motion)",
            "backend": "Express 4 + Sequelize 6 + JWT auth + validated routes" if is_fullstack else "none (static hosting)",
            "database": "PostgreSQL (Neon) + versioned migrations + soft deletes" if is_fullstack else "none",
            "hosting": "Vercel (edge) + database marketplace integration",
        },
        "features": features,
        "pages": (["home", "features", "pricing", "about", "contact",
                   "privacy", "terms", "refund_policy", "cookie_policy"]
                  + (["login", "register", "dashboard", "history", "credits"] if is_fullstack else [])),
        "api_surface": (["POST /auth/register (transactional user+initial credits)",
                         "POST /auth/login", "POST /auth/refresh",
                         "GET/POST accounts", "GET history", "POST selection action", "GET health (DB-checked)"]
                        if is_fullstack else ["POST /contact (rate-limited)", "GET health"]),
        "db_tables": db_tables,
        "integrations": {
            "payments": "none in lean/internal; Stripe-compatible flow in paid options (tax + refunds + webhooks)",
            "ai_provider": "any OpenAI-compatible key (OpenAI/OpenRouter/DeepSeek/Gemini); demo generator without key",
            "email": "transactional welcome + password reset when fullstack",
            "analytics": "consent-gated, cookie banner included",
        },
        "legal_required": ["privacy", "terms", "refund_policy", "cookie_consent",
                           *(["data_processing_agreement"] if is_fullstack else [])],
        "i18n": {"locales": ["en"], "rtl_ready": True, "expand_when": "market priority"},
        "qa_gates": {
            "tests": "pytest/vitest suites green (no production DB usage)",
            "build": "production build clean",
            "market_audit": "POST /api/market-audit must score >= 80 (STANDARD) with no legal/international fails",
            "design_score": "STANDARD 80 (PREMIUM 88 target on paid options)",
        },
        "acceptance_criteria": [
            "registered user journey works end-to-end without manual fixes",
            "market_audit overall >= 80 with all legal checks passing",
            "no placeholder copy, no debugging logs, .env.example complete",
            "deployment smoke: health endpoint reports DB-healthy",
        ],
        "next_steps": [
            "confirm product name + primary market (default: international/US pricing)",
            "approve blueprint -> run orchestrator with this option",
            "on completion: run quality_gate + market_audit and ship the client package",
        ],
    }
    if design_style:
        blueprint["design_style"] = design_style
    intake["blueprint"] = blueprint
    intake["status"] = "awaiting_build_approval"
    return blueprint


def blueprint_summary(blueprint: Dict[str, Any]) -> str:
    """One-glance text for chat/UI confirmation."""
    m = blueprint["market_guidance"]
    lines = [
        f"Product: {blueprint['product']} ({blueprint['mode']})",
        f"Positioning: {m['positioning']}",
        f"Must implement first: {', '.join(m['must_have_drivers'][:4])}",
        f"Features: {len(blueprint['features'])} mapped to contract keys",
        f"Pages: {len(blueprint['pages'])} | DB tables: {len(blueprint['db_tables'])} | API: {len(blueprint['api_surface'])} groups",
        f"Legal: {', '.join(blueprint['legal_required'])}",
        f"QA: {blueprint['qa_gates']['market_audit']} | tests+build clean",
    ]
    return "\n".join(lines)
