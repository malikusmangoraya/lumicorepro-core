"""The CI workflow is the promise that the suite runs. These tests read it.

A workflow file is executable policy, so it gets the same treatment as code: if
a future edit swaps the test runner for a collector that silently skips two
thirds of the suite, CI must fail here rather than stay green.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _workflow_text() -> str:
    assert WORKFLOW.is_file(), f"CI workflow is missing: {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def _run_commands() -> list[str]:
    """Every `run:` value in the workflow, with comments excluded.

    Reading raw text would count a comment that merely mentions unittest as a
    violation, which teaches people to delete the explanation instead of the
    defect. YAML comments are not part of a step's command.
    """
    yaml = pytest.importorskip("yaml")
    parsed = yaml.safe_load(_workflow_text())
    commands: list[str] = []
    for job in (parsed.get("jobs") or {}).values():
        for step in job.get("steps", []) or []:
            run = step.get("run")
            if isinstance(run, str):
                commands.append(run)
    return commands


def test_ci_runs_pytest_not_unittest():
    """unittest discovers only TestCase subclasses; pytest collects the rest."""
    commands = "\n".join(_run_commands())
    assert "pytest" in commands or "unittest" in commands, "CI defines no python test runner at all"
    assert "unittest" not in commands, (
        "CI must not collect python tests with unittest: it silently skips every "
        "bare def test_* function"
    )
    assert "python -m pytest" in commands, "CI must run the suite with pytest"


def test_ci_python_command_ignores_the_cli_e2e_suite():
    """The CLI e2e suite drives a live process and is excluded by contract."""
    text = _workflow_text()
    assert "tests/test_cli_e2e_progress.py" in text, (
        "the pytest invocation must keep the --ignore for the CLI e2e suite"
    )


def test_ci_workflow_parses_as_yaml():
    yaml = pytest.importorskip("yaml")
    parsed = yaml.safe_load(_workflow_text())
    assert isinstance(parsed, dict) and "jobs" in parsed
