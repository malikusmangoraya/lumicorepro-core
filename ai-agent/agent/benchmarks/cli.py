"""CLI: `python -m agent.benchmarks <doctor|list|run|report|package>`."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

from .dataset import TASK_FILE_NAMES, BenchmarkDataset
from .grader import TestGrader
from .packaging import build_kaggle_bundle
from .report import build_report, load_report, summarise, write_report
from .runner import BenchmarkRunner
from .solvers import AiPatchSolver, NoOpSolver, ScriptedSolver
from .workspace import WorkspaceManager

EXIT_OK = 0
EXIT_MISSING_DATA = 2
EXIT_ERRORS = 3
EXIT_GATE = 4  # ran cleanly, but the resolve rate missed --fail-under


def _log(quiet: bool, message: str = "") -> None:
    if not quiet:
        print(message, flush=True)


def _settings() -> Dict[str, Any]:
    from config.settings import (
        BENCH_DATA_DIR,
        BENCH_JOBS,
        BENCH_KEEP_WORKSPACES,
        BENCH_MAX_CONTEXT_CHARS,
        BENCH_PYTEST_TIMEOUT_SECS,
        BENCH_REPORT_DIR,
        BENCH_WORKSPACES_DIR,
    )

    return {
        "data_dir": Path(BENCH_DATA_DIR),
        "workspaces_dir": Path(BENCH_WORKSPACES_DIR),
        "report_dir": Path(BENCH_REPORT_DIR),
        "jobs": BENCH_JOBS,
        "keep": BENCH_KEEP_WORKSPACES,
        "max_context_chars": BENCH_MAX_CONTEXT_CHARS,
        "pytest_timeout": BENCH_PYTEST_TIMEOUT_SECS,
    }


def cmd_doctor(args: argparse.Namespace) -> int:
    quiet = args.quiet
    settings = _settings()
    dataset = BenchmarkDataset.load(args.data)
    stats = dataset.stats()

    _log(quiet, "== environment ==")
    _log(quiet, f"python           : {sys.version.split()[0]} ({sys.executable})")
    _log(quiet, f"pytest           : {'yes' if shutil.which('pytest') or _pytest_importable() else 'NO'}")
    _log(quiet, f"git              : {shutil.which('git') or 'NOT FOUND (required for status/log/diff)'}")
    _log(quiet, f"dataset root     : {stats['root']} ({'exists' if stats['root_exists'] else 'MISSING'})")
    _log(quiet, f"workspaces       : {settings['workspaces_dir']}")

    _log(quiet, "\n== corpus ==")
    rows = [
        ("tasks.jsonl", stats["tasks_file"] or "-", stats["tasks"]),
        ("snapshots/*.tgz", stats["snapshots_dir"] or "-", stats["snapshots"]),
        ("graphs/*.json", stats["graphs_dir"] or "-", stats["graphs"]),
        ("embeddings", stats["embeddings_dir"] or "-", stats["embeddings"]),
        ("wheels/*.whl", stats["wheels_dir"] or "-", stats["wheels"]),
        ("HARNESS_README", stats["harness_readme"] or "-", "yes" if stats["harness_readme"] else "no"),
    ]
    for label, path, count in rows:
        _log(quiet, f"{label:<18}: {count!s:<6} {path}")

    _log(quiet, "\n== task integrity ==")
    _log(quiet, f"repos                 : {stats['repos']}")
    _log(quiet, f"gradeable tasks       : {stats['gradeable_tasks']}")
    _log(quiet, f"tasks w/ snapshot     : {stats['tasks_with_snapshot']}")
    _log(quiet, f"tasks w/ gold patch   : {stats['tasks_with_gold_patch']}")
    _log(quiet, f"tasks w/ test patch   : {stats['tasks_with_test_patch']}")

    missing = [t.id for t in dataset.tasks if dataset.snapshot_archive(t) is None]
    if missing:
        _log(quiet, f"\nWARNING: {len(missing)} task(s) have no resolvable snapshot (first: {missing[0]})")

    if not stats["tasks"]:
        _log(quiet, "\nRESULT: no tasks.jsonl found - set BENCH_DATA_DIR or pass --data <dir>")
        return EXIT_MISSING_DATA
    if not shutil.which("git"):
        _log(quiet, "\nRESULT: git not on PATH - snapshots cannot be graded")
        return EXIT_MISSING_DATA
    _log(quiet, "\nRESULT: ready")
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    dataset = BenchmarkDataset.load(args.data)
    if dataset.tasks_file is None:
        _log(
            args.quiet,
            f"No task file under {dataset.root} "
            f"(looked for {'/'.join(TASK_FILE_NAMES)}). Set BENCH_DATA_DIR or pass --data.",
        )
        return EXIT_MISSING_DATA
    tasks = dataset.select(limit=args.limit, repos=args.repo, task_ids=args.task)
    if args.json:
        print(json.dumps([t.to_dict() if hasattr(t, "to_dict") else _task_dict(t) for t in tasks], indent=2))
        return EXIT_OK
    for task in tasks:
        flags = []
        if dataset.snapshot_archive(task):
            flags.append("snapshot")
        if task.has_test_patch:
            flags.append("test_patch")
        if task.has_gold_patch:
            flags.append("gold")
        if task.fail_to_pass:
            flags.append(f"f2p={len(task.fail_to_pass)}")
        print(f"{task.id:<40} {task.repo:<24} {task.language:<8} [{', '.join(flags) or 'no-assets'}]")
    print(f"\n{len(tasks)} task(s) of {len(dataset.tasks)}")
    return EXIT_OK


def _task_dict(task: Any) -> Dict[str, Any]:
    return {
        "id": task.id,
        "repo": task.repo,
        "language": task.language,
        "base_commit": task.base_commit,
        "issue_chars": len(task.issue),
        "has_gold_patch": task.has_gold_patch,
        "has_test_patch": task.has_test_patch,
        "fail_to_pass": task.fail_to_pass,
        "pass_to_pass": task.pass_to_pass,
        "test_targets": task.test_targets,
    }


def cmd_run(args: argparse.Namespace) -> int:
    settings = _settings()
    dataset = BenchmarkDataset.load(args.data)
    if not dataset.tasks:
        _log(args.quiet, f"No tasks found under {dataset.root}. Set BENCH_DATA_DIR or pass --data.")
        return EXIT_MISSING_DATA

    tasks = dataset.select(limit=args.limit, repos=args.repo, task_ids=args.task)
    if not tasks:
        _log(args.quiet, "No task matched the filters.")
        return EXIT_MISSING_DATA

    if args.solver == "noop":
        solver = NoOpSolver()
    elif args.solver == "scripted":
        patch = Path(args.patch).read_text(encoding="utf-8") if args.patch else ""
        if not patch:
            _log(args.quiet, "--solver scripted requires --patch <file>")
            return EXIT_MISSING_DATA
        solver = ScriptedSolver(patch)
    else:
        solver = AiPatchSolver(max_attempts=args.attempts)

    manager = WorkspaceManager(
        cache_dir=Path(args.cache_dir) if args.cache_dir else settings["workspaces_dir"].parent / ".bench-cache",
        workspaces_dir=Path(args.workspaces_dir) if args.workspaces_dir else settings["workspaces_dir"],
        reuse_cache=args.reuse_cache,
    )
    if args.clean:
        manager.cleanup()

    grader = TestGrader(timeout=args.timeout or settings["pytest_timeout"])
    runner = BenchmarkRunner(
        dataset=dataset,
        manager=manager,
        solver=solver,
        grader=grader,
        keep_workspaces=args.keep_workspaces or settings["keep"],
        max_context_chars=args.max_context_chars or settings["max_context_chars"],
    )

    _log(args.quiet, f"running {len(tasks)} task(s) with solver '{getattr(solver, 'name', 'ai')}' (jobs={args.jobs})")

    def progress(run: Any, index: int, total: int) -> None:
        mark = "OK " if run.resolved else ("ERR" if run.status.startswith("error") else "-- ")
        _log(
            args.quiet,
            f"[{index:>3}/{total}] {mark} {run.task_id[:36]:<36} {run.repo[:22]:<22} "
            f"{run.status:<24} {run.seconds:>6.1f}s {run.detail[:60]}",
        )

    runs = runner.run_tasks(tasks, jobs=args.jobs or settings["jobs"], progress=progress)
    report = build_report(
        runs,
        dataset_stats=dataset.stats(),
        solver=getattr(solver, "name", "ai"),
        command=" ".join(["python", "-m", "agent.benchmarks", *sys.argv[1:]]),
    )
    out_dir = Path(args.out) if args.out else settings["report_dir"]
    paths = write_report(report, out_dir)

    _log(args.quiet, "\n== summary ==")
    _log(args.quiet, summarise(report))
    _log(args.quiet, f"report: {paths['markdown']}")
    _log(args.quiet, f"        {paths['json']}")
    if not report["integrity"]["leakage_free"]:
        _log(args.quiet, "WARNING: reference-solution leakage detected - treat scores as invalid")
        return EXIT_ERRORS
    if report["totals"]["errors"]:
        return EXIT_ERRORS
    # A clean run that resolved nothing is a valid measurement, not a harness
    # error: only the opt-in quality gate turns a low resolve rate into a
    # non-zero exit (so CI can enforce a floor without reinterpreting errors).
    rate = report["totals"]["resolve_rate"]
    if args.fail_under is not None and rate is not None and rate < args.fail_under:
        _log(args.quiet, f"GATE: resolve rate {rate}% is below the required {args.fail_under}%")
        return EXIT_GATE
    return EXIT_OK


def cmd_report(args: argparse.Namespace) -> int:
    report = load_report(Path(args.json))
    if args.out:
        paths = write_report(report, Path(args.out), basename=args.basename)
        _log(args.quiet, f"wrote {paths['markdown']} and {paths['json']}")
    else:
        from .report import render_markdown

        print(render_markdown(report, top=args.top))
    return EXIT_OK


def cmd_package(args: argparse.Namespace) -> int:
    dataset = BenchmarkDataset.load(args.data)
    if dataset.tasks_file is None:
        _log(
            args.quiet,
            f"No task file under {dataset.root} - set BENCH_DATA_DIR or pass --data.",
        )
        return EXIT_MISSING_DATA
    readme = Path(args.readme) if args.readme else Path(__file__).resolve().parent / "README.md"
    out = Path(args.out)
    build_kaggle_bundle(out, dataset=dataset, readme_text=readme.read_text(encoding="utf-8") if readme.is_file() else None)
    size_kb = out.stat().st_size / 1024
    _log(args.quiet, f"wrote {out} ({size_kb:.1f} KB)")
    _log(args.quiet, "next: mount the corpus, then `bash run_benchmarks.sh <dataset_dir>`")
    return EXIT_OK


def _pytest_importable() -> bool:
    try:
        import pytest  # noqa: F401

        return True
    except Exception:
        return False


def build_parser() -> argparse.ArgumentParser:
    settings = _settings()
    parser = argparse.ArgumentParser(
        prog="python -m agent.benchmarks",
        description="Offline public-development benchmark (real bug-fixing tasks).",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--data", default=None, help=f"dataset root (default: {settings['data_dir']})")

    doctor = sub.add_parser("doctor", help="verify corpus, git, interpreter and task integrity")
    add_common(doctor)
    doctor.set_defaults(func=cmd_doctor)

    listing = sub.add_parser("list", help="list tasks and which assets each one resolves")
    add_common(listing)
    listing.add_argument("--limit", type=int, default=None)
    listing.add_argument("--repo", action="append", default=None)
    listing.add_argument("--task", action="append", default=None)
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=cmd_list)

    run = sub.add_parser("run", help="run the benchmark and write a report")
    add_common(run)
    run.add_argument("--solver", choices=("ai", "noop", "scripted"), default="ai")
    run.add_argument("--patch", default=None, help="diff file for --solver scripted")
    run.add_argument("--limit", type=int, default=None, help="0 = all tasks")
    run.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="exit 4 when the resolve rate (%%) is below this floor, e.g. --fail-under 30",
    )
    run.add_argument("--repo", action="append", default=None)
    run.add_argument("--task", action="append", default=None)
    run.add_argument("--jobs", type=int, default=0, help="0 = BENCH_JOBS (default 1)")
    run.add_argument("--timeout", type=int, default=0, help="per-task pytest timeout in seconds")
    run.add_argument("--attempts", type=int, default=3, help="max model rounds per task")
    run.add_argument("--out", default=None, help="report directory")
    run.add_argument("--workspaces-dir", default=None)
    run.add_argument("--cache-dir", default=None, help="snapshot extraction cache")
    run.add_argument("--reuse-cache", action="store_true", help="edit the cached tree in place (fast, destructive)")
    run.add_argument("--keep-workspaces", action="store_true")
    run.add_argument("--clean", action="store_true", help="delete stale workspaces first")
    run.add_argument("--max-context-chars", type=int, default=0)
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="re-render a stored JSON report")
    report.add_argument("--json", required=True, help="path to benchmark-report.json")
    report.add_argument("--out", default=None, help="write markdown+json to this directory")
    report.add_argument("--basename", default="benchmark-report")
    report.add_argument("--top", type=int, default=30)
    report.set_defaults(func=cmd_report)

    package = sub.add_parser("package", help="build the Kaggle-uploadable bundle")
    add_common(package)
    package.add_argument("--out", default="dist/bench-kaggle.zip")
    package.add_argument("--readme", default=None)
    package.set_defaults(func=cmd_package)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        _log(False, "\ninterrupted")
        return 130
    except Exception as exc:  # CLI must fail with a message, not a stack trace
        agent_logger.error(f"[BENCH] {type(exc).__name__}: {exc}")
        print(f"benchmark error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
