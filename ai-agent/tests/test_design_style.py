import sys
import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.design_style import DesignStyleEngine

EMPTY_ENV = {
    "GEMINI_API_KEY": "",
    "DEEPSEEK_API_KEY": "",
    "OPENROUTER_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "MISTRAL_API_KEY": "",
    "OPENAI_API_KEY": "",
    "ACTIVE_AI_PROVIDER": "gemini",
}


class TestDesignStyleEngine(unittest.TestCase):
    def setUp(self):
        for k, v in EMPTY_ENV.items():
            os.environ[k] = v
        self.engine = DesignStyleEngine()
        self.tmp = tempfile.mkdtemp(prefix="test-ds-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _apply(self, spec, project_dir=None):
        target = project_dir or self.tmp
        Path(target, "frontend").mkdir(parents=True, exist_ok=True)
        Path(target, "frontend", "public").mkdir(parents=True, exist_ok=True)
        return self.engine.apply(target, spec)

    def test_style_catalog_has_full_catalog(self):
        self.assertGreaterEqual(len(self.engine.STYLES), 15)
        for style_id, meta in self.engine.STYLES.items():
            self.assertIn("name", meta)
            self.assertIn("color", meta)
            self.assertIn("composition", meta)
            for key in ("primary", "secondary", "accent", "bg", "card", "surface", "text", "muted", "border"):
                self.assertIn(key, meta["color"], style_id)
            self.assertIn("fonts", meta)
            self.assertIn("radius", meta)
            self.assertIn("shadow", meta)
            self.assertIn("border", meta)
            self.assertIn("effects", meta)
            self.assertIn("bg", meta["color"])

    def test_resolve_style_user_override_wins(self):
        spec = {"design_style": "cyberpunk", "industry": "restaurant"}
        style = self.engine.resolve_style(spec)
        self.assertEqual(style["id"], "cyberpunk")

    def test_resolve_style_auto_suggestion_by_industry(self):
        self.assertEqual(self.engine.resolve_style({"industry": "SaaS"})["id"], "glassmorphism")
        self.assertEqual(self.engine.resolve_style({"website_type": "portfolio"})["id"], "minimalism")
        self.assertEqual(self.engine.resolve_style({"website_type": "ai assistant"})["id"], "aurora")

    def test_resolve_style_default(self):
        self.assertEqual(self.engine.resolve_style({})["id"], DesignStyleEngine.DEFAULT_STYLE)

    def test_apply_writes_all_root_outputs(self):
        report = self._apply({"project_name": "CloudShop", "design_style": "bento_grid"})
        tokens = os.path.join(self.tmp, "frontend", "design-tokens.json")
        self.assertTrue(os.path.exists(tokens), report)
        data = json.load(open(tokens, encoding="utf-8"))
        self.assertIn("style", data)
        self.assertEqual(data["style"], "bento_grid")
        self.assertIn("palette", data)
        self.assertIn("palette_hsl", data)
        self.assertIn("typography", data)
        self.assertIn("generated_by", data)

        manifest = json.load(open(report["manifest_path"], encoding="utf-8"))
        counts = {}
        for entry in manifest["assets"]:
            counts[entry["category"]] = counts.get(entry["category"], 0) + 1
        self.assertEqual(counts["hero"], 4)
        self.assertEqual(counts["icons"], 12)
        self.assertEqual(counts["backgrounds"], 3)
        self.assertEqual(counts["illustrations"], 5)
        self.assertEqual(counts["mockups"], 3)

        css_file = report["css_file"]
        self.assertTrue(os.path.exists(css_file))
        css = open(css_file, encoding="utf-8").read()
        self.assertIn(":root {", css)
        self.assertIn("--background:", css)
        self.assertIn("--foreground:", css)
        self.assertIn("--primary:", css)
        self.assertIn("--primary-foreground:", css)
        self.assertIn("--card:", css)
        self.assertIn("--destructive:", css)
        self.assertIn("--font-display:", css)
        self.assertIn('[data-style="bento_grid"]', css)

        doc = report["design_doc"]
        self.assertTrue(os.path.exists(doc))
        self.assertIn("CloudShop", open(doc, encoding="utf-8").read())

    def test_apply_writes_assets_and_manifest(self):
        self._apply({"project_name": "StyleTest", "design_style": "neo_brutalism"})
        assets_dir = os.path.join(self.tmp, "frontend", "public", "assets")
        manifest = json.load(open(os.path.join(assets_dir, "manifest.json"), encoding="utf-8"))
        self.assertEqual(manifest["count"], 27)
        self.assertEqual(manifest["style"], "neo_brutalism")
        for entry in manifest["assets"]:
            path = os.path.join(self.tmp, "frontend", "public", entry["file"])
            self.assertTrue(os.path.exists(path), entry["file"])
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            self.assertTrue(body.startswith("<svg"))
            self.assertIn("</svg>", body)

    def test_all_styles_generate_hero_and_icons(self):
        for style_id in self.engine.STYLES:
            project = tempfile.mkdtemp(prefix=f"test-{style_id}-", dir=self.tmp)
            self._apply({"project_name": "X", "design_style": style_id}, project_dir=project)
            hero = os.path.join(project, "frontend", "public", "assets", style_id, "hero")
            icon = os.path.join(project, "frontend", "public", "assets", style_id, "icons")
            self.assertEqual(len(os.listdir(hero)), 4, style_id)
            self.assertEqual(len(os.listdir(icon)), 12, style_id)

    def test_deterministic_output(self):
        def run_once():
            project = tempfile.mkdtemp(prefix="det-", dir=self.tmp)
            self._apply({"project_name": "SameName", "design_style": "aurora"}, project_dir=project)
            hero = os.path.join(project, "frontend", "public", "assets", "aurora", "hero", "hero-1.svg")
            return open(hero, encoding="utf-8").read()

        a = run_once()
        b = run_once()
        self.assertEqual(a, b)

    def test_register_style_extends_catalog(self):
        base_count = len(self.engine.STYLES)
        self.engine.register_style({
            'id': 'neon_test',
            'name': 'Neon Test',
            'color': {'bg': '#0b0f19', 'primary': '#22d3ee', 'secondary': '#f0abfc',
                      'accent': '#a78bfa', 'text': '#f8fafc', 'muted': '#64748b',
                      'surface': '#101827', 'card': '#0f172a', 'border': '#1e293b'},
            'fonts': {'display': 'Sans', 'sans': 'Sans', 'mono': 'Mono'},
            'radius': {'card': '0.5rem', 'button': '0.5rem'},
            'shadow': {'card': 'none', 'button': 'none'},
            'border': {'card': '1px', 'button': '1px'},
            'effects': {'blur': '0px', 'glow': 'glow'},
            'composition': 'neon', 'weight': 'bold',
        })
        try:
            style = self.engine.resolve_style({"design_style": "neon_test"})
            self.assertEqual(style["id"], "neon_test")
            self.assertEqual(len(self.engine.STYLES), base_count + 1)
        finally:
            self.engine.STYLES.pop('neon_test')
        self.assertEqual(len(self.engine.STYLES), base_count)

    def test_inject_css_is_non_destructive(self):
        project = tempfile.mkdtemp(prefix="css-", dir=self.tmp)
        css_dir = os.path.join(project, "frontend", "src")
        os.makedirs(css_dir, exist_ok=True)
        existing = os.path.join(css_dir, "index.css")
        sentinel = "/* existing user styles */"
        with open(existing, "w", encoding="utf-8") as fh:
            fh.write(sentinel + "\n")
        self._apply({"project_name": "Keep", "design_style": "minimalism"},
                    project_dir=project)
        with open(existing, encoding="utf-8") as fh:
            content = fh.read()
        self.assertTrue(content.startswith(sentinel))
        self.assertIn(":root {", content)


if __name__ == "__main__":
    unittest.main()