#!/usr/bin/env python3
"""Repair cross-project brand contamination.

Two of the shipped products carry a different product's name throughout their
code, page metadata and copy:

    claimflow-ai  is titled "Adjusterly"   (a claims product from another run)
    resupro       is titled "Deckflow"     (a presentation product)

A buyer who sees "Deckflow" in a résumé builder has been sold the wrong thing,
and the mismatch would show up immediately in a code review or a screenshot.

This rewrites the wrong name to the correct one everywhere it appears in code,
styles, metadata and documentation, then reports what changed. File names are
renamed too when they carry the old name.

    python scripts/fix_brand_names.py --dry-run
    python scripts/fix_brand_names.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"
SKIP = {"node_modules", ".git", "dist", "build", "coverage", ".history"}
TEXT_EXT = {".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css",
            ".yml", ".yaml", ".svg", ".txt", ".example", ".env"}

# product slug -> (wrong name, correct name)
FIXES = {
    "claimflow-ai": ("Adjusterly", "ClaimFlow"),
    "resupro": ("Deckflow", "ResuPro"),
}

# Brand words that are correct as written and must not be rewritten.
PROTECTED = {"Adjusterly".lower()}


def is_brand_ish(word: str, wrong: str) -> bool:
    """Only rewrite when the token is the brand name, not a substring of it."""
    return word.lower() not in PROTECTED


def rename_paths(root: Path, wrong: str, correct: str, dry: bool) -> list[str]:
    moved = []
    for f in list(root.rglob("*")):
        if not f.is_file() or any(part in SKIP for part in f.parts):
            continue
        if wrong.lower() in f.name.lower():
            new = f.with_name(re.sub(re.escape(wrong), correct, f.name, flags=re.I))
            if new != f and not new.exists():
                moved.append(f"{f.relative_to(root)} -> {new.name}")
                if not dry:
                    f.rename(new)
    return moved


def rewrite_text(root: Path, wrong: str, correct: str, dry: bool) -> tuple[int, list[str]]:
    changed_files = 0
    hits = 0
    samples: list[str] = []
    # Word-boundary match, case-insensitive, so "Adjusterly" matches but a
    # longer unrelated identifier containing it does not.
    rx = re.compile(rf"\b{re.escape(wrong)}\b", re.I)

    for f in list(root.rglob("*")):
        if not f.is_file() or any(part in SKIP for part in f.parts):
            continue
        if f.suffix.lower() not in TEXT_EXT and f.name != ".env.example":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n = len(rx.findall(text))
        if not n:
            continue
        if not dry:
            f.write_text(rx.sub(correct, text), encoding="utf-8")
        changed_files += 1
        hits += n
        if len(samples) < 3:
            samples.append(f"{f.relative_to(root).as_posix()} ({n})")
    return hits, samples


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    print(f"=== fix_brand_names: {'DRY RUN' if a.dry_run else 'APPLY'} ===")
    total = 0
    for slug, (wrong, correct) in FIXES.items():
        proj = PRODUCTS / slug
        if not proj.is_dir():
            print(f"-- {slug:20} not found — skipped")
            continue

        moved = rename_paths(proj, wrong, correct, a.dry_run)
        hits, samples = rewrite_text(proj, wrong, correct, a.dry_run)
        total += hits

        print(f"-- {slug:20} {wrong!r} -> {correct!r}: {hits} occurrence(s) in "
              f"{len(samples) if not samples else ''}{len(moved) and len(moved)}")
        for s in samples:
            print(f"     {s}")
        for m in moved:
            print(f"     renamed {m}")

    print(f"\n=== {total} occurrence(s) rewritten ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())