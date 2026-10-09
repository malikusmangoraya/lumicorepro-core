#!/usr/bin/env python3
"""Verify the built product archives are safe to sell.

A packaging step that runs green proves nothing about what is inside the ZIP.
This script opens every archive and checks the properties that actually matter
to a buyer and to the vendor's reputation:

  * no `node_modules/`, `dist/`, `.git/` or stray sqlite database is included,
  * every file a buyer needs is present (Docker, CI/CD, lockfiles, the full
    documentation set, the auth screens),
  * the fixes that made the products sellable are present inside the archive,
    not only in the working tree — the auth middleware really exports every
    symbol the routes import, the server really mounts routes, the Vite base
    really is environment driven,
  * no generator attribution or developer path leaked into the payload,
  * the recorded SHA-256 matches the archive on disk.

    python scripts/verify_release.py
Exit code is 1 if any archive fails.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys
import zipfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED = [
    "backend/server.js",
    "backend/middleware/auth.js",
    "backend/package-lock.json",
    "frontend/package-lock.json",
    "frontend/vite.config.js",
    "frontend/scripts/postbuild-spa-fallback.mjs",
    ".github/workflows/ci.yml",
    ".github/workflows/deploy.yml",
    "docker-compose.yml",
    "DEPLOYMENT.md", "SECURITY.md", "CHANGELOG.md",
    "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md",
    "COMMERCIAL_LICENSE.md", "LEMON_SQUEEZY_SELLER_KIT.md",
    "frontend/src/pages/Login.jsx", "frontend/src/pages/Register.jsx",
]

FORBIDDEN_PATH_PARTS = ("node_modules/", "/dist/", ".git/", "database.sqlite")
VENDOR_LEAKS = ("AZAM COMPUTERS", "OneDrive", "generated-projects/", "LumicorePro")

AUTH_EXPORTS = ("optionalProtect", "authorize", "adminOnly",
                "generateToken", "registerInMemoryStore")

TEXT_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html",
                 ".yml", ".yaml", ".css")


def check_archive(zip_path: pathlib.Path, manifest: str) -> tuple[list[str], int]:
    problems: list[str] = []
    slug = zip_path.stem

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        blob = {n: zf.read(n) for n in names}

    joined = "\n".join(names)
    for bad in FORBIDDEN_PATH_PARTS:
        if bad in joined:
            problems.append(f"contains {bad!r}")

    for req in REQUIRED:
        if f"{slug}/{req}" not in blob:
            problems.append(f"missing {req}")

    auth = blob.get(f"{slug}/backend/middleware/auth.js", b"").decode("utf-8", "replace")
    for sym in AUTH_EXPORTS:
        if not re.search(rf"export\s+(?:async\s+)?(?:function|const)\s+{sym}\b", auth):
            problems.append(f"auth middleware does not export {sym}")

    server = blob.get(f"{slug}/backend/server.js", b"").decode("utf-8", "replace")
    if "mountRoutes" not in server:
        problems.append("server.js does not mount routes")

    vite = blob.get(f"{slug}/frontend/vite.config.js", b"").decode("utf-8", "replace")
    if "VITE_BASE_PATH" not in vite:
        problems.append("vite base is not env-driven")

    payload = "\n".join(
        blob[n].decode("utf-8", "replace")
        for n in names if n.endswith(TEXT_SUFFIXES)
    )
    for leak in VENDOR_LEAKS:
        if leak in payload:
            problems.append(f"vendor leak in payload: {leak!r}")

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    if digest not in manifest:
        problems.append("sha256 is absent from MANIFEST.txt")

    return problems, len(names)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default="release/products",
                    help="directory holding the built archives")
    a = ap.parse_args()

    release = (ROOT / a.release) if not pathlib.Path(a.release).is_absolute() else pathlib.Path(a.release)
    zips = sorted(release.glob("*.zip"))
    if not zips:
        print(f"No archives in {release}", file=sys.stderr)
        return 2

    manifest_path = release / "MANIFEST.txt"
    manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else ""
    if not manifest:
        print(f"[warn] {manifest_path} not found; digest checks skipped", file=sys.stderr)

    print(f"=== verify_release: {len(zips)} archive(s) in {release} ===")
    failed = 0
    for z in zips:
        problems, entries = check_archive(z, manifest)
        if problems:
            failed += 1
        print(f"[{'PASS' if not problems else 'FAIL'}] {z.stem:20} {entries:>4} entries")
        for p in problems:
            print(f"        - {p}")

    print(f"\n=== {len(zips) - failed}/{len(zips)} archives verified ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())