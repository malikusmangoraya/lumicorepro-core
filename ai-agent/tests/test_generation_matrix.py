"""Tests for the Generation Matrix era-baseline premium layer.

Covers all four PRD pillars over a produced project tree:
- Responsive Fluid UI (index.css @layer utilities, fluid tokens)
- Micro-Interactions (MotionCanvas + MotionSystems + framer-motion dep)
- Lead Capture / Conversion Checkout (LeadForm, CheckoutFlow, analyticsBus)
- Dual Runtime surfacing (spec + layout report + GENERATION-MATRIX.md)
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.generation_matrix import default_matrix
from agent.project_mode_engine import (
    ProjectModeEngine,
    MODE_CLIENT_STATIC,
    MODE_ENTERPRISE,
)

MARKER = "LUMICORE_MATRIX"


def _write(path, content=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content is not None else "")
    return path


def _read(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as f:
        return f.read()


class _Tree:
    """Synthetic min project tree (App.jsx + index.css) for matrix runs."""

    def __init__(self, src, public):
        self.src = src
        self.public = public
        _write(os.path.join(src, "components", "common", ".keep"))
        _write(os.path.join(src, "components", "checkout", ".keep"))
        _write(
            os.path.join(src, "App.jsx"),
            (
                "import React from 'react';\n"
                "import './index.css';\n\n"
                "export function App() {\n"
                "  return (\n"
                "    <div className=\"min-h-screen\">\n"
                "      <h1>Hello</h1>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default App;\n"
            ),
        )

    def path(self, *rel):
        return os.path.join(self.src, *rel)


class GenerationMatrixTest(unittest.TestCase):
    @staticmethod
    def _spec(website_type="ecommerce"):
        return {
            "project_name": "matrix-test",
            "website_type": website_type,
            "project_root": "matrix-test",
        }

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="matrix_test_")
        self.tree = _Tree(
            os.path.join(self.tmp, "frontend", "src"),
            os.path.join(self.tmp, "frontend", "public"),
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── Fluid UI ───────────────────────────────────────────────────────────
    def test_fluid_ui_appends_tokens_and_utilities(self):
        _write(self.tree.path("index.css"), "/* base */\n")
        report = default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        css = _read(self.tree.path("index.css"))
        self.assertTrue(report["fluid_ui"]["applied"])
        self.assertIn("--fluid-space-1", css)
        self.assertIn("--fluid-page", css)
        self.assertIn(".fluid-container", css)
        self.assertIn(".text-fluid-hero", css)
        self.assertIn("@layer utilities", css)
        self.assertIn("/* base */", css)  # pre-existing content preserved

    def test_fluid_ui_idempotent(self):
        _write(self.tree.path("index.css"), "/* base */\n")
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        report2 = default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        self.assertFalse(report2["fluid_ui"]["applied"])
        self.assertEqual(_read(self.tree.path("index.css")).count(MARKER), 1)

    # ── Micro-Interactions ─────────────────────────────────────────────────
    def test_motion_layer_writes_components(self):
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        for rel in (
            "components/common/MotionCanvas.jsx",
            "components/common/MotionSystems.jsx",
            "hooks/useInView.js",
        ):
            self.assertTrue(os.path.isfile(self.tree.path(rel)), rel)
        motion = _read(self.tree.path("components/common/MotionCanvas.jsx"))
        self.assertIn("prefers-reduced-motion", motion)
        self.assertIn("requestAnimationFrame", motion)
        systems = _read(self.tree.path("components/common/MotionSystems.jsx"))
        for export in ("Reveal", "MagneticButton", "TiltCard", "HoverGlow"):
            self.assertIn(f"export function {export}", systems)

    def test_framer_motion_auto_dependency_injected(self):
        _write(self.tmp + "/frontend/package.json", '{"name": "matrix-test", "dependencies": {"react": "^18.2.0"}}')
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        content = _read(self.tmp + "/frontend/package.json")
        self.assertIn('"framer-motion": "^11.0.0"', content)
        self.assertIn('"react": "^18.2.0"', content)  # existing deps preserved

    def test_motion_canvas_mounted_in_app_once(self):
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        app = _read(self.tree.path("App.jsx"))
        self.assertIn("import MotionCanvas from './components/common/MotionCanvas'", app)
        self.assertIn("<MotionCanvas />", app)
        # idempotent — second run does not double-mount or duplicate imports
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        app2 = _read(self.tree.path("App.jsx"))
        self.assertEqual(app2.count("import MotionCanvas"), 1)
        self.assertEqual(app2.count("<MotionCanvas />"), 1)
        self.assertEqual(app2.count("export default App"), 1)
        # marker tokens must be comment-safe (no raw text in JSX / module scope)
        self.assertIn("import MotionCanvas from './components/common/MotionCanvas'; // LUMICORE_MATRIX", app2)
        self.assertIn("{/* LUMICORE_MATRIX */}", app2)
        self.assertIn("<MotionCanvas />", app2)

    # ── Lead Capture / Conversion ──────────────────────────────────────────
    def test_lead_capture_pipeline(self):
        default_matrix.generate(self._spec(), self.tmp, MODE_CLIENT_STATIC)
        bus = _read(self.tree.path("services/analyticsBus.js"))
        lead = _read(self.tree.path("components/common/LeadForm.jsx"))
        checkout = _read(self.tree.path("components/checkout/CheckoutFlow.jsx"))
        self.assertIn("track('lead_capture_start'", lead)
        self.assertIn("honeypot", lead)
        self.assertIn("trackConversion('purchase'", checkout)
        self.assertIn("TRUST_BADGES", checkout)
        self.assertIn("begin_checkout", checkout)
        self.assertIn("window.dispatchEvent(new CustomEvent('lumicore:analytics'", bus)

    # ── Dual Runtime ───────────────────────────────────────────────────────
    def test_runtime_mode_surfaces_in_spec_and_doc(self):
        spec_static = self._spec("portfolio")
        report_static = default_matrix.generate(spec_static, self.tmp, MODE_CLIENT_STATIC)
        self.assertEqual(spec_static["runtime_mode"], "static")
        self.assertEqual(report_static["runtime_mode"], "static")
        doc = _read(os.path.join(self.tmp, "GENERATION-MATRIX.md"))
        self.assertIn("Runtime: **static** pipeline", doc)
        self.assertIn("Go-Live Checklist", doc)

    def test_enterprise_runtime_transactional(self):
        spec = self._spec("ecommerce")
        report = default_matrix.generate(spec, self.tmp, MODE_ENTERPRISE)
        self.assertEqual(spec["runtime_mode"], "transactional")
        self.assertEqual(report["runtime_mode"], "transactional")
        doc = _read(os.path.join(self.tmp, "GENERATION-MATRIX.md"))
        self.assertIn("**transactional**", doc)

    # ── Engine integration ─────────────────────────────────────────────────
    def test_render_static_layout_applies_matrix(self):
        spec = self._spec("portfolio")  # static showcase website type
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_static")
        # minimal frontend tree the static layout expects
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _Tree(os.path.join(root, "frontend", "src"), os.path.join(root, "frontend", "public"))
        report = engine.render_layout(root, spec)
        self.assertEqual(report["mode"], MODE_CLIENT_STATIC)
        self.assertEqual(report["runtime_mode"], "static")
        self.assertEqual(spec["runtime_mode"], "static")
        self.assertTrue(os.path.isfile(os.path.join(root, "GENERATION-MATRIX.md")))
        self.assertTrue(
            os.path.isfile(os.path.join(root, "frontend", "src", "components", "common", "MotionCanvas.jsx"))
        )
        self.assertIn("generation_matrix", report)

    def test_render_enterprise_layout_applies_matrix(self):
        spec = self._spec("ecommerce")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_ent")
        # enterprise layout mounts the backend scaffold copies — fake it
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "backend", "models", "user.js"), "module.exports = {};")
        _write(os.path.join(root, "backend", "routes", "users.routes.js"), "module.exports = {};")
        _write(os.path.join(root, "backend", "config", ".keep"))
        _Tree(os.path.join(root, "frontend", "src"), os.path.join(root, "frontend", "public"))
        report = engine.render_layout(root, spec)
        self.assertEqual(report["mode"], MODE_ENTERPRISE)
        self.assertEqual(report["runtime_mode"], "transactional")
        self.assertEqual(spec["runtime_mode"], "transactional")
        self.assertTrue(
            os.path.isfile(os.path.join(root, "frontend", "src", "components", "checkout", "CheckoutFlow.jsx"))
        )
        self.assertIn("generation_matrix", report)


if __name__ == "__main__":
    unittest.main()