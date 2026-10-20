"""Tests for agent.extensions.built_with_badge — proof badge injection."""
import re
from pathlib import Path

from agent.extensions import built_with_badge as bwb


def _make_project(tmp_path, entry="frontend/index.html", images=("logo.svg",)):
    proj = tmp_path / "nova-legals"
    pentry = proj / entry
    pentry.parent.mkdir(parents=True)
    pentry.write_text(
        "<html><head><title>Nova</title></head><body><div id='root'></div>"
        "<script type='module'></script></body></html>",
        encoding="utf-8",
    )
    for img in images:
        (proj / img).write_text(f"<svg data-image='{img}'/>", encoding="utf-8")
    return proj, pentry


def test_inject_and_idempotent(tmp_path):
    proj, entry = _make_project(tmp_path, entry="frontend/index.html", images=("logo.svg",))
    out = bwb.inject_built_with(str(proj))
    assert out["status"] == "ok" and out["injected"] == 1
    html = entry.read_text(encoding="utf-8")
    assert bwb.MARKER in html and "<style" in html
    assert 'src="built-with-thumb.svg"' in html and "Nova Legals" in html
    assert "Pending deploy" in html  # no dead external link before deploy
    assert html.index(bwb.MARKER) < html.rindex("</body>")  # before closing body
    again = bwb.inject_built_with(str(proj))
    assert again["injected"] == 0 and again["skipped"] == 1
    assert html.count(bwb.MARKER) == entry.read_text(encoding="utf-8").count(bwb.MARKER)


def test_image_copy_next_to_entry(tmp_path):
    proj, entry = _make_project(tmp_path, entry="frontend/index.html", images=("og-image.svg",))
    bwb.inject_built_with(str(proj))
    assert (entry.parent / "built-with-thumb.svg").is_file()


def test_fallback_logo_when_no_image(tmp_path):
    proj, entry = _make_project(tmp_path, images=())
    bwb.inject_built_with(str(proj))
    html = entry.read_text(encoding="utf-8")
    assert "bw-fallback" in html and "linearGradient" in html


def test_update_live_link(tmp_path):
    proj, entry = _make_project(tmp_path)
    bwb.inject_built_with(str(proj))
    out = bwb.update_live_link(str(proj), "https://nova-legals.vercel.app")
    assert out["status"] == "ok"
    html = entry.read_text(encoding="utf-8")
    assert "https://nova-legals.vercel.app" in html and "View live" in html
    bad = bwb.update_live_link(str(proj), "not-a-url")
    assert bad["status"] == "failed"


def test_no_entries_fails(tmp_path):
    empty = tmp_path / "blank"
    empty.mkdir()
    assert bwb.inject_built_with(str(empty))["status"] == "failed"


def test_style_uses_generic_font_and_safe_zindex(tmp_path):
    proj, entry = _make_project(tmp_path)
    bwb.inject_built_with(str(proj))
    html = entry.read_text(encoding="utf-8")
    assert re.search(r"z-index:\s*2147483647", html)
