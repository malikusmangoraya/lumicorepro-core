"""Test execution + resolution grading.

Grading is evidence-based only: a task counts as resolved when the dataset's
FAIL_TO_PASS tests go green and no previously-passing test regresses. Anything
that could not be measured is reported as `not_measured` / `grader_error`, never
as a pass.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from utils.logger import agent_logger

from .workspace import TaskWorkspace

STATUS_LINE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(\S+)")
SUMMARY_LINE = re.compile(r"(\d+)\s+(passed|failed|error|errors|skipped)")
NO_TESTS_MARKERS = ("no tests ran", "file or directory not found", "not found:", "ERROR: not found")


@dataclass
class TestRun:
    """Raw outcome of one pytest invocation."""

    __test__ = False  # not a pytest test class

    exit_code: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    results: Dict[str, str] = field(default_factory=dict)
    duration: float = 0.0
    timed_out: bool = False
    output: str = ""
    command: List[str] = field(default_factory=list)
    status: str = "ok"

    def test_ids(self, wanted_status: str = "PASSED") -> List[str]:
        return [t for t, s in self.results.items() if s == wanted_status]

    def to_dict(self) -> Dict[str, object]:
        return {
            "exit_code": self.exit_code,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "results": dict(self.results),
            "duration_seconds": round(self.duration, 2),
            "timed_out": self.timed_out,
            "status": self.status,
            "command": " ".join(self.command),
        }


@dataclass
class Grade:
    """Resolution verdict for one task attempt."""

    resolved: bool = False
    status: str = "unresolved"
    f2p_total: int = 0
    f2p_passed: int = 0
    f2p_missing: List[str] = field(default_factory=list)
    p2p_total: int = 0
    p2p_regressed: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "resolved": self.resolved,
            "status": self.status,
            "f2p_total": self.f2p_total,
            "f2p_passed": self.f2p_passed,
            "f2p_missing": self.f2p_missing,
            "p2p_total": self.p2p_total,
            "p2p_regressed": self.p2p_regressed,
            "detail": self.detail,
        }


def _match_test(report_id: str, wanted: str) -> bool:
    """Match a dataset test id against a pytest-reported id, tolerantly."""
    if not report_id or not wanted:
        return False
    if report_id == wanted:
        return True
    r_tail = report_id.split("::")[-1]
    w_tail = wanted.split("::")[-1]
    if r_tail == w_tail:
        return True
    return report_id.endswith(wanted) or wanted.endswith(report_id)


class TestGrader:
    """Runs the repository's own test suite in the task workspace."""

    __test__ = False  # not a pytest test class

    def __init__(
        self,
        python_exe: Optional[str] = None,
        timeout: int = 300,
        extra_args: Optional[Sequence[str]] = None,
    ):
        self.python_exe = python_exe or sys.executable
        self.timeout = timeout
        self.extra_args = list(extra_args or [])

    def build_command(self, workspace: TaskWorkspace, targets: List[str]) -> List[str]:
        python = workspace.python_exe or self.python_exe
        cmd = [
            python, "-m", "pytest",
            "-q", "-rA", "--tb=line", "-p", "no:cacheprovider", "--no-header",
            "-o", "addopts=",
        ]
        cmd += self.extra_args
        if targets:
            cmd += targets
        return cmd

    def env_for(self, workspace: TaskWorkspace, task_id: str = "") -> Dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_CURRENT_TEST")}
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(workspace.root) + (os.pathsep + existing if existing else "")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["NO_COLOR"] = "1"
        env["PY_COLORS"] = "0"
        env["COLUMNS"] = "120"
        if task_id:
            env["BENCH_TASK_ID"] = task_id
        return env

    def run(
        self,
        workspace: TaskWorkspace,
        task: Optional[object] = None,
        targets: Optional[List[str]] = None,
    ) -> TestRun:
        task_id = getattr(task, "id", "") or ""
        chosen = targets if targets is not None else self._default_targets(workspace, task)
        cmd = self.build_command(workspace, chosen)
        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace.root),
                env=self.env_for(workspace, task_id),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
            return self._parse(proc.returncode, proc.stdout + proc.stderr, cmd, time.time() - start)
        except subprocess.TimeoutExpired as exc:
            output = ((exc.stdout or b"") if isinstance(exc.stdout, bytes) else exc.stdout or "") or ""
            run = self._parse(124, str(output) + f"\n[bench] pytest timed out after {self.timeout}s", cmd, time.time() - start)
            run.timed_out = True
            run.status = "timeout"
            return run
        except FileNotFoundError as exc:
            run = TestRun(exit_code=127, status="python_missing", command=cmd, output=str(exc))
            agent_logger.warning(f"[BENCH] Interpreter missing: {exc}")
            return run

    def _default_targets(self, workspace: TaskWorkspace, task: Optional[object]) -> List[str]:
        explicit = list(getattr(task, "test_targets", []) or [])
        node_ids = list(getattr(task, "fail_to_pass", []) or []) + list(getattr(task, "pass_to_pass", []) or [])
        if explicit and all("::" not in t and not t.endswith(".py") for t in explicit):
            explicit = [f"{t.rstrip('/')}/" for t in explicit]
        if node_ids and all("::" in nid for nid in node_ids):
            return node_ids
        if explicit:
            return explicit
        for candidate in ("tests", "test"):
            if (workspace.root / candidate).is_dir():
                return [candidate]
        return []

    def _parse(self, exit_code: int, output: str, cmd: List[str], duration: float) -> TestRun:
        run = TestRun(exit_code=exit_code, output=output[-40_000:], duration=duration, command=list(cmd))
        lower = output.lower()
        for line in output.splitlines():
            match = STATUS_LINE.match(line.strip())
            if match:
                status, test_id = match.group(1), match.group(2)
                run.results[test_id] = status
        for line in reversed(output.splitlines()):
            summary = SUMMARY_LINE.findall(line)
            if summary and (" in " in line or "passed" in line or "failed" in line):
                for count, word in summary:
                    if word == "passed":
                        run.passed = max(run.passed, int(count))
                    elif word == "failed":
                        run.failed = max(run.failed, int(count))
                    elif word in ("error", "errors"):
                        run.errors = max(run.errors, int(count))
                    elif word == "skipped":
                        run.skipped = max(run.skipped, int(count))
                break
        if not run.results:
            if any(marker in lower for marker in NO_TESTS_MARKERS) and exit_code != 0:
                run.status = "no_tests_collected"
            elif "modulenotfounderror" in lower and "no module named 'pytest'" in lower:
                run.status = "pytest_missing"
            elif "modulenotfounderror" in lower or "importerror" in lower:
                run.status = "collection_error"
        return run

    def grade(self, task: object, baseline: TestRun, final: TestRun) -> Grade:
        f2p = list(getattr(task, "fail_to_pass", []) or [])
        p2p = list(getattr(task, "pass_to_pass", []) or [])

        if final.status in ("python_missing", "pytest_missing"):
            return Grade(status="grader_error", detail=f"{final.status}: cannot execute tests")
        if final.timed_out:
            return Grade(status="grader_error", detail="pytest timed out")

        f2p_missing: List[str] = []
        f2p_passed = 0
        for wanted in f2p:
            matched = any(
                _match_test(reported, wanted) and status == "PASSED"
                for reported, status in final.results.items()
            )
            if matched:
                f2p_passed += 1
            else:
                f2p_missing.append(wanted)

        regressions: List[str] = []
        for wanted in p2p:
            was_passing = any(_match_test(r, wanted) and s == "PASSED" for r, s in baseline.results.items())
            still_passing = any(_match_test(r, wanted) and s == "PASSED" for r, s in final.results.items())
            if was_passing and not still_passing:
                regressions.append(wanted)

        grade = Grade(
            f2p_total=len(f2p),
            f2p_passed=f2p_passed,
            f2p_missing=f2p_missing,
            p2p_total=len(p2p),
            p2p_regressed=regressions,
        )

        if f2p:
            grade.resolved = f2p_passed == len(f2p) and not regressions
            grade.status = "resolved" if grade.resolved else "unresolved"
            grade.detail = f"f2p {f2p_passed}/{len(f2p)} passed, {len(regressions)} p2p regression(s)"
        else:
            no_failures = final.exit_code == 0 and final.failed == 0 and final.errors == 0
            if not final.results and final.passed == 0:
                grade.status = "grader_error" if final.status != "ok" else "no_tests"
                grade.detail = f"no tests executed (status={final.status}, exit={final.exit_code})"
            else:
                grade.resolved = no_failures and not regressions
                grade.status = "resolved" if grade.resolved else "unresolved"
                grade.detail = (
                    f"suite exit={final.exit_code} passed={final.passed} failed={final.failed} "
                    f"errors={final.errors} (no F2P list supplied; whole-suite gate)"
                )
        return grade
