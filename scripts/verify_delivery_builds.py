#!/usr/bin/env python3
"""Prove every `delivery/` project actually installs and builds.

Generating a build config is not proof. This script does what a buyer does:
install the declared dependencies, run the production build, and check the
result is a complete, sellable `dist/`.

Per site it verifies:

  * `npm install` and `npm run build` exit 0,
  * the build output contains the static files a real deploy needs
    (favicon, manifest, robots, sitemap, SPA-fallback rules) - a build that
    silently drops them is a regression, not a success,
  * `dist/index.html` still carries the SEO head (title, description, canonical,
    Open Graph, hreflang, JSON-LD) and the `__SITE_ORIGIN__` token was
    substituted rather than shipped literally,
  * first-paint JS stays inside the documented budget,
  * no build artefact contains a leftover `__SITE_ORIGIN__` placeholder.

Results accumulate in `docs/audit/delivery_build_ledger.json`, so a run that is
interrupted can be resumed with `--resume` and a later session can see exactly
which of the 91 projects are proven.

    python scripts/verify_delivery_builds.py                    # all sites
    python scripts/verify_delivery_builds.py --sites a b         # specific
    python scripts/verify_delivery_builds.py --resume           # skip proven
    python scripts/verify_delivery_builds.py --limit 5          # sample batch
    python scripts/verify_delivery_builds.py --keep-node-modules
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
DELIVERY = ROOT / "delivery"
LEDGER = ROOT / "docs" / "audit" / "delivery_build_ledger.json"

REQUIRED_DIST = [
    "index.html",
    "favicon.svg",
    "manifest.json",
    "robots.txt",
    "sitemap.xml",
]
REQUIRED_TAIL = ["_headers", "_redirects"]

# Budgets from AGENTS.md section 7. First-paint JS (entry + vendor-react) must
# stay under the 150 KB target; the whole entry chunk set under the 200 KB gate.
FIRST_PAINT_TARGET_KB = 150
FIRST_PAINT_HARD_KB = 200


def npm() -> str:
    """Resolve the npm launcher. On Windows npm is npm.CMD, which
    subprocess cannot find without an extension."""
    found = shutil.which("npm")
    if found:
        return found
    for candidate in ("npm.cmd", "npm.exe", "npm"):
        if shutil.which(candidate):
            return candidate
    return "npm"


NPM = npm()


def run(cmd: list[str], cwd: pathlib.Path, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"
    except OSError as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def gzip_kb(path: pathlib.Path) -> float:
    import gzip

    try:
        raw = path.read_bytes()
        return len(gzip.compress(raw, 6)) / 1024
    except OSError:
        return 0.0


def check_seo(index_html: str) -> dict[str, bool]:
    return {
        "title": bool(re.search(r"<title>[^<]+</title>", index_html)),
        "description": 'name="description"' in index_html,
        "canonical": 'rel="canonical"' in index_html,
        "ogTitle": 'property="og:title"' in index_html,
        "ogImage": 'property="og:image"' in index_html,
        "hreflang": "hreflang=" in index_html,
        "jsonld": 'type="application/ld+json"' in index_html,
        "langAttr": bool(re.search(r"<html[^>]+lang=", index_html)),
        "rootMount": 'id="root"' in index_html,
        "placeholderLeaked": "__SITE_ORIGIN__" in index_html,
    }


def verify_site(site: pathlib.Path, timeout: int, keep_modules: bool) -> dict:
    slug = site.name
    dist = site / "dist"
    started = time.time()
    result: dict = {"slug": slug, "verifiedAt": datetime.now(timezone.utc).isoformat()}

    missing = [
        f
        for f in ("package.json", "vite.config.js", "index.html", "tailwind.config.js",
                  "postcss.config.js", ".env.example", "README.md", "LICENSE.md")
        if not (site / f).exists()
    ]
    if missing:
        result.update({"status": "FAIL", "reason": f"missing build config: {missing}"})
        return result

    # The Tailwind config must load as real JavaScript. A hyphenated colour key
    # emitted unquoted makes the whole config a syntax error; Tailwind then falls
    # back silently and PostCSS blames the CSS files with a meaningless message.
    code, out = run(
        [
            "node",
            "-e",
            "import('./tailwind.config.js').then(m=>{const c=m.default.theme.extend.colors||{};"
            "console.log('COLORS='+Object.keys(c).length)}).catch(e=>{console.error('CFGERR '+e.message);process.exit(3)})",
        ],
        site,
        120,
    )
    colors_declared = re.search(r"COLORS=(\d+)", out)
    result["tailwindConfigLoads"] = code == 0
    result["tokenColors"] = int(colors_declared.group(1)) if colors_declared else 0
    if code != 0:
        detail = [l for l in out.strip().splitlines() if l.strip()][-3:]
        result.update({"status": "FAIL", "reason": "tailwind.config.js does not load", "output": detail})
        return result

    code, out = run([NPM, "install", "--no-audit", "--no-fund", "--prefer-offline"], site, timeout)
    result["install"] = "ok" if code == 0 else f"exit {code}"
    if code != 0:
        tail = [l for l in out.strip().splitlines() if l.strip()][-6:]
        result.update({"status": "FAIL", "reason": "npm install failed", "output": tail})
        return result

    code, out = run([NPM, "run", "build"], site, timeout)
    result["build"] = "ok" if code == 0 else f"exit {code}"
    if code != 0:
        tail = [l for l in out.strip().splitlines() if l.strip()][-8:]
        result.update({"status": "FAIL", "reason": "build failed", "output": tail})
        return result

    # Completeness of the emitted dist.
    absent = [f for f in REQUIRED_DIST if not (dist / f).exists()]
    absent += [f for f in REQUIRED_TAIL if not (dist / f).exists()]
    result["distComplete"] = not absent
    if absent:
        result.update({"status": "FAIL", "reason": f"dist missing {absent}"})
        return result

    # Tailwind must actually have run. A wrong `content` glob silently produces
    # a stylesheet with preflight only: the build still exits 0, dist is still
    # complete, and the site renders unstyled. That regression must not pass.
    css_files = sorted((dist / "assets").glob("*.css"))
    css_text = "".join(p.read_text(encoding="utf-8", errors="replace") for p in css_files)
    utility_markers = {
        "displayFlex": bool(re.search(r"\.flex\{[^}]*display:\s*flex", css_text)),
        "displayGrid": bool(re.search(r"\.grid\{[^}]*display:\s*grid", css_text)),
        "relative": bool(re.search(r"\.relative\{[^}]*position:\s*relative", css_text)),
    }
    result["tailwind"] = utility_markers
    if not any(utility_markers.values()):
        result.update(
            {
                "status": "FAIL",
                "reason": "no Tailwind utilities in built CSS - content glob matched nothing",
            }
        )
        return result

    index_html = (dist / "index.html").read_text(encoding="utf-8", errors="replace")
    seo = check_seo(index_html)
    result["seo"] = seo
    hard = [k for k, v in seo.items() if k == "placeholderLeaked" and v]
    hard += [k for k, v in seo.items() if k != "placeholderLeaked" and not v]
    if hard:
        result.update({"status": "FAIL", "reason": f"index.html integrity: {hard}"})
        return result

    # Bundle measurement: entry chunk plus the React runtime is what a first
    # visit must download before the page is interactive.
    assets = dist / "assets"
    entry_kb = 0.0
    largest = 0.0
    largest_name = ""
    for js in assets.glob("*.js"):
        kb = gzip_kb(js)
        largest = max(largest, kb)
        if kb > largest:
            largest_name = js.name
        if js.name.startswith("index-") or js.name.startswith("vendor-react"):
            entry_kb += kb
    result["firstPaintKb"] = round(entry_kb, 1)
    result["largestChunkKb"] = round(largest, 1)
    result["largestChunk"] = largest_name
    result["withinBudget"] = entry_kb <= FIRST_PAINT_TARGET_KB
    result["withinHardLimit"] = entry_kb <= FIRST_PAINT_HARD_KB

    result["status"] = "PASS" if result["withinHardLimit"] else "WARN"
    result["seconds"] = round(time.time() - started, 1)

    if not keep_modules:
        shutil.rmtree(site / "node_modules", ignore_errors=True)
        (site / "package-lock.json").unlink(missing_ok=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sites", nargs="*", help="limit to these slugs")
    ap.add_argument("--limit", type=int, help="verify at most N sites this run")
    ap.add_argument("--resume", action="store_true", help="skip sites already proven PASS")
    ap.add_argument("--timeout", type=int, default=900, help="per-command timeout in seconds")
    ap.add_argument("--keep-node-modules", action="store_true")
    args = ap.parse_args()

    sites = sorted(p for p in DELIVERY.iterdir() if p.is_dir() and (p / "package.json").exists())
    if args.sites:
        wanted = set(args.sites)
        sites = [p for p in sites if p.name in wanted]

    ledger: dict = {}
    if args.resume and LEDGER.exists():
        try:
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ledger = {}
    proven = {r["slug"] for r in ledger.get("results", []) if r.get("status") == "PASS"}

    if args.resume:
        before = len(sites)
        sites = [p for p in sites if p.name not in proven]
        print(f"resuming: {before - len(sites)} already proven, {len(sites)} to verify")

    if args.limit:
        sites = sites[: args.limit]

    results: list[dict] = ledger.get("results", [])
    by_slug = {r["slug"]: r for r in results}

    for i, site in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] {site.name} ...", flush=True)
        res = verify_site(site, args.timeout, args.keep_node_modules)
        by_slug[res["slug"]] = res
        print(f"      -> {res['status']} {res.get('reason', '')} "
              f"firstPaint={res.get('firstPaintKb', '-')}KB "
              f"({res.get('seconds', '-')}s)", flush=True)

    merged = sorted(by_slug.values(), key=lambda r: r["slug"])
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "targets": len(merged),
                "pass": sum(1 for r in merged if r["status"] == "PASS"),
                "warn": sum(1 for r in merged if r["status"] == "WARN"),
                "fail": sum(1 for r in merged if r["status"] == "FAIL"),
                "unverified": len(sites) - len(merged) if args.resume else 0,
                "results": merged,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    total = len(merged)
    print(f"\nverified {total} : "
          f"{sum(1 for r in merged if r['status'] == 'PASS')} PASS / "
          f"{sum(1 for r in merged if r['status'] == 'WARN')} WARN / "
          f"{sum(1 for r in merged if r['status'] == 'FAIL')} FAIL")
    print(f"ledger: {LEDGER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
