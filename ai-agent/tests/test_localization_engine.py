"""Tests for the localization engine's completeness and honesty guarantees.

The generator used to advertise 40+ languages while only overlaying partial
translation tables, so a locale with no overlay shipped the English string
as-is: an Arabic, Urdu or Japanese visitor saw English buttons ("Save",
"Delete", "Next") inside an otherwise translated page.

These tests pin the two rules that fixed it:

  1. Completeness — every locale the engine emits has zero English leftovers
     for every website type.
  2. Honesty — the selector never offers a locale the pack cannot translate,
     so English content is never published under a foreign label.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.i18n_pack import LOCALES as PACK_LOCALES
from agent.i18n_pack import TRANSLATIONS, has_locale, needs_translation
from agent.localization_engine import LocalizationEngine

WEBSITE_TYPES = ("ecommerce", "restaurant", "healthcare", "education", "saas")


class TestPackIntegrity(unittest.TestCase):
    """The pack is the single source of truth, so it must be internally sound."""

    def test_every_locale_covers_the_same_keys(self):
        reference = set(TRANSLATIONS[PACK_LOCALES[0]])
        for code in PACK_LOCALES:
            with self.subTest(locale=code):
                self.assertEqual(set(TRANSLATIONS[code]), reference)

    def test_has_locale_accepts_pack_locales_and_rejects_others(self):
        for code in PACK_LOCALES:
            self.assertTrue(has_locale(code))
        for code in ("it", "nl", "sw", "th", ""):
            self.assertFalse(has_locale(code))

    def test_cognates_are_not_reported_as_missing(self):
        # A reviewed cognate is spelled like English on purpose.
        self.assertFalse(needs_translation("fr", "Contact"))
        self.assertFalse(needs_translation("es", "No"))
        # Untranslated vocabulary is a real gap.
        self.assertTrue(needs_translation("ja", "Save"))
        self.assertTrue(needs_translation("ur", "Track Order"))


class TestTranslationCompleteness(unittest.TestCase):
    def setUp(self):
        self.engine = LocalizationEngine()

    def test_no_english_leftovers_for_any_locale_or_website_type(self):
        for website_type in WEBSITE_TYPES:
            for code in PACK_LOCALES:
                with self.subTest(locale=code, website_type=website_type):
                    self.assertEqual(
                        self.engine.english_leftovers(code, website_type),
                        0,
                        f"{code} still contains English values for {website_type}",
                    )

    def test_leftover_counter_actually_detects_a_regression(self):
        """Prove the gate is not vacuous: without the completion layer it fails."""
        with mock.patch("agent.localization_engine.translate", return_value=None):
            leftovers = self.engine.english_leftovers("ur", "ecommerce")
        self.assertGreater(leftovers, 20, "counter failed to notice English content")

    def test_localisation_applies_to_industry_sections(self):
        healthcare = self.engine._build_translations("ur", "healthcare")
        self.assertEqual(healthcare["healthcare"]["doctors"], "ڈاکٹرز")
        self.assertNotEqual(healthcare["healthcare"]["patients"], "Patients")

    def test_localisation_applies_to_accessibility_strings(self):
        merged = self.engine._build_translations("ja", "ecommerce")
        self.assertNotEqual(merged["accessibility"]["skip_to_main"] if "skip_to_main" in merged["accessibility"] else "x", "Skip to main content")
        self.assertNotEqual(merged["accessibility"]["close_menu"], "Close menu")


class TestLocaleSelectionHonesty(unittest.TestCase):
    def setUp(self):
        self.engine = LocalizationEngine()

    def test_selector_only_returns_translatable_locales(self):
        regions = ("SA", "MENA", "EU", "NA", "APAC", "AF", "LATAM")
        specs = [{"region": r} for r in regions]
        specs += [
            {"features": ["i18n_multilingual"]},
            {"website_type": "saas"},
            {"rtl_support": True},
            {"language_detected": "urdu"},
        ]
        for spec in specs:
            with self.subTest(spec=spec):
                for code in self.engine._select_languages(spec):
                    if code == "en":
                        continue
                    self.assertTrue(
                        has_locale(code),
                        f"selector offered {code} which the pack cannot translate",
                    )

    def test_english_is_always_offered(self):
        for spec in ({}, {"region": "EU"}, {"region": "APAC"}):
            self.assertIn("en", self.engine._select_languages(spec))

    def test_coverage_is_reported_for_every_offered_locale(self):
        langs = self.engine._select_languages({"features": ["i18n_multilingual"]})
        self.assertGreaterEqual(len(langs), 10)


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self.engine = LocalizationEngine()

    def _generate(self, spec):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return self.engine.generate(spec, tmp), tmp

    def test_generate_reports_fully_translated(self):
        result, _ = self._generate(
            {"region": "SA", "rtl_support": True, "website_type": "healthcare"}
        )
        self.assertTrue(result["fully_translated"], result["english_leftovers"])
        self.assertEqual(result["english_leftovers"], {})
        self.assertEqual(sorted(result["rtl_languages"]), ["ar", "ur"])

    def test_generated_urdu_file_is_really_translated(self):
        result, tmp = self._generate({"region": "SA", "website_type": "ecommerce"})
        self.assertIn("ur", result["languages_generated"])
        path = os.path.join(tmp, "frontend", "src", "i18n", "locales", "ur.json")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["common"]["save"], "محفوظ کریں")
        self.assertEqual(data["common"]["delete"], "حذف کریں")
        self.assertEqual(data["common"]["next"], "اگلا")

    def test_generated_japanese_file_is_really_translated(self):
        result, tmp = self._generate({"region": "APAC", "website_type": "ecommerce"})
        self.assertIn("ja", result["languages_generated"])
        path = os.path.join(tmp, "frontend", "src", "i18n", "locales", "ja.json")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["common"]["save"], "保存")
        self.assertEqual(data["ecommerce"]["checkout"], "購入手続き")

    def test_index_declares_supported_languages_and_rtl_switch(self):
        result, tmp = self._generate({"region": "SA", "rtl_support": True})
        index = os.path.join(tmp, "frontend", "src", "i18n", "index.js")
        with open(index, encoding="utf-8") as handle:
            source = handle.read()
        # The template injects the language lists with json.dumps, so the
        # quotes are double quotes.
        for code in result["languages_generated"]:
            self.assertIn(f'"{code}"', source)
        self.assertIn("document.documentElement.dir", source)

    def test_no_locale_file_is_written_for_an_untranslatable_language(self):
        result, tmp = self._generate({"region": "EU"})
        directory = os.path.join(tmp, "frontend", "src", "i18n", "locales")
        written = sorted(name[:-5] for name in os.listdir(directory))
        self.assertEqual(written, sorted(result["languages_generated"]))
        for code in ("it", "nl", "pl", "sw", "th", "vi"):
            self.assertNotIn(code, written)


if __name__ == "__main__":
    unittest.main()
