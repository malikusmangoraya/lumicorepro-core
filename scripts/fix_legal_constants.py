"""Normalise the legal-page constants so every used name is declared once.

Strips any partial declarations and re-inserts a single clean block declaring
exactly the constants the page interpolates.
"""
import pathlib
import re

DEL = pathlib.Path(r"D:\lumicorepro-core\delivery")
META = {
    "kestrel-fleet": "Kestrel Fleet",
    "maison-noir": "Maison Noir",
    "ledgerline": "Ledgerline",
    "kinetiq-health": "Kinetiq Health",
}
SUPPORT = "malikusmangoraya786@gmail.com"
# The pages compose the address as {EMAIL}@{DOMAIN}, so EMAIL must stay a
# local part. It is chosen to match the address shown in the link text.
LOCAL_PART = {"Privacy.jsx": "privacy", "Terms.jsx": "legal"}

# multi-line DOMAIN declaration: const DOMAIN = ... ; (ends at the first ';' line)
STRIP = [
    re.compile(r"const BRAND = '[^']*';\n*"),
    re.compile(r"const EMAIL = '[^']*';\n*"),
    re.compile(r"const DOMAIN = [\s\S]*?;\n*"),
]

DOMAIN_DECL = (
    "const DOMAIN = import.meta.env.VITE_SITE_URL\n"
    "  ? new URL(import.meta.env.VITE_SITE_URL).hostname\n"
    "  : (typeof window !== 'undefined' ? window.location.hostname : '{slug}.example.com');\n"
)

for slug, brand in META.items():
    for name in ("Privacy.jsx", "Terms.jsx"):
        p = DEL / slug / "frontend" / "src" / "pages" / name
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        used = {n for n in ("BRAND", "EMAIL", "DOMAIN") if re.search(rf"\{{{n}\}}", t)}
        if not used:
            print(f"{slug}/{name}: no constants used")
            continue
        for pat in STRIP:
            t = pat.sub("", t)

        block = ""
        if "BRAND" in used:
            block += f"const BRAND = '{brand}';\n"
        if "EMAIL" in used:
            block += f"const EMAIL = '{LOCAL_PART.get(name, 'support')}';\n"
        if "DOMAIN" in used:
            block += DOMAIN_DECL.replace("{slug}", slug)
        block += "\n"

        lines = t.splitlines(keepends=True)
        last_import = 0
        for i, line in enumerate(lines):
            if line.lstrip().startswith("import "):
                last_import = i
        lines.insert(last_import + 1, block)
        out = "".join(lines)
        out = re.sub(r"\n{4,}", "\n\n\n", out)
        p.write_text(out, encoding="utf-8")
        print(f"{slug}/{name}: declared {sorted(used)}")
