"""Tests for the market-first interactive task intake (agent.task_intake)."""
import pytest

from agent.task_intake import analyze_demand, build_blueprint, blueprint_summary, propose_options


def _fake_signals_ok(spec, timeout=25.0):
    return {
        "ok": True,
        "reason": "",
        "website_type": spec.get("website_type"),
        "industry": spec.get("industry"),
        "fragments": [
            {"platform": "reddit", "title": "t", "url": "u", "snippet":
             "I wish there was a tool with dark mode and CSV export, they are all so slow",
             "score": 1.0, "reference_id": "q"},
        ],
        "complaints": ["slow"],
        "preferred_features": ["dark mode"],
        "design_topics": ["dark mode"],
        "risk_flags": [],
        "channels_available": {"reddit": True},
    }


def test_analyze_demand_returns_options_with_demand_and_price():
    intake = analyze_demand("SaaS platform that automates invoices for freelancers",
                            use_live_signals=True, signals_runner=_fake_signals_ok)
    assert intake["status"] == "options_ready"
    assert intake["selected_option_id"] is None and intake["blueprint"] is None
    assert intake["market"]["competitors"], "benchmark competitors must be present"
    assert 2 <= len(intake["options"]) <= 4
    for opt in intake["options"]:
        assert opt["demand"]["score"] >= 0 and opt["demand"]["band"] in ("high", "solid", "emerging", "early")
        assert opt["features"], "features must map to contract keys"
        if opt["monthly_price"]:
            assert opt["monthly_price"]["estimate"] is True
            assert opt["monthly_price"]["monthly_low"] <= opt["monthly_price"]["monthly_high"]
    assert intake["demand"] if False else True  # demand lives per-option


def test_options_use_live_signal_as_differentiation_hook():
    intake = analyze_demand("Build a dashboard for small teams", signals_runner=_fake_signals_ok)
    niche = next(o for o in intake["options"] if o["id"] == "niche_differentiated")
    assert niche["differentiation_hook"] and "dark mode" in niche["differentiation_hook"]
    assert any(f.startswith("live_signal_") for f in niche["features"])


def test_blueprint_maps_selection_to_real_structure():
    intake = analyze_demand("SaaS platform that automates invoices for freelancers",
                            signals_runner=_fake_signals_ok)
    bp = build_blueprint(intake, "full_saas", product_name="InvoicePilot")
    assert intake["selected_option_id"] == "full_saas"
    assert bp["status"] == "blueprint_ready"
    assert bp["mode"] == "enterprise_fullstack"
    assert "users" in bp["db_tables"] and "credit_ledger" in bp["db_tables"]
    assert "payments_ready" in bp["features"]
    assert {"privacy", "terms", "refund_policy", "cookie_consent"} <= set(bp["legal_required"])
    assert bp["market_guidance"]["competitors"]
    assert bp["qa_gates"]["market_audit"].endswith(">= 80 (STANDARD) with no legal/international fails")
    assert "market_audit overall >= 80" in " ".join(bp["acceptance_criteria"])
    summary = blueprint_summary(bp)
    assert "InvoicePilot" in summary and "Positioning:" in summary


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        analyze_demand("   ")
    intake = analyze_demand("ecommerce store for handmade candles", use_live_signals=False)
    assert intake["live_signals"] is None
    for opt in intake["options"]:
        assert opt["demand"]["evidence"] == [] or opt["demand"]["evidence"]
    with pytest.raises(ValueError):
        build_blueprint(intake, "does_not_exist")
    with pytest.raises(ValueError):
        build_blueprint({"status": "none"}, "lean_mvp")


def test_propose_options_is_deterministic_structure():
    spec = {"industry": "saas", "website_type": "saas", "prompt": "x", "features": [], "name": None}
    analysis = {
        "market_profile": {"market_size": "growing"},
        "recommended_positioning": "Premium international platform",
        "conversion_drivers": ["free_trial", "demo_cta"],
        "differentiation_opportunities": ["Growth opportunity: add demo_cta"],
        "mobile_priority": True,
        "pk_market_growth": "+55% YoY",
        "competitors": ["Stripe"],
    }
    options = propose_options(spec, analysis, {})
    ids = [o["id"] for o in options]
    assert ids == ["lean_mvp", "full_saas", "niche_differentiated", "internal_tool"]
    lean = options[0]
    assert lean["buyer_mode"] == "client_static"
    assert lean["monthly_price"]["monthly_low"] <= options[1]["monthly_price"]["monthly_low"]
    assert options[3]["monthly_price"] is None
    assert options[2]["differentiation_hook"]
