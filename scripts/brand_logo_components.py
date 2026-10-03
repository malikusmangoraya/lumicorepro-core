"""Rewrite each project's LumicorePro.jsx into a unique branded logo.

Reads the uniquely-generated logo.svg mark + brand card and emits a
self-contained component (same filename, so Navbar/Footer keep working).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R
from brand_map import BRANDS

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"


def split_name(name: str):
    parts = name.split()
    first = parts[0]
    rest = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first, rest


def component_for(proj: Path, pal: dict) -> str:
    slug = proj.name
    brand = BRANDS.get(slug, BRANDS["build"])
    name = brand["name"]
    first, rest = split_name(name)
    g1 = pal["brand"] if pal["brand"].startswith("#") else "#" + pal["brand"]
    g2 = pal["accent"] if pal["accent"].startswith("#") else "#" + pal["accent"]
    logo = (proj / "frontend" / "public" / "logo.svg").read_text(encoding="utf-8")
    # extract inner svg markup after opening svg tag
    inner = re.sub(r"^.*?<svg[^>]*>", "", logo, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    # map literal gradient ids -> React expressions
    inner = inner.replace("url(#lgb)", "url(`#${lgb}`)")
    inner = inner.replace("url(#lg1)", "url(`#${lg1}`)")
    inner = inner.replace("url(#lg2)", "url(`#${lg2}`)")
    # logo.svg uses raw hex in stopColor + symbol fill; keep them as literal colors.
    inner = inner.replace("#" + g1.lstrip("#").lower(), g1)
    inner = inner.replace("#" + g2.lstrip("#").lower(), g2)
    rest_text = f" {rest}" if rest else ""
    tpl = """import React from 'react';
import { Link } from 'react-router-dom';

export default function LumicorePro({ to = '/', size = 34, dark = false }) {
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const lg1 = `lg1-${uid}`;
  const lg2 = `lg2-${uid}`;
  const lgb = `lgb-${uid}`;
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
      aria-label="__BRAND__"
    >
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        __INNER__
      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>__FIRST__</span>
        <span className="bg-gradient-to-r from-primary to-accent-400 bg-clip-text text-transparent">
          __REST__
        </span>
      </span>
    </Link>
  );
}
"""
    return (
        tpl.replace("__BRAND__", name)
        .replace("__INNER__", inner)
        .replace("__FIRST__", first)
        .replace(
            "__REST__",
            rest_text,
        )
    )


def theme_hexes(proj: Path) -> dict:
    """Read --t-brand / --t-accent-gold straight from the project's theme."""
    for cand in (proj / "frontend" / "src" / "lib" / "theme.js",
                 proj / "frontend" / "src" / "styles" / "theme.js"):
        if cand.exists():
            t = cand.read_text(encoding="utf-8", errors="replace")
            b = re.search(r"--t-brand\s*:\s*([^;\n]+)", t)
            a = re.search(r"--t-accent-gold\s*:\s*([^;\n]+)", t)
            if b:
                return {"brand": b.group(1).strip(),
                        "accent": (a.group(1).strip() if a else b.group(1).strip())}
    return {}


def main() -> int:
    wanted = set(sys.argv[1:])
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    pmap = {p.name: i for i, p in enumerate(projects)}
    for proj in projects:
        lcp = proj / "frontend" / "src" / "components" / "LumicorePro.jsx"
        pal = R.palette_for(pmap[proj.name])
        th = theme_hexes(proj)
        if th:
            pal = dict(pal); pal["brand"] = th["brand"]; pal["accent"] = th["accent"]
        comp = component_for(proj, pal)
        lcp.write_text(comp, encoding="utf-8")
    print("branded LumicorePro written:", len(projects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())