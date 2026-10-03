import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.orchestrator import AgentOrchestrator
from agent.api_generator import APIGenerator
from agent.seo_automation import SEOAutomationEngine
from agent.cdn_optimizer import CDNOptimizer
from agent.performance_budget import PerformanceBudgetEngine
from agent.analytics_pipeline import AnalyticsPipeline
from agent.ab_testing_engine import ABTestingEngine
from agent.webhook_manager import WebhookManager
from agent.global_deployment import GlobalDeploymentEngine


class TestEnterpriseEngines(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="lumicore_test_")
        self.spec = {
            "project_name": "medtech-pro",
            "website_type": "healthcare",
            "industry": "medical",
            "region": "NA",
            "features": [
                "doctors", "appointments", "stripe_payments", "jwt_auth",
                "reviews", "notifications", "search", "cookie_consent", "webhooks"
            ],
            "languages_generated": ["en", "es"],
        }
        self.plan = {
            "project_name": "medtech-pro",
            "spec": self.spec,
            "backend": {"name": "Healthcare API"},
            "assembly_steps": [],
            "ai_tasks_required": [],
        }

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_api_generator(self):
        api_gen = APIGenerator()
        target_backend = Path(self.test_dir) / "backend"
        api_gen.generate_full_backend(target_backend, self.plan)
        
        self.assertTrue((target_backend / "server.js").exists())
        self.assertTrue((target_backend / "package.json").exists())
        self.assertTrue((target_backend / "routes").exists())
        self.assertTrue((target_backend / "controllers").exists())
        self.assertTrue((target_backend / "middleware").exists())

    def test_seo_automation(self):
        seo_engine = SEOAutomationEngine()
        res = seo_engine.generate(self.spec, self.test_dir)
        
        self.assertGreater(res.get("pages_optimized", 0), 0)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "frontend", "public", "sitemap.xml")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "frontend", "public", "robots.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "SEO_AUDIT.md")))

        seo_json = os.path.join(self.test_dir, "frontend", "src", "seo-config.json")
        if os.path.exists(seo_json):
            import json
            with open(seo_json, "r", encoding="utf-8") as fh:
                config = json.load(fh)
            for page in config.values():
                self.assertIn("ogLocale", page)
                self.assertTrue(page["ogLocale"])

    def test_cdn_optimizer(self):
        cdn_opt = CDNOptimizer()
        res = cdn_opt.generate(self.test_dir, self.spec)
        
        self.assertIn("platforms_configured", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "CDN_DEPLOYMENT.md")))

    def test_performance_budget(self):
        perf_engine = PerformanceBudgetEngine()
        res = perf_engine.generate(self.spec, self.test_dir)
        
        self.assertIn("targets", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "PERFORMANCE.md")))

    def test_analytics_pipeline(self):
        analytics = AnalyticsPipeline()
        res = analytics.generate(self.spec, self.test_dir)
        
        self.assertGreater(res.get("total_events", 0), 0)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ANALYTICS.md")))

    def test_ab_testing_engine(self):
        ab_engine = ABTestingEngine()
        res = ab_engine.generate(self.spec, self.test_dir)
        
        self.assertIn("total_experiments", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "EXPERIMENTS.md")))

    def test_webhook_manager(self):
        wh_mgr = WebhookManager()
        res = wh_mgr.generate(self.spec, self.test_dir)
        
        self.assertIn("total_events", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "WEBHOOKS.md")))

    def test_global_deployment(self):
        deploy_engine = GlobalDeploymentEngine()
        res = deploy_engine.generate(self.spec, self.test_dir)
        
        self.assertIn("platforms_supported", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "DEPLOYMENT_GUIDE.md")))

    def test_orchestrator_lifecycle_callbacks(self):
        events_captured = []
        def callback(phase, event_type, data):
            events_captured.append((phase, event_type))

        # Offline fast execution: every AI call (orchestrator + self-heal
        # reasoning) resolves to a deterministic fake provider in-process, so
        # the full pipeline completes without network or dead-gateway retries.
        from providers.base_provider import BaseAIProvider
        from utils.helpers import safe_json_parse

        class FakeOfflineProvider(BaseAIProvider):
            def __init__(self):
                super().__init__("", "fake-offline", timeout=5)

            def analyze_requirement(self, prompt):
                return safe_json_parse(
                    '{"website_type": "ecommerce", "industry": "electronics", '
                    '"frontend": "react", "backend": "express", "database": "mysql", '
                    '"features": ["cart", "auth"], "style": ["modern"]}'
                )

            def generate_code(self, prompt, context_files=None):
                return "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -0,0 +1 @@\n+"

            def modify_code(self, file_content, instruction):
                return file_content

            def fix_error(self, error_log, file_content):
                return file_content

            def validate_project(self, project_summary):
                return {"valid": True, "suggestions": []}

        fake = FakeOfflineProvider()

        orch = AgentOrchestrator()
        orch.ai_provider = fake

        import unittest.mock as mock
        from agent.quality_gate import DevOpsQualityGate, CommandResult

        async def _stub_run_command(command, cwd=None, **kwargs):
            return CommandResult(command=command[0] if command else "", returncode=0,
                                 stdout="stub ok", stderr="")

        with mock.patch.object(DevOpsQualityGate, "run_command", new=_stub_run_command), \
             mock.patch.object(DevOpsQualityGate, "_github_recovery_for",
                               new=mock.AsyncMock(return_value={})), \
             mock.patch("config.providers.get_reasoning_provider", return_value=fake):
            res = orch.run(
                "Build an online electronics store with shopping cart and stripe payment",
                interactive=False,
                progress_callback=callback,
            )
        self.assertIn("project_name", res)
        self.assertEqual(len(orch.PHASES), 18)
        self.assertIn("design_planner", orch.PHASES)
        self.assertIn("browser_qa", orch.PHASES)
        self.assertGreater(len(events_captured), 5)


if __name__ == "__main__":
    unittest.main()
