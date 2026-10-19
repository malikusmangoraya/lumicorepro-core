"""Tests for agent.free_web_tools — free keyless internet QA tools (mocked HTTP)."""
import json
from unittest import mock

from agent import free_web_tools as fwt


def _fake_urlopen(payload):
    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(payload).encode()

        def geturl(self):
            return payload.get("final_url", "https://x.test")

    return lambda req, timeout=0: _Resp()


def test_pagespeed_scores_and_opportunities():
    report = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.93}, "seo": {"score": 1.0}},
            "audits": {
                "largest-contentful-paint": {"displayValue": "1.2 s", "numericValue": 1200, "score": 0.95},
                "unused-css-rules": {"score": 0.5, "details": {"overallSavingsMs": 700}, "title": "Unused CSS"},
            },
        }
    }
    with mock.patch.object(fwt.urllib.request, "urlopen", _fake_urlopen(report)):
        out = fwt.pagespeed_audit("https://x.test", "desktop")
    assert out["status"] == "ok"
    assert out["scores"]["performance"] == 93
    assert out["metrics"]["largest-contentful-paint"]["display"] == "1.2 s"
    assert out["opportunities"][0]["id"] == "unused-css-rules"


def test_pagespeed_rejects_bad_input():
    assert fwt.pagespeed_audit("not-a-url")["status"] == "failed"


def test_pagespeed_strategy_fallback():
    report = {"lighthouseResult": {"categories": {}, "audits": {}}}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(report).encode()

    with mock.patch.object(fwt.urllib.request, "urlopen") as fake:
        fake.return_value = _Resp()
        fwt.pagespeed_audit("https://x.test", strategy="walrus")
        passed = fake.call_args[0][0].full_url
    assert "strategy=mobile" in passed


def test_w3c_url_and_counts():
    report = {"messages": [
        {"type": "error", "lastLine": 12, "message": "bogus attribute x"},
        {"type": "info", "lastLine": 2, "message": "note"},
    ]}
    with mock.patch.object(fwt.urllib.request, "urlopen", _fake_urlopen(report)):
        out = fwt.w3c_validate(url="https://x.test")
    assert out["status"] == "ok"
    assert out["error_count"] == 1
    assert out["first_errors"][0]["line"] == 12


def test_w3c_content_posts_body():
    sent = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"{}"

    def catcher(req, timeout=0):
        sent["data"] = req.data
        return _Resp()

    with mock.patch.object(fwt.urllib.request, "urlopen", catcher):
        out = fwt.w3c_validate(content="<html></html>")
    assert out["status"] == "ok"
    assert b"<html>" in sent["data"]


def test_w3c_requires_input():
    assert fwt.w3c_validate()["status"] == "failed"


def test_npm_latest_versions():
    def latest(req, timeout=0):
        if "nope-pkg" in req.full_url:
            raise fwt.urllib.error.HTTPError(req.full_url, 404, "not found", {}, None)

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"version": "1.2.3"}).encode()

        return _Resp()

    with mock.patch.object(fwt.urllib.request, "urlopen", latest):
        out = fwt.npm_latest(["react", "@scope/pkg", "nope-pkg"])
    assert out["status"] == "ok"
    assert out["versions"]["react"] == "1.2.3"
    assert out["versions"]["@scope/pkg"] == "1.2.3"
    assert "nope-pkg" in out["missing"]


def test_npm_empty_input():
    assert fwt.npm_latest([])["status"] == "failed"


def test_http_reachable_codes():
    with mock.patch.object(fwt.urllib.request, "urlopen", _fake_urlopen({"u": 1})):
        ok = fwt.http_reachable("https://x.test")
    assert ok["status"] == "ok"
    assert fwt.http_reachable("ftp://no")["status"] == "failed"
