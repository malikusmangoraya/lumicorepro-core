"""Tests for the pre-coding design planner, browser layer and screenshot adapter."""
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.design_planner import (
    DESIGN_SYSTEM,
    build_design_system,
    create_design_plan,
    load_playbook,
    validate_design_plan,
)


class TestPlaybookLoading(unittest.TestCase):
    def test_loads_industry_and_brand_from_subdirectories(self):
        result = load_playbook("ecommerce", "luxury")
        self.assertTrue(result["industry"], "industry playbook should load")
        self.assertTrue(result["brand"], "brand playbook should load")

    def test_unknown_playbook_returns_empty(self):
        result = load_playbook("no-such-industry", "no-such-style")
        self.assertEqual(result, {"industry": {}, "brand": {}})


class TestDesignSystemIsolation(unittest.TestCase):
    def test_each_call_returns_independent_copy(self):
        first = build_design_system()
        second = build_design_system()
        first["colors"]["primary"] = "#ff0000"
        self.assertNotEqual(second["colors"]["primary"], "#ff0000")

    def test_module_constant_is_not_mutated(self):
        snapshot = DESIGN_SYSTEM["colors"]["primary"]
        system = build_design_system()
        system["colors"]["primary"] = "#00ff00"
        self.assertEqual(DESIGN_SYSTEM["colors"]["primary"], snapshot)

    def test_palette_override_applies(self):
        system = build_design_system(palette={"primary": "#7a1f2b"})
        self.assertEqual(system["colors"]["primary"], "#7a1f2b")

    def test_design_token_fonts_apply(self):
        system = build_design_system(design_tokens={"heading_font": "Playfair"})
        self.assertEqual(system["typography"]["heading_font"], "Playfair")

    def test_default_palette_has_no_blue_family(self):
        colors = build_design_system()["colors"]
        for key, value in colors.items():
            with self.subTest(color=key):
                self.assertNotIn(value.lower(), ("#3b6ef6", "#2554eb", "#6090fa"))


class TestCreateDesignPlan(unittest.TestCase):
    def test_plan_is_valid_and_populated(self):
        plan = create_design_plan("D2C store", industry="ecommerce", brand_style="luxury")
        self.assertEqual(validate_design_plan(plan), [])
        self.assertTrue(plan["pages"])
        self.assertTrue(plan["page_plans"])
        self.assertTrue(plan["design_system"]["colors"]["primary"])
        self.assertTrue(plan["playbooks_loaded"])

    def test_unknown_industry_falls_back_to_page_set(self):
        plan = create_design_plan("thing", industry="not-real")
        self.assertTrue(plan["pages"])

    def test_custom_sections_override_defaults(self):
        plan = create_design_plan(
            "thing",
            industry="saas",
            custom_sections={"Home": ["hero", "faq"]},
        )
        self.assertEqual(plan["page_plans"]["Home"]["sections"], ["hero", "faq"])

    def test_auth_pages_use_a_centered_card(self):
        """Auth pages are a single centred card, not a multi-section page."""
        plan = create_design_plan("thing", industry="saas")
        self.assertEqual(plan["page_plans"]["Login"]["layout"], "centered_card")
        self.assertEqual(plan["page_plans"]["Register"]["layout"], "centered_card")

    def test_app_pages_use_app_shell(self):
        plan = create_design_plan("thing", industry="saas")
        self.assertEqual(plan["page_plans"]["Dashboard"]["layout"], "app_shell")
        self.assertEqual(plan["page_plans"]["Dashboard"]["hero_variant"], "none")

    def test_plan_does_not_mutate_shared_defaults(self):
        before = DESIGN_SYSTEM["colors"]["primary"]
        create_design_plan("thing", palette={"primary": "#123456"})
        self.assertEqual(DESIGN_SYSTEM["colors"]["primary"], before)


class TestBrowserLayerHonesty(unittest.TestCase):
    def test_unavailable_runtime_reports_not_measured(self):
        from agent.intelligence import browser_integration as bi

        with patch.object(bi, "_resolve_cli", return_value=""):
            report = bi.deep_browser_audit("http://127.0.0.1:1/")
        self.assertEqual(report["status"], "not_measured")
        self.assertFalse(report["available"])
        self.assertTrue(report["reason"])

    def test_never_reports_pass_without_measurement(self):
        """A stalled browser must degrade, not fabricate a pass."""
        from agent.intelligence import browser_integration as bi

        stub = types.SimpleNamespace(
            available=True,
            executable="agent-browser",
            open=lambda url: False,
            close=lambda: None,
        )
        with patch.object(bi, "_resolve_cli", return_value="agent-browser"), \
                patch.object(bi, "AgentBrowser", lambda **kw: stub):
            report = bi.deep_browser_audit("http://127.0.0.1:1/")
        self.assertNotEqual(report["status"], "measured")
        self.assertEqual(report["status"], "failed")

    def test_json_parser_tolerates_noisy_output(self):
        from agent.intelligence.browser_integration import _parse_json

        self.assertEqual(_parse_json('prefix {"a": 1}'), {"a": 1})
        self.assertIsNone(_parse_json("not json at all"))


class TestScreenshotToCode(unittest.TestCase):
    BLUE = ("#3b6ef6", "#2554eb", "#0ea5e9", "#6366f1", "#6090fa")

    def test_empty_source_fails(self):
        from agent.intelligence.screenshot_to_code import screenshot_to_design_spec

        result = screenshot_to_design_spec("")
        self.assertEqual(result["status"], "failed")

    def test_non_image_file_is_rejected(self):
        """A text/HTML file must not pass as an analysed screenshot."""
        from agent.intelligence.screenshot_to_code import screenshot_to_design_spec

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as handle:
            handle.write("<html><body>not an image</body></html>")
            path = handle.name
        try:
            result = screenshot_to_design_spec(path)
            self.assertEqual(result["status"], "failed")
            self.assertIn("unsupported_image_type", result["reason"])
        finally:
            os.unlink(path)

    def test_spoofed_extension_rejected_by_magic_bytes(self):
        """A .png that is really HTML must still be refused."""
        from agent.intelligence.screenshot_to_code import screenshot_to_design_spec

        with tempfile.NamedTemporaryFile("w", suffix=".png", delete=False) as handle:
            handle.write("<html><body>spoofed</body></html>")
            path = handle.name
        try:
            result = screenshot_to_design_spec(path)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["reason"], "image_content_not_an_image")
        finally:
            os.unlink(path)

    def _png(self) -> str:
        import base64

        raw = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        handle = tempfile.NamedTemporaryFile("wb", suffix=".png", delete=False)
        handle.write(raw)
        handle.close()
        return handle.name

    def test_unparsed_image_never_claims_measured_colours(self):
        from agent.intelligence.screenshot_to_code import screenshot_to_design_spec

        path = self._png()
        try:
            result = screenshot_to_design_spec(path, business_type="coffee shop")
        finally:
            os.unlink(path)

        self.assertIn(result["status"], ("analyzed", "heuristic_fallback"))
        self.assertTrue(result["sections"])
        if not result["analyzed"]:
            self.assertFalse(result["colors_measured"])
            self.assertEqual(result["colors"], {})
            self.assertIsNotNone(result["note"])
        for value in self.BLUE:
            self.assertNotIn(value, str(result.get("colors", {})))

    def test_prompt_carries_business_type_and_structure(self):
        from agent.intelligence.screenshot_to_code import (
            design_spec_to_prompt,
            screenshot_to_design_spec,
        )

        path = self._png()
        try:
            spec = screenshot_to_design_spec(path, business_type="coffee shop")
        finally:
            os.unlink(path)
        prompt = design_spec_to_prompt(spec)
        self.assertIn("coffee shop", prompt)
        self.assertIn("sections", prompt)

    def test_prompt_tolerates_empty_spec(self):
        from agent.intelligence.screenshot_to_code import design_spec_to_prompt

        self.assertTrue(design_spec_to_prompt({}))
        self.assertTrue(design_spec_to_prompt(None))


if __name__ == "__main__":
    unittest.main()