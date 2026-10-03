"""Unit Tests for Next-Gen Engines
=================================
Tests:
  1. InternationalWebsiteEngine (inspection, replication, pages, icons, images)
  2. Modern3DWebsiteEngine (Three.js/R3F scenes, archetypes, JSX generation)
  3. OmniRepairEngine (auto-repair for 3D canvas, syntax, icons, a11y, layout)
  4. TurboAcceleratorEngine (concurrency, parallel synthesis, caching)
  5. Orchestrator Integration (access & invocation from AgentOrchestrator)
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

from agent.international_website_engine import InternationalWebsiteEngine
from agent.modern_3d_engine import Modern3DWebsiteEngine
from agent.omni_repair_engine import OmniRepairEngine
from agent.turbo_acceleration_engine import TurboAcceleratorEngine
from agent.orchestrator import AgentOrchestrator


class TestNextGenEngines(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lumicore_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_international_website_engine_reference(self):
        """Test inspection of reference sites with sections, icons, and photography."""
        engine = InternationalWebsiteEngine()
        res = engine.replicate_website_spec("stripe.com")

        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "Stripe")
        self.assertEqual(res["industry"], "fintech")
        spec = res["spec"]
        self.assertIn("sections", spec)
        self.assertTrue(len(spec["sections"]) >= 4)
        self.assertIn("pages", spec)
        self.assertIn("Home", spec["pages"])
        self.assertIn("icons", spec)
        self.assertTrue(len(spec["icons"]) > 0)
        self.assertIn("resolved_images", spec)
        self.assertIn("hero_bg", spec["resolved_images"])

    def test_international_website_engine_domain_fallback(self):
        """Test synthesis of arbitrary new domain."""
        engine = InternationalWebsiteEngine()
        res = engine.replicate_website_spec("fintechquantum.io", brand_override="QuantumPay")

        self.assertTrue(res["success"])
        self.assertEqual(res["brand"], "QuantumPay")
        self.assertEqual(res["industry"], "fintech")
        self.assertIn("Home", res["spec"]["pages"])
        self.assertIn("hero", [s["type"] for s in res["spec"]["sections"]])

    def test_modern_3d_engine_generation(self):
        """Test 3D code generation across all archetypes."""
        engine = Modern3DWebsiteEngine()
        archetypes = engine.get_supported_archetypes()
        self.assertIn("floating_crystal", archetypes)
        self.assertIn("cyber_grid", archetypes)
        self.assertIn("particle_cosmos", archetypes)
        self.assertIn("product_viewer", archetypes)
        self.assertIn("holographic_bento", archetypes)

        for arch in archetypes:
            code = engine.generate_component_code(arch, brand_name="Apex3D", primary_color="#6366f1")
            self.assertIsInstance(code, str)
            self.assertTrue(len(code) > 200)

        # Test injection into directory
        src_dir = os.path.join(self.temp_dir, "src", "components", "motion")
        os.makedirs(src_dir, exist_ok=True)
        inject_res = engine.inject_3d_experience(self.temp_dir, archetype="floating_crystal", brand_name="Apex3D")
        self.assertTrue(inject_res["success"])
        self.assertTrue(os.path.exists(inject_res["injected_file"]))

    def test_omni_repair_engine(self):
        """Test auto-repair of broken 3D canvas, unclosed JSX text, missing alt, and non-canonical icons."""
        src_dir = os.path.join(self.temp_dir, "src", "pages")
        os.makedirs(src_dir, exist_ok=True)

        broken_file = os.path.join(src_dir, "TestPage.jsx")
        broken_content = """import React from 'react';

export default function TestPage() {
  return (
    <main className="min-h-screen bg-slate-900">
      <h1>It's the world's most advanced platform</h1>
      <img src="https://example.com/banner.jpg" />
      <TechIcon className="w-5 h-5" />
      <div className="w-full h-0">
        <Canvas>
          <mesh />
        </Canvas>
      </div>
    </main>
  );
}
"""
        with open(broken_file, "w", encoding="utf-8") as f:
            f.write(broken_content)

        engine = OmniRepairEngine()
        repair_res = engine.scan_and_repair_project(self.temp_dir)

        self.assertTrue(repair_res["success"])
        self.assertTrue(repair_res["repairs_applied"] > 0)

        with open(broken_file, "r", encoding="utf-8") as f:
            fixed_content = f.read()

        # Canvas import & Suspense injected
        self.assertIn("@react-three/fiber", fixed_content)
        self.assertIn("<Suspense", fixed_content)
        # Zero-height fixed
        self.assertNotIn("h-0", fixed_content)
        # TechIcon replaced with Cpu
        self.assertIn("Cpu", fixed_content)
        self.assertNotIn("TechIcon", fixed_content)
        # Image alt injected
        self.assertIn("alt=", fixed_content)
        # Apostrophe replaced with &apos;
        self.assertIn("&apos;", fixed_content)
        # Overflow-x-hidden added
        self.assertIn("overflow-x-hidden", fixed_content)

    def test_turbo_accelerator_engine(self):
        """Test concurrent multi-threaded synthesis and in-memory caching."""
        engine = TurboAcceleratorEngine(max_workers=4)
        pages = ["Home", "Features", "Pricing", "About", "Contact", "FAQ"]

        def mock_synth(page: str):
            return {
                "page": page,
                "sections": 6,
                "rendered": True,
            }

        res = engine.synthesize_pages_parallel(pages, mock_synth)
        self.assertTrue(res["success"])
        self.assertEqual(res["completed_pages"], len(pages))
        self.assertTrue(res["turbo_speedup_factor"] >= 1.0)
        self.assertIn("Home", res["results"])

        # Test caching
        calls = [0]
        def loader():
            calls[0] += 1
            return "<div>Cached Template</div>"

        t1 = engine.get_cached_template("temp1", loader)
        t2 = engine.get_cached_template("temp1", loader)
        self.assertEqual(t1, t2)
        self.assertEqual(calls[0], 1)  # Only called once!

    def test_orchestrator_integration(self):
        """Test that AgentOrchestrator exposes and coordinates all 4 engines."""
        orchestrator = AgentOrchestrator(provider_name="gemini")
        self.assertTrue(hasattr(orchestrator, "international_engine"))
        self.assertTrue(hasattr(orchestrator, "modern_3d_engine"))
        self.assertTrue(hasattr(orchestrator, "omni_repair_engine"))
        self.assertTrue(hasattr(orchestrator, "turbo_engine"))

        # Test delegating calls
        spec_res = orchestrator.inspect_and_replicate_website("linear.app")
        self.assertEqual(spec_res["brand"], "Linear")

        archetypes = orchestrator.modern_3d_engine.get_supported_archetypes()
        self.assertIn("floating_crystal", archetypes)


if __name__ == "__main__":
    unittest.main()
