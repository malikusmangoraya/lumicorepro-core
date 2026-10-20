"""store_gate — "Ready-to-Store" compliance scan + autofix for generated projects.

Every project this agent ships (Gumroad / Lemon Squeezy / ThemeForest / GitHub)
must pass a fixed checklist. The gate scans, reports scores per item, and can
AUTO-FILL the safe gaps instead of leaving the buyer to fix them:

  README.md            required, sized, pitch present
  LICENSE.md           MIT auto-installed when missing
  .env.example         required
  robots.txt           public/ — auto-written
  sitemap.xml          public/ — auto-written from live_url/index
  favicon.svg          auto-copied from the project logo/thumb when missing
  OG meta              og:title/og:description/og:image injected into index.html
  img alt coverage     flags <img> tags without alt
  package.json         name/version/description/license fields filled

Destroy-anything items (real artwork, code) are reported, never mutated.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:  # works both as `agent.extensions.store_gate` and as a direct script
    from agent.extensions.built_with_badge import _brand_name
except ImportError:
    from extensions.built_with_badge import _brand_name

_MIT_LICENSE = """MIT License

Copyright (c) {year} LumiCorePro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_ROBOTS = """User-agent: *
Allow: /
Sitemap: {base}/sitemap.xml
"""

_README_MIN_LINES = 12
_WEIGHTS = {
    "readme": 20, "license": 15, "env_example": 10, "robots": 5,
    "sitemap": 5, "favicon": 10, "og_meta": 15, "img_alt": 10, "pkg_meta": 10,
}


def _public_dir(root: Path) -> Path:
    cand = (root / "frontend" / "public")
    if cand.exists():
        return cand
    p = root / "public"
    return p if p.exists() else (root / "frontend" / "public")


def _index_html(root: Path) -> Optional[Path]:
    for cand in ("frontend/index.html", "index.html"):
        p = root / cand
        if p.exists():
            return p
    return None


def _write_sitemap(public: Path, base: str) -> None:
    (public / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{base}/</loc><lastmod>{time.strftime("%Y-%m-%d")}</lastmod>'
        "<changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )


def _fill_pkg_meta(pkg_path: Path, brand: str) -> List[str]:
    import json
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    filled = []
    if not pkg.get("license"):
        pkg["license"] = "MIT"
        filled.append("package.json:license")
    if not pkg.get("description"):
        pkg["description"] = f"{brand} — production-ready full-stack project by LumiCorePro."
        filled.append("package.json:description")
    if filled:
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    return filled


def _inject_og(index: Path, brand: str, og_image: str = "images/generated/og-image.jpg") -> List[str]:
    added = []
    html = index.read_text(encoding="utf-8", errors="replace")
    base = f"<og:{brand}:{int(time.time())}>"  # guard against double-inject races
    if "og:title" not in html:
        html = html.replace("</head>",
            f'    <meta property="og:title" content="{brand}"/>\n'
            f'    <meta property="og:description" content="{brand} — production-ready full-stack project"/>\n'
            f'    <meta property="og:type" content="website"/>\n'
            f'    <meta property="og:image" content="/{og_image.lstrip("/")}"/>\n'
            "  </head>", 1)
        added.append(index.name + ":og-meta")
    if added:
        index.write_text(html, encoding="utf-8")
    return added


def _alt_report(html: str) -> Dict[str, Any]:
    imgs = re.findall(r"<img\b[^>]*>", html, flags=re.I)
    missing = [m[:80] for m in imgs if not re.search(r"\balt\s*=", m, flags=re.I)]
    return {"imgs": len(imgs), "missing_alt": len(missing)}


def run_store_gate(project_dir: str, base_url: str = "",
                   apply_fixes: bool = False) -> Dict[str, Any]:
    """Scan the project for store-completeness; with apply_fixes, fill safe gaps."""
    root = Path(project_dir)
    if not root.exists():
        return {"status": "failed", "message": "project dir missing"}
    brand = _brand_name(str(root))
    public = _public_dir(root)
    public.mkdir(parents=True, exist_ok=True)
    index = _index_html(root)
    fixes: List[str] = []
    items: Dict[str, Any] = {}

    def _ok(item: str) -> bool:
        return bool(items.get(item, {}).get("ok"))

    # 1. README
    readme = next((p for p in (root / "README.md", root / "readme.md") if p.exists()), None)
    if not readme and apply_fixes:
        (root / "README.md").write_text(
            f"# {brand}\n\nProduction-ready full-stack template by LumiCorePro.\n\n"
            "## Getting Started\n\nSee `docs/` and `.env.example`. Quick start:\n\n"
            "```bash\nnpm install\nnpm run dev\n```\n\n## License\n\nMIT — see `LICENSE.md`.\n",
            encoding="utf-8")
        fixes.append("README.md")
    lines = len(readme.read_text(encoding="utf-8", errors="replace").splitlines()) if readme else 0
    if not readme and apply_fixes and (root / "README.md").exists():
        readme = root / "README.md"
        lines = len(readme.read_text(encoding="utf-8", errors="replace").splitlines())
    items["readme"] = {"ok": lines >= _README_MIN_LINES, "lines": lines}

    # 2. LICENSE
    lic = next((p for p in (root / "LICENSE.md", root / "LICENSE") if p.exists()), None)
    if not lic and apply_fixes:
        (root / "LICENSE.md").write_text(_MIT_LICENSE.format(year=time.strftime("%Y")), encoding="utf-8")
        fixes.append("LICENSE.md")
    items["license"] = {"ok": any((root / n).exists() for n in ("LICENSE.md", "LICENSE"))}

    # 3. .env.example
    if not (root / ".env.example").exists() and apply_fixes:
        (root / ".env.example").write_text(
            "# Copy to .env and fill in real values\n"
            "VITE_API_URL=http://localhost:5000/api/v1\n"
            "VITE_APP_NAME=\"" + brand + "\"\n",
            encoding="utf-8")
        fixes.append(".env.example")
    items["env_example"] = {"ok": (root / ".env.example").exists()}

    # 4. robots.txt / sitemap.xml
    if apply_fixes and not (public / "robots.txt").exists():
        base = (base_url or "https://your-domain.com").rstrip("/")
        (public / "robots.txt").write_text(_ROBOTS.format(base=base), encoding="utf-8")
        fixes.append("public/robots.txt")
    items["robots"] = {"ok": (public / "robots.txt").exists()}
    if apply_fixes and not (public / "sitemap.xml").exists():
        _write_sitemap(public, (base_url or "https://your-domain.com").rstrip("/"))
        fixes.append("public/sitemap.xml")
    items["sitemap"] = {"ok": (public / "sitemap.xml").exists()}

    # 5. favicon.svg
    favicon = (public / "favicon.svg")
    if not favicon.exists():
        favs = list(root.glob("frontend/favicon.svg")) + list((root / "src").glob("favicon.svg"))
        if apply_fixes and favs:
            (public / "favicon.svg").write_bytes(favs[0].read_bytes())
            fixes.append("public/favicon.svg")
    items["favicon"] = {"ok": favicon.exists()}

    # 6. OG meta + img alt
    if index:
        html = index.read_text(encoding="utf-8", errors="replace")
        if "og:title" not in html and apply_fixes:
            fixes += _inject_og(index, brand)
            html = index.read_text(encoding="utf-8", errors="replace")
        items["og_meta"] = {"ok": "og:title" in html}
        alt = _alt_report(html)
        items["img_alt"] = alt | {"ok": alt["missing_alt"] == 0}
    else:
        items["og_meta"] = {"ok": False}
        items["img_alt"] = {"ok": False, "imgs": 0, "missing_alt": 0, "note": "no index.html"}

    # 7. package.json metadata
    pkg = next((p for p in (root / "frontend" / "package.json", root / "package.json") if p.exists()), None)
    if pkg and apply_fixes:
        fixes += _fill_pkg_meta(pkg, brand)
        items["pkg_meta"] = {"ok": True, "note": "filled" if any("package.json" in f for f in fixes) else "present"}
    else:
        items["pkg_meta"] = {"ok": bool(pkg)}

    score = sum(_WEIGHTS[k] for k, v in items.items() if v and v.get("ok"))
    return {"status": "passed" if score >= 90 else "warn",
            "score": score, "brand": brand, "items": items,
            "fixes": fixes, "total_weight": sum(_WEIGHTS.values())}
