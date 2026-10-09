#!/usr/bin/env python3
"""Measure a real production build of every product's frontend.

STRUCTURE_REPORT.md previously carried "None KB" for the products whose build
had never been run, which is an unverifiable claim in a buyer-facing document.
This installs, builds and measures each product so every shipped number comes
from an actual `vite build`.

For each product it records, in gzip bytes as a browser would download them:
  * first-paint JS — the entry chunk plus everything it statically imports,
    read from the Vite manifest so the number is not a guess,
  * the largest single JS chunk,
  * total CSS,
  * build wall-clock time.

    python scripts/measure_product_bundles.py               # all products
    python scripts/measure_product_bundles.py --only apex
    python scripts/measure_product_bundles.py --json out.json

Exit code is 1 if any product fails to install or build.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"


def gz_size(path: pathlib.Path) -> int:
    return len(gzip.compress(path.read_bytes(), compresslevel=9))


def lib_size(path: pathlib.Path) -> int:
    """Bytes a browser downloads: the Brotli/gzip transfer size."""
    return gz_size(path)


def measure(product: pathlib.Path) -> dict:
    frontend = product / "frontend"
    result: dict = {"product": product.name, "frontend": str(frontend)}
    if not (frontend / "package.json").is_file():
        result["error"] = "no frontend/package.json"
        return result

    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        result["error"] = "npm not found on PATH"
        return result

    install = subprocess.run(
        [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        cwd=frontend, capture_output=True, text=True, shell=False,
    )
    if install.returncode != 0:
        result["error"] = "npm ci failed"
        result["stderr"] = install.stderr[-800:]
        return result

    started = time.time()
    build = subprocess.run(
        [npm, "run", "build"], cwd=frontend, capture_output=True, text=True, shell=False,
    )
    result["build_seconds"] = round(time.time() - started, 1)
    if build.returncode != 0:
        result["error"] = "build failed"
        result["stderr"] = build.stderr[-1200:]
        return result

    dist = frontend / "dist"
    assets = dist / "assets"
    index = dist / "index.html"
    if not index.is_file():
        result["error"] = "no dist/index.html"
        return result

    # No Vite build manifest is emitted by these configs (dist/manifest.json is
    # the PWA manifest), so first paint is read from what index.html tells the
    # browser to fetch: the module entry plus every modulepreload it lists.
    html = index.read_text(encoding="utf-8", errors="replace")
    refs = set(re.findall(r'<script[^>]+src="([^"]+)"', html))
    refs |= set(re.findall(r'<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"', html))
    refs |= set(re.findall(r'<link[^>]+href="([^"]+)"[^>]+rel="modulepreload"', html))

    first_paint = 0
    entry = None
    counted: list[str] = []
    for ref in sorted(refs):
        if not ref.endswith(".js"):
            continue
        rel = ref.lstrip("./").lstrip("/")
        path = dist / rel
        if not path.is_file():
            path = dist / pathlib.Path(rel).name
        if path.is_file():
            first_paint += lib_size(path)
            counted.append(path.name)
            if entry is None or "index-" in path.name:
                entry = path.name

    if not counted:
        result["error"] = "index.html references no JS — nothing to measure"
        return result

    js_files = sorted(assets.glob("*.js")) if assets.is_dir() else []
    css_files = sorted(assets.glob("*.css")) if assets.is_dir() else []
    largest = max((lib_size(p) for p in js_files), default=0)
    # CSS the browser blocks on: the stylesheets index.html links.
    css_refs = set(re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html))
    css_refs |= set(re.findall(r'<link[^>]+href="([^"]+)"[^>]+rel="stylesheet"', html))
    blocking_css = 0
    for ref in sorted(css_refs):
        rel = ref.lstrip("./").lstrip("/")
        path = dist / rel
        if not path.is_file():
            path = dist / pathlib.Path(rel).name
        if path.is_file():
            blocking_css += lib_size(path)

    result.update(
        {
            "entry": entry,
            "first_paint_chunks": counted,
            "first_paint_js_kb": round(first_paint / 1024, 1),
            "largest_chunk_kb": round(largest / 1024, 1),
            "css_kb": round((blocking_css or sum(lib_size(p) for p in css_files)) / 1024, 1),
            "js_chunks": len(js_files),
            "css_files": len(css_files),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="single product directory name")
    parser.add_argument("--json", help="write the measurements to this path")
    parser.add_argument("--keep-node-modules", action="store_true",
                        help="do not delete node_modules/dist after measuring")
    args = parser.parse_args()

    products = sorted(
        p for p in PRODUCTS.iterdir() if p.is_dir() and (p / "frontend").is_dir()
    )
    if args.only:
        products = [p for p in products if p.name == args.only]
    if not products:
        print("no products selected", file=sys.stderr)
        return 1

    print(f"=== measuring {len(products)} product build(s) ===")
    results = []
    failures = 0
    for product in products:
        print(f"  {product.name:<18} ", end="", flush=True)
        row = measure(product)
        results.append(row)
        if "error" in row:
            failures += 1
            print(f"FAILED — {row['error']}")
        else:
            print(
                f"first-paint {row['first_paint_js_kb']:>6.1f} KB gz | "
                f"largest {row['largest_chunk_kb']:>6.1f} KB | "
                f"css {row['css_kb']:>5.1f} KB | {row['build_seconds']}s"
            )
        if not args.keep_node_modules:
            shutil.rmtree(product / "frontend" / "node_modules", ignore_errors=True)
            shutil.rmtree(product / "frontend" / "dist", ignore_errors=True)

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        print(f"\nwrote {args.json}")

    print(f"\n{len(results) - failures}/{len(results)} measured successfully")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
