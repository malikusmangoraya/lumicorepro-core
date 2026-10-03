"""Build every project and report pass/fail with the actual error.

Usage: python scripts/build_all_projects.py [slug ...]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"


def slugs():
    return [d.name for d in sorted(PROJECTS.iterdir()) if (d / "frontend" / "package.json").exists()]


def build(slug: str, timeout: int = 420) -> tuple:
    fe = PROJECTS / slug / "frontend"
    npm = shutil.which("npm") or shutil.which("npm.cmd") or r"C:\Program Files\nodejs\npm.cmd"
    try:
        p = subprocess.run(
            [npm, "run", "build"],
            cwd=str(fe), capture_output=True, text=True, timeout=timeout,
            shell=True,
        )
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode == 0:
        return True, "ok"
    # extract the most useful error line
    for marker in ("[MISSING_EXPORT]", "error:", "Error:", "not exported"):
        for line in out.splitlines():
            if marker in line:
                return False, line.strip()[:200]
    return False, (out.strip().splitlines() or ["unknown error"])[-1][:200]


def main():
    targets = sys.argv[1:] or slugs()
    ok, bad = [], []
    for i, s in enumerate(targets, 1):
        passed, msg = build(s)
        if passed:
            ok.append(s)
            print(f"[{i}/{len(targets)}] PASS {s}")
        else:
            bad.append((s, msg))
            print(f"[{i}/{len(targets)}] FAIL {s} :: {msg}", flush=True)
    print()
    print(f"green: {len(ok)}/{len(targets)} | failed: {len(bad)}")
    if bad:
        print("\nFAILURES:")
        for s, m in bad:
            print(f"  {s}: {m}")
        Path(ROOT / "generated-projects" / "BUILD_FAILURES.json").write_text(
            json.dumps([{"slug": s, "error": m} for s, m in bad], indent=1), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())