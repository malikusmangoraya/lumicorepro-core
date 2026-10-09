#!/usr/bin/env python
"""package_for_sale.py — build a clean, sell-ready distribution archive.

The repository contains a lot that must never reach a paying customer:
node_modules, logs, coverage, the SQLite/Postgres data volume, generated
customer projects, local .env files with real secrets, and the git history.

This script produces exactly one deterministic ZIP plus a JSON manifest
(file count, unpacked size, sha256) that can be uploaded to Lemon Squeezy as a
version file and verified by the customer after download.

Usage::

    python scripts/package_for_sale.py                    # build
    python scripts/package_for_sale.py --dry-run          # list what would ship
    python scripts/package_for_sale.py --out ../dist-sale --include-tests
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Shipped directories/files — the product a customer installs.
INCLUDE_DIRS = [
    "backend", "src", "ai-agent", "database", "docs", "nginx", "k8s",
    "public", "e2e", "registry", "scripts", "backend-library",
]
# Past customer deliveries live in delivery/ — they are NOT part of the
# product. Include them only with --with-deliveries (support/debugging).
OPTIONAL_DIRS = ["delivery"]
INCLUDE_FILES = [
    "index.html", "package.json", "package-lock.json", "vite.config.js",
    "tailwind.config.js", "postcss.config.js", "jsconfig.json",
    "eslint.config.js", "playwright.config.js", "docker-compose.yml",
    "docker-compose.prod.yml", "Dockerfile.frontend", "vercel.json",
    "README.md", "LICENSE.md", "CHANGELOG.md", "SECURITY.md", "CONTRIBUTING.md",
    ".env.example", ".env.production.example", ".prettierrc", ".gitignore",
    ".dockerignore", ".gitattributes", ".prettierignore",
]

# Never shipped, regardless of location.
EXCLUDE_DIR_NAMES = {
    "node_modules", ".git", ".github", ".history", "dist", "build", "coverage",
    "logs", "log", "pgdata", "venv", ".venv", "__pycache__", ".pytest_cache",
    ".pytest_cache", "generated-projects", "release", "uploads", "test-results",
    "playwright-report", ".cache", ".mypy_cache", ".ruff_cache", "sandbox",
}
EXCLUDE_SUFFIXES = {
    ".log", ".pid", ".zip", ".tar", ".gz", ".tgz", ".pyc", ".pyo", ".env",
    ".sqlite", ".sqlite3", ".db", ".key", ".pem", ".crt",
}
EXCLUDE_EXACT = {
    ".env", ".env.production", ".env.staging", ".env.local",
    "gen_out.log", "gen_err.log", "animate.out.log", "animate.err.log",
}
# Scratch files from interactive/debug sessions (e.g. ai-agent/_test_home.jsx).
EXCLUDE_NAME_RE = re.compile(r"^_test_.*\.jsx$", re.IGNORECASE)


def _excluded(path: Path, root: Path) -> bool:
    if path.name in EXCLUDE_EXACT or EXCLUDE_NAME_RE.match(path.name):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    rel_parts = path.relative_to(root).parts
    return any(part in EXCLUDE_DIR_NAMES for part in rel_parts)


def collect_files(root: Path, include_tests: bool, with_deliveries: bool = False) -> list[Path]:
    files: list[Path] = []

    for name in INCLUDE_FILES:
        candidate = root / name
        if candidate.is_file():
            files.append(candidate)

    for name in INCLUDE_DIRS + (OPTIONAL_DIRS if with_deliveries else []):
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or _excluded(path, root):
                continue
            if not include_tests and any(part in {"tests", "__tests__", "test", ".pytest_cache"}
                                        for part in path.relative_to(root).parts):
                continue
            files.append(path)

    # Unique + stable order → deterministic archives.
    return sorted({f.resolve() for f in files})


def build(root: Path, out_dir: Path, include_tests: bool, dry_run: bool,
          with_deliveries: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    version = _read_version(root)
    files = collect_files(root, include_tests, with_deliveries)

    manifest = {
        "product": "lumicorepro-core",
        "version": version,
        "file_count": len(files),
        "unpacked_bytes": sum(f.stat().st_size for f in files),
        "include_tests": include_tests,
        "with_deliveries": with_deliveries,
        "archive": None,
        "sha256": None,
        "files": [str(f.relative_to(root)).replace("\\", "/") for f in files],
    }

    if dry_run:
        print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2))
        print(f"\nFirst 20 files:")
        for entry in manifest["files"][:20]:
            print(f"  {entry}")
        print(f"  … and {len(manifest['files']) - 20} more")
        return manifest

    archive_path = out_dir / f"lumicorepro-core-{version}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            zf.write(path, arcname=str(Path("lumicorepro-core") / path.relative_to(root)))

    digest = hashlib.sha256()
    with archive_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)

    manifest["archive"] = str(archive_path)
    manifest["archive_bytes"] = archive_path.stat().st_size
    manifest["sha256"] = digest.hexdigest()
    (out_dir / f"lumicorepro-core-{version}.manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def _read_version(root: Path) -> str:
    try:
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
        return str(data.get("version", "0.0.0"))
    except (OSError, json.JSONDecodeError):
        return "0.0.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a sell-ready distribution archive")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument("--out", default=str(ROOT / "release"), help="output directory")
    parser.add_argument("--include-tests", action="store_true", help="include test suites in the archive")
    parser.add_argument("--with-deliveries", action="store_true",
                        help="also include past customer deliveries from delivery/")
    parser.add_argument("--dry-run", action="store_true", help="print the manifest without building")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    manifest = build(root, Path(args.out).resolve(), args.include_tests, args.dry_run,
                     args.with_deliveries)

    if not args.dry_run:
        print(f"Built {manifest['archive']}")
        print(f"  files     : {manifest['file_count']}")
        print(f"  unpacked  : {manifest['unpacked_bytes'] / 1_048_576:.1f} MB")
        print(f"  archive   : {manifest['archive_bytes'] / 1_048_576:.1f} MB")
        print(f"  sha256    : {manifest['sha256']}")
        print(f"  manifest  : {args.out}/{manifest['product']}-{manifest['version']}.manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())