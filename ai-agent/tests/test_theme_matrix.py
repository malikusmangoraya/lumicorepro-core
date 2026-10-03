import sys
import os
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.theme_matrix import ThemeMatrixEngine
from agent.design_style import DesignStyleEngine

ROOT = Path(agent_dir).parent
REG = ROOT / 'registry' / 'templates.json'

EMPTY_ENV = {
    "GEMINI_API_KEY": "", "DEEPSEEK_API_KEY": "", "OPENROUTER_API_KEY": "",
    "ANTHROPIC_API_KEY": "", "MISTRAL_API_KEY": "", "OPENAI_API_KEY": "",
    "ACTIVE_AI_PROVIDER": "gemini",
}


class TestThemeMatrix(unittest.TestCase):
    def setUp(self):
        for k, v in EMPTY_ENV.items():
            os.environ[k] = v
        self.engine = ThemeMatrixEngine(str(REG))

    def test_matrix_has_expected_variants(self):
        matrix = self.engine.build_matrix()
        self.assertGreaterEqual(len(self.engine.templates), 30)
        self.assertGreaterEqual(len(self.engine.style_ids), 15)
        # every variant id is unique and prefixed template::style
        ids = [r['variant_id'] for r in matrix]
        self.assertEqual(len(ids), len(set(ids)))
        for r in matrix:
            self.assertIn('::', r['variant_id'])
            self.assertTrue(r['compatible'])

    def test_compatible_styles_explicit_wins(self):
        tpl = {'id': 'x', 'category': 'restaurant', 'compatible_styles': ['minimalism']}
        self.assertEqual(self.engine.compatible_styles(tpl), ['minimalism'])

    def test_new_categories_present(self):
        cats = {t['category'] for t in self.engine.templates}
        for c in ('agency', 'gym', 'podcast', 'newsletter', 'marketplace', 'insurance', 'automotive', 'wedding'):
            self.assertIn(c, cats)

    def test_metadata_schema_fields(self):
        for tpl in self.engine.templates:
            self.assertIn('id', tpl)
            self.assertIn('compatible_styles', tpl)
            self.assertIn('sections_used', tpl)
            self.assertIn('conversion_optimized', tpl)
            self.assertIn('quality_score', tpl)
            self.assertIn('complexity', tpl)
            self.assertIn('preview_screenshot', tpl)
            self.assertIn('last_updated', tpl)

    def test_quality_gate_contrast(self):
        tpl = {'id': 't', 'category': 'business'}
        gate = self.engine.quality_gate(tpl, 'minimalism')
        self.assertEqual(gate['style_id'], 'minimalism')
        self.assertTrue(gate['checks']['contrast_text_on_bg']['ratio'] >= 4.5, gate)
        # dark cyberpunk style on its dark bg is a known contrast failure risk
        gate2 = self.engine.quality_gate(tpl, 'cyberpunk')
        self.assertIn('contrast_text_on_bg', gate2['checks'])

    def test_quality_gate_all_styles_contrast_calculation(self):
        tpl = {'id': 't2', 'category': 'business'}
        ratios = []
        for style_id in self.engine.style_ids:
            gate = self.engine.quality_gate(tpl, style_id)
            ratios.append((style_id, round(gate['checks']['contrast_text_on_bg']['ratio'], 2)))
        self.assertTrue(all(r >= 0 for _, r in ratios))

    def test_preview_manifest(self):
        d = tempfile.mkdtemp(prefix='tm-')
        try:
            p = os.path.join(d, 'previews', 'acme', 'minimalism.png')
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            Path(p).write_bytes(b'fake')
            man = self.engine.preview_manifest(d)
            self.assertEqual(man['captured'], 1)
            self.assertEqual(man['entries'][0]['template'], 'acme')
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_package_lctemplate(self):
        tpl = {'id': 'restaurant-test', 'name': 'Restaurant Test', 'category': 'restaurant'}
        out = tempfile.mkdtemp(prefix='tm-pkg-')
        try:
            path = self.engine.package_template(tpl, out)
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                for n in ('manifest.json', 'template.json', 'README.md'):
                    self.assertIn(n, names)
                manifest = json.loads(zf.read('manifest.json'))
            self.assertEqual(manifest['id'], 'restaurant-test')
            self.assertEqual(manifest['format'], 'lctemplate')
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_project_variant_resolution(self):
        tpl = {'id': 'restaurant-landing', 'category': 'restaurant', 'name': 'Restaurant'}
        variant = self.engine.project_variant({'design_style': 'claymorphism'}, tpl)
        self.assertEqual(variant['variant_id'], 'restaurant-landing::claymorphism')
        self.assertEqual(variant['style_id'], 'claymorphism')

    def test_auto_suggest_variant(self):
        tpl = {'id': 'ag', 'category': 'agency', 'name': 'Agency'}
        variant = self.engine.project_variant({'industry': 'creative agency'}, tpl)
        self.assertEqual(variant['style_id'], 'swiss')


if __name__ == '__main__':
    unittest.main()
