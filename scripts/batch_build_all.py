"""Batch-build all generated projects and report status + blue/gold audit."""
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

BLUE_RE = re.compile(r"#(?:2563eb|1d4ed8|1e40af|3b82f6|0ea5e9|0284c7|0369a1|60a5fa|0f172a|1e3a8a|172554|1e293b)\b", re.I)
GOLD_RE = re.compile(r"#(?:b8860b|8b4513|daa520|a16207|b45309)\b", re.I)


def build(front: Path) -> tuple:
    exe = "npm.cmd"
    p = subprocess.run([exe, "run", "build"], cwd=str(front),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = p.returncode == 0 and "built in" in (p.stdout + p.stderr)
    msg = (p.stdout + p.stderr).strip().splitlines()
    tail = " | ".join(x.strip() for x in msg[-3:] if x.strip())
    return ok, tail[:220]


def audit(front: Path) -> dict:
    dist = front / "dist" / "assets"
    blue = gold = 0
    files = 0
    if dist.exists():
        for f in glob.glob(str(dist / "*.js")) + glob.glob(str(dist / "*.css")):
            t = open(f, encoding="utf-8", errors="replace").read()
            files += 1
            blue += len(BLUE_RE.findall(t))
            gold += len(GOLD_RE.findall(t))
    return {"files": files, "blue": blue, "gold": gold}


def main():
    slugs = sys.argv[1:] or [
        d.name for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    results = []
    for s in slugs:
        front = PROJECTS / s / "frontend"
        if not front.exists():
            continue
        ok, tail = build(front)
        au = audit(front)
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {s}  blue={au['blue']} gold={au['gold']}  {tail[:140] if not ok else ''}")
        results.append({"slug": s, "ok": ok, **au, "tail": tail})
        if not ok:
            print("   ^^^ BUILD FAILED:", tail)

    ok_n = sum(1 for r in results if r["ok"])
    blue_n = sum(1 for r in results if r["blue"] == 0)
    gold_n = sum(1 for r in results if r["gold"] == 0)
    print("\n=== SUMMARY ===")
    print(f"build green : {ok_n}/{len(results)}")
    print(f"zero blue   : {blue_n}/{len(results)}")
    print(f"zero gold   : {gold_n}/{len(results)}")
    if ok_n != len(results):
        print("FAILED:", [r["slug"] for r in results if not r["ok"]])
    return 0 if ok_n == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())