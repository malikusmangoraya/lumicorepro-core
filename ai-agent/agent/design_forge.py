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
from copy import deepcopy
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

_COMPOSITIONS = {
    "aurora": {
        "hero": "split-asymmetric",
        "section_order": ["capabilities", "workflow", "principles"],
        "content_width": "80rem", "spacing": "generous", "surface": "layered",
        "motion": "interaction-only",
    },
    "editorial": {
        "hero": "divided-reading",
        "section_order": ["principles", "capabilities", "workflow"],
        "content_width": "72rem", "spacing": "reading", "surface": "divided",
        "motion": "interaction-only",
    },
    "kinetic": {
        "hero": "stacked-stepped",
        "section_order": ["workflow", "principles", "capabilities"],
        "content_width": "84rem", "spacing": "expansive", "surface": "offset",
        "motion": "interaction-only",
    },
    "precision": {
        "hero": "compact-columns",
        "section_order": ["workflow", "capabilities", "principles"],
        "content_width": "76rem", "spacing": "compact", "surface": "outlined",
        "motion": "interaction-only",
    },
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
        "composition": deepcopy(_COMPOSITIONS[archetype_name]),
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
    composition = design["composition"]
    rhythm = {"generous": "6rem", "reading": "5rem", "expansive": "7rem", "compact": "4rem"}
    # Pale actions with dark ink stay readable even for very dark owner colors.
    action = hsl_to_hex(design["hue"], 68, 80)
    return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --brand-primary: {design['primary']};
  --brand-accent: {design['accent']};
  --ink: {design['ink']};
  --muted: {design['muted']};
  --surface: {design['slate']['950']};
  --surface-raised: {design['slate']['900']};
  --surface-soft: {design['slate']['800']};
  --line: {design['slate']['700']};
  --control-line: {design['slate']['500']};
  --action: {action};
  --on-action: {design['slate']['950']};
  --danger: {hsl_to_hex(5, 85, 80)};
  --content-width: {composition['content_width']};
  --section-space: clamp(3.5rem, 7vw, {rhythm[composition['spacing']]});
  --panel-radius: {design['radius']['2xl']};
  --display-font: "{design['fonts']['display']}", Georgia, serif;
  --gutter: clamp(1.25rem, 4vw, 3rem);
  color-scheme: dark;
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
  background: var(--action);
  color: var(--on-action);
}}
""" + _PUBLIC_STYLES


_PUBLIC_STYLES = """
/* Shared public design system. Layout is mobile-first, not overflow-clipped. */
* { box-sizing: border-box; }
body { margin: 0; }
.site-shell { min-height: 100vh; display: flex; flex-direction: column; }
.site-shell > main { flex: 1; min-width: 0; }
.site-shell :where(h1, h2, h3, p, a, dd) { overflow-wrap: anywhere; }
.site-shell :where(a, button, input, textarea, summary):focus-visible {
  outline: 3px solid var(--action); outline-offset: 4px;
}
.public-container { width: 100%; max-width: var(--content-width); margin-inline: auto; padding-inline: var(--gutter); }
.public-page { padding-block: var(--section-space); }
.public-page h1, .public-page h2, .public-page h3 { font-family: var(--display-font); letter-spacing: -.035em; }
.public-page h1 { font-size: clamp(2.5rem, 5vw, 4.5rem); line-height: 1.08; }
.public-page h2 { font-size: clamp(1.7rem, 3vw, 2.6rem); line-height: 1.2; }
.public-page h3 { font-size: 1.3rem; line-height: 1.3; }
.public-page p { line-height: 1.75; }
.eyebrow { color: var(--action); font-size: .75rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.page-intro { max-width: 46rem; margin-bottom: 3rem; }
.page-intro h1 { margin-block: 1rem 1.5rem; }
.page-intro > p:last-child, .hero-description { color: var(--muted); font-size: 1.075rem; max-width: 38rem; }
.hero-brand { margin-block: 1.25rem; }
.hero-statement { font-size: clamp(1.35rem, 2.5vw, 2rem); line-height: 1.35 !important; max-width: 30ch; }
.hero-description { margin-top: 1.25rem; }
.action-row { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 2rem; }
.public-button { min-height: 2.75rem; display: inline-flex; align-items: center; justify-content: center;
  gap: .65rem; padding: .8rem 1.2rem; border: 1px solid transparent; border-radius: var(--panel-radius);
  background: var(--action); color: var(--on-action); font-weight: 700; font-size: .875rem;
  text-decoration: none; cursor: pointer; transition: transform .2s, background-color .2s; }
.public-button:hover { transform: translateY(-2px); }
.public-button.secondary { background: var(--surface-raised); border-color: var(--control-line); color: var(--ink); }
.public-button:disabled { cursor: wait; opacity: .65; transform: none; }
.text-link { color: var(--action); text-decoration: underline; text-underline-offset: .25em; }
.skip-link { position: fixed; inset-inline-start: 1rem; top: -8rem; z-index: 100; padding: 1rem;
  background: var(--action); color: var(--on-action); border-radius: .5rem; }
.skip-link:focus { top: 1rem; }
.public-header { border-bottom: 1px solid var(--line); background: var(--surface); }
.nav-row { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem;
  flex-wrap: wrap; min-height: 5rem; padding-block: 1rem; }
.brand-link { display: inline-flex; gap: .7rem; align-items: center; min-width: 0; max-width: calc(100% - 7rem);
  font-weight: 800; font-size: 1.1rem; line-height: 1.25; text-decoration: none; }
.brand-mark { width: 2rem; height: 2rem; flex-shrink: 0; color: var(--action); }
.menu-toggle { min-height: 2.75rem; padding: .6rem .9rem; border: 1px solid var(--control-line);
  border-radius: .5rem; background: var(--surface-raised); color: var(--ink); }
.public-navigation { display: none; width: 100%; }
.public-navigation.is-open { display: flex; flex-direction: column; gap: .75rem; }
.nav-links, .nav-actions { display: flex; flex-direction: column; gap: .4rem; }
.nav-links a, .nav-signin { min-height: 2.75rem; padding: .65rem .5rem; color: var(--muted); font-size: .875rem; }
.nav-links a:hover, .nav-signin:hover, .nav-links a[aria-current="page"] { color: var(--ink); }
.nav-links a[aria-current="page"] { text-decoration: underline; text-underline-offset: .45rem; }
.hero-split, .hero-editorial, .hero-precision { display: grid; gap: 3rem; align-items: center; }
.hero-art { margin: 0; padding: 1.5rem; border: 1px solid var(--line); border-radius: var(--panel-radius); background: var(--surface-raised); }
.hero-art img { display: block; width: 100%; height: auto; }
.hero-art figcaption { color: var(--muted); line-height: 1.6; font-size: .85rem; margin-top: 1rem; }
.hero-editorial { align-items: start; border-top: 1px solid var(--control-line); padding-top: 2rem; }
.editorial-note { border-inline-start: 1px solid var(--control-line); padding-inline-start: 1.5rem; }
.editorial-note p { color: var(--muted); margin-block: 1rem; }
.hero-kinetic .hero-brand { font-size: clamp(3.25rem, 9vw, 8rem); letter-spacing: -.06em; }
.kinetic-strip { list-style: none; display: grid; gap: .75rem; margin-top: 3rem; padding: 0; }
.kinetic-strip li { padding: 1.25rem; border: 1px solid var(--line); border-radius: var(--panel-radius); background: var(--surface-raised); }
.kinetic-strip span { color: var(--action); margin-inline-end: 1rem; font-size: .8rem; }
.precision-details { border: 1px solid var(--control-line); border-radius: var(--panel-radius); padding: .5rem 1.5rem; }
.precision-details > div { padding-block: 1.25rem; }
.precision-details > div + div { border-top: 1px solid var(--line); }
.precision-details dt { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.precision-details dd { margin: .5rem 0 0; }
.public-section { margin-top: var(--section-space); }
.section-heading { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 2rem; }
.section-heading p { max-width: 32rem; color: var(--muted); }
.capability-grid, .capability-asymmetric, .capability-alternating, .choice-grid { display: grid; gap: 1rem; }
.capability-card, .choice-card { padding: clamp(1.5rem, 3vw, 2.5rem); border: 1px solid var(--line);
  border-radius: var(--panel-radius); background: var(--surface-raised); }
.capability-card p, .choice-card p { color: var(--muted); margin-block: 1rem; }
.capability-card .eyebrow { color: var(--action); margin-top: 0; }
.capability-divided { border-top: 1px solid var(--control-line); }
.capability-divided .capability-card { border: 0; border-bottom: 1px solid var(--line); border-radius: 0;
  background: transparent; padding-inline: 0; }
.workflow-list { list-style: none; padding: 0; display: grid; gap: 1rem; }
.workflow-list li { display: flex; gap: 1.25rem; padding-block: 1.5rem; border-top: 1px solid var(--line); }
.workflow-number { color: var(--action); font-variant-numeric: tabular-nums; font-size: .8rem; padding-top: .2rem; }
.workflow-list p { color: var(--muted); margin-top: .75rem; }
.principles-reading { max-width: 46rem; border-inline-start: 2px solid var(--action); padding-inline-start: 1.5rem; }
.principles-reading p { color: var(--muted); margin-block: 1.5rem; }
.closing-note { display: flex; flex-direction: column; gap: 1.5rem; padding-block: 2rem;
  margin-top: var(--section-space); border-block: 1px solid var(--line); }
.closing-note p { color: var(--muted); margin-top: .75rem; }
.closing-note .action-row { margin: 0; }
.public-faq { max-width: 48rem; margin-top: 3rem; }
.public-faq details { padding-block: 1.5rem; border-bottom: 1px solid var(--line); }
.public-faq summary { cursor: pointer; min-height: 2.75rem; font-weight: 600; }
.public-faq p { color: var(--muted); margin-top: .75rem; }
.contact-grid { display: grid; gap: 3rem; align-items: start; }
.contact-form, .contact-result { padding: clamp(1.25rem, 4vw, 2.5rem); border-radius: var(--panel-radius);
  background: var(--surface-raised); border: 1px solid var(--line); }
.contact-field + .contact-field { margin-top: 1.5rem; }
.contact-field label { display: block; margin-bottom: .5rem; font-size: .875rem; }
.contact-field input, .contact-field textarea { display: block; width: 100%; padding: .85rem 1rem;
  border: 1px solid var(--control-line); border-radius: .5rem; background: var(--surface); color: var(--ink); }
.contact-field textarea { resize: vertical; }
.contact-field [aria-invalid="true"] { border-color: var(--danger); }
.field-error, .form-error { color: var(--danger); font-size: .875rem; margin-top: .5rem; }
.contact-form > .public-button { margin-top: 1.5rem; width: 100%; }
.form-note { color: var(--muted); font-size: .8rem; margin-top: 1rem; }
.contact-result p { color: var(--muted); margin-block: 1rem; }
.public-footer { border-top: 1px solid var(--line); padding-block: 3rem 2rem; }
.footer-grid { display: grid; gap: 2.5rem; }
.footer-grid p { max-width: 28rem; color: var(--muted); line-height: 1.75; margin-top: 1rem; }
.footer-grid h2 { font-size: .75rem; text-transform: uppercase; letter-spacing: .12em; margin-bottom: 1rem; }
.footer-grid ul { list-style: none; padding: 0; }
.footer-grid li a { display: inline-block; min-height: 2.75rem; padding-block: .6rem; color: var(--muted); }
.footer-grid li a:hover { color: var(--ink); }
.footer-bottom { margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .75rem; }
.route-loading { padding: 4rem var(--gutter); color: var(--muted); }
.scene-slot { margin-top: 3rem; }
@media (min-width: 48rem) {
  .hero-split { grid-template-columns: 1.1fr 1fr; gap: 2rem; }
  .hero-editorial { grid-template-columns: 1.7fr 1fr; }
  .hero-precision { grid-template-columns: 1.4fr 1fr; }
  .capability-grid, .choice-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .capability-asymmetric { grid-template-columns: 1.35fr 1fr; }
  .capability-asymmetric .capability-card:first-child { grid-row: span 2; display: flex; flex-direction: column; justify-content: center; }
  .capability-divided .capability-card { display: grid; grid-template-columns: 1fr 1.4fr; column-gap: 2rem; }
  .capability-divided .eyebrow { grid-column: 1 / -1; }
  .capability-divided .capability-card p { margin-top: 0; }
  .capability-alternating .capability-card { max-width: 85%; }
  .capability-alternating .capability-card:nth-child(even) { margin-inline-start: 15%; }
  .kinetic-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); padding-bottom: 2rem; }
  .kinetic-strip li:nth-child(2) { transform: translateY(1rem); }
  .kinetic-strip li:nth-child(3) { transform: translateY(2rem); }
  .workflow-stepped li:nth-child(2) { margin-inline-start: 8%; }
  .workflow-stepped li:nth-child(3) { margin-inline-start: 16%; }
  .contact-grid { grid-template-columns: 1fr 1.1fr; }
  .footer-grid { grid-template-columns: 2fr 1fr 1fr; }
}
@media (min-width: 64rem) {
  .menu-toggle { display: none; }
  .nav-row { flex-wrap: nowrap; gap: 2rem; }
  .brand-link { max-width: 16rem; }
  .public-navigation, .public-navigation.is-open { display: flex; flex-direction: row; align-items: center; justify-content: flex-end; gap: 1.5rem; width: auto; }
  .nav-links, .nav-actions { flex-direction: row; align-items: center; gap: .5rem; }
  .hero-split { gap: 4rem; }
  .hero-editorial { gap: 5rem; }
  .hero-split .hero-art { margin-top: 4rem; }
  .section-heading, .closing-note { flex-direction: row; align-items: center; justify-content: space-between; }
  .section-heading h2 { max-width: 25rem; }
  .closing-note .action-row { flex-shrink: 0; }
}
@media (min-width: 90rem) {
  .hero-split { grid-template-columns: 1.15fr 1fr; }
  .hero-precision { gap: 5rem; }
  .public-navigation, .public-navigation.is-open { gap: 2.5rem; }
}
@media (min-width: 120rem) {
  .public-page { padding-top: calc(var(--section-space) + 1rem); }
}
@media (prefers-reduced-motion: reduce) {
  .site-shell *, .site-shell *::before, .site-shell *::after {
    animation: none !important; transition: none !important; scroll-behavior: auto !important;
  }
  .public-button:hover { transform: none; }
}
"""


__all__ = ["ARCHETYPES", "build_design", "hex_to_hsl", "hsl_to_hex", "slate_scale"]
