"""Tests — design_forge: each brand gets a coherent, distinct design system."""
import unittest

from agent.design_forge import build_design, hex_to_hsl, hsl_to_hex, slate_scale


class DesignForgeTests(unittest.TestCase):
    def _assert_color_close(self, actual, expected):
        for index in (1, 3, 5):
            self.assertLessEqual(
                abs(int(actual[index:index + 2], 16) - int(expected[index:index + 2], 16)), 1,
                f"{actual} != {expected}",
            )

    def test_hex_hsl_round_trip(self):
        self._assert_color_close(hsl_to_hex(*hex_to_hsl("#10b981")).lower(), "#10b981")
        self._assert_color_close(hsl_to_hex(*hex_to_hsl("#f97316")).lower(), "#f97316")
        self.assertEqual(hex_to_hsl("not-a-color"), (165.0, 35.0, 45.0))

    def test_two_brands_get_different_systems(self):
        a = build_design("CortexDesk", "saas", "#10b981", "#34d399")
        b = build_design("Nimbus", "saas", "#8b5cf6", "#22d3ee")
        self.assertNotEqual(a["slate"]["950"], b["slate"]["950"])
        self.assertNotEqual((a["fonts"]["sans"], a["archetype"]), (b["fonts"]["sans"], b["archetype"]))
        self.assertNotEqual(a["tailwind_config"], b["tailwind_config"])

    def test_same_brand_is_deterministic(self):
        first = build_design("Acme", "fintech", "#0ea5e9", "#22c55e")
        second = build_design("Acme", "fintech", "#0ea5e9", "#22c55e")
        self.assertEqual(first, second)

    def test_industry_hint_selects_an_archetype(self):
        fintech = build_design("AnyBrand", "fintech", "#0ea5e9", "#22c55e")
        editorial = build_design("AnyBrand", "legal", "#0ea5e9", "#22c55e")
        kinetic = build_design("AnyBrand", "gaming", "#0ea5e9", "#22c55e")
        self.assertEqual(fintech["archetype"], "precision")
        self.assertEqual(editorial["archetype"], "editorial")
        self.assertEqual(kinetic["archetype"], "kinetic")

    def test_slate_ramp_is_ordered_and_readable(self):
        scale = slate_scale(200.0, 12.0, 5.0)
        values = [int(scale[str(step)][1:3], 16) for step in (950, 900, 800, 700)]
        self.assertEqual(values, sorted(values))
        self.assertLess(int(scale["950"][1:3], 16), int(scale["400"][1:3], 16))
        self.assertGreater(int(scale["50"][1:3], 16), int(scale["300"][1:3], 16))

    def test_tailwind_config_overrides_slate_and_fonts(self):
        design = build_design("Acme", "saas", "#10b981", "#34d399")
        config = design["tailwind_config"]
        self.assertIn('slate: {', config)
        self.assertIn('950: "', config)
        self.assertIn(f'white: "{design["ink"]}"', config)
        self.assertIn(design["fonts"]["sans"], config)
        self.assertIn(design["radius"]["3xl"], config)

    def test_index_css_defines_brand_variables_and_typography(self):
        design = build_design("Acme", "saas", "#10b981", "#34d399")
        css = design["index_css"]
        self.assertIn("--brand-primary: #10b981", css)
        self.assertIn(design["fonts"]["sans"], css)
        self.assertIn("::selection", css)

    def test_no_glow_archetype_omits_the_radial_gradient(self):
        editorial = build_design("Acme", "legal", "#10b981", "#34d399")
        self.assertFalse(editorial["glow"])
        self.assertNotIn("radial-gradient", editorial["index_css"])

    def test_four_compositions_drive_distinct_heroes_and_section_orders(self):
        fixtures = [
            ("Evergreen", "saas", "aurora", "split-asymmetric"),
            ("Northstar", "legal", "editorial", "divided-reading"),
            ("Meridian", "gaming", "kinetic", "stacked-stepped"),
            ("Ledger", "finance", "precision", "compact-columns"),
        ]
        orders = set()
        for brand, industry, archetype, hero in fixtures:
            design = build_design(brand, industry, "#2563eb", "#0d9488")
            self.assertEqual(design["archetype"], archetype)
            composition = design["composition"]
            self.assertEqual(composition["hero"], hero)
            self.assertEqual(set(composition), {
                "hero", "section_order", "content_width", "spacing", "surface", "motion",
            })
            orders.add(tuple(composition["section_order"]))
            self.assertEqual(composition["motion"], "interaction-only")
        self.assertEqual(len(orders), 4)

    def test_composition_is_not_shared_mutable_state(self):
        first = build_design("Evergreen", "saas", "#2563eb", "#0d9488")
        first["composition"]["section_order"].clear()
        second = build_design("Evergreen", "saas", "#2563eb", "#0d9488")
        self.assertGreater(len(second["composition"]["section_order"]), 2)

    def test_styles_supply_composition_tokens_and_accessible_responsive_controls(self):
        css = build_design("Evergreen", "saas", "#2563eb", "#0d9488")["index_css"]
        for token in ("--surface", "--content-width", "--section-space", "--action", "--on-action"):
            self.assertIn(token, css)
        for selector in (".hero-split", ".hero-editorial", ".hero-kinetic", ".hero-precision",
                         ".capability-asymmetric", ".capability-divided", ".workflow-stepped",
                         ":focus-visible", "prefers-reduced-motion", ".menu-toggle"):
            self.assertIn(selector, css)
        self.assertNotIn("overflow-x: hidden", css)
        self.assertNotIn("@keyframes", css)


if __name__ == "__main__":
    unittest.main()
