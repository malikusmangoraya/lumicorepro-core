import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.design_resources import (  # noqa: E402
    load_catalog,
    merge_profiles,
    resolve_references,
    resource_contribution,
    verify_catalog,
)
from agent.intelligence.reference_intelligence import (  # noqa: E402
    extract_reference_intelligence,
    _KNOWN_REFERENCES,
)
from agent.intelligence.benchmark_first import run_benchmark_first  # noqa: E402


class TestDesignResources(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(refresh=True)
        cls.slugs = {r.get("slug") for r in cls.catalog}

    def test_catalog_has_all_expected_resources(self):
        expected = {
            "penpot", "astryx", "appica-ui", "shadcn-ui", "magic-ui",
            "aceternity-ui", "cult-ui", "chonks-ui", "uiverse", "codrops",
            "webzibition", "design-resources-for-developers",
            "awesome-ui-libraries", "ui-ux-design-resources",
        }
        self.assertTrue(expected.issubset(self.slugs))

    def test_every_resource_has_required_keys(self):
        for item in self.catalog:
            self.assertTrue(item.get("slug"))
            self.assertTrue(item.get("name"))
            self.assertTrue(item.get("license"))
            self.assertTrue(item.get("url"))
            self.assertTrue(item.get("role"))
            self.assertIn(item["role"],
                          {"design_tool", "design_system", "component_library",
                           "component_gallery", "inspiration", "curated_list",
                           "reverse_engineering_tool"})
            self.assertIsInstance(item.get("attributes") or {}, dict)

    def test_verify_catalog_is_clean(self):
        report = verify_catalog()
        self.assertTrue(report["found"])
        self.assertTrue(report["ok"], report)
        self.assertGreaterEqual(report["count"], 14)
        self.assertEqual(report["duplicate_slugs"], [])
        self.assertEqual(report["invalid_attribute_keys"], [])
        self.assertEqual(report["missing_url"], [])

    def test_resolve_magic_ui_matches_motion(self):
        matches = resolve_references("Build with magicui-level motion polish")
        slugs = {m.get("slug") for m in matches}
        self.assertIn("magic-ui", slugs)
        attrs = merge_profiles(matches)
        self.assertGreaterEqual(attrs.get("motion", 0), 0.8)

    def test_resolve_shadcn_style(self):
        matches = resolve_references("shadcn-style clean utility-first UI")
        slugs = {m.get("slug") for m in matches}
        self.assertIn("shadcn-ui", slugs)

    def test_reference_analyzer_knows_resources(self):
        analysis = extract_reference_intelligence("magic ui style motion primitives")
        self.assertTrue(
            any("magic" in h for h in analysis["hints"]),
            analysis["hints"],
        )
        self.assertGreaterEqual(analysis["traits"]["motion"], 0.8)

    def test_known_references_include_catalog_slugs(self):
        keys = {k for k in _KNOWN_REFERENCES}
        self.assertIn("shadcn-ui", keys)
        self.assertIn("magic-ui", keys)
        self.assertIn("aceternity-ui", keys)

    def test_benchmark_first_returns_design_resources(self):
        spec = {"project_name": "Orion Console",
                "industry": "saas",
                "description": "shadcn-style developer dashboard with magicui motion"}
        report = run_benchmark_first(spec, provider=None, live=False)
        ref_spec = report["reference_spec"]
        self.assertIn("design_resources", ref_spec)
        resource_spec = ref_spec["design_resources"]
        self.assertIsInstance(resource_spec, dict)
        matched = {str(m.get("slug")) for m in resource_spec.get("matched") or []}
        self.assertIn("shadcn-ui", matched)


if __name__ == "__main__":
    unittest.main()