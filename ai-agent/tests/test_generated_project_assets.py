"""Tests — generated projects ship every production asset they rely on.

These are the portability guarantees: a generated frontend must build on a clean
machine/CI (PostCSS config included), the backend must carry its env template,
schema mirror, migrations and tests, and the branding must be brand-derived.
"""
import json
import tempfile
import unittest
from pathlib import Path

from agent.fullstack_ultra_engine import FullStackUltraEngine
from agent.generation_contract import resolve_generation_contract


def _generate(root: Path, brand: str, industry: str, prompt: str) -> Path:
    destination = root / brand.lower()
    result = FullStackUltraEngine().generate_project(
        str(destination),
        prompt=prompt,
        brand_name=brand,
        industry=industry,
        generation_contract=resolve_generation_contract({}),
    )
    assert result["success"], result.get("errors")
    return destination


class GeneratedProjectAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.fintech = _generate(root, "Zephyr", "fintech", "Zephyr treasury platform")
        cls.gaming = _generate(root, "NexaPlay", "gaming", "NexaPlay community platform")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_postcss_config_ships_with_the_frontend(self):
        config = self.fintech / "frontend" / "postcss.config.cjs"
        self.assertTrue(config.is_file(), "frontend must build without a parent PostCSS config")
        text = config.read_text(encoding="utf-8")
        self.assertIn("tailwindcss", text)
        self.assertIn("autoprefixer", text)

    def test_tailwind_config_is_brand_derived(self):
        a = (self.fintech / "frontend" / "tailwind.config.js").read_text(encoding="utf-8")
        b = (self.gaming / "frontend" / "tailwind.config.js").read_text(encoding="utf-8")
        self.assertIn("slate: {", a)
        self.assertIn("fontFamily", a)
        self.assertNotEqual(a, b)

    def test_index_html_loads_the_generated_fonts_and_archetype(self):
        html = (self.fintech / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("fonts.googleapis.com", html)
        self.assertIn('data-design="', html)
        self.assertIn("theme-color", html)

    def test_contact_api_migration_schema_and_env_example(self):
        backend = self.fintech / "backend"
        self.assertTrue((backend / "routes" / "contact.routes.js").is_file())
        self.assertTrue((backend / "migrations" / "003_create_contact_messages.js").is_file())
        self.assertTrue((backend / "migrations" / "002_create_records_table.js").is_file())
        self.assertTrue((backend / ".env.example").is_file())
        self.assertTrue((self.fintech / "database" / "schema.sql").is_file())
        schema = (self.fintech / "database" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("contact_messages", schema)
        self.assertIn("records", schema)

    def test_backend_tests_exist_and_cover_validation(self):
        test_file = self.fintech / "backend" / "test" / "smoke.test.js"
        self.assertTrue(test_file.is_file())
        self.assertIn("validate", test_file.read_text(encoding="utf-8"))

    def test_logo_uses_brand_variables(self):
        logo = (self.fintech / "frontend" / "src" / "components" / "common" / "UniqueLogo.jsx").read_text(encoding="utf-8")
        self.assertIn("var(--brand-primary)", logo)
        self.assertIn("var(--brand-accent)", logo)
        self.assertNotIn("#64748b", logo)

    def test_generated_env_example_documents_groq_and_xai(self):
        env = (self.fintech / ".env.example").read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=", env)
        self.assertIn("XAI_API_KEY=", env)
        self.assertIn("AI_PROVIDER=", env)

    def test_ai_client_supports_groq_grok_and_custom_base_urls(self):
        client = (self.fintech / "backend" / "services" / "aiClient.js").read_text(encoding="utf-8")
        self.assertIn("groq:", client)
        self.assertIn("grok:", client)
        self.assertIn("OPENAI_BASE_URL", client)
        self.assertIn("GROQ_MODEL", client)


if __name__ == "__main__":
    unittest.main()
