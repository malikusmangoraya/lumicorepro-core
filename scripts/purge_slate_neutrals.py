"""Purge slate-blue literals (#0f172a / #1e293b) to hue-neutral equivalents
across every project's source (src/, public/, tailwind.config) so dists stay
zero-blue. Idempotent. Usage: python scripts/purge_slate_neutrals.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

REPLACEMENTS = [
    # slate neutrals that read blue-ish
    ("#0f172a", "#0e1116"),
    ("#1e293b", "#26292f"),
    ("--t-text-rgb: 30 41 59", "--t-text-rgb: 38 41 47"),
    ("--t-text-rgb:30 41 59", "--t-text-rgb:38 41 47"),
    # saturated Tailwind blue/sky family -> hue-neutral equivalents that keep
    # roughly the same lightness, so contrast survives the de-blue pass
    ("#3b82f6", "#4b5563"),   # blue-500 -> gray-600
    ("#60a5fa", "#9ca3af"),   # blue-400 -> gray-400
    ("#1d4ed8", "#1f2937"),   # blue-700 -> gray-800
    ("#1e40af", "#111827"),   # blue-800 -> gray-900
    ("#2563eb", "#374151"),   # blue-600 -> gray-700
    ("#1e3a8a", "#1f2937"),   # blue-900 -> gray-800
    ("#172554", "#111827"),   # blue-950 -> gray-900
    ("#0ea5e9", "#6b7280"),   # sky-500 -> gray-500
    ("#0284c7", "#4b5563"),   # sky-600 -> gray-600
    ("#0369a1", "#374151"),   # sky-700 -> gray-700
    ("#38bdf8", "#9ca3af"),   # sky-400 -> gray-400
    ("#22d3ee", "#a1a1aa"),   # cyan-400 -> zinc-400
    ("#06b6d4", "#71717a"),   # cyan-600 -> zinc-500
]

TARGETS = re.compile(r".*\.(jsx?|css|html|svg|tsx?|json)$")


def purge(root: str, dist: bool = False) -> dict:
    base = PROJECTS / root / "frontend"
    if not base.exists():
        return {"changed": 0, "files": 0}
    if dist:
        kinds = ["dist"]
    else:
        # index.html at the Vite root is the entry template: it carries the
        # theme-color/OG meta and is copied verbatim into dist, so scanning only
        # src/ and public/ left #0f172a in every build.
        kinds = ["src", "public"]
        for extra in ("tailwind.config.js", "index.html", "index.css"):
            if (base / extra).exists():
                kinds.append(extra)
    changed = files = 0
    for kind in kinds:
        if kind in ("tailwind.config.js", "index.html", "index.css"):
            paths = [base / kind]
        else:
            paths = list((base / kind).rglob("*"))
        for p in paths:
            if not p.is_file() or not TARGETS.match(p.name):
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if not t:
                continue
            if any(r[0] in t for r in REPLACEMENTS):
                for old, new in REPLACEMENTS:
                    t = t.replace(old, new)
                p.write_text(t, encoding="utf-8")
                changed += 1
            files += 1
    return {"changed": changed, "files": files}


def main():
    args = sys.argv[1:]
    dist = "--dist" in args
    slugs = [a for a in args if not a.startswith("--")] or [
        d.name for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    total = files = 0
    for s in slugs:
        r = purge(s, dist=dist)
        total += r["changed"]
        files += r["files"]
        if r["changed"]:
            print(f"  {s}: {r['changed']} files touched")
    where = "dist/" if dist else "source"
    print(f"purge-slate ({where}): {total} files changed across {len(slugs)} projects")


if __name__ == "__main__":
    main()