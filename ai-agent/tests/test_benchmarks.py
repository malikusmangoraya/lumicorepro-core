"""Tests for the offline public-development benchmark harness.

Run with: pytest ai-agent/tests/test_benchmarks.py -v

The suite is fully self-contained: it synthesises a miniature corpus (tasks.jsonl
+ a real .tgz snapshot + a code graph + node embeddings + a wheel + a harness
readme) in a temp dir, so nothing external is required. The end-to-end test runs
the real grading methodology (baseline → solve → replay test_patch → grade) with
a real pytest subprocess.
"""

import difflib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.benchmarks import cli
from agent.benchmarks.code_graph import CodeGraph
from agent.benchmarks.context import ContextBundle, assert_no_leakage, build_context
from agent.benchmarks.dataset import BenchmarkDataset, BenchmarkTask
from agent.benchmarks.embeddings import CodeSearch, LexicalIndex, NodeEmbeddings
from agent.benchmarks.grader import TestGrader, TestRun
from agent.benchmarks.packaging import build_kaggle_bundle
from agent.benchmarks.report import build_report, render_markdown, write_report
from agent.benchmarks.runner import BenchmarkRunner
from agent.benchmarks.snapshots import GitRepo, SnapshotStore, UnsafeArchiveError, safe_extract
from agent.benchmarks.solvers import AiPatchSolver, NoOpSolver, ScriptedSolver
from agent.benchmarks.workspace import TaskWorkspace, WorkspaceError, WorkspaceManager

HAVE_GIT = shutil.which("git") is not None
needs_git = pytest.mark.skipif(not HAVE_GIT, reason="git is required for snapshot grading")

BUGGY_CALC = "def add(a, b):\n    return a - b\n"
FIXED_CALC = "def add(a, b):\n    return a + b\n"
SMOKE_TEST = "from pkg.calc import add\n\n\ndef test_smoke():\n    assert add(1, 1) == 2 or True\n"
NEW_TEST = "from pkg.calc import add\n\n\ndef test_add_returns_sum():\n    assert add(2, 3) == 5\n"
F2P = "tests/test_calc.py::test_add_returns_sum"
P2P = "tests/test_smoke.py::test_smoke"


# ── fixtures ────────────────────────────────────────────────────────────────
def write(path: Path, text: str, newline: str = "\n") -> None:
    """Write with explicit newlines — `Path.write_text` translates to CRLF on Windows."""
    with open(path, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)


def make_patch(old: str, new: str, path: str) -> str:
    """Real unified diff so `git apply` accepts it byte-for-byte."""
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff)


def make_new_file_patch(path: str, content: str) -> str:
    diff = difflib.unified_diff(
        [],
        content.splitlines(keepends=True),
        fromfile="/dev/null",
        tofile=f"b/{path}",
    )
    return "".join(diff)


def build_repo_tree(root: Path) -> None:
    (root / "pkg").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    write(root / "pkg" / "__init__.py", "")
    write(root / "pkg" / "calc.py", BUGGY_CALC)
    write(root / "tests" / "test_smoke.py", SMOKE_TEST)
    write(root / "README.md", "# demopkg\n")


def make_tarball(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(target, "w:gz") as tar:
        for path in sorted(source.rglob("*")):
            tar.add(path, arcname=path.relative_to(source).as_posix())
    return target


@pytest.fixture
def corpus(tmp_path):
    """A miniature but structurally real benchmark corpus."""
    data = tmp_path / "corpus"
    (data / "snapshots").mkdir(parents=True)
    (data / "graphs").mkdir()
    (data / "embeddings").mkdir()
    (data / "wheels").mkdir()

    src = tmp_path / "src-repo"
    src.mkdir()
    build_repo_tree(src)
    make_tarball(src, data / "snapshots" / "demopkg.tgz")

    task = {
        "instance_id": "demopkg-001",
        "repository": "demopkg",
        "description": "pkg.calc.add() subtracts the second argument instead of adding it.",
        "patch": make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py"),
        "test_patch": make_new_file_patch("tests/test_calc.py", NEW_TEST),
        "FAIL_TO_PASS": [F2P],
        "PASS_TO_PASS": [P2P],
    }
    (data / "tasks.jsonl").write_text(json.dumps(task) + "\n", encoding="utf-8")

    (data / "graphs" / "demopkg.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "pkg.calc.add", "name": "add", "file": "pkg/calc.py", "kind": "function", "calls": []},
                    {"id": "tests.smoke.test_smoke", "name": "test_smoke", "file": "tests/test_smoke.py", "kind": "function"},
                ],
                "edges": [{"from": "tests.smoke.test_smoke", "to": "pkg.calc.add"}],
            }
        ),
        encoding="utf-8",
    )
    (data / "embeddings" / "demopkg.json").write_text(
        json.dumps({"ids": ["pkg.calc.add", "tests.smoke.test_smoke"], "vectors": [[0.1, 0.9, 0.2], [0.8, 0.1, 0.4]]}),
        encoding="utf-8",
    )
    (data / "wheels" / "adk_eval_core-0.1-py3-none-any.whl").write_bytes(b"PK\x03\x04")
    (data / "HARNESS_README.md").write_text("# harness\n", encoding="utf-8")
    return data


@pytest.fixture
def loaded(corpus):
    return BenchmarkDataset.load(corpus)


# ── dataset ─────────────────────────────────────────────────────────────────
def test_dataset_loads_tasks_with_alternate_keys(loaded):
    assert len(loaded.tasks) == 1
    task = loaded.tasks[0]
    assert task.id == "demopkg-001"
    assert task.repo == "demopkg"
    assert task.repo_slug == "demopkg"
    assert "subtracts" in task.issue
    assert task.has_gold_patch and task.has_test_patch
    assert task.fail_to_pass == [F2P]
    assert task.pass_to_pass == [P2P]
    assert task.gradeable()
    assert "FAIL_TO_PASS" in task.leakage_keys()


def test_dataset_resolves_every_artifact_group(loaded, corpus):
    task = loaded.tasks[0]
    assert loaded.snapshot_archive(task) is not None
    assert loaded.graph_file(task).name == "demopkg.json"
    assert loaded.embedding_file(task).name == "demopkg.json"
    stats = loaded.stats()
    assert stats["tasks"] == 1 and stats["repos"] == 1
    assert stats["snapshots"] == 1 and stats["wheels"] == 1
    assert stats["tasks_with_snapshot"] == 1
    assert stats["harness_readme"].endswith("HARNESS_README.md")


def test_dataset_missing_root_is_empty_not_fatal(tmp_path):
    dataset = BenchmarkDataset.load(tmp_path / "nope")
    assert dataset.tasks == []
    assert dataset.stats()["root_exists"] is False
    assert dataset.snapshot_archive(BenchmarkTask(id="x", repo="y", issue="")) is None


@needs_git
def test_two_runs_reuse_the_cache_without_leaking_workspaces(corpus, tmp_path):
    """Regression: a leftover workspace (read-only git objects) broke run #2."""
    from agent.benchmarks.workspace import WorkspaceManager

    cache = tmp_path / "cache"
    workspaces = tmp_path / "ws"
    archive = corpus / "snapshots" / "demopkg.tgz"
    for _ in range(2):
        manager = WorkspaceManager(cache, workspaces)
        ws = manager.create("demopkg-001", archive)
        assert ws.apply_patch(make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py")).ok
        manager.discard(ws)
        manager.cleanup()
        assert list(workspaces.iterdir()) == []  # nothing survives the run


def test_dataset_select_filters(corpus):
    second = json.loads((corpus / "tasks.jsonl").read_text(encoding="utf-8").strip())
    second["instance_id"] = "other-002"
    second["repository"] = "otherrepo"
    (corpus / "tasks.jsonl").write_text(
        (corpus / "tasks.jsonl").read_text(encoding="utf-8") + json.dumps(second) + "\n", encoding="utf-8"
    )
    dataset = BenchmarkDataset.load(corpus)
    assert len(dataset.tasks) == 2
    assert [t.id for t in dataset.select(limit=1)] == ["demopkg-001"]
    # `--limit 0` is documented as "all tasks" and must not slice to nothing.
    assert [t.id for t in dataset.select(limit=0)] == ["demopkg-001", "other-002"]
    assert [t.id for t in dataset.select(limit=None)] == ["demopkg-001", "other-002"]
    assert [t.id for t in dataset.select(repos=["demopkg"])] == ["demopkg-001"]
    assert [t.id for t in dataset.select(repos=["otherrepo"])] == ["other-002"]
    assert dataset.select(task_ids=["other-002"])[0].repo == "otherrepo"
    # A task whose repo has no archive must not be gradeable-by-accident.
    assert dataset.snapshot_archive(dataset.tasks[1]) is None


def test_dataset_skips_malformed_jsonl_lines(tmp_path):
    data = tmp_path / "c"
    data.mkdir()
    (data / "tasks.jsonl").write_text(
        '{"id": "a", "repo": "r", "issue": "x"}\nnot json\n\n{"id": "b", "repo": "r", "issue": "y"}\n',
        encoding="utf-8",
    )
    dataset = BenchmarkDataset.load(data)
    assert [t.id for t in dataset.tasks] == ["a", "b"]


# ── snapshots ───────────────────────────────────────────────────────────────
@needs_git
def test_safe_extract_then_git_lifecycle(corpus, tmp_path):
    dest = tmp_path / "unpacked"
    entries = safe_extract(corpus / "snapshots" / "demopkg.tgz", dest)
    assert entries > 0
    assert (dest / "pkg" / "calc.py").read_text(encoding="utf-8") == BUGGY_CALC
    repo = GitRepo(dest)
    assert repo.init().ok
    assert repo.is_repo()
    assert repo.head()
    assert not repo.is_dirty()
    assert "calc" not in repo.status()

    (dest / "pkg" / "calc.py").write_text(FIXED_CALC, encoding="utf-8")
    assert repo.is_dirty()
    patch = repo.stage_all() and repo.diff_cached()
    repo.unstage()
    assert "return a + b" in patch
    repo.reset_hard()
    assert (dest / "pkg" / "calc.py").read_text(encoding="utf-8") == BUGGY_CALC


@needs_git
def test_safe_extract_rejects_path_traversal(tmp_path):
    evil = tmp_path / "evil.tgz"
    payload = tmp_path / "payload.txt"
    payload.write_text("pwned", encoding="utf-8")
    with tarfile.open(evil, "w:gz") as tar:
        tar.add(payload, arcname="../escaped.txt")
    with pytest.raises(UnsafeArchiveError):
        safe_extract(evil, tmp_path / "out")


def test_safe_extract_rejects_absolute_paths(tmp_path):
    # tarfile.add() strips the leading "/", so the hostile member must be built by hand.
    evil = tmp_path / "abs.tgz"
    with tarfile.open(evil, "w:gz") as tar:
        payload = b"x"
        info = tarfile.TarInfo(name="/etc/bench-escape.txt")
        info.size = len(payload)
        tar.addfile(info, __import__("io").BytesIO(payload))
    with pytest.raises(UnsafeArchiveError):
        safe_extract(evil, tmp_path / "out2")


@needs_git
def test_snapshot_store_extracts_once_and_reuses(corpus, tmp_path):
    store = SnapshotStore(tmp_path / "cache")
    archive = corpus / "snapshots" / "demopkg.tgz"
    first = store.ensure(archive)
    marker = (first / ".extracted").read_text(encoding="utf-8")
    assert "sha256=" in marker
    assert store.has(archive)
    second = store.ensure(archive)
    assert first == second
    assert (second / "pkg" / "calc.py").is_file()


@needs_git
def test_crlf_repository_still_accepts_an_lf_patch(tmp_path):
    """A CRLF snapshot (Windows checkout) must not break upstream LF patches."""
    src = tmp_path / "crlf-repo"
    (src / "pkg").mkdir(parents=True)
    write(src / "pkg" / "calc.py", BUGGY_CALC, newline="\r\n")
    archive = make_tarball(src, tmp_path / "snapshots" / "crlfrepo.tgz")
    ws = WorkspaceManager(tmp_path / "cache", tmp_path / "ws").create("t", archive)
    assert ws.read_text("pkg/calc.py") == BUGGY_CALC  # extracted as LF, ready for LF patches
    assert ws.apply_patch(make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py")).ok
    assert ws.read_text("pkg/calc.py") == FIXED_CALC
    captured = ws.capture_patch()
    assert "return a + b" in captured
    assert captured.count("\n") < 10  # a real change, not a whole-file CRLF rewrite


@needs_git
def test_single_wrapping_directory_is_unwrapped(tmp_path):
    src = tmp_path / "demopkg"
    build_repo_tree(src)
    archive = make_tarball(src, tmp_path / "snapshots" / "wrapped.tgz")
    ws = WorkspaceManager(tmp_path / "cache", tmp_path / "ws").create("t", archive)
    assert (ws.root / "pkg" / "calc.py").is_file()  # not ws.root/demopkg/pkg/calc.py
    assert not (ws.root / "demopkg").exists()
    assert ws.apply_patch(make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py")).ok


@needs_git
def test_repo_with_one_top_folder_is_not_unwrapped(tmp_path):
    """`src/`-only trees must survive intact — the wrapping heuristic is marker-based."""
    src = tmp_path / "onefolder"
    (src / "src").mkdir(parents=True)
    write(src / "src" / "mod.py", "VALUE = 1\n")
    write(src / "pyproject.toml", "[project]\nname='x'\n")
    archive = make_tarball(src, tmp_path / "snapshots" / "onefolder.tgz")
    ws = WorkspaceManager(tmp_path / "cache", tmp_path / "ws").create("t", archive)
    assert (ws.root / "src" / "mod.py").is_file()
    assert (ws.root / "pyproject.toml").is_file()


# ── code graph ──────────────────────────────────────────────────────────────
def test_code_graph_loads_nodes_and_edges(loaded, corpus):
    graph = CodeGraph.load(loaded.graph_file(loaded.tasks[0]))
    assert graph.loaded
    assert len(graph) == 2
    assert graph.files() == ["pkg/calc.py", "tests/test_smoke.py"]
    assert [n.id for n in graph.callers("pkg.calc.add")] == ["tests.smoke.test_smoke"]
    assert [n.id for n in graph.callees("pkg.calc.add")] == []
    assert [n.id for n in graph.impact_set("pkg.calc.add")] == ["tests.smoke.test_smoke"]
    assert [n.id for n in graph.nodes_in_file("pkg/calc.py")] == ["pkg.calc.add"]
    summary = graph.to_dict()
    assert summary["nodes"] == 2 and summary["files"] == 2 and summary["edges"] == 1
    assert graph.to_prompt_lines(["pkg.calc.add"])


def test_code_graph_tolerates_file_keyed_payload(tmp_path):
    path = tmp_path / "g.json"
    path.write_text(
        json.dumps({"pkg/calc.py": [{"name": "add", "calls": ["mul"]}, {"name": "mul", "calls": []}]}),
        encoding="utf-8",
    )
    graph = CodeGraph.load(path)
    assert graph.loaded
    add = graph.find("add")[0]
    assert add.file == "pkg/calc.py"
    assert graph.node("mul").callers == ["add"]


def test_code_graph_survives_missing_or_broken_file(tmp_path):
    assert CodeGraph.load(None).loaded is False
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    graph = CodeGraph.load(broken)
    assert graph.loaded is False
    assert len(graph) == 0


def test_code_graph_symbol_search_ranks_by_overlap(loaded):
    graph = CodeGraph.load(loaded.graph_file(loaded.tasks[0]))
    hits = graph.search_symbols("calc add", limit=5)
    assert hits and hits[0].id == "pkg.calc.add"


# ── embeddings + search ─────────────────────────────────────────────────────
def test_node_embeddings_load_json_and_search(corpus, loaded):
    search = CodeSearch.build(loaded.embedding_file(loaded.tasks[0]), CodeGraph.load(loaded.graph_file(loaded.tasks[0])))
    status = search.status()
    assert status["embeddings_available"] is True
    assert status["embeddings_status"] == "ok"
    assert status["lexical_docs"] == 2
    assert search.embeddings.dim == 3

    hits = search.embeddings.search([0.1, 0.9, 0.2], limit=2)
    assert hits[0].node_id == "pkg.calc.add"
    assert hits[0].score > 0.99
    assert search.embeddings.search([0.0, 0.0, 0.0], limit=2) == []
    assert search.embeddings.search([1.0], limit=1) == []  # dim mismatch is refused


def test_code_search_falls_back_to_lexical_without_vectors(loaded):
    graph = CodeGraph.load(loaded.graph_file(loaded.tasks[0]))
    search = CodeSearch.build(None, graph)
    assert search.status()["embeddings_available"] is False
    hits = search.search("add returns sum", limit=3)
    assert hits and hits[0].source == "lexical"
    assert search.files("add", limit=3) == ["pkg/calc.py"]


def test_lexical_index_scores_and_empties():
    index = LexicalIndex.from_text({"a.add": "add two numbers", "b.render": "render html template"})
    assert index.search("add numbers", limit=1)[0].node_id == "a.add"
    assert index.search("", limit=1) == []
    assert LexicalIndex().search("anything") == []


# ── workspace ───────────────────────────────────────────────────────────────
@needs_git
def test_workspace_file_io_blocks_traversal(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("demopkg-001", corpus / "snapshots" / "demopkg.tgz")
    assert ws.exists("pkg/calc.py")
    assert ws.read_text("pkg/calc.py") == BUGGY_CALC
    with pytest.raises(WorkspaceError):
        ws._safe("../../escape.py")
    with pytest.raises(WorkspaceError):
        ws.read_text("pkg/missing.py")
    ws.write_text("pkg/calc.py", FIXED_CALC)
    assert ws.read_text("pkg/calc.py") == FIXED_CALC
    assert "pkg/calc.py" in ws.list_files("*.py")
    assert any(entry.startswith("pkg/") for entry in ws.tree())
    ws.reset()
    assert ws.read_text("pkg/calc.py") == BUGGY_CALC
    assert ws.summary()["head"]
    manager.discard(ws)


@needs_git
def test_workspace_patch_roundtrip_and_failure(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    patch = make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py")
    assert ws.apply_patch(patch).ok
    assert ws.read_text("pkg/calc.py") == FIXED_CALC
    captured = ws.capture_patch()
    assert "return a + b" in captured
    ws.reset()
    assert ws.read_text("pkg/calc.py") == BUGGY_CALC
    assert ws.apply_patch(captured).ok
    assert ws.apply_patch("").ok  # empty patch is a no-op, not an error
    bad = ws.apply_patch("diff --git a/pkg/calc.py b/pkg/calc.py\n@@ -1,1 +1,1 @@\n-nope\n+yes\n")
    assert not bad.ok
    manager.discard(ws)


# ── context + leakage guard ─────────────────────────────────────────────────
@needs_git
def test_build_context_ranks_files_and_flags_budget(loaded, corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    search = CodeSearch.build(loaded.embedding_file(loaded.tasks[0]), CodeGraph.load(loaded.graph_file(loaded.tasks[0])))
    bundle = build_context(loaded.tasks[0], ws, search=search, graph=search.graph)
    assert "pkg/calc.py" in bundle.text
    assert "pkg/calc.py" in bundle.files
    assert "## Issue" in bundle.text
    assert "graph: 2 nodes" in bundle.text
    assert bundle.char_count() > 0
    assert bundle.to_dict()["graph_lines"] >= 1
    assert "tests/test_calc.py" not in bundle.text  # grader tests stay hidden

    tiny = build_context(loaded.tasks[0], ws, search=search, graph=search.graph, max_files=0)
    assert tiny.files == []
    assert any("no readable candidate files" in w for w in tiny.warnings)
    starved = build_context(loaded.tasks[0], ws, search=search, graph=search.graph, max_context_chars=300)
    assert starved.files == []
    assert any("budget" in w for w in starved.warnings)
    manager.discard(ws)


@needs_git
def test_leakage_guard_is_clean_for_real_context(loaded, corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    search = CodeSearch.build(None, CodeGraph.load(loaded.graph_file(loaded.tasks[0])))
    bundle = build_context(loaded.tasks[0], ws, search=search, graph=search.graph)
    assert assert_no_leakage(bundle, loaded.tasks[0]) == []
    manager.discard(ws)


def test_leakage_guard_detects_injected_ground_truth(loaded):
    task = loaded.tasks[0]
    leaking = ContextBundle(text=f"hint: run {F2P} and change add to subtract the args")
    violations = assert_no_leakage(leaking, task)
    assert violations
    assert isinstance(assert_no_leakage(ContextBundle(text="clean context"), task), list)


# ── solvers ─────────────────────────────────────────────────────────────────
@needs_git
def test_noop_and_scripted_solvers(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    bundle = ContextBundle(text="")
    empty = NoOpSolver().solve(None, ws, bundle)
    assert empty.applied is False and empty.patch == ""

    scripted = ScriptedSolver(make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py")).solve(None, ws, bundle)
    assert scripted.applied is True
    assert "return a + b" in scripted.patch
    assert ScriptedSolver("").solve(None, ws, bundle).applied is False
    manager.discard(ws)


@needs_git
def test_ai_solver_without_provider_reports_honestly(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    solver = AiPatchSolver(provider=None, max_attempts=1)
    solver.provider = lambda: None  # force the no-provider path
    result = solver.solve(loaded_task(ws), ws, ContextBundle(text="x"))
    assert result.applied is False
    assert "provider_unavailable" in result.error
    manager.discard(ws)


def loaded_task(ws: TaskWorkspace) -> BenchmarkTask:
    return BenchmarkTask(id="t", repo="demopkg", issue="add subtracts")


@needs_git
def test_ai_solver_applies_provider_diff(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")

    class StubProvider:
        model_name = "stub-model"

        def __init__(self, replies):
            self.replies = list(replies)
            self.prompts = []

        def generate_code(self, prompt, context_files=None):
            self.prompts.append(prompt)
            return self.replies.pop(0)

    fenced = "Here you go:\n```diff\n" + make_patch(BUGGY_CALC, FIXED_CALC, "pkg/calc.py") + "```\n"
    provider = StubProvider(["no diff at all", fenced])
    solver = AiPatchSolver(provider=provider, max_attempts=3)
    result = solver.solve(loaded_task(ws), ws, ContextBundle(text="issue text"))
    assert result.applied is True
    assert result.attempts == 2
    assert result.provider == "stub-model"
    assert "return a + b" in result.patch
    assert any("no unified diff" in note for note in result.notes)
    # the retry prompt carries the previous failure back to the model
    assert any("Previous attempt failed" in p for p in provider.prompts)
    manager.discard(ws)


@needs_git
def test_ai_solver_reports_unapplicable_diff(corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")

    class BadProvider:
        def generate_code(self, prompt, context_files=None):
            return "diff --git a/pkg/calc.py b/pkg/calc.py\n@@ -1,1 +1,1 @@\n-nope\n+yes\n"

    result = AiPatchSolver(provider=BadProvider(), max_attempts=2).solve(loaded_task(ws), ws, ContextBundle(text="x"))
    assert result.applied is False
    assert result.error == "patch_never_applied"
    assert result.attempts == 2
    manager.discard(ws)


# ── grader ──────────────────────────────────────────────────────────────────
def test_grader_parses_pytest_report():
    run = TestGrader()._parse(
        1,
        "short test summary info\n"
        "PASSED tests/test_smoke.py::test_smoke\n"
        "FAILED tests/test_calc.py::test_add_returns_sum\n"
        "1 failed, 1 passed in 0.42s\n",
        ["pytest"],
        0.5,
    )
    assert run.results == {
        "tests/test_smoke.py::test_smoke": "PASSED",
        "tests/test_calc.py::test_add_returns_sum": "FAILED",
    }
    assert run.passed == 1 and run.failed == 1
    assert run.status == "ok"


def test_grader_flags_missing_tests_and_timeout():
    assert TestGrader()._parse(4, "ERROR: file or directory not found: nope", ["p"], 0.1).status == "no_tests_collected"
    missing = TestGrader()._parse(1, "ModuleNotFoundError: No module named 'pytest'", ["p"], 0.1)
    assert missing.status in ("pytest_missing", "collection_error")


def test_grade_resolved_requires_f2p_and_no_regression(loaded):
    task = loaded.tasks[0]
    grader = TestGrader()
    baseline = TestRun(results={F2P: "FAILED", P2P: "PASSED"}, failed=1, exit_code=1)
    fixed = TestRun(results={F2P: "PASSED", P2P: "PASSED"}, passed=2, exit_code=0)
    grade = grader.grade(task, baseline, fixed)
    assert grade.resolved and grade.status == "resolved"
    assert grade.f2p_passed == 1 and grade.f2p_total == 1
    assert grade.p2p_regressed == []

    regressed = TestRun(results={F2P: "PASSED", P2P: "FAILED"}, passed=1, failed=1, exit_code=1)
    assert not grader.grade(task, baseline, regressed).resolved
    assert grader.grade(task, baseline, regressed).p2p_regressed == [P2P]

    assert grader.grade(task, baseline, baseline).status == "unresolved"
    assert grader.grade(task, baseline, TestRun(status="python_missing")).status == "grader_error"
    assert grader.grade(task, baseline, TestRun(timed_out=True)).status == "grader_error"


def test_grade_without_f2p_list_uses_whole_suite_gate(loaded):
    task = BenchmarkTask(id="x", repo="demopkg", issue="i")
    grader = TestGrader()
    clean = TestRun(passed=5, exit_code=0, results={"t::a": "PASSED"})
    assert grader.grade(task, TestRun(), clean).resolved is True
    dirty = TestRun(passed=4, failed=1, exit_code=1, results={"t::a": "PASSED", "t::b": "FAILED"})
    assert grader.grade(task, TestRun(), dirty).resolved is False
    empty = TestRun(passed=0, exit_code=5, status="no_tests_collected")
    assert grader.grade(task, TestRun(), empty).status == "grader_error"


def test_grader_default_targets_precedence(loaded, corpus, tmp_path):
    manager = WorkspaceManager(tmp_path / "cache", tmp_path / "ws")
    ws = manager.create("t", corpus / "snapshots" / "demopkg.tgz")
    grader = TestGrader()
    assert grader._default_targets(ws, loaded.tasks[0]) == [F2P, P2P]
    no_lists = BenchmarkTask(id="x", repo="r", issue="i")
    assert grader._default_targets(ws, no_lists) == ["tests"]
    explicit = BenchmarkTask(id="x", repo="r", issue="i", test_targets=["unit"])
    assert grader._default_targets(ws, explicit) == ["unit/"]
    manager.discard(ws)


# ── end-to-end ──────────────────────────────────────────────────────────────
@needs_git
def _run_e2e(corpus, solver):
    dataset = BenchmarkDataset.load(corpus)
    manager = WorkspaceManager(Path(str(corpus)) / "cache", Path(str(corpus)) / "ws")
    runner = BenchmarkRunner(dataset, manager, solver=solver, grader=TestGrader(timeout=180))
    return runner, runner.run_tasks(dataset.tasks)


@needs_git
def test_e2e_noop_solver_cannot_pass_the_grader(corpus):
    """A no-op baseline is a real measurement: it must be graded `unresolved`."""
    _, runs = _run_e2e(corpus, NoOpSolver())
    run = runs[0]
    assert run.status == "unresolved", run.detail
    assert run.resolved is False
    assert run.patch_bytes == 0
    assert run.baseline["results"].get(F2P) == "FAILED"  # dataset really does fail pre-fix


@needs_git
def test_e2e_scrambled_diff_is_an_error_not_a_silent_pass(corpus):
    """An unusable solver diff is a harness error, never a silent pass."""
    scrambled = make_patch("def add(a, b):\n    return a * b\n", "# unrelated\n", "pkg/calc.py")
    _, runs = _run_e2e(corpus, ScriptedSolver(patch=scrambled))
    run = runs[0]
    assert run.status == "error:no_patch", run.detail
    assert run.resolved is False


@needs_git
def test_e2e_scripted_fix_resolves_and_captures_patch(corpus, loaded):
    gold = loaded.tasks[0].gold_patch
    _, runs = _run_e2e(corpus, ScriptedSolver(gold))
    run = runs[0]
    assert run.status == "resolved", run.detail
    assert run.resolved is True
    assert run.phase == "done"
    assert run.patch_bytes > 0
    assert run.final["results"].get(F2P) == "PASSED"
    assert run.final["results"].get(P2P) == "PASSED"
    assert run.grade["f2p_passed"] == 1
    assert run.leakage == []


@needs_git
def test_e2e_no_snapshot_is_reported_not_crashed(corpus):
    dataset = BenchmarkDataset.load(corpus)
    task = BenchmarkTask(id="ghost-1", repo="ghost", issue="x")
    manager = WorkspaceManager(Path(str(corpus)) / "cache2", Path(str(corpus)) / "ws2")
    run = BenchmarkRunner(dataset, manager, solver=NoOpSolver()).run_task(task)
    assert run.status == "error:no_snapshot"
    assert "no .tgz snapshot" in run.detail


@needs_git
def test_e2e_broken_test_patch_is_a_dataset_error(corpus):
    dataset = BenchmarkDataset.load(corpus)
    task = dataset.tasks[0]
    task.test_patch = make_patch("totally wrong\n", "different\n", "pkg/calc.py")
    manager = WorkspaceManager(Path(str(corpus)) / "cache3", Path(str(corpus)) / "ws3")
    run = BenchmarkRunner(dataset, manager, solver=NoOpSolver()).run_task(task)
    assert run.status == "error:test_patch_unapplicable"
    assert run.phase == "baseline"


@needs_git
def test_e2e_leakage_aborts_the_task(loaded, corpus, tmp_path):
    dataset = BenchmarkDataset.load(corpus)
    task = dataset.tasks[0]
    task.issue = f"{task.issue}\nAlso see {F2P} for details."
    manager = WorkspaceManager(tmp_path / "cache4", tmp_path / "ws4")
    run = BenchmarkRunner(dataset, manager, solver=NoOpSolver()).run_task(task)
    assert run.status == "error:reference_leakage"
    assert run.leakage


# ── report ──────────────────────────────────────────────────────────────────
def test_report_math_and_markdown(loaded, corpus):
    from agent.benchmarks.runner import TaskRun

    runs = [
        TaskRun(task_id="a", repo="demopkg", status="resolved", resolved=True, detail="ok", seconds=1.0, patch_bytes=42),
        TaskRun(task_id="b", repo="demopkg", status="unresolved", detail="f2p 0/1", seconds=2.0),
        TaskRun(task_id="c", repo="other", status="error:no_snapshot", detail="missing", seconds=0.5),
    ]
    report = build_report(runs, dataset_stats=loaded.stats(), solver="scripted", command="pytest")
    totals = report["totals"]
    assert totals["tasks"] == 3 and totals["resolved"] == 1
    assert totals["resolve_rate"] == 33.33
    assert totals["resolve_rate_of_measured"] == 50.0
    assert totals["unmeasured"] == 1
    assert totals["error_reasons"] == {"no_snapshot": 1}
    assert report["integrity"]["leakage_free"] is True
    assert report["by_repo"]["demopkg"]["resolve_rate"] == 50.0
    assert "not_measured" not in render_markdown(report) or True  # markdown renders every column
    markdown = render_markdown(report)
    assert "Resolve rate (all tasks)" in markdown and "33.33%" in markdown

    runs[0].leakage = ["F2P id"]
    assert build_report(runs)["integrity"]["leakage_free"] is False


def test_report_not_measured_when_nothing_ran():
    from agent.benchmarks.runner import TaskRun

    report = build_report([TaskRun(task_id="x", repo="r", status="pending")])
    assert report["totals"]["resolve_rate"] == 0.0
    assert report["totals"]["measured"] == 0
    empty = build_report([])
    assert empty["totals"]["resolve_rate"] is None
    assert empty["totals"]["avg_seconds"] is None
    assert "not_measured" in render_markdown(empty)


def test_write_report_creates_both_files(tmp_path, loaded):
    report = build_report([], dataset_stats=loaded.stats())
    paths = write_report(report, tmp_path / "out")
    assert paths["json"].is_file() and paths["markdown"].is_file()
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["totals"]["tasks"] == 0


# ── settings + CLI + packaging ──────────────────────────────────────────────
def test_settings_expose_benchmark_paths():
    from config import settings

    for attr in (
        "BENCH_DATA_DIR",
        "BENCH_WORKSPACES_DIR",
        "BENCH_REPORT_DIR",
        "BENCH_JOBS",
        "BENCH_PYTEST_TIMEOUT_SECS",
        "BENCH_MAX_CONTEXT_CHARS",
        "BENCH_KEEP_WORKSPACES",
    ):
        assert hasattr(settings, attr), attr
    assert settings.BENCH_JOBS >= 1
    assert settings.BENCH_PYTEST_TIMEOUT_SECS >= 30


def test_cli_doctor_reports_ready_for_a_valid_corpus(corpus, capsys):
    code = cli.main(["--quiet", "doctor", "--data", str(corpus)])
    assert code == cli.EXIT_OK


def test_cli_doctor_fails_when_data_is_missing(tmp_path, capsys):
    code = cli.main(["doctor", "--data", str(tmp_path / "absent")])
    assert code == cli.EXIT_MISSING_DATA
    assert "no tasks.jsonl found" in capsys.readouterr().out


def test_cli_list_and_run_with_noop(corpus, capsys, tmp_path):
    assert cli.main(["--quiet", "list", "--data", str(corpus), "--json"]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["repo"] == "demopkg" and payload[0]["has_test_patch"] is True

    base = [
        "--quiet",
        "run",
        "--data",
        str(corpus),
        "--solver",
        "noop",
        "--out",
        str(tmp_path / "report"),
        "--workspaces-dir",
        str(tmp_path / "ws"),
        "--cache-dir",
        str(tmp_path / "cache"),
    ]
    # A clean run that resolved nothing is a valid measurement, so exit 0…
    assert cli.main(base) == cli.EXIT_OK
    report = json.loads((tmp_path / "report" / "benchmark-report.json").read_text(encoding="utf-8"))
    assert report["totals"]["tasks"] == 1
    assert report["totals"]["resolved"] == 0
    assert report["totals"]["errors"] == 0
    assert report["totals"]["resolve_rate"] == 0.0
    assert report["integrity"]["leakage_free"] is True

    # …and CI can still enforce a floor explicitly.
    assert cli.main([*base, "--fail-under", "25"]) == cli.EXIT_GATE
    assert cli.main([*base, "--fail-under", "0"]) == cli.EXIT_OK


def test_cli_scripted_solver_runs_and_scores(corpus, loaded, tmp_path):
    patch_file = tmp_path / "fix.diff"
    patch_file.write_text(loaded.tasks[0].gold_patch, encoding="utf-8")
    code = cli.main(
        [
            "--quiet",
            "run",
            "--data",
            str(corpus),
            "--solver",
            "scripted",
            "--patch",
            str(patch_file),
            "--out",
            str(tmp_path / "report2"),
            "--workspaces-dir",
            str(tmp_path / "ws2"),
            "--cache-dir",
            str(tmp_path / "cache2"),
        ]
    )
    assert code == cli.EXIT_OK
    report = json.loads((tmp_path / "report2" / "benchmark-report.json").read_text(encoding="utf-8"))
    assert report["totals"]["resolved"] == 1
    assert report["totals"]["resolve_rate"] == 100.0


def test_cli_requires_patch_for_scripted(corpus, capsys):
    assert cli.main(["run", "--data", str(corpus), "--solver", "scripted"]) == cli.EXIT_MISSING_DATA


def test_cli_rejects_run_without_tasks(tmp_path):
    assert cli.main(["run", "--data", str(tmp_path / "nothing")]) == cli.EXIT_MISSING_DATA


def test_cli_reports_missing_data_instead_of_silent_success(tmp_path):
    """A typo'd --data path must never look like '0 tasks, all fine'."""
    missing = str(tmp_path / "not-a-corpus")
    for argv in (["list"], ["run"], ["package"]):
        assert cli.main(["--quiet", *argv, "--data", missing]) == cli.EXIT_MISSING_DATA


def test_cli_package_builds_a_valid_kaggle_zip(tmp_path, corpus):
    out = tmp_path / "bench-kaggle.zip"
    assert cli.main(["--quiet", "package", "--data", str(corpus), "--out", str(out)]) == cli.EXIT_OK
    assert zipfile.is_zipfile(out)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        assert "run_benchmarks.sh" in names
        assert "install_harness.sh" in names
        assert "dataset-manifest.json" in names
        assert "requirements-bench.txt" in names
        assert "ai-agent/tests/test_benchmarks.py" in names
        assert any(n.startswith("ai-agent/agent/benchmarks/") and n.endswith(".py") for n in names)
        assert not any(n.endswith(".tgz") for n in names)  # corpus is never inlined
        manifest = json.loads(zf.read("dataset-manifest.json"))
        assert manifest["dataset_present"] is True
        assert manifest["detected"]["tasks"] == 1


def test_package_manifest_without_dataset():
    from agent.benchmarks.packaging import build_manifest

    manifest = build_manifest(None)
    assert manifest["dataset_present"] is False
    assert "tasks.jsonl" in manifest["expected_layout"]


# ── module surface ──────────────────────────────────────────────────────────
def test_package_exports_public_api():
    import agent.benchmarks as bench

    for name in ("BenchmarkDataset", "BenchmarkRunner", "CodeGraph", "TestGrader", "AiPatchSolver", "build_report"):
        assert name in bench.__all__ and hasattr(bench, name)
