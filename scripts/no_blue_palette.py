"""Replace blue-Tailwind palette with each project's own brand palette (no blue websites)."""
import colorsys
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "ai-agent"))

BLUE_FAMILY = re.compile(r"\b(blue|indigo|sky|teal|cyan)-(\d+)", re.IGNORECASE)
MAP = {
    "blue": "primary", "indigo": "primary", "sky": "primary",
    "teal": "accent", "cyan": "accent",
}


def hsl_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def shade_range(hue: float, sat: float, base_l: float = 0.60) -> dict:
    """10 shades (50..900) from a hue."""
    out = {}
    for i, l in enumerate([0.97, 0.93, 0.87, 0.78, 0.66, 0.55, 0.46, 0.38, 0.30, 0.22]):
        out[str(50 * (i + 1))] = hsl_hex(hue, sat, l)
    return out


def make_tailwind(primary_hex: str, accent_hex: str, repo: str) -> str:
    hue = R._PALETTE_HUES[0]  # placeholder
    return f"""export default {{
  content: ['./index.html', './src/**/*{{js,jsx}}'],
  darkMode: 'class',
  theme: {{
    extend: {{
      colors: {{
        primary: {primary_shades},
        accent: {accent_shades},
      }},
    }},
  }},
}}"""


def main() -> int:
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    total_repl = 0
    for idx, proj in enumerate(projects):
        pal = R.palette_for(idx)
        brand = pal["brand"]
        accent = pal["accent"]
        brand_hue = R._PALETTE_HUES[idx % len(R._PALETTE_HUES)]
        accent_hue = (brand_hue + 30) % 360
        primary_shades = shade_range(brand_hue, 0.62)
        accent_shades = shade_range(accent_hue, 0.55)
        primary_list = "{ " + ", ".join(f"'{k}': '{v}'" for k, v in primary_shades.items()) + " }"
        accent_list = "{ " + ", ".join(f"'{k}': '{v}'" for k, v in accent_shades.items()) + " }"
        repo = proj.name

        # Rewrite tailwind.config.js
        tw = proj / "frontend" / "tailwind.config.js"
        if tw.exists():
            tw.write_text(f"""export default {{
  content: ['./index.html', './src/**/*{{js,jsx}}'],
  darkMode: 'class',
  theme: {{
    extend: {{
      ringColor: {{ DEFAULT: "{brand}", offset: "{brand}" }},
      colors: {{
        primary: {primary_list},
        accent: {accent_list},
        blue: {primary_list},
        indigo: {primary_list},
        cyan: {accent_list},
        teal: {accent_list},
        sky: {primary_list},
      }},
    }},
  }},
}}
""", encoding="utf-8")

        # Replace blue-* -> primary-/accent- in src files
        for f in proj.rglob("*"):
            if f.suffix not in (".jsx", ".js", ".tsx", ".ts", ".css"):
                continue
            if "node_modules" in str(f) or "dist" in str(f):
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            new, n = BLUE_FAMILY.subn(lambda m: MAP[m.group(1)] + "-" + m.group(2), txt)
            if n:
                f.write_text(new, encoding="utf-8")
                total_repl += n
        print(f"{proj.name}: primary={brand} repl={n}")
    print("total blue->primary/accent replacements:", total_repl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
