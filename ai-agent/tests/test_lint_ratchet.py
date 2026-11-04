"""A ratchet gate can only fall. These tests pin that behaviour."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "lint_ratchet.py"


def _module():
    spec = importlib.util.spec_from_file_location("lint_ratchet", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_rise_above_the_baseline_fails():
    module = _module()
    failures = module.check({"ruff": 100, "bandit_high": 2}, {"ruff": 101, "bandit_high": 2})
    assert failures == ["ruff: 101 > baseline 100"]


def test_a_fall_below_the_baseline_passes():
    module = _module()
    assert module.check({"ruff": 100, "bandit_high": 2}, {"ruff": 99, "bandit_high": 2}) == []


def test_an_unmeasured_tool_never_passes_silently():
    """If ruff is not installed, the run must say so, not report zero."""
    module = _module()
    failures = module.check({"ruff": 100}, {"ruff": None})
    assert failures == ["ruff: not measured (tool unavailable)"]


def test_the_committed_baseline_is_a_complete_measurement():
    baseline_path = ROOT / "ai-agent" / "lint-baseline.json"
    assert baseline_path.is_file(), f"missing baseline: {baseline_path}"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert set(baseline) == {"ruff", "bandit_high", "bandit_medium"}
    assert all(isinstance(value, int) and value >= 0 for value in baseline.values())
