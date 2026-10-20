"""Tests for agent.asset_gen + agent.extensions.store_gate (network mocked)."""
import json
from pathlib import Path
from unittest import mock

import pytest

from agent import asset_gen
from agent.extensions import store_gate


def _fake_fetch_ok(path=None, payload=b"\xff\xd8" + b"x" * 4000):
    def _fetch(url, out):
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(payload)
        return {"status": "ok", "file": str(out), "bytes": len(payload)}
    return _fetch


@pytest.fixture()
def project(tmp_path):
    f = tmp_path / "frontend"
    (f / "public").mkdir(parents=True)
    (f / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (f / "index.html").write_text(
        "<html><head><title>T</title></head><body><img src='a.jpg'><img src='b.jpg' alt='x'></body></html>",
        encoding="utf-8")
    (f / "package.json").write_text(json.dumps({"name": "demo", "version": "1.0.0"}), encoding="utf-8")
    return tmp_path


def test_image_url_is_deterministic_and_keyless():
    u1 = asset_gen.image_url("hero", 1200, 630, seed=7)
    u2 = asset_gen.image_url("hero", 1200, 630, seed=7)
    assert u1 == u2
    assert "nologo=true" in u1 and "?width=1200&height=630" in u1


def test_generate_image_writes_jpeg(tmp_path):
    with mock.patch.object(asset_gen, "_fetch", _fake_fetch_ok()):
        out = asset_gen.generate_image("brand hero image", str(tmp_path / "x.jpg"))
    assert out["status"] == "ok"


def test_generate_image_rejects_short_prompt(tmp_path):
    out = asset_gen.generate_image("hi", str(tmp_path / "x.jpg"))
    assert out["status"] == "failed"


def test_gen_project_images_skips_existing(project):
    (project / "frontend" / "public" / "images" / "generated").mkdir(parents=True)
    (project / "frontend" / "public" / "images" / "generated" / "og-image.jpg").write_bytes(b"real")
    with mock.patch.object(asset_gen, "_fetch", _fake_fetch_ok()) as calls:  # never called for og
        out = asset_gen.gen_project_images(str(project))
    og = next(r for r in out["results"] if r["target"] == "og-image.jpg")
    assert og["status"] == "skipped"
    assert (project / "frontend" / "public" / "images" / "generated" / "og-image.jpg").read_bytes() == b"real"


def test_gen_project_images_generates_missing(project):
    with mock.patch.object(asset_gen, "_fetch", _fake_fetch_ok()) as calls:
        out = asset_gen.gen_project_images(str(project))
    assert out["generated"] == 2
    for name in ("og-image.jpg", "hero.jpg"):
        assert (project / "frontend" / "public" / "images" / "generated" / name).exists()


def test_store_gate_scores_incomplete_project(project):
    out = store_gate.run_store_gate(str(project), apply_fixes=False)
    assert out["score"] < 90
    assert out["items"]["readme"]["ok"] is False
    assert out["items"]["img_alt"]["missing_alt"] == 1


def test_store_gate_autofix_completes_project(project):
    out = store_gate.run_store_gate(str(project), base_url="https://demo.vercel.app", apply_fixes=True)
    assert (project / "LICENSE.md").exists()
    assert "MIT" in (project / "LICENSE.md").read_text(encoding="utf-8")
    assert (project / "frontend" / "public" / "robots.txt").exists()
    assert (project / "frontend" / "public" / "sitemap.xml").exists()
    assert "demo.vercel.app" in (project / "frontend" / "public" / "sitemap.xml").read_text(encoding="utf-8")
    html = (project / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "og:title" in html
    pkg = json.loads((project / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert pkg["license"] == "MIT" and pkg["description"]
    assert out["score"] >= 90


def test_store_gate_never_touches_real_artwork(project):
    (project / "frontend" / "public" / "hero.jpg").write_bytes(b"artist work")
    store_gate.run_store_gate(str(project), apply_fixes=True)
    assert (project / "frontend" / "public" / "hero.jpg").read_bytes() == b"artist work"


def test_store_gate_missing_dir_fails(tmp_path):
    out = store_gate.run_store_gate(str(tmp_path / "nope"))
    assert out["status"] == "failed"
