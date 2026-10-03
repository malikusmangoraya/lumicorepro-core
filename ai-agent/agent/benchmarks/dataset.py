"""Dataset discovery + task normalisation for the offline public-development benchmark.

The benchmark corpus ships as a directory bundle:

    <data>/tasks.jsonl          129 real GitHub bug-fixing tasks
    <data>/snapshots/*.tgz      frozen working trees (FastAPI, Rich, requests, httpx, ...)
    <data>/graphs/*.json        AST call + dependency graphs
    <data>/embeddings/*         node embedding vectors
    <data>/wheels/*.whl         offline evaluation wheels (adk_eval_core)
    <data>/HARNESS_README*      official harness notes

Real-world task files never share one exact schema, so every field is resolved
through a candidate-key probe (`problem_statement` / `issue` / `description` /
...). Unknown extra keys are preserved on `raw` so nothing is silently dropped.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from utils.logger import agent_logger

TASK_FILE_NAMES = ("tasks.jsonl", "tasks.json", "instances.jsonl", "instances.json")
SNAPSHOT_DIR_NAMES = ("snapshots", "snapshot", "repos", "repo_snapshots", "workspaces")
GRAPH_DIR_NAMES = ("graphs", "graph", "code_graphs", "ast_graphs")
EMBEDDING_DIR_NAMES = ("embeddings", "embedding", "node_embeddings", "vectors")
WHEEL_DIR_NAMES = ("wheels", "wheelhouse", "eval_wheels", "evaluation_wheels")
HARNESS_FILE_PATTERNS = ("HARNESS_README", "harness_readme", "README_HARNESS")


# ── Key probes (ordered: first hit wins) ─────────────────────────────────────
KEY_ID = ("id", "task_id", "instance_id", "instance", "name", "slug")
KEY_REPO = ("repo", "repository", "repo_name", "repo_slug", "project", "source_repo", "git_repo")
KEY_ISSUE = (
    "problem_statement", "issue", "issue_text", "description", "bug_report",
    "task", "prompt", "instructions", "user_report", "body",
)
KEY_BASE_COMMIT = ("base_commit", "base_commit_hash", "commit", "base_rev", "commit_sha", "sha")
KEY_GOLD_PATCH = ("patch", "gold_patch", "solution", "solution_patch", "reference_patch", "model_patch", "diff")
KEY_TEST_PATCH = ("test_patch", "tests_patch", "test_diff", "tests", "test_files", "grader_patch")
KEY_F2P = ("FAIL_TO_PASS", "fail_to_pass", "f2p", "fail_to_pass_tests", "target_tests")
KEY_P2P = ("PASS_TO_PASS", "pass_to_pass", "p2p", "pass_to_pass_tests", "regression_tests")
KEY_SNAPSHOT = ("snapshot", "snapshot_path", "snapshot_id", "archive", "tarball", "tgz", "repo_archive", "path")
KEY_LANGUAGE = ("language", "repo_language", "lang", "programming_language")
KEY_SETUP = ("setup_cmd", "setup", "install", "install_cmd", "prepare_cmd", "build_cmd")
KEY_TEST_TARGETS = ("test_targets", "tests_to_run", "test_paths", "test_files", "test_cmd", "run_tests")
KEY_REQS = ("requirements", "requirements_txt", "deps", "dependencies", "pyproject")

SNAPSHOT_EXTS = (".tgz", ".tar.gz", ".tar", ".tar.xz", ".tbz2")


def _first(record: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(v) for v in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {_as_text(v)}" for k, v in value.items())
    return str(value)


def _as_list(value: Any) -> List[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(v) for v in value.values()]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


def slugify(value: str) -> str:
    """Normalise a repo / task name to a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "")).strip("-").lower()
    return slug or "unknown"


@dataclass
class BenchmarkTask:
    """One normalised real-world bug-fixing task."""

    id: str
    repo: str
    issue: str
    base_commit: str = ""
    gold_patch: str = ""
    test_patch: str = ""
    fail_to_pass: List[str] = field(default_factory=list)
    pass_to_pass: List[str] = field(default_factory=list)
    snapshot: str = ""
    language: str = "python"
    setup_cmd: str = ""
    test_targets: List[str] = field(default_factory=list)
    requirements: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    # ── derived ──────────────────────────────────────────────────────────────
    @property
    def repo_slug(self) -> str:
        return slugify(self.repo)

    @property
    def has_gold_patch(self) -> bool:
        return bool(self.gold_patch.strip())

    @property
    def has_test_patch(self) -> bool:
        return bool(self.test_patch.strip())

    def gradeable(self) -> bool:
        """A task is gradeable when it carries tests to run or a test patch."""
        return bool(self.has_test_patch or self.fail_to_pass or self.test_targets)

    def leakage_keys(self) -> List[str]:
        """Keys that must never reach the solver (reference solution leakage)."""
        return [k for k in (KEY_GOLD_PATCH + KEY_F2P) if k in self.raw]

    @classmethod
    def from_record(cls, record: Dict[str, Any], index: int = 0) -> "BenchmarkTask":
        repo = _as_text(_first(record, KEY_REPO, "")) or "unknown-repo"
        task_id = _as_text(_first(record, KEY_ID, "")) or f"{slugify(repo)}-{index:03d}"
        return cls(
            id=task_id,
            repo=repo,
            issue=_as_text(_first(record, KEY_ISSUE, "")),
            base_commit=_as_text(_first(record, KEY_BASE_COMMIT, "")),
            gold_patch=_as_text(_first(record, KEY_GOLD_PATCH, "")),
            test_patch=_as_text(_first(record, KEY_TEST_PATCH, "")),
            fail_to_pass=_as_list(_first(record, KEY_F2P, [])),
            pass_to_pass=_as_list(_first(record, KEY_P2P, [])),
            snapshot=_as_text(_first(record, KEY_SNAPSHOT, "")),
            language=_as_text(_first(record, KEY_LANGUAGE, "python")) or "python",
            setup_cmd=_as_text(_first(record, KEY_SETUP, "")),
            test_targets=_as_list(_first(record, KEY_TEST_TARGETS, [])),
            requirements=_as_text(_first(record, KEY_REQS, "")),
            raw=dict(record),
        )


def _read_task_file(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        payload = json.loads(text)
        if isinstance(payload, dict):
            payload = payload.get("tasks") or payload.get("instances") or payload.get("data") or []
        if isinstance(payload, list):
            records = [r for r in payload if isinstance(r, dict)]
    else:
        for lineno, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                agent_logger.warning(f"[BENCH] {path.name}:{lineno} skipped ({exc})")
                continue
            if isinstance(row, dict):
                if "tasks" in row and isinstance(row["tasks"], list):
                    records.extend(r for r in row["tasks"] if isinstance(r, dict))
                else:
                    records.append(row)
    return records


def _first_existing_dir(root: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        candidate = root / name
        if candidate.is_dir():
            return candidate
    return None


def _find_harness_readme(root: Path) -> Optional[Path]:
    for pattern in HARNESS_FILE_PATTERNS:
        for path in sorted(root.glob(f"{pattern}*")):
            if path.is_file():
                return path
    return None


def _find_artifact(directory: Optional[Path], slug: str, names: Iterable[str]) -> Optional[Path]:
    """Locate `<slug>.<name>` or `<slug>/<name>` inside an artifact directory."""
    if not directory or not directory.is_dir():
        return None
    for name in names:
        direct = directory / f"{slug}.{name}"
        if direct.is_file():
            return direct
        nested = directory / slug / name
        if nested.is_file():
            return nested
    for ext in (".json", ".jsonl", ".npy", ".npz"):
        candidate = directory / f"{slug}{ext}"
        if candidate.is_file():
            return candidate
    return None


def default_data_dir() -> Path:
    """Resolve the dataset root from env, then well-known locations."""
    from config.settings import BENCH_DATA_DIR, PROJECT_ROOT, AI_AGENT_DIR

    if os.getenv("BENCH_DATA_DIR"):
        return Path(os.getenv("BENCH_DATA_DIR")).expanduser().resolve()
    if BENCH_DATA_DIR and Path(BENCH_DATA_DIR).is_dir():
        return Path(BENCH_DATA_DIR)

    candidates = [
        PROJECT_ROOT / "benchmarks-data",
        PROJECT_ROOT / "benchmark-data",
        PROJECT_ROOT / "data" / "benchmarks",
        PROJECT_ROOT / ".bench",
        PROJECT_ROOT / "generated-projects" / "bench-data",
        AI_AGENT_DIR / "benchmarks-data",
        AI_AGENT_DIR.parent / "public-dev-benchmark",
        Path.cwd() / "benchmarks-data",
        Path.cwd(),
    ]
    for candidate in candidates:
        try:
            if candidate.is_dir() and any((candidate / n).is_file() for n in TASK_FILE_NAMES):
                return candidate.resolve()
        except OSError:
            continue
    return PROJECT_ROOT / "benchmarks-data"


class BenchmarkDataset:
    """A loaded, validated benchmark corpus."""

    def __init__(self, root: Path, tasks: List[BenchmarkTask]):
        self.root = Path(root).resolve()
        self.tasks = tasks
        self.tasks_file = self._locate_tasks_file()
        self.snapshots_dir = _first_existing_dir(self.root, SNAPSHOT_DIR_NAMES)
        self.graphs_dir = _first_existing_dir(self.root, GRAPH_DIR_NAMES)
        self.embeddings_dir = _first_existing_dir(self.root, EMBEDDING_DIR_NAMES)
        self.wheels_dir = _first_existing_dir(self.root, WHEEL_DIR_NAMES)
        self.harness_readme = _find_harness_readme(self.root)

    # ── loading ──────────────────────────────────────────────────────────────
    @classmethod
    def load(cls, root: Optional[Path] = None) -> "BenchmarkDataset":
        root = Path(root).resolve() if root else default_data_dir()
        if not root.is_dir():
            return cls(root, [])
        tasks_file = next((root / n for n in TASK_FILE_NAMES if (root / n).is_file()), None)
        tasks: List[BenchmarkTask] = []
        if tasks_file:
            for index, record in enumerate(_read_task_file(tasks_file)):
                tasks.append(BenchmarkTask.from_record(record, index))
        else:
            agent_logger.warning(f"[BENCH] No task file under {root} (looked for {TASK_FILE_NAMES})")
        return cls(root, tasks)

    def _locate_tasks_file(self) -> Optional[Path]:
        for name in TASK_FILE_NAMES:
            candidate = self.root / name
            if candidate.is_file():
                return candidate
        return None

    # ── per-task artifact resolution ─────────────────────────────────────────
    def snapshot_archive(self, task: BenchmarkTask) -> Optional[Path]:
        """Find the `.tgz` working tree for a task (explicit field, then slug/id)."""
        if not self.snapshots_dir:
            return None
        if task.snapshot:
            raw = task.snapshot
            candidate = Path(raw)
            if candidate.is_file():
                return candidate
            for ext in SNAPSHOT_EXTS:
                for name in (f"{slugify(raw)}{ext}", f"{raw}{ext}"):
                    probe = self.snapshots_dir / name
                    if probe.is_file():
                        return probe
        for key in (task.repo_slug, slugify(task.id), task.id, task.repo):
            for ext in SNAPSHOT_EXTS:
                probe = self.snapshots_dir / f"{key}{ext}"
                if probe.is_file():
                    return probe
        return None

    def graph_file(self, task: BenchmarkTask) -> Optional[Path]:
        return _find_artifact(
            self.graphs_dir, task.repo_slug, ("graph.json", "code_graph.json", "ast_graph.json", "graph.jsonl")
        )

    def embedding_file(self, task: BenchmarkTask) -> Optional[Path]:
        return _find_artifact(
            self.embeddings_dir,
            task.repo_slug,
            ("embeddings.npy", "embeddings.npz", "embeddings.json", "nodes.json", "index.json"),
        )

    # ── reporting ────────────────────────────────────────────────────────────
    def snapshot_count(self) -> int:
        if not self.snapshots_dir:
            return 0
        return sum(1 for p in self.snapshots_dir.iterdir() if p.is_file() and p.name.endswith(SNAPSHOT_EXTS))

    def stats(self) -> Dict[str, Any]:
        with_snapshot = sum(1 for t in self.tasks if self.snapshot_archive(t))
        return {
            "root": str(self.root),
            "root_exists": self.root.is_dir(),
            "tasks_file": str(self.tasks_file) if self.tasks_file else None,
            "tasks": len(self.tasks),
            "repos": len({t.repo_slug for t in self.tasks}),
            "gradeable_tasks": sum(1 for t in self.tasks if t.gradeable()),
            "tasks_with_snapshot": with_snapshot,
            "tasks_with_gold_patch": sum(1 for t in self.tasks if t.has_gold_patch),
            "tasks_with_test_patch": sum(1 for t in self.tasks if t.has_test_patch),
            "snapshots_dir": str(self.snapshots_dir) if self.snapshots_dir else None,
            "snapshots": self.snapshot_count(),
            "graphs_dir": str(self.graphs_dir) if self.graphs_dir else None,
            "graphs": sum(1 for _ in self.graphs_dir.iterdir()) if self.graphs_dir and self.graphs_dir.is_dir() else 0,
            "embeddings_dir": str(self.embeddings_dir) if self.embeddings_dir else None,
            "embeddings": (
                sum(1 for _ in self.embeddings_dir.iterdir())
                if self.embeddings_dir and self.embeddings_dir.is_dir()
                else 0
            ),
            "wheels_dir": str(self.wheels_dir) if self.wheels_dir else None,
            "wheels": (
                sum(1 for p in self.wheels_dir.glob("*.whl"))
                if self.wheels_dir and self.wheels_dir.is_dir()
                else 0
            ),
            "harness_readme": str(self.harness_readme) if self.harness_readme else None,
        }

    def select(
        self,
        limit: Optional[int] = None,
        repos: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
    ) -> List[BenchmarkTask]:
        tasks = list(self.tasks)
        if repos:
            wanted = {slugify(r) for r in repos}
            tasks = [t for t in tasks if t.repo_slug in wanted or t.repo in repos]
        if task_ids:
            wanted_ids = set(task_ids)
            tasks = [t for t in tasks if t.id in wanted_ids or slugify(t.id) in {slugify(i) for i in wanted_ids}]
        # `limit` 0/None means "no cap" — the CLI documents `--limit 0` as all
        # tasks, and slicing with 0 would silently select nothing.
        if limit is not None and limit > 0:
            tasks = tasks[:limit]
        return tasks
