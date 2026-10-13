"""Reference Cloner — reverse-engineer a live reference website.

Takes a reference URL and decomposes it into the same 18-attribute design
schema the rest of the pipeline uses, so a cited site becomes *inspiration
attributes*, never a template copy. This is the executable half of Reference
Intelligence: :mod:`agent.intelligence.reference_intelligence` already knows how
to turn a *phrase* ("Apple-style clarity") into attributes; this module turns a
*live page* into attributes.

Backend order (first available wins), each reported honestly:

  1. ``agent-browser`` — live DOM read: measured, not inferred.
  2. ``single-file``    — faithful single-HTML capture, then static parse.
  3. ``firecrawl``      — structured scrape of the reference page.
  4. static HTTP fetch  — urllib/requests + stdlib HTMLParser: heuristic.

Every result carries a ``status`` of ``measured`` (browser/DOM), ``heuristic``
(static parse) or ``unavailable`` (nothing could be read). Nothing is fabricated:
a value that cannot be measured from the page (brand warmth, luxury, motion) is
left neutral and named as not-measured rather than guessed.

The three external tools are registered in ``registry/design-resources.json``
under ``role: reverse_engineering_tool``; this module describes and detects them
but never bundles or copies their code.

Deterministic and offline-capable: with no browser and no network the static
path still runs, and a failed fetch returns ``unavailable`` instead of raising.
"""
from __future__ import annotations

import json
import re
import shutil
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:  # package-relative import (normal runtime)
    from .reference_intelligence import _DEFAULT_ATTRIBUTE, _ATTRIBUTE_KEYS
except Exception:  # pragma: no cover - flat import fallback
    from agent.intelligence.reference_intelligence import (
        _DEFAULT_ATTRIBUTE,
        _ATTRIBUTE_KEYS,
    )


# ---------------------------------------------------------------------------
# Registered reverse-engineering tools (mirrors registry/design-resources.json)
# ---------------------------------------------------------------------------
REVERSE_ENGINEER_TOOLS: Dict[str, Dict[str, str]] = {
    "screenshot-to-code": {
        "name": "Screenshot to Code",
        "repo": "https://github.com/abi/screenshot-to-code",
        "url": "https://github.com/abi/screenshot-to-code",
        "license": "MIT",
        "capability": "screenshot_or_url_to_code",
        "binary": "",
        "install": "https://github.com/abi/screenshot-to-code#installation",
    },
    "firecrawl": {
        "name": "Firecrawl",
        "repo": "https://github.com/firecrawl/firecrawl",
        "url": "https://github.com/firecrawl/firecrawl",
        "license": "AGPL-3.0",
        "capability": "structured_web_scrape",
        "binary": "firecrawl",
        "install": "npm install -g firecrawl",
    },
    "single-file-cli": {
        "name": "SingleFile CLI",
        "repo": "https://github.com/gildas-lormeau/single-file-cli",
        "url": "https://github.com/gildas-lormeau/single-file-cli",
        "license": "AGPL-3.0",
        "capability": "faithful_html_snapshot",
        "binary": "single-file",
        "install": "npm install -g single-file-cli",
    },
}

#: Attributes that cannot be read from markup and are therefore left neutral.
UNMEASURABLE_ATTRIBUTES = (
    "warmth", "luxury", "cinematic", "bold", "futuristic", "craft",
)

_ANIMATION_LIBS = (
    "framer-motion", "framer_motion", "gsap", "scrolltrigger", "lenis",
    "anime.js", "animejs", "motion.dev", "data-aos", "@react-spring",
)
_CSS_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_RGB_RE = re.compile(
    r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", re.IGNORECASE
)
_FONT_RE = re.compile(r"font-family\s*:\s*([^;}\"']+)", re.IGNORECASE)
_CTA_CLASS_RE = re.compile(
    r"(btn|button|cta|call-to-action|primary-action)", re.IGNORECASE
)

#: Landmark/section tags that give a coarse page skeleton.
_LANDMARK_TAGS = {"header", "nav", "main", "footer", "aside", "section", "article"}
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


# ---------------------------------------------------------------------------
# Static HTML structure parsing (stdlib only)
# ---------------------------------------------------------------------------
class _StructureParser(HTMLParser):
    """Collect page skeleton from markup without any third-party parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: List[str] = []
        self.cta_texts: List[str] = []
        self.images = 0
        self.image_alts = 0
        self.forms = 0
        self.inputs = 0
        self.sections = 0
        self.links = 0
        self.nav_links = 0
        self.buttons = 0
        self.landmarks: set = set()
        self._nav_depth = 0
        self._capture: Optional[str] = None
        self._buf: List[str] = []

    # -- capture helpers ---------------------------------------------------
    def _flush(self) -> None:
        text = " ".join("".join(self._buf).split())
        if not text:
            self._capture = None
            self._buf = []
            return
        if self._capture in ("h1", "h2", "h3", "h4"):
            self.headings.append(text)
        elif self._capture == "cta":
            self.cta_texts.append(text)
        self._capture = None
        self._buf = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        attr = {k.lower(): (v or "") for k, v in attrs}
        if tag == "nav":
            self._nav_depth += 1
        if tag in _LANDMARK_TAGS:
            self.landmarks.add(tag)
            if tag in ("section", "article"):
                self.sections += 1
        if tag in ("h1", "h2", "h3", "h4"):
            if self._capture:
                self._flush()
            self._capture = tag
            self._buf = []
        elif tag == "button":
            self.buttons += 1
            self._capture = "cta"
            self._buf = []
        elif tag == "img":
            self.images += 1
            if attr.get("alt", "").strip():
                self.image_alts += 1
        elif tag == "form":
            self.forms += 1
        elif tag == "input":
            self.inputs += 1
        elif tag == "a":
            self.links += 1
            if self._nav_depth:
                self.nav_links += 1
            elif _CTA_CLASS_RE.search(attr.get("class", "")):
                self._capture = "cta"
                self._buf = []
        if tag in _VOID_TAGS and self._capture == "cta" and tag not in ("button",):
            pass

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self._nav_depth:
            self._nav_depth -= 1
        if self._capture and tag == self._capture:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)


def _hex_to_rgb(value: str) -> Optional[Tuple[int, int, int]]:
    raw = value.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return None
    try:
        return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
    except ValueError:
        return None


def _saturation(rgb: Tuple[int, int, int]) -> float:
    r, g, b = (channel / 255.0 for channel in rgb)
    high, low = max(r, g, b), min(r, g, b)
    if high == 0:
        return 0.0
    return (high - low) / high


def _luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = (channel / 255.0 for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _scan_css_and_markup(html: str) -> Dict[str, Any]:
    """Regex pass for colours, fonts and animation libraries."""
    styles = " ".join(_CSS_RE.findall(html or ""))
    haystack = (html or "") + " " + styles

    colors: List[str] = []
    for match in _HEX_RE.finditer(haystack):
        colors.append("#" + match.group(1))
    for match in _RGB_RE.finditer(haystack):
        colors.append("#%02x%02x%02x" % tuple(int(g) for g in match.groups()))

    fonts = {
        f.split(",")[0].strip().strip("'\"")
        for f in _FONT_RE.findall(haystack)
        if f.strip()
    }
    fonts = {f for f in fonts if f and not f.startswith("var(")}

    lowered = haystack.lower()
    animations = [lib for lib in _ANIMATION_LIBS if lib in lowered]

    return {
        "colors": colors,
        "fonts": sorted(fonts),
        "animation_libraries": animations,
    }


def _structure_from_html(html: str) -> Dict[str, Any]:
    parser = _StructureParser()
    try:
        parser.feed(html or "")
    except Exception:  # pragma: no cover - malformed markup must not raise
        pass
    scanned = _scan_css_and_markup(html or "")
    return {
        "html_length": len(html or ""),
        "headings": parser.headings[:60],
        "cta_texts": parser.cta_texts[:30],
        "images": parser.images,
        "image_alts": parser.image_alts,
        "forms": parser.forms,
        "inputs": parser.inputs,
        "sections": parser.sections,
        "links": parser.links,
        "nav_links": parser.nav_links,
        "buttons": parser.buttons,
        "landmarks": sorted(parser.landmarks),
        "fonts": scanned["fonts"],
        "colors": scanned["colors"][:200],
        "animation_libraries": scanned["animation_libraries"],
    }


# ---------------------------------------------------------------------------
# DOM read via agent-browser (measured)
# ---------------------------------------------------------------------------
_BROWSER_JS = (
    "() => {"
    " const q=(s)=>Array.from(document.querySelectorAll(s));"
    " const txt=(e)=>(e.textContent||'').trim().slice(0,120);"
    " const hs=q('h1,h2,h3,h4').map(txt).filter(Boolean).slice(0,60);"
    " const nav=q('nav a');"
    " const cta=q('button, a[class*=btn], a[class*=cta], a[class*=button], [role=button]')"
    "   .map(txt).filter(Boolean).slice(0,30);"
    " const styles=Array.from(document.styleSheets).flatMap((ss)=>{try{"
    "   return Array.from(ss.cssRules||[]).map((r)=>r.cssText);}catch(e){return [];}});"
    " const blobs=styles.join(' ');"
    " const colors=(blobs.match(/#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgba?\\([^)]+\\)/g)||[]);"
    " const fonts=Array.from(new Set((blobs.match(/font-family\\s*:\\s*([^;}\"']+)/gi)||[])))"
    "   .map((f)=>f.replace(/font-family\\s*:\\s*/i,'').split(',')[0].trim());"
    " const all=document.documentElement.innerHTML.toLowerCase();"
    " const libs=['framer-motion','motion','gsap','lenis','anime','aos'].filter((l)=>all.includes(l));"
    " return {"
    "  html_length: document.documentElement.innerHTML.length,"
    "  headings: hs, cta_texts: cta,"
    "  images: q('img').length,"
    "  image_alts: q('img[alt]').filter((i)=>i.getAttribute('alt').trim()).length,"
    "  forms: q('form').length, inputs: q('input,textarea,select').length,"
    "  sections: q('section,article').length,"
    "  links: q('a').length, nav_links: nav.length,"
    "  buttons: q('button').length,"
    "  landmarks: ['header','nav','main','footer','aside','section','article']"
    "    .filter((t)=>document.querySelector(t)),"
    "  fonts: fonts.slice(0,10), colors: colors.slice(0,200),"
    "  animation_libraries: libs"
    " };}"
)


def _structure_from_browser(url: str) -> Optional[Dict[str, Any]]:
    try:
        from .browser_integration import AgentBrowser
    except Exception:  # pragma: no cover - flat import fallback
        try:
            from agent.intelligence.browser_integration import AgentBrowser
        except Exception:
            return None
    browser = AgentBrowser()
    if not browser.available:
        return None
    try:
        if not browser.open(url):
            return None
        browser.wait(1200)
        data = browser.eval(_BROWSER_JS)
        if isinstance(data, dict) and data.get("html_length"):
            data.setdefault("landmarks", [])
            return data
    except Exception:  # pragma: no cover - runtime dependent
        return None
    finally:
        try:
            browser.close()
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Static HTTP fetch
# ---------------------------------------------------------------------------
def _fetch_html(url: str, timeout: int = 15) -> Tuple[Optional[str], Optional[str]]:
    """Fetch a URL's HTML. Returns (html, error) — never raises."""
    if not url or not url.startswith(("http://", "https://")):
        return None, "unsupported_url_scheme"
    try:
        import requests  # type: ignore

        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "LumicorePro-ReferenceCloner/1.0"},
        )
        if resp.status_code >= 400:
            return None, f"http_{resp.status_code}"
        return resp.text, None
    except Exception as exc:  # noqa: BLE001 - requests optional/network dependent
        try:
            from urllib.request import Request, urlopen

            req = Request(url, headers={"User-Agent": "LumicorePro-ReferenceCloner/1.0"})
            with urlopen(req, timeout=timeout) as handle:  # noqa: S310 - user-supplied reference
                return handle.read().decode("utf-8", errors="replace"), None
        except Exception as exc2:  # pragma: no cover - network dependent
            return None, f"fetch_failed: {exc2 or exc}"


# ---------------------------------------------------------------------------
# Attribute decomposition (from measured structure signals)
# ---------------------------------------------------------------------------
def structure_to_attributes(structure: Dict[str, Any]) -> Dict[str, float]:
    """Map measured structure signals onto the 18-attribute schema.

    Deterministic and documented. Attributes that markup cannot express
    (warmth, luxury, cinematic, bold, futuristic, craft) stay at the schema
    default and are reported in ``unmeasured`` by :func:`clone_reference`.
    """
    structure = structure or {}
    headings = structure.get("headings") or []
    cta = structure.get("cta_texts") or []
    colors = structure.get("colors") or []
    fonts = structure.get("fonts") or []

    images = int(structure.get("images") or 0)
    sections = int(structure.get("sections") or 0)
    links = int(structure.get("links") or 0)
    nav_links = int(structure.get("nav_links") or 0)
    forms = int(structure.get("forms") or 0)
    inputs = int(structure.get("inputs") or 0)
    animation_libs = structure.get("animation_libraries") or []

    # Element density: structural elements per 1 KB of markup.
    html_len = max(1, int(structure.get("html_length") or 1))
    elements = len(headings) + sections + images + forms + links
    density = _clamp01(elements / (html_len / 1000.0) / 8.0)

    rgb_colors = [rgb for rgb in (_hex_to_rgb(c) for c in colors) if rgb]
    if rgb_colors:
        avg_saturation = sum(_saturation(rgb) for rgb in rgb_colors) / len(rgb_colors)
        dark_share = (
            sum(1 for rgb in rgb_colors if _luminance(rgb) < 0.35) / len(rgb_colors)
        )
    else:
        avg_saturation = 0.35
        dark_share = 0.0

    font_count = len(fonts)
    if font_count <= 1:
        typography = 0.85
    elif font_count == 2:
        typography = 0.78
    elif font_count == 3:
        typography = 0.68
    else:
        typography = 0.5

    motion = 0.75 if animation_libs else 0.35

    attributes = dict(_DEFAULT_ATTRIBUTE)
    attributes.update({
        "minimalism": _clamp01(1.0 - density),
        "whitespace": _clamp01(1.0 - density * 0.9),
        "typography": typography,
        "motion": motion,
        "visual_density": _clamp01(density),
        "content_density": _clamp01(sections / 8.0),
        "image_dominance": _clamp01(images / (images + len(headings) + 1)),
        "color_saturation": _clamp01(avg_saturation),
        "dark_canvas": _clamp01(dark_share),
        "navigation": _clamp01(nav_links / 8.0),
        "cta_focus": _clamp01(len(cta) / 3.0),
        "interaction_complexity": _clamp01(forms * 0.3 + inputs * 0.05),
    })
    return {key: _round(attributes.get(key, _DEFAULT_ATTRIBUTE.get(key, 0.45)))
            for key in _ATTRIBUTE_KEYS}


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------
def detect_backends() -> Dict[str, Dict[str, Any]]:
    """Report which reverse-engineering backends exist in this environment."""
    report: Dict[str, Dict[str, Any]] = {}
    for slug, meta in REVERSE_ENGINEER_TOOLS.items():
        binary = meta.get("binary") or ""
        available = bool(binary) and bool(shutil.which(binary))
        report[slug] = {
            "name": meta["name"],
            "repo": meta["repo"],
            "license": meta["license"],
            "capability": meta["capability"],
            "available": available,
        }
    try:
        from .browser_integration import AgentBrowser
    except Exception:  # pragma: no cover
        try:
            from agent.intelligence.browser_integration import AgentBrowser
        except Exception:
            AgentBrowser = None  # type: ignore[assignment]
    browser_ok = bool(AgentBrowser and AgentBrowser().available)
    report["agent-browser"] = {
        "name": "agent-browser",
        "repo": "https://www.npmjs.com/package/agent-browser",
        "license": "MIT",
        "capability": "live_dom_read",
        "available": browser_ok,
    }
    return report


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def extract_structure(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Read a reference URL's structure, preferring the most trustworthy backend."""
    result: Dict[str, Any] = {
        "url": url,
        "host": urlparse(url).hostname or "",
        "backend": None,
        "status": "unavailable",
        "structure": {},
        "error": None,
    }
    if not url:
        result["error"] = "no_url"
        return result

    browser_structure = _structure_from_browser(url)
    if browser_structure:
        result["backend"] = "agent-browser"
        result["status"] = "measured"
        result["structure"] = browser_structure
        return result

    html, error = _fetch_html(url, timeout=timeout)
    if html is None:
        result["error"] = error or "fetch_failed"
        return result
    result["backend"] = "static-http"
    result["status"] = "heuristic"
    result["structure"] = _structure_from_html(html)
    return result


def clone_reference(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Reverse-engineer a reference URL into measurable design attributes.

    Returns a manifest. A ``status`` of ``unavailable`` means the page could not
    be read at all — callers must not treat that as a neutral profile.
    """
    reading = extract_structure(url, timeout=timeout)
    structure = reading.get("structure") or {}
    attributes: Dict[str, float] = {}
    if reading.get("status") != "unavailable":
        attributes = structure_to_attributes(structure)

    return {
        "url": url,
        "host": reading.get("host"),
        "status": reading.get("status"),
        "backend": reading.get("backend"),
        "error": reading.get("error"),
        "tools": detect_backends(),
        "structure": structure,
        "attributes": attributes,
        "unmeasured": list(UNMEASURABLE_ATTRIBUTES) if attributes else [],
        "constraints": {
            "copy_style": "do_not_copy",
            "layout": "derive_attributes_only",
            "branding": "fully_original",
        },
        "note": (
            "Reverse-engineered for inspiration attributes only; layouts, copy and "
            "branding must be fully original."
            if attributes
            else "Reference could not be read; no attributes were derived."
        ),
    }


def to_plan_inputs(clone: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a clone manifest into pipeline kwargs (reference_intelligence block)."""
    clone = clone or {}
    return {
        "reference_url": clone.get("url"),
        "reference_attributes": dict(clone.get("attributes") or {}),
        "reference_intelligence": {
            "source": clone.get("backend"),
            "measured": clone.get("status") == "measured",
            "host": clone.get("host"),
        },
    }


def run_cli(url: str) -> str:
    """CLI entry: prints the clone manifest as JSON."""
    return json.dumps(clone_reference(url), indent=2)


__all__ = [
    "REVERSE_ENGINEER_TOOLS",
    "UNMEASURABLE_ATTRIBUTES",
    "clone_reference",
    "detect_backends",
    "extract_structure",
    "structure_to_attributes",
    "to_plan_inputs",
]


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else ""
    print(run_cli(target))
