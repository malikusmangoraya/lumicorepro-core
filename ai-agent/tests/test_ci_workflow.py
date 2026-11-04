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


def test_ci_guards_against_committed_credentials():
    """A tracked .env leaks in every clone; the guard must run before install."""
    commands = _run_commands()
    assert any("check-tracked-secrets.mjs" in command for command in commands), (
        "no CI step runs scripts/check-tracked-secrets.mjs"
    )
    assert (ROOT / "scripts" / "check-tracked-secrets.mjs").is_file()
    # It must be the first thing the job does, so a later step cannot run
    # first and report success against a leaked tree.
    assert "check-tracked-secrets.mjs" in commands[0], (
        "the credential guard must be the first command in the workflow"
    )


FIXTURE = ROOT / "generated-projects" / "blogforge"


def test_ci_fixture_is_committed():
    """A leg that runs npm ci on a gitignored path can never pass on CI."""
    assert FIXTURE.is_dir(), f"the committed fixture is missing: {FIXTURE}"
    assert (FIXTURE / "backend" / "package.json").is_file()
    assert (FIXTURE / "frontend" / "package.json").is_file()
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "generated-projects/" not in ignored, (
        "the whole generated-projects/ tree is gitignored, so the fixture "
        "cannot be committed; ignore the volatile subpaths instead"
    )


def test_ci_fixture_leg_uses_scripts_that_exist():
    """Every npm script the workflow calls must exist in the target package."""
    import json

    commands = "\n".join(_run_commands())
    calls = [
        ("generated-projects/blogforge", "test:backend"),
        ("generated-projects/blogforge/frontend", "test:e2e"),
        ("generated-projects/blogforge/backend", "db:migrate"),
        ("generated-projects/blogforge/frontend", "build"),
    ]
    for prefix, script in calls:
        assert f"npm run {script} --prefix {prefix}" in commands, (
            f"CI no longer calls {script} on {prefix}"
        )
        package = ROOT / prefix / "package.json"
        assert package.is_file(), f"missing {package}"
        scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        assert script in scripts, f"{prefix}/package.json defines no {script} script"


def test_ci_verifies_delivered_products():
    """A verification script nothing invokes is documentation, not a gate."""
    commands = "\n".join(_run_commands())
    assert "verify_delivery_builds.py" in commands, (
        "no workflow invokes scripts/verify_delivery_builds.py"
    )
    assert "products/sell-today" in commands, (
        "delivery verification must run on the products that carry real source"
    )
    assert (ROOT / "scripts" / "verify_delivery_builds.py").is_file()


def test_ci_provides_a_database_for_the_fixture():
    """db:migrate needs a reachable Postgres; a job without one cannot pass."""
    yaml = pytest.importorskip("yaml")
    parsed = yaml.safe_load(_workflow_text())
    services = {}
    for job in (parsed.get("jobs") or {}).values():
        services.update(job.get("services") or {})
    assert "postgres" in services, "the fixture job needs a postgres service container"
    text = _workflow_text()
    assert "DATABASE_URL" in text, "the fixture backend needs DATABASE_URL for migrations"
    # The generated suite guards every test with `skip: !process.env.TEST_DATABASE_URL`,
    # so DATABASE_URL alone runs zero assertions and still exits 0.
    assert "TEST_DATABASE_URL" in text, (
        "the generated backend suite skips every test unless TEST_DATABASE_URL is set"
    )
