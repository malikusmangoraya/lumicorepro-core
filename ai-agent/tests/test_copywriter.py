"""
Tests for CopyWriter — industry-specific persuasive copy for generated sites.
"""
import sys
from pathlib import Path

from agent.copywriter import (
    COPY_BANK,
    copy_for,
    resolve_industry,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCopyWriter:
    def test_resolve_known_industry(self):
        assert resolve_industry("RESTAURANT") == "restaurant"
        assert resolve_industry("bakery") == "restaurant"
        assert resolve_industry("real estate") == "realestate"

    def test_resolve_unknown_industry_falls_back(self):
        assert resolve_industry("quantum-spaceport") == "general"

    def test_resolve_none_falls_back(self):
        assert resolve_industry(None) == "general"

    def test_copy_for_returns_industry_copy(self):
        copy = copy_for({"spec": {"industry": "fitness"}, "project_name": "gymx"})
        assert copy["industry"] == "fitness"
        assert copy["headline"]

    def test_copy_for_general_fallback(self):
        copy = copy_for({"spec": {"industry": "unknown"}, "project_name": "site"})
        assert copy["industry"] == "general"

    def test_copy_block_has_all_required_keys(self):
        for key, block in COPY_BANK.items():
            for field in ("tagline", "headline", "subheadline", "cta",
                          "meta_description", "og_description", "keywords",
                          "testimonial", "value_props"):
                assert field in block, f"{key} missing {field}"
            assert len(block["value_props"]) >= 3

    def test_deck_integrates_into_seo(self):
        from agent.project_builder import ProjectBuilder

        plan = {
            "project_name": "spice-garden",
            "spec": {"industry": "restaurant", "website_type": "restaurant", "features": []},
        }
        copy = copy_for(plan)
        assert copy["meta_description"]
        assert "Book a Table" in copy["cta"]
        assert "restaurant" in copy["industry"]

    def test_no_placeholder_text_in_meta(self):
        general = COPY_BANK["general"]
        for field in ("meta_description", "og_description", "headline"):
            assert "standard.\"" not in general[field]
            assert "modern UI" not in general[field]