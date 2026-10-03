"""
Codex Dev Loop - LumiCorePro Integration Wrapper

Runs the codex-dev-loop harness for autonomous development within LumiCorePro.
Provides TDD gates, spec baselines, quality checks, and PR automation.

Usage:
    python scripts/dev_loop.py --goal "Add user auth" --scale standard
    python scripts/dev_loop.py --goal "Fix login bug" --scale small
    python scripts/dev_loop.py --spec specs/my-feature.md
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "vendors" / "codextron-dev" / "scripts" / "dev_loop_harness.py"


def main():
    parser = argparse.ArgumentParser(description="Codex Dev Loop for LumiCorePro")
    parser.add_argument("--goal", help="Development goal description")
    parser.add_argument("--spec", help="Path to spec markdown file")
    parser.add_argument("--scale", choices=["small", "standard", "large"], default="standard")
    parser.add_argument("--mode", choices=["plan", "implement", "review", "ship"], default="implement")
    args = parser.parse_args()

    if not HARNESS.exists():
        print(f"ERROR: Dev loop harness not found at {HARNESS}")
        print("Run: git clone https://github.com/Thyd/codex-dev-loop.git vendors/codextron-dev")
        sys.exit(1)

    cmd = [sys.executable, str(HARNESS)]
    if args.goal:
        cmd.extend(["--goal", args.goal])
    if args.spec:
        cmd.extend(["--spec", args.spec])
    cmd.extend(["--scale", args.scale, "--mode", args.mode])

    print(f"[dev-loop] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
