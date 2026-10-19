"""Layout variation engine tests — determinism, anti-repeat, sweep behaviour."""
import sys
from pathlib import Path

import pytest

AI_AGENT = Path(__file__).resolve().parents[1]
if str(AI_AGENT) not in sys.path:
    sys.path.insert(0, str(AI_AGENT))


import agent.layout_variation as lv


@pytest.fixture(autouse=True)
def reset_ring():
    lv._LAST.clear()
    yield
    lv._LAST.clear()


def test_deterministic_for_same_slug():
    a = lv.choose_layout_variation("build-090")
    b = lv.choose_layout_variation("build-090")
    assert a["accent"] == b["accent"]
    assert a["surface"] == b["surface"]
    assert a["order"] == b["order"]


def test_profile_axes_in_bounds():
    prof = lv.choose_layout_variation("anything")
    assert prof["accent"] in lv.ACCENT_PALETTES
    assert prof["surface"] in lv.SURFACE_FAMILIES
    assert len(prof["order"]) == 3
    assert sorted(prof["order"]) == ["faq", "pricing", "testimonials"]
    assert set(prof["gradient"]) == {"from", "via", "to"}


def test_anti_repeat_rotates_between_consecutive_projects():
    a = lv.choose_layout_variation("proj-a", avoid_previous=True)
    b = lv.choose_layout_variation("proj-b", avoid_previous=True)
    assert a["accent"] != b["accent"]
    assert a["surface"] != b["surface"]
    assert a["order"] != b["order"]


def test_sweep_swaps_accent_surface_gradient_order(tmp_path):
    src = tmp_path / "src"
    (src / "pages").mkdir(parents=True)
    (src / "pages" / "Home.jsx").write_text(
        "export default function Home() {\n"
        "  return (\n"
        "    <div className=\"min-h-screen bg-slate-950 text-slate-100\">\n"
        "      <span className=\"bg-cyan-500 text-cyan-400 border-cyan-500/30 border-cyan-500/20\">x</span>\n"
        "      <h1 className=\"bg-gradient-to-r from-cyan-400 via-teal-300 to-violet-500\">Hero</h1>\n"
        "    </div>\n"
        "  );\n"
        "}\n"
    )
    profile = {
        "accent": "violet",
        "surface": "zinc",
        "order": ["pricing", "testimonials", "faq"],
        "gradient": {"from": "violet-300", "via": "fuchsia-400", "to": "rose-500"},
    }
    home = src / "pages" / "Home.jsx"
    report = lv.apply_layout_variation(str(src), "proj-x", avoid_previous=False, profile=profile)
    assert report["applied"] is True
    body = home.read_text(encoding="utf-8")
    assert "cyan" not in body
    assert "slate" not in body
    assert "violet-500" in body
    assert "from-violet-300 via-fuchsia-400 to-rose-500" in body

    # Section order swap: canonical order missing (already permuted input text)
    # so append canonical trio and re-sweep to assert permutation.
    (src / "pages" / "Home2.jsx").rename(src / "pages" / "Home.jsx") if False else None
    (src / "pages" / "Trio.jsx").write_text(
        "      {/* Testimonials Section */}\n"
        "        <TestimonialGrid />\n\n"
        "      {/* Pricing Section */}\n"
        "        <PricingTable />\n\n"
        "      {/* FAQ Section */}\n"
        "        <FAQAccordion />\n"
    )
    report2 = lv.apply_layout_variation(str(src), "proj-x", avoid_previous=False, profile=profile)
    trio = (src / "pages" / "Trio.jsx").read_text(encoding="utf-8")
    assert report2["order_swaps"] == 0  # only Home.jsx is considered
    (src / "pages" / "Home.jsx").write_text(
        (src / "pages" / "Trio.jsx").read_text(encoding="utf-8")
    )
    report3 = lv.apply_layout_variation(str(src), "proj-x", avoid_previous=False, profile=profile)
    assert report3["order_swaps"] >= 1
    reordered = (src / "pages" / "Home.jsx").read_text(encoding="utf-8")
    assert reordered.index("PricingTable") < reordered.index("TestimonialGrid")
    assert reordered.index("TestimonialGrid") < reordered.index("FAQAccordion")


def test_sweep_missing_dir_is_safe(tmp_path):
    report = lv.apply_layout_variation(tmp_path / "nope", "proj")
    assert report == {"applied": False, "reason": "frontend dir missing"}
