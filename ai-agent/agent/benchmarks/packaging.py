"""Build a Kaggle-uploadable bundle of the benchmark code (no dataset blobs).

The zip contains only what Kaggle needs to re-run the evaluation after the
corpus is mounted: the harness package, its tests, the offline wheel installer,
a dataset manifest describing the expected layout, and a shell entrypoint.
Repository snapshots, graphs and embeddings are never inlined — they are mounted
or downloaded separately, so the bundle stays small and reproducible.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dataset import BenchmarkDataset

RUN_SCRIPT = """#!/usr/bin/env bash
# Kaggle entrypoint: verify the corpus, then run the benchmark end to end.
set -euo pipefail
cd "${AI_AGENT_DIR:-/kaggle/working/ai-agent}"

export BENCH_DATA_DIR="${BENCH_DATA_DIR:-${1:-/kaggle/input/public-dev-benchmark}}"
export BENCH_WORKSPACES_DIR="${BENCH_WORKSPACES_DIR:-/kaggle/working/.bench-workspaces}"

python -m agent.benchmarks doctor --data "$BENCH_DATA_DIR"
python -m agent.benchmarks run \\
  --data "$BENCH_DATA_DIR" \\
  --solver "${BENCH_SOLVER:-ai}" \\
  --limit "${BENCH_LIMIT:-0}" \\
  --jobs "${BENCH_JOBS:-4}" \\
  --out "${BENCH_REPORT_DIR:-/kaggle/working/generated-projects/bench-out}"
"""

INSTALL_SCRIPT = """#!/usr/bin/env bash
# Fully offline dependency install using the bundled evaluation wheels.
set -euo pipefail
WHEELS="${BENCH_WHEELS_DIR:-$(dirname "$0")/wheels}"
python -m pip install --no-index --find-links "$WHEELS" \\
  adk_eval_core 2>/dev/null || echo "[bench] adk_eval_core wheel not found; continuing with stdlib harness"
python -m pip install -r "$(dirname "$0")/requirements-bench.txt"
"""

REQUIREMENTS = """# Benchmark-only dependencies (the harness itself is stdlib + pytest).
pytest>=8.0
# Optional: enables .npy / .npz node-embedding loading (JSON + lexical fallback work without it).
numpy>=1.24
"""

EXPECTED_LAYOUT = {
    "tasks.jsonl": "129 bug-fixing tasks (issue text + gold patch + test patch)",
    "snapshots/*.tgz": "frozen git working trees (FastAPI, Rich, requests, httpx, ...)",
    "graphs/*.json": "per-repo AST call + dependency graph",
    "embeddings/*": "per-repo node embedding vectors",
    "wheels/*.whl": "offline evaluation wheels (adk_eval_core)",
    "HARNESS_README*": "official harness notes",
}


def _iter_package_files(package_dir: Path) -> List[Path]:
    return sorted(
        p for p in package_dir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".md")
    )


def build_manifest(dataset: Optional[BenchmarkDataset] = None) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "name": "lumicore-offline-benchmark",
        "dataset_root_env": "BENCH_DATA_DIR",
        "expected_layout": EXPECTED_LAYOUT,
        "entrypoint": "bash run_benchmarks.sh <dataset_dir>",
        "smoke_test": "python -m agent.benchmarks doctor --data <dataset_dir>",
    }
    if dataset is not None:
        stats = dataset.stats()
        manifest["detected"] = {
            key: stats.get(key)
            for key in ("tasks", "repos", "tasks_with_snapshot", "snapshots", "graphs", "embeddings", "wheels")
        }
        manifest["dataset_present"] = bool(stats.get("tasks"))
    else:
        manifest["dataset_present"] = False
    return manifest


def build_kaggle_bundle(
    out_zip: Path,
    dataset: Optional[BenchmarkDataset] = None,
    readme_text: Optional[str] = None,
    extra_files: Optional[List[Path]] = None,
) -> Path:
    """Write the bundle zip and return its path."""
    package_dir = Path(__file__).resolve().parent
    ai_agent_dir = package_dir.parent.parent
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:

        def add(path: Path, arcname: str) -> None:
            zf.write(path, arcname)
            written.append(arcname)

        for path in _iter_package_files(package_dir):
            rel = path.relative_to(ai_agent_dir).as_posix()
            add(path, f"ai-agent/{rel}")

        tests_file = ai_agent_dir / "tests" / "test_benchmarks.py"
        if tests_file.is_file():
            add(tests_file, "ai-agent/tests/test_benchmarks.py")

        for path in extra_files or []:
            path = Path(path)
            if path.is_file():
                add(path, path.name)

        zf.writestr("requirements-bench.txt", REQUIREMENTS)
        written.append("requirements-bench.txt")
        zf.writestr("dataset-manifest.json", json.dumps(build_manifest(dataset), indent=2))
        written.append("dataset-manifest.json")
        zf.writestr("run_benchmarks.sh", RUN_SCRIPT)
        written.append("run_benchmarks.sh")
        zf.writestr("install_harness.sh", INSTALL_SCRIPT)
        written.append("install_harness.sh")
        if readme_text:
            zf.writestr("BENCHMARKS.md", readme_text)
            written.append("BENCHMARKS.md")

    return out_zip
