"""Tests for the asset_wire extension: remote image localization + generated art wiring."""
import re

import pytest

from agent.extensions import asset_wire


HOMEPAGE = """import React from 'react';
export default function Home() {
  return (
    <section>
      <img
        src="https://images.unsplash.com/photo-1559526324-4b87b5e36e44/?auto=format&fit=crop&w=1200&q=80"
        alt="Product overview"
        loading="eager"
      />
      <img
        src="https://images.unsplash.com/photo-1509062522246-3755977927d7/?auto=format&fit=crop&w=1200&q=80"
        alt=""
        loading="lazy"
      />
      <img src={`https://images.unsplash.com/photo-${id}?w=100`} alt="" />
    </section>
  );
}
"""

_INDEX = """<!doctype html>
<html>
  <head><title>Test</title></head>
  <body><div id="root"></div></body>
</html>
"""


@pytest.fixture()
def project(tmp_path):
    (tmp_path / "frontend" / "public" / "images" / "generated").mkdir(parents=True)
    (tmp_path / "frontend" / "src" / "pages").mkdir(parents=True)
    (tmp_path / "frontend" / "index.html").write_text(_INDEX, encoding="utf-8")
    (tmp_path / "frontend" / "src" / "pages" / "Home.jsx").write_text(HOMEPAGE, encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def no_webp(monkeypatch):
    """Deterministic extension in tests: PIL transcode checked separately."""
    monkeypatch.setattr(asset_wire, "_to_webp", lambda data: None)


@pytest.fixture()
def fake_download(monkeypatch):
    """Patch the module's download entrypoint: counts calls, serves fake JPEGs."""
    opened: list = []

    def _download(url, timeout=20):
        opened.append(url)
        return b"\xff\xd8" + b"j" * 3000

    monkeypatch.setattr(asset_wire, "_download", _download)
    return opened


def test_localize_downloads_and_rewrites(project, fake_download):
    out = asset_wire.localize_images(str(project))
    assert out["status"] == "ok"
    assert out["downloaded"] == 2  # template literal skipped
    text = (project / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
    assert 'src="https://images.unsplash.com' not in text  # regular refs replaced
    assert re.search(r'src="/images/local/[^"]+\.jpg"', text)
    assert "${id}" in text  # untouched — inside backticks, not a real request
    assert len(list((project / "frontend" / "public" / "images" / "local").glob("*.jpg"))) == 2


def test_localize_cache_hits_after_first_run(project, fake_download):
    first = asset_wire.localize_images(str(project))
    assert first["downloaded"] == 2
    calls_after_first_run = len(fake_download)
    # a new file references the same URLs — cache must serve without network
    (project / "frontend" / "src" / "pages" / "Team.jsx").write_text(
        HOMEPAGE, encoding="utf-8")
    second = asset_wire.localize_images(str(project))
    assert second["downloaded"] == 0
    assert second["rewritten_refs"] == 2
    assert len(fake_download) == calls_after_first_run  # no re-download


def test_localize_failures_reported_without_rewrite(project, fake_download, monkeypatch):
    def fail(url, timeout=20):
        raise RuntimeError("HTTP Error 404")

    monkeypatch.setattr(asset_wire, "_download", fail)
    out = asset_wire.localize_images(str(project))
    assert out["status"] == "partial"
    assert out["downloaded"] == 0
    assert len(out["failed"]) == 2
    text = (project / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
    assert 'src="https://images.unsplash.com' in text  # refs untouched when download fails


def test_to_webp_real_image_smaller(monkeypatch):
    pytest.importorskip("PIL")
    monkeypatch.undo()  # restore the real _to_webp (unpatch the autouse stub)
    from agent.extensions.asset_wire import _to_webp as real_to_webp
    from PIL import Image
    import io

    src = io.BytesIO()
    Image.new("RGB", (60, 60), (200, 60, 60)).save(src, format="PNG")
    webp = real_to_webp(src.getvalue())
    assert webp is not None and webp[:4] == b"RIFF" and len(webp) < len(src.getvalue())
    assert real_to_webp(b"junkjunkjunk") is None  # corrupt input → keep original


def test_wire_og_and_hero(project):
    gen = project / "frontend" / "public" / "images" / "generated"
    (gen / "og-image.jpg").write_bytes(b"\xff\xd8" + b"o" * 2000)
    (gen / "hero.jpg").write_bytes(b"\xff\xd8" + b"h" * 2000)
    out = asset_wire.wire_generated(str(project))
    assert out["art"]["og"] == "/images/generated/og-image.jpg"
    assert out["art"]["hero"] == "/images/generated/hero.jpg"
    html = (project / "frontend" / "index.html").read_text(encoding="utf-8")
    assert 'property="og:image" content="/images/generated/og-image.jpg"' in html
    page = (project / "frontend" / "src" / "pages" / "Home.jsx").read_text(encoding="utf-8")
    assert 'src="/images/generated/hero.jpg"' in page  # eager hero replaced


def test_wire_is_idempotent(project):
    gen = project / "frontend" / "public" / "images" / "generated"
    (gen / "og-image.jpg").write_bytes(b"\xff\xd8" + b"o" * 2000)
    (gen / "hero.jpg").write_bytes(b"\xff\xd8" + b"h" * 2000)
    asset_wire.wire_generated(str(project))
    second = asset_wire.wire_generated(str(project))
    assert second["wired"] == []  # already wired


def test_wire_hero_requires_eager(project):
    page = project / "frontend" / "src" / "pages" / "Home.jsx"
    page.write_text(HOMEPAGE.replace('loading="eager"', 'loading="lazy"'), encoding="utf-8")
    gen = project / "frontend" / "public" / "images" / "generated"
    (gen / "hero.jpg").write_bytes(b"\xff\xd8" + b"h" * 2000)
    out = asset_wire.wire_generated(str(project))
    assert not any("hero=" in a for a in out["wired"])


def test_scope_skips_backend(project, fake_download):
    backend = project / "backend" / "scripts"
    backend.mkdir(parents=True)
    (backend / "seedFull.js").write_text(
        "const a='https://images.unsplash.com/photo-xxxx/?w=100';", encoding="utf-8")
    out = asset_wire.localize_images(str(project))
    assert not any("photo-xxxx" in u for u in fake_download)


def test_one_shot_wire_assets(project, fake_download):
    (project / "frontend" / "public" / "images" / "generated" / "og-image.jpg").write_bytes(
        b"\xff\xd8" + b"o" * 2000)
    out = asset_wire.wire_assets(str(project))
    assert {"localize", "wire"} <= set(out)
    assert out["localize"]["downloaded"] == 2
    assert out["status"] == "ok"
