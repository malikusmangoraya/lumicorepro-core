"""Benchmark runner: prepare → baseline → context → solve → grade → record.

Per task the harness does, in this exact order:

1. extract the frozen snapshot into a disposable git checkout
2. apply `test_patch` and run the suite to learn the *baseline* failures
3. reset the tree back to pristine (so the solver never sees the grader's tests)
4. build the context bundle (embeddings/graph) and assert zero reference leakage
5. let the solver mutate the tree
6. capture the candidate diff, re-apply it onto a clean tree, apply `test_patch`
7. run the suite again and grade resolution
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from utils.logger import agent_logger

from .code_graph import CodeGraph
from .context import assert_no_leakage, build_context
from .dataset import BenchmarkDataset, BenchmarkTask
from .embeddings import CodeSearch
from .grader import Grade, TestGrader, TestRun
from .solvers import AiPatchSolver, NoOpSolver, SolveResult, Solver
from .workspace import TaskWorkspace, WorkspaceManager

ProgressFn = Optional[Callable[["TaskRun", int, int], None]]


@dataclass
class TaskRun:
    """Everything measured about one task attempt."""

    task_id: str
    repo: str
    phase: str = "pending"
    status: str = "pending"
    resolved: bool = False
    detail: str = ""
    leakage: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    solve: Dict[str, Any] = field(default_factory=dict)
    baseline: Dict[str, Any] = field(default_factory=dict)
    final: Dict[str, Any] = field(default_factory=dict)
    grade: Dict[str, Any] = field(default_factory=dict)
    patch_bytes: int = 0
    seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo": self.repo,
            "phase": self.phase,
            "status": self.status,
            "resolved": self.resolved,
            "detail": self.detail,
            "leakage": self.leakage,
            "context": self.context,
            "solve": self.solve,
            "baseline": self.baseline,
            "final": self.final,
            "grade": self.grade,
            "patch_bytes": self.patch_bytes,
            "seconds": round(self.seconds, 2),
        }


class BenchmarkRunner:
    """Executes the benchmark for a dataset + solver, offline."""

    def __init__(
        self,
        dataset: BenchmarkDataset,
        manager: WorkspaceManager,
        solver: Optional[Solver] = None,
        grader: Optional[TestGrader] = None,
        keep_workspaces: bool = False,
        max_context_chars: int = 24_000,
    ):
        self.dataset = dataset
        self.manager = manager
        self.solver: Solver = solver or NoOpSolver()
        self.grader = grader or TestGrader()
        self.keep_workspaces = keep_workspaces
        self.max_context_chars = max_context_chars
        self._search_cache: Dict[str, CodeSearch] = {}

    # ── intelligence (cached per repo) ───────────────────────────────────────
    def intelligence_for(self, task: BenchmarkTask) -> CodeSearch:
        if task.repo_slug in self._search_cache:
            return self._search_cache[task.repo_slug]
        graph = CodeGraph.load(self.dataset.graph_file(task))
        search = CodeSearch.build(self.dataset.embedding_file(task), graph)
        self._search_cache[task.repo_slug] = search
        return search

    # ── single task ──────────────────────────────────────────────────────────
    def run_task(self, task: BenchmarkTask) -> TaskRun:
        started = time.time()
        run = TaskRun(task_id=task.id, repo=task.repo)

        archive = self.dataset.snapshot_archive(task)
        if archive is None:
            run.phase, run.status, run.detail = "prepare", "error:no_snapshot", (
                f"no .tgz snapshot resolved for repo '{task.repo}' under "
                f"{self.dataset.snapshots_dir or '<no snapshots dir>'}"
            )
            run.seconds = time.time() - started
            return run

        try:
            workspace = self.manager.create(task.id, archive)
        except Exception as exc:
            run.phase, run.status, run.detail = "prepare", "error:snapshot_extract", str(exc)[:300]
            run.seconds = time.time() - started
            return run

        try:
            return self._run_in_workspace(task, workspace, run, started)
        finally:
            if not self.keep_workspaces:
                self.manager.discard(workspace)

    def _run_in_workspace(
        self,
        task: BenchmarkTask,
        workspace: TaskWorkspace,
        run: TaskRun,
        started: float,
    ) -> TaskRun:
        # ── 1. baseline with the grader's own tests ──────────────────────────
        if task.has_test_patch:
            applied = workspace.apply_patch(task.test_patch)
            if not applied.ok:
                run.phase, run.status = "baseline", "error:test_patch_unapplicable"
                run.detail = (applied.stderr or applied.stdout or "test_patch rejected").strip()[:300]
                run.seconds = time.time() - started
                return run
        baseline = self.grader.run(workspace, task)
        run.baseline = baseline.to_dict()
        workspace.reset()

        # ── 2. context + leakage guard ───────────────────────────────────────
        search = self.intelligence_for(task)
        graph = search.graph
        bundle = build_context(
            task,
            workspace,
            search=search,
            graph=graph,
            max_context_chars=self.max_context_chars,
        )
        run.context = bundle.to_dict()
        run.leakage = assert_no_leakage(bundle, task)
        if run.leakage:
            run.phase, run.status = "context", "error:reference_leakage"
            run.detail = f"{len(run.leakage)} reference fragment(s) reached the solver"
            run.seconds = time.time() - started
            return run

        # ── 3. solve ─────────────────────────────────────────────────────────
        try:
            result: SolveResult = self.solver.solve(task, workspace, bundle)
        except Exception as exc:
            run.phase, run.status, run.detail = "solve", "error:solver_crash", str(exc)[:300]
            run.seconds = time.time() - started
            return run
        run.solve = result.to_dict()

        # A solver that *declines* (no-op baseline, empty scripted patch) is a
        # legitimate measurement: it must be graded so the F2P set fails and the
        # task reports `unresolved`. Only a solver that tried and failed (provider
        # outage, unapplicable diff) is a harness `error`.
        if not result.applied and not result.declined:
            run.phase, run.status = "solve", "error:no_patch"
            run.detail = result.error or "solver produced no applicable patch"
            run.seconds = time.time() - started
            return run

        # ── 4. re-apply solver diff on a clean tree, then the test patch ──────
        candidate = "" if result.declined else (workspace.capture_patch() or result.patch)
        run.patch_bytes = len(candidate.encode("utf-8", errors="replace"))
        if not candidate.strip():
            run.phase = "grade"  # declined: grade the pristine tree as-is
        else:
            workspace.reset()
            replay = workspace.apply_patch(candidate)
            if not replay.ok:
                run.phase, run.status = "replay", "error:patch_not_replayable"
                run.detail = (replay.stderr or "candidate diff did not re-apply").strip()[:300]
                run.seconds = time.time() - started
                return run

        if task.has_test_patch:
            graded = workspace.apply_patch(task.test_patch)
            if not graded.ok:
                run.phase, run.status = "replay", "error:test_patch_conflict"
                run.detail = "grader test_patch conflicts with the candidate fix"
                run.seconds = time.time() - started
                return run

        # ── 5. grade ─────────────────────────────────────────────────────────
        final = self.grader.run(workspace, task)
        run.final = final.to_dict()
        grade: Grade = self.grader.grade(task, baseline, final)
        run.grade = grade.to_dict()
        run.phase = "done"
        run.status = grade.status
        run.resolved = grade.resolved
        run.detail = grade.detail
        run.seconds = time.time() - started
        return run

    # ── batch ────────────────────────────────────────────────────────────────
    def run_tasks(self, tasks: List[BenchmarkTask], jobs: int = 1, progress: ProgressFn = None) -> List[TaskRun]:
        results: List[TaskRun] = []
        total = len(tasks)
        if jobs <= 1:
            for index, task in enumerate(tasks, 1):
                run = self.run_task(task)
                results.append(run)
                if progress:
                    progress(run, index, total)
            return results

        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(self.run_task, task): task for task in tasks}
            for index, future in enumerate(as_completed(futures), 1):
                task = futures[future]
                try:
                    run = future.result()
                except Exception as exc:  # a crashed task must not kill the batch
                    run = TaskRun(
                        task_id=task.id,
                        repo=task.repo,
                        phase="run",
                        status="error:runner_crash",
                        detail=str(exc)[:300],
                    )
                results.append(run)
                if progress:
                    progress(run, index, total)
        order = {task.id: i for i, task in enumerate(tasks)}
        results.sort(key=lambda r: order.get(r.task_id, 10_000))
        return results


def build_ai_solver(provider: Any = None, max_attempts: int = 3) -> Solver:
    return AiPatchSolver(provider=provider, max_attempts=max_attempts)


def default_workspaces_dir() -> Path:
    from config.settings import BENCH_WORKSPACES_DIR

    return Path(BENCH_WORKSPACES_DIR)
