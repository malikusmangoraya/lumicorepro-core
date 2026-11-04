"""Python lint ratchet: violation counts may only fall.

ruff and bandit both report a large existing backlog over 64K lines of agent
code. A gate that demands zero today would never pass, and a gate that is
disabled to make it pass is not a gate. This tool records the measured
baseline in ai-agent/lint-baseline.json and fails only when a count rises.

A tool that cannot be measured reports None, and None never passes: silence is
not evidence of a clean run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "ai-agent" / "lint-baseline.json"
RUFF_TARGETS = ["ai-agent/agent", "ai-agent/tests", "ai-agent/main.py", "ai-agent/server.py"]
BANDIT_TARGETS = ["ai-agent/agent"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _ruff_binary() -> str | None:
    """ruff next to the running interpreter, then PATH.

    `pip install --user`/venv puts the console script beside python.exe but
    does not always add that directory to PATH, so a bare which() reports the
    tool as missing in exactly the environment the repo uses.
    """
    candidate = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
    if candidate.is_file():
        return str(candidate)
    return shutil.which("ruff")


def ruff_violations() -> int | None:
    binary = _ruff_binary()
    if not binary:
        return None
    proc = _run([binary, "check", *RUFF_TARGETS, "--output-format=json", "--no-cache"])
    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, list):
        return None
    return len(payload)


def bandit_violations() -> dict[str, int] | None:
    proc = _run(
        [sys.executable, "-m", "bandit", "-r", *BANDIT_TARGETS, "-f", "json", "-q",
         "-x", "tests"]
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "results" not in payload:
        return None
    counts = {"bandit_high": 0, "bandit_medium": 0}
    for finding in payload["results"]:
        severity = str(finding.get("issue_severity", "")).upper()
        if severity == "HIGH":
            counts["bandit_high"] += 1
        elif severity == "MEDIUM":
            counts["bandit_medium"] += 1
    return counts


def measure() -> dict[str, int | None]:
    current: dict[str, int | None] = {"ruff": ruff_violations()}
    bandit = bandit_violations()
    current["bandit_high"] = None if bandit is None else bandit["bandit_high"]
    current["bandit_medium"] = None if bandit is None else bandit["bandit_medium"]
    return current


def check(baseline: dict, current: dict) -> list[str]:
    """Return one failure line per tool that rose or could not be measured."""
    failures: list[str] = []
    for key, floor in baseline.items():
        value = current.get(key)
        if value is None:
            failures.append(f"{key}: not measured (tool unavailable)")
        elif value > floor:
            failures.append(f"{key}: {value} > baseline {floor}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()

    current = measure()
    if args.write_baseline:
        if any(value is None for value in current.values()):
            print(json.dumps(current, indent=1))
            print(
                "Refusing to write a baseline containing an unmeasured tool.",
                file=sys.stderr,
            )
            return 2
        BASELINE.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)}: {current}")
        return 0

    if not BASELINE.is_file():
        print(f"No baseline at {BASELINE}; run with --write-baseline once.", file=sys.stderr)
        return 2

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    failures = check(baseline, current)
    print(json.dumps({"baseline": baseline, "current": current}, indent=1))
    for line in failures:
        print(line, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
