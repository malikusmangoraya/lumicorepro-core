#!/usr/bin/env python3
"""Dump every hotlinked Unsplash URL with product, file and line.

Output: docs/audit/product_image_urls.json mapping
  product -> [{file, line, url, photo_id}]
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "audit" / "product_image_urls.json"
URL_RE = re.compile(r"https://images\.unsplash\.com/[^\"'\s\)]+")
PID_RE = re.compile(r"photo-[0-9a-f\-]+")


def main() -> int:
    data: dict[str, list[dict]] = {}
    for p in sorted((ROOT / "products").iterdir()):
        if not p.is_dir():
            continue
        fe = p / "frontend" / "src"
        if not fe.exists():
            continue
        rows: list[dict] = []
        for f in sorted(fe.rglob("*.jsx")):
            for i, line in enumerate(
                f.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                for u in URL_RE.findall(line):
                    m = PID_RE.search(u)
                    rows.append(
                        {
                            "file": str(f.relative_to(fe)),
                            "line": i,
                            "url": u,
                            "photo_id": m.group(0) if m else None,
                        }
                    )
        data[p.name] = rows
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in data.values())
    print(f"products: {len(data)}  hotlinked refs: {total}  -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
