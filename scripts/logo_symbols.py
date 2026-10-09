#!/usr/bin/env python3
"""Designed logo symbols for the ten products.

The mark used to be a monogram letter in a gradient tile, which reads as a
default avatar rather than an identity. Each product now has a purpose-built
geometric symbol drawn from its own industry, so the favicon, the PWA icon and
the navbar mark are a real logo.

Every symbol is a list of primitives so the SAME geometry renders as SVG (for
the browser and for Canva import) and as PNG (for installable icons and share
images) with no second source of truth.

Primitives
    ("poly", [(x, y), ...])          filled polygon
    ("ring", cx, cy, r, width)      stroked circle
    ("line", x1, y1, x2, y2, w)     stroked line
    ("ell",  cx, cy, rx, ry, w)     stroked ellipse
    ("knock", <primitive>)          same shape drawn in the knockout colour

A "knock" wrapper matters whenever a smaller shape sits inside a larger filled
one: drawn in the same colour it would simply vanish. The knockout colour is a
deeper tone of the tile gradient, so it reads on both light and dark tiles.
Coordinates are in a 64x64 box; the renderer scales.
"""

from __future__ import annotations


def _hex_spiral(cx, cy, r, n, start=0.0, step=60.0):
    """Polygon approximation of a circular arc, n points."""
    import math
    return [(cx + r * math.cos(math.radians(start + i * step / (n - 1))),
             cy + r * math.sin(math.radians(start + i * step / (n - 1))))
            for i in range(n)]


SYMBOLS = {
    # Precision commerce - modern summit: layered peak, inner facet, summit orb + base rail.
    "apex": [
        ("poly", [(32, 8), (53, 50), (11, 50)]),
        ("knock", ("poly", [(32, 26), (41, 45), (23, 45)])),
        ("poly", [(32, 8), (36, 16), (28, 16)]),
        ("line", 14, 54, 50, 54, 3.5),
    ],
    # Luxury real estate - modern portal: arch, inner door, keystone, stepped base.
    "aurelia-estates": [
        ("poly", [(16, 54), (16, 32), (23, 20), (32, 14), (41, 20), (48, 32), (48, 54)]),
        ("knock", ("poly", [(27, 54), (27, 36), (32, 29), (37, 36), (37, 54)])),
        ("poly", [(29, 14), (35, 14), (33, 22), (31, 22)]),
        ("line", 20, 54, 44, 54, 2.5),
    ],
    # Performance gym - modern power: bar, dual plates, knurled core ring + end caps.
    "aurum-fitness": [
        ("line", 12, 32, 52, 32, 7),
        ("poly", [(10, 19), (21, 19), (21, 45), (10, 45)]),
        ("poly", [(43, 19), (54, 19), (54, 45), (43, 45)]),
        ("knock", ("ring", 32, 32, 6, 3)),
        ("poly", [(29, 29), (35, 29), (35, 35), (29, 35)]),
    ],
    # Insurance claims - modern aegis: double shield, resolved check, crown notch.
    "claimflow-ai": [
        ("poly", [(32, 7), (53, 16), (53, 33), (32, 57), (11, 33), (11, 16)]),
        ("knock", ("poly", [(32, 13), (47, 20), (47, 32), (32, 50), (17, 32), (17, 20)])),
        ("poly", [(23, 31), (29, 37), (42, 23), (45, 26), (29, 43), (20, 34)]),
        ("poly", [(29, 7), (35, 7), (33, 12), (31, 12)]),
    ],
    # Private capital - modern meridian: globe, ellipse, equator, pole-star + core.
    "meridian-capital": [
        ("ring", 32, 32, 21, 4),
        ("ell", 32, 32, 9, 21, 3.5),
        ("line", 11, 32, 53, 32, 3.5),
        ("poly", [(32, 5), (35, 11), (29, 11)]),
        ("poly", [(29, 29), (35, 29), (35, 35), (29, 35)]),
    ],
    # Event production - modern celebration: cloud base, burst star, spark satellites.
    "nuage-events": [
        ("ring", 26, 37, 13, 4),
        ("ring", 41, 40, 9, 4),
        ("line", 16, 50, 48, 50, 3.5),
        ("poly", [(45, 8), (48, 19), (59, 22), (48, 25), (45, 36), (42, 25), (31, 22), (42, 19)]),
        ("poly", [(16, 12), (18, 17), (23, 19), (18, 21), (16, 26), (14, 21), (9, 19), (14, 17)]),
    ],
    # Creative studio - modern aperture: ring, triangular blades, hex core + focus.
    "prestige-studio": [
        ("ring", 32, 32, 22, 4),
        ("poly", [(32, 16), (46, 41), (18, 41)]),
        ("knock", ("poly", [(32, 25), (40, 38), (24, 38)])),
        ("poly", [(29, 29), (35, 29), (35, 35), (29, 35)]),
        ("line", 32, 10, 32, 16, 3),
    ],
    # Resume builder - modern ascent: folded doc, scored lines, growth arrow + seal.
    "resupro": [
        ("poly", [(18, 6), (38, 6), (46, 15), (46, 58), (18, 58)]),
        ("knock", ("poly", [(38, 6), (46, 15), (38, 15)])),
        ("knock", ("line", 24, 28, 38, 28, 3)),
        ("knock", ("line", 24, 37, 38, 37, 3)),
        ("poly", [(24, 44), (36, 44), (33, 40), (33, 48), (31, 46)]),
        ("poly", [(38, 48), (42, 48), (42, 52), (38, 52)]),
    ],
    # Curated travel - modern compass: outer ring, cardinal ticks, needle + pivot.
    "saffron-voyage": [
        ("ring", 32, 32, 22, 4),
        ("line", 32, 6, 32, 12, 3),
        ("line", 32, 52, 32, 58, 3),
        ("line", 6, 32, 12, 32, 3),
        ("line", 52, 32, 58, 32, 3),
        ("poly", [(32, 12), (40, 32), (32, 52), (24, 32)]),
        ("knock", ("poly", [(32, 12), (40, 32), (32, 32)])),
        ("poly", [(29, 29), (35, 29), (35, 35), (29, 35)]),
    ],
    # Photography - modern optic: dual lens, crosshair, blade tick + flare.
    "studio-lumen": [
        ("ring", 32, 32, 22, 4),
        ("ring", 32, 32, 11, 3.5),
        ("line", 32, 8, 32, 18, 2.5),
        ("line", 32, 46, 32, 56, 2.5),
        ("line", 8, 32, 18, 32, 2.5),
        ("line", 46, 32, 56, 32, 2.5),
        ("poly", [(29, 29), (35, 29), (35, 35), (29, 35)]),
        ("poly", [(44, 12), (47, 12), (47, 15), (44, 15)]),
    ],
    # SaaS operations - an orbital flow: orbit ring, flow band, launch chevron + satellite.
    "flowpilot": [
        ("ring", 32, 33, 22, 4),
        ("ell", 32, 33, 22, 9, 3),
        ("poly", [(24, 24), (40, 33), (24, 42)]),
        ("knock", ("poly", [(29, 29), (35, 33), (29, 37)])),
        ("poly", [(48, 8), (51, 11), (48, 14), (45, 11)]),
    ],
}

SYMBOL_LABELS = {
    "apex": "A layered summit peak with summit orb and base rail",
    "aurelia-estates": "A modern portal arch with keystone and stepped base",
    "aurum-fitness": "A power barbell with plated ends and core grip ring",
    "claimflow-ai": "A double aegis shield with resolved check and crown notch",
    "meridian-capital": "A meridian globe with equator, pole-star and core",
    "nuage-events": "A celebration cloud with burst star and spark satellites",
    "prestige-studio": "A precision aperture with triangular blades and hex core",
    "resupro": "An ascent document with fold, scores, growth arrow and seal",
    "saffron-voyage": "A cardinal compass with ring, ticks, needle and pivot",
    "studio-lumen": "A dual optic lens with crosshair, ticks and flare",
    "flowpilot": "An orbital flow with launch chevron",
}


def _fmt_pts(pts, prec=2):
    return " ".join(f"{round(x, prec)},{round(y, prec)}" for x, y in pts)


def symbol_to_svg(slug: str, color: str, knock: str = None, opacity: float = 1.0) -> str:
    """Render a symbol as SVG child elements (fills/strokes use `color`)."""
    out = []
    op = "" if opacity >= 1 else f' opacity="{opacity}"'
    for prim in SYMBOLS[slug]:
        col = color
        if prim[0] == "knock":
            if not knock:
                continue
            prim, col = prim[1], knock
        kind = prim[0]
        if kind == "poly":
            pts = prim[1]
            out.append(f'<polygon points="{_fmt_pts(pts)}" fill="{col}"{op}/>')
        elif kind == "line":
            _, x1, y1, x2, y2, w = prim
            out.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{col}" stroke-width="{w}" stroke-linecap="round"{op}/>')
        elif kind == "ring":
            _, cx, cy, r, w = prim
            out.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{col}" stroke-width="{w}"{op}/>')
        elif kind == "ell":
            _, cx, cy, rx, ry, w = prim
            out.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" '
                f'stroke="{col}" stroke-width="{w}"{op}/>')
    return "".join(out)


def draw_symbol(draw, slug: str, box, color, knock=None, scale: float = 1.0, offset=(0.0, 0.0)):
    """Draw a symbol with PIL into `box` (an l,t,r,b tuple)."""
    l, t, r, b = box
    side = min(r - l, b - t)
    # centre the 64x64 design box inside the tile and scale it to the tile
    k = side / 64.0 * scale
    ox = l + (r - l - 64 * k) / 2 + offset[0]
    oy = t + (b - t - 64 * k) / 2 + offset[1]

    def P(x, y):
        return (ox + x * k, oy + y * k)

    for prim in SYMBOLS[slug]:
        col = color
        if prim[0] == "knock":
            if knock is None:
                continue
            prim, col = prim[1], knock
        kind = prim[0]
        if kind == "poly":
            draw.polygon([P(x, y) for x, y in prim[1]], fill=col)
        elif kind == "line":
            _, x1, y1, x2, y2, w = prim
            draw.line([P(x1, y1), P(x2, y2)], fill=col, width=max(1, int(round(w * k))))
            r_ = w * k / 2.0
            for (px, py) in (P(x1, y1), P(x2, y2)):
                draw.ellipse([px - r_, py - r_, px + r_, py + r_], fill=col)
        elif kind == "ring":
            _, cx, cy, r_, w = prim
            px, py = P(cx, cy)
            rr = r_ * k
            draw.ellipse([px - rr, py - rr, px + rr, py + rr],
                         outline=col, width=max(1, int(round(w * k))))
        elif kind == "ell":
            _, cx, cy, rx, ry, w = prim
            px, py = P(cx, cy)
            draw.ellipse([px - rx * k, py - ry * k, px + rx * k, py + ry * k],
                         outline=col, width=max(1, int(round(w * k))))
