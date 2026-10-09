#!/usr/bin/env python3
"""Add `prefers-reduced-motion` support where the global stylesheet lacks it.

Two of the products ship animations that ignore the operating-system "reduce
motion" setting. For a product sold on accessibility grounds, and for anyone
sensitive to motion, that is a real defect rather than a nice-to-have.

This appends a single, self-contained block to the global stylesheet of any
project that does not already honour the preference. The block is additive and
scoped to the media query, so nothing else changes.

    python scripts/add_reduced_motion.py --dry-run
    python scripts/add_reduced_motion.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

MARKER = "prefers-reduced-motion"

BLOCK = """
/* ── Reduced motion ───────────────────────────────────────────────────────────
 * Honour the operating-system "reduce motion" setting. Animations and smooth
 * scrolling are shortened rather than removed, so layout and transitions stay
 * intact for people who set the preference. */
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto !important;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
"""


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

    print(f"=== add_reduced_motion: {'DRY RUN' if a.dry_run else 'APPLY'} ===")
    changed = 0
    for d in dirs:
        css_dir = d / "frontend" / "src"
        if not css_dir.is_dir():
            print(f"-- {d.name:20} no frontend/src — skipped")
            continue

        # A project-level stylesheet that already covers it needs no change.
        already = any(
            MARKER in f.read_text(encoding="utf-8", errors="replace")
            for f in css_dir.rglob("*.css")
        )
        if already:
            print(f"-- {d.name:20} already honours {MARKER} — skipped")
            continue

        entry = css_dir / "index.css"
        if not entry.is_file():
            print(f"-- {d.name:20} no index.css — skipped")
            continue

        if not a.dry_run:
            entry.write_text(
                entry.read_text(encoding="utf-8", errors="replace").rstrip("\n") + "\n" + BLOCK,
                encoding="utf-8",
            )
        changed += 1
        print(f"-- {d.name:20} [ok] appended the {MARKER} block to src/index.css")

    print(f"\n=== {changed} stylesheet(s) updated ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())