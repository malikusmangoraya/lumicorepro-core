#!/usr/bin/env python3
"""Repair the shipped JSON-LD graph in each product's frontend config.

`frontend/src/config/structured-data.js` is the one file in the catalogue that
the brand pass never rewrote, so three things survived into the sale:

1. **The Pages path is not always the deployed path.** `apex` shipped
   `github.io/apex` while the deployment lives at `github.io/apex-digital`;
   `resupro` still said `github.io/build`, the template slug it was built from.
   A JSON-LD `url` or `@id` that 404s is worse than none - it tells search
   engines the canonical location of a page that does not exist.
2. **Two files carry the wrong brand.** `resupro` described an organisation
   called "Build", and `claimflow-ai` spelled its own name "Claimflow".
3. **The header comment is mojibake** in all ten files - an em-dash that was
   decoded as U+FFFD and written back as `ef bf bd 3f 3f`.

The URL and brand name both come from `LIVE_URL.txt` and `brand_map`, so this
cannot drift from the identity the rest of the package uses.

Usage:  python scripts/fix_jsonld.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from brand_map import BRANDS  # noqa: E402

PRODUCTS_DIR = ROOT / "products"
REL = Path("frontend/src/config/structured-data.js")

def js(value: str) -> str:
    """Render a Python string as a JS single-quoted literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


# The corrupted dash, exactly as it sits in the shipped bytes.
MOJIBAKE = "\ufffd??"

# Names that are page roles rather than the organisation, e.g. the breadcrumb
# item for the home page. They must never be rewritten to the brand.
NON_BRAND_NAMES = {"Home", "Products", "Services", "Pricing", "Contact",
                   "About", "Blog", "Careers", "FAQ", "Privacy", "Terms"}


def _stem(name: str) -> str:
    """Reduce a JSON-LD name to the part that must match the brand.

    `'What is Build?'` -> `Build`, `'Build Team'` -> `Build`, `'Home'` -> `Home`.
    """
    stem = name
    if stem.startswith("What is "):
        stem = stem[len("What is "):]
    if stem.endswith(" Team"):
        stem = stem[:-len(" Team")]
    if stem.endswith("?"):
        stem = stem[:-1]
    return stem.strip()


def _rebrand(name: str, brand: str) -> str:
    """Rebuild a JSON-LD name around the real brand, preserving its shape."""
    suffix = ""
    if name.endswith(" Team"):
        suffix = " Team"
    elif name.startswith("What is "):
        suffix = "?"
    return "What is " + brand + suffix if suffix == "?" else brand + suffix


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    touched = 0

    for product in sorted(p for p in PRODUCTS_DIR.iterdir() if p.is_dir()):
        path = product / REL
        if not path.is_file():
            continue

        live_file = product / "LIVE_URL.txt"
        live = ""
        if live_file.is_file():
            live = live_file.read_text(encoding="utf-8", errors="replace").strip()
        m = re.search(r"https?://[^/\s]+/([A-Za-z0-9._-]+)", live)
        deployed = m.group(1) if m else ""
        brand = BRANDS.get(product.name, {}).get("name", "")

        text = original = path.read_text(encoding="utf-8", errors="replace")
        notes = []

        # 1. every Pages path in the file must be the deployed one
        paths = set(re.findall(r"github\.io/([A-Za-z0-9._-]+)", text))
        if deployed and paths - {deployed}:
            for wrong in sorted(paths - {deployed}):
                n = text.count(f"github.io/{wrong}")
                text = text.replace(f"github.io/{wrong}", f"github.io/{deployed}")
                notes.append(f"{n}x path /{wrong} -> /{deployed}")
            if deployed.lower() != deployed:
                notes.append(f"WARNING: LIVE_URL path /{deployed} is not lowercase")

        # 2. the organisation name must be the brand, not the template slug.
        #    The catalogue convention is the brand's first word ("Aurelia" for
        #    "Aurelia Estates"), so a name is only wrong when its stem is
        #    neither the brand nor that first word - "Build" and "Claimflow",
        #    left over from the template each product was generated from.
        if brand:
            stems = {brand, brand.split()[0]}
            wrong_names = sorted({
                nm for nm in re.findall(r"name: '([^']+)'", text)
                if _stem(nm) not in stems and _stem(nm) not in NON_BRAND_NAMES
            })
            for nm in wrong_names:
                fixed = _rebrand(nm, brand)
                n = text.count(f"name: '{nm}'")
                text = text.replace(f"name: '{nm}'", f"name: '{fixed}'")
                notes.append(f"{n}x name '{nm}' -> '{fixed}'")

        # 3. the Product description is template filler ("X core platform
        #    offering") and, in resupro's case, still names the template slug.
        #    The brand entry already carries a real sentence, so use that.
        desc = BRANDS.get(product.name, {}).get("sub", "")
        if desc:
            filler = re.search(r"description: '([^']*?) core platform offering'", text)
            if filler and filler.group(1) != brand:
                text = text.replace(filler.group(0), f"description: {js(desc)}")
                notes.append(f"description '{filler.group(1)} core platform offering' -> brand line")

        # 4. the corrupted dash
        if MOJIBAKE in text:
            n = text.count(MOJIBAKE)
            text = text.replace(MOJIBAKE, "—")
            notes.append(f"{n}x mojibake -> em dash")

        if text == original:
            continue

        touched += 1
        rel = path.relative_to(ROOT).as_posix()
        if args.dry_run:
            print(f"  would fix {rel}")
        else:
            path.write_text(text, encoding="utf-8")
            print(f"  fixed     {rel}")
        for note in notes:
            print(f"             - {note}")

    verb = "would fix" if args.dry_run else "fixed"
    print(f"\n{verb} {touched} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())