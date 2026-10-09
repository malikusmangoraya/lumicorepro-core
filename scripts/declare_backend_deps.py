#!/usr/bin/env python3
"""Declare the npm packages each backend imports but does not depend on.

The generated backends import 16 packages that appear nowhere in
`backend/package.json` — winston, bullmq, ioredis, zod, stripe, nodemailer and
others. A fresh `npm ci` therefore installs a tree that cannot satisfy those
imports, and every module that touches one fails to load. The route isolation
in server.js hides that at boot, but the feature is simply dead.

This maps every bare import in the backend to its declared version, and records
only the ones that are genuinely missing.

    python scripts/declare_backend_deps.py --dry-run
    python scripts/declare_backend_deps.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage"}

# Node built-ins; never declared as dependencies.
NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "domain",
    "events", "fs", "http", "http2", "https", "inspector", "module", "net",
    "os", "path", "perf_hooks", "process", "punycode", "querystring", "readline",
    "repl", "stream", "string_decoder", "sys", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}

# Known-good major lines. Anything not listed is reported but never guessed.
PINNED: dict[str, str] = {
    "@sentry/node": "^8.0.0",
    "awilix": "^8.0.1",
    "bullmq": "^5.12.0",
    "ioredis": "^5.4.1",
    "multer": "^1.4.5-lts.1",
    "node-fetch": "^3.3.2",
    "nodemailer": "^6.9.14",
    "pg": "^8.13.1",
    "sequelize": "^6.37.5",
    "passport": "^0.7.0",
    "passport-github2": "^0.1.12",
    "passport-google-oauth20": "^2.0.0",
    "rate-limit-redis": "^4.2.0",
    "react-turnstile": "^1.0.0",
    "sharp": "^0.33.5",
    "stripe": "^16.12.0",
    "winston": "^3.15.0",
    "zod": "^3.23.8",
}

IMPORT_RE = re.compile(
    r"""(?:^|\s)(?:import\s[^'"]*?from\s*|import\s*|export\s[^'"]*?from\s*|"""
    r"""require\s*\(\s*)['"]([^'"]+)['"]""",
    re.M,
)


def bare_package(spec: str) -> str | None:
    if not spec or spec.startswith(".") or spec.startswith("/"):
        return None
    if spec.startswith("node:"):
        return None
    parts = spec.split("/")
    if spec.startswith("@"):
        return "/".join(parts[:2]) if len(parts) >= 2 else None
    return parts[0]


def imported_packages(be: Path) -> set[str]:
    found: set[str] = set()
    for f in be.rglob("*.js"):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in IMPORT_RE.finditer(text):
            pkg = bare_package(m.group(1))
            if pkg and pkg not in NODE_BUILTINS and not pkg.startswith("node:"):
                found.add(pkg)
    return found


@dataclass
class Report:
    name: str
    added: dict[str, str] = field(default_factory=dict)
    unknown: list[str] = field(default_factory=list)


def process(proj: Path, dry: bool) -> Report:
    rep = Report(name=proj.name)
    be = proj / "backend"
    pj = be / "package.json"
    if not pj.is_file():
        return rep

    data = json.loads(pj.read_text(encoding="utf-8"))
    declared = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    missing = sorted(p for p in imported_packages(be) if p not in declared)

    for pkg in missing:
        version = PINNED.get(pkg)
        if version is None:
            rep.unknown.append(pkg)
            continue
        rep.added[pkg] = version

    if rep.added and not dry:
        data.setdefault("dependencies", {}).update(rep.added)
        pj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rep


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

    print(f"=== declare_backend_deps: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)}) ===")
    total_added = 0
    unknown: set[str] = set()
    for d in dirs:
        rep = process(d, a.dry_run)
        total_added += len(rep.added)
        unknown.update(rep.unknown)
        listed = ", ".join(f"{k}@{v}" for k, v in sorted(rep.added.items())) or "none"
        print(f"-- {rep.name:20} +{len(rep.added):<2} {listed}")
        if rep.unknown:
            print(f"     NEEDS A VERSION: {', '.join(sorted(rep.unknown))}")

    print(f"\n=== {total_added} dependency declaration(s) added ===")
    if unknown:
        print(f"REVIEW: no version pinned for: {', '.join(sorted(unknown))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())