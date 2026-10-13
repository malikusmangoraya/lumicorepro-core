"""Tests for the Reference Cloner (reverse-engineer a live reference website).

All network and browser access is patched out (FakeBrowser / canned HTML), so
the suite is deterministic and offline. The real backends are exercised
separately in the e2e suite.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence import reference_cloner as rc  # noqa: E402
from agent.intelligence import benchmark_first as bf  # noqa: E402
from agent.intelligence.design_resources import load_catalog  # noqa: E402


SAMPLE_HTML = """
<!doctype html><html><head>
<style>
  body { font-family: Inter, sans-serif; background: #0e1116; color: #e8e6e3; }
  .accent { color: #14b8a6; }
</style></head>
<body>
  <header><nav><a href="/">Home</a><a href="/fleet">Fleet</a></nav></header>
  <main>
    <h1>Curated performance cars</h1>
    <section><h2>Inventory</h2><img src="car.jpg" alt="car"></section>
    <section><h2>Provenance</h2><img src="vin.jpg" alt=""></section>
    <form><input type="email" name="email"></form>
    <button>Book a viewing</button>
  </main>
</body></html>
"""


class TestToolRegistry(unittest.TestCase):

    def test_three_tools_registered(self):
        expected = {"screenshot-to-code", "firecrawl", "single-file-cli"}
        self.assertTrue(expected.issubset(set(rc.REVERSE_ENGINEER_TOOLS)))

    def test_every_tool_has_repo_and_license(self):
        for slug, meta in rc.REVERSE_ENGINEER_TOOLS.items():
            self.assertTrue(meta.get("repo"), slug)
            self.assertTrue(meta.get("license"), slug)
            self.assertTrue(meta.get("capability"), slug)

    def test_catalog_registers_tools(self):
        catalog = load_catalog(refresh=True)
        by_slug = {r.get("slug"): r for r in catalog}
        for slug in rc.REVERSE_ENGINEER_TOOLS:
            self.assertIn(slug, by_slug, slug)
            self.assertEqual(by_slug[slug].get("role"), "reverse_engineering_tool")
            self.assertTrue(by_slug[slug].get("url"))


class TestStructureParsing(unittest.TestCase):

    def setUp(self):
        self.structure = rc._structure_from_html(SAMPLE_HTML)

    def test_counts_skeleton(self):
        self.assertGreaterEqual(self.structure["nav_links"], 2)
        self.assertEqual(self.structure["images"], 2)
        self.assertEqual(self.structure["image_alts"], 1)
        self.assertEqual(self.structure["forms"], 1)
        self.assertEqual(self.structure["inputs"], 1)
        self.assertGreaterEqual(self.structure["sections"], 2)

    def test_heading_order_preserved(self):
        self.assertEqual(
            self.structure["headings"][0], "Curated performance cars"
        )
        self.assertIn("Inventory", self.structure["headings"])
        self.assertIn("Provenance", self.structure["headings"])

    def test_detects_fonts_and_colors(self):
        self.assertIn("Inter", self.structure["fonts"])
        self.assertIn("#0e1116", self.structure["colors"])
        self.assertIn("#14b8a6", self.structure["colors"])

    def test_no_animation_libraries_in_static_html(self):
        self.assertEqual(self.structure["animation_libraries"], [])


class TestAttributeMapping(unittest.TestCase):

    def test_attributes_are_bounded_and_complete(self):
        attrs = rc.structure_to_attributes(
            rc._structure_from_html(SAMPLE_HTML)
        )
        for key, value in attrs.items():
            self.assertGreaterEqual(value, 0.0, key)
            self.assertLessEqual(value, 1.0, key)

    def test_dark_canvas_detected(self):
        attrs = rc.structure_to_attributes(
            rc._structure_from_html(SAMPLE_HTML)
        )
        self.assertGreater(attrs["dark_canvas"], 0.0)

    def test_motion_high_when_animation_library_present(self):
        structure = rc._structure_from_html(
            SAMPLE_HTML.replace("<body>", "<body><script src='gsap.js'></script>")
        )
        attrs = rc.structure_to_attributes(structure)
        self.assertGreaterEqual(attrs["motion"], 0.7)

    def test_deterministic(self):
        first = rc.structure_to_attributes(rc._structure_from_html(SAMPLE_HTML))
        second = rc.structure_to_attributes(rc._structure_from_html(SAMPLE_HTML))
        self.assertEqual(first, second)


class TestExtractStructure(unittest.TestCase):

    @mock.patch.object(rc, "_structure_from_browser", return_value=None)
    @mock.patch.object(rc, "_fetch_html", return_value=(SAMPLE_HTML, None))
    def test_static_backend_is_heuristic(self, _fetch, _browser):
        reading = rc.extract_structure("https://example.com")
        self.assertEqual(reading["backend"], "static-http")
        self.assertEqual(reading["status"], "heuristic")
        self.assertTrue(reading["structure"]["headings"])

    @mock.patch.object(rc, "_structure_from_browser")
    def test_browser_backend_is_measured(self, browser):
        browser.return_value = {"html_length": 5000, "headings": ["Hi"], "images": 2}
        reading = rc.extract_structure("https://example.com")
        self.assertEqual(reading["backend"], "agent-browser")
        self.assertEqual(reading["status"], "measured")

    @mock.patch.object(rc, "_structure_from_browser", return_value=None)
    @mock.patch.object(rc, "_fetch_html", return_value=(None, "fetch_failed"))
    def test_unreadable_is_unavailable(self, _fetch, _browser):
        reading = rc.extract_structure("https://example.com")
        self.assertEqual(reading["status"], "unavailable")
        self.assertEqual(reading["error"], "fetch_failed")


class TestCloneReference(unittest.TestCase):

    @mock.patch.object(rc, "_structure_from_browser", return_value=None)
    @mock.patch.object(rc, "_fetch_html", return_value=(SAMPLE_HTML, None))
    def test_clone_derives_attributes(self, _fetch, _browser):
        clone = rc.clone_reference("https://cars.example.com")
        self.assertEqual(clone["status"], "heuristic")
        self.assertTrue(clone["attributes"])
        self.assertEqual(clone["constraints"]["copy_style"], "do_not_copy")
        self.assertIn("warmth", clone["unmeasured"])

    @mock.patch.object(rc, "_structure_from_browser", return_value=None)
    @mock.patch.object(rc, "_fetch_html", return_value=(None, "fetch_failed"))
    def test_clone_unavailable_has_no_attributes(self, _fetch, _browser):
        clone = rc.clone_reference("https://offline.example.com")
        self.assertEqual(clone["status"], "unavailable")
        self.assertEqual(clone["attributes"], {})
        self.assertEqual(clone["unmeasured"], [])


class TestBenchmarkFirstWiring(unittest.TestCase):

    def test_no_url_yields_not_requested(self):
        spec = {"project_name": "Orion", "industry": "saas", "description": "calm"}
        report = bf.run_benchmark_first(spec, provider=None, live=False)
        self.assertEqual(report["reference_clone"]["status"], "not_requested")

    def test_reference_url_merges_clone(self):
        clone = {
            "url": "https://cars.example.com",
            "host": "cars.example.com",
            "status": "heuristic",
            "attributes": {"dark_canvas": 1.0, "cta_focus": 0.9},
            "constraints": {"copy_style": "do_not_copy"},
        }
        spec = {
            "project_name": "Apex", "industry": "automotive",
            "description": "performance cars", "reference_url": "https://cars.example.com",
        }
        with mock.patch.object(bf, "clone_reference", return_value=clone):
            report = bf.run_benchmark_first(spec, provider=None, live=False)
        self.assertEqual(report["reference_clone"]["status"], "measured")
        self.assertTrue(report["source"].endswith("+reference_clone"))
        self.assertIn("reference_clone", report["reference_spec"])
        traits = report["reference_spec"]["reference_intelligence"]["traits"]
        self.assertEqual(traits["dark_canvas"], 1.0)

    def test_failed_clone_is_non_blocking(self):
        spec = {
            "project_name": "Apex", "industry": "automotive",
            "description": "cars", "reference_url": "https://cars.example.com",
        }
        with mock.patch.object(bf, "clone_reference", side_effect=RuntimeError("boom")):
            report = bf.run_benchmark_first(spec, provider=None, live=False)
        self.assertEqual(report["reference_clone"]["status"], "unavailable")
        self.assertTrue(report["reference_spec"]["reference_intelligence"]["traits"])


if __name__ == "__main__":
    unittest.main()
