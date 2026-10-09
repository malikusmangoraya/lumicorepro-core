#!/usr/bin/env python3
"""Build a sale-ready archive for every product.

A deliverable must not contain anything the buyer can regenerate or that
belongs only to this machine. This script:

  * strips `node_modules/`, `dist/` and stray sqlite databases, which are
    reproduced by `npm ci` and `npm run build`,
  * zips the remainder with deterministic ordering, a fixed timestamp and a
    normalised permission set, so the same input always yields the same bytes,
  * writes a manifest beside each archive recording the file count, unpacked
    size and a SHA-256 digest,
  * refuses to finish if a forbidden path survived into an archive.

    python scripts/package_products.py --dry-run
    python scripts/package_products.py --out release/products
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

# Regenerable or machine-local. Never shipped.
STRIP_DIRS = {"node_modules", "dist", "build", "coverage", ".git", ".history", ".pytest_cache"}
STRIP_FILES = {"database.sqlite", "database.sqlite-journal", ".DS_Store", "Thumbs.db"}
STRIP_SUFFIX = {".sqlite", ".sqlite3", ".log"}

# Anything matching these must never reach a buyer.
FORBIDDEN = (
    ".env", "id_rsa", "id_ed25519", ".npmrc", ".netrc",
    ".git/config", ".env.production", ".env.staging", ".env.local",
)

# A fixed timestamp keeps the archive byte-identical between runs.
FIXED_DATE = (2020, 1, 1, 0, 0, 0)


def should_skip(path: Path) -> bool:
    if path.name in STRIP_FILES:
        return True
    if path.suffix.lower() in STRIP_SUFFIX:
        return True
    return False


def is_forbidden(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if any(rel.endswith(f) for f in FORBIDDEN):
        return True
    return ".git/" in rel or "/.git" in rel


def collect(src: Path) -> list[Path]:
    out: list[Path] = []
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if any(part in STRIP_DIRS for part in f.relative_to(src).parts):
            continue
        if should_skip(f):
            continue
        out.append(f)
    return out


def strip(src: Path, dry: bool) -> int:
    removed = 0
    for d in ("node_modules", "dist"):
        for target in list(src.rglob(d)):
            if any(part in {"node_modules", "dist"} for part in target.parts[:1]):
                continue
            if target.is_dir() and not dry:
                shutil.rmtree(target, ignore_errors=True)
                removed += 1
    for f in list(src.rglob("*.sqlite")) + list(src.rglob("*.sqlite3")):
        if not dry:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed


@dataclass
class Built:
    slug: str
    zip_path: Path
    files: int
    unpacked: int
    sha256: str
    violations: list[str]


def build(slug: str, src: Path, out_dir: Path) -> Built:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{slug}.zip"
    files = collect(src)
    violations: list[str] = []
    unpacked = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for f in files:
            rel = f.relative_to(src).as_posix()
            if is_forbidden(rel):
                violations.append(rel)
                continue
            data = f.read_bytes()
            unpacked += len(data)
            info = zipfile.ZipInfo(f"{slug}/{rel}", date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0644 for files, so the archive is identical across machines.
            info.external_attr = (0o100644) << 16
            z.writestr(info, data)

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return Built(slug, zip_path, len(files), unpacked, digest, violations)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="release/products")
    ap.add_argument("--only", action="append")
    ap.add_argument("--keep-artifacts", action="store_true",
                    help="do not delete node_modules/dist before zipping")
    a = ap.parse_args()

    out_dir = (ROOT / a.out) if not Path(a.out).is_absolute() else Path(a.out)

    dirs = sorted(q for q in PRODUCTS.iterdir()
                  if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if q.name in a.only]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    print(f"=== package_products: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)}) ===")
    if not a.keep_artifacts and not a.dry_run:
        print("stripping regenerable artefacts (node_modules, dist, *.sqlite) ...")

    results = []
    for d in dirs:
        removed = 0 if (a.dry_run or a.keep_artifacts) else strip(d, a.dry_run)
        b = build(d.name, d, out_dir)
        results.append(b)
        size_mb = b.zip_path.stat().st_size / 1_048_576
        print(f"-- {b.slug:20} {size_mb:6.2f} MB  {b.files:>5} files  "
              f"{b.unpacked / 1_048_576:6.1f} MB unpacked  sha256 {b.sha256[:16]}…")
        if removed:
            print(f"     stripped {removed} artefact path(s)")
        if b.violations:
            print(f"     [FAIL] {len(b.violations)} forbidden entr(y/ies): {b.violations[:5]}")

    # Manifest
    manifest = out_dir / "MANIFEST.txt"
    lines = [
        "Product archives — SHA-256 manifest",
        "",
        "Verify a download with:  sha256sum <file>.zip",
        "",
    ]
    for b in results:
        lines += [
            f"{b.sha256}  {b.zip_path.name}",
            f"    files={b.files}  unpacked_bytes={b.unpacked}",
        ]
    if not a.dry_run:
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    bad = [b for b in results if b.violations]
    total_mb = sum(b.zip_path.stat().st_size for b in results) / 1_048_576
    print(f"\n=== {len(results)} archive(s), {total_mb:.1f} MB total ===")
    print(f"manifest: {manifest}")
    if bad:
        print(f"FAIL: {len(bad)} archive(s) contain forbidden entries")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())