"""Definitive layout uniqueness check: hash each landing page's hero DOM."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOTS = [
    ("generated-projects", Path(r"D:\lumicorepro-core\generated-projects"), "frontend/src/pages/Home.jsx"),
    ("delivery", Path(r"D:\lumicorepro-core\delivery"), "src/pages/Home.jsx"),
    ("products", Path(r"D:\lumicorepro-core\products"), "frontend/src/pages/Home.jsx"),
]


def first_section(text: str) -> str:
    s = text.find("<section")
    if s == -1:
        return ""
    i, d = s, 0
    while i < len(text):
        if text.startswith("<section", i):
            d += 1; i += 8; continue
        if text.startswith("</section>", i):
            d -= 1
            if d == 0:
                return text[s:i]
            i += len("</section>"); continue
        i += 1
    return ""


def norm(hero: str, slug: str) -> str:
    """Blank out only the project's own name; keep every class name.

    Class names, element order and grid ratios are exactly what makes one
    layout different from another, so nothing structural may be stripped.
    """
    h = re.sub(r"\s+", " ", hero)
    for token in {slug, slug.upper(), slug.replace("-", " "),
                  slug.replace("-", " ").upper(), slug.replace("-", "_")}:
        if token:
            h = h.replace(token, "NAME")
    return h.strip()


report = {}
for label, root, rel in ROOTS:
    hashes = {}
    for proj in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        f = proj / rel
        if not f.is_file():
            continue
        hero = first_section(f.read_text(encoding="utf-8", errors="ignore"))
        if not hero:
            continue
        key = hashlib.md5(norm(hero, proj.name).encode()).hexdigest()
        hashes.setdefault(key, []).append(proj.name)
    dupes = {k: v for k, v in hashes.items() if len(v) > 1}
    report[label] = {
        "projects": sum(len(v) for v in hashes.values()),
        "distinct_hero_structures": len(hashes),
        "duplicates": {k: v for k, v in dupes.items()},
    }
    print(f"[{label}] projects={report[label]['projects']} "
          f"distinct hero structures={len(hashes)} duplicates={len(dupes)}")
    for k, v in dupes.items():
        print("     ", ", ".join(sorted(v)))

Path(r"C:\Users\AZAM COMPUTERS\AppData\Local\Temp\opencode\uniqueness.json").write_text(
    json.dumps(report, indent=1), encoding="utf-8")