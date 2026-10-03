"""Tests for the browser integration layer.

A fake AgentBrowser stands in for the real CLI so the orchestration logic
(step dispatch, failure short-circuit, remediation prioritisation) is tested
without a browser. The real CLI is exercised separately in the e2e suite.
"""
import sys

sys.path.insert(0, r"D:\lumicorepro-core\ai-agent")

from agent.intelligence import browser_integration as bi  # noqa: E402


class FakeBrowser:
    """Records actions and returns canned responses."""

    available = True
    executable = "agent-browser"

    def __init__(self, *args, **kwargs):
        self.actions = []
        self.closed = False

    def open(self, url):
        self.actions.append(("open", url))
        return True

    def wait(self, ms=0):
        self.actions.append(("wait", ms))
        return True

    def set_viewport(self, w, h):
        self.actions.append(("set_viewport", w, h))
        return True

    def screenshot(self, path, full=False):
        self.actions.append(("screenshot", path, full))
        from pathlib import Path
        Path(path).write_bytes(b"fake-png")
        return path

    def close(self):
        self.closed = True

    def click(self, sel):
        self.actions.append(("click", sel))
        return True

    def fill(self, sel, val):
        self.actions.append(("fill", sel, val))
        return True

    def press(self, key):
        self.actions.append(("press", key))
        return True

    def is_visible(self, sel):
        self.actions.append(("is_visible", sel))
        return True

    def is_enabled(self, sel):
        self.actions.append(("is_enabled", sel))
        return True

    def text(self, sel):
        self.actions.append(("text", sel))
        return "Welcome to Acme"

    def title(self):
        return "Acme Home"

    def eval(self, js):
        return {"sw": 1440, "iw": 1440}

    def network_requests(self, clear=False):
        return [
            {"url": "https://cdn.example.com/app.js", "status": 200},
            {"url": "https://ads.thirdparty.com/pixel", "status": 200},
            {"url": "https://api.local/missing", "status": 404},
        ]

    def vitals(self):
        return {"status": "measured", "metrics": {"LCP": 1800, "CLS": 0.02}}

    def diff_screenshot(self, baseline):
        return {"diffPercent": 4.2}


def test_capture_reference(monkeypatch, tmp_path):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)
    report = bi.capture_reference("http://x", str(tmp_path))
    assert report["status"] == "measured"
    assert set(report["baselines"]) == {"desktop", "tablet", "mobile"}
    assert all(b["status"] == "measured" for b in report["baselines"].values())
    assert (tmp_path / "reference-desktop.png").is_file()


def test_verify_flow_passes(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)
    steps = [
        {"action": "open", "url": "http://x"},
        {"action": "fill", "selector": "#email", "value": "a@b.c"},
        {"action": "click", "selector": "#submit"},
        {"action": "visible", "selector": "#success"},
        {"action": "text", "selector": "#success", "contains": "Welcome"},
    ]
    report = bi.verify_flow("http://x", steps)
    assert report["status"] == "passed"
    assert report["passed"] == 5
    assert report["failed"] == 0


def test_verify_flow_stops_at_failure(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)

    class Failing(FakeBrowser):
        def is_visible(self, sel):
            self.actions.append(("is_visible", sel))
            return False

    monkeypatch.setattr(bi, "AgentBrowser", Failing)
    steps = [
        {"action": "click", "selector": "#a"},
        {"action": "visible", "selector": "#missing"},
        {"action": "click", "selector": "#never-reached"},
    ]
    report = bi.verify_flow("http://x", steps)
    assert report["status"] == "failed"
    assert report["failed_at"] == 1
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert len(report["steps"]) == 2, "flow must stop after the failing step"


def test_verify_flow_unknown_action(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)
    report = bi.verify_flow("http://x", [{"action": "teleport"}])
    assert report["status"] == "failed"
    assert "unknown action" in report["steps"][0]["error"]


def test_network_audit_flags_failures_and_external(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)
    report = bi.network_audit("http://x", allow_external=["cdn.example.com"])
    assert report["status"] == "measured"
    assert report["total_requests"] == 3
    assert report["failed_count"] == 1
    assert report["failed_requests"][0]["status"] == 404
    hosts = {r["host"] for r in report["external_requests"]}
    assert "ads.thirdparty.com" in hosts
    assert "cdn.example.com" not in hosts, "allowed host must not be flagged"


def test_responsive_check_detects_overflow(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)

    class Overflow(FakeBrowser):
        def eval(self, js):
            return {"sw": 1600, "iw": 1440}

    monkeypatch.setattr(bi, "AgentBrowser", Overflow)
    report = bi.responsive_check("http://x")
    assert report["status"] == "measured"
    assert report["overflowing_viewports"] == ["desktop", "tablet", "mobile"]
    assert report["viewports"]["desktop"]["overflow_px"] == 160


def test_responsive_check_no_overflow(monkeypatch):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)
    report = bi.responsive_check("http://x")
    assert report["overflowing_viewports"] == []


def test_performance_audit(monkeypatch, tmp_path):
    monkeypatch.setattr(bi, "AgentBrowser", FakeBrowser)

    class Tracing(FakeBrowser):
        def trace_start(self):
            self.actions.append(("trace_start",))
            return True

        def trace_stop(self, path):
            self.actions.append(("trace_stop", path))
            return path

        def reload(self):
            self.actions.append(("reload",))
            return True

    monkeypatch.setattr(bi, "AgentBrowser", Tracing)
    trace = str(tmp_path / "trace.json")
    report = bi.performance_audit("http://x", trace_path=trace)
    assert report["status"] == "measured"
    assert report["web_vitals"]["metrics"]["LCP"] == 1800
    assert report["trace"]["status"] == "measured"


def test_remediate_findings_prioritises():
    report = {
        "sections": {
            "overflow": {"overflowing": True, "scroll_width": 1600, "inner_width": 1440},
            "console_errors": {"count": 2},
            "page_errors": {"count": 0},
            "accessibility": {"status": "measured", "violation_count": 3},
            "web_vitals": {"status": "measured", "metrics": {"LCP": 3200, "CLS": 0.2}},
        }
    }
    items = bi.remediate_findings(report)
    assert items, "expected remediation items"
    priorities = [i["priority"] for i in items]
    assert priorities == sorted(priorities), "items must be priority-ordered"
    phases = {i["phase"] for i in items}
    assert {"css", "javascript", "a11y", "performance"} <= phases
    assert all(i["status"] == "open" for i in items)


def test_remediate_findings_clean_report():
    report = {
        "sections": {
            "overflow": {"overflowing": False},
            "console_errors": {"count": 0},
            "page_errors": {"count": 0},
            "accessibility": {"status": "measured", "violation_count": 0},
            "web_vitals": {"status": "measured", "metrics": {"LCP": 1200, "CLS": 0.01}},
        }
    }
    assert bi.remediate_findings(report) == []


def test_visual_diff_missing_baseline():
    report = bi.visual_diff("/no/such/baseline.png")
    assert report["status"] == "not_measured"
    assert "baseline image missing" in report["reason"]


def test_deep_browser_audit_not_measured_without_cli(monkeypatch):
    monkeypatch.setattr(bi, "_resolve_cli", lambda: "")
    report = bi.deep_browser_audit("http://x")
    assert report["status"] == "not_measured"
    assert "not found" in report["reason"]
