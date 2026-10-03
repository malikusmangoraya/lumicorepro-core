"""Offline public-development benchmark harness.

Grades a coding agent on real bug-fixing tasks shipped as a local corpus:

    tasks.jsonl   issue text + gold patch + test patch
    snapshots/    frozen git working trees (*.tgz)
    graphs/       per-repo AST call + dependency graphs
    embeddings/   per-repo node vectors
    wheels/       offline evaluation wheels

Everything runs offline. Typical use:

    python -m agent.benchmarks doctor
    python -m agent.benchmarks list --limit 10
    python -m agent.benchmarks run --solver ai --jobs 4
    python -m agent.benchmarks run --solver noop     # grader sanity check
"""

from .code_graph import CodeGraph, GraphNode
from .context import ContextBundle, assert_no_leakage, build_context
from .dataset import BenchmarkDataset, BenchmarkTask
from .embeddings import CodeSearch, LexicalIndex, NodeEmbeddings
from .grader import Grade, TestGrader, TestRun
from .report import build_report, render_markdown, write_report
from .runner import BenchmarkRunner, TaskRun
from .snapshots import GitRepo, SnapshotStore, safe_extract
from .solvers import AiPatchSolver, NoOpSolver, ScriptedSolver, SolveResult, Solver
from .workspace import TaskWorkspace, WorkspaceManager

__all__ = [
    "BenchmarkDataset",
    "BenchmarkTask",
    "BenchmarkRunner",
    "TaskRun",
    "TaskWorkspace",
    "WorkspaceManager",
    "SnapshotStore",
    "GitRepo",
    "safe_extract",
    "CodeGraph",
    "GraphNode",
    "CodeSearch",
    "NodeEmbeddings",
    "LexicalIndex",
    "ContextBundle",
    "build_context",
    "assert_no_leakage",
    "Solver",
    "SolveResult",
    "NoOpSolver",
    "ScriptedSolver",
    "AiPatchSolver",
    "TestGrader",
    "TestRun",
    "Grade",
    "build_report",
    "render_markdown",
    "write_report",
]
