"""Tests for SRS Quality Gates — Functional System Compliance (TRD #5).

Covers SEO architecture (14 default JSON-LD types + OG/twitter meta + heading
hierarchy), i18n architecture (bootstrap + RTL + translator key hooks + coverage
metric), the DevOps ESLint/Prettier ZIP-gate verification, QUALITY-GATES.md, and
engine wiring (static + enterprise).
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.functional_compliance import (
    functional_compliance,
    SEO_MARKER,
    I18N_MARKER,
    JSONLD_REQUIRED_TYPES,
)
from agent.project_mode_engine import ProjectModeEngine

STRUCTURED_DATA_JS = """\
export const SITE_URL = 'https://x.dev';
export const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'X',
};
export const websiteSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
};
export const productSchema = () => ({
  '@context': 'https://schema.org',
  '@type': 'Product',
  offers: { '@type': 'Offer' },
  ...({ rating: true } && { aggregateRating: { '@type': 'AggregateRating' } }),
});
export const breadcrumbSchema = () => ({ '@type': 'BreadcrumbList' });
export const faqSchema = () => ({ '@type': 'FAQPage' });
"""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>X</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>
"""


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
    def __init__(self, root):
        self.root = root
        self.src = os.path.join(root, "frontend", "src")
        _write(os.path.join(self.src, "config", "structured-data.js"), STRUCTURED_DATA_JS)
        _write(
            os.path.join(root, "frontend", "index.html"),
            INDEX_HTML,
        )
        _write(
            os.path.join(self.src, "Home.jsx"),
            'export default function Home() { return <h1>Hello</h1>; }\n',
        )
        _write(
            os.path.join(self.src, "components", "common", "Button.jsx"),
            "export default function Button() { return <span/>; }\n",
        )
        _write(
            os.path.join(self.src, "components", "common", "Localized.jsx"),
            "import { useTranslation } from 'react-i18next';\n"
            "export default function L() { const { t } = useTranslation(); return <p>{t('home')}</p>; }\n",
        )

    def src_path(self, *rel):
        return os.path.join(self.src, *rel)


class FunctionalComplianceTest(unittest.TestCase):
    @staticmethod
    def _spec(website_type="ecommerce"):
        return {
            "project_name": "quality-test",
            "website_type": website_type,
            "project_root": "quality-test",
            "runtime_mode": "transactional",
        }

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fg_test_")
        self.tree = _Tree(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 1a. JSON-LD 14 default types ───────────────────────────────────────
    def test_jsonld_topped_up_to_fourteen(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        j = report["seo"]["jsonld"]
        self.assertEqual(len(j["types"]), 14, j["types"])
        self.assertFalse(j["missing_types"])
        self.assertTrue(j["pass"])
        self.assertEqual(j["top_up"]["status"], "ok")
        self.assertIn(SEO_MARKER, _read(self.tree.src_path("config", "structured-data.js")))
        self.assertEqual(_read(self.tree.src_path("config", "structured-data.js")).count(SEO_MARKER), 1)

    def test_jsonld_topup_idempotent(self):
        functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        second = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        self.assertEqual(second["seo"]["jsonld"]["top_up"]["status"], "skip")
        self.assertEqual(len(second["seo"]["jsonld"]["types"]), 14)

    def test_jsonld_gap_when_no_structured_data(self):
        os.remove(self.tree.src_path("config", "structured-data.js"))
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        j = report["seo"]["jsonld"]
        self.assertFalse(j["pass"])
        self.assertIn("no structured-data.js", j["top_up"]["reason"])

    # ── 1b. Open Graph metadata ────────────────────────────────────────────
    def test_open_graph_injected(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        og = report["seo"]["og"]
        self.assertTrue(og["pass"])
        self.assertEqual(og["missing"], [])
        html = _read(os.path.join(self.tmp, "frontend", "index.html"))
        self.assertIn(SEO_MARKER, html)
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:locale"', html)
        self.assertIn('property="twitter:card"', html)

    def test_open_graph_idempotent(self):
        functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        before = _read(os.path.join(self.tmp, "frontend", "index.html"))
        second = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        after = _read(os.path.join(self.tmp, "frontend", "index.html"))
        self.assertEqual(before, after)
        self.assertEqual(after.count("LUMICORE_SEO:open_graph"), 1)
        self.assertTrue(second["seo"]["og"]["pass"])

    def test_open_graph_gap_reported_when_no_head(self):
        _write(os.path.join(self.tmp, "frontend", "index.html"), "<html><body>x</body></html>\n")
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        self.assertFalse(report["seo"]["og"]["pass"])
        self.assertIn("og:title", report["seo"]["og"]["missing"])

    # ── 1c. Heading hierarchy ──────────────────────────────────────────────
    def test_headings_clean_page_passes(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        self.assertTrue(report["seo"]["headings"]["pass"])
        self.assertEqual(report["seo"]["headings"]["violations"], [])

    def test_headings_multiple_h1_flagged(self):
        _write(self.tree.src_path("Home.jsx"),
               "export default function Home() { return <><h1>A</h1><h1>B</h1></>; }\n")
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        self.assertFalse(report["seo"]["headings"]["pass"])
        self.assertTrue(any("multiple h1" in v for v in report["seo"]["headings"]["violations"]))

    def test_headings_level_jump_flagged(self):
        _write(self.tree.src_path("Home.jsx"),
               "export default function Home() { return <><h1>A</h1><h4>B</h4></>; }\n")
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        self.assertFalse(report["seo"]["headings"]["pass"])
        self.assertTrue(any("level jump" in v for v in report["seo"]["headings"]["violations"]))

    # ── 2. i18n architecture ───────────────────────────────────────────────
    def test_i18n_bootstrap_injected_with_rtl(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        boot = report["i18n"]["bootstrap"]
        self.assertTrue(boot["pass"])
        self.assertTrue(boot["rtl_support"])
        content = _read(self.tree.src_path("i18n", "i18n.js"))
        self.assertIn(I18N_MARKER, content)
        self.assertIn("RTL_LANGUAGES", content)
        self.assertIn("document.documentElement.dir", content)
        self.assertIn("initReactI18next", content)

    def test_i18n_translator_key_hook_and_coverage(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        hook = report["i18n"]["hook"]
        self.assertIn("useAppTranslation", hook["file"])
        self.assertEqual(hook["status"], "injected")
        cov = report["i18n"]["coverage"]
        self.assertEqual(cov["components"], 2)
        self.assertEqual(cov["hook_using"], 1)
        self.assertEqual(cov["percent"], 50.0)

    # ── 3. Code-quality gates (verified wiring) ────────────────────────────
    def test_devops_gate_verified(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        cq = report["code_quality"]
        self.assertTrue(cq["eslint_pipeline"])
        self.assertTrue(cq["prettier_pipeline"])
        self.assertTrue(cq["gate_module"])
        self.assertIn("ZIP", cq["note"])

    def test_quality_gates_doc_written(self):
        report = functional_compliance.generate(self._spec(), self.tmp, "enterprise")
        doc = _read(os.path.join(self.tmp, "QUALITY-GATES.md"))
        self.assertIn("SEO Architecture", doc)
        self.assertIn("Internationalization", doc)
        self.assertIn("Code Quality Assurance", doc)
        self.assertIn("14/14", doc)

    # ── 4. Engine integration ───────────────────────────────────────────────
    def _render(self, wtype, suffix):
        spec = {"project_name": "qg", "website_type": wtype, "project_root": "qg"}
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, suffix)
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        return engine.render_layout(root, spec), root

    def test_render_static_injects_compliance_gate(self):
        report, root = self._render("portfolio", "render_static")
        self.assertIn("functional_compliance", report)
        fc = report["functional_compliance"]
        self.assertIn("seo", fc)
        self.assertIn("i18n", fc)
        self.assertTrue(fc["i18n"]["bootstrap"]["pass"])
        self.assertTrue(os.path.isfile(os.path.join(root, "QUALITY-GATES.md")))
        self.assertEqual(fc["i18n"]["hook"]["status"], "injected")

    def test_render_enterprise_injects_compliance_gate(self):
        report, root = self._render("ecommerce", "render_ent")
        fc = report["functional_compliance"]
        self.assertIn("seo", fc)
        self.assertIn("i18n", fc)
        self.assertTrue(os.path.isfile(os.path.join(root, "QUALITY-GATES.md")))
        self.assertTrue(fc["i18n"]["bootstrap"]["pass"])


if __name__ == "__main__":
    unittest.main()