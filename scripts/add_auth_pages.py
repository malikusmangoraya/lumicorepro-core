#!/usr/bin/env python3
"""Give every product a working login and signup page.

Two of the products ship a complete backend authentication system but no
front-end screen to reach it: `apex` and `claimflow-ai` route only the public
marketing pages, so a buyer cannot register or sign in from the interface even
though the API supports it.

This copies the proven Login/Register pages from a sibling product, rewrites the
brand copy to the target product, and registers both routes in App.jsx. The
pages are dependency-free React that posts to `/api/auth/login` and
`/api/auth/register`, which are exactly the endpoints the backend exposes.

    python scripts/add_auth_pages.py --dry-run
    python scripts/add_auth_pages.py
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

# A project whose Login/Register pages are known good.
SOURCE = "aurelia-estates"

TITLES = {
    "apex": ("Apex", "Precision commerce for ambitious brands"),
    "claimflow-ai": ("ClaimFlow", "Insurance claims, processed at the speed of reality."),
    "aurelia-estates": ("Aurelia Estates", "Exceptional residences, curated for the discerning."),
    "aurum-fitness": ("Aurum Fitness", "Coaching that compounds, for every athlete."),
    "meridian-capital": ("Meridian Capital", "Institutional-grade portfolio intelligence."),
    "nuage-events": ("Nuage Events", "Events worth travelling for."),
    "prestige-studio": ("Prestige Studio", "A studio site with the craft to match the work."),
    "resupro": ("ResuPro", "Resumes that get you the interview."),
    "saffron-voyage": ("Saffron Voyage", "Curated journeys across the Mediterranean."),
    "studio-lumen": ("Studio Lumen", "Light, considered, and precisely captured."),
}


def rebrand(text: str, src_title: str, dst_title: str, tagline: str) -> str:
    out = text.replace(src_title, dst_title)
    if tagline:
        out = re.sub(r"(subtitle\s*=\s*[\"'])[^\"']+([\"'])",
                     rf"\g<1>{tagline}\g<2>", out, count=1)
    return out


def add_routes(app_jsx: Path, has_basename: bool) -> bool:
    """Register /login and /register in App.jsx, once."""
    text = app_jsx.read_text(encoding="utf-8", errors="replace")
    if re.search(r'path="/login"', text):
        return False

    changed = False

    if "const Login = lazy(" not in text:
        anchor = "const Privacy = lazy("
        if anchor in text:
            text = text.replace(
                anchor,
                "const Login = lazy(() => import('./pages/Login'));\n"
                "const Register = lazy(() => import('./pages/Register'));\n" + anchor,
                1,
            )
            changed = True

    # Insert the routes before the catch-all, or before </Routes>.
    if "</Routes>" in text:
        text = text.replace(
            "</Routes>",
            '            <Route path="/login" element={<Login />} />\n'
            '            <Route path="/register" element={<Register />} />\n'
            "            </Routes>",
            1,
        )
        changed = True

    if changed:
        app_jsx.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    src_pages = PRODUCTS / SOURCE / "frontend" / "src" / "pages"
    if not src_pages.is_dir():
        print(f"Source pages not found at {src_pages}", file=sys.stderr)
        return 2

    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]

    print(f"=== add_auth_pages: {'DRY RUN' if a.dry_run else 'APPLY'} ===")
    added = 0
    for d in dirs:
        pages = d / "frontend" / "src" / "pages"
        app = d / "frontend" / "src" / "App.jsx"
        if not pages.is_dir() or not app.is_file():
            print(f"-- {d.name:20} skipped (no frontend/src/pages or App.jsx)")
            continue

        has_login = (pages / "Login.jsx").is_file()
        has_register = (pages / "Register.jsx").is_file()
        if has_login and has_register:
            print(f"-- {d.name:20} already has Login and Register — skipped")
            continue

        title, tagline = TITLES.get(d.name, (d.name.replace("-", " ").title(), ""))
        print(f"-- {d.name:20} adding Login + Register pages")
        added += 1

        if a.dry_run:
            continue

        for name in ("Login.jsx", "Register.jsx"):
            text = (src_pages / name).read_text(encoding="utf-8", errors="replace")
            (pages / name).write_text(rebrand(text, TITLES[SOURCE][0], title, tagline),
                                      encoding="utf-8")

        if add_routes(app, "basename" in app.read_text(encoding="utf-8", errors="replace")):
            print(f"     routes /login and /register added to App.jsx")

    print(f"\n=== {added} product(s) updated ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())