"""Screenshot-to-Code Engine — LumicorePro Agent.

Turns screenshots/mockups into a design specification that the generation
pipeline can consume *and* into real React section components.

Pipeline position: this runs **before** the Design Planner, and its output is
one of the planner's inputs, so a screenshot decides structure and tokens before
a single file is written.

    screenshots -> VisionPipeline (per shot)
               -> merge_shots      (multi-shot: hero + sections + mobile)
               -> derive tokens    (contrast-guarded)
               -> to_plan_inputs   (feeds design_planner.create_design_plan)
               -> emit_section_jsx (optional real JSX)

Input:  local image path (PNG/JPG/WEBP/AVIF/GIF), URL, or data URI — one or many
Output: design spec dict + design-plan inputs + optional JSX

The reported status always distinguishes a genuine vision read from a heuristic
fallback or an unreadable image, so downstream phases never mistake an inferred
brief for measured design data.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REGION_ALIASES = {
    "nav": "navbar",
    "navigation": "navbar",
    "header": "navbar",
    "hero": "hero",
    "banner": "hero",
    "feature": "features",
    "features": "features",
    "pricing": "pricing",
    "testimonial": "testimonial",
    "cta": "cta",
    "footer": "footer",
    "gallery": "gallery",
    "products": "products",
}


_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif"}
_IMAGE_MAGIC = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"BM",
)


def _magic_ok(head: bytes, suffix: str) -> bool:
    """Verify the file signature, allowing container formats whose marker is
    not at offset 0 (RIFF/WEBP, ISO-BMFF/AVIF)."""
    if any(head.startswith(sig) for sig in _IMAGE_MAGIC):
        return True
    if suffix == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if suffix == ".avif":
        return head[4:8] == b"ftyp" and b"avif" in head[:16]
    return False


def _has_image_magic(head: bytes, suffix: str) -> bool:
    if suffix == ".webp":
        return head.startswith(b"RIFF") and head[8:12] == b"WEBP"
    if suffix == ".avif":
        return head[4:8] == b"ftyp" and head[8:12] in (b"avif", b"avis")
    return any(head.startswith(sig) for sig in _IMAGE_MAGIC)


def _local_image_ok(image_source: str) -> Optional[str]:
    """Return an error reason when a local source is clearly not an image.

    ``VisionPipeline._load_image`` labels any readable file as ``image/png``,
    which would let a text/HTML file masquerade as an analysed screenshot.
    """
    from pathlib import Path as _Path

    source = image_source.strip()
    if source.startswith(("data:", "http://", "https://")):
        return None

    path = _Path(source)
    if not path.is_file():
        return "image_unreadable"

    if path.suffix.lower() not in _IMAGE_EXTS:
        return f"unsupported_image_type:{path.suffix.lower() or 'none'}"

    try:
        with path.open("rb") as handle:
            head = handle.read(12)
    except OSError as exc:
        return f"image_unreadable:{exc.strerror or 'io_error'}"

    if not _has_image_magic(head, path.suffix.lower()):
        return "image_content_not_an_image"
    return None


def _load_vision(provider: Optional[Any] = None):
    from agent.vision_pipeline import LayoutMapper, VisionPipeline

    return VisionPipeline(provider=provider), LayoutMapper()


def screenshot_to_design_spec(
    image_source: str,
    business_type: str = "",
    provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """Analyze a screenshot and return a structured, codegen-ready design spec."""
    if not image_source:
        return {
            "source": image_source,
            "status": "failed",
            "reason": "no image source supplied",
        }

    type_error = _local_image_ok(image_source)
    if type_error:
        return {
            "source": image_source,
            "status": "failed",
            "reason": type_error,
        }

    try:
        vision, mapper = _load_vision(provider)
    except Exception as exc:  # pragma: no cover - import guard
        return {
            "source": image_source,
            "status": "failed",
            "reason": f"vision pipeline unavailable: {exc}",
        }

    layout = vision.extract_layout(image_source)

    if not layout or layout.get("reason") == "image_unreadable":
        return {
            "source": image_source,
            "status": "failed",
            "reason": (layout or {}).get("reason", "image_unreadable"),
        }

    overlays = {}
    try:
        overlays = vision.to_spec_overlays(layout) or {}
    except Exception:
        overlays = {}

    regions = ((layout.get("layout") or {}).get("regions") or [])
    sections: List[str] = []
    for region in regions:
        key = str(region).strip().lower()
        mapped = _REGION_ALIASES.get(key, key)
        if mapped and mapped not in sections:
            sections.append(mapped)

    try:
        mapped_regions = mapper.map_regions(layout) or []
    except Exception:
        mapped_regions = []

    components: List[str] = []
    for entry in mapped_regions:
        if isinstance(entry, dict):
            name = entry.get("component") or entry.get("name")
            if name and name not in components:
                components.append(name)

    tokens = layout.get("design_tokens") or {}
    typography = layout.get("typography") or {}
    parsed = bool(layout.get("parsed"))

    vision_hint = str(layout.get("raw_vision_hint") or "").strip()
    colors_measured = bool(parsed or vision_hint)
    if not colors_measured:
        tokens = {}
        layout = {**layout, "design_tokens": {}}

    return {
        "source": image_source,
        "status": "analyzed" if parsed else "heuristic_fallback",
        "analyzed": parsed,
        "colors_measured": colors_measured,
        "business_type": business_type,
        "layout": "single_page",
        "sections": sections,
        "components": components,
        "colors": dict(tokens) or dict(layout.get("colors") or {}),
        "typography": {
            "heading": typography.get("headings", "Sans-serif"),
            "body": typography.get("body", "Sans-serif"),
        },
        "spacing": layout.get("spacing") or {},
        "design_tokens": tokens,
        "overlays": overlays,
        "element_hierarchy": layout.get("element_hierarchy") or [],
        "vision_source": layout.get("source"),
        "note": None if colors_measured else (
            "No vision provider produced a readable parse, so no colours could be "
            "measured from this image. Structure below is a deterministic heuristic "
            "fallback and colour must come from the resolved brand palette."
        ),
    }


def analyze_screenshot(image_path: str, provider: Optional[Any] = None) -> Dict[str, Any]:
    """Backwards-compatible alias for :func:`screenshot_to_design_spec`."""
    return screenshot_to_design_spec(image_path, provider=provider)


# ═══════════════════════════════════════════════════════════════════════════
# Multi-shot analysis
# ═══════════════════════════════════════════════════════════════════════════

#: Common naming for the shots a designer actually uploads. Anything else is
#: merged in the order it was given.
SHOT_ROLES = ("hero", "sections", "mobile", "footer", "full")

_ROLE_HINTS = {
    "hero": "hero, navigation, call to action",
    "sections": "features, product grid, pricing, testimonials, faq",
    "mobile": "mobile layout, stacked sections, hamburger menu",
    "footer": "footer, newsletter, legal links",
    "full": "entire page, every section in order",
}


def _shot_role(source: str, index: int) -> str:
    """Infer what a shot is *for* from its filename, else fall back to order."""
    name = str(source or "").lower()
    for role in SHOT_ROLES:
        if re.search(rf"(^|[^a-z]){role}([^a-z]|$)", name):
            return role
    return SHOT_ROLES[0] if index == 0 else ("full" if index else "hero")


def _shot_parsed(shot: Dict[str, Any]) -> bool:
    """True when a vision provider actually parsed the shot.

    Accepts either the explicit ``analyzed`` flag or the ``analyzed`` status
    string, so a spec from either producer is treated the same way.
    """
    if "analyzed" in shot:
        return bool(shot.get("analyzed"))
    return str(shot.get("status") or "") == "analyzed"


def _shot_role_rank(role: Any) -> int:
    name = str(role or "full")
    return SHOT_ROLES.index(name) if name in SHOT_ROLES else len(SHOT_ROLES)


def merge_shots(specs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge per-shot specs into one design spec.

    Only shots that a vision provider actually parsed may contribute colours —
    a heuristic shot contributes structure only. Section order comes from the
    first parsed shot, so a single full-page capture wins over a crop.
    """
    usable = [s for s in specs if isinstance(s, dict) and s.get("status") != "failed"]
    merged: Dict[str, Any] = {
        "status": "failed" if not usable else "analyzed",
        "shot_count": len(usable),
        "shots": [
            {
                "source": s.get("source"),
                "role": s.get("role"),
                "status": s.get("status"),
                "analyzed": _shot_parsed(s),
                "colors_measured": s.get("colors_measured"),
            }
            for s in usable
        ],
        "failed_shots": [
            {"source": s.get("source"), "reason": s.get("reason")}
            for s in specs if isinstance(s, dict) and s.get("status") == "failed"
        ],
        "sections": [],
        "components": [],
        "colors": {},
        "typography": {},
        "spacing": {},
        "design_tokens": {},
    }
    if not usable:
        merged["reason"] = "no readable screenshot"
        return merged

    any_parsed = any(_shot_parsed(s) for s in usable)
    merged["analyzed"] = any_parsed
    merged["colors_measured"] = any(s.get("colors_measured") for s in usable)

    # Section order: prefer a parsed shot, else first usable shot.
    ordered = sorted(
        usable,
        key=lambda s: (0 if _shot_parsed(s) else 1, _shot_role_rank(s.get("role"))),
    )
    for shot in ordered:
        for section in shot.get("sections") or []:
            if section not in merged["sections"]:
                merged["sections"].append(section)
    for shot in usable:
        for component in shot.get("components") or []:
            if component not in merged["components"]:
                merged["components"].append(component)

    if merged["colors_measured"]:
        for shot in usable:
            if not shot.get("colors_measured"):
                continue
            for key, value in (shot.get("colors") or {}).items():
                if key not in merged["colors"] and isinstance(value, str) and value.strip():
                    merged["colors"][key] = value.strip()
            merged["design_tokens"].update(
                {k: v for k, v in (shot.get("design_tokens") or {}).items()
                 if k not in merged["design_tokens"]}
            )
            merged["spacing"].update(shot.get("spacing") or {})
            merged["typography"].update(shot.get("typography") or {})

    merged["layout"] = "single_page" if any(
        (s.get("role") or "") != "mobile" for s in usable
    ) else "single_page_mobile_first"
    merged["note"] = None if merged["colors_measured"] else (
        "No vision provider produced a readable parse, so no colours were measured. "
        "Structure is a deterministic heuristic; colour must come from the resolved "
        "brand palette."
    )
    return merged


def screenshot_to_design_spec_multi(
    sources: Sequence[str],
    business_type: str = "",
    provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """Analyze one or many screenshots and return a single merged design spec."""
    items = [s for s in (sources or []) if str(s or "").strip()]
    if not items:
        return {"status": "failed", "reason": "no image source supplied", "shot_count": 0}

    vision, mapper = _load_vision(provider)
    specs: List[Dict[str, Any]] = []
    for index, source in enumerate(items):
        spec = screenshot_to_design_spec(
            source, business_type=business_type, provider=provider
        )
        spec["role"] = _shot_role(source, index)
        specs.append(spec)

    merged = merge_shots(specs)
    merged["business_type"] = business_type
    if merged.get("status") != "failed":
        mapped: List[str] = []
        for region in merged.get("sections") or []:
            hints = LayoutMapper.REGION_HINTS.get(str(region).lower(), [])
            component = mapper._find_component(hints) if hints else ""
            if component and component not in mapped:
                mapped.append(component)
        merged["components"] = mapped or merged.get("components") or []
    return merged


# ═══════════════════════════════════════════════════════════════════════════
# Design-token derivation — measured colour, guaranteed readable
# ═══════════════════════════════════════════════════════════════════════════

_COLOR_ALIASES = {
    "background": "bg",
    "bg": "bg",
    "surface": "surface",
    "card": "surface",
    "text": "text",
    "text_muted": "text_dim",
    "muted": "text_dim",
    "border": "border",
    "primary": "primary",
    "secondary": "secondary",
    "accent": "accent",
}

_TOKEN_COLOR_KEYS = (
    "primary", "primary_light", "primary_dark", "accent", "bg", "surface",
    "surface_2", "border", "text", "text_dim", "success", "warning", "danger",
)

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _is_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX_RE.match(value.strip()))


def _shift(hex_color: str, amount: float) -> str:
    """Lighten (amount > 0) or darken (amount < 0) a hex colour in sRGB."""
    raw = hex_color.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return hex_color
    try:
        parts = [int(raw[i:i + 2], 16) for i in (0, 2, 4)]
    except ValueError:
        return hex_color
    shifted = [max(0, min(255, int(round(ch + amount * 255)))) for ch in parts]
    return "#" + "".join(f"{ch:02x}" for ch in shifted)


def derive_design_tokens(
    colors: Dict[str, str],
    spacing: Optional[Dict[str, Any]] = None,
    typography: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Turn measured colours into a complete, readable token set.

    A screenshot shows *some* colours; a design system needs *all* of them. This
    derives the missing steps (primary_light/dark, surface_2, on_primary,
    status colours) from what was measured, then runs the same WCAG audit the
    planner uses so an unreadable pairing is corrected rather than shipped.
    """
    from agent.intelligence.design_planner import build_design_system

    normalized: Dict[str, str] = {}
    for key, value in (colors or {}).items():
        name = _COLOR_ALIASES.get(str(key).strip().lower(), str(key).strip().lower())
        if _is_hex(value):
            normalized[name] = value.strip()

    tokens: Dict[str, Any] = dict(normalized)
    primary = normalized.get("primary") or normalized.get("accent")
    if primary:
        tokens.setdefault("primary", primary)
        tokens["primary_light"] = _shift(primary, 0.18)
        tokens["primary_dark"] = _shift(primary, -0.18)

    bg = normalized.get("bg")
    if bg:
        surface = normalized.get("surface")
        tokens["surface"] = surface or _shift(bg, 0.04 if _is_dark(bg) else -0.04)
        tokens["surface_2"] = _shift(tokens["surface"], 0.04 if _is_dark(bg) else -0.04)

    spacing_map = spacing if isinstance(spacing, dict) else {}
    gap = spacing_map.get("section_gap_px")
    if isinstance(gap, (int, float)) and 16 <= float(gap) <= 240:
        tokens["section_gap_px"] = int(gap)
    pad = spacing_map.get("card_padding_px")
    if isinstance(pad, (int, float)) and 4 <= float(pad) <= 96:
        tokens["card_padding_px"] = int(pad)

    type_map = typography if isinstance(typography, dict) else {}
    for src, dst in (("headings", "heading_font"), ("body", "body_font")):
        value = type_map.get(src)
        if isinstance(value, str) and value.strip():
            tokens[dst] = value.strip()
    base_size = type_map.get("base_size_px")
    if isinstance(base_size, (int, float)) and 12 <= float(base_size) <= 24:
        tokens["base_size_px"] = int(base_size)

    if not any(_is_hex(tokens.get(key)) for key in _TOKEN_COLOR_KEYS):
        return {}

    system = build_design_system(design_tokens=tokens)
    result: Dict[str, Any] = {}
    for group in ("colors", "typography", "spacing", "border_radius", "shadows"):
        result.update(system.get(group) or {})
    for key, value in tokens.items():
        if _is_hex(value) or isinstance(value, (int, float)):
            result.setdefault(key, value)
    result["_contrast"] = system.get("contrast") or {}
    return result


def _is_dark(hex_color: str) -> bool:
    from agent.intelligence.design_planner import relative_luminance

    luminance = relative_luminance(hex_color)
    return luminance is not None and luminance < 0.4


def to_plan_inputs(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a design spec into kwargs the Design Planner understands."""
    spec = spec or {}
    colors = spec.get("colors") or {}
    palette = {
        key: value for key, value in colors.items()
        if _is_hex(value) and _COLOR_ALIASES.get(key, key) in _TOKEN_COLOR_KEYS
    }
    palette = {_COLOR_ALIASES.get(k, k): v for k, v in palette.items()}
    tokens = derive_design_tokens(
        colors, spec.get("spacing"), spec.get("typography")
    )
    tokens = {k: v for k, v in tokens.items() if not k.startswith("_")}
    return {
        "palette": palette,
        "design_tokens": tokens,
        "reference_sections": list(spec.get("sections") or []),
        "website_type": spec.get("business_type") or "",
        "reference_intelligence": {
            "reference_hints": list(spec.get("components") or []),
            "source": spec.get("vision_source"),
            "measured": bool(spec.get("colors_measured")),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# JSX emission — a screenshot spec becomes real components
# ═══════════════════════════════════════════════════════════════════════════

_ICON_BY_SECTION = {
    "features": "Sparkles", "stats": "TrendingUp", "pricing": "Tag",
    "testimonial": "Quote", "faq": "HelpCircle", "cta": "ArrowRight",
    "newsletter": "Mail", "contact": "Send", "products": "Package",
}

_JSX_HEADER = "import { useState } from 'react';"


def _icon_import(section: str) -> str:
    return _ICON_BY_SECTION.get(section, "ArrowRight")


def emit_section_jsx(section: str, tokens: Optional[Dict[str, str]] = None) -> str:
    """Emit a real React section component for one planned section.

    Deliberately token-driven: every colour is resolved to a literal now (so the
    emitted file is self-contained) with a CSS-variable fallback, and every
    interactive element ships the keyboard/ARIA contract the planner asked for.
    Built with percent substitution rather than f-strings so JSX braces stay
    literal instead of needing brace-doubling.
    """
    tok = tokens or {}
    ctx = {
        "icon": _icon_import(section),
        "primary": tok.get("primary") or "var(--t-primary, #3f3a35)",
        "on_primary": tok.get("on_primary") or "var(--t-on-primary, #ffffff)",
        "bg": tok.get("bg") or "var(--t-bg, #0e1116)",
        "surface": tok.get("surface") or "var(--t-surface, #151920)",
        "text": tok.get("text") or "var(--t-text, #e8e6e3)",
        "text_dim": tok.get("text_dim") or "var(--t-text-dim, #9a9793)",
        "border": tok.get("border") or "var(--t-border, #26292f)",
        "key": section.replace("_", "-"),
        "name": section.title().replace("_", "") + "Section",
    }

    if section == "faq":
        return _FAQ_JSX % ctx
    if section == "newsletter":
        return _NEWSLETTER_JSX % ctx
    if section == "cta":
        return _CTA_JSX % ctx
    if section == "testimonial":
        return _TESTIMONIAL_JSX % ctx
    return _GENERIC_JSX % dict(
        ctx,
        heading=_GENERIC_HEADINGS.get(section, section.replace("_", " ").title() or "Section"),
        body=_GENERIC_BODIES.get(section, "Add real content here - no placeholder copy ships."),
    )


_GENERIC_HEADINGS = {
    "features": "Everything you need, nothing you don't",
    "stats": "Results our customers measure",
    "product": "Built for real workflows",
    "product_grid": "Pick the right plan for the job",
}

_GENERIC_BODIES = {
    "features": "Purpose-built modules with the loading, error and empty states already handled.",
    "stats": "Measured across live accounts, not projections.",
}


_FAQ_JSX = """import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const FAQ = [
  { q: 'How long does setup take?', a: 'Most teams are live in under 30 minutes.' },
  { q: 'Is support included?', a: 'Yes - every plan includes human support.' },
  { q: 'Can I change plan later?', a: 'Anytime, from your billing settings.' },
];

export default function FaqSection() {
  const [open, setOpen] = useState(0);

  return (
    <section id="faq" className="px-4 py-20" style={{ background: '%(bg)s', color: '%(text)s' }}>
      <div className="mx-auto max-w-3xl">
        <h2 className="text-3xl font-bold">Frequently asked questions</h2>
        <ul className="mt-8 space-y-3">
          {FAQ.map((item, index) => (
            <li
              key={item.q}
              className="rounded-xl border"
              style={{ borderColor: '%(border)s', background: '%(surface)s' }}
            >
              <button
                type="button"
                aria-expanded={open === index}
                aria-controls={`faq-panel-${index}`}
                onClick={() => setOpen(open === index ? -1 : index)}
                className="flex w-full items-center justify-between gap-4 p-5 text-left font-semibold"
              >
                {item.q}
                <ChevronDown
                  size={18}
                  aria-hidden="true"
                  className={open === index ? 'rotate-180 transition-transform' : 'transition-transform'}
                />
              </button>
              <div
                id={`faq-panel-${index}`}
                hidden={open !== index}
                className="px-5 pb-5"
                style={{ color: '%(text_dim)s' }}
              >
                {item.a}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}"""


_NEWSLETTER_JSX = """import { useState } from 'react';
import { Mail } from 'lucide-react';

export default function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ type: 'idle', message: '' });

  const submit = async (event) => {
    event.preventDefault();
    if (!email.includes('@')) {
      setStatus({ type: 'error', message: 'Enter a valid email address.' });
      return;
    }
    setStatus({ type: 'loading', message: 'Subscribing...' });
    try {
      await new Promise((resolve) => setTimeout(resolve, 400));
      setStatus({ type: 'success', message: "You're on the list." });
      setEmail('');
    } catch (error) {
      setStatus({ type: 'error', message: 'Could not subscribe. Try again.' });
    }
  };

  return (
    <section id="newsletter" className="px-4 py-16" style={{ background: '%(surface)s', color: '%(text)s' }}>
      <form
        onSubmit={submit}
        noValidate
        className="mx-auto flex max-w-xl flex-col gap-3 sm:flex-row"
      >
        <label htmlFor="newsletter-email" className="sr-only">Email address</label>
        <div
          className="flex flex-1 items-center gap-2 rounded-lg border px-3"
          style={{ borderColor: '%(border)s', background: '%(bg)s' }}
        >
          <Mail size={18} aria-hidden="true" style={{ color: '%(text_dim)s' }} />
          <input
            id="newsletter-email"
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
            aria-describedby="newsletter-status"
            className="w-full bg-transparent py-3 outline-none"
            style={{ color: '%(text)s' }}
          />
        </div>
        <button
          type="submit"
          disabled={status.type === 'loading'}
          className="rounded-lg px-6 py-3 font-semibold disabled:opacity-60"
          style={{ background: '%(primary)s', color: '%(on_primary)s' }}
        >
          {status.type === 'loading' ? 'Subscribing...' : 'Subscribe'}
        </button>
      </form>
      <p
        id="newsletter-status"
        role="status"
        aria-live="polite"
        className="mx-auto mt-3 max-w-xl text-sm"
        style={{ color: '%(text_dim)s' }}
      >
        {status.message}
      </p>
    </section>
  );
}"""


_CTA_JSX = """import { %(icon)s } from 'lucide-react';

export default function CtaSection() {
  return (
    <section id="cta" className="px-4 py-20" style={{ background: '%(bg)s', color: '%(text)s' }}>
      <div
        className="mx-auto max-w-3xl rounded-2xl p-10 text-center"
        style={{ background: '%(surface)s', border: '1px solid %(border)s' }}
      >
        <h2 className="text-3xl font-bold">Ready to get started?</h2>
        <p className="mt-3" style={{ color: '%(text_dim)s' }}>
          Join the teams shipping faster with a workspace built for the work.
        </p>
        <a
          href="/register"
          className="mt-6 inline-flex items-center gap-2 rounded-lg px-6 py-3 font-semibold transition-transform hover:-translate-y-0.5"
          style={{ background: '%(primary)s', color: '%(on_primary)s' }}
        >
          Create your account
          <%(icon)s size={18} aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}"""


_TESTIMONIAL_JSX = """import { Quote } from 'lucide-react';

const QUOTES = [
  {
    quote: 'We replaced three tools with one and cut our release cycle in half.',
    name: 'Aisha Rahman',
    role: 'Head of Engineering',
    company: 'Northwind',
  },
  {
    quote: 'Onboarding took an afternoon. The team adopted it without a single doc.',
    name: 'Marco Silva',
    role: 'Operations Lead',
    company: 'Contoso',
  },
  {
    quote: 'The reporting alone paid for the plan.',
    name: 'Priya Nair',
    role: 'Finance Director',
    company: 'Fabrikam',
  },
];

export default function TestimonialSection() {
  return (
    <section id="testimonials" className="px-4 py-20" style={{ background: '%(bg)s', color: '%(text)s' }}>
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-3xl font-bold">Trusted by teams who ship</h2>
        <ul className="mt-10 grid gap-6 md:grid-cols-3">
          {QUOTES.map((item) => (
            <li
              key={item.name}
              className="rounded-xl p-6"
              style={{ background: '%(surface)s', border: '1px solid %(border)s' }}
            >
              <Quote size={20} aria-hidden="true" style={{ color: '%(primary)s' }} />
              <blockquote className="mt-4" style={{ color: '%(text_dim)s' }}>{item.quote}</blockquote>
              <p className="mt-4 text-sm font-semibold">{item.name}</p>
              <p className="text-sm" style={{ color: '%(text_dim)s' }}>
                {item.role}, {item.company}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}"""


_GENERIC_JSX = """import { %(icon)s } from 'lucide-react';

const ITEMS = [
  { title: 'First capability', body: '%(body)s' },
  {
    title: 'Second capability',
    body: 'Every surface handles loading, success, error and empty states.',
  },
  {
    title: 'Third capability',
    body: 'Keyboard reachable, screen-reader labelled, dark-mode ready.',
  },
];

export default function %(name)s() {
  return (
    <section
      id="%(key)s"
      className="px-4 py-20"
      style={{ background: '%(bg)s', color: '%(text)s' }}
      data-reveal
    >
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold">%(heading)s</h2>
        <ul className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {ITEMS.map((item) => (
            <li
              key={item.title}
              className="rounded-xl p-6"
              style={{ background: '%(surface)s', border: '1px solid %(border)s' }}
            >
              <%(icon)s size={22} aria-hidden="true" style={{ color: '%(primary)s' }} />
              <h3 className="mt-4 text-lg font-semibold">{item.title}</h3>
              <p className="mt-2" style={{ color: '%(text_dim)s' }}>{item.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}"""


def emit_components_jsx(
    sections: Sequence[str],
    tokens: Optional[Dict[str, str]] = None,
    only_interactive: bool = False,
) -> Dict[str, str]:
    """Emit a `{section_key: jsx}` map for the given sections."""
    wanted = ("faq", "newsletter", "cta", "testimonial")
    out: Dict[str, str] = {}
    for section in sections or []:
        key = str(section).strip().lower()
        if not key:
            continue
        if only_interactive and key not in wanted:
            continue
        out[key] = emit_section_jsx(key, tokens)
    return out


def design_spec_to_prompt(spec: Dict[str, Any]) -> str:
    """Convert a design spec into a natural-language prompt for generation."""
    spec = spec or {}
    business = spec.get("business_type") or "professional"
    sections = ", ".join(spec.get("sections") or []) or "hero, features, cta, footer"

    parts = [
        f"Build a {business} website.",
        f"Structure the page with these sections in order: {sections}.",
    ]

    colors = spec.get("colors") or {}
    if colors.get("primary"):
        parts.append(f"Use {colors['primary']} as the primary brand colour.")
    if colors.get("bg"):
        parts.append(f"Page background {colors['bg']}.")

    typography = spec.get("typography") or {}
    if typography.get("heading"):
        parts.append(f"Headings in {typography['heading']}, body in {typography.get('body', 'sans-serif')}.")

    components = spec.get("components") or []
    if components:
        parts.append(f"Compose the page from: {', '.join(str(c) for c in components)}.")

    spacing = spec.get("spacing") or {}
    if isinstance(spacing.get("section_gap_px"), (int, float)):
        parts.append(f"Keep section rhythm at roughly {int(spacing['section_gap_px'])}px.")

    shots = spec.get("shots") or []
    if len(shots) > 1:
        parts.append(
            "Reference comprises "
            + ", ".join(str(s.get("role") or "shot") for s in shots)
            + "; keep the mobile variant single-column."
        )

    if spec.get("analyzed") is False:
        parts.append(
            "Treat the section order as a starting point and refine hierarchy, "
            "spacing and contrast during design review."
        )

    return " ".join(parts)


def spec_fingerprint(spec: Dict[str, Any]) -> str:
    """Stable hash of the structural reading, for change detection between runs."""
    import hashlib
    import json as _json

    payload = {
        "sections": spec.get("sections"),
        "colors": spec.get("colors"),
        "typography": spec.get("typography"),
    }
    return hashlib.sha256(
        _json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]