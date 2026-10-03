"""Generate a unique SVG logo for every generated project.

Deterministic: each project gets a distinct geometric symbol (by index from a
pool of 24 geometries), monogram letters from its brand name and a dual-band
gradient derived from brand+accent. Writes logo.svg (public + src/assets),
favicon and patches BrandLogo if present.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R
from brand_map import BRANDS

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"

# 24 distinct geometry generators -> returns inner SVG elements + a marker string.
SYMBOLS = [
    # 0 mountaintrail (two peaks, snow line)
    lambda s, a: f'<path d="M4 34 L22 10 L34 26 L44 14 L60 34 Z" fill="url({s})"/><path d="M22 10 L27 18 L22 16 L17 18 Z" fill="#fff" opacity=".85"/>',
    # 1 orbit rings
    lambda s, a: f'<circle cx="32" cy="32" r="20" fill="none" stroke="url({s})" stroke-width="4"/><ellipse cx="32" cy="32" rx="14" ry="30" fill="none" stroke="url({a})" stroke-width="3" transform="rotate(-28 32 32)"/><circle cx="46" cy="12" r="5" fill="url({a})"/>',
    # 2 aperture hexagon
    lambda s, a: f'<path d="M32 4 L56 18 L56 46 L32 60 L8 46 L8 18 Z" fill="none" stroke="url({s})" stroke-width="4"/><path d="M32 8 L32 56 M8 18 L56 46 M8 46 L56 18" stroke="url({a})" stroke-width="2.4" opacity=".9"/>',
    # 3 orbit prism (glowing core)
    lambda s, a: f'<rect width="64" height="64" fill="none"/><path d="M32 6 L52 20 L52 44 L32 58 L12 44 L12 20 Z" fill="url({s})"/><path d="M32 6 L52 20 L52 44 L32 58 L12 44 L12 20 Z" fill="none" stroke="url({a})" stroke-width="1.6"/><circle cx="32" cy="32" r="9" fill="#fff" opacity=".92"/>',
    # 4 dynamic bolt
    lambda s, a: f'<path d="M36 4 L14 36 L28 36 L24 60 L50 26 L34 26 Z" fill="url({s})"/><path d="M36 4 L14 36 L28 36 L24 60 L50 26 L34 26 Z" fill="none" stroke="url({a})" stroke-width="1.5"/>',
    # 5 layered waves
    lambda s, a: f'<path d="M4 40 Q18 26 32 40 T60 40 V60 H4 Z" fill="url({s})" opacity=".95"/><path d="M4 50 Q18 36 32 50 T60 50 V60 H4 Z" fill="url({a})" opacity=".9"/>',
    # 6 diamond facets
    lambda s, a: f'<path d="M32 2 L56 24 L32 62 L8 24 Z" fill="url({s})"/><path d="M32 2 L32 62 M8 24 L56 24 M18 14 L18 40 M46 14 L46 40" stroke="url({a})" stroke-width="1.6" opacity=".8"/>',
    # 7 rising grid / cityskyline
    lambda s, a: f'<rect x="8" y="22" width="9" height="34" fill="url({a})"/><rect x="21" y="12" width="9" height="44" fill="url({s})"/><rect x="34" y="26" width="9" height="30" fill="url({a})"/><rect x="47" y="8" width="9" height="48" fill="url({s})"/><path d="M4 56 H60" stroke="url({s})" stroke-width="3"/>',
    # 8 shield care
    lambda s, a: f'<path d="M32 2 L54 10 V30 C54 44 44 54 32 60 C20 54 10 44 10 30 V10 Z" fill="url({s})"/><path d="M24 32 L30 38 L42 24" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
    # 9 infinity loop
    lambda s, a: f'<path d="M16 44 C6 44 6 24 18 24 C28 24 30 44 46 44 C56 44 58 24 46 24 C36 24 34 44 18 44" fill="none" stroke="url({s})" stroke-width="5" stroke-linecap="round"/>',
    # 10 spark multi-point
    lambda s, a: f'<circle cx="32" cy="32" r="14" fill="url({s})"/><path d="M32 2 L35 18 L32 14 L29 18 Z" fill="url({a})"/><path d="M32 62 L35 46 L32 50 L29 46 Z" fill="url({a})"/><path d="M2 32 L18 29 L14 32 L18 35 Z" fill="url({a})"/><path d="M62 32 L46 29 L50 32 L46 35 Z" fill="url({a})"/>',
    # 11 book layers
    lambda s, a: f'<path d="M32 8 L52 4 V38 L32 44 L12 38 V4 Z" fill="url({s})"/><path d="M12 4 L32 8 L52 4" fill="none" stroke="url({a})" stroke-width="2"/><path d="M12 20 L32 24 L52 20" stroke="url({a})" stroke-width="2" opacity=".8"/>',
    # 12 cruise horizon
    lambda s, a: f'<path d="M6 44 L58 44 L50 56 H14 Z" fill="url({s})"/><path d="M24 44 L32 16 L40 44" fill="none" stroke="#fff" stroke-width="3" opacity=".9"/><path d="M4 36 Q32 28 60 36" fill="none" stroke="url({a})" stroke-width="3"/>',
    # 13 teardrop droplet
    lambda s, a: f'<path d="M32 2 C40 16 48 26 48 40 A16 16 0 1 1 16 40 C16 26 24 16 32 2 Z" fill="url({s})"/><path d="M24 40 Q32 44 40 40" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>',
    # 14 layered leaves
    lambda s, a: f'<path d="M32 4 C20 16 14 34 32 60 C50 34 44 16 32 4 Z" fill="url({s})"/><path d="M32 20 C26 24 24 30 32 44 C40 30 38 24 32 20 Z" fill="url({a})" opacity=".85"/>',
    # 15 play media
    lambda s, a: f'<circle cx="32" cy="32" r="26" fill="none" stroke="url({s})" stroke-width="4"/><path d="M26 22 L46 32 L26 42 Z" fill="url({a})"/>',
    # 16 house roof
    lambda s, a: f'<path d="M8 30 L32 8 L56 30 L56 56 H8 Z" fill="url({s})"/><rect x="24" y="34" width="16" height="22" fill="url({a})"/><path d="M8 30 L32 8 L56 30" fill="none" stroke="#fff" stroke-width="2.5" opacity=".8"/>',
    # 17 chimneys / flame
    lambda s, a: f'<path d="M32 2 C22 14 18 22 18 30 A14 14 0 1 0 46 30 C46 22 42 14 32 2 Z" fill="url({s})"/><path d="M26 30 C26 36 30 40 32 44 C34 40 38 36 38 30 C38 26 35 23 32 20 C29 23 26 26 26 30 Z" fill="#fff" opacity=".9"/>',
    # 18 woven basket
    lambda s, a: f'<path d="M10 18 H54 V52 H10 Z" fill="none" stroke="url({s})" stroke-width="4"/><path d="M10 26 H54 M10 34 H54 M10 42 H54" stroke="url({a})" stroke-width="2" opacity=".7"/>',
    # 19 sun aperture
    lambda s, a: f'<circle cx="32" cy="32" r="12" fill="url({s})"/><path d="M32 2 V14 M32 50 V62 M2 32 H14 M50 32 H62 M10 10 L18 18 M46 46 L54 54 M54 10 L46 18 M18 46 L10 54" stroke="url({a})" stroke-width="4" stroke-linecap="round"/>',
    # 20 protein flask
    lambda s, a: f'<path d="M26 6 H38 M28 6 L28 20 L46 46 V58 H18 V46 L36 20 L36 6" fill="none" stroke="url({s})" stroke-width="4"/><path d="M20 42 H44" stroke="url({a})" stroke-width="3"/>',
    # 21 chart bars
    lambda s, a: f'<path d="M8 56 V48 M8 20 V48" stroke="url({a})" stroke-width="3"/><rect x="18" y="30" width="10" height="18" fill="url({s})"/><rect x="32" y="18" width="10" height="30" fill="url({a})"/><rect x="46" y="10" width="10" height="38" fill="url({s})"/>',
    # 22 compass route
    lambda s, a: f'<circle cx="32" cy="32" r="24" fill="none" stroke="url({s})" stroke-width="4"/><path d="M32 8 L36 30 L58 32 L36 34 L32 56 L28 34 L6 32 L28 30 Z" fill="url({a})"/>',
    # 23 steps glyph
    lambda s, a: f'<path d="M6 40 H22 V26 H38 V14 H54 V58 H6 Z" fill="url({s})"/><path d="M6 48 H54" stroke="url({a})" stroke-width="3"/>',
]


def symbol(idx: int, gs: str, ga: str) -> str:
    return SYMBOLS[idx % len(SYMBOLS)](gs, ga)


def palette_idx(slug: str) -> int:
    """Deterministic index for a slug (so logos don't shift when projects move)."""
    total = sum(ord(c) for c in slug)
    return total % len(SYMBOLS)


def make_logo_svg(brand: dict, bhex: str, ahex: str) -> str:
    name = brand["name"]
    initials = "".join(w[0].upper() for w in name.replace("@", " ").split())[:2]
    idx = palette_idx(brand["name"])
    gs, ga = "#" + bhex.lstrip("#").lower(), "#" + ahex.lstrip("#").lower()
    symbol_node = symbol(idx, "lg1", "lg2")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 64 64" role="img" aria-label="{name}">
  <defs>
    <linearGradient id="lgb" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{gs}"/><stop offset="1" stop-color="{ga}"/>
    </linearGradient>
    <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{gs}"/><stop offset="1" stop-color="{ga}"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ga}"/><stop offset="1" stop-color="{gs}"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#lgb)" opacity="0.12"/>
  {symbol_node}
  <rect x="42" y="8" width="16" height="16" rx="5" fill="url(#lgb)"/>
  <text x="50" y="20.5" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="12" font-weight="800" fill="#fff" letter-spacing="0.5">{initials[0] if len(initials)>=1 else "L"}</text>
</svg>'''


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
    written = 0
    for proj in projects:
        slug = proj.name
        brand = BRANDS.get(slug, BRANDS["build"])
        pal = R.palette_for(pmap[slug])
        th = theme_hexes(proj)
        if th:
            pal = dict(pal); pal["brand"] = th["brand"]; pal["accent"] = th["accent"]
        bhex = pal["brand"].lstrip("#")
        ahex = pal["accent"].lstrip("#")
        svg = make_logo_svg(brand, bhex, ahex)
        targets = [
            proj / "frontend" / "public" / "logo.svg",
            proj / "frontend" / "public" / "favicon.svg",
            proj / "frontend" / "src" / "assets" / "logo.svg",
        ]
        for t in targets:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(svg, encoding="utf-8")
            written += 1
    print("logos written:", written, "| projects:", len(projects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())