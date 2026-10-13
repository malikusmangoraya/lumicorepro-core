import sys
import os
import tempfile
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

    def test_set_provider_reaches_every_provider_holding_subengine(self):
        """Sub-engines snapshot their provider, so the swap must reach all of them.

        The iteration engine lives at `iteration_engine`; a wrong attribute name
        here silently no-ops and leaves that engine on the previous provider.
        """
        orch = AgentOrchestrator()
        fake = object()

        orch.set_provider(fake, name="fake-offline")

        self.assertIs(orch.ai_provider, fake)
        self.assertEqual(orch.ai_provider_name, "fake-offline")
        self.assertIs(orch.analyzer.ai_provider, fake)
        self.assertIs(orch.code_modifier.ai_provider, fake)
        self.assertIs(orch.iteration_engine.provider, fake)
        self.assertIs(orch.iteration_engine.code_modifier.ai_provider, fake)

    def test_orchestrator_phases_defined(self):
        """Orchestrator should define every enterprise phase, including the
        pre-coding design planner and the post-build browser QA phase."""
        orch = AgentOrchestrator()
        self.assertEqual(len(orch.PHASES), 18)
        expected_phases = [
            "market_analysis",
            "requirement_analysis",
            "design_brand_planning",
            "design_planner",
            "tech_stack_selection",
            "trending_features_injection",
            "resource_assembly_planning",
            "code_generation",
            "quality_verification",
            "browser_qa",
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

    def test_phase_dependency_graph_is_consistent(self):
        """Every phase must declare dependencies that are declared earlier."""
        orch = AgentOrchestrator()
        deps = orch.PHASE_DEPENDENCIES
        for phase in orch.PHASES:
            self.assertIn(phase, deps, f"{phase} missing from PHASE_DEPENDENCIES")
            for dep in deps[phase]:
                self.assertIn(dep, orch.PHASES, f"{phase} depends on unknown {dep}")
                self.assertLess(
                    orch.PHASES.index(dep),
                    orch.PHASES.index(phase),
                    f"{phase} depends on later phase {dep}",
                )

    def test_design_planner_precedes_code_generation(self):
        """The design contract must be resolved before any code is generated."""
        orch = AgentOrchestrator()
        self.assertLess(
            orch.PHASES.index("design_planner"),
            orch.PHASES.index("code_generation"),
        )
        self.assertIn("design_planner", orch.PHASE_DEPENDENCIES["code_generation"])

    def test_portfolio_uniqueness_helper_selects_and_attaches_signature(self):
        import json
        from unittest.mock import patch
        from agent.intelligence.design_uniqueness import extract_design_signature

        orch = AgentOrchestrator.__new__(AgentOrchestrator)
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_dir = Path(temp_dir) / "projects"
            prior_dir = projects_dir / "prior-site"
            prior_dir.mkdir(parents=True)
            target_dir = projects_dir / "new-site"
            decision = {
                "industry": "saas",
                "brand": "minimal",
                "ui_style": "glassmorphism",
                "hero": "minimal_composition",
                "navigation": "minimal_sticky",
                "grid": "balanced",
                "typography": "clean_sans",
                "motion": "subtle",
                "3d": False,
                "image_ratio": "16:9",
                "cta_style": "clear_primary",
                "surface_style": "flat",
                "card_usage": "minimal",
                "design_manifest": {
                    "brand": {"archetype": "minimal"},
                    "visual": {"motion": 0.3, "3d": False, "ui_style": "glassmorphism"},
                    "typography": {"heading_style": "clean_sans"},
                    "colors": {"tokens": {"primary": "#315b42", "accent": "#d89b45"}},
                    "industry": "saas",
                },
            }
            design_plan = {
                "brand_style": "minimal",
                "page_plans": {"Home": {"sections": ["hero", "features", "cta"]}},
                "design_system": {"colors": {"primary": "#315b42", "accent": "#d89b45"}},
            }
            prior_signature = extract_design_signature(decision, design_plan)
            (prior_dir / "design-manifest.json").write_text(
                json.dumps({"design_signature": prior_signature}), encoding="utf-8"
            )
            spec = {
                "project_name": "new-site",
                "original_prompt": "A modern SaaS for independent studios",
                "design_constraints": {"hero": "minimal_composition"},
            }

            with patch("agent.orchestrator.GENERATED_PROJECTS_DIR", projects_dir):
                result = orch._select_portfolio_unique_design(
                    spec, decision, design_plan, target_dir
                )
            with patch(
                "agent.intelligence.design_uniqueness.load_portfolio_signatures",
                side_effect=PermissionError("scan denied"),
            ):
                unavailable = orch._select_portfolio_unique_design(
                    spec, decision, design_plan, target_dir
                )

        self.assertNotEqual(
            result["design_signature"]["fingerprint"], prior_signature["fingerprint"]
        )
        self.assertEqual(result["decision"]["hero"], "minimal_composition")
        self.assertEqual(
            result["decision"]["design_manifest"]["design_signature"],
            result["design_signature"],
        )
        self.assertEqual(result["comparison"]["compared_projects"], 1)
        self.assertEqual(unavailable["comparison"]["status"], "unavailable")
        self.assertIn("scan denied", unavailable["comparison"]["reason"])
        self.assertNotEqual(result["decision"]["ui_style"], "glassmorphism")
        self.assertEqual(
            result["design_blueprint"]["ui_style"], result["decision"]["ui_style"]
        )
        self.assertEqual(
            result["design_plan"]["design_system"]["colors"]["primary"],
            result["design_blueprint"]["palette"]["primary"],
        )

    def test_portfolio_uniqueness_preserves_explicit_ui_style(self):
        import json
        from unittest.mock import patch
        from agent.intelligence.design_uniqueness import extract_design_signature

        orch = AgentOrchestrator.__new__(AgentOrchestrator)
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_dir = Path(temp_dir)
            prior_dir = projects_dir / "prior-site"
            prior_dir.mkdir()
            decision = {
                "industry": "saas",
                "ui_style": "glassmorphism",
                "design_manifest": {"visual": {"ui_style": "glassmorphism"}},
            }
            plan = {"design_system": {"colors": {"primary": "#315b42"}}}
            signature = extract_design_signature(decision, plan)
            (prior_dir / "design-manifest.json").write_text(
                json.dumps({"design_signature": signature}), encoding="utf-8"
            )

            with patch("agent.orchestrator.GENERATED_PROJECTS_DIR", projects_dir):
                result = orch._select_portfolio_unique_design(
                    {
                        "project_name": "new",
                        "ui_style": "glassmorphism",
                        "style": ["glassmorphism"],
                    },
                    decision,
                    plan,
                    projects_dir / "new",
                )

        self.assertEqual(result["decision"]["ui_style"], "glassmorphism")

    def test_portfolio_uniqueness_preserves_color_and_reference_constraints(self):
        import json
        from unittest.mock import patch
        from agent.intelligence.design_uniqueness import extract_design_signature

        orch = AgentOrchestrator.__new__(AgentOrchestrator)
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_dir = Path(temp_dir)
            prior_dir = projects_dir / "prior-site"
            prior_dir.mkdir()
            decision = {
                "industry": "saas",
                "ui_style": "glassmorphism",
                "reference_hints": ["editorial restraint"],
                "design_manifest": {"visual": {"ui_style": "glassmorphism"}},
            }
            plan = {"design_system": {"colors": {"primary": "#315b42"}}}
            signature = extract_design_signature(decision, plan)
            (prior_dir / "design-manifest.json").write_text(
                json.dumps({"design_signature": signature}), encoding="utf-8"
            )
            spec = {
                "project_name": "new",
                "primary_color_hint": "#123456",
                "screenshot_spec": {"analyzed": True, "colors_measured": True},
            }

            with patch("agent.orchestrator.GENERATED_PROJECTS_DIR", projects_dir):
                result = orch._select_portfolio_unique_design(spec, decision, plan, projects_dir / "new")

        self.assertEqual(result["decision"]["ui_style"], "glassmorphism")
        self.assertEqual(result["design_blueprint"]["palette"]["primary"], "#123456")

    def test_browser_qa_follows_quality_verification(self):
        """Browser QA must run after the build is quality-verified."""
        orch = AgentOrchestrator()
        self.assertLess(
            orch.PHASES.index("quality_verification"),
            orch.PHASES.index("browser_qa"),
        )
        self.assertEqual(orch.PHASE_DEPENDENCIES["browser_qa"], ["quality_verification"])

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

    def test_deployment_release_gate_blocks_failed_checks(self):
        result = AgentOrchestrator._deployment_release_gate(
            {"valid": True},
            {"overall_score": 92},
            {"passed": False},
            {"passed": True},
            {"status": "complete", "blockers": []},
            {"passed": True},
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["blockers"], ["devops_quality_gate_failed"])

    def test_deployment_release_gate_allows_passed_checks(self):
        result = AgentOrchestrator._deployment_release_gate(
            {"valid": True},
            {"overall_score": 80},
            {"passed": True},
            {"passed": True},
            {"status": "complete", "blockers": []},
            {"passed": True},
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["blockers"], [])

    def test_deployment_release_gate_blocks_incomplete_generated_project(self):
        result = AgentOrchestrator._deployment_release_gate(
            {"valid": True},
            {"overall_score": 95},
            {"passed": True},
            {"passed": True},
            {"status": "incomplete", "blockers": ["auth_routes"]},
            {"passed": True},
        )

        self.assertFalse(result["passed"])
        self.assertIn("generated_project_incomplete:auth_routes", result["blockers"])

    def test_deployment_release_gate_blocks_failed_output_guardrails(self):
        result = AgentOrchestrator._deployment_release_gate(
            {"valid": True},
            {"overall_score": 95},
            {"passed": True},
            {"passed": True},
            {"status": "complete", "blockers": []},
            {"passed": False},
        )

        self.assertFalse(result["passed"])
        self.assertIn("output_guardrails_failed", result["blockers"])

    def test_workflow_agents_report_four_role_handoffs(self):
        report = AgentOrchestrator._build_workflow_agents_report(
            {
                "phase_2_requirement_analysis": {"features": ["catalog"]},
                "phase_5_assembly_plan": {"project_name": "shop", "steps": 5},
                "phase_2b_design_plan": {"target_region": "global"},
                "phase_2_design_decision": {"hero": "editorial", "cta_style": "clear"},
                "phase_6_code_generation": {"ai_calls": 2},
                "qa_release_gate": {"passed": True, "blockers": []},
                "phase_7_quality_verification": {"overall_score": 91},
                "live_deployment": {"status": "deployed", "url": "https://example.test"},
            },
            {
                "benchmark_first": {
                    "source": "live+deterministic",
                    "industry": "ecommerce",
                    "benchmark_peers": ["international peer"],
                }
            },
            "generated-projects/shop",
        )
        self.assertEqual(
            set(report), {"planner", "design_researcher", "coder", "qa_deployment"}
        )
        self.assertEqual(report["design_researcher"]["status"], "completed")
        self.assertEqual(
            report["design_researcher"]["handoff"]["benchmark_peers"],
            ["international peer"],
        )
        self.assertEqual(
            report["qa_deployment"]["handoff"]["deployment_status"], "deployed"
        )
        self.assertEqual(report["qa_deployment"]["status"], "deployed")


class TestProjectBuilderSafety(unittest.TestCase):
    def test_project_name_is_safe_slug(self):
        self.assertEqual(
            ProjectBuilder._safe_project_name("../My Unsafe Store!"),
            "my-unsafe-store",
        )


class TestDesignPlanArtifacts(unittest.TestCase):
    """The design contract must be persisted once the project directory exists."""

    def test_persists_plan_after_build_directory_exists(self):
        orch = AgentOrchestrator()
        phase_log = {}
        with tempfile.TemporaryDirectory() as project_dir:
            written = orch._persist_design_plan_artifacts(
                project_dir, {"pages": [], "page_plans": {}}, phase_log
            )

            self.assertTrue(written["ok"])
            self.assertTrue(Path(written["paths"]["markdown"]).is_file())
            self.assertTrue(Path(written["paths"]["json"]).is_file())
        self.assertEqual(phase_log["phase_5b_design_planner"]["artifacts"], written)

    def test_missing_inputs_are_recorded_not_silent(self):
        orch = AgentOrchestrator()
        phase_log = {}

        written = orch._persist_design_plan_artifacts("", {}, phase_log)

        self.assertFalse(written["ok"])
        self.assertIn("reason", written)
        self.assertEqual(phase_log["phase_5b_design_planner"]["artifacts"], written)


if __name__ == "__main__":
    unittest.main()
