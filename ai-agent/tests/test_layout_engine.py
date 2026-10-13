"""Tests for the generic layout engine (agent.layout_engine)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.layout_engine import (  # noqa: E402
    LayoutEngine, CSS_MARKER, _hex_to_rgb_triplet, _svg_to_html, _rotate_hue,
    _luminance, main,
)

_APP_JSX = """import React, { lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Pricing = lazy(() => import('./pages/Pricing'));
const Contact = lazy(() => import('./pages/Contact'));
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/about" element={<About />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}
"""


def _make_project(root: Path) -> Path:
    frontend = root / 'frontend'
    (frontend).mkdir(parents=True, exist_ok=True)
    (frontend / 'package.json').write_text(json.dumps({'name': 'apex-motors', 'version': '1.0.0'}), encoding='utf-8')
    (frontend / 'index.html').write_text('<!doctype html><html><head><title>Apex</title></head><body><div id="root"></div></body></html>', encoding='utf-8')
    (frontend / 'tailwind.config.js').write_text('export default { theme: {} };', encoding='utf-8')
    for rel, content in {
        'src/App.jsx': _APP_JSX,
        'src/index.css': '@tailwind base;\n@tailwind components;\n@tailwind utilities;\n',
        'src/pages/Home.jsx': 'export default function Home() { return <div>Old home</div>; }\n',
        'src/pages/About.jsx': 'export default function About() { return <div>About</div>; }\n',
        'src/components/Navbar.jsx': 'export default function Navbar() { return <nav>Old</nav>; }\n',
        'src/components/Footer.jsx': 'export default function Footer() { return <footer>Old</footer>; }\n',
        'src/components/brand/BRAND.js': 'export const BRAND = { name: "Old" };\n',
        'src/components/brand/BrandLockup.jsx': 'export default function BrandLockup() { return null; }\n',
        'src/components/navigation/GlassNavbar.jsx': 'export default function GlassNavbar() { return null; }\n',
        'src/components/common/UniqueLogo.jsx': 'export default function UniqueLogo() { return null; }\n',
        'src/i18n/index.js': 'export const i18n = {};\n',
    }.items():
        p = frontend / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    return frontend


class TestLayoutEngine(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='lume-layout-'))
        self.frontend = _make_project(self.tmp)
        self.engine = LayoutEngine(str(self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── discovery ────────────────────────────────────────────────────────────
    def test_discovers_frontend_and_routes(self):
        disc = self.engine.discover()
        self.assertTrue(disc['restyleable'])
        self.assertEqual(Path(disc['frontend']).resolve(), self.frontend.resolve())
        self.assertTrue(disc['has_navbar'])
        self.assertTrue(disc['has_footer'])
        self.assertTrue(disc['has_brand_dir'])
        paths = {r['path'] for r in disc['routes']}
        self.assertIn('/', paths)
        self.assertIn('/pricing', paths)

    # ── planning ─────────────────────────────────────────────────────────────
    def test_plan_is_deterministic(self):
        a = self.engine.plan()
        b = LayoutEngine(str(self.tmp)).plan()
        self.assertEqual(a['palette'], b['palette'])
        self.assertEqual(a['style'], b['style'])
        self.assertEqual(a['seed'], b['seed'])

    def test_plan_shape_and_hex_palette(self):
        plan = self.engine.plan()
        for key in ('palette', 'style', 'region', 'sections', 'fonts', 'logo_svg',
                    'brand', 'slug', 'features', 'stats', 'category'):
            self.assertIn(key, plan)
        self.assertTrue(plan['sections'])
        for tok, val in plan['palette'].items():
            self.assertTrue(val.startswith('#'), f'{tok}={val} not hex')

    def test_explicit_style_wins(self):
        plan = self.engine.plan(style='aurora')
        self.assertEqual(plan['style'], 'aurora')

    def test_region_tuning_applies(self):
        gcc = self.engine.plan(region='gcc')
        self.assertEqual(gcc['palette'].get('primary'), '#b8860b')

    def test_industry_inferred_from_name(self):
        plan = self.engine.plan()
        self.assertEqual(plan['category'], 'automotive')

    # ── apply / revert ───────────────────────────────────────────────────────
    def test_dry_run_writes_nothing(self):
        res = self.engine.apply(dry_run=True)
        self.assertTrue(res['success'])
        self.assertTrue(res['dry_run'])
        self.assertIn('src/index.css', res['would_write'])
        self.assertFalse((self.frontend / 'src' / 'styles' / 'design-tokens.json').exists())

    def test_apply_writes_shell_and_manifest(self):
        res = self.engine.apply(skin='full')
        self.assertTrue(res['success'])
        css = (self.frontend / 'src' / 'index.css').read_text(encoding='utf-8')
        self.assertIn(CSS_MARKER, css)
        self.assertIn('--t-primary:', css)
        self.assertTrue((self.frontend / 'src' / 'styles' / 'design-tokens.json').exists())
        self.assertTrue((self.tmp / '.lumicore' / 'layout-manifest.json').exists())
        home = (self.frontend / 'src' / 'pages' / 'Home.jsx').read_text(encoding='utf-8')
        self.assertIn('Navbar', home)
        tw = (self.frontend / 'tailwind.config.js').read_text(encoding='utf-8')
        self.assertIn('--t-primary-rgb', tw)

    def test_generated_logo_is_html_not_react_attrs(self):
        self.engine.apply()
        logo = (self.frontend / 'src' / 'components' / 'common' / 'UniqueLogo.jsx').read_text(encoding='utf-8')
        markup = logo.split('__html:', 1)[1]
        self.assertNotIn('className=', markup)
        self.assertNotIn('stopColor=', markup)

    def test_revert_restores_originals(self):
        original_css = (self.frontend / 'src' / 'index.css').read_text(encoding='utf-8')
        self.engine.apply()
        self.assertNotEqual((self.frontend / 'src' / 'index.css').read_text(encoding='utf-8'), original_css)
        res = self.engine.revert()
        self.assertTrue(res['success'])
        self.assertEqual((self.frontend / 'src' / 'index.css').read_text(encoding='utf-8'), original_css)
        self.assertFalse((self.frontend / 'src' / 'styles' / 'design-tokens.json').exists())
        self.assertFalse((self.tmp / '.lumicore' / 'layout-manifest.json').exists())

    def test_revert_without_manifest_fails_cleanly(self):
        res = self.engine.revert()
        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 404)

    def test_refuses_non_project_dir(self):
        empty = Path(tempfile.mkdtemp(prefix='lume-empty-'))
        try:
            res = LayoutEngine(str(empty)).apply()
            self.assertFalse(res['success'])
            self.assertEqual(res['status'], 422)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    # ── helpers / CLI ────────────────────────────────────────────────────────
    def test_rgb_triplet(self):
        self.assertEqual(_hex_to_rgb_triplet('#ffffff'), '255 255 255')
        self.assertEqual(_hex_to_rgb_triplet('#000'), '0 0 0')
        self.assertEqual(_hex_to_rgb_triplet('nonsense'), '15 23 42')

    def test_category_copy_is_industry_appropriate(self):
        auto = self.engine.plan(industry='automotive')
        self.assertIn('inventory', auto['hero_desc'].lower())
        saas = self.engine.plan(industry='saas')
        self.assertNotEqual(auto['eyebrow'], saas['eyebrow'])

    def test_rotate_hue_preserves_lightness(self):
        out = _rotate_hue('#8b5cf6', 20)
        self.assertTrue(out.startswith('#'))
        self.assertEqual(len(out), 7)
        self.assertNotEqual(out, '#8b5cf6')
        self.assertLess(abs(_luminance(out) - _luminance('#8b5cf6')), 0.2)

    def test_distinct_brands_get_distinct_palettes(self):
        a = self.engine.plan(brand='Alpha Systems')
        b = self.engine.plan(brand='Beta Systems')
        self.assertNotEqual(a['palette']['primary'], b['palette']['primary'])

    def test_dark_style_neutrals_are_dark(self):
        plan = self.engine.plan(style='futuristic')
        self.assertLess(_luminance(plan['palette']['canvas']), 0.5)
        self.assertLess(_luminance(plan['palette']['border']), 0.5)
        self.assertLess(_luminance(plan['palette']['footerBg']), 0.5)

    def test_svg_to_html_conversion(self):
        svg = '<svg className="x"><stop stopColor="#fff"/></svg>'
        out = _svg_to_html(svg)
        self.assertIn('class="x"', out)
        self.assertIn('stop-color="#fff"', out)

    def test_cli_dry_run_exit_zero(self):
        code = main([str(self.tmp), '--dry-run'])
        self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main()
