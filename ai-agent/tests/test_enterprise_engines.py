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
from agent.project_builder import ProjectBuilder
from agent.project_mode_engine import ProjectModeEngine
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

    def test_frontend_auth_journeys_use_api_and_accessible_states(self):
        frontend = Path(self.test_dir) / "frontend"
        app = frontend / "src" / "App.jsx"
        app.parent.mkdir(parents=True)
        app.write_text(
            "import React from 'react';\n"
            "import { Routes, Route } from 'react-router-dom';\n"
            "export default function App() { return <Routes><Route path=\"/\" element={<div />} /></Routes>; }\n",
            encoding="utf-8",
        )

        ProjectBuilder()._generate_frontend_journeys(frontend, "Example Brand")

        login = (frontend / "src" / "pages" / "GeneratedLogin.jsx").read_text(encoding="utf-8")
        register = (frontend / "src" / "pages" / "GeneratedRegister.jsx").read_text(encoding="utf-8")
        app_source = app.read_text(encoding="utf-8")
        self.assertIn("api.post('/auth/login'", login)
        self.assertIn("role=\"alert\"", login)
        self.assertIn("disabled={submitting}", login)
        self.assertIn("api.post('/auth/register'", register)
        self.assertIn("aria-describedby", register)
        self.assertIn('path="/login"', app_source)
        self.assertIn('path="/register"', app_source)
        self.assertIn("path=\"/\"", app_source)

    def test_frontend_contact_form_only_reports_success_after_api_response(self):
        frontend = Path(self.test_dir) / "frontend"
        src = frontend / "src"
        (src / "pages").mkdir(parents=True)
        (src / "pages" / "Contact.jsx").write_text(
            "import React from 'react';\n"
            "export default function Contact() { return <main><h1>Contact us</h1>"
            "<form onSubmit={handleSubmit}><input /><button>Send</button></form></main>; }\n",
            encoding="utf-8",
        )
        (src / "App.jsx").write_text(
            "import React from 'react';\n"
            "import { Routes, Route } from 'react-router-dom';\n"
            "import Contact from './pages/Contact.jsx';\n"
            "export default function App() { return <Routes><Route path=\"/contact\" element={<Contact />} /></Routes>; }\n",
            encoding="utf-8",
        )
        result = ProjectBuilder()._generate_frontend_journeys(frontend, "Example Brand")

        contact = (
            frontend / "src" / "components" / "forms" / "GeneratedContactForm.jsx"
        ).read_text(encoding="utf-8")
        self.assertIn("api.post('/contact'", contact)
        self.assertIn("role=\"alert\"", contact)
        self.assertIn("role=\"status\"", contact)
        self.assertIn("disabled={submitting}", contact)
        self.assertLess(contact.index("await api.post('/contact'"), contact.index("setSucceeded(true)"))
        contact_page = (src / "pages" / "Contact.jsx").read_text(encoding="utf-8")
        self.assertIn("<h1>Contact us</h1>", contact_page)
        self.assertIn("<GeneratedContactForm />", contact_page)
        self.assertTrue(result["contact_form"])

    def test_enterprise_api_client_sends_cookies_and_rotates_expired_access_tokens(self):
        client = ProjectModeEngine()._api_js()
        self.assertIn("withCredentials: true", client)
        self.assertIn("api.post('/auth/refresh')", client)
        self.assertIn("originalRequest._retry", client)
        self.assertIn("isAuthRequest", client)

    def test_explicit_static_mode_skips_persisted_frontend_journeys(self):
        root = Path(self.test_dir)
        report = ProjectModeEngine().render_layout(
            str(root),
            {"project_name": "Static Brand", "website_type": "portfolio", "buyer_type": "static"},
        )
        self.assertEqual(report["mode"], "client-static")
        self.assertFalse((root / "frontend" / "src" / "pages" / "GeneratedLogin.jsx").exists())
        self.assertFalse((root / "frontend" / "src" / "pages" / "GeneratedContactPage.jsx").exists())

    def test_enterprise_layout_generates_auth_routes_and_contact_form(self):
        root = Path(self.test_dir)
        app = root / "frontend" / "src" / "App.jsx"
        app.parent.mkdir(parents=True)
        app.write_text(
            "import React from 'react';\n"
            "import { Routes, Route } from 'react-router-dom';\n"
            "export default function App() { return <Routes><Route path=\"/\" element={<div />} /></Routes>; }\n",
            encoding="utf-8",
        )

        report = ProjectModeEngine().render_layout(
            str(root),
            {"project_name": "Example Brand", "website_type": "portfolio", "buyer_type": "enterprise"},
        )

        self.assertTrue(report["frontend_journeys"]["auth_routes"])
        self.assertTrue(report["frontend_journeys"]["contact_form"])
        app_source = app.read_text(encoding="utf-8")
        self.assertIn("path=\"/login\"", app_source)
        self.assertIn("path=\"/register\"", app_source)
        self.assertIn("path=\"/contact\"", app_source)
        self.assertTrue(
            (root / "frontend" / "src" / "pages" / "GeneratedContactPage.jsx").is_file()
        )

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
        # set_provider (not plain attribute assignment): sub-engines snapshot
        # the provider at construction, so only the centralized swap keeps
        # code_modifier/analyzer/iteration_engine offline too.
        orch.set_provider(fake, name="fake-offline")

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
