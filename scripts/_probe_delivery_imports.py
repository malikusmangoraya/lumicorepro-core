#!/usr/bin/env python3
"""Throwaway probe: what does a delivery site's src actually import?

Answers the question that decides the shape of the missing build config:
which npm packages must be declared in a package.json for the source to build,
and does it use the `@/` alias that a vite.config.js must define.
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

IMPORT_RE = re.compile(r"""(?:from|import)\s+['"]([^'"]+)['"]""")


def probe(site: pathlib.Path) -> dict:
    src = site / "src"
    mods: collections.Counter = collections.Counter()
    alias = 0
    files = 0
    for f in src.rglob("*.js*"):
        files += 1
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in IMPORT_RE.findall(text):
            if m.startswith("."):
                continue
            if m.startswith("@/"):
                alias += 1
                continue
            parts = m.split("/")
            mods["/".join(parts[:2]) if m.startswith("@") else parts[0]] += 1
    return {
        "site": site.name,
        "files": files,
        "alias_imports": alias,
        "bare_imports": dict(mods.most_common()),
    }


def main() -> int:
    target = ROOT / "delivery" / (sys.argv[1] if len(sys.argv) > 1 else "apex-digital")
    result = probe(target)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
