import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.design_vault import _hex_freq, _extract_fonts, scan_vault  # noqa: E402
from agent.requirement_analyzer import RequirementAnalyzer  # noqa: E402


class TestDesignVault(unittest.TestCase):

    def test_hex_frequency_picks_registered_colors(self):
        css = 'a { color: #7c5cff; } b { color: #7c5cff; background: #f4f4f5; }'
        top = _hex_freq(css)
        self.assertTrue(top)
        self.assertEqual(top[0][0], '#7c5cff')

    def test_font_extraction_parses_google_kit(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400&display=swap" rel="stylesheet">'
        fonts = _extract_fonts(html)
        self.assertEqual(fonts.get('display'), 'Sora')

    def test_vault_scans_registered_sources(self):
        vault = scan_vault()
        self.assertIsInstance(vault, dict)
        self.assertIn('horizonx', vault)

    def test_gcc_region_detected_from_dubai(self):
        spec = RequirementAnalyzer().analyze('Premium restaurant website for the Dubai UAE market')
        self.assertEqual(spec.get('target_region'), 'gcc')

    def test_south_asia_region_detected(self):
        spec = RequirementAnalyzer().analyze('Fashion ecommerce store targeting India and Pakistan')
        self.assertEqual(spec.get('target_region'), 'south-asia')

    def test_ok_tokens_json_is_valid(self):
        p = (Path(__file__).resolve().parent.parent.parent / 'registry' /
             'design-vault' / 'horizonx' / 'style-tokens.json')
        data = json.loads(p.read_text(encoding='utf-8'))
        self.assertIn('palette', data['tokens'])
        self.assertIn('primary', data['tokens']['palette'])


if __name__ == '__main__':
    unittest.main()