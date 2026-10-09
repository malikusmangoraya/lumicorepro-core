"""Static accessibility smoke check (not a WCAG certification).

Checks the shipped frontend trees for the baseline the code claims:
skip link, main landmark, labelled icon buttons, image alt text, and
reduced-motion CSS. Writes products/ACCESSIBILITY_SMOKE.md.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\lumicorepro-core\products")
OUT = ROOT / "ACCESSIBILITY_SMOKE.md"

rows = []
for prod in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    src = prod / "frontend" / "src"
    if not src.is_dir():
        continue
    files = [f for f in src.rglob("*") if f.is_file() and f.suffix in {".jsx", ".js", ".css"}]
    text = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files)
    checks = {
        "skip-link": "skip-link" in text or "skip_to_content" in text,
        "main-landmark": bool(re.search(r"<main[\s>]", text)),
        "icon-buttons-labelled": ("aria-label" in text),
        "reduced-motion": "prefers-reduced-motion" in text,
    }
    imgs = re.findall(r"<img[\s][^>]*>", text)
    imgs_no_alt = [t for t in imgs if "alt=" not in t]
    checks["img-alt"] = (len(imgs_no_alt) == 0)
    rows.append((prod.name, checks, len(imgs), len(imgs_no_alt)))

lines = ["# Accessibility smoke (static, 2026-10-07)", "",
         "This is a static baseline check, not a WCAG certification. Full axe-core + Lighthouse passes are required per release (see ACCESSIBILITY.md).", "",
         "| Product | skip link | main | labelled icons | reduced motion | images w/o alt |",
         "|---|---|---|---|---|---|"]
bad = 0
for name, checks, total, missing in rows:
    ok = all(checks.values())
    bad += 0 if ok else 1
    lines.append(f"| {name} | {'yes' if checks['skip-link'] else 'NO'} | {'yes' if checks['main-landmark'] else 'NO'} | {'yes' if checks['icon-buttons-labelled'] else 'NO'} | {'yes' if checks['reduced-motion'] else 'NO'} | {missing}/{total} |")
lines += ["", f"Products failing at least one static check: {bad}/{len(rows)}"]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(OUT)
for name, checks, total, missing in rows:
    if not all(checks.values()):
        print("FAIL", name, checks, f"img {missing}/{total}")
print(f"done: {len(rows)-bad}/{len(rows)} pass")
