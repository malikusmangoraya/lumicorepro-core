"""Reconstruct corrupted theme.js files from the canonical template."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restyle_unique_all as R

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "ai-agent"))

def make_theme(brand, soft, accent, accent_alt):
    css_braces = lambda s: s.replace('{', '{{').replace('}', '}}')
    tokens_block = css_braces("""
:root {
  --t-brand: """ + brand + """;
  --t-brand-soft: """ + soft + """;
  --t-surface-lux-bg: #0b0c10;
  --t-surface-lux-2: #14161c;
  --t-surface-lux-3: #1d2026;
  --t-glass-blur: 6px;
  --t-glass-opacity: 0.55;
  --t-accent-gold: """ + accent + """;
  --t-accent-cyan: """ + accent_alt + """;
  --t-error: #ff5f6d;
  --t-success: #34d399;
  --t-warn: #fbbf24;
  --t-serif: "Cormorant Garamond", Georgia, serif;
  --t-sans: "Inter", system-ui, sans-serif;
  --t-radius-xl: 1.25rem;
  --t-radius-lg: 1rem;
  --t-radius-md: 0.5rem;
  --t-shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --t-shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --t-shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  --t-shadow-xl: 0 20px 25px rgba(0,0,0,0.1);
}
/* ===== end LUMICORE_DESIGN_TOKENS_V7 ===== */""")
    motion_block = css_braces("""
[data-reveal] { opacity: 0; transform: translateY(18px); transition: opacity 0.6s ease, transform 0.6s ease; }
[data-reveal].visible { opacity: 1; transform: translateY(0); }
.card-lift { transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), box-shadow 0.4s ease; }
.card-lift:hover { transform: translateY(-6px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }
.shimmer { background: linear-gradient(110deg, transparent 33%, rgba(255,255,255,0.08) 50%, transparent 67%); background-size: 200% 100%; animation: shimmer 2s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
/* ===== end LUMI_MOTION_V7 ===== */""")
    return (
        '/**\n * theme.js - dark-canvas default (TRD #3 canvas archetypes).\n'
        ' * Applies `.dark` on <html> by default, honoring a saved preference, then the\n'
        ' * operating-system scheme. Runs on import.\n'
        ' */\n'
        '(function applyTheme() {\n'
        '  try {\n'
        '    const root = document.documentElement;\n'
        '    const saved = localStorage.getItem(\'theme\');\n'
        '    const pref = saved\n'
        '      ? saved === \'dark\'\n'
        '      : window.matchMedia && window.matchMedia(\'(prefers-color-scheme: dark)\').matches;\n'
        '    root.classList.toggle(\'dark\', pref === true || saved === \'dark\');\n'
        '    if (!saved) root.classList.add(\'dark\'); // dark default per design tokens\n'
        '  } catch (e) {\n'
        '    void e;\n'
        '  }\n'
        '})();\n\n'
        'export default function theme() {\n'
        '  return document.documentElement.classList.contains(\'dark\');\n'
        '}\n\n'
        'export const designTokens = `/* ===== LUMICORE_DESIGN_TOKENS_V7 ===== */\n'
        + tokens_block + '`;\n\n'
        'export const lumiMotionCss = `/* ===== LUMI_MOTION_V7 ===== */\n'
        + motion_block + '`;\n'
    )


def main() -> int:
    from agent.intelligence.benchmark_first import run_benchmark_first  # noqa: E402
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    pmap = {p.name: i for i, p in enumerate(projects)}
    fixed = 0
    for proj in projects:
        idx = pmap[proj.name]
        pal = R.palette_for(idx)
        for tf in [(proj / "frontend" / "src" / "lib" / "theme.js"),
                   (proj / "frontend" / "src" / "styles" / "theme.js")]:
            if not tf.exists():
                continue
            tf.write_text(make_theme(pal["brand"], pal["brand_soft"],
                                     pal["accent"], pal["accent_alt"]))
            fixed += 1
    print("theme.js reconstructed:", fixed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
