"""Unit Tests for Benchmark3DFactory
====================================
Tests:
  1. Vertical identification ("3d luxury realestate", "fintech payment", "automotive supercar", etc.)
  2. International benchmark analysis (Sotheby's, Compass, etc.)
  3. Generation of complete 3D interactive platform (WebGL Three.js canvas, mortgage calculator, multi-currency catalog)
  4. Execution speed benchmark (< 3500ms)
  5. Frontend, 3D components, backend, and docker file integrity
  6. Integration with AgentOrchestrator
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

from agent.benchmark_3d_factory import Benchmark3DFactory
from agent.orchestrator import AgentOrchestrator


class TestBenchmark3DFactory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lumicore_3d_bench_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_identify_vertical(self):
        """Test accurate vertical detection from natural language prompt."""
        factory = Benchmark3DFactory()
        
        self.assertEqual(factory.identify_vertical("3d luxury real estate villa with pool"), "realestate")
        self.assertEqual(factory.identify_vertical("penthouse architecture and modern mansion"), "realestate")
        self.assertEqual(factory.identify_vertical("global crypto banking and payment gateway"), "fintech")
        self.assertEqual(factory.identify_vertical("high performance electric supercar showroom"), "automotive")
        self.assertEqual(factory.identify_vertical("enterprise AI cloud database OS"), "saas")

    def test_analyze_and_benchmark(self):
        """Test extraction of international leader benchmarks and supercharged features."""
        factory = Benchmark3DFactory()
        analysis = factory.analyze_and_benchmark("modern luxury architectural realestate")

        self.assertEqual(analysis["vertical"], "realestate")
        self.assertIn("Sotheby's International Realty", analysis["reference_leaders"])
        self.assertIn("Compass", analysis["reference_leaders"])
        self.assertIn("3d_villa_interactive_viewer", analysis["supercharged_features"])
        self.assertIn("live_mortgage_roi_slider", analysis["supercharged_features"])

    def test_generate_full_3d_website_and_speed(self):
        """Test full 3D website synthesis under 3.5s with all 3D components and pages."""
        factory = Benchmark3DFactory()
        res = factory.generate_full_3d_website(
            destination_dir=self.temp_dir,
            prompt="3d luxury realestate architectural residences with 3d villa",
            brand_name="Elysian Estates",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "Elysian Estates")
        self.assertEqual(res["vertical"], "realestate")
        self.assertTrue(res["total_files"] >= 20)
        self.assertLess(res["elapsed_ms"], 3500)

        # ── Verify Critical 3D and Luxury Real Estate Components ─────────
        crucial_files = [
            "frontend/package.json",
            "frontend/vite.config.js",
            "frontend/tailwind.config.js",
            "frontend/index.html",
            "frontend/src/main.jsx",
            "frontend/src/App.jsx",
            "frontend/src/components/common/GlassNavbar.jsx",
            "frontend/src/components/common/ModernFooter.jsx",
            "frontend/src/components/3d/InteractiveVilla3D.jsx",
            "frontend/src/components/business/MortgageCalculator.jsx",
            "frontend/src/pages/Home.jsx",
            "frontend/src/pages/Properties.jsx",
            "frontend/src/pages/Tour3D.jsx",
            "frontend/src/pages/MortgageCalc.jsx",
            "frontend/src/pages/About.jsx",
            "frontend/src/pages/Contact.jsx",
            "backend/package.json",
            "backend/server.js",
            "docker-compose.yml",
            "README.md",
        ]

        for rel_p in crucial_files:
            abs_p = os.path.join(self.temp_dir, rel_p)
            self.assertTrue(os.path.exists(abs_p), f"Missing expected file: {rel_p}")

        # Verify 3D canvas content
        villa_code_path = os.path.join(self.temp_dir, "frontend/src/components/3d/InteractiveVilla3D.jsx")
        with open(villa_code_path, "r", encoding="utf-8") as f:
            villa_code = f.read()
        self.assertIn("Canvas", villa_code)
        self.assertIn("OrbitControls", villa_code)
        self.assertIn("Villa Solaria", villa_code)

        # Verify Brand Name in GlassNavbar.jsx and index.html
        nav_path = os.path.join(self.temp_dir, "frontend/src/components/common/GlassNavbar.jsx")
        with open(nav_path, "r", encoding="utf-8") as f:
            nav_code = f.read()
        self.assertIn("Elysian Estates", nav_code)

        index_path = os.path.join(self.temp_dir, "frontend/index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            index_code = f.read()
        self.assertIn("Elysian Estates", index_code)

        # Verify Mortgage Calculator content
        calc_code_path = os.path.join(self.temp_dir, "frontend/src/components/business/MortgageCalculator.jsx")
        with open(calc_code_path, "r", encoding="utf-8") as f:
            calc_code = f.read()
        self.assertIn("monthlyPayment", calc_code)
        self.assertIn("propertyPrice", calc_code)

    def test_orchestrator_integration(self):
        """Verify seamless invocation via AgentOrchestrator."""
        orchestrator = AgentOrchestrator()
        dest = os.path.join(self.temp_dir, "orchestrator_test_output")

        res = orchestrator.synthesize_benchmark_3d_site(
            destination_dir=dest,
            prompt="Ultra modern luxury real estate penthouse",
            brand_name="Zenith Horizon",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "Zenith Horizon")
        self.assertTrue(os.path.exists(os.path.join(dest, "frontend/src/components/3d/InteractiveVilla3D.jsx")))
        self.assertTrue(os.path.exists(os.path.join(dest, "backend/server.js")))


if __name__ == "__main__":
    unittest.main()
