"""Port the missing pages into the ported delivery projects.

kestrel-fleet shipped without Login/Register/Admin/Checkout, so its backend
auth could not be exercised from the UI at all. None of the four had the GDPR
Account page. Both gaps are filled from the verified catalogue pages, which use
the same design-token variables the delivery sources already define.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

DEL = Path(r"D:\lumicorepro-core\delivery")
SRC = Path(r"D:\lumicorepro-core\products\resupro\frontend\src\pages")

TARGETS = ["kestrel-fleet", "maison-noir", "ledgerline", "kinetiq-health"]
NEEDED = ["Login.jsx", "Register.jsx", "Admin.jsx", "Checkout.jsx", "Account.jsx"]

PAGE_ROUTES = {
    "Login.jsx": "/login",
    "Register.jsx": "/register",
    "Admin.jsx": "/admin",
    "Checkout.jsx": "/checkout",
    "Account.jsx": "/account",
}


def ensure_nav(pages: Path, app: str, stem: str, path: str) -> str:
    if f'"{path}"' in app:
        return app
    # lazy import next to the existing Contact lazy import
    lines = app.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if "pages/Contact" in line and "lazy" in line:
            lines.insert(i + 1, f"const {stem} = lazy(() => import('./pages/{stem}'));\n")
            break
    app = "".join(lines)
    if f'path="{path}"' in app:
        return app
    route = f'              <Route path="{path}" element{{<{stem} />}} />\n'
    lines = app.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if 'path="/"' in line:
            lines.insert(i, route)
            break
    return "".join(lines)


for slug in TARGETS:
    pages = DEL / slug / "frontend" / "src" / "pages"
    app_p = pages.parent / "App.jsx"
    added = []
    for name in NEEDED:
        dst = pages / name
        if dst.is_file():
            continue
        src = SRC / name
        if not src.is_file():
            print(f"  !! missing source {name}")
            continue
        shutil.copy2(src, dst)
        added.append(name)

    app = app_p.read_text(encoding="utf-8")
    for name in added:
        stem = name.replace(".jsx", "")
        app = ensure_nav(pages, app, stem, PAGE_ROUTES[name])
    app_p.write_text(app, encoding="utf-8")
    print(f"{slug:<16} added: {', '.join(added) if added else 'nothing'}")
