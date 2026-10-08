"""Behavioral tests for deterministic website design DNA selection."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.design_system_engine import DesignSystemEngine, get_design_catalog


class TestDesignSystemEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DesignSystemEngine()
        self.spec = {
            "project_name": "claim-desk",
            "original_prompt": "Insurance claims intake and adjuster workflow",
            "industry": "insurance",
            "audience": ["claims adjusters"],
            "design_seed": "claims-v1",
            "features": ["claim intake", "document review", "adjuster queue"],
        }

    def test_selection_is_deterministic_for_the_same_brief_and_seed(self):
        first = self.engine.resolve(self.spec)
        second = self.engine.resolve(self.spec)

        self.assertEqual(first, second)
        self.assertEqual(first["design_dna"]["version"], 1)
        self.assertEqual(first["design_dna"]["niche"], "insurance")

    def test_catalog_has_required_hero_navigation_and_niche_blocks(self):
        catalog = get_design_catalog()

        self.assertGreaterEqual(len(catalog["heroes"]), 12)
        self.assertGreaterEqual(len(catalog["navigation"]), 8)
        self.assertGreaterEqual(len(catalog["sections"]), 10)
        self.assertTrue(all(item.get("id") and item.get("niches") for item in catalog["heroes"]))

    def test_insurance_selection_includes_claims_specific_home_block(self):
        result = self.engine.resolve(self.spec)
        home_blocks = result["design_dna"]["layout"]["pages"]["Home"]["section_order"]

        self.assertIn("claims_queue", home_blocks)

    def test_explicit_hero_constraint_is_preserved(self):
        constrained = dict(self.spec, design_constraints={"hero": "typographic"})

        result = self.engine.resolve(constrained)

        self.assertEqual(result["design_dna"]["layout"]["hero_archetype"], "typographic")

    def test_collision_regenerates_unconstrained_layout_within_three_candidates(self):
        baseline = self.engine.resolve(self.spec)["design_dna"]
        collision = {
            "dimensions": {
                "hero": baseline["layout"]["hero_archetype"],
                "navigation": baseline["layout"]["navigation_pattern"],
                "home_sections": baseline["layout"]["pages"]["Home"]["section_order"],
            }
        }

        result = self.engine.resolve(self.spec, prior=[collision])
        selected = result["design_dna"]["layout"]

        self.assertLessEqual(len(result["attempts"]), 3)
        self.assertNotEqual(
            (selected["hero_archetype"], selected["navigation_pattern"], selected["pages"]["Home"]["section_order"]),
            (
                collision["dimensions"]["hero"],
                collision["dimensions"]["navigation"],
                collision["dimensions"]["home_sections"],
            ),
        )

    def test_three_unavoidable_collisions_are_reported_as_failed(self):
        constrained = dict(
            self.spec,
            design_constraints={
                "hero": "typographic",
                "navigation": "minimal_top",
                "home_sections": ["hero", "claims_queue", "contact_cta"],
            },
        )
        dimensions = {
            "hero": "typographic",
            "navigation": "minimal_top",
            "home_sections": ["hero", "claims_queue", "contact_cta"],
        }

        result = self.engine.resolve(
            constrained,
            prior=[{"dimensions": dimensions}] * 3,
        )

        self.assertEqual(len(result["attempts"]), 3)
        self.assertFalse(result["design_dna"]["selection"]["unique"])


if __name__ == "__main__":
    unittest.main()