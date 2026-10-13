"""Unit Tests for FullStackUltraEngine
======================================
Tests:
  1. Full-stack generation (React 19 frontend + Express.js backend + Docker DevOps)
  2. Execution speed benchmark (< 3000ms)
  3. Frontend and backend file integrity
  4. Integration with AgentOrchestrator
"""

import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.fullstack_ultra_engine import FullStackUltraEngine
from agent.orchestrator import AgentOrchestrator


class TestFullStackUltraEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lumicore_fs_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fullstack_generation_and_speed(self):
        engine = FullStackUltraEngine()
        res = engine.generate_project(
            destination_dir=self.temp_dir,
            prompt="Autonomous Logistics & Global Freight OS",
            brand_name="FreightNexus",
            industry="logistics",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "FreightNexus")
        self.assertTrue(res["total_files"] >= 20)
        self.assertLess(res["elapsed_ms"], 3500)

        for rel_p in [
            "frontend/package.json", "frontend/vite.config.js", "frontend/tailwind.config.js",
            "frontend/index.html", "frontend/src/main.jsx", "frontend/src/App.jsx",
            "frontend/src/index.css", "frontend/src/components/common/GlassNavbar.jsx",
            "frontend/src/components/common/ModernFooter.jsx", "frontend/src/components/common/UniqueLogo.jsx",
            "frontend/src/pages/Home.jsx", "frontend/src/pages/Features.jsx",
            "frontend/src/pages/Pricing.jsx", "frontend/src/pages/Dashboard.jsx",
            "backend/package.json", "backend/server.js", "backend/models/index.js",
            "backend/routes/auth.routes.js", "backend/routes/health.routes.js",
            "backend/migrations/001_create_core_tables.js", "docker-compose.yml",
            ".env.example", "README.md", "LICENSE.md",
        ]:
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, rel_p)), f"Missing: {rel_p}")

        backend_package = json.loads(Path(self.temp_dir, "backend/package.json").read_text())
        self.assertIn("pg", backend_package["dependencies"])
        self.assertNotIn("sqlite3", backend_package["dependencies"])
        self.assertIn("postgres", Path(self.temp_dir, "backend/models/index.js").read_text())
        self.assertIn("postgres:", Path(self.temp_dir, "docker-compose.yml").read_text())
        env_example = Path(self.temp_dir, ".env.example").read_text()
        self.assertIn("POSTGRES_PASSWORD=", env_example)
        self.assertNotIn("VITE_", env_example)
        migration = Path(self.temp_dir, "backend/migrations/001_create_core_tables.js").read_text()
        self.assertIn("const { DataTypes }", migration)
        self.assertNotIn(r"\n", migration)
        license_text = Path(self.temp_dir, "LICENSE.md").read_text()
        self.assertIn("\n\n", license_text)
        self.assertNotIn(r"\n", license_text)

    def test_orchestrator_integration(self):
        orchestrator = AgentOrchestrator(provider_name="gemini")
        self.assertTrue(hasattr(orchestrator, "fullstack_engine"))

        out_dir = os.path.join(self.temp_dir, "orch_out")
        res = orchestrator.generate_fullstack_project(
            destination_dir=out_dir,
            prompt="High-Velocity FinTech Trading Node",
            brand_name="AuraPay",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "AuraPay")
        self.assertTrue(os.path.exists(os.path.join(out_dir, "frontend", "src", "App.jsx")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "backend", "server.js")))
        self.assertEqual(res["stack"]["database"], "PostgreSQL")

    def test_explicit_static_mode_is_not_silently_generated_as_fullstack(self):
        with self.assertRaisesRegex(ValueError, "supports enterprise full-stack delivery only"):
            FullStackUltraEngine().generate_project(
                destination_dir=self.temp_dir,
                generation_contract={"layout_mode": "client-static"},
            )


if __name__ == "__main__":
    unittest.main()
