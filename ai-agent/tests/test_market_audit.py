"""Tests for agent.market_audit - global-market readiness scoring."""
import json
from pathlib import Path

from agent import market_audit as ma


def _runner(results):
    def run(cmd, cwd=None, *a, **kw):
        # cmd = [node, <helper path>, <url>]; key on the helper name.
        key = Path(cmd[1]).name if cmd and len(cmd) > 1 else ""
        data = results.get(key) or results.get("*") or {"status": "failed", "message": "unexpected"}
        return (0, json.dumps(data), "")
    return run


def _good_payload():
    dom = {
        "title": "BlogForge - AI Blog Generator for International Teams" + "x" * 10,
        "meta_description": "d" * 80,
        "canonical": True,
        "og": {"title": True, "image": True},
        "twitter_card": True,
        "lang": "en",
        "dir": None,
        "hreflangs": 2,
        "viewport": True,
        "jsonld_types": ["WebPage", "Organization"],
        "heading_jumps": 0,
        "cta_above_fold": 2,
        "images_missing_alt": 0,
        "unlabeled_inputs": 0,
        "currency": {"symbols": "present", "switcher": True},
        "jsonld_currency": "USD",
        "legal": {"privacy": True, "terms": True, "refund": True, "gdpr_cookies": True},
        "placeholder_copy": False,
        "h1_count": 1,
    }
    metrics = {"status": "ok", "http_status": 200, "lcp": 1200, "cls": 0.02, "ttfb": 400,
               "bytes": 150000, "resource_count": 20, "console_errors": 0, "page_errors": 0}
    return {
        "status": "ok",
        "url": "https://x.test",
        "desktop": metrics,
        "mobile": dict(metrics, lcp=1800),
        "dom": dom,
        "endpoint_tests": {"robots_txt": True, "sitemap_xml": True},
    }


def test_market_audit_scores_perfect_page():
    runner = _runner({"market_audit.cjs": _good_payload()})
    out = ma.market_audit("https://x.test", runner=runner)
    assert out["status"] == "ok"
    assert out["grade"] in ("STANDARD", "PREMIUM", "SIGNATURE")
    assert out["overall"] >= 80
    assert out["scores"]["performance"] >= 100 - 5  # mobile lcp 1800 is within limits


def test_market_audit_flags_broken_market_readiness():
    payload = _good_payload()
    payload["desktop"]["lcp"] = 4000
    payload["mobile"]["lcp"] = 4200
    payload["dom"].update({
        "lang": None, "hreflangs": 0, "placeholder_copy": True,
        "currency": {"symbols": "none", "switcher": False},
        "legal": {"privacy": False, "terms": False, "refund": False, "gdpr_cookies": False},
        "cta_above_fold": 0, "unlabeled_inputs": 4, "images_missing_alt": 9,
        "canonical": False, "og": {"title": False, "image": False}, "twitter_card": False,
        "jsonld_types": [], "heading_jumps": 3, "h1_count": 0,
    })
    payload["endpoint_tests"] = {"robots_txt": False, "sitemap_xml": False}
    runner = _runner({"market_audit.cjs": payload})
    out = ma.market_audit("https://x.test", runner=runner)
    assert out["status"] == "warn"
    assert out["overall"] < 80
    assert out["grade"] == "NEEDS_WORK"
    assert out["scores"]["legal"] == 0
    assert any(c["check"] == "legal_privacy" and c["status"] == "fail" for c in out["checks"])


def test_market_audit_reports_playwright_missing():
    runner = _runner({"*": {"status": "skipped", "message": "playwright not installed"}})
    out = ma.market_audit("https://x.test", runner=runner)
    assert out["status"] == "skipped"


def test_market_audit_reports_helper_missing(tmp_path):
    out = ma.market_audit("https://x.test", script=tmp_path / "nope.cjs")
    assert out["status"] == "skipped"


def test_market_audit_reports_load_failure():
    runner = _runner({"*": {"status": "failed", "message": "desktop load failed: net::ERR_NAME_NOT_RESOLVED"}})
    out = ma.market_audit("https://x.test", runner=runner)
    assert out["status"] == "failed"
