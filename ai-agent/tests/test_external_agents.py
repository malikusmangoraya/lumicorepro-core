import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent import external_agents as ext


def _proc(returncode=0, stdout="", stderr=""):
    return mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)


class TestToolStatus(unittest.TestCase):
    def setUp(self):
        ext._status_cache.update({"at": 0.0, "data": None})

    def test_missing_clis_are_not_installed(self):
        with mock.patch.object(ext, "_opencode_binary", return_value=None), \
             mock.patch.object(ext, "_freebuff_binary", return_value=None):
            status = ext.tool_status()
        self.assertFalse(status["opencode"]["installed"])
        self.assertFalse(status["freebuff"]["installed"])
        self.assertEqual(status["opencode"]["path"], "")

    def test_opencode_is_headless_and_freebuff_is_not(self):
        def fake_run(cmd, **kwargs):
            if "--version" in cmd:
                return _proc(stdout="1.2.3")
            if cmd[0] == "opencode":
                return _proc(
                    stdout="USAGE opencode run [flags]\n  --format choice\n  --auto"
                )
            return _proc(
                stdout="Usage: freebuff [options] [command]\n"
                "  -v, --version  Print the CLI version\n  --print-logs  logs"
            )

        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext.subprocess, "run", side_effect=fake_run) as run:
            status = ext.tool_status()

        self.assertTrue(status["opencode"]["headless"])
        self.assertFalse(status["freebuff"]["headless"])
        self.assertIn("terminal UI", status["freebuff"]["headless_reason"])
        # version + help probe per CLI
        self.assertEqual(run.call_count, 4)

    def test_status_is_cached_until_forced(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext, "_freebuff_binary", return_value=None), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc(stdout="1.0")) as run:
            first = ext.tool_status()
            second = ext.tool_status()
            ext.tool_status(force=True)

        self.assertIs(first, second)
        self.assertEqual(run.call_count, 4)  # 2 probes + 2 forced probes

    def test_print_logs_is_not_mistaken_for_a_headless_mode(self):
        def fake_run(cmd, **kwargs):
            if "--version" in cmd:
                return _proc(stdout="0.2.34")
            return _proc(stdout="Usage: freebuff [options]\n  --print-logs  logs")

        with mock.patch.object(ext, "_opencode_binary", return_value=None), \
             mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext.subprocess, "run", side_effect=fake_run):
            status = ext.tool_status(force=True)
        self.assertFalse(status["freebuff"]["headless"])

    def test_opencode_version_probe_is_standalone(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if "--version" in cmd:
                return _proc(stdout="opencode v2.1.3")
            return _proc(stdout="USAGE opencode run\n  --format choice\n  --auto")

        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext, "_freebuff_binary", return_value=None), \
             mock.patch.object(ext.subprocess, "run", side_effect=fake_run):
            status = ext.tool_status(force=True)

        self.assertTrue(status["opencode"]["headless"])
        self.assertIn(["opencode", "--standalone", "--version"], calls)
        self.assertIn(["opencode", "run", "--help"], calls)

    def test_probe_failure_never_raises(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext, "_freebuff_binary", return_value=None), \
             mock.patch.object(ext.subprocess, "run", side_effect=OSError("boom")):
            status = ext.tool_status()
        self.assertTrue(status["opencode"]["installed"])
        self.assertFalse(status["opencode"]["version_ok"])
        self.assertIn("boom", status["opencode"]["probe_error"])


class TestRunOpencode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_arguments_are_an_argv_list_with_auto_and_format(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc()) as run:
            result = ext.run_opencode(
                self.tmp.name, "add tests", model="p/m", agent="build", format="json"
            )

        self.assertEqual(result["status"], "passed")
        cmd = run.call_args.args[0]
        self.assertEqual(
            cmd,
            ["opencode", "run", "add tests", "--format", "json", "--model", "p/m",
             "--agent", "build", "--auto", "--standalone"],
        )
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["cwd"], str(Path(self.tmp.name)))
        self.assertEqual(kwargs["stdin"], ext.subprocess.DEVNULL)
        self.assertFalse(kwargs["shell"] if "shell" in kwargs else False)

    def test_invalid_format_is_rejected_without_spawning(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_opencode(self.tmp.name, "task", format="yaml")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "invalid_format")
        run.assert_not_called()

    def test_missing_project_dir_is_refused_not_redirected(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_opencode(str(Path(self.tmp.name) / "nope"), "task")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "invalid_project_dir")
        run.assert_not_called()

    def test_empty_task_is_rejected(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_opencode(self.tmp.name, "   ")
        self.assertEqual(result["reason"], "invalid_task")
        run.assert_not_called()

    def test_oversized_task_is_rejected(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_opencode(self.tmp.name, "x" * (ext._MAX_TASK_CHARS + 1))
        self.assertEqual(result["reason"], "invalid_task")
        run.assert_not_called()

    def test_timeout_is_reported_not_raised(self):
        expired = ext.subprocess.TimeoutExpired("opencode", 30)
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run", side_effect=expired):
            result = ext.run_opencode(self.tmp.name, "task", timeout_s=30)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "timeout")

    def test_nonzero_exit_keeps_the_stderr_tail(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc(2, stderr="bad thing")):
            result = ext.run_opencode(self.tmp.name, "task")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "exit_nonzero")
        self.assertIn("bad thing", result["error"])

    def test_bun_crash_is_named(self):
        crash = "panic(main thread): Segmentation fault"
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc(3, stderr=crash)):
            result = ext.run_opencode(self.tmp.name, "task")
        self.assertEqual(result["reason"], "runtime_crash")

    def test_missing_binary_is_not_available(self):
        with mock.patch.object(ext, "_opencode_binary", return_value=None):
            result = ext.run_opencode(self.tmp.name, "task")
        self.assertEqual(result["status"], "not_available")

    def test_timeout_is_clamped_and_invalid_values_refused(self):
        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc()) as run:
            ext.run_opencode(self.tmp.name, "task", timeout_s=1)
        self.assertEqual(run.call_args.kwargs["timeout"], 30)

        with mock.patch.object(ext, "_opencode_binary", return_value="opencode"), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_opencode(self.tmp.name, "task", timeout_s="soon")
        self.assertEqual(result["reason"], "invalid_timeout")
        run.assert_not_called()


class TestRunFreebuff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_tui_only_cli_is_unsupported_without_spawning(self):
        with mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext, "_supports_headless", return_value=False), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_freebuff(self.tmp.name, "task")
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["reason"], "no_headless_mode")
        self.assertFalse(result["headless"])
        run.assert_not_called()

    def test_interactive_opt_in_runs_and_marks_headless_false(self):
        with mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext, "_supports_headless", return_value=False), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc()) as run:
            result = ext.run_freebuff(self.tmp.name, "task", interactive=True)
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["headless"])
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], "freebuff")

    def test_headless_capable_release_runs(self):
        with mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext, "_supports_headless", return_value=True), \
             mock.patch.object(ext.subprocess, "run", return_value=_proc()) as run:
            result = ext.run_freebuff(self.tmp.name, "task", extra_args=["--agent", "base"])
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["headless"])
        self.assertEqual(run.call_args.args[0], ["freebuff", "task", "--agent", "base"])

    def test_missing_binary_is_not_available(self):
        with mock.patch.object(ext, "_freebuff_binary", return_value=None):
            result = ext.run_freebuff(self.tmp.name, "task")
        self.assertEqual(result["status"], "not_available")

    def test_too_many_extra_args_rejected(self):
        with mock.patch.object(ext, "_freebuff_binary", return_value="freebuff"), \
             mock.patch.object(ext, "_supports_headless", return_value=True), \
             mock.patch.object(ext.subprocess, "run") as run:
            result = ext.run_freebuff(
                self.tmp.name, "task", extra_args=["x"] * (ext._MAX_EXTRA_ARGS + 1)
            )
        self.assertEqual(result["reason"], "invalid_args")
        run.assert_not_called()


class TestHelpers(unittest.TestCase):
    def test_tail_keeps_the_end(self):
        self.assertEqual(ext._tail("abcdef", 3), "def")

    def test_tail_handles_none(self):
        self.assertEqual(ext._tail(None), "")


if __name__ == "__main__":
    unittest.main()
