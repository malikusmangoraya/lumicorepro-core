#!/usr/bin/env python3
"""Repair the brand component after the identity scrub renamed it badly.

The scrub replaced the vendor's component name with the product's display title.
That is correct for prose ("Studio Lumen is a photographer's collective") but
wrong for code, because the title contains a space:

    import Studio Lumen from './Studio Lumen';   // syntax error
    export default function Studio Lumen({ ... }) // syntax error
    <Studio Lumen dark />                         // syntax error

This renames the file and restores a valid identifier in exactly the three
places the name is used as code — the import statement, the function
declaration, and JSX element usage — while leaving every piece of display copy
untouched. The component becomes `BrandLogo`, which also reads better than a
product name in a component import.

    python scripts/fix_brand_component.py --dry-run
    python scripts/fix_brand_component.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

# Relative to the frontend/ directory, not the product root.
COMPONENT_DIR = Path("src/components")
VENDOR_FILES = ("LumicorePro.jsx", "LumicorePro.js")
NEW_NAME = "BrandLogo"

TITLES = {
    "apex": "Apex",
    "aurelia-estates": "Aurelia Estates",
    "aurum-fitness": "Aurum Fitness",
    "claimflow-ai": "ClaimFlow",
    "meridian-capital": "Meridian Capital",
    "nuage-events": "Nuage Events",
    "prestige-studio": "Prestige Studio",
    "resupro": "ResuPro",
    "saffron-voyage": "Saffron Voyage",
    "studio-lumen": "Studio Lumen",
}


def repair_component_file(path: Path, title: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    # `export default function <Title>(` -> `export default function BrandLogo(`
    text = re.sub(rf"(export\s+default\s+function\s+){re.escape(title)}\s*\(",
                  rf"\g<1>{NEW_NAME}(", text)
    text = re.sub(rf"(export\s+default\s+function\s+)[A-Z][A-Za-z]*\s+[A-Z][A-Za-z]*\s*\(",
                  rf"\g<1>{NEW_NAME}(", text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def repair_references(fe: Path, title: str) -> list[str]:
    """Fix import statements and JSX usages of the brand component."""
    touched: list[str] = []
    src = fe / "src"
    if not src.is_dir():
        return touched

    title_rx = re.escape(title)

    for f in src.rglob("*"):
        if f.suffix not in {".js", ".jsx", ".ts", ".tsx"} or not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        original = text

        # import <Title> from './<Title>'  ->  import BrandLogo from './BrandLogo'
        text = re.sub(
            rf"import\s+{title_rx}\s+from\s+(['\"])\./{title_rx}\1",
            f"import {NEW_NAME} from './{NEW_NAME}'",
            text,
        )
        # Any remaining './<Title>' path pointing at the renamed file.
        text = re.sub(rf"(['\"])\./{title_rx}\1", rf"\1./{NEW_NAME}\1", text)

        # JSX element usage: <Title ...>, <Title/>, </Title>
        text = re.sub(rf"<{title_rx}(?=[\s/>])", f"<{NEW_NAME}", text)
        text = re.sub(rf"</{title_rx}\s*>", f"</{NEW_NAME}>", text)

        # Self-closing with no space at all: <Title/>
        text = re.sub(rf"<{title_rx}/>", f"<{NEW_NAME} />", text)

        if text != original:
            f.write_text(text, encoding="utf-8")
            touched.append(f.relative_to(fe).as_posix())
    return touched


def repair_license_config(fe: Path, title: str) -> bool:
    """`seller: '<Title> Core Generator'` still announces the generator."""
    cfg = fe / "src" / "config" / "license-config.js"
    if not cfg.is_file():
        return False
    text = cfg.read_text(encoding="utf-8", errors="replace")
    new = re.sub(rf"(seller\s*:\s*['\"]){re.escape(title)}\s+Core Generator(['\"])",
                 rf"\g<1>{title}\g<2>", text)
    new = re.sub(rf"(seller\s*:\s*['\"])[^'\"]*Core Generator([^'\"]*)(['\"])",
                 rf"\g<1>{title}\g<3>", new)
    if new != text:
        cfg.write_text(new, encoding="utf-8")
        return True
    return False


def process(proj: Path, dry: bool) -> tuple[int, list[str]]:
    fe = proj / "frontend"
    title = TITLES.get(proj.name, proj.name.replace("-", " ").title())
    if not fe.is_dir():
        return 0, ["no frontend/"]

    notes: list[str] = []

    comp_dir = fe / COMPONENT_DIR
    renamed = 0
    for vf in VENDOR_FILES:
        src = comp_dir / vf
        if src.is_file():
            dst = comp_dir / f"{NEW_NAME}.jsx"
            if not dry:
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
            renamed += 1
            notes.append(f"renamed {vf} -> {NEW_NAME}.jsx")

    if not dry and (comp_dir / f"{NEW_NAME}.jsx").is_file():
        if repair_component_file(comp_dir / f"{NEW_NAME}.jsx", title):
            notes.append(f"{NEW_NAME}.jsx: restored valid function name")

    touched = repair_references(fe, title) if not dry else []
    if touched:
        notes.append(f"{len(touched)} file(s) had import/JSX references repaired")

    if not dry and repair_license_config(fe, title):
        notes.append("license-config.js: removed 'Core Generator' seller wording")

    return renamed, notes


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

    print(f"=== fix_brand_component: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)}) ===")
    total = 0
    for d in dirs:
        n, notes = process(d, a.dry_run)
        total += n
        print(f"-- {d.name:20} renamed={n}")
        for note in notes:
            print(f"     {note}")
    print(f"\n=== {total} component file(s) renamed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())