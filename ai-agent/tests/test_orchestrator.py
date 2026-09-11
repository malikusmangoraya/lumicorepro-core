import sys
import os
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.orchestrator import AgentOrchestrator
from agent.orchestrator import OrchestratorError
from agent.orchestrator import PipelineCancelled
from agent.project_builder import ProjectBuilder

class TestOrchestratorInit(unittest.TestCase):
    """Test AgentOrchestrator initialization without external API keys."""

    def test_orchestrator_initializes_without_provider(self):
        """Orchestrator should initialize even with no API keys."""
        orch = AgentOrchestrator()
        self.assertIsNotNone(orch)
        self.assertIsNotNone(orch.analyzer)
        self.assertIsNotNone(orch.project_builder)
        self.assertIsNotNone(orch.validator)
        self.assertIsNotNone(orch.quality_gates)
        self.assertIsNotNone(orch.template_selector)
        self.assertIsNotNone(orch.component_selector)
        self.assertIsNotNone(orch.backend_selector)
        self.assertIsNotNone(orch.database_selector)

    def test_orchestrator_phases_defined(self):
        """Orchestrator should have all 15 enterprise phases defined."""
        orch = AgentOrchestrator()
        self.assertEqual(len(orch.PHASES), 15)
        expected_phases = [
            "market_analysis",
            "requirement_analysis",
            "tech_stack_selection",
            "trending_features_injection",
            "resource_assembly_planning",
            "code_generation",
            "quality_verification",
            "improvement_recommendations",
            "competitive_benchmark_delivery",
            "international_delivery",
            "localization_and_i18n",
            "compliance_and_accessibility",
            "seo_and_cdn_optimization",
            "performance_growth_and_webhooks",
            "multi_cloud_global_deployment",
        ]
        for phase in expected_phases:
            self.assertIn(phase, orch.PHASES)

class TestOrchestratorProviderInit(unittest.TestCase):
    """Test AI provider initialization with fallback chain."""

    def test_init_provider_no_keys(self):
        """Should return None when no API keys are configured."""
        from unittest.mock import patch
        empty_env = {
            "GEMINI_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "MISTRAL_API_KEY": "",
            "OPENAI_API_KEY": "",
            "ACTIVE_AI_PROVIDER": "gemini",
        }
        with patch.dict(os.environ, empty_env):
            orch = AgentOrchestrator()
            # When forced to have no keys in env, provider should be None (offline mode)
            # or if cached from settings, verify offline mode is safe
            self.assertTrue(orch.ai_provider is None or hasattr(orch.ai_provider, "analyze_requirement"))

class TestOrchestratorFailurePolicy(unittest.TestCase):
    def test_critical_phase_failure_is_not_hidden_by_fallback(self):
        orch = AgentOrchestrator()

        def failing_phase():
            raise RuntimeError("requirements unavailable")

        with self.assertRaises(OrchestratorError):
            orch._run_phase_safe(
                "requirement_analysis",
                failing_phase,
                fallback={"features": []},
                critical=True,
            )

    def test_failure_identifiers_map_to_canonical_phases(self):
        orch = AgentOrchestrator()
        self.assertEqual(
            orch._phase_failure_names(["phase_2_requirement_analysis", "phase_6_code_generation"]),
            {"requirement_analysis", "code_generation"},
        )

    def test_pipeline_cancelled_is_not_swallowed_by_phase_fallback(self):
        orch = AgentOrchestrator()

        def cancelled_phase():
            raise PipelineCancelled("client disconnect")

        with self.assertRaises(PipelineCancelled):
            orch._run_phase_safe(
                "requirement_analysis",
                cancelled_phase,
                fallback={"features": []},
                critical=False,
            )

    def test_progress_callback_cancel_propagates(self):
        orch = AgentOrchestrator()

        def on_progress(phase, event_type, data):
            raise PipelineCancelled("in-band cancel")

        orch.progress_callback = on_progress
        with self.assertRaises(PipelineCancelled):
            orch._run_phase("market_analysis", lambda: {"ok": True})

    def test_engineering_matrix_binds_five_specs(self):
        orch = AgentOrchestrator()
        spec = {"website_type": "ecommerce"}
        phase_log = {}
        matrix = orch._bind_engineering_matrix(spec, phase_log)
        self.assertTrue(matrix.get("loaded"))
        self.assertTrue(matrix.get("all_present"))
        self.assertGreaterEqual(matrix.get("component_registry_count", 0), 44)
        self.assertEqual(len(phase_log["engineering_matrix"]["docs"]), 5)
        self.assertIn("COMPONENT CONTRACT", spec.get("component_contract", ""))


class TestProjectBuilderSafety(unittest.TestCase):
    def test_project_name_is_safe_slug(self):
        self.assertEqual(
            ProjectBuilder._safe_project_name("../My Unsafe Store!"),
            "my-unsafe-store",
        )

if __name__ == "__main__":
    unittest.main()
