"""Tests for the new auto-mode design packs: 5 styles, 9 scaffolds, 2026 trends."""

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.design_style import DesignStyleEngine, STYLE_ALIASES
from agent.intelligence.design_system_engine import DesignSystemEngine, get_design_catalog
from agent.intelligence.page_composer import compose_project_pages
from agent.requirement_analyzer import RequirementAnalyzer
from agent.theme_matrix import ThemeMatrixEngine, _ALL_STYLES, _BASE_STYLE_GROUPS

NEW_STYLES = ["luxury", "corporate", "playful", "bold", "brutalism"]
NEW_SCAFFOLDS = [
    "masonry_flow", "bento_showcase", "magazine_spread", "dashboard_app",
    "split_screen", "narrow_single", "wide_immersive", "overlapping_layers",
]


def test_catalog_has_35_styles_including_new_ids():
    engine = DesignStyleEngine()
    assert len(engine.STYLES) >= 35
    for sid in NEW_STYLES:
        assert sid in engine.STYLES, sid


def test_new_styles_resolve_directly_and_by_industry():
    engine = DesignStyleEngine()
    assert engine.resolve_style({"design_style": "luxury"})["id"] == "luxury"
    assert engine.resolve_style({"design_style": "corporate"})["id"] == "corporate"
    assert engine.resolve_style({"design_style": "playful"})["id"] == "playful"
    assert engine.resolve_style({"design_style": "bold"})["id"] == "bold"
    assert engine.resolve_style({"design_style": "brutalism"})["id"] == "brutalism"
    assert engine.resolve_style({"industry": "luxury hotel brand"})["id"] == "luxury"
    assert engine.resolve_style({"industry": "b2b corporate site"})["id"] == "corporate"
    assert engine.resolve_style({"industry": "kids playful games"})["id"] == "playful"
    assert engine.resolve_style({"design_style": "brutalist"})["id"] == "brutalism"


def test_existing_resolutions_unchanged():
    engine = DesignStyleEngine()
    assert engine.resolve_style({"industry": "media"})["id"] == "neo_brutalism"
    assert engine.resolve_style({"industry": "creative agency"})["id"] == "swiss"
    assert engine.resolve_style({"industry": "portfolio"})["id"] == "minimalism"
    assert "luxury" not in STYLE_ALIASES  # luxury is a real style now, not an alias


def test_new_styles_render_distinct_hero_art():
    engine = DesignStyleEngine()
    arts = {}
    for sid in NEW_STYLES + ["maximalism"]:
        svg = engine._hero(engine.STYLES[sid], random.Random(7), "t7")
        assert svg.startswith("<svg"), sid
        arts[sid] = svg
    assert len(set(arts.values())) == len(arts), "hero art must differ per style"


def test_theme_matrix_covers_new_styles():
    engine = ThemeMatrixEngine()
    for sid in NEW_STYLES:
        assert sid in engine.style_ids, sid
        assert sid in _ALL_STYLES, sid
    assert "corporate" in _BASE_STYLE_GROUPS["business"]
    assert "luxury" in _BASE_STYLE_GROUPS["ecommerce"]
    assert "bold" in _BASE_STYLE_GROUPS["creative"]


def test_scaffold_catalog_and_explicit_selection():
    catalog = get_design_catalog()
    assert len(catalog["scaffolds"]) == 9
    engine = DesignSystemEngine()
    for scaffold in NEW_SCAFFOLDS:
        result = engine.resolve({
            "project_name": "t",
            "original_prompt": "x",
            "industry": "saas",
            "design_constraints": {"page_scaffold": scaffold},
        })
        assert result["design_dna"]["layout"]["page_scaffold"] == scaffold, scaffold


def test_unknown_scaffold_rejected():
    import pytest

    engine = DesignSystemEngine()
    with pytest.raises(ValueError):
        engine.resolve({
            "project_name": "t",
            "original_prompt": "x",
            "industry": "saas",
            "design_constraints": {"page_scaffold": "nope"},
        })


def test_scaffold_selection_is_deterministic():
    engine = DesignSystemEngine()
    spec = {"project_name": "t", "original_prompt": "x", "industry": "saas"}
    assert engine.resolve(spec) == engine.resolve(spec)


def test_scaffold_drives_layout_tokens():
    engine = DesignSystemEngine()
    narrow = engine.resolve({
        "project_name": "t", "original_prompt": "x", "industry": "education",
        "design_constraints": {"page_scaffold": "narrow_single"},
    })
    assert narrow["design_dna"]["tokens"]["layout"]["container_max"] == "44rem"
    dash = engine.resolve({
        "project_name": "t", "original_prompt": "x", "industry": "saas",
        "design_constraints": {"page_scaffold": "dashboard_app"},
    })
    assert dash["design_dna"]["layout"]["density"] == "compact"


def test_composer_renders_scaffold_end_to_end():
    import pytest

    engine = DesignSystemEngine()
    dna = engine.resolve({
        "project_name": "demo", "original_prompt": "portfolio site",
        "industry": "portfolio",
        "design_constraints": {"page_scaffold": "masonry_flow"},
    })["design_dna"]
    tmp = Path(tempfile.mkdtemp())
    out = compose_project_pages(tmp, dna, {"project_name": "demo"})
    assert out["structure"]["scaffold"] == "masonry_flow"
    home = (tmp / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
    assert 'data-scaffold="masonry_flow"' in home
    css = (tmp / "frontend" / "src" / "design-system.css").read_text(encoding="utf-8")
    assert 'data-scaffold="masonry_flow"' in css
    bad = dict(dna, layout=dict(dna["layout"], page_scaffold="nope"))
    with pytest.raises(ValueError):
        compose_project_pages(Path(tempfile.mkdtemp()), bad, {"project_name": "demo"})


def test_trend_registry_has_2026_entries():
    here = Path(__file__).resolve().parent.parent.parent
    data = json.loads((here / "registry" / "trending-features.json").read_text(encoding="utf-8"))
    assert len(data) >= 32
    ids = {e["id"] for e in data}
    for expected in ("bento_grids", "micro_interactions", "passkeys_passwordless",
                     "bnpl_gateway", "rtl_layout_pack", "ai_search_answers",
                     "live_shopping", "webgpu_3d_viewer"):
        assert expected in ids, expected


def test_injector_selects_new_trends_for_matching_types():
    from agent.trending_features import TrendingFeaturesInjector

    injector = TrendingFeaturesInjector()
    result = injector.inject({"website_type": "general", "industry": "general", "features": []}, {"market_trends": []})
    assert result["injected_count"] >= 5
    assert "ai_search_answers" in result["feature_ids"]
    assert "passkeys_passwordless" in result["feature_ids"]
    assert any(f.get("trend_year") == 2026 for f in result["features"])


def test_requirement_analyzer_folds_market_context():
    analyzer = RequirementAnalyzer(ai_provider=None)
    spec = analyzer.analyze("a coffee shop website", market_context={
        "market_trends": ["AI chat support", "Voice ordering", "Loyalty wallets"],
    })
    assert "AI chat support" in spec["market_trends"]
    assert len(spec["market_feature_hints"]) == 3


def test_requirement_analyzer_without_context_unchanged():
    analyzer = RequirementAnalyzer(ai_provider=None)
    spec = analyzer.analyze("a coffee shop website")
    assert "market_trends" not in spec


def test_planner_carries_market_trends():
    from agent.planner import GenerationPlanner

    planner = GenerationPlanner()
    plan = planner.create_plan(
        {"project_name": "p", "features": [], "market_trends": ["AI chat", "BNPL"],
         "trending_features": ["ai_chat"]},
        {}, [], {}, {}, [],
    )
    assert plan["market_trends"] == ["AI chat", "BNPL"]
    assert plan["trending_features"] == ["ai_chat"]
    assert any("AI chat" in t for t in plan["ai_tasks_required"])


def test_auto_request_model_validates_timeout():
    import pytest

    from server import AutoRequest

    ok = AutoRequest(prompt="a proper website prompt here", timeout_secs=300)
    assert ok.timeout_secs == 300
    assert ok.run_autopilot is False
    with pytest.raises(Exception):
        AutoRequest(prompt="a proper website prompt here", timeout_secs=10)
