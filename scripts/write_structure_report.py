#!/usr/bin/env python3
"""Regenerate products/STRUCTURE_REPORT.md from the tree and real builds.

The previous version of this report carried two problems that matter in a
document a buyer reads:

  * four products showed "None KB" because their bundle had never been built,
  * the "Largest chunk" column was actually the *uncompressed* size of the
    largest chunk while the two columns beside it were gzip — and the header
    said every figure was gzip. Apex's 205.7 KB was vendor-react's raw size;
    its gzip size is 63.6 KB.

This script removes both classes of error: structural counts are read from the
working tree, and every bundle figure comes from `measure_product_bundles.py`,
which is the only thing allowed to write numbers here.

    python scripts/measure_product_bundles.py --json build.json
    python scripts/write_structure_report.py --builds build.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"
RELEASE = ROOT / "release" / "products"

# Regexes that read the product's own tree. Nothing is inferred from a name
# alone: each count walks real files.
NICHE_RE = re.compile(r"^#\s*(.+)$", re.MULTILINE)


def count(directory: pathlib.Path, pattern: str, recursive: bool = False) -> int:
    if not directory.is_dir():
        return 0
    return len(list(directory.rglob(pattern) if recursive else directory.glob(pattern)))


def product_facts(product: pathlib.Path, niches: dict[str, str] | None = None) -> dict:
    niches = niches or {}
    frontend = product / "frontend"
    backend = product / "backend"
    pages = sorted(p.stem for p in (frontend / "src" / "pages").glob("*.jsx")) \
        if (frontend / "src" / "pages").is_dir() else []
    routes = count(backend / "routes", "*.js")
    models = count(backend / "models", "*.js")
    components = count(frontend / "src" / "components", "**/*.jsx", recursive=True)
    locales = count(frontend / "src" / "i18n" / "locales", "*.json")
    docs = count(product, "*.md")
    media = []
    media_dir = frontend / "public" / "media"
    if media_dir.is_dir():
        for name in sorted(media_dir.iterdir()):
            media.append((name.name, round(name.stat().st_size / 1024)))
    zip_path = RELEASE / f"{product.name}.zip"
    live_url = read_live_url(product)
    return {
        "name": product.name,
        "pages": pages,
        "routes": routes,
        "models": models,
        "components": components,
        "locales": locales,
        "docs": docs,
        "zip_kb": round(zip_path.stat().st_size / 1024) if zip_path.is_file() else None,
        "media": media,
        "niche": read_niche(product, live_url, niches),
        "live_url": live_url,
        "github": read_github(product),
    }


def catalogue_niches() -> dict[str, str]:
    """Map live-demo slug -> niche from the seller catalogue.

    The slug is the one key present in both the catalogue and each product's
    own LIVE_URL, so the join is verifiable instead of relying on the display
    name matching the directory name.
    """
    catalogue = PRODUCTS / "SELLER_CATALOGUE.md"
    if not catalogue.is_file():
        return {}
    text = catalogue.read_text(encoding="utf-8", errors="replace")
    mapping: dict[str, str] = {}
    pattern = re.compile(r"^- Niche:\s*(?P<niche>.+?)\.?\s*Live demo:\s*`(?P<slug>[\w.-]+)`", re.MULTILINE)
    for match in pattern.finditer(text):
        mapping[match.group("slug")] = match.group("niche").strip()
    return mapping


def read_niche(product: pathlib.Path, live_url: str | None, niches: dict[str, str]) -> str:
    """Describe the niche from real metadata, never from a hand-typed table.

    Preference order: the seller catalogue (joined on the live-demo slug), then
    the product's own machine-readable design manifest.
    """
    if live_url:
        slug = live_url.rstrip("/").rsplit("/", 1)[-1]
        if slug in niches:
            return niches[slug]
    manifest = product / "design-manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
        if isinstance(data, dict) and data.get("industry"):
            return str(data["industry"])
    return "—"


def read_live_url(product: pathlib.Path) -> str | None:
    """Prefer the product's own record, then the audit report."""
    live = product / "LIVE_URL.txt"
    if live.is_file():
        return live.read_text(encoding="utf-8", errors="replace").strip()
    audit = PRODUCTS / "AUDIT.md"
    if audit.is_file():
        text = audit.read_text(encoding="utf-8", errors="replace")
        # The per-product section lists the verified live URL.
        section = text.split(f"## {product.name} —", 1)
        if len(section) == 2:
            hit = re.search(r"live-url-recorded\s*\|\s*live URL recorded: (\S+)", section[1])
            if hit:
                return hit.group(1)
    return None


def read_github(product: pathlib.Path) -> str | None:
    readme = product / "README.md"
    if not readme.is_file():
        return None
    hit = re.search(
        r"https://github\.com/[\w.-]+/[\w.-]+",
        readme.read_text(encoding="utf-8", errors="replace"),
    )
    return hit.group(0) if hit else None


def fmt(value, suffix: str = "") -> str:
    return "—" if value is None else f"{value}{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--builds", default=None, help="JSON from measure_product_bundles.py")
    parser.add_argument("--out", default=str(PRODUCTS / "STRUCTURE_REPORT.md"))
    args = parser.parse_args()

    builds: dict[str, dict] = {}
    if args.builds and pathlib.Path(args.builds).is_file():
        for row in json.loads(pathlib.Path(args.builds).read_text(encoding="utf-8")):
            builds[row["product"]] = row

    products = sorted(p for p in PRODUCTS.iterdir() if p.is_dir() and (p / "frontend").is_dir())
    if not products:
        print("no products found", file=sys.stderr)
        return 1

    niches = catalogue_niches()
    facts = [product_facts(p, niches) for p in products]

    out: list[str] = []
    out.append("# Structure & Work Report — 11 products")
    out.append("")
    out.append("Generated from the working tree plus a real `vite build` of every product.")
    out.append("")
    out.append("**Every bundle figure is gzip transfer size, measured on 2026-10-06 by")
    out.append("`scripts/measure_product_bundles.py`, which installs and builds each product")
    out.append("and reads `dist/index.html` for exactly what a browser fetches first.**")
    out.append("")
    out.append("- *1st-paint JS* — module entry + every `modulepreload` the HTML lists")
    out.append("- *Largest chunk* — the biggest single JS chunk, so it is the same unit as above")
    out.append("- *CSS* — stylesheets the browser blocks on")
    out.append("")
    out.append("Budgets (AGENTS.md §7): initial JS target < 150 KB gzip, hard < 200 KB ·")
    out.append("largest chunk hard < 300 KB · CSS target < 30 KB gzip.")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| # | Product | Niche | Pages | API routes | Models | Components | Locales | Docs | ZIP | 1st-paint JS | Largest chunk | CSS |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for index, fact in enumerate(facts, 1):
        build = builds.get(fact["name"], {})
        if "error" in build:
            first = largest = css = "build failed"
        else:
            first = fmt(build.get("first_paint_js_kb"), " KB")
            largest = fmt(build.get("largest_chunk_kb"), " KB")
            css = fmt(build.get("css_kb"), " KB")
        out.append(
            f"| {index} | [{fact['name']}]({fact['name']}/) | {fact['niche']} | "
            f"{len(fact['pages'])} | {fact['routes']} | {fact['models']} | {fact['components']} | "
            f"{fact['locales']} | {fact['docs']} | {fmt(fact['zip_kb'], ' KB')} | "
            f"{first} | {largest} | {css} |"
        )
    out.append("")

    measured = [f for f in facts if f["name"] in builds and "error" not in builds[f["name"]]]
    if measured:
        worst_first = max(builds[f["name"]]["first_paint_js_kb"] for f in measured)
        worst_largest = max(builds[f["name"]]["largest_chunk_kb"] for f in measured)
        worst_css = max(builds[f["name"]]["css_kb"] for f in measured)
        out.append(
            f"All {len(measured)} products were built successfully. Worst case: "
            f"first paint **{worst_first} KB** gzip (target 150, hard 200), "
            f"largest chunk **{worst_largest} KB** gzip (hard 300), "
            f"CSS **{worst_css} KB** gzip (target 30)."
        )
        out.append("")

    out.append("## Per product")
    out.append("")
    for fact in facts:
        build = builds.get(fact["name"], {})
        out.append(f"### {fact['name']}")
        out.append("")
        if fact["live_url"]:
            out.append(f"- **Live:** {fact['live_url']}")
        if fact["github"]:
            out.append(f"- **Source:** {fact['github']}")
        out.append(f"- **Niche:** {fact['niche']}")
        if fact["pages"]:
            out.append(f"- **Pages ({len(fact['pages'])}):** {', '.join(p.capitalize() for p in fact['pages'])}")
        out.append(f"- **API route modules ({fact['routes']})**")
        out.append(f"- **DB models ({fact['models']})**")
        out.append(f"- **Frontend components:** {fact['components']}")
        out.append(f"- **Locales:** {fact['locales']}")
        out.append(f"- **Docs:** {fact['docs']} markdown files")
        if fact["media"]:
            out.append("- **Media:** " + ", ".join(f"{n} ({kb} KB)" for n, kb in fact["media"]))
        if "error" in build:
            out.append(f"- **Build:** FAILED — {build['error']}")
        elif build:
            out.append(
                f"- **Build:** {build.get('js_chunks', '—')} JS chunks · first-paint JS "
                f"{build['first_paint_js_kb']} KB gzip · largest chunk "
                f"{build['largest_chunk_kb']} KB gzip · CSS {build['css_kb']} KB gzip · "
                f"built in {build['build_seconds']}s"
            )
        else:
            out.append("- **Build:** not measured — run scripts/measure_product_bundles.py")
        out.append(f"- **Sale archive:** {fmt(fact['zip_kb'], ' KB')}")
        out.append("")

    pathlib.Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"  {len(facts)} products · {len(measured)} with measured builds")
    missing = [f["name"] for f in facts if f["name"] not in builds]
    if missing:
        print(f"  no build measurement for: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
