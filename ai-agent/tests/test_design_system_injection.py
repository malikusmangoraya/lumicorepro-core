"""Tests for UI/UX Architecture & Design System Design Tokens (TRD #3).

Covers semantic color mapping (canvas archetypes + primary/secondary/accent/muted),
glassmorphism spec, cohesive Framer Motion profiles, dark-default theme wiring,
and the raw-hex component conformance gate.
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.design_system_injection import design_system_injector
from agent.project_mode_engine import (
    ProjectModeEngine,
    MODE_CLIENT_STATIC,
    MODE_ENTERPRISE,
)

MARKER = "LUMICORE_DESIGN"


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
    """Synthetic project tree for design-system runs."""

    def __init__(self, root):
        self.root = root
        self.src = os.path.join(root, "frontend", "src")
        _write(os.path.join(root, "frontend", "package.json"),
               '{"name": "trd", "dependencies": {"react": "^19.0.0"}}')
        _write(os.path.join(self.src, "index.css"),
               "@tailwind base;\n@tailwind utilities;\n")
        _write(
            os.path.join(self.src, "App.jsx"),
            (
                "import React from 'react';\n"
                "import './index.css';\n\n"
                "export function App() {\n"
                "  return <div className=\"min-h-screen\">Hi</div>;\n"
                "}\n\n"
                "export default App;\n"
            ),
        )

    def src_path(self, *rel):
        return os.path.join(self.src, *rel)


class DesignSystemTest(unittest.TestCase):
    @staticmethod
    def _spec(website_type="ecommerce"):
        return {"project_name": "trd-test", "website_type": website_type, "project_root": "trd-test"}

    @staticmethod
    def _component_tree(root, body=None):
        comp = os.path.join(root, "frontend", "src", "components", "ui")
        _write(os.path.join(comp, "CleanBtn.jsx"),
               body or "export const c = 'clean';\n")
        return root

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ds_test_")
        self.tree = _Tree(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 1. Semantic color mapping ───────────────────────────────────────────
    def test_semantic_tokens_appended_to_css(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        css = _read(self.tree.src_path("index.css"))
        self.assertEqual(css.count(MARKER), 1)
        self.assertIn("--t-canvas", css)
        self.assertIn("--t-primary", css)
        self.assertIn("--t-secondary", css)
        self.assertIn("--t-accent", css)
        self.assertIn("--t-muted", css)
        # Canvas archetypes: dark default (slate-950 / slate-50), light (white / slate-900).
        self.assertIn(".dark", css)
        self.assertIn("background-color: var(--t-canvas)", css)
        self.assertIn("color: var(--t-canvas-text)", css)

    def test_tailwind_config_written_when_missing(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        cfg = _read(os.path.join(self.tmp, "frontend", "tailwind.config.js"))
        self.assertIn("darkMode", cfg)
        self.assertIn("'class'", cfg)
        self.assertIn("rgb(var(--t-primary) / <alpha-value>)", cfg)
        self.assertIn("primary", cfg)
        self.assertIn("secondary", cfg)
        self.assertIn("accent", cfg)
        self.assertIn("muted", cfg)
        self.assertIn("canvas", cfg)

    def test_tailwind_config_preserved_when_present(self):
        existing = "export default { darkMode: 'media' };\n"
        _write(os.path.join(self.tmp, "frontend", "tailwind.config.js"), existing)
        report = design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        self.assertEqual(report["tailwind_config"]["status"], "skip")
        self.assertEqual(_read(os.path.join(self.tmp, "frontend", "tailwind.config.js")), existing)

    # ── 2. Glassmorphism spec ───────────────────────────────────────────────
    def test_glass_spec_utility_and_component(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        css = _read(self.tree.src_path("index.css"))
        self.assertIn(".glass-md", css)
        self.assertIn("backdrop-filter: blur(12px)", css)
        card = _read(self.tree.src_path("components", "common", "GlassCard.jsx"))
        self.assertIn("backdrop-blur-md", card)
        self.assertIn("bg-white/70", card)
        self.assertIn("dark:bg-slate-900/70", card)
        self.assertIn("border-white/10", card)

    # ── 3. Motion profiles ──────────────────────────────────────────────────
    def test_motion_profiles_cohesive_durations(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        presets = _read(self.tree.src_path("lib", "motionPresets.js"))
        self.assertIn("instant: 80", presets)
        self.assertIn("fast: 140", presets)
        self.assertIn("standard: 240", presets)
        self.assertIn("expressive: 420", presets)
        self.assertIn("[0.22, 1, 0.36, 1]", presets)
        wrapper = _read(self.tree.src_path("components", "motion", "MotionWrapper.jsx"))
        self.assertIn("framer-motion", wrapper)
        self.assertIn("motionPresets", wrapper)
        self.assertIn("useReducedMotion", wrapper)
        self.assertIn("whileInView", wrapper)

    # ── 4. Dark default canvas ──────────────────────────────────────────────
    def test_dark_theme_wired_into_app(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        theme = _read(self.tree.src_path("lib", "theme.js"))
        self.assertIn("classList.add('dark')", theme)
        self.assertIn("prefers-color-scheme", theme)
        app = _read(self.tree.src_path("App.jsx"))
        self.assertIn("import './lib/theme'", app)
        self.assertIn(MARKER, app)

    def test_theme_wiring_idempotent(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        before = _read(self.tree.src_path("App.jsx"))
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        after = _read(self.tree.src_path("App.jsx"))
        self.assertEqual(before, after)
        self.assertEqual(after.count("import './lib/theme'"), 1)

    # ── 5. Raw-hex conformance gate ─────────────────────────────────────────
    def test_raw_hex_in_components_flagged(self):
        self._component_tree(self.tmp, "export const c = { color: '#0f172a' };\n")
        report = design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        scan = report["conformance"]
        self.assertFalse(scan["pass"])
        self.assertGreater(scan["raw_hex_count"], 0)
        self.assertIn("CleanBtn.jsx", scan["violations"][0])

    def test_raw_hex_clean_components_pass(self):
        self._component_tree(self.tmp, "export const c = 'bg-primary';\n")
        report = design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        self.assertTrue(report["conformance"]["pass"])
        self.assertEqual(report["conformance"]["raw_hex_count"], 0)

    # ── 6. Documentation + engine integration ───────────────────────────────
    def test_design_tokens_doc_written(self):
        design_system_injector.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        doc = _read(os.path.join(self.tmp, "DESIGN-TOKENS.md"))
        self.assertIn("Semantic Color Mapping", doc)
        self.assertIn("glass-md", doc)
        self.assertIn("Motion Profiles", doc)
        self.assertIn("DURATIONS", doc)
        self.assertIn("Conformance", doc)

    def test_render_static_layout_injects_design_system(self):
        spec = self._spec("portfolio")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_static")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertIn("design_system", report)
        ds = report["design_system"]
        self.assertIn("tokens_css", ds)
        self.assertTrue(os.path.isfile(os.path.join(root, "DESIGN-TOKENS.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "frontend", "src", "components", "common", "GlassCard.jsx")))
        self.assertTrue(os.path.isfile(os.path.join(root, "frontend", "src", "lib", "motionPresets.js")))
        self.assertTrue(os.path.isfile(os.path.join(root, "frontend", "tailwind.config.js")))
        css = _read(os.path.join(root, "frontend", "src", "index.css"))
        self.assertIn(MARKER, css)

    def test_render_enterprise_layout_injects_design_system(self):
        spec = self._spec("saas")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_ent")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertEqual(report["runtime_mode"], "transactional")
        ds = report["design_system"]
        self.assertIn("tokens_css", ds)
        self.assertTrue(os.path.isfile(os.path.join(root, "DESIGN-TOKENS.md")))
        app = _read(os.path.join(root, "frontend", "src", "App.jsx"))
        self.assertIn("import './lib/theme'", app)


if __name__ == "__main__":
    unittest.main()