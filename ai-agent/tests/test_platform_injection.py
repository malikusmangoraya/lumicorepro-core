"""Tests for Platform Injection Rules (TRD #2).

Covers frontend runtime architecture (stack pins, state topologies, lazy layouts,
CLS budget) and backend blueprint conformance (Express/Sequelize/BullMQ with
in-memory Redis fallback).
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.platform_injection import platform_injection
from agent.project_mode_engine import (
    ProjectModeEngine,
    MODE_CLIENT_STATIC,
    MODE_ENTERPRISE,
)

MARKER = "LUMICORE_PLATFORM"


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
    """Synthetic project tree for platform-injection runs."""

    def __init__(self, root):
        self.root = root
        self.src = os.path.join(root, "frontend", "src")
        _write(os.path.join(root, "frontend", "package.json"),
               '{"name": "trd-test", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}, "devDependencies": {"vite": "^5.4.0", "tailwindcss": "^3.4.1"}}')
        _write(os.path.join(self.src, "index.css"), "@tailwind base;\n@tailwind utilities;\n")
        _write(
            os.path.join(self.src, "App.jsx"),
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

    def pkg(self):
        import json

        return json.loads(_read(os.path.join(self.root, "frontend", "package.json")))

    def src_path(self, *rel):
        return os.path.join(self.src, *rel)


class PlatformInjectionTest(unittest.TestCase):
    @staticmethod
    def _spec(website_type="ecommerce"):
        return {"project_name": "trd-test", "website_type": website_type, "project_root": "trd-test"}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="trd_test_")
        self.tree = _Tree(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 1. Frontend core stack pins ────────────────────────────────────────
    def test_frontend_stack_pins(self):
        report = platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        report["frontend_stack"]
        pkg = self.tree.pkg()
        deps = pkg["dependencies"]
        self.assertEqual(deps["react"], "^19.2.0")
        self.assertEqual(deps["react-dom"], "^19.2.0")
        self.assertEqual(deps["@tanstack/react-query"], "^5.59.0")
        self.assertEqual(deps["zustand"], "^5.0.0")
        self.assertEqual(pkg["devDependencies"]["vite"], "^8.2.0")
        # Tailwind stays on v3.4.x line (already compliant)
        self.assertTrue(pkg["devDependencies"]["tailwindcss"].startswith("^3.4"))

    def test_stack_pins_are_idempotent(self):
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        before = self.tree.pkg()
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        after = self.tree.pkg()
        self.assertEqual(before, after)

    # ── 2. State topologies (React Query cluster + Zustand) ────────────────
    def test_state_topology_files(self):
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        query = _read(self.tree.src_path("lib", "queryClient.js"))
        self.assertIn("new QueryClient", query)
        self.assertIn("staleTime", query)
        hook = _read(self.tree.src_path("hooks", "useApiQuery.js"))
        self.assertIn("useQuery", hook)
        self.assertIn("import('../services/api')", hook)  # static/build-safe fallback
        store = _read(self.tree.src_path("store", "useAppStore.js"))
        self.assertIn("create", store)
        self.assertIn("Zustand", store)
        providers = _read(self.tree.src_path("lib", "AppProviders.jsx"))
        self.assertIn("QueryClientProvider", providers)

    def test_provider_wraps_app_default_export(self):
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        app = _read(self.tree.src_path("App.jsx"))
        self.assertIn("import AppProviders from './lib/AppProviders';", app)
        self.assertIn("export default function AppWithProviders()", app)
        self.assertIn("<AppProviders>", app)
        self.assertIn("<App />", app)
        # original App + default behaviours preserved
        self.assertIn("export function App()", app)
        self.assertNotIn("export default App;", app)

    def test_provider_wrap_skips_unknown_template(self):
        _write(self.tree.src_path("App.jsx"), "export default function Custom() { return null; }\n")
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        app = _read(self.tree.src_path("App.jsx"))
        self.assertIn("Custom", app)
        self.assertNotIn("AppWithProviders", app)

    # ── 3. Optimization budgets (lazy layouts + CLS) ───────────────────────
    def test_lazy_layouts_use_react_lazy(self):
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        registry = _read(self.tree.src_path("lib", "LazyLayouts.jsx"))
        self.assertIn("React.lazy", registry)
        self.assertIn("LandingLayout", registry)
        self.assertIn("AppLayout", registry)
        self.assertIn("Suspense", registry)
        for rel in ("layouts/LandingLayout.jsx", "layouts/AppLayout.jsx",
                    "components/common/LayoutSkeleton.jsx"):
            self.assertTrue(os.path.isfile(self.tree.src_path(rel)), rel)
        skeleton = _read(self.tree.src_path("components", "common", "LayoutSkeleton.jsx"))
        self.assertIn("minHeight", skeleton)
        self.assertIn("skeleton-shimmer", skeleton)

    def test_cls_budget_css_appended_idempotent(self):
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        css = _read(self.tree.src_path("index.css"))
        self.assertEqual(css.count(MARKER), 1)
        self.assertIn(".cls-reserve", css)
        self.assertIn(".skeleton-shimmer", css)
        self.assertIn("img, video, iframe", css)
        self.assertIn("@tailwind utilities", css)  # tailwind directives preserved
        # idempotency
        platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        css2 = _read(self.tree.src_path("index.css"))
        self.assertEqual(css2.count(MARKER), 1)

    # ── 4. Backend blueprint conformance ───────────────────────────────────
    def _backend_tree(self, with_memory_fallback=True):
        b = os.path.join(self.tmp, "backend")
        _write(os.path.join(b, "controllers", "user.controller.js"), "/* controller */")
        _write(os.path.join(b, "utils", "response.js"),
               "// status helpers\nexport const sendSuccess = (res, data) => res.status(200);")
        _write(os.path.join(b, "middleware", "errorHandler.js"), "// status maps\n")
        _write(os.path.join(b, "models", "User.js"), "// sequelize model\n")
        _write(os.path.join(b, "services", "queue", "queue.service.js"),
               "import { Queue } from 'bullmq';\nif (connection.isMemory) {}\n")
        redis_body = "isMemory" if with_memory_fallback else "export const getRedis = () => {};\n"
        _write(os.path.join(b, "services", "cache", "redis.client.js"), redis_body)
        return b

    def test_backend_blueprint_applies_only_to_transactional_runtime(self):
        report = platform_injection.generate(self._spec("portfolio"), self.tmp, MODE_CLIENT_STATIC)
        self.assertFalse(report["backend_blueprint"]["applies"])
        self.assertIn("not", report["backend_blueprint"]["reason"])

    def test_backend_blueprint_conformant(self):
        self._backend_tree(with_memory_fallback=True)
        spec = self._spec("ecommerce")
        spec["runtime_mode"] = "transactional"
        report = platform_injection.generate(spec, self.tmp, MODE_ENTERPRISE)
        bb = report["backend_blueprint"]
        self.assertTrue(bb["applies"])
        self.assertTrue(bb["queue_service"]["pass"])
        self.assertIn("in-memory fallback present", bb["queue_service"]["hint"])
        self.assertTrue(bb["conformant"])

    def test_backend_blueprint_flags_missing_memory_fallback(self):
        self._backend_tree(with_memory_fallback=False)
        spec = self._spec("ecommerce")
        spec["runtime_mode"] = "transactional"
        report = platform_injection.generate(spec, self.tmp, MODE_ENTERPRISE)
        self.assertFalse(report["backend_blueprint"]["conformant"])
        self.assertNotIn("in-memory fallback present", report["backend_blueprint"]["redis_protected_fallback"]["hint"])

    # ── Engine integration ─────────────────────────────────────────────────
    def test_render_static_layout_injects_platform(self):
        spec = self._spec("portfolio")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_static")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))

        # Minimal tree (reuse the same shape as the matrix tests).
        _write(os.path.join(root, "frontend", "package.json"),
               '{"name": "trd", "dependencies": {"react": "^18.2.0"}}')
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertEqual(report["runtime_mode"], "static")
        self.assertIn("platform_injection", report)
        self.assertTrue(os.path.isfile(os.path.join(root, "PLATFORM-INJECTION.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "frontend", "src", "lib", "queryClient.js")))
        # static runtime: backend blueprint not applicable
        self.assertFalse(report["platform_injection"]["backend_blueprint"]["applies"])

    def test_render_enterprise_layout_injects_platform(self):
        spec = self._spec("ecommerce")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_ent")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertEqual(report["runtime_mode"], "transactional")
        self.assertIn("platform_injection", report)
        bb = report["platform_injection"]["backend_blueprint"]
        self.assertTrue(bb["applies"])
        # Canonical overlay provides the full blueprint (queue + Redis fallback).
        self.assertTrue(bb["conformant"])


if __name__ == "__main__":
    unittest.main()