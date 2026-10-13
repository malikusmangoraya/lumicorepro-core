"""Tests for auto mode — the zero-prompt, budget-enforced generation contract."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.auto_mode import (
    AUTO_RUN_TIMEOUT_SECS,
    AutoModeInputBlocked,
    AutoModeTimeout,
    block_interactive_input,
    describe_auto_mode,
    run_auto,
)


def _canned_report(**overrides):
    report = {
        "status": "succeeded",
        "project_name": "demo",
        "generated_project_dir": "/tmp/demo",
        "phase_failures": [],
        "providers_used": [],
        "fallback_used": False,
        "reason": None,
        "skipped_phases": [],
    }
    report.update(overrides)
    return report


def _mock_orchestrator(report):
    orch = MagicMock()
    orch.NON_CRITICAL_FAILURE_LIMIT = 5
    orch.run.return_value = report
    return orch


def test_input_guard_blocks_prompt():
    with block_interactive_input():
        with pytest.raises(AutoModeInputBlocked):
            input("say something: ")


def test_input_restored_after_guard():
    real = __builtins__["input"] if isinstance(__builtins__, dict) else __builtins__.input
    with block_interactive_input():
        pass
    current = __builtins__["input"] if isinstance(__builtins__, dict) else __builtins__.input
    assert current is real


def test_run_auto_success_attaches_auto_block():
    report = _canned_report()
    with patch("agent.orchestrator.AgentOrchestrator", return_value=_mock_orchestrator(report)):
        out = run_auto("a test shop", design_style="minimalism")
    assert out["status"] == "succeeded"
    auto = out["auto_mode"]
    assert auto["mode"] == "auto"
    assert auto["input_guard"] == "enforced"
    assert auto["failure_limit"] == 5
    assert auto["failure_count"] == 0
    assert auto["failure_budget_exceeded"] is False
    assert auto["elapsed_secs"] >= 0


def test_run_auto_passes_interactive_false_and_scaffold():
    report = _canned_report()
    orch = _mock_orchestrator(report)
    with patch("agent.orchestrator.AgentOrchestrator", return_value=orch):
        run_auto("prompt", page_scaffold="bento_showcase", provider="gemini")
    _, kwargs = orch.run.call_args
    assert kwargs["interactive"] is False
    extra = kwargs["extra_spec"]
    assert extra["design_constraints"]["page_scaffold"] == "bento_showcase"


def test_run_auto_enforces_failure_budget():
    report = _canned_report(status="partial", phase_failures=["a", "b", "c", "d", "e", "f"])
    with patch("agent.orchestrator.AgentOrchestrator", return_value=_mock_orchestrator(report)):
        out = run_auto("prompt")
    assert out["status"] == "failed"
    assert out["reason"] == "auto_failure_budget_exceeded"
    assert out["auto_mode"]["failure_budget_exceeded"] is True
    assert out["auto_mode"]["failure_count"] == 6


def test_run_auto_within_budget_keeps_partial():
    report = _canned_report(status="partial", phase_failures=["a", "b"])
    with patch("agent.orchestrator.AgentOrchestrator", return_value=_mock_orchestrator(report)):
        out = run_auto("prompt")
    assert out["status"] == "partial"
    assert out["auto_mode"]["failure_budget_exceeded"] is False


def test_run_auto_timeout_raises():
    orch = MagicMock()
    orch.NON_CRITICAL_FAILURE_LIMIT = 5
    orch.run.side_effect = lambda *a, **k: time.sleep(2)
    with patch("agent.orchestrator.AgentOrchestrator", return_value=orch):
        with pytest.raises(AutoModeTimeout):
            run_auto("prompt", timeout_secs=1)


def test_run_auto_input_attempt_fails_loud():
    orch = MagicMock()
    orch.NON_CRITICAL_FAILURE_LIMIT = 5

    def _prompting_run(*a, **k):
        input("clarify?")
        return _canned_report()

    orch.run.side_effect = _prompting_run
    with patch("agent.orchestrator.AgentOrchestrator", return_value=orch):
        with pytest.raises(AutoModeInputBlocked):
            run_auto("prompt")


def test_run_auto_no_report_raises():
    orch = MagicMock()
    orch.NON_CRITICAL_FAILURE_LIMIT = 5
    orch.run.return_value = None
    with patch("agent.orchestrator.AgentOrchestrator", return_value=orch):
        with pytest.raises(Exception):
            run_auto("prompt")


def test_describe_auto_mode_contract():
    contract = describe_auto_mode()
    assert contract["mode"] == "auto"
    assert contract["entry_python"] == "agent.auto_mode.run_auto"
    assert contract["entry_http"] == "POST /api/auto"
    assert "python main.py --auto" in contract["entry_cli"]
    assert len(contract["guarantees"]) >= 4
    assert contract["report_block"] == "auto_mode"
    assert AUTO_RUN_TIMEOUT_SECS == 1800
