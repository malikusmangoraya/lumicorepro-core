#!/usr/bin/env python3
"""Brand identity + logo pass for the ten sellable products in products/.

Deterministic and idempotent. For every product it:

  1. Builds a professional identity kit from the product's own design tokens:
     favicon.svg, favicon.ico, PWA icon PNGs (72/96/128/144/152/192/384/512
     plus a maskable variant), apple-touch-icon.png, og-image.svg, og-image.png.
  2. Rewrites public/manifest.json so it points at files that exist and uses
     relative URLs (the old ones were absolute, which 404s under a GitHub Pages
     project subpath).
  3. Generates one canonical vector logo component per product and rewrites the
     four existing logo components into thin wrappers, so every import path in
     the app keeps working while the artwork and palette become brand-specific.
  4. Repoints canonical URLs (index.html canonical/hreflang/og/twitter,
     public/robots.txt, public/sitemap.xml, JSON-LD) at the live URL recorded in
     LIVE_URL.txt, which is a real GitHub Pages URL.
  5. Removes the generator brand leak from shipped source.
  6. Clears placeholder text (example.com) using the RFC 2606 reserved .test
     TLD, so sample data can never resolve.

Usage:  python scripts/brand_pass.py [--dry-run] [--only slug ...]
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from brand_map import BRANDS as BRAND_MAP
except Exception:  # pragma: no cover - the map is optional
    BRAND_MAP = {}

from logo_symbols import SYMBOLS, SYMBOL_LABELS, symbol_to_svg, draw_symbol

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

PRODUCTS = [
    "apex",
    "aurelia-estates",
    "aurum-fitness",
    "claimflow-ai",
    "flowpilot",
    "meridian-capital",
    "nuage-events",
    "prestige-studio",
    "resupro",
    "saffron-voyage",
    "studio-lumen",
]

ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Per-product logo identity: (gradient start, gradient end, angle).
#
# Five of the ten products share an identical three-colour palette, so the
# palette alone cannot tell their logos apart. Each product therefore gets its
# own start/end pair and its own gradient angle, drawn only from colours its
# own design tokens already define - the mark stays on-theme but is visually
# distinct from every other product in the catalogue.
LOGO_IDENTITY = {
    "apex":             ("#00e5ff", "#7c4dff", 135),
    "aurelia-estates":  ("#a855f7", "#38bdf8", 120),
    "aurum-fitness":    ("#ec4899", "#8b5cf6", 150),
    "claimflow-ai":     ("#dc2626", "#2563eb", 135),
    "flowpilot":         ("#10b981", "#6366f1", 140),
    "meridian-capital": ("#38bdf8", "#a855f7", 150),
    "nuage-events":     ("#0ea5e9", "#111827", 120),
    "prestige-studio":  ("#2563eb", "#dc2626", 165),
    "resupro":          ("#b91c1c", "#1d4ed8", 105),
    "saffron-voyage":   ("#111827", "#0ea5e9", 135),
    "studio-lumen":     ("#06b6d4", "#8b5cf6", 165),
}

TEXT_SUFFIXES = {
    ".md", ".html", ".json", ".js", ".jsx", ".mjs", ".cjs",
    ".txt", ".xml", ".yml", ".yaml", ".css", ".svg", ".toml", ".env",
    ".example", ".sh", ".ps1",
}

# Domains that belong to third parties and must never be rewritten.
THIRD_PARTY_DOMAINS = {
    "schema.org", "www.w3.org", "www.w3.org", "w3.org",
    "fonts.googleapis.com", "fonts.gstatic.com",
    "github.com", "www.github.com", "githubusercontent.com",
    "raw.githubusercontent.com", "pages.github.com",
    "npmjs.com", "www.npmjs.com", "registry.npmjs.org",
    "developer.mozilla.org", "nodejs.org", "www.nodejs.org",
    "stripe.com", "www.stripe.com", "docs.stripe.com",
    "paypal.com", "www.paypal.com", "developer.paypal.com",
    "lemonsqueezy.com", "www.lemonsqueezy.com", "docs.lemonsqueezy.com",
    "paddle.com", "www.paddle.com",
    "razorpay.com", "www.razorpay.com",
    "squareup.com", "www.squareup.com",
    "mollie.com", "www.mollie.com",
    "flutterwave.com", "www.flutterwave.com",
    "mercadopago.com", "www.mercadopago.com",
    "liqpay.com", "www.liqpay.com",
    "paytm.com", "www.paytm.com",
    "bkash.com", "www.bkash.com",
    "google.com", "www.google.com", "googleapis.com",
    "apple.com", "www.apple.com", "developer.apple.com",
    "mozilla.org", "developer.mozilla.org",
    "ubuntu.com", "debian.org", "postgresql.org", "www.postgresql.org",
    "redis.io", "www.redis.io",
    "letsencrypt.org", "certbot.eff.org", "eff.org",
    "cloudflare.com", "www.cloudflare.com", "developers.cloudflare.com",
    "vercel.com", "www.vercel.com", "netlify.com", "www.netlify.com",
    "render.com", "www.render.com", "railway.app", "fly.io",
    "heroku.com", "www.heroku.com",
    "docker.com", "www.docker.com", "hub.docker.com",
    "sentry.io", "www.sentry.io",
    "openai.com", "www.openai.com", "platform.openai.com",
    "anthropic.com", "www.anthropic.com",
    "supabase.com", "www.supabase.com",
    "twilio.com", "www.twilio.com", "sendgrid.com", "www.sendgrid.com",
    "mailchimp.com", "sendinblue.com",
    "localhost", "127.0.0.1", "0.0.0.0",
    "opencollective.com", "www.opencollective.com", "tidelift.com",
    "patreon.com", "www.patreon.com", "liberapay.com", "ko-fi.com",
    "unsplash.com", "images.unsplash.com", "source.unsplash.com",
    "imgur.com", "i.imgur.com", "giphy.com", "pexels.com",
    "opensource.org", "www.opensource.org", "choosealicense.com",
    "githubusercontent.com", "codecov.io", "coveralls.io",
    "unicode.org", "www.unicode.org", "iana.org", "www.iana.org",
    "json-schema.org", "swagger.io", "postman.com", "www.postman.com",
    # social / profiles
    "instagram.com", "www.instagram.com", "facebook.com", "www.facebook.com",
    "twitter.com", "www.twitter.com", "x.com", "www.x.com",
    "linkedin.com", "www.linkedin.com", "youtube.com", "www.youtube.com",
    "tiktok.com", "pinterest.com", "wa.me", "t.me", "discord.gg", "discord.com",
    # XML / metadata namespaces (never rewrite these - they are not URLs)
    "sitemaps.org", "www.sitemaps.org", "ogp.me", "www.ogp.me",
}

# Files that carry the product's canonical identity. The canonical domain is
# detected from these only, so npm funding URLs and third-party links in the
# lockfiles can never be mistaken for the product's own domain.
SEO_FILES = (
    "frontend/index.html",
    "frontend/public/robots.txt",
    "frontend/public/sitemap.xml",
    "frontend/src/seo-config.json",
    "frontend/src/structured-data.json",
    "frontend/src/hreflang-config.json",
    "frontend/src/config/structured-data.js",
    "structured-data.json",
)

# Never rewritten: npm needs these byte-identical for `npm ci`.
LOCKED_FILES = ("package-lock.json", "package.json", "npm-shrinkwrap.json")

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype"), Path("/System/Library/Fonts")]
BOLD_FONTS = ["segoeuib.ttf", "arialbd.ttf", "seguisb.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"]
REGULAR_FONTS = ["segoeui.ttf", "arial.ttf", "segoeuisl.ttf", "calibri.ttf", "DejaVuSans.ttf"]


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def hex_to_rgb(value: str, default=(16, 24, 40)):
    if not isinstance(value, str):
        return default
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return default
    try:
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    except ValueError:
        return default


def luminance(rgb) -> float:
    r, g, b = (c / 255.0 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mix(c1, c2, t: float):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "brand"


def _darken(hex_color: str, amount: float) -> str:
    rgb = hex_to_rgb(hex_color)
    return "#" + "".join(f"{int(round(c * (1 - amount))):02x}" for c in rgb)


def _usable_end(primary: str, candidate: str) -> bool:
    """True when candidate is a real gradient endpoint distinct from primary."""
    if not candidate:
        return False
    c = hex_to_rgb(candidate)
    if luminance(c) < 0.05:          # black / near-black reads as a flat tile
        return False
    p = hex_to_rgb(primary)
    if sum(abs(a - b) for a, b in zip(c, p)) < 24:   # effectively the same colour
        return False
    return True


def find_font(names):
    for name in names:
        for d in FONT_DIRS:
            p = d / name
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), 100)
                except Exception:
                    continue
    return None


FONT_BOLD = find_font(BOLD_FONTS)
FONT_REGULAR = find_font(REGULAR_FONTS)


# --------------------------------------------------------------------------- #
# product facts
# --------------------------------------------------------------------------- #
class Brand:
    def __init__(self, slug: str):
        self.slug = slug
        self.root = PRODUCTS_DIR / slug
        self.frontend = self.root / "frontend"
        self.public = self.frontend / "public"

        # Brand identity comes from the shared brand map (one source of truth
        # for name and tagline); the shipped <title> is the fallback.
        entry = BRAND_MAP.get(slug, {})
        name = entry.get("name") or ""
        tagline = entry.get("tagline") or ""
        html = self.frontend / "index.html"
        html_text = ""
        if html.exists():
            html_text = html.read_text(encoding="utf-8", errors="replace")
            if not name:
                m = re.search(r"<title>(.*?)</title>", html_text, re.S)
                if m:
                    name = re.split(r"\s+[—–|-]\s+", m.group(1).strip())[0].strip()
        if not tagline and html_text:
            m = re.search(r'<meta name="description" content="(.*?)"', html_text, re.S)
            if m:
                tagline = re.split(r"(?<=[.!?])\s", re.sub(r"\s+", " ", m.group(1)).strip())[0]
        self.name = name or slug.replace("-", " ").title()
        self.tagline = tagline
        self.initials = self._initials(self.name)

        tokens = load_json(self.frontend / "design-tokens.json") or {}
        palette = tokens.get("palette") or {}
        primary = palette.get("primary") or palette.get("secondary") or "#4f46e5"
        accent = palette.get("accent") or ""
        # A gradient endpoint that is pure black (or the same hue as primary)
        # makes a flat, muddy mark, so prefer the accent and fall back to a
        # darkened primary rather than shipping a black tile.
        secondary = palette.get("secondary") or ""
        if not _usable_end(primary, secondary):
            secondary = accent if _usable_end(primary, accent) else _darken(primary, 0.45)
        if not _usable_end(primary, secondary):
            secondary = _darken(primary, 0.45)

        # A curated per-product identity wins, so no two marks in the
        # catalogue share a gradient.
        angle = 135.0
        identity = LOGO_IDENTITY.get(slug)
        if identity:
            primary, secondary, angle = identity
        self.gradient_angle = angle

        self.palette = {
            "primary": primary,
            "secondary": secondary,
            "accent": accent or primary,
            "bg": palette.get("bg") or "#0b1220",
            "card": palette.get("card") or "#111827",
            "text": palette.get("text") or "#e2e8f0",
            "muted": palette.get("muted") or "#94a3b8",
        }
        self.style = tokens.get("style") or "modern"
        self.display_font = (tokens.get("typography") or {}).get("display") or "Inter"
        self.sans_font = (tokens.get("typography") or {}).get("sans") or "Inter"

        # Live URL (GitHub Pages). The demo is served from a project subpath.
        live = ""
        live_file = self.root / "LIVE_URL.txt"
        if live_file.exists():
            live = live_file.read_text(encoding="utf-8", errors="replace").strip()
        if not live.startswith("http"):
            live = ""
        self.live_base = live.rstrip("/")
        self.live_url_ok = bool(self.live_base)

        self.domain = slugify(self.name) + ".test"

    @staticmethod
    def _initials(name: str) -> str:
        words = [w for w in re.split(r"[\s&]+", name) if w and w[0].isalpha()]
        if not words:
            return name[:1].upper()
        if len(words) == 1:
            return words[0][:2].upper() if len(words[0]) > 1 else words[0].upper()
        return (words[0][0] + words[1][0]).upper()

    @property
    def c_primary(self):
        return hex_to_rgb(self.palette["primary"])

    @property
    def c_secondary(self):
        return hex_to_rgb(self.palette["secondary"])

    @property
    def c_bg(self):
        return hex_to_rgb(self.palette["bg"])

    @property
    def c_text(self):
        return hex_to_rgb(self.palette["text"])

    @property
    def c_muted(self):
        return hex_to_rgb(self.palette["muted"])

    @property
    def c_card(self):
        return hex_to_rgb(self.palette["card"])

    @property
    def mark_ink(self):
        """White ink on the gradient tile, dark ink only when the tile is pale."""
        return (11, 18, 32) if luminance(mix(self.c_primary, self.c_secondary, 0.5)) > 0.72 else (255, 255, 255)

    @property
    def mark_knock(self):
        """Deeper tone of the tile gradient, for shapes cut out of a larger one.

        Always distinct from both gradient stops, so it reads on a pale tile and
        on a dark one alike.
        """
        mid = mix(self.c_primary, self.c_secondary, 0.5)
        knock = mix(mid, (0, 0, 0), 0.42)
        return knock if sum(abs(a - b) for a, b in zip(knock, mid)) >= 36 else mix(mid, (255, 255, 255), 0.45)

    @property
    def light_site(self) -> bool:
        return luminance(self.c_bg) > 0.6


# --------------------------------------------------------------------------- #
# raster rendering
# --------------------------------------------------------------------------- #
SS = 4  # supersampling factor


def linear_gradient(w, h, c1, c2, angle_deg: float = 135.0) -> Image.Image:
    import numpy as np

    a = math.radians(angle_deg)
    xs = np.linspace(0.0, 1.0, w, dtype=np.float64)[None, :]
    ys = np.linspace(0.0, 1.0, h, dtype=np.float64)[:, None]
    t = xs * math.cos(a) + ys * math.sin(a)
    t = (t - t.min()) / max(t.max() - t.min(), 1e-9)
    arr = np.zeros((h, w, 3), dtype=np.float64)
    for i in range(3):
        arr[:, :, i] = c1[i] + (c2[i] - c1[i]) * t
    return Image.fromarray(arr.clip(0, 255).astype("uint8"), "RGB")


def text_width(draw, text, font, tracking):
    if not text:
        return 0
    return sum(draw.textlength(ch, font=font) for ch in text) + tracking * (len(text) - 1)


def draw_tracked(draw, cx, cy, text, font, fill, tracking=0):
    w = text_width(draw, text, font, tracking)
    x = cx - w / 2.0
    for ch in text:
        draw.text((x, cy), ch, font=font, fill=fill, anchor="lm")
        x += draw.textlength(ch, font=font) + tracking
    return w


def render_mark(brand: Brand, size: int, maskable: bool = False, rounded: bool = True) -> Image.Image:
    """The app icon: gradient tile + geometric monogram, with a soft depth sheen."""
    S = size * SS
    tile = linear_gradient(S, S, brand.c_primary, brand.c_secondary, brand.gradient_angle).convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    if maskable or not rounded:
        md.rectangle([0, 0, S - 1, S - 1], fill=255)
    else:
        md.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.2237), fill=255)

    # Soft light sweep across the upper third gives the flat gradient depth.
    sheen = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([-int(S * 0.45), -int(S * 0.85), int(S * 1.45), int(S * 0.62)], fill=(255, 255, 255, 34))
    tile = Image.alpha_composite(tile, sheen)

    draw = ImageDraw.Draw(tile)
    ink = brand.mark_ink
    if brand.slug in SYMBOLS:
        # Purpose-built symbol: bigger presence, legible down to 16px.
        pad = 0.30 if maskable else 0.22
        draw_symbol(draw, brand.slug, (S * pad, S * pad, S * (1 - pad), S * (1 - pad)),
                    ink + (255,), brand.mark_knock + (255,), scale=1.0)
    else:
        glyph_scale = 0.50 if maskable else 0.58
        font_px = int(S * glyph_scale)
        font = _sized(FONT_BOLD, font_px)
        tracking = font_px * 0.06
        draw_tracked(draw, S / 2, S / 2 - S * 0.005, brand.initials, font, ink + (255,), tracking)

    if maskable:
        out = Image.alpha_composite(Image.new("RGBA", (S, S), (0, 0, 0, 0)), tile)
    else:
        out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        out.paste(tile, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


def _sized(base_font, px):
    if base_font is None:
        return ImageFont.load_default()
    try:
        # Re-create the same typeface at the requested pixel size.
        path = getattr(base_font, "path", None)
        if path:
            return ImageFont.truetype(path, px)
    except Exception:
        pass
    return base_font


def render_og_image(brand: Brand) -> Image.Image:
    """The 1200x630 share card: mark, wordmark, tagline, live host."""
    W, H = 1200, 630
    bg_top = brand.c_bg
    bg_bottom = mix(brand.c_bg, brand.c_card, 0.85)
    canvas = linear_gradient(W, H, bg_top, bg_bottom, 110.0).convert("RGBA")

    # Accent wash so the card is not a flat rectangle.
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    accent = brand.c_primary if not brand.light_site else brand.c_secondary
    wd.ellipse([W * 0.52, -H * 0.55, W * 1.25, H * 0.75], fill=accent + (38,))
    canvas = Image.alpha_composite(canvas, wash)

    canvas.alpha_composite(render_mark(brand, 148), (88, H // 2 - 74))

    d = ImageDraw.Draw(canvas)
    ink = brand.c_text if brand.light_site else (248, 250, 252)
    sub = brand.c_muted if brand.light_site else (203, 213, 225)

    x0 = 88 + 148 + 56
    name_font = _sized(FONT_BOLD, 72)
    d.text((x0, H // 2 - 62), brand.name, font=name_font, fill=ink + (255,), anchor="lm")

    d.rounded_rectangle([x0, H // 2 - 18, x0 + 92, H // 2 - 14], radius=2, fill=accent + (255,))
    tag_font = _sized(FONT_REGULAR, 30)
    d.text((x0, H // 2 + 26), brand.tagline or brand.palette.get("accent", ""),
           font=tag_font, fill=sub + (255,), anchor="lm")

    foot_font = _sized(FONT_REGULAR, 22)
    d.text((W - 88, H - 56), brand.live_base.replace("https://", "") or brand.slug,
           font=foot_font, fill=sub + (170,), anchor="rs")
    return canvas.convert("RGB")


def save_png(img: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)


# --------------------------------------------------------------------------- #
# vector assets
# --------------------------------------------------------------------------- #
def favicon_svg(brand: Brand) -> str:
    p1, p2, ink = brand.palette["primary"], brand.palette["secondary"], brand.mark_ink
    if brand.slug in SYMBOLS:
        pad = 14.0
        body = (f'  <g transform="translate({pad} {pad}) scale({(64 - 2 * pad) / 64:.4f})">\n    '
                + symbol_to_svg(brand.slug, f"rgb{ink}", f"rgb{brand.mark_knock}") + "\n  </g>")
    else:
        body = (f'  <text x="32" y="32" text-anchor="middle" dominant-baseline="central"\n'
                f'        font-family="{brand.display_font}, Inter, system-ui, sans-serif"\n'
                f'        font-size="34" font-weight="800" letter-spacing="0.5" '
                f'fill="rgb{ink}">{brand.initials}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="{brand.name}">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p1}"/>
      <stop offset="100%" stop-color="{p2}"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14.3" fill="url(#g)"/>
{body}
</svg>
"""


def og_svg(brand: Brand) -> str:
    p1, p2 = brand.palette["primary"], brand.palette["secondary"]
    bg, card = brand.palette["bg"], brand.palette["card"]
    ink = brand.palette["text"] if brand.light_site else "#f8fafc"
    sub = brand.palette["muted"] if brand.light_site else "#cbd5e1"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{brand.name}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{bg}"/>
      <stop offset="1" stop-color="{card}"/>
    </linearGradient>
    <linearGradient id="mark" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{p1}"/>
      <stop offset="1" stop-color="{p2}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <g opacity="0.10" transform="translate(292,315)">
    <rect x="-204" y="-235" width="1040" height="470" rx="28" fill="none" stroke="{ink}" stroke-width="2"/>
  </g>
  <g>
    <rect x="88" y="241" width="148" height="148" rx="33" fill="url(#mark)"/>
    <g transform="translate(125 278) scale(2.3125)">
      {symbol_to_svg(brand.slug, f"rgb{brand.mark_ink}", f"rgb{brand.mark_knock}") if brand.slug in SYMBOLS else ''}
    </g>
    {'    <text x="162" y="315" text-anchor="middle" dominant-baseline="central" font-family="' + brand.display_font + ', Inter, system-ui, sans-serif" font-size="80" font-weight="800" letter-spacing="1" fill="rgb' + str(brand.mark_ink) + '">' + brand.initials + '</text>' if brand.slug not in SYMBOLS else ''}
  </g>
  <text x="292" y="290" font-family="{brand.display_font}, Inter, system-ui, sans-serif"
        font-size="72" font-weight="800" fill="{ink}">{brand.name}</text>
  <rect x="292" y="308" width="92" height="5" rx="2.5" fill="{brand.palette['accent']}"/>
  <text x="292" y="352" font-family="{brand.sans_font}, Inter, system-ui, sans-serif"
        font-size="30" fill="{sub}">{brand.tagline}</text>
</svg>
"""


def manifest_json(brand: Brand, description: str) -> str:
    data = {
        "name": brand.name,
        "short_name": brand.name[:12],
        "description": description,
        "start_url": "./",
        "scope": "./",
        "id": "./",
        "display": "standalone",
        "background_color": brand.palette["bg"],
        "theme_color": brand.palette["primary"],
        "orientation": "portrait-primary",
        "icons": [
            {"src": "favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
            {"src": "icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icons/icon-maskable-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "categories": ["productivity", "business"],
        "screenshots": [],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- #
# react components
# --------------------------------------------------------------------------- #
def brand_js(brand: Brand) -> str:
    return f"""// Single source of truth for {brand.name} brand constants.
// Colours mirror frontend/design-tokens.json and frontend/public/favicon.svg.
export const BRAND = {{
  name: {json.dumps(brand.name)},
  initials: {json.dumps(brand.initials)},
  primary: {json.dumps(brand.palette["primary"])},
  secondary: {json.dumps(brand.palette["secondary"])},
  accent: {json.dumps(brand.palette["accent"])},
  displayFont: {json.dumps(brand.display_font)},
  sansFont: {json.dumps(brand.sans_font)},
}};

export default BRAND;
"""


def brand_mark_jsx(brand: Brand) -> str:
    if brand.slug in SYMBOLS:
        pad = 14.0
        scale = (64 - 2 * pad) / 64.0
        knock_hex = "%02x%02x%02x" % brand.mark_knock
        glyph = symbol_to_svg(brand.slug, "#ffffff", f"#{knock_hex}").replace('"', "'")
        body = (f'      <g transform="translate({pad} {pad}) scale({scale:.4f})">\n'
                f'        {glyph}\n'
                f'      </g>')
        desc = SYMBOL_LABELS.get(brand.slug, brand.name)
    else:
        body = (f'      <text\n'
                f'        x="32"\n'
                f'        y="32"\n'
                f'        textAnchor="middle"\n'
                f'        dominantBaseline="central"\n'
                f'        fontFamily={{`${{BRAND.displayFont}}, Inter, system-ui, sans-serif`}}\n'
                f'        fontSize="34"\n'
                f'        fontWeight="800"\n'
                f'        letterSpacing="0.5"\n'
                f'        fill="#ffffff"\n'
                f'      >\n'
                f'        {{BRAND.initials}}\n'
                f'      </text>')
        desc = "the brand monogram"
    return f"""import React from 'react';
import {{ BRAND }} from './BRAND';

/**
 * The {brand.name} mark: a gradient tile carrying {desc}.
 * Vector only - no raster assets - so it stays crisp at any size and
 * inherits the surrounding layout.
 */
export function BrandMark({{ size = 34, className = '', title, ...rest }}) {{
  const uid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const gid = `bm-{{uid}}`;
  const label = title || BRAND.name;
  return (
    <svg
      viewBox="0 0 64 64"
      width={{size}}
      height={{size}}
      className={{className}}
      role="img"
      aria-label={{label}}
      {{...rest}}
    >
      <defs>
        <linearGradient id={{gid}} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={{BRAND.primary}} />
          <stop offset="100%" stopColor={{BRAND.secondary}} />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="14.3" fill={{`url(#${{gid}})`}} />
{body}
    </svg>
  );
}}

export default BrandMark;
"""


def brand_lockup_jsx(brand: Brand) -> str:
    return f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ BrandMark }} from './BrandMark';
import {{ BRAND }} from './BRAND';

/** Mark + wordmark lockup used in the navbar and footer. */
export default function BrandLockup({{ to = '/', size = 34, dark = false, className = '' }}) {{
  return (
    <Link
      to={{to}}
      className={{`inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90 ${{className}}`}}
      aria-label={{BRAND.name}}
    >
      <BrandMark size={{size}} className="shrink-0" />
      <span
        className="font-bold tracking-tight leading-none whitespace-nowrap"
        style={{{{
          fontFamily: `${{BRAND.displayFont}}, system-ui, -apple-system, 'Segoe UI', sans-serif`,
          color: dark ? '#ffffff' : 'var(--t-heading, inherit)',
        }}}}
      >
        {{BRAND.name}}
      </span>
    </Link>
  );
}}
"""


def wrapper_jsx(brand: Brand, kind: str) -> str:
    """Rewrite an existing logo component as a thin wrapper over the canonical mark."""
    header = f"// {brand.name} logo wrapper. The artwork lives in ./brand/BrandMark.jsx."
    if kind == "root_brand":          # components/BrandLogo.jsx  -> BrandLockup({to,size,dark})
        return f"""{header}
export {{ default }} from './brand/BrandLockup';
"""
    if kind == "root_unique":         # components/UniqueLogo.jsx  -> UniqueLogo({{size:'sm'|'md'|'lg'}})
        return f"""{header}
import React from 'react';
import BrandLockup from './brand/BrandLockup';

const SIZES = {{ sm: 24, md: 32, lg: 40 }};

export default function UniqueLogo({{ size = 'md' }}) {{
  return <BrandLockup size={{SIZES[size] || SIZES.md}} />;
}}
"""
    if kind == "common_brand":        # components/common/BrandLogo.jsx -> LogoMark + BrandLogo({size,className})
        return f"""{header}
import React from 'react';
import {{ BrandMark }} from '../brand/BrandMark';

const SIZES = {{ sm: 24, md: 30, lg: 40 }};

export function LogoMark({{ size = 30, className = '' }}) {{
  return <BrandMark size={{size}} className={{className}} />;
}}

export default function BrandLogo({{ size = 'md', className = '' }}) {{
  return <LogoMark size={{SIZES[size] || SIZES.md}} className={{className}} />;
}}
"""
    # common_unique -> UniqueLogo({name,size}) kept API-compatible
    return f"""{header}
import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ BrandMark }} from '../brand/BrandMark';
import {{ BRAND }} from '../brand/BRAND';

const SIZES = {{ sm: 24, md: 32, lg: 40 }};

export const LOGO_SYMBOLS = [BRAND];

export default function UniqueLogo({{ name, size = 'md', className = '' }}) {{
  const px = SIZES[size] || SIZES.md;
  const label = name || BRAND.name;
  return (
    <Link
      to="/"
      className={{`inline-flex items-center gap-2.5 select-none ${{className}}`}}
      aria-label={{label}}
    >
      <BrandMark size={{px}} className="shrink-0" />
      <span className="font-bold tracking-tight whitespace-nowrap">{{label}}</span>
    </Link>
  );
}}
"""


# --------------------------------------------------------------------------- #
# URL repair
# --------------------------------------------------------------------------- #
URL_RE = re.compile(r"https?://([a-z0-9][a-z0-9.-]*\.[a-z]{2,12})(?=[/\"'#?)\s]|$)")


def find_own_domains(root: Path):
    """Stale canonical domains this product still carries.

    Detected only from the SEO identity files, so npm funding URLs and other
    third-party links elsewhere in the tree can never be mistaken for the
    product's own domain. A product may legitimately carry more than one stale
    host (one per file), so every candidate found this way is returned.
    """
    counter: Counter = Counter()
    for rel in SEO_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in URL_RE.finditer(text):
            dom = m.group(1).lower()
            if dom in THIRD_PARTY_DOMAINS or "github.io" in dom:
                continue
            counter[dom] += 1
    return [d for d, _ in counter.most_common(8)]


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "node_modules" in path.parts or ".git" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith(".env"):
            yield path


def replace_in_files(root: Path, pairs, dry: bool, log):
    """Apply literal (old, new) replacements across the product tree."""
    changed = 0
    for path in iter_text_files(root):
        if path.name in LOCKED_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        original = text
        for old, new in pairs:
            text = text.replace(old, new)
        if text != original:
            changed += 1
            log(f"    rewrite {path.relative_to(root).as_posix()}")
            if not dry:
                path.write_text(text, encoding="utf-8")
    return changed


# --------------------------------------------------------------------------- #
# per-product work
# --------------------------------------------------------------------------- #
def process(slug: str, dry: bool, log):
    brand = Brand(slug)
    if not brand.frontend.is_dir():
        log(f"  SKIP {slug}: no frontend/")
        return None

    result = {"slug": slug, "files": 0, "urls": 0, "notes": []}

    def write(path: Path, content: str):
        if dry:
            existing = path.read_text(encoding="utf-8") if path.exists() else None
            if existing != content:
                result["files"] += 1
                log(f"    would write {path.relative_to(brand.root).as_posix()}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        result["files"] += 1

    # 1. description for the manifest, taken from the shipped page
    description = ""
    meta = re.search(r'<meta name="description" content="(.*?)"', brand.frontend.joinpath("index.html").read_text(encoding="utf-8", errors="replace"), re.S) if brand.frontend.joinpath("index.html").exists() else None
    if meta:
        description = re.sub(r"\s+", " ", meta.group(1)).strip()
    if not description:
        description = f"{brand.name} — production-ready application."

    # 2. identity kit
    log(f"  [{slug}] {brand.name}  initials={brand.initials}  "
        f"primary={brand.palette['primary']} secondary={brand.palette['secondary']}  live={brand.live_base or 'MISSING'}")

    icons_dir = brand.public / "icons"
    for size in ICON_SIZES:
        img = render_mark(brand, size)
        path = icons_dir / f"icon-{size}x{size}.png"
        if dry:
            if not path.exists():
                result["files"] += 1
                log(f"    would write {path.relative_to(brand.root).as_posix()}")
        else:
            save_png(img, path)
            result["files"] += 1

    maskable = render_mark(brand, 512, maskable=True)
    mpath = icons_dir / "icon-maskable-512x512.png"
    if dry:
        if not mpath.exists():
            result["files"] += 1
    else:
        save_png(maskable, mpath)
        result["files"] += 1

    # apple touch icon: opaque, iOS rejects transparency
    apple = render_mark(brand, 180, maskable=True)
    apath = brand.public / "apple-touch-icon.png"
    if dry:
        if not apath.exists():
            result["files"] += 1
    else:
        save_png(apple.convert("RGB"), apath)
        result["files"] += 1

    # favicon.ico (browsers still request /favicon.ico unprompted)
    ipath = brand.public / "favicon.ico"
    if dry:
        if not ipath.exists():
            result["files"] += 1
            log(f"    would write {ipath.relative_to(brand.root).as_posix()}")
    else:
        render_mark(brand, 64).save(ipath, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        result["files"] += 1

    write(brand.public / "favicon.svg", favicon_svg(brand))
    write(brand.public / "og-image.svg", og_svg(brand))
    write(brand.public / "manifest.json", manifest_json(brand, description))

    og_png = brand.public / "og-image.png"
    if dry:
        if not og_png.exists():
            result["files"] += 1
    else:
        save_png(render_og_image(brand), og_png)
        result["files"] += 1

    # 3. react identity components
    brand_dir = brand.frontend / "src" / "components" / "brand"
    write(brand_dir / "BRAND.js", brand_js(brand))
    write(brand_dir / "BrandMark.jsx", brand_mark_jsx(brand))
    write(brand_dir / "BrandLockup.jsx", brand_lockup_jsx(brand))
    comp = brand.frontend / "src" / "components"
    write(comp / "BrandLogo.jsx", wrapper_jsx(brand, "root_brand"))
    write(comp / "UniqueLogo.jsx", wrapper_jsx(brand, "root_unique"))
    write(comp / "common" / "BrandLogo.jsx", wrapper_jsx(brand, "common_brand"))
    write(comp / "common" / "UniqueLogo.jsx", wrapper_jsx(brand, "common_unique"))

    # 4. generator identity leak
    leak = brand.name
    result["urls"] += replace_in_files(brand.frontend, [("LuminaCore", leak)], dry, log)

    # 5. canonical URLs -> the recorded live GitHub Pages URL
    own = find_own_domains(brand.root)
    if brand.live_base and own:
        pairs = [(f"https://{d}", brand.live_base) for d in own]
        pairs += [(f"http://{d}", brand.live_base) for d in own]
        result["urls"] += replace_in_files(brand.root, pairs, dry, log)
        result["notes"].append(f"canonical base {own} -> {brand.live_base}")
    elif not brand.live_base:
        result["notes"].append("LIVE_URL.txt missing or not a URL - canonical URLs left alone")

    # the schema logo must point at a file that exists
    if brand.live_base:
        replace_in_files(brand.root, [
            (f"{brand.live_base}/logo.svg", f"{brand.live_base}/icons/icon-512x512.png"),
            (f"{brand.live_base}/og-image.svg", f"{brand.live_base}/og-image.png"),
        ], dry, log)

    # 6. head tags: real icon + real share image
    index = brand.frontend / "index.html"
    if index.exists():
        html = index.read_text(encoding="utf-8", errors="replace")
        new = html
        if '<link rel="apple-touch-icon"' not in new:
            new = new.replace(
                '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />',
                '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />\n'
                '    <link rel="alternate icon" href="/favicon.ico" sizes="32x32" />\n'
                '    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />',
                1,
            )
        if brand.live_base:
            new = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf'\g<1>{brand.live_base}/og-image.png\g<2>', new)
            new = re.sub(r'(<meta property="og:image:type" content=")[^"]*(")', r'\g<1>image/png\g<2>', new)
            new = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', rf'\g<1>{brand.live_base}/og-image.png\g<2>', new)
        if new != html:
            log("    rewrite frontend/index.html (head tags)")
            result["urls"] += 1
            if not dry:
                index.write_text(new, encoding="utf-8")

    # 7. placeholder domains -> RFC 2606 reserved .test, plus a go-live note
    result["urls"] += replace_in_files(brand.root, [("example.com", brand.domain)], dry, log)

    note = (
        f"> **Before you go live:** every address in these documents uses the reserved "
        f"`{brand.domain}` domain (RFC 2606). Replace them with your real support address — "
        f"for example `support@yourdomain.com` — in DEPLOYMENT.md, SECURITY.md and "
        f"THIRD_PARTY_NOTICES.md.\n"
    )
    for doc in ("DEPLOYMENT_CHECKLIST.md", "BUYER_DOCUMENTATION.md"):
        path = brand.root / doc
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if brand.domain in text and "RFC 2606" not in text:
            if not dry:
                path.write_text(text.rstrip() + "\n\n" + note, encoding="utf-8")
            result["files"] += 1

    # 8. brand guidelines for whoever picks this up
    guidelines = brand_guidelines_md(brand)
    gpath = brand.root / "BRAND_GUIDELINES.md"
    if dry:
        if not gpath.exists() or gpath.read_text(encoding="utf-8", errors="replace") != guidelines:
            result["files"] += 1
    else:
        gpath.write_text(guidelines, encoding="utf-8")
        result["files"] += 1

    return result


def brand_guidelines_md(brand: Brand) -> str:
    light = brand.light_site
    ink = brand.palette["text"] if light else "#0b1220"
    desc = SYMBOL_LABELS.get(brand.slug, f"the **{brand.initials}** monogram in {brand.display_font}")
    return f"""# Brand Guidelines — {brand.name}

The complete identity kit for this product. Everything here is generated from
`frontend/design-tokens.json`, so the logo, the favicon, the PWA icons and the
social share image are all the same artwork in different sizes.

## Logo

| Asset | Path | Use |
|---|---|---|
| Vector mark (app icon) | `frontend/public/favicon.svg` | browser tab, bookmarks |
| Multi-resolution icon | `frontend/public/favicon.ico` | legacy favicon requests |
| PWA icons | `frontend/public/icons/icon-*.png` | installable app, splash screens |
| Maskable icon | `frontend/public/icons/icon-maskable-512x512.png` | Android adaptive icons |
| iOS icon | `frontend/public/apple-touch-icon.png` | iOS home screen |
| Share image | `frontend/public/og-image.png` / `.svg` | link previews |

In React, import the mark instead of inlining an image:

```jsx
import {{ BrandMark }} from './components/brand/BrandMark';
import BrandLockup from './components/brand/BrandLockup';

<BrandMark size={{40}} />
<BrandLockup size={{34}} />
```

Brand constants live in `frontend/src/components/brand/BRAND.js`
(`BRAND.name`, `BRAND.initials`, `BRAND.primary`, `BRAND.secondary`,
`BRAND.accent`). Changing a colour there and in `design-tokens.json` updates
every surface at once.

## Colour

| Role | Value |
|---|---|
| Primary | `{brand.palette['primary']}` |
| Secondary | `{brand.palette['secondary']}` |
| Accent | `{brand.palette['accent']}` |
| Surface | `{brand.palette['bg']}` |
| Text on surface | `{brand.palette['text']}` |

The mark is a gradient tile from primary to secondary carrying
{desc}. Ink flips to dark automatically when the gradient is pale, and the
knockout tone is derived from the gradient itself, so the mark stays legible on
any palette you choose. The wordmark beside it is set in
{brand.display_font}; the monogram **{brand.initials}** is kept in
`BRAND.initials` for favicons and anywhere a single pair of letters is needed.

## Typography

- Display: **{brand.display_font}**
- Sans / body: **{brand.sans_font}**

## Clear space and minimum size

Keep clear space equal to the monogram height on all sides. Never render the
mark below 16 px, and never recolour, rotate, outline or add effects to it —
use the maskable variant for adaptive-icon crops and let the browser handle
the rest.

## Live demo

{brand.live_base or "Set LIVE_URL.txt before publishing."}

The demo is served from a GitHub Pages **project subpath**, which is why every
asset path in `manifest.json` is relative. If you move the product to a custom
domain, update `LIVE_URL.txt`, `frontend/index.html` (canonical, hreflang,
og:*, twitter:*, JSON-LD), `frontend/public/robots.txt` and
`frontend/public/sitemap.xml` in one pass.
"""


def assert_unique_identities(products, log):
    """Every product must ship a gradient nobody else uses."""
    seen = {}
    clashes = []
    for slug in products:
        b = Brand(slug)
        key = (b.palette["primary"].lower(), b.palette["secondary"].lower(), b.gradient_angle)
        if key in seen:
            clashes.append(f"{slug} and {seen[key]} share {key}")
        seen[key] = slug
    if clashes:
        log("  ERROR: duplicate logo identities:")
        for c in clashes:
            log(f"    - {c}")
        return False
    log(f"  logo identities: {len(seen)}/{len(products)} unique gradients")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    slugs = args.only or PRODUCTS
    lines = []

    def log(msg):
        lines.append(msg)

    if not assert_unique_identities(slugs, log):
        print("\n".join(lines))
        return 1

    results = []
    for slug in slugs:
        res = process(slug, args.dry_run, log)
        if res:
            results.append(res)

    print("\n".join(lines))
    print()
    print(f"{'product':22} {'files':>6} {'rewrites':>9}")
    total = 0
    for r in results:
        total += r["files"]
        print(f"{r['slug']:22} {r['files']:>6} {r['urls']:>9}")
    print(f"{'TOTAL':22} {total:>6}")
    if args.dry_run:
        print("\n(dry run - nothing written)")


if __name__ == "__main__":
    main()