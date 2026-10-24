"""Design Forge — deterministic, brand-specific design systems for generated sites.

Every generated site used the same slate palette, the same font and the same
rounded-3xl cards, so all output looked like one template. This module derives a
complete visual system from the brand:

  * one of four archetypes (aurora / editorial / kinetic / precision) chosen by a
    stable hash of brand + industry,
  * a tinted neutral scale built from the brand hue (surfaces, borders, muted
    text) instead of Tailwind's fixed slate,
  * a two-font pairing (Google Fonts with system fallbacks),
  * a radius scale and accent glow,
  * ready-to-write `tailwind.config.js`, `index.html` font links and `index.css`.

The generated markup keeps its semantic slate classes; overriding the `slate`
and `white` color scales in Tailwind re-skins the whole site coherently, which is
why this works without rewriting every page.

Pure functions only — no filesystem, no network. Tested in
`tests/test_design_forge.py`.
"""
from __future__ import annotations

import colorsys
import hashlib
from typing import Any, Dict


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    value = str(hex_color).strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return (165.0, 35.0, 45.0)
    try:
        r, g, b = (int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return (165.0, 35.0, 45.0)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360.0, s * 100.0, l * 100.0)


def hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb(
        (hue % 360.0) / 360.0,
        _clamp(lightness, 0.0, 100.0) / 100.0,
        _clamp(saturation, 0.0, 100.0) / 100.0,
    )
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in (r, g, b))


def _hash_ratio(brand: str, industry: str) -> float:
    digest = hashlib.sha256(f"{brand}:{industry}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "aurora": {
        "hue": None,  # brand hue
        "surface_saturation": 18,
        "background_lightness": 4.6,
        "sans": "Plus Jakarta Sans",
        "display": "Plus Jakarta Sans",
        "google": "family=Plus+Jakarta+Sans:wght@400;500;600;700;800",
        "radius": {"lg": "0.75rem", "xl": "1rem", "2xl": "1.5rem", "3xl": "2rem"},
        "glow": True,
    },
    "editorial": {
        "hue": 28,
        "surface_saturation": 11,
        "background_lightness": 5.2,
        "sans": "Manrope",
        "display": "Fraunces",
        "google": "family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,700",
        "radius": {"lg": "0.375rem", "xl": "0.5rem", "2xl": "0.75rem", "3xl": "1rem"},
        "glow": False,
    },
    "kinetic": {
        "hue": 285,
        "surface_saturation": 20,
        "background_lightness": 4.8,
        "sans": "Space Grotesk",
        "display": "Space Grotesk",
        "google": "family=Space+Grotesk:wght@400;500;600;700",
        "radius": {"lg": "1rem", "xl": "1.25rem", "2xl": "1.75rem", "3xl": "2.25rem"},
        "glow": True,
    },
    "precision": {
        "hue": 210,
        "surface_saturation": 8,
        "background_lightness": 4.2,
        "sans": "IBM Plex Sans",
        "display": "Sora",
        "google": "family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@400;500;600;700",
        "radius": {"lg": "0.375rem", "xl": "0.5rem", "2xl": "0.625rem", "3xl": "0.75rem"},
        "glow": False,
    },
}

_INDUSTRY_HINT = {
    "fintech": "precision", "finance": "precision", "healthcare": "precision",
    "legal": "editorial", "real-estate": "editorial", "education": "editorial",
    "entertainment": "kinetic", "gaming": "kinetic", "travel": "kinetic",
}


def slate_scale(hue: float, saturation: float, background_lightness: float) -> Dict[str, str]:
    """Neutral ramp tinted toward the brand hue, clamped to readable contrasts."""
    steps = {
        950: background_lightness,
        900: background_lightness + 3.5,
        800: background_lightness + 8.5,
        700: background_lightness + 14.5,
        600: background_lightness + 22.0,
        500: 46.0,
        400: 63.0,
        300: 76.0,
        200: 86.0,
        100: 93.0,
        50: 97.0,
    }
    scale: Dict[str, str] = {}
    for step, lightness in steps.items():
        # Saturation fades out as surfaces get lighter, keeping text crisp.
        fade = 1.0 - (lightness / 130.0)
        scale[str(step)] = hsl_to_hex(hue, saturation * max(0.18, fade), lightness)
    return scale


def build_design(brand: str, industry: str, primary: str, accent: str) -> Dict[str, Any]:
    """Return the complete design system for one brand."""
    ratio = _hash_ratio(brand, industry)
    hinted = _INDUSTRY_HINT.get((industry or "").strip().lower())
    names = list(ARCHETYPES)
    archetype_name = hinted or names[int(ratio * len(names)) % len(names)]
    archetype = ARCHETYPES[archetype_name]

    primary_hue, primary_sat, _ = hex_to_hsl(primary)
    _, accent_sat, _ = hex_to_hsl(accent)
    hue = primary_hue if archetype["hue"] is None else (archetype["hue"] + (ratio - 0.5) * 24.0)
    surface_sat = float(archetype["surface_saturation"])
    # Strongly saturated brand colors are reserved for accents; surfaces stay calm.
    surface_sat = _clamp(surface_sat + primary_sat * 0.08, 6.0, 26.0)
    slate = slate_scale(hue, surface_sat, float(archetype["background_lightness"]))
    ink = hsl_to_hex(hue, _clamp(surface_sat * 0.9, 6.0, 20.0), 97.5)
    muted = slate["400"]

    design: Dict[str, Any] = {
        "archetype": archetype_name,
        "brand": brand,
        "industry": industry,
        "hue": round(hue, 1),
        "primary": primary,
        "accent": accent,
        "ink": ink,
        "muted": muted,
        "slate": slate,
        "fonts": {"sans": archetype["sans"], "display": archetype["display"]},
        "google_fonts": archetype["google"],
        "radius": dict(archetype["radius"]),
        "accent_saturation": round(accent_sat, 1),
        "glow": bool(archetype["glow"]),
    }
    design["tailwind_config"] = _tailwind_config(design)
    design["index_css"] = _index_css(design)
    design["html_attrs"] = f'class="dark" data-design="{archetype_name}"'
    return design


def _tailwind_config(design: Dict[str, Any]) -> str:
    slate = ",\n".join(f'          {step}: "{value}"' for step, value in design["slate"].items())
    radius = ",\n".join(f'        "{key}": "{value}"' for key, value in design["radius"].items())
    shadow = (
        f'        glow: "0 0 60px {design["accent"]}33",\n'
        if design["glow"] else ""
    )
    return f"""/** Generated design system — brand-derived, do not hand-edit per page. */
export default {{
  content: ["./index.html", "./src/**/*.{{js,ts,jsx,tsx}}"],
  darkMode: "class",
  theme: {{
    extend: {{
      colors: {{
        brand: {{
          primary: "{design['primary']}",
          accent: "{design['accent']}",
        }},
        slate: {{
{slate},
        }},
        white: "{design['ink']}",
      }},
      fontFamily: {{
        sans: ["{design['fonts']['sans']}", "system-ui", "sans-serif"],
        display: ["{design['fonts']['display']}", "{design['fonts']['sans']}", "serif"],
      }},
      borderRadius: {{
{radius},
      }},
      boxShadow: {{
{shadow}      }},
    }},
  }},
  plugins: [],
}};
"""


def _index_css(design: Dict[str, Any]) -> str:
    glow = (
        f"  background-image: radial-gradient(70% 50% at 50% 0%, {design['accent']}1f, transparent 70%);\n"
        if design["glow"] else ""
    )
    return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --brand-primary: {design['primary']};
  --brand-accent: {design['accent']};
  --ink: {design['ink']};
  --muted: {design['muted']};
}}

body {{
  font-family: "{design['fonts']['sans']}", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: {design['slate']['950']};
{glow}  background-attachment: fixed;
  color: {design['ink']};
}}

.font-display {{
  font-family: "{design['fonts']['display']}", "{design['fonts']['sans']}", Georgia, serif;
  letter-spacing: -0.02em;
}}

::selection {{
  background: {design['primary']};
  color: {design['ink']};
}}
"""


__all__ = ["ARCHETYPES", "build_design", "hex_to_hsl", "hsl_to_hex", "slate_scale"]
