"""Blue/gold-class + hex/rgb cleanup for the 10 AI-agent products (7.13).

For every agent frontend:
  1. remap cyan/violet/blue/sky/indigo Tailwind utilities -> accent/primary,
  2. remap slate-800/900 utilities -> neutral-800/900 (audit blue list),
  3. recolor residual blue/slate-navy/gold hex literals across src
     (css/jsx/js/json/html/svg) using _brand_assets_purge.recolour,
  4. purge blue-family rgba()/rgb() tuples in src CSS -> brand (Lightning CSS
     converts alpha-rgb() to 8-digit hex in dist, e.g. rgba(37,99,235,.25) ->
     #2563eb40, so source rgb() blues must be branded at the source),
  5. neutralise the Tailwind preflight default ring colour
     (rgb(59 130 246 / .5) -> #3b82f680 in dist) with an unlayered override,
  6. rebrand the MotionSystems spotlight arbitrary-class rgba() (css-bearing),
  7. recolor extra cyan/sky hex tones (#06b6d4 #22d3ee #0891b2 #38bdf8
     #7dd3fc #93c5fd #4dd6ff) -> accent/primary keeping any alpha suffix.

After this the rebuilt dist is blue-free under BOTH the official BLUE_RE (\b)
audit and final_verify's stricter substring scan; then run
_brand_assets_purge on public+dist for the final pass.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
from _brand_assets_purge import brand_tokens, recolour  # noqa: E402

AGENTS = [
    "appointly-ai", "claimflow-ai", "clausecheck-ai", "insightpipe-ai",
    "leadscout-ai", "ledgerai", "onboarder-ai", "recruitiq-ai",
    "supportdesk-ai", "tablehost-ai",
]
SRC_EXT = {".css", ".jsx", ".js", ".json", ".html", ".svg", ".txt"}
CLASS_REMAP = [
    # (pattern, repl). cyan -> accent; others -> primary; drop shade, keep /opacity
    (r"(cyan|blue|sky|indigo|violet)-(\d{2,3}(/\d+)?)",
     lambda m: ("accent" if m.group(1) == "cyan" else "primary") + (m.group(3) or "")),
    # slate-800/900 -> neutral (these two compile to audited blues)
    (r"slate-(800|900)", r"neutral-\1"),
]

utilities = ("bg|text|border|from|via|to|ring|shadow|outline|divide|placeholder|"
             "caret|stroke|fill|decoration|ring-offset|accent")
TOKEN_RE = __import__("re").compile(
    r"(?<![A-Za-z0-9_\[\]#.-])(" + utilities + r")-(" + CLASS_REMAP[0][0] + r"-?\d+"
    r"(?:/[0-9]+)?)(?![A-Za-z0-9])")
# simpler tokenization: match base-family-shade as a unit
FAMILY_RE = __import__("re").compile(
    r"(?<![\w#.-])(" + utilities + r")-(cyan|blue|sky|indigo|violet)"
    r"-(\d{2,3})(/[0-9]+)?(?![A-Za-z0-9/])")


def remap_classes(text: str) -> str:
    def _r(m):
        base, fam, shade, op = m.groups()
        color = "accent" if fam == "cyan" else "primary"
        return base + "-" + color + (op or "")

    text = FAMILY_RE.sub(_r, text)
    text = __import__("re").sub(r"(?<![\w#.-])slate-(800|900)(?![A-Za-z0-9-])",
                                r"neutral-\1", text)
    return text


def _hex_rgb(hx):
    v = hx.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


# extra 6-digit cyan/sky/blue tones recolour misses; value -> family
EXTRA_HEX = {
    "#06b6d4": "cyan", "#22d3ee": "cyan", "#0891b2": "cyan",
    "#38bdf8": "sky", "#7dd3fc": "cyan", "#93c5fd": "blue",
    "#4dd6ff": "cyan", "#0ea5e9": "sky",
}


def purge_extra_hexes(text: str, brand_rgb, accent_rgb):
    import re
    def _rep(m):
        hx = m.group(1).lower()
        alpha = m.group(2) or ""
        fam = EXTRA_HEX["#" + hx]
        r, g, b = accent_rgb if fam == "cyan" else brand_rgb
        return "#%02x%02x%02x%s" % (r, g, b, alpha)
    return re.sub(r"#(06b6d4|22d3ee|0891b2|38bdf8|7dd3fc|93c5fd|4dd6ff|0ea5e9)"
                  r"([0-9a-fA-F]{2})?", _rep, text, flags=re.I)


RGB_PAT = __import__("re").compile(
    r"(rgba?\()\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)"
    r"(?:\s*,\s*([0-9.]+%?))?\s*(\))?", __import__("re").I)


def is_blue(r, g, b):
    return b >= 45 and b - min(r, g) >= 28 and b - max(r, g) >= 20


def purge_rgb_tuples(text: str, brand_rgb):
    """Rebrand blue-family rgb()/rgba() tuples to brand (alpha preserved);
    always re-emits a canonical, correctly-closed tuple (repairs parens)."""
    def _rep(m):
        r, g, b = int(m.group(2)), int(m.group(3)), int(m.group(4))
        alpha = m.group(5) or ""
        if is_blue(r, g, b):
            r, g, b = brand_rgb
        return "%s%d, %d, %d%s%s)" % (
            m.group(1), r, g, b,
            (", " if alpha else ""), alpha,
        )
    return RGB_PAT.sub(_rep, text)


RING_OVERRIDE = ("/* lumi-ring-neutral */\n"
                 "*, ::before, ::after, ::backdrop {\n"
                 "  --tw-ring-color: rgb(14 17 22 / 0.5);\n"
                 "}")


def ensure_ring_override(css_path, existing_text) -> bool:
    if "lumi-ring-neutral" in existing_text:
        return False
    import re
    stripped = existing_text.rstrip()
    if stripped and not stripped.endswith(";"):
        stripped += ";"
    css_path.write_text(stripped + "\n\n" + RING_OVERRIDE + "\n",
                        encoding="utf-8")
    return True


def main() -> int:
    import json
    progress = {}
    pf = GEN / "AGENT_UNIQUE_PROGRESS.json"
    if pf.exists():
        try:
            progress = {r["slug"]: r for r in json.loads(pf.read_text(encoding="utf-8"))}
        except Exception:
            progress = {}
    for slug in AGENTS:
        fe = GEN / slug / "frontend"
        brand, accent = brand_tokens(GEN / slug)
        if not brand:
            row = progress.get(slug, {})
            brand = row.get("brand")
        accent = accent or brand or "#e0a33a"
        brand = brand or "#e0a33a"
        brand_rgb = _hex_rgb(brand)
        accent_rgb = _hex_rgb(accent)
        touched = 0
        src = fe / "src"
        for f in src.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in SRC_EXT:
                continue
            if "node_modules" in str(f) or "dist" in str(f):
                continue
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            nt = remap_classes(t)
            nt = recolour(nt, brand, accent)
            if f.suffix.lower() == ".css":
                nt = purge_rgb_tuples(nt, brand_rgb)
                # stray `};` after a rule -> lightningcss "Invalid empty selector"
                nt = __import__("re").sub(r"}\s*;", "}", nt)
            elif f.suffix.lower() in (".jsx", ".js"):
                # arbitrary tailwind class keeps an rgb() that compiles to css
                nt = __import__("re").sub(
                    r"(bg-\[[^\]]*?)rgba\(\s*6,\s*182,\s*212([^\]]*?\])",
                    r"\1rgba(14, 17, 22\2", nt, flags=__import__("re").I)
            nt = purge_extra_hexes(nt, brand_rgb, accent_rgb)
            if nt != t:
                f.write_text(nt, encoding="utf-8")
                touched += 1
        css_index = src / "index.css"
        if css_index.exists() and ensure_ring_override(
                css_index, css_index.read_text(encoding="utf-8", errors="replace")):
            touched += 1
        tw = fe / "tailwind.config.js"
        if tw.exists():
            twt = tw.read_text(encoding="utf-8", errors="replace")
            _tw0 = twt
            twt = recolour(twt, brand, accent)
            twt = purge_extra_hexes(twt, brand_rgb, accent_rgb)
            if "lumi-ring-neutral" not in twt:
                twt = __import__("re").sub(
                    r"(extend\s*:\s*\{)",
                    r"\1\n    // lumi-ring-neutral\n    ringColor: { DEFAULT: 'rgb(14 17 22 / 0.5)' },",
                    twt, count=1, flags=__import__("re").I)
            def _cfg(m):
                slot, name = m.group(1), m.group(2)
                if name == "primary":
                    rgb = brand_rgb
                elif name == "accent":
                    rgb = accent_rgb
                elif name == "text":
                    rgb = (14, 17, 22)
                else:
                    rgb = (int(m.group(3)), int(m.group(4)), int(m.group(5)))
                return "rgb(var(%s %d %d %d)" % (slot, rgb[0], rgb[1], rgb[2])
            twt = __import__("re").sub(
                r"rgb\(var\((--t-(\w+)-rgb,)\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\)",
                _cfg, twt)
            if twt != _tw0:
                tw.write_text(twt, encoding="utf-8")
                touched += 1
        print("%-18s brand=%s touched=%d src-files" % (slug, brand, touched))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())