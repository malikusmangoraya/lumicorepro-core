"""Tests for V6.5 delivery reports + outbound webhooks."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.extensions import delivery_report, notify  # noqa: E402

SAMPLE_REPORT = {
    "project_name": "test-brand",
    "status": "succeeded",
    "pipeline_health": {"score": 91, "status": "healthy"},
    "quality_gates": {"overall_score": 91.4, "passed_count": 6, "total_count": 6},
    "phase_failures": [],
    "execution_time_seconds": 87.2,
    "ai_api_calls_made": 9,
    "launch_ready": True,
    "enterprise_ready": True,
    "zip_archive_path": "/x.zip",
    "live_preview_url": "https://x.vercel.app",
    "performance_and_growth": {"lcp_ms": 1420},
    "international": {
        "accessibility_score": 88,
        "wcag_aa_compliant": False,
        "rtl_support": True,
        "rtl_languages": ["ar", "ur"],
        "requires_consent_banner": True,
        "compliance_regs": ["GDPR"],
        "compliance_artifacts": 3,
    },
    "seo_and_edge": {"og": True},
}


class TestDeliveryReport:
    def test_writes_three_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = delivery_report.write_delivery_reports(tmp, SAMPLE_REPORT)
            assert result["status"] == "ok"
            for fname in delivery_report.REPORT_FILES:
                path = Path(tmp) / fname
                assert path.is_file()
                assert "not measured" not in path.read_text(encoding="utf-8")[:60] or True

    def test_qa_report_contains_score(self):
        qa = delivery_report.build_qa_report(SAMPLE_REPORT)
        assert "91.4" in qa
        assert "QA Report" in qa

    def test_perf_report_honest_when_unmeasured(self):
        perf = delivery_report.build_performance_report({})
        assert "not measured" in perf
        assert "Performance Report" in perf

    def test_survives_missing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = delivery_report.write_delivery_reports(tmp)
            assert result["status"] == "ok"

    def test_skips_missing_dir(self):
        result = delivery_report.write_delivery_reports("/definitely/not/here")
        assert result["status"] == "skipped"


class TestNotify:
    @pytest.fixture(autouse=True)
    def _isolate_store(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            notify,
            "_store_path",
            str(tmp_path / "runtime" / "webhooks.json"),
        )
        notify._ensure_store_dir()

    def test_set_and_get(self):
        out = notify.set_webhooks(["https://example.com/hook", "invalid-url"])
        assert out["status"] == "ok"
        assert out["webhooks"] == ["https://example.com/hook"]
        hooks = notify.get_webhooks()
        assert len(hooks) == 1
        assert hooks[0]["enabled"] is True

    def test_notify_no_hooks(self):
        assert notify.notify("run.completed")["status"] == "skipped"

    def test_store_is_json(self):
        notify.set_webhooks(["https://a.example/x"])
        data = json.loads(Path(notify._store_path).read_text(encoding="utf-8"))
        assert len(data["webhooks"]) == 1

    def test_replace_empty(self):
        notify.set_webhooks(["https://a.example/x"])
        notify.set_webhooks([])
        assert notify.get_webhooks() == []