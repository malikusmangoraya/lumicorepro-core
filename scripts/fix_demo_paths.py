#!/usr/bin/env python3
"""Remove the generator's internal folder names from backend demo data.

`/api/ai/projects` returns a hardcoded offline fallback whose entries carry
paths like `generated-projects/saas`. That string is the name of the folder the
generator wrote projects into on the author's machine — it tells a buyer
nothing useful and reveals how the product was produced, so it is replaced with
a neutral, product-scoped path.

The affected response is only a fallback used when the upstream AI service is
unreachable, so changing the labels cannot alter real behaviour.

    python scripts/fix_demo_paths.py --dry-run
    python scripts/fix_demo_paths.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

TITLES = {
    "apex": "Apex",
    "claimflow-ai": "ClaimFlow",
}


def rewrite(text: str, slug: str) -> tuple[str, int]:
    """Replace `generated-projects/<x>` with a neutral workspace path."""
    new, n = re.subn(r"generated-projects/[A-Za-z0-9_-]+",
                     f"workspace/{slug}", text)
    # Also normalise the hard-coded sample names, which belong to other products.
    new, n2 = re.subn(r"'Aurelia Luxury Commerce'",
                      f"'{TITLES.get(slug, slug)} Showcase'", new)
    new, n3 = re.subn(r"'Ultra SaaS Launchpad'",
                      f"'{TITLES.get(slug, slug)} Workspace'", new)
    return new, n + n2 + n3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]

    print(f"=== fix_demo_paths: {'DRY RUN' if a.dry_run else 'APPLY'} ===")
    total = 0
    for d in dirs:
        touched = []
        for f in (d / "backend").rglob("*.js"):
            if "node_modules" in f.parts:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if "generated-projects" not in text:
                continue
            new, n = rewrite(text, d.name)
            if new == text:
                continue
            if not a.dry_run:
                f.write_text(new, encoding="utf-8")
                proc = subprocess.run(
                    ["node", "--experimental-vm-modules",
                     str(ROOT / "scripts" / "js_parse_check.mjs"), str(f)],
                    capture_output=True, text=True, timeout=120,
                )
                if proc.returncode != 0:
                    print(f"-- {d.name:20} [FAIL] {f.name} no longer parses")
                    return 1
            touched.append(f"{f.relative_to(d).as_posix()} ({n})")
            total += n

        print(f"-- {d.name:20} {len(touched)} file(s)")
        for t in touched:
            print(f"     {t}")

    print(f"\n=== {total} replacement(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())