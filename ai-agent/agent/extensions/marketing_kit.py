"""Marketing Kit Auto-Gen — turns design tokens into a sellable brand kit.

From a generated project's `design-tokens.json` it produces:
  - logo.svg (geometric gradient brand mark + wordmark)
  - favicon.svg
  - og-image.svg / og.jpg (1200x630 social card, PNG if Pillow present)
  - app icons (icon-192 / icon-512, PNG if Pillow present, else SVG)
  - README-MARKETING.md (buyer-facing copy)
  - seller-kit.zip (everything above, ready to list on Gumroad/LemonSqueezy)

Rendered into both `public/` roots (static root + frontend/public) so SEO,
PWA and social crawlers all pick up the same brand assets. Never blocks:
missing Pillow simply falls back to SVG-only outputs.
"""
import json
import os
import re
import zipfile
import html
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import agent_logger

_TOKEN_FILES = ("design-tokens.json", "frontend/design-tokens.json")

_DEFAULT_PALETTE = {
    "primary": "#6366f1",
    "secondary": "#a855f7",
    "accent": "#22d3ee",
    "background": "#0b1020",
    "foreground": "#f8fafc",
    "muted": "#94a3b8",
}


def _brand_name(project_dir: Path) -> str:
    name = project_dir.name
    name = re.sub(r"[-_]+", " ", name).strip()
    return (name or "Brand").title()


def _extract_palette(project_dir: Path) -> Dict[str, str]:
    for rel in _TOKEN_FILES:
        cand = project_dir / rel
        if not cand.is_file():
            continue
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
        except Exception:
            continue
        palette = dict(_DEFAULT_PALETTE)
        colors = data.get("color") or data.get("colors") or data.get("palette") or {}
        if not isinstance(colors, dict):
            continue
        for key, val in colors.items():
            val = str(val)
            m = re.search(r"(#(?:[0-9a-fA-F]{3,8}|(?:[0-9a-fA-F]{6})))", val)
            if m:
                palette[key] = m.group(1)
        if any(v != d for v, d in zip(palette.values(), _DEFAULT_PALETTE.values())):
            agent_logger.info(f"[MARKETING] Palette extracted from {rel}")
            return palette
    return dict(_DEFAULT_PALETTE)


def _logo_svg(name: str, palette: Dict[str, str]) -> str:
    """Geometric double-gradient brand mark + wordmark (never plain text)."""
    p = palette
    initial = html.escape(name[:1].upper() or "L")
    word = html.escape(name)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" width="400" height="100">
  <defs>
    <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p['primary']}"/>
      <stop offset="100%" stop-color="{p['secondary']}"/>
    </linearGradient>
    <linearGradient id="g2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p['secondary']}"/>
      <stop offset="100%" stop-color="{p['accent']}"/>
    </linearGradient>
  </defs>
  <rect x="6" y="18" width="64" height="64" rx="16" fill="url(#g1)"/>
  <path d="M14 62 L38 26 L62 62" fill="none" stroke="url(#g2)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="38" cy="34" r="6" fill="{p['foreground']}"/>
  <text x="84" y="62" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="700"
        letter-spacing="1" fill="{p['foreground']}">{word}</text>
</svg>"""


def _favicon_svg(palette: Dict[str, str]) -> str:
    p = palette
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="f" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p['primary']}"/>
      <stop offset="100%" stop-color="{p['secondary']}"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="14" fill="url(#f)"/>
  <path d="M14 44 L32 16 L50 44" fill="none" stroke="{p['foreground']}" stroke-width="6"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="32" cy="28" r="4" fill="{p['foreground']}"/>
</svg>"""


def _og_svg(name: str, palette: Dict[str, str]) -> str:
    p = palette
    word = html.escape(name)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="og1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p['background']}"/>
      <stop offset="100%" stop-color="{p['primary']}"/>
    </linearGradient>
    <linearGradient id="og2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p['secondary']}"/>
      <stop offset="100%" stop-color="{p['accent']}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#og1)"/>
  <circle cx="1030" cy="140" r="220" fill="{p['secondary']}" opacity="0.35"/>
  <circle cx="180" cy="520" r="260" fill="{p['accent']}" opacity="0.22"/>
  <rect x="90" y="210" width="150" height="150" rx="38" fill="url(#og2)"/>
  <path d="M112 312 L156 236 L200 312" fill="none" stroke="{p['foreground']}" stroke-width="14"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="156" cy="252" r="13" fill="{p['foreground']}"/>
  <text x="92" y="460" font-family="Arial, Helvetica, sans-serif" font-size="82" font-weight="800"
        fill="{p['foreground']}">{word}</text>
  <text x="94" y="520" font-family="Arial, Helvetica, sans-serif" font-size="36" fill="{p['muted']}">
    Premium digital experience — designed &amp; built with LumicorePro</text>
</svg>"""


def _rasterize_svg(svg: str, out_png: Path, width: int = 512):
    """Convert SVG text to PNG using Pillow (best-effort; dtcImage no-op on failure)."""
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageOps
    except Exception:
        return False
    try:
        import io
        from PIL import Image
        from argparse import Namespace
        # Minimal embedded renderer: draw a gradient + mark fallback so we never
        # depend on cairosvg. Produces a clean professional tile.
        m = re.search(r"stroke-color=\"(#[0-9a-fA-F]+)\"", svg)
        # Locate the two gradient stop colors.
        stops = re.findall(r'stop-color="(#[0-9a-fA-F]+)"', svg)
        c1 = stops[0] if stops else "#6366f1"
        c2 = stops[1] if stops else "#a855f7"
        img = Image.new("RGB", (width, width))
        px = img.load()
        for y in range(width):
            t = y / width
            r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * t)
            g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * t)
            b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * t)
            for x in range(width):
                px[x, y] = (r, g, b)
        d = ImageDraw.Draw(img)
        d.polygon([(width * 0.25, width * 0.68), (width * 0.5, width * 0.28), (width * 0.75, width * 0.68)],
                  fill=None, outline=None)
        # Ensure outline color parse
        fg = "#ffffff"
        d.line([(width * 0.25, width * 0.68), (width * 0.5, width * 0.28), (width * 0.75, width * 0.68)],
               fill=fg, width=int(width * 0.08))
        d.ellipse([width * 0.5 - width * 0.05, width * 0.28 - width * 0.05,
                   width * 0.5 + width * 0.05, width * 0.28 + width * 0.05], fill=fg)
        img = img.resize((width, width), Image.LANCZOS)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_png), "PNG")
        return True
    except Exception as exc:
        agent_logger.warning(f"[MARKETING] SVG rasterize skipped: {exc}")
        return False


def _buyer_readme(name: str, files: List[str]) -> str:
    joins = "\n".join(f"- `{f}`" for f in files)
    return f"""# {name} — Brand Kit & Seller Package

Thank you for choosing **{name}**. This project ships as a complete, ready-to-sell
digital product with a professional brand identity baked in.

## What's inside
- A fully responsive website (React 19 + Vite + Tailwind) with dark mode, i18n + RTL, and PWA support
- An Express + MySQL + Redis backend with auth, API docs and security middleware
- Design tokens (colors, typography, spacing) so rebranding takes minutes, not days
- PNG/SVG icons, favicon, and a social-sharing OG image

## Included brand assets
{joins}

## Getting started
1. `npm install` in `frontend/` and `backend/`
2. Copy `.env.example` → `.env` and fill in your keys
3. `npm run dev` in `frontend/` to preview locally
4. `npm run build` to produce the production bundle

## Monetization
- List this product on Gumroad, Lemon Squeezy, ThemeForest or Creative Market
- The included checkout + order flow makes it a drop-in "sell-ready" template
- Replace the sample brand assets with your buyer's identity using the token file

## License
MIT — free to use, modify and resell. See `LICENSE.md`.
"""


class MarketingKit:
    """Generate a complete brand kit for a generated project."""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.name = _brand_name(self.project_dir)
        self.palette = _extract_palette(self.project_dir)

    def _public_roots(self) -> List[Path]:
        roots = [self.project_dir]
        if (self.project_dir / "frontend" / "public").is_dir():
            roots.append(self.project_dir / "frontend" / "public")
        return roots

    def generate(self) -> Dict[str, Any]:
        created: List[str] = []
        artifacts: Dict[str, str] = {}

        logo_svg = _logo_svg(self.name, self.palette)
        favicon_svg = _favicon_svg(self.palette)
        og_svg = _og_svg(self.name, self.palette)

        for root in self._public_roots():
            root.mkdir(parents=True, exist_ok=True)
            (root / "logo.svg").write_text(logo_svg, encoding="utf-8")
            (root / "favicon.svg").write_text(favicon_svg, encoding="utf-8")
            (root / "og-image.svg").write_text(og_svg, encoding="utf-8")
            created += ["logo.svg", "favicon.svg", "og-image.svg"]
            # PNG variants (rasterization best-effort)
            for w in (192, 512):
                ok = _rasterize_svg(logo_svg, root / f"icon-{w}.png", w)
                if ok:
                    created += [f"icon-{w}.png"]
                artifacts[f"icon-{w}"] = "png" if ok else "svg"

        # Pillow OG → JPG (only cite as jpg when it actually exists)
        og_ok = _rasterize_svg(og_svg, self.project_dir / "public" / "_og_tmp.png", 1200 // 1)
        if og_ok:
            for base_dir in (self.project_dir, self.project_dir / "frontend" / "public"):
                if not base_dir.is_dir():
                    continue
                src = self.project_dir / "public" / "_og_tmp.png"
                try:
                    from PIL import Image
                    im = Image.open(src)
                    im.save(str(base_dir / "og.jpg"), "JPEG", quality=88)
                    created += ["og.jpg"]
                except Exception:
                    pass
            (self.project_dir / "public" / "_og_tmp.png").unlink(missing_ok=True)
        artifacts["og_image"] = "jpg" if og_ok else "svg"

        # Marketing README + seller kit zip
        readme_path = self.project_dir / "README-MARKETING.md"
        readme_path.write_text(_buyer_readme(self.name, sorted(set(created))), encoding="utf-8")
        created += ["README-MARKETING.md"]

        kit_path = self.project_dir / "marketing-kit.zip"
        with zipfile.ZipFile(kit_path, "w", zipfile.ZIP_DEFLATED) as zf:
            seen = set()
            for root in self._public_roots():
                for fname in ("logo.svg", "favicon.svg", "og-image.svg", "og.jpg"):
                    fp = root / fname
                    if fp.is_file() and fname not in seen:
                        zf.write(fp, f"brand/{fname}")
                        seen.add(fname)
            if readme_path.is_file():
                zf.write(readme_path, "README-MARKETING.md")
        if kit_path.is_file():
            created += ["marketing-kit.zip"]

        return {
            "status": "ok",
            "project": self.name,
            "palette": {k: v for k, v in self.palette.items()},
            "created": sorted(set(created)),
            "kit_path": str(kit_path),
            "artifacts": artifacts,
            "tip": "Replace sample OG/logo with buyer assets via design-tokens.json before shipping.",
        }


def generate_marketing_kit(project_dir: str) -> Dict[str, Any]:
    return MarketingKit(project_dir).generate()