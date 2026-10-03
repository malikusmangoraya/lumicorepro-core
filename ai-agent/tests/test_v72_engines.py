"""Unit Tests for Update, Motion & Hyper-Unique Engines
======================================================
Tests:
  1. UpdateUpgradeEngine (database verification, health, model auditing)
  2. MotionWebsiteEngine (presets, JSX code generation, directory injection)
  3. HyperUniqueSiteEngine (harmonic palettes, SVG vector logo generation, distinct seeds)
  4. AgentOrchestrator integration
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

from agent.update_engine import UpdateUpgradeEngine
from agent.motion_website_engine import MotionWebsiteEngine
from agent.hyper_unique_site_engine import HyperUniqueSiteEngine
from agent.orchestrator import AgentOrchestrator


class TestV72Engines(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lumicore_v72_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_update_engine(self):
        """Test system update, DB health inspection, and environment check."""
        engine = UpdateUpgradeEngine()
        report = engine.run_full_system_update()

        self.assertTrue(report["success"])
        self.assertIn("system_status", report)
        self.assertIn(report["system_status"], ["operational", "auto_healed", "degraded_dependencies"])
        self.assertIn("database", report)
        self.assertIn("runtime", report)
        self.assertTrue(report["runtime"]["all_healthy"])

    def test_motion_website_engine_presets(self):
        """Test motion component code generation across all 5 presets."""
        engine = MotionWebsiteEngine()
        presets = engine.get_supported_presets()
        self.assertEqual(len(presets), 5)
        self.assertIn("kinetic_text", presets)
        self.assertIn("magnetic_spotlight", presets)
        self.assertIn("scroll_parallax", presets)
        self.assertIn("smooth_scroll", presets)
        self.assertIn("staggered_bento", presets)

        for p in presets:
            code = engine.generate_motion_component(p, brand="MotionCorp", primary_color="#10b981")
            self.assertIsInstance(code, str)
            self.assertTrue(len(code) > 150)

        # Test injection
        res = engine.inject_motion_layer(self.temp_dir, preset="kinetic_text", brand="MotionCorp")
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["injected_file"]))

    def test_hyper_unique_site_engine(self):
        """Test generation of unique brand, SVG vector logo, and palettes."""
        engine = HyperUniqueSiteEngine()

        blueprints = []
        prompts = [
            "Quantum Cloud Computing Platform",
            "Luxury Organic Artisan Coffee",
            "Next-Gen High-Frequency Trading Terminal",
        ]

        for p in prompts:
            bp = engine.synthesize_hyper_unique_blueprint(p)
            self.assertTrue(bp["success"])
            self.assertIn("palette", bp)
            self.assertIn("primary", bp["palette"])
            self.assertIn("svg_logo", bp)
            self.assertTrue(bp["svg_logo"].startswith("<svg"))
            self.assertTrue(bp["svg_logo"].endswith("</svg>"))
            self.assertIn("typography", bp)
            blueprints.append(bp)

        # Ensure distinct seeds and palettes across different prompts
        seeds = [b["seed"] for b in blueprints]
        self.assertEqual(len(seeds), len(set(seeds)))

    def test_orchestrator_integration(self):
        """Test integration of the 3 engines inside AgentOrchestrator."""
        orchestrator = AgentOrchestrator(provider_name="gemini")
        self.assertTrue(hasattr(orchestrator, "update_engine"))
        self.assertTrue(hasattr(orchestrator, "motion_engine"))
        self.assertTrue(hasattr(orchestrator, "hyper_unique_engine"))

        # Test helper method
        bp = orchestrator.generate_hyper_unique_blueprint("Autonomous Robotics Studio")
        self.assertTrue(bp["success"])
        self.assertEqual(bp["brand"], "Autonomous")


if __name__ == "__main__":
    unittest.main()
