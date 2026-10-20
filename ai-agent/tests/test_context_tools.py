"""Tests for utils.context_tools — Headroom compression + reference mining (no network)."""
import sys
import time
from unittest import mock

from utils import context_tools as ct


def test_context_lint_truncates_and_cleans():
    dirty = "a\n\n\n\n\nb   \nc" + "x" * 500
    out = ct.context_lint(dirty, max_chars=150)
    assert len(out) <= 150
    assert out.endswith("[context truncated]")
    plain = ct.context_lint("one\n\n\n\n\ntwo\n\n\n\nthree")
    assert "two" in plain and "\n\n\n" not in plain


def test_compress_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("HEADROOM_ENABLED", "0")
    monkeypatch.delenv("HEADROOM_ENABLED_VERSION", raising=False)
    text = "word " * 600
    assert ct.compress_context(text) == ct.context_lint(text)


def test_compress_gains_when_enabled():
    call = {"sent": None}

    class _Resp:
        tokens_saved = 42
        compression_ratio = 0.4
        messages = [{"role": "user", "content": "COMPRESSED OUTPUT"}]

    def fake_compress(messages, **kw):
        call["sent"] = messages[0]["content"]
        return _Resp()

    with mock.patch.dict("os.environ", {"HEADROOM_ENABLED": "1"}), \
         mock.patch.dict("sys.modules", {"headroom": mock.MagicMock(compress=fake_compress)}):
        out = ct.compress_context("LONG TOOL DUMP " * 200)
    assert out == "COMPRESSED OUTPUT"
    assert call["sent"].startswith("LONG TOOL DUMP")


def test_compress_survives_failure():
    with mock.patch.dict("os.environ", {"HEADROOM_ENABLED": "1"}), \
         mock.patch.dict("sys.modules", {"headroom": None}):
        text = "stable " * 300
        assert "stable" in ct.compress_context(text)


def test_reference_markdown_urllib_fallback(tmp_path):
    html = ""
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return html.encode()

    html = "<html><script>noise()</script><style>.x{}</style><body><h1>Design Reference</h1><p>Hero layout rules</p></body></html>"
    req = urllib_get = _Resp

    def catcher(u, timeout=0):
        return req()

    with mock.patch.object(ct.urllib.request, "urlopen", catcher), \
         mock.patch("utils.context_tools._CACHE_DIR", tmp_path):
        out = ct.reference_markdown("https://example.test/page")
    assert out["status"] == "ok"
    assert out["source"] == "urllib-fallback"
    assert "Design Reference" in out["markdown"]
    assert "noise()" not in out["markdown"] and ".x{}" not in out["markdown"]


def test_reference_markdown_rejects_bad_url(tmp_path):
    with mock.patch("utils.context_tools._CACHE_DIR", tmp_path):
        assert ct.reference_markdown("nowhere")["status"] == "failed"


def test_reference_markdown_caches(tmp_path):
    body = "<html><body><h1>Cached One</h1></body></html>"

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return body.encode()

    with mock.patch.object(ct.urllib.request, "urlopen", lambda u, timeout=0: _Resp()), \
         mock.patch("utils.context_tools._CACHE_DIR", tmp_path):
        first = ct.reference_markdown("https://cache.test/a")
        second = ct.reference_markdown("https://cache.test/a")
    assert first["status"] == "ok" and second.get("cached") is True
    hits = list(tmp_path.glob("*.json"))
    assert len(hits) == 1


def test_reference_crawl4ai_path(tmp_path):
    import asyncio
    md = "## Hero guidance\nfit markdown body"

    class _MD:
        fit_markdown = md
        raw_markdown = md

    class _Res:
        markdown = _MD()
        metadata = {"title": "Ref"}

    class _Crawler:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def arun(self, url=None, config=None):
            return _Res()

    fake_mod = mock.MagicMock()
    fake_mod.AsyncWebCrawler = _Crawler
    fake_mod.CrawlerRunConfig = lambda **kw: object()
    fake_mod.CacheMode = mock.MagicMock(BYPASS=1)
    with mock.patch.dict(sys.modules, {"crawl4ai": fake_mod}), \
         mock.patch("utils.context_tools._CACHE_DIR", tmp_path):
        out = ct.reference_markdown("https://ref.test/guide", focus="hero")
    assert out["status"] == "ok"
    assert out["source"] == "crawl4ai"
    assert "fit markdown body" in out["markdown"]
