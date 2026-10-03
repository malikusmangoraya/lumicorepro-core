import sys
import os
import asyncio
import unittest
from pathlib import Path
from unittest import mock

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

import json

from agent.quality_gate import (
    DevOpsQualityGate,
    GateNotAvailableError,
    CommandResult,
    run_quality_gate,
)


def _result(returncode: int, stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(
        command="mock",
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _async_result(returncode: int, stdout: str = "", stderr: str = "") -> mock.AsyncMock:
    """AsyncMock of format_project/lint_project returning a CommandResult."""
    return mock.AsyncMock(return_value=_result(returncode, stdout, stderr))


class TestDevOpsQualityGate(unittest.IsolatedAsyncioTestCase):
    """Hermetic tests for the async DevOps quality gate (format + lint before ZIP)."""

    def setUp(self):
        # Legacy format/lint tests keep self-correction (AI feedback) off so their
        # build-verify assertions stay hermetic; self-correction is covered by the
        # dedicated tests below.
        self.gate = DevOpsQualityGate(require_node=False, self_correct_enabled=False)
        self.project_dir = str(
            Path(os.environ.get("TEMP", "/tmp")) / "lumicore-test-proj" / "generated-projects" / "test-project"
        )
        os.makedirs(os.path.join(self.project_dir, "frontend", "src", "pages"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "backend"), exist_ok=True)
        for rel in (
            "frontend/src/App.jsx",
            "frontend/src/pages/Home.jsx",
            "backend/server.js",
        ):
            with open(os.path.join(self.project_dir, rel), "w", encoding="utf-8") as fh:
                fh.write("export const a = 1;\n")
        for root in ("frontend", "backend"):
            with open(os.path.join(self.project_dir, root, "package.json"), "w", encoding="utf-8") as fh:
                json.dump({"name": root, "scripts": {"build": "echo build"}}, fh)
        test_runner = mock.patch.object(
            self.gate,
            "run_tests",
            new=mock.AsyncMock(return_value={
                "configured": True,
                "passed": True,
                "status": "passed",
                "suites": [{"stack": "frontend", "passed": True}],
            }),
        )
        test_runner.start()
        self.addCleanup(test_runner.stop)

    def tearDown(self):
        root = Path(self.project_dir).parent.parent  # <TEMP>/lumicore-test-proj
        if root.exists():
            import shutil

            shutil.rmtree(str(root), ignore_errors=True)

    def test_available_defaults_to_npm_on_path(self):
        """npm/npx resolution should find executables via shutil.which when present."""
        with mock.patch("agent.quality_gate._resolve_tool", side_effect=lambda n: f"C:/bin/{n}.cmd"):
            gate = DevOpsQualityGate(require_node=True)
            self.assertTrue(gate.npm)
            self.assertEqual(gate.npm, "C:/bin/npm.cmd")

    def test_raises_when_node_tooling_missing(self):
        """A strict gate must refuse to run when npm is unavailable."""
        with mock.patch("agent.quality_gate._resolve_tool", return_value=None):
            with self.assertRaises(GateNotAvailableError):
                DevOpsQualityGate(require_node=True)

    def test_discovers_lintable_sources(self):
        """Lint targets should be scoped to the generated project, excluding vendor dirs."""
        targets = self.gate._lint_targets(self.project_dir)
        self.assertTrue(any(t.endswith("App.jsx") for t in targets))
        self.assertTrue(any(t.endswith("Home.jsx") for t in targets))
        self.assertTrue(any(t.endswith("server.js") for t in targets))

    async def test_missing_project_dir_blocks_gate(self):
        """A nonexistent project directory must block (passed=False)."""
        report = await self.gate.run_gate(os.path.join(self.project_dir, "nope"))
        self.assertFalse(report["passed"])
        self.assertEqual(report["status"], "blocked")

    async def test_gate_passes_when_format_and_lint_exit_zero(self):
        """ZIP compilation is allowed when both format and lint exit 0."""
        with mock.patch.object(self.gate, "format_project", new=_async_result(0)):
            with mock.patch.object(self.gate, "lint_project", new=_async_result(0, stdout="No problems.")):
                report = await self.gate.run_gate(self.project_dir, self_heal=mock.Mock())
        self.assertTrue(report["passed"])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["lint"]["exit_code"], 0)

    async def test_gate_blocks_when_lint_fails_and_no_heal_recovers(self):
        """Non-zero lint exit must block the ZIP and exhaust the heal loop."""
        calls = {"heals": 0}

        def heal(_dir, _files):
            calls["heals"] += 1

        with mock.patch.object(self.gate, "format_project", new=_async_result(0)):
            with mock.patch.object(self.gate, "lint_project", new=_async_result(1, stderr="error  Unexpected token  App.jsx:5:9")):
                report = await self.gate.run_gate(self.project_dir, self_heal=heal)
        self.assertFalse(report["passed"])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(calls["heals"], self.gate.max_heal_attempts)
        self.assertGreaterEqual(report["attempts"], 2)

    async def test_self_heal_recovers_on_second_attempt(self):
        """After a self-healing round fixes the file, the gate should pass."""
        lint_results = [
            _result(1, stderr="error  BadCode  frontend/src/App.jsx:3:1"),
            _result(0),
        ]
        state = {"idx": 0, "heals": 0}

        async def lint_side(_dir, **kwargs):
            value = lint_results[state["idx"]]
            state["idx"] += 1
            return value

        def heal(_dir, _files):
            state["heals"] += 1

        with mock.patch.object(self.gate, "format_project", new=_async_result(0)):
            with mock.patch.object(self.gate, "lint_project", side_effect=lint_side):
                report = await self.gate.run_gate(self.project_dir, self_heal=heal)
        self.assertTrue(report["passed"])
        self.assertEqual(state["heals"], 1)

    async def test_format_failure_alone_blocks_gate(self):
        """A non-zero format exit must independently block ZIP compilation."""
        with mock.patch.object(self.gate, "format_project", new=_async_result(2, stderr="prettier error")):
            with mock.patch.object(self.gate, "lint_project", new=_async_result(0)):
                report = await self.gate.run_gate(self.project_dir, self_heal=mock.Mock())
        self.assertFalse(report["passed"])
        self.assertNotEqual(report["format"]["exit_code"], 0)

    def test_lint_offenders_extracts_project_files(self):
        """lint_offenders should surface unique project-relative paths from ESLint output."""
        lint = _result(
            1,
            stdout="generated-projects/test-project/frontend/src/App.jsx:5:9  error  Unexpected token\n"
                   "generated-projects/test-project/frontend/src/App.jsx:5:9  error  Parsing error",
            stderr="",
        )
        offenders = self.gate.lint_offenders(lint, self.project_dir)
        self.assertEqual(offenders, ["generated-projects/test-project/frontend/src/App.jsx"])

    async def test_run_quality_gate_helper(self):
        """Drop-in helper should expose the same gated pipeline (async)."""
        with mock.patch("agent.quality_gate.DevOpsQualityGate") as m_gate:
            instance = m_gate.return_value
            instance.run_gate = mock.AsyncMock(return_value={"passed": True, "status": "passed"})
            report = await run_quality_gate(self.project_dir, max_heal_attempts=1, require_node=False)
        self.assertTrue(report["passed"])

    def test_run_command_is_awaitable(self):
        """The subprocess layer exposes an awaitable coroutine, not a blocking call."""
        coro = self.gate.run_command(["echo", "hi"])
        self.assertTrue(asyncio.iscoroutine(coro))
        coro.close()

    def test_package_roots_discovers_frontend_and_backend(self):
        """verify_build targets every package.json root (root/frontend/backend)."""
        roots = self.gate._package_roots(self.project_dir)
        self.assertEqual(
            [os.path.basename(r) for r in roots],
            ["frontend", "backend"],
        )

    async def test_run_tests_executes_each_declared_script_in_ci_mode(self):
        for root in ("frontend", "backend"):
            package_path = os.path.join(self.project_dir, root, "package.json")
            with open(package_path, encoding="utf-8") as fh:
                package = json.load(fh)
            package["scripts"]["test"] = "test-command"
            with open(package_path, "w", encoding="utf-8") as fh:
                json.dump(package, fh)

        calls = []

        async def run_command(args, cwd=None, env=None):
            calls.append((args, cwd, env))
            return _result(0, stdout="tests passed")

        with mock.patch.object(self.gate, "run_command", side_effect=run_command):
            result = await DevOpsQualityGate.run_tests(self.gate, self.project_dir)

        self.assertTrue(result["passed"])
        self.assertEqual(len(result["suites"]), 2)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[2]["CI"] == "1" for call in calls))
        self.assertTrue(all(call[0][-1] == "test" for call in calls))

    async def test_run_tests_reports_missing_test_scripts(self):
        result = await DevOpsQualityGate.run_tests(self.gate, self.project_dir)
        self.assertFalse(result["configured"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "not_configured")

    async def test_gate_blocks_when_package_tests_fail(self):
        failed_tests = {
            "configured": True,
            "passed": False,
            "status": "failed",
            "suites": [{"stack": "frontend", "passed": False}],
        }
        with mock.patch.object(self.gate, "format_project", new=_async_result(0)):
            with mock.patch.object(self.gate, "lint_project", new=_async_result(0)):
                with mock.patch.object(
                    self.gate, "run_tests", new=mock.AsyncMock(return_value=failed_tests)
                ):
                    report = await self.gate.run_gate(self.project_dir)
        self.assertFalse(report["passed"])
        self.assertEqual(report["tests"]["status"], "failed")

    async def test_verify_build_skips_when_no_package_json(self):
        """A project with no package roots must be treated as OK (nothing to build)."""
        empty_dir = os.path.join(self.project_dir, "static-only")
        os.makedirs(empty_dir, exist_ok=True)
        result = await self.gate.verify_build(empty_dir)
        self.assertTrue(result["ok"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["builds"], [])

    async def test_verify_build_not_run_when_disabled(self):
        """Build verification only runs when enabled."""
        with mock.patch.object(self.gate, "format_project", new=_async_result(0)):
            with mock.patch.object(self.gate, "lint_project", new=_async_result(0)):
                report = await self.gate.run_gate(self.project_dir, self_heal=mock.Mock())
        self.assertTrue(report["passed"])
        self.assertFalse(report["build_verify"]["enabled"])
        self.assertFalse(report["build_verify"]["verified"])

    async def test_self_correction_feeds_error_blob_and_recovers(self):
        """Compiler/lint error output must reach the error_fixer and the loop must
        then re-run to green."""
        gate = DevOpsQualityGate(require_node=False, self_correct_enabled=True)
        lint_results = [
            _result(1, stderr="error  Unexpected token  frontend/src/App.jsx:5:9"),
            _result(0),
        ]
        state = {"idx": 0}
        errors_seen = []

        async def lint_side(_dir, **kwargs):
            value = lint_results[state["idx"]]
            state["idx"] += 1
            return value

        def fixer(_dir, error_blob, round_idx):
            errors_seen.append((round_idx, error_blob))
            return {"status": "applied", "files_changed": ["frontend/src/App.jsx"]}

        with mock.patch.object(gate, "run_tests", new=mock.AsyncMock(return_value={
            "configured": True,
            "passed": True,
            "status": "passed",
            "suites": [{"stack": "frontend", "passed": True}],
        })):
            with mock.patch.object(gate, "format_project", new=_async_result(0)):
                with mock.patch.object(gate, "lint_project", side_effect=lint_side):
                    with mock.patch.object(
                        gate, "verify_build",
                        mock.AsyncMock(return_value={"ok": True, "verified": True, "builds": []}),
                    ):
                        report = await gate.run_gate(self.project_dir, error_fixer=fixer)
        self.assertTrue(report["passed"])
        self.assertEqual(len(errors_seen), 1)
        self.assertIn("Unexpected token", errors_seen[0][1])
        self.assertEqual(len(report["self_correction"]), 1)
        self.assertTrue(report["build_verify"]["enabled"])

    async def test_self_correction_exhausts_ai_rounds(self):
        """A persistently failing build must exhaust SELF_CORRECT_MAX_ROUNDS AI
        feedback rounds before blocking ZIP compilation."""
        gate = DevOpsQualityGate(
            require_node=False, self_correct_enabled=True, self_correct_max_rounds=3,
        )
        fix_calls = []

        def fixer(_dir, error_blob, round_idx):
            fix_calls.append(round_idx)
            return {"status": "no_changes"}

        with mock.patch.object(gate, "format_project", new=_async_result(0)):
            with mock.patch.object(
                gate, "lint_project",
                new=_async_result(1, stderr="error  Cannot find name 'X'  frontend/src/App.jsx:2:1"),
            ):
                report = await gate.run_gate(self.project_dir, error_fixer=fixer)
        self.assertFalse(report["passed"])
        self.assertEqual(fix_calls, [0, 1, 2])
        self.assertEqual(len(report["self_correction"]), 3)
        self.assertEqual(report["status"], "blocked")


if __name__ == "__main__":
    unittest.main()