"""Define the missing BRAND constant used by Privacy.jsx and Terms.jsx.

Both pages interpolate `{BRAND}` but never declared it, so every privacy and
terms page threw `BRAND is not defined` at render. Declared here as a plain
module constant to match how the rest of these pages are written.
"""
import pathlib
import re

DEL = pathlib.Path(r"D:\lumicorepro-core\delivery")
BRANDS = {
    "kestrel-fleet": "Kestrel Fleet",
    "maison-noir": "Maison Noir",
    "ledgerline": "Ledgerline",
    "kinetiq-health": "Kinetiq Health",
}

for slug, brand in BRANDS.items():
    pages = DEL / slug / "frontend" / "src" / "pages"
    for name in ("Privacy.jsx", "Terms.jsx"):
        p = pages / name
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        if re.search(r"\bconst BRAND\b", t):
            print(f"{slug}/{name}: already defined")
            continue
        if "{BRAND}" not in t:
            print(f"{slug}/{name}: no BRAND usage, skipped")
            continue
        decl = f"const BRAND = '{brand}';\n\n"
        lines = t.splitlines(keepends=True)
        # after the last import statement
        last_import = 0
        for i, line in enumerate(lines):
            if line.lstrip().startswith("import "):
                last_import = i
        lines.insert(last_import + 1, "\n" + decl)
        p.write_text("".join(lines), encoding="utf-8")
        print(f"{slug}/{name}: BRAND declared = {brand}")
