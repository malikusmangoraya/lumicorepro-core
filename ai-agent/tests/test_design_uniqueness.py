"""Tests for portfolio-aware uniqueness of generated website designs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.design_uniqueness import (
    apply_design_uniqueness,
    extract_design_signature,
    load_portfolio_signatures,
)
from agent.intelligence.design_manifest import DesignManifestWriter


def _decision():
    return {
        "industry": "saas",
        "brand": "minimal",
        "ui_style": "glassmorphism",
        "hero": "minimal_composition",
        "navigation": "minimal_sticky",
        "grid": "balanced",
        "typography": "clean_sans",
        "motion": "subtle",
        "3d": False,
        "image_ratio": "16:9",
        "cta_style": "clear_primary",
        "surface_style": "flat",
        "card_usage": "minimal",
        "design_manifest": {
            "brand": {"archetype": "minimal"},
            "visual": {"motion": 0.3, "3d": False},
            "typography": {"heading_style": "clean_sans"},
            "colors": {"tokens": {"primary": "#315b42", "accent": "#d89b45"}},
            "industry": "saas",
        },
    }


def _design_plan():
    return {
        "brand_style": "minimal",
        "page_plans": {"Home": {"sections": ["hero", "features", "cta"]}},
        "design_system": {"colors": {"primary": "#315b42", "accent": "#d89b45"}},
    }


class TestDesignSignature(unittest.TestCase):
    def test_signature_is_stable_and_changes_for_meaningful_decisions(self):
        decision = _decision()
        signature = extract_design_signature(decision, _design_plan())
        repeated = extract_design_signature(decision, _design_plan())
        changed = dict(decision, hero="editorial_photography")

        self.assertEqual(signature["fingerprint"], repeated["fingerprint"])
        self.assertNotEqual(
            signature["fingerprint"],
            extract_design_signature(changed, _design_plan())["fingerprint"],
        )
        self.assertIn("palette", signature["dimensions"])
        self.assertIn("home_sections", signature["dimensions"])

    def test_empty_missing_and_malformed_portfolios_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(load_portfolio_signatures(root / "missing"), [])
            broken = root / "broken" / "design-manifest.json"
            broken.parent.mkdir()
            broken.write_text("not-json", encoding="utf-8")
            unreadable = root / "unreadable" / "design-manifest.json"
            unreadable.mkdir(parents=True)
            good = root / "good" / "design-manifest.json"
            good.parent.mkdir()
            good.write_text(json.dumps({"brand": {"archetype": "editorial"}}), encoding="utf-8")

            signatures = load_portfolio_signatures(root)

            self.assertEqual(len(signatures), 1)
            self.assertEqual(signatures[0]["dimensions"]["brand_archetype"], "editorial")

    def test_portfolio_root_scan_error_is_not_reported_as_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("os.scandir", side_effect=PermissionError("scan denied")):
                with self.assertRaises(PermissionError):
                    load_portfolio_signatures(Path(temp_dir))

    def test_portfolio_reads_new_and_legacy_manifests_and_excludes_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = root / "current"
            current.mkdir()
            current_manifest = current / "design-manifest.json"
            current_manifest.write_text(json.dumps({"hero": "minimal_composition"}), encoding="utf-8")

            legacy = root / "legacy" / "design-manifest.json"
            legacy.parent.mkdir()
            legacy_manifest = {
                "brand": {"archetype": "editorial"},
                "visual": {"motion": 0.4, "3d": False},
                "typography": {"heading_style": "refined_serif"},
                "industry": "portfolio",
            }
            legacy.write_text(json.dumps(legacy_manifest), encoding="utf-8")

            before_current = current_manifest.read_bytes()
            before_legacy = legacy.read_bytes()
            signatures = load_portfolio_signatures(root, exclude_project=current)

            self.assertEqual(len(signatures), 1)
            self.assertEqual(signatures[0]["dimensions"]["brand_archetype"], "editorial")
            self.assertEqual(current_manifest.read_bytes(), before_current)
            self.assertEqual(legacy.read_bytes(), before_legacy)

    def test_manifest_writer_persists_signature_without_dropping_existing_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DesignManifestWriter(temp_dir)
            signature = {
                "version": 1,
                "fingerprint": "abc123",
                "dimensions": {"hero": "editorial_photography"},
            }
            decision = {
                "industry": "portfolio",
                "brand": {"archetype": "editorial", "personality": ["direct"]},
                "visual": {"density": 0.4, "motion": "subtle", "3d": False},
                "typography": {"heading_style": "refined_serif"},
                "design_signature": signature,
            }

            writer.write_manifest(decision)
            stored = writer.load_manifest()

        self.assertEqual(stored["design_signature"], signature)
        self.assertEqual(stored["brand"]["archetype"], "editorial")
        self.assertEqual(stored["industry"], "portfolio")
        self.assertEqual(stored["visual"]["motion"], "subtle")

    def test_duplicate_signature_selects_deterministic_alternative_without_mutating_inputs(self):
        decision = _decision()
        plan = _design_plan()
        prior = [extract_design_signature(decision, plan)]

        first = apply_design_uniqueness(decision, plan, prior, seed="brand-a")
        second = apply_design_uniqueness(decision, plan, prior, seed="brand-a")

        self.assertNotEqual(first["design_signature"]["fingerprint"], prior[0]["fingerprint"])
        self.assertEqual(first["design_signature"], second["design_signature"])
        self.assertEqual(decision, _decision())
        self.assertEqual(plan, _design_plan())

    def test_empty_portfolio_preserves_current_design_and_applies_explicit_constraints(self):
        decision = _decision()
        result = apply_design_uniqueness(
            decision,
            _design_plan(),
            [],
            seed="first-project",
            explicit_constraints={"hero": "typographic_hero"},
        )

        expected = _decision()
        expected["hero"] = "typographic_hero"
        for key, value in expected.items():
            if key == "design_manifest":
                for manifest_key in ("brand", "colors", "industry"):
                    self.assertEqual(
                        result["decision"][key][manifest_key], value[manifest_key]
                    )
            else:
                self.assertEqual(result["decision"][key], value)

    def test_explicit_constraints_are_preserved_while_other_dimensions_can_vary(self):
        decision = _decision()
        plan = _design_plan()
        prior = [extract_design_signature(decision, plan)]

        result = apply_design_uniqueness(
            decision,
            plan,
            prior,
            seed="brand-b",
            explicit_constraints={"hero": "minimal_composition"},
        )

        self.assertEqual(result["decision"]["hero"], "minimal_composition")
        self.assertNotEqual(result["design_signature"]["fingerprint"], prior[0]["fingerprint"])

    def test_applied_design_choices_are_recorded_in_manifest_and_plan(self):
        decision = _decision()
        plan = _design_plan()
        prior = [extract_design_signature(decision, plan)]

        result = apply_design_uniqueness(decision, plan, prior, seed="brand-c")
        applied = result["decision"]
        visual = applied["design_manifest"]["visual"]

        self.assertEqual(visual["hero"], applied["hero"])
        self.assertEqual(visual["grid"], applied["grid"])
        self.assertEqual(visual["motion"], applied["motion"])
        self.assertEqual(visual["ui_style"], applied["ui_style"])
        self.assertEqual(
            applied["design_manifest"]["typography"]["heading_style"],
            applied["typography"],
        )
        self.assertEqual(applied["design_manifest"]["design_signature"], result["design_signature"])
        self.assertEqual(result["design_plan"]["design_signature"], result["design_signature"])

    def test_final_restyle_applies_valid_palette_overrides(self):
        from agent.pro_design import restyle_project

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "frontend" / "src" / "config").mkdir(parents=True)
            applied = restyle_project(
                str(project),
                "PaletteTest",
                "minimalist",
                palette_override={"primary": "#123456", "accent": "invalid;"},
            )
            tokens_path = project / "frontend" / "src" / "styles" / "design-tokens.json"
            tokens = json.loads(tokens_path.read_text(encoding="utf-8"))

        self.assertTrue(applied)
        self.assertEqual(tokens["palette"]["primary"], "#123456")
        self.assertNotEqual(tokens["palette"]["accent"], "invalid;")


if __name__ == "__main__":
    unittest.main()