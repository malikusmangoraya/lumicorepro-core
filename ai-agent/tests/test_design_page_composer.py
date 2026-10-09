"""Tests for real tokenized layout composition from design DNA."""

import copy
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.layout_recipes import get_layout_catalog
from agent.intelligence.page_composer import compose_project_pages
from agent.project_builder import ProjectBuilder


def _design_dna(hero="data_metrics", navigation="utility_dashboard"):
    return {
        "version": 1,
        "project": "claim-desk",
        "niche": "insurance",
        "audience": ["claims adjusters"],
        "tone": "clear and trustworthy",
        "tokens": {
            "colors": {
                "canvas": "#ffffff",
                "surface": "#f8fafc",
                "primary": "#1f2937",
                "accent": "#b45309",
                "text": "#111827",
                "text_on_primary": "#ffffff",
                "muted": "#64748b",
                "border": "#e2e8f0",
            },
            "typography": {"display": "Georgia", "sans": "system-ui", "mono": "monospace"},
            "spacing": {"unit": "4px", "scale": [4, 8, 12, 16, 24, 32, 48, 64, 96]},
            "radius": {"card": "8px", "button": "4px"},
            "shadows": {"card": "0 1px 3px rgba(0,0,0,.08)"},
            "motion": {"intensity": "subtle", "reduced_motion": "disable_nonessential"},
        },
        "layout": {
            "navigation_pattern": navigation,
            "hero_archetype": hero,
            "pages": {
                "Home": {
                    "section_order": ["hero", "claims_intake", "claims_queue", "contact_cta"],
                },
            },
            "grid_system": "asymmetric_12_column",
            "card_style": "bordered",
            "footer_type": "sitemap_columns",
            "density": "spacious",
        },
        "fingerprint": {"value": "test-fingerprint"},
    }


class TestDesignPageComposer(unittest.TestCase):
    def test_layout_catalog_has_required_archetype_and_section_counts(self):
        catalog = get_layout_catalog()

        self.assertGreaterEqual(len(catalog["heroes"]), 12)
        self.assertGreaterEqual(len(catalog["navigation"]), 8)
        self.assertGreaterEqual(len(catalog["sections"]), 10)

    def test_composition_writes_tokenized_home_and_niche_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            app = project / "frontend" / "src" / "App.jsx"
            app.parent.mkdir(parents=True)
            app.write_text(
                "import React from 'react';\n"
                "import { Routes, Route } from 'react-router-dom';\n"
                "export default function App() { return <Routes><Route path=\"/\" element={<main />} /></Routes>; }\n",
                encoding="utf-8",
            )

            result = compose_project_pages(
                project,
                _design_dna(),
                {
                    "project_name": "claim-desk",
                    "industry": "insurance",
                    "original_prompt": "Insurance claim intake for claims adjusters.",
                    "tagline": "Review claims with clarity",
                },
            )

            home = (project / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
            claims = (project / "frontend" / "src" / "pages" / "Claims.jsx").read_text(encoding="utf-8")
            stylesheet = (project / "frontend" / "src" / "design-system.css").read_text(encoding="utf-8")
            app_source = app.read_text(encoding="utf-8")

        self.assertTrue(result["ok"])
        self.assertEqual(result["structure"]["hero"], "data_metrics")
        self.assertEqual(result["structure"]["navigation"], "utility_dashboard")
        self.assertIn("claims_queue", result["structure"]["home_sections"])
        self.assertIn("Claims", claims)
        self.assertIn("/claims", app_source)
        self.assertIn("--ds-color-primary", stylesheet)
        self.assertNotRegex(home, re.compile(r"#[0-9a-fA-F]{3,8}|\b\d+px\b"))

    def test_hero_navigation_and_section_order_change_rendered_markup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_dir = Path(temp_dir) / "first"
            second_dir = Path(temp_dir) / "second"
            first = compose_project_pages(first_dir, _design_dna(), {"industry": "insurance"})
            other_dna = copy.deepcopy(_design_dna("editorial_image", "editorial_masthead"))
            other_dna["layout"]["pages"]["Home"]["section_order"] = [
                "hero", "claims_queue", "claims_intake", "contact_cta"
            ]
            second = compose_project_pages(second_dir, other_dna, {"industry": "insurance"})

            first_home = (first_dir / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
            second_home = (second_dir / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")

        self.assertTrue(first["ok"] and second["ok"])
        self.assertNotEqual(first_home, second_home)
        self.assertLess(first_home.index("claims_intake"), first_home.index("claims_queue"))
        self.assertLess(second_home.index("claims_queue"), second_home.index("claims_intake"))

    def test_centered_brand_navigation_keeps_balanced_anchor_markup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dna = _design_dna("editorial_image", "centered_brand")
            dna["layout"]["pages"]["Home"]["section_order"] = [
                "hero", "claims_intake", "claims_queue", "coverage_review", "contact_cta"
            ]
            compose_project_pages(Path(temp_dir), dna, {"industry": "insurance"})
            home = (Path(temp_dir) / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
            header = home.split("</header>", 1)[0]

        nav_groups = re.findall(r'<div className="ds-nav-links">(.*?)</div>', header)
        self.assertGreaterEqual(len(nav_groups), 2)
        self.assertTrue(all(group.count("<a ") == group.count("</a>") for group in nav_groups))

    def test_workspace_sidebar_navigation_uses_a_real_sidebar_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dna = _design_dna("dashboard_preview", "workspace_sidebar")
            compose_project_pages(Path(temp_dir), dna, {"industry": "insurance"})
            home = (Path(temp_dir) / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
            stylesheet = (Path(temp_dir) / "frontend" / "src" / "design-system.css").read_text(encoding="utf-8")

        self.assertIn('<aside className="ds-sidebar"', home)
        self.assertIn('.ds-site[data-navigation="workspace_sidebar"]', stylesheet)

    def test_project_builder_applies_design_dna_only_when_supplied(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            with patch("agent.project_builder.GENERATED_PROJECTS_DIR", output_root):
                builder = ProjectBuilder()
                builder._resolve_template_path = lambda _template: output_root / "missing-template"
                project_dir = Path(builder.build_project({
                    "project_name": "claim-desk",
                    "template": {"file_path": "missing-template"},
                    "features": [],
                    "design_dna": _design_dna(),
                    "spec": {
                        "project_name": "claim-desk",
                        "industry": "insurance",
                        "original_prompt": "Claims intake for adjusters.",
                    },
                }))

                home = (project_dir / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")

                self.assertIn('data-hero="data_metrics"', home)
                self.assertTrue((project_dir / "frontend" / "src" / "design-system.css").exists())

    def test_untrusted_brief_copy_is_escaped_before_writing_jsx(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            compose_project_pages(
                project,
                _design_dna(),
                {"industry": "insurance", "tagline": "<script>{alert(1)}</script>"},
            )
            home = (project / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")

        self.assertNotIn("<script>", home)
        self.assertNotIn("{alert(1)}", home)
        self.assertIn("&#123;alert(1)&#125;", home)


if __name__ == "__main__":
    unittest.main()