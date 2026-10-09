#!/usr/bin/env python3
"""Repair GitHub Pages URLs that carry the brand casing instead of the repo casing.

GitHub Pages paths are case-sensitive, so a canonical written with the brand's
display casing - `github.io/ClaimFlow` - 404s even though the deployment is
live at `github.io/claimflow`. That URL is the source of truth for every
canonical tag: `LIVE_URL.txt`, `index.html` canonical and Open Graph tags,
`sitemap.xml`, `structured-data.json`, `seo-config.json` and `hreflang-config.json`
all copy from it, so one wrong letter de-indexes the whole product.

Found by fetching the live URL in `products/README.md` for all ten products:
eight answered 200, `ClaimFlow` and `ResuPro` answered 404, and fetching the
lowercase form returned each product's own branded <title>, confirming the
deployment is live and only the spelling was wrong.

Usage:  python scripts/fix_canonical_urls.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage"}

# Display name -> the repo path segment Pages actually serves.
RENAMES = {
    "github.io/ClaimFlow": "github.io/claimflow",
    "github.io/ResuPro": "github.io/resupro",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    total = 0

    for path in sorted(PRODUCTS_DIR.rglob("*")):
        if not path.is_file() or any(p in SKIP_DIRS for p in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        new = text
        hits = 0
        for old, correct in RENAMES.items():
            n = new.count(old)
            if n:
                new = new.replace(old, correct)
                hits += n
        if not hits:
            continue

        total += hits
        changed += 1
        rel = path.relative_to(ROOT).as_posix()
        if args.dry_run:
            print(f"  would fix {hits:3d}  {rel}")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"  fixed    {hits:3d}  {rel}")

    verb = "would fix" if args.dry_run else "fixed"
    print(f"\n{verb} {total} reference(s) across {changed} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())