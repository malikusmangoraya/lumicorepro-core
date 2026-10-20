"""Tests for agent.oss_power_tools â€” OSS power-up pack (no network needed)."""
import json
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from agent import oss_power_tools as opt


@pytest.fixture()
def tiny_project(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "src.js").write_text("const a = 1;\n", encoding="utf-8")
    return tmp_path


def _runner(results):
    """Build a fake subprocess runner keyed by command[0]."""
    def run(cmd, cwd=None, *a, **kw):
        key = Path(cmd[0]).name if cmd else ""
        if key.endswith((".cmd", ".exe")):
            key = key.rsplit(".", 1)[0]
        if key in results:
            return results[key]
        return (results.get("*", (1, "", "unexpected cmd: " + " ".join(cmd))))
    return run


def test_secrets_scan_finds_planted_key(tmp_path):
    (tmp_path / "config.js").write_text('const KEY = "sk-proj-abcdefghij0123456789abcd";\n', encoding="utf-8")
    out = opt.secrets_scan(str(tmp_path))
    assert out["status"] == "failed"
    assert out["total_findings"] == 1
    assert out["findings"][0]["kind"] == "openai_key"
    assert out["findings"][0]["line"] == 1
    assert "abcdefghij0123456789abcd" not in out["findings"][0]["match"]


def test_secrets_scan_skips_examples_and_vendor(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "leak.js").write_text("ghp_AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHH1111\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "# your_api_key_here placeholder example: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", encoding="utf-8")
    out = opt.secrets_scan(str(tmp_path))
    assert out["status"] == "passed"
    assert out["total_findings"] == 0


def test_secrets_scan_clean_project_passes(tiny_project):
    out = opt.secrets_scan(str(tiny_project))
    assert out["status"] == "passed"
    assert out["checked_files"] >= 1


def test_npm_audit_skipped_without_lockfile(tiny_project):
    out = opt.npm_audit(str(tiny_project))
    assert out["status"] == "skipped"


def test_npm_audit_summarises_vulnerabilities(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package-lock.json").write_text("{}", encoding="utf-8")
    payload = {
        "metadata": {"vulnerabilities": {"info": 0, "low": 1, "moderate": 0, "high": 2, "critical": 0, "total": 3}},
        "vulnerabilities": {"lodash": {"severity": "high", "fixAvailable": True}},
    }
    runner = _runner({"npm": (0, json.dumps(payload), "")})
    out = opt.npm_audit(str(tmp_path), runner=runner)
    assert out["status"] == "warn"
    assert out["counts"]["total"] == 3
    assert out["vulnerabilities"][0]["package"] == "lodash"


def test_license_report_flags_copyleft(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text(
        json.dumps({"dependencies": {"liba": "^1", "libg": "^2"}}), encoding="utf-8")
    runner = _runner({"npm": (0, "GPL-3.0-only\n", "")})
    out = opt.license_report(str(tmp_path), runner=runner)
    assert out["copyleft_risk"] == ["liba", "libg"]
    assert out["dependencies"][0]["commercial_ok"] is False


def test_license_report_cache_reuses_lookups(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text(
        json.dumps({"dependencies": {"liba": "^1"}}), encoding="utf-8")
    calls = []

    def runner(cmd, cwd=None, *a, **kw):
        calls.append(cmd)
        return (0, "MIT\n", "")

    cache = {"liba": "MIT"}
    opt.license_report(str(tmp_path), runner=runner, _cache=cache)
    assert not calls  # all packages served from cache


def test_lint_project_parses_oxlint_json(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "frontend" / "src.js").write_text("const a = 1;\n", encoding="utf-8")
    payload = [
        {"rule": "no-unused-vars", "file": "src/a.js"},
        {"rule": "no-unused-vars", "file": "src/a.js"},
        {"rule": "eqeqeq", "file": "src/b.js"},
    ]
    runner = _runner({"npx": (0, json.dumps(payload), "")})
    out = opt.lint_project(str(tmp_path), runner=runner)
    assert out["status"] == "warn"
    assert out["issues"] == 3
    assert out["by_rule"]["no-unused-vars"] == 2
    assert out["worst_files"]["src/a.js"] == 2


def test_lint_project_skipped_without_package_json(tmp_path):
    assert opt.lint_project(str(tmp_path))["status"] == "skipped"


def test_a11y_audit_parses_helper_output():
    runner = _runner({"node": (0, json.dumps({"status": "ok", "url": "https://x", "passes": 42,
        "violations": [{"id": "color-contrast", "impact": "serious", "nodes": 3}]}), "")})
    out = opt.a11y_audit("https://x.test", runner=runner)
    assert out["status"] == "warn"
    assert out["node_counts"]["serious"] == 3
    assert out["passes"] == 42


def test_a11y_audit_reports_helper_missing(tmp_path):
    out = opt.a11y_audit("https://x.test", script=tmp_path / "nope.cjs")
    assert out["status"] == "skipped"


def test_mermaid_doc_writes_blueprint(tiny_project):
    (tiny_project / "backend").mkdir()
    (tiny_project / "backend" / "srv.js").write_text("", encoding="utf-8")
    out = opt.mermaid_doc(str(tiny_project))
    assert out["status"] == "ok"
    doc = (tiny_project / "docs" / "architecture.mmd").read_text(encoding="utf-8")
    assert doc.startswith("graph LR")
    assert "Express API" in doc and "PostgreSQL" in doc
    assert "REST /api/v1" in doc


def test_mermaid_doc_includes_agent_layer(tmp_path):
    (tmp_path / "ai-agent").mkdir()
    (tmp_path / "ai-agent" / "m.py").write_text("", encoding="utf-8")
    out = opt.mermaid_doc(str(tmp_path))
    assert "FastAPI agent" in out["mermaid"]
    assert "LLM providers" in out["mermaid"]
