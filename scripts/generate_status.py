"""Generate docs/STATUS.md - the single source of truth for project status.

Design rule: this script never invents a measured number.

* Static inventory (versions, test declarations, file counts) is counted from the
  tree every time it runs.
* Anything that requires execution (coverage, bundle size, live probes) is either
  read from a real artifact on disk or listed with the exact command that produces
  it, marked `not measured` when the artifact is absent.

Usage:
    python scripts/generate_status.py            # write docs/STATUS.md
    python scripts/generate_status.py --check    # exit 1 if the file is stale (CI gate)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "STATUS.md"

SKIP_DIRS = {"node_modules", "dist", "build", ".git", "venv", "__pycache__",
             ".pytest_cache", "coverage", "generated-projects", "backend-library"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def json_field(path: Path, *keys, default=None):
    if not path.exists():
        return default
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return default
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return default
        data = data[key]
    return data


def walk(root: Path, suffixes: tuple[str, ...]):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def count_tests(files: list[Path], pattern: str) -> int:
    rx = re.compile(pattern, re.MULTILINE)
    total = 0
    for path in files:
        total += len(rx.findall(read_text(path)))
    return total


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, timeout=10, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _expand_braces(pattern: str) -> list[str]:
    """Expand top-level {a,b} alternations (pathlib has none)."""
    start = pattern.find("{")
    if start == -1:
        return [pattern]
    end = pattern.find("}", start)
    if end == -1:
        return [pattern]
    out: list[str] = []
    for alt in pattern[start + 1 : end].split(","):
        out.extend(_expand_braces(pattern[:start] + alt + pattern[end + 1 :]))
    return out


def _glob_re(pattern: str) -> "re.Pattern[str]":
    """Compile a glob to a regex anchored at both ends.

    pathlib.Path.match() was the previous matcher and it silently matched zero
    files: it has no brace expansion and its ``**`` does not cross directory
    boundaries, so ``**/__tests__/**/*.{test,spec}.{js,jsx}`` and friends never
    fired (the report showed 0 frontend / 0 backend / 0 pytest test files).
    """
    parts: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern[i : i + 3] == "**/":
                parts.append("(?:[^/]+/)*")
                i += 3
                continue
            if pattern[i : i + 2] == "**":
                parts.append(".*")
                i += 2
                continue
            parts.append("[^/]*")
        elif char == "?":
            parts.append("[^/]")
        else:
            parts.append(re.escape(char))
        i += 1
    return re.compile("^" + "".join(parts) + "$")


def suite(name: str, root: Path, glob: str, pattern: str, command: str) -> dict:
    regexes = [_glob_re(p) for p in _expand_braces(glob)]
    files = []
    for path in walk(root, (".js", ".jsx", ".ts", ".tsx", ".py")):
        rel = path.relative_to(root).as_posix()
        if any(rx.match(rel) for rx in regexes):
            files.append(path)
    return {
        "name": name,
        "files": len(files),
        "tests": count_tests(files, pattern),
        "command": command,
    }


def build_report() -> str:
    versions = {
        "package.json": json_field(ROOT / "package.json", "version", default="?"),
        "backend/package.json": json_field(ROOT / "backend" / "package.json", "version", default="?"),
    }

    frontend = suite("Frontend (Vitest)", ROOT / "src", "**/__tests__/**/*.{test,spec}.{js,jsx,ts,tsx}",
                     r"\b(?:it|test)\s*\(", "npm run test")
    backend = suite("Backend (Jest)", ROOT / "backend", "**/{__tests__,tests}/**/*.test.js",
                    r"\b(?:it|test)\s*\(", "cd backend && npm test")
    agent = suite("AI agent (pytest)", ROOT / "ai-agent", "**/tests/**/test_*.py",
                  r"^\s*def test_", r"venv\\Scripts\python.exe -m pytest ai-agent/tests -q")
    e2e = suite("E2E (Playwright)", ROOT / "e2e", "**/*.spec.js",
                r"\btest\s*\(", "npm run test:e2e")

    coverage = json_field(ROOT / "backend" / "coverage" / "coverage-summary.json",
                          "total", "statements", "pct", default=None)
    frontend_coverage = json_field(ROOT / "coverage" / "coverage-summary.json",
                                   "total", "statements", "pct", default=None)

    delivery = json_field(ROOT / "delivery" / "DELIVERY_EVIDENCE.json", "totals", default=None)

    src_files = len(list(walk(ROOT / "src", (".js", ".jsx", ".css"))))
    backend_files = len(list(walk(ROOT / "backend", (".js",))))
    agent_files = len(list(walk(ROOT / "ai-agent", (".py",))))

    changelog = read_text(ROOT / "CHANGELOG.md")[:6000]
    changelog_versions = re.findall(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\d+\.\d+)\s*\|", changelog)
    newest_changelog = changelog_versions[0] if changelog_versions else ("?", "?")

    agents_md = read_text(ROOT / "AGENTS.md")
    header_match = re.search(r"^>\s*v([\d.]+)", agents_md, re.MULTILINE)
    agents_version = header_match.group(1) if header_match else "?"

    readme = read_text(ROOT / "README.md")
    readme_match = re.search(r"v(\d+\.\d+\.\d+[\w.-]*)", readme)
    readme_version = readme_match.group(1) if readme_match else "?"

    lines: list[str] = []
    add = lines.append
    add("# Project Status")
    add("")
    add("> Generated by `python scripts/generate_status.py`. Do not edit by hand.")
    add("> CI enforces freshness with `python scripts/generate_status.py --check`.")
    add("")
    add(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    head = git("rev-parse", "--short", "HEAD")
    if head:
        add(f"Commit: `{head}` on `{git('rev-parse', '--abbrev-ref', 'HEAD')}`")
    add("")

    add("## Versions")
    add("")
    add("| Source | Version |")
    add("|--------|---------|")
    for key, value in versions.items():
        add(f"| `{key}` | `{value}` |")
    add(f"| `AGENTS.md` header | `{agents_version}` |")
    add(f"| `README.md` badge | `{readme_version}` |")
    add(f"| newest `CHANGELOG.md` entry | `{newest_changelog[1]}` ({newest_changelog[0]}) |")
    add("")
    drift = {versions["package.json"], agents_version, newest_changelog[1]} - {"?"}
    add(
        "- Version sources agree (`package.json` == `AGENTS.md` == `CHANGELOG.md`): "
        + ("**yes**" if len(drift) <= 1 else f"**no** - found {sorted(drift)}")
    )
    add("")

    add("## Test inventory (declared cases, counted from source)")
    add("")
    add("| Suite | Test files | Declared cases | Command |")
    add("|-------|-----------|----------------|---------|")
    for entry in (frontend, backend, agent, e2e):
        add(f"| {entry['name']} | {entry['files']} | {entry['tests']} | `{entry['command']}` |")
    add("")
    add("Declared cases are a static count of `it(`/`test(`/`def test_` occurrences - they are")
    add("not a pass/fail result. Run the command column for a real result.")
    add("")

    add("## Last measured results (from artifacts on disk)")
    add("")
    add("| Metric | Value | Artifact |")
    add("|--------|-------|----------|")
    add(f"| Backend statement coverage | {f'{coverage}%' if coverage is not None else 'not measured'} | `backend/coverage/coverage-summary.json` |")
    add(f"| Frontend statement coverage | {f'{frontend_coverage}%' if frontend_coverage is not None else 'not measured'} | `coverage/coverage-summary.json` |")
    if delivery:
        add(f"| Delivery projects | {delivery.get('projects', '?')} | `delivery/DELIVERY_EVIDENCE.json` |")
        add(f"| Delivery zips valid | {delivery.get('zips_valid', '?')}/{delivery.get('zips_present', '?')} | `delivery/DELIVERY_EVIDENCE.json` |")
        add(f"| Delivery live probes OK | {delivery.get('probe_ok', 'not probed')}/{delivery.get('probed', 0)} | `delivery/DELIVERY_EVIDENCE.json` |")
    else:
        add("| Delivery verification | not measured | run `python scripts/final_verify_delivery.py --probe` |")
    add("| Initial JS bundle (gzip) | not measured here | run `npm run build && npm run size` |")
    add("")

    add("## Code size")
    add("")
    add("| Area | Files |")
    add("|------|-------|")
    add(f"| `src/` | {src_files} |")
    add(f"| `backend/` | {backend_files} |")
    add(f"| `ai-agent/` | {agent_files} |")
    add("")

    add("## Gates that must pass before a release")
    add("")
    add("| Gate | Command | Blocking |")
    add("|------|---------|----------|")
    add("| Frontend lint | `npm run lint` | yes |")
    add("| Frontend tests | `npm run test` | yes |")
    add("| Frontend build | `npm run build` | yes |")
    add("| Bundle budget | `npm run size` | yes |")
    add("| Backend tests + coverage | `cd backend && npm test` | yes |")
    add("| AI agent tests | `venv\\Scripts\\python.exe -m pytest ai-agent/tests -q` | yes |")
    add("| E2E smoke | `npm run test:e2e` | yes |")
    add("| Delivery verification | `python scripts/final_verify_delivery.py --probe` | yes |")
    add("")
    add("Evidence rule: no gate may be reported as passing without the command output that")
    add("proves it. `not measured` is a valid status; an invented number is not.")
    add("")
    return "\n".join(lines)


def _static_view(text: str) -> str:
    """Drop the lines that cannot be identical between two runs/machines.

    * ``Generated:`` — timestamp, differs every run.
    * ``Commit:`` — a committed file can never contain the sha of the commit
      that will carry it, and CI checks out a detached HEAD, so this line is
      volatile by construction.
    * the "Last measured results" section — derived from gitignored artifacts
      (``coverage/``, ``delivery/``) that a fresh CI checkout does not have.

    Everything else (versions, test inventory, code size, gate list) comes from
    committed sources and must match exactly.
    """
    out: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith("## Last measured results"):
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if skipping or line.startswith("Generated:") or line.startswith("Commit:"):
            continue
        out.append(line)
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if docs/STATUS.md is stale")
    args = parser.parse_args()

    report = build_report()
    if args.check:
        current = read_text(OUT)
        if _static_view(current) != _static_view(report):
            print("docs/STATUS.md is stale - run: python scripts/generate_status.py")
            return 1
        print("docs/STATUS.md is up to date")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
