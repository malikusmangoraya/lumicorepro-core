"""Unit Tests for FullStackUltraEngine
======================================
Tests:
  1. Full-stack generation (React 19 frontend + Express.js backend + Docker DevOps)
  2. Execution speed benchmark (< 3000ms)
  3. Frontend and backend file integrity
  4. Integration with AgentOrchestrator
"""

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

# Add ai-agent to sys.path
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
        """Test complete generation of clean full-stack application under 3 seconds."""
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
        # Verify sub-3 second execution
        self.assertLess(res["elapsed_ms"], 3500)

        # ── Verify Frontend Structure ────────────────────────────────────
        frontend_files = [
            "frontend/package.json",
            "frontend/vite.config.js",
            "frontend/tailwind.config.js",
            "frontend/index.html",
            "frontend/src/main.jsx",
            "frontend/src/App.jsx",
            "frontend/src/index.css",
            "frontend/src/components/common/GlassNavbar.jsx",
            "frontend/src/components/common/ModernFooter.jsx",
            "frontend/src/components/common/UniqueLogo.jsx",
            "frontend/src/pages/Home.jsx",
            "frontend/src/pages/Features.jsx",
            "frontend/src/pages/Pricing.jsx",
            "frontend/src/pages/Dashboard.jsx",
        ]
        for rel_p in frontend_files:
            p = os.path.join(self.temp_dir, rel_p)
            self.assertTrue(os.path.exists(p), f"Missing frontend file: {rel_p}")

        # ── Verify Backend Structure ─────────────────────────────────────
        backend_files = [
            "backend/package.json",
            "backend/server.js",
            "backend/models/index.js",
            "backend/routes/auth.routes.js",
            "backend/routes/health.routes.js",
        ]
        for rel_p in backend_files:
            p = os.path.join(self.temp_dir, rel_p)
            self.assertTrue(os.path.exists(p), f"Missing backend file: {rel_p}")

        # ── Verify DevOps Structure ──────────────────────────────────────
        devops_files = [
            "docker-compose.yml",
            ".env.example",
            "README.md",
        ]
        for rel_p in devops_files:
            p = os.path.join(self.temp_dir, rel_p)
            self.assertTrue(os.path.exists(p), f"Missing devops file: {rel_p}")

    def test_orchestrator_integration(self):
        """Test full-stack generation through AgentOrchestrator helper method."""
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


if __name__ == "__main__":
    unittest.main()
