import sys
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.project_mode_engine import (
    ProjectModeEngine,
    MODE_CLIENT_STATIC,
    MODE_ENTERPRISE,
)


class TestProjectModeEngine(unittest.TestCase):
    """Hermetic tests for the buyer-directed layout mode engine."""

    def setUp(self):
        self.engine = ProjectModeEngine()
        self.tmp = tempfile.mkdtemp(prefix="lumicore-mode-test-")
        self.project = os.path.join(self.tmp, "mode-app")
        os.makedirs(os.path.join(self.project, "frontend", "public"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── Mode selection ─────────────────────────────────────────────────────
    def test_select_enterprise_for_portfolio_by_default(self):
        spec = {"website_type": "portfolio"}
        mode = self.engine.select_mode(spec)
        self.assertEqual(mode, MODE_ENTERPRISE)
        self.assertTrue(spec["has_api"])
        self.assertEqual(spec["deployment_mode"], MODE_ENTERPRISE)

    def test_select_enterprise_default_for_ecommerce(self):
        spec = {"website_type": "ecommerce"}
        mode = self.engine.select_mode(spec)
        self.assertEqual(mode, MODE_ENTERPRISE)
        self.assertTrue(spec["has_api"])
        self.assertEqual(spec["deployment_mode"], MODE_ENTERPRISE)

    def test_select_enterprise_for_business_by_default(self):
        spec = {"website_type": "business"}
        self.assertEqual(self.engine.select_mode(spec), MODE_ENTERPRISE)
        self.assertTrue(spec["has_api"])

    def test_select_enterprise_for_saas(self):
        spec = {"website_type": "saas"}
        mode = self.engine.select_mode(spec)
        self.assertEqual(mode, MODE_ENTERPRISE)
        self.assertTrue(spec["has_api"])

    def test_buyer_enterprise_overrides_ecommerce(self):
        spec = {"website_type": "ecommerce", "buyer_type": "enterprise"}
        self.assertEqual(self.engine.select_mode(spec), MODE_ENTERPRISE)

    def test_buyer_static_overrides_ecommerce(self):
        spec = {"website_type": "ecommerce", "buyer_type": "static"}
        self.assertEqual(self.engine.select_mode(spec), MODE_CLIENT_STATIC)

    def test_buyer_enterprise_overrides_portfolio(self):
        spec = {"website_type": "portfolio", "buyer_type": "enterprise"}
        self.assertEqual(self.engine.select_mode(spec), MODE_ENTERPRISE)

    # ── Mode 1: client-static showcase ─────────────────────────────────────
    def test_static_layout_strips_backend_and_writes_showcase(self):
        for rel in ("backend", "nginx", "frontend", "frontend/Dockerfile"):
            os.makedirs(os.path.join(self.project, rel), exist_ok=True)
        with open(os.path.join(self.project, "docker-compose.yml"), "w") as fh:
            fh.write("services: {}\n")

        report = self.engine.render_static_layout(self.project, {"project_name": "demo"})

        self.assertEqual(report["mode"], MODE_CLIENT_STATIC)
        self.assertTrue(report["backend_removed"])
        self.assertFalse(os.path.exists(os.path.join(self.project, "backend")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "nginx")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "docker-compose.yml")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "frontend", "Dockerfile")))
        self.assertTrue(os.path.exists(os.path.join(self.project, "frontend", "src", "services", "staticForms.js")))
        self.assertTrue(os.path.exists(os.path.join(self.project, "frontend", "src", "services", "mockApi.js")))

    def test_static_deploy_configs_are_api_less(self):
        self.engine.render_static_layout(self.project, {"project_name": "demo"})
        vercel = Path(self.project, "vercel.json").read_text()
        self.assertIn('"rootDirectory": "frontend"', vercel)
        self.assertNotIn("functions", vercel)
        netlify = Path(self.project, "netlify.toml").read_text()
        self.assertIn('base    = "frontend"', netlify)
        redirects = Path(self.project, "frontend", "public", "_redirects").read_text()
        self.assertIn("/index.html", redirects)
        headers = Path(self.project, "frontend", "public", "_headers").read_text()
        self.assertIn("X-Content-Type-Options", headers)

    def test_static_env_has_no_server_secrets(self):
        self.engine.render_static_layout(self.project, {"project_name": "demo"})
        env = Path(self.project, ".env.example").read_text()
        self.assertIn("VITE_FORMSPREE_ENDPOINT", env)
        self.assertNotIn("DATABASE_URL", env)

    def test_static_readme_is_bespoke(self):
        self.engine.render_static_layout(self.project, {"project_name": "showcase-app", "website_type": "portfolio"})
        readme = Path(self.project, "README.md").read_text()
        self.assertIn("Vercel", readme)
        self.assertIn("Netlify", readme)
        self.assertIn("Formspree", readme)
        self.assertIn("copy-paste".lower(), readme.lower())

    # ── Mode 2: enterprise full-stack hydration ────────────────────────────
    def test_enterprise_hydrates_models_routes_queue(self):
        report = self.engine.render_enterprise_layout(self.project, {"project_name": "saas-app", "website_type": "saas"})

        self.assertEqual(report["mode"], MODE_ENTERPRISE)
        self.assertGreaterEqual(report["models_mounted"], 14, "14 Sequelize models expected")
        self.assertGreaterEqual(report["route_groups_mapped"], 18, "18 API route groups expected")
        self.assertIn("User", report["models"])
        self.assertIn("order", report["routes"])
        # Redis/BullMQ background jobs mounted.
        self.assertTrue(os.path.exists(os.path.join(self.project, "backend", "services", "queue", "queue.service.js")))
        self.assertTrue(os.path.exists(os.path.join(self.project, "backend", "workers", "worker.js")))
        pkg = Path(self.project, "backend", "package.json").read_text()
        self.assertIn("bullmq", pkg)
        self.assertIn("sequelize", pkg)

    def test_enterprise_has_nginx_gateway_and_axios_interceptor(self):
        self.engine.render_enterprise_layout(self.project, {"project_name": "saas-app", "website_type": "saas"})
        nginx = Path(self.project, "nginx", "nginx.conf").read_text()
        self.assertIn("location /api", nginx)
        self.assertIn("proxy_pass", nginx)
        api_js = Path(self.project, "frontend", "src", "services", "api.js").read_text()
        self.assertIn("baseURL: API_URL", api_js)
        self.assertIn("interceptors.request", api_js)
        cfg = Path(self.project, "frontend", "src", "services", "apiConfig.js").read_text()
        self.assertIn("'/api'", cfg)

    def test_enterprise_strips_secret_envs(self):
        os.makedirs(os.path.join(self.project, "backend"), exist_ok=True)
        with open(os.path.join(self.project, "backend", ".env.production"), "w") as fh:
            fh.write("JWT_SECRET=should-never-ship\n")
        self.engine.render_enterprise_layout(self.project, {"project_name": "saas-app", "website_type": "saas"})
        self.assertFalse(os.path.exists(os.path.join(self.project, "backend", ".env.production")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "backend", ".env")))
        env_example = Path(self.project, "backend", ".env.example").read_text()
        self.assertIn("DATABASE_URL", env_example)
        self.assertIn("REDIS_URL", env_example)

    def test_enterprise_readme_is_bespoke(self):
        self.engine.render_enterprise_layout(self.project, {"project_name": "saas-app", "website_type": "saas"})
        readme = Path(self.project, "README.md").read_text()
        self.assertIn("PostgreSQL", readme)
        self.assertIn("MySQL", readme)
        self.assertIn("BullMQ", readme)
        self.assertIn("nginx", readme.lower())
        model_files = sorted(
            p.name for p in Path(self.project, "backend", "models").glob("*.js") if p.name != "index.js"
        )
        listed_models = set(re.findall(r"- `([A-Za-z]+)`(?=\n)", readme.split("## Data model")[1]))
        self.assertIn(f"{len(model_files)} models", readme)
        for model in model_files:
            self.assertIn(model[: -len(".js")], listed_models, f"{model} missing from readme model list")
        for name in ("auth", "order", "org", "product", "user"):
            self.assertIn(f"- `{name}`", readme.split("## REST API surface")[1], f"{name} route missing")
        route_bullets = re.findall(r"^\s+- `([a-z0-9_-]+)`$", readme.split("## REST API surface")[1], re.M)
        self.assertGreaterEqual(len(route_bullets), 15)

    # ── Finalize invariants ────────────────────────────────────────────────
    def test_finalize_static_reprunes_artifacts(self):
        spec = {"project_name": "demo", "website_type": "portfolio"}
        self.engine.render_static_layout(self.project, spec)
        # Simulate a later phase re-creating server artifacts.
        os.makedirs(os.path.join(self.project, "nginx"), exist_ok=True)
        os.makedirs(os.path.join(self.project, "backend"), exist_ok=True)
        with open(os.path.join(self.project, "docker-compose.yml"), "w") as fh:
            fh.write("x\n")

        self.engine.finalize_layout(self.project, spec)

        self.assertFalse(os.path.exists(os.path.join(self.project, "nginx")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "backend")))
        self.assertFalse(os.path.exists(os.path.join(self.project, "docker-compose.yml")))
        self.assertTrue(os.path.exists(os.path.join(self.project, "vercel.json")))

    def test_finalize_enterprise_is_noop(self):
        spec = {"project_name": "saas-app", "website_type": "saas"}
        self.engine.render_enterprise_layout(self.project, spec)
        self.engine.finalize_layout(self.project, spec)
        self.assertTrue(os.path.exists(os.path.join(self.project, "backend", "server.js")))


if __name__ == "__main__":
    unittest.main()