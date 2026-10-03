"""Rebuild stub/partial frontends from the modern reference (build-015).

For each target dir: remove frontend/ and re-create from the clean modern
reference (11 pages, Vite, tailwind, i18n, theme tokens) excluding heavy/derived
dirs. Preserves the project's own non-frontend assets (backend, etc.) which
live OUTSIDE frontend/.
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
REF = GEN / "build-015" / "frontend"

TARGETS = [
    "auto-deploy-test",
    "edtech-fitness-001",
    "generated-website-002",
    "generated-website-008",
    "personal-portfolio-001",
    "realestate-realestate-001",
    "resupro",
    "saas-saas-001",
    "saas-saas-001-002",
    "saas-saas-001-003",
    "saas-saas-001-004",
    "test-i18n",
    "build-017",
    "build-018",
    "build-019",
]

EXCLUDE_DIRS = {
    "node_modules", "dist", ".git", ".vite", "coverage", "__pycache__",
    ".pytest_cache", ".mypy_cache", "cache",
}
EXCLUDE_FILES = {".DS_Store"}


def copytree(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE_DIRS:
            continue
        s = src / item.name
        d = dst / item.name
        if s.is_dir():
            shutil.copytree(s, d,
                            ignore=shutil.ignore_patterns(*EXCLUDE_DIRS))
        elif s.is_file() and s.name not in EXCLUDE_FILES:
            shutil.copy2(s, d)


def main() -> int:
    assert REF.is_dir(), "reference missing: %s" % REF
    ok, fail = [], []
    for name in TARGETS:
        fe = GEN / name / "frontend"
        try:
            if fe.exists():
                shutil.rmtree(fe)
            copytree(REF, fe)
            ok.append(name)
            print("REBUILT %s" % name)
        except Exception as exc:  # pragma: no cover
            fail.append((name, str(exc)))
            print("FAIL    %s: %s" % (name, exc))
    print("\nrebuilt=%d failed=%d" % (len(ok), len(fail)))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())