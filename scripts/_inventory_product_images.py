#!/usr/bin/env python3
"""Inventory every hotlinked Unsplash photo across products/*/frontend/src.

Reports which photo IDs are shared between products (the copy-look) and how
many each product uses. Read-only.
"""

from __future__ import annotations

import collections
import itertools
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL_RE = re.compile(r"https://images\.unsplash\.com/[^\"'\s\)]+")
PID_RE = re.compile(r"photo-[0-9a-f\-]+")


def main() -> int:
    per_product: dict[str, set[str]] = {}
    for p in sorted((ROOT / "products").iterdir()):
        if not p.is_dir():
            continue
        fe = p / "frontend" / "src"
        if not fe.exists():
            continue
        found: set[str] = set()
        for f in fe.rglob("*.jsx"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for u in URL_RE.findall(text):
                m = PID_RE.search(u)
                if m:
                    found.add(m.group(0))
        per_product[p.name] = found

    all_pids = set(itertools.chain.from_iterable(per_product.values()))
    print(f"products with hotlinked unsplash: {len(per_product)}")
    print(f"distinct photo IDs: {len(all_pids)}")
    shared = collections.Counter(itertools.chain.from_iterable(per_product.values()))
    print("top shared photo IDs:")
    for pid, n in shared.most_common(10):
        users = sorted(k for k, v in per_product.items() if pid in v)
        print(f"  {n}x  {pid}  [{', '.join(users)}]")
    print("per product:")
    for k, v in sorted(per_product.items()):
        print(f"  {k:18} {len(v)} photos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
