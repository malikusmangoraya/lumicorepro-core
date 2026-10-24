"""Market-first pipeline guarantee tests.

The user request: every task must pass through market analysis FIRST and every
downstream stage must be guided by it. These tests pin that contract."""
from agent.orchestrator import AgentOrchestrator


def test_market_analysis_is_the_first_phase():
    assert AgentOrchestrator.PHASES[0] == "market_analysis"


def test_market_analysis_has_no_upstream_dependency():
    deps = AgentOrchestrator.PHASE_DEPENDENCIES["market_analysis"]
    assert deps == [], "market analysis must run first, nothing before it"


def test_downstream_stages_depend_on_market_analysis():
    deps = AgentOrchestrator.PHASE_DEPENDENCIES
    for phase in ("design_brand_planning", "trending_features_injection",
                  "competitive_benchmark_delivery"):
        assert "market_analysis" in deps[phase], f"{phase} must consume market guidance"


def test_market_analysis_is_retryable():
    assert "market_analysis" in AgentOrchestrator.RETRYABLE_PHASES
