"""UI/UX Architecture & Design System Design Tokens (TRD #3).

Injects a semantic, token-driven design system into every generated project:

1. Semantic Color Mapping
   - Canvas archetypes: Dark default (slate-950 / slate-50), Light default
     (white / slate-900) — driven by CSS variables toggled under `.dark`.
   - Brand accents: pure-functional semantic mappings `primary`, `secondary`,
     `accent`, `muted` wired through tailwind.config.js as
     `rgb(var(--t-*) / <alpha-value>)` so opacity modifiers + dark mode work
     natively. Explicit raw hex in components is barred → conformance scan on
     `frontend/src/components/**` flags violations.

2. Component Layout & Structural Fidelity
   - Glassmorphism spec: `.glass-md` utility == `backdrop-blur-md
     bg-white/70 dark:bg-slate-900/70 border border-white/10`, plus a `GlassCard`
     React component implementing that exact class combo.
   - Motion profiles: `motionPresets.js` frozen duration/easing metrics
     (instant/fast/standard/expressive) + `MotionWrapper` (framer-motion) so
     transition states stay cohesive.

Outputs: token CSS in index.css, frontend/tailwind.config.js (when missing),
src/lib/theme.js (dark default), GlassCard, motionPresets + MotionWrapper,
DESIGN-TOKENS.md, and a design-system conformance report. Idempotent via marker
`LUMICORE_DESIGN`.
"""
import os
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger
from utils.file_manager import FileManager

_MARKER = "LUMICORE_DESIGN"

# Semantic RGB token triplets (space-separated for Tailwind <alpha-value>).
_TOKENS_LIGHT = {
    "t-canvas": "255 255 255",
    "t-canvas-text": "15 23 42",
    "t-primary": "14 165 233",
    "t-secondary": "109 40 217",
    "t-accent": "245 158 11",
    "t-muted": "100 116 139",
    "t-glass-bg": "255 255 255",
    "t-glass-border": "255 255 255",
}
_TOKENS_DARK = {
    "t-canvas": "2 6 23",
    "t-canvas-text": "248 250 252",
    "t-primary": "34 211 238",
    "t-secondary": "167 139 250",
    "t-accent": "251 191 36",
    "t-muted": "148 163 184",
    "t-glass-bg": "15 23 42",
    "t-glass-border": "255 255 255",
}

_TAILWIND_CONFIG = """/**
 * Design Tokens — semantic color mapping (TRD #3).
 * Tokens are RGB triplets resolved via `rgb(var(--t-*) / <alpha-value>)`,
 * so `bg-primary/70`, `dark:bg-secondary` and every opacity modifier work.
 * `darkMode: 'class'` lets `src/lib/theme.js` pin the dark default.
 */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'rgb(var(--t-canvas) / <alpha-value>)',
        primary: 'rgb(var(--t-primary) / <alpha-value>)',
        secondary: 'rgb(var(--t-secondary) / <alpha-value>)',
        accent: 'rgb(var(--t-accent) / <alpha-value>)',
        muted: 'rgb(var(--t-muted) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
"""

_TOKEN_CSS = """
/* ── Design Tokens: semantic color mapping (TRD #3) ─────────────────────── */
/* LUMICORE_DESIGN -- tokens */
:root {
  --t-canvas: 255 255 255;
  --t-canvas-text: 15 23 42;
  --t-primary: 14 165 233;
  --t-secondary: 109 40 217;
  --t-accent: 245 158 11;
  --t-muted: 100 116 139;
  --t-glass-bg: 255 255 255;
  --t-glass-border: 255 255 255;
}
.dark {
  --t-canvas: 2 6 23;
  --t-canvas-text: 248 250 252;
  --t-primary: 34 211 238;
  --t-secondary: 167 139 250;
  --t-accent: 251 191 36;
  --t-muted: 148 163 184;
  --t-glass-bg: 15 23 42;
  --t-glass-border: 255 255 255;
}

/* Canvas archetypes (dark default per TRD). */
@layer base {
  body { background-color: var(--t-canvas); color: var(--t-canvas-text); }
  /* lumicore-design-font */
}
/* lumicore-design: glassmorphism */
@layer utilities {
  .glass-md {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    background-color: rgb(var(--t-glass-bg) / 0.70);
    border: 1px solid rgb(var(--t-glass-border) / 0.10);
  }
}
/* ── End Design Tokens ─────────────────────────────────────────────────── */
"""

_THEME_JS = """/**
 * theme.js — dark-canvas default (TRD #3 canvas archetypes).
 * Applies `.dark` on <html> by default, honoring a saved preference, then the
 * operating-system scheme. Runs on import.
 */
(function applyTheme() {
  try {
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    const pref = saved
      ? saved === 'dark'
      : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    root.classList.toggle('dark', pref === true || saved === 'dark');
    if (!saved) root.classList.add('dark'); // dark default per design tokens
  } catch (e) {
    /* noop */
  }
})();

export default function theme() { return document.documentElement.classList.contains('dark'); }
"""


class DesignSystemInjector:
    """Injects the token-driven design system + layout fidelity layer."""

    def generate(self, spec: Dict[str, Any], project_dir: str, mode: str = "") -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "runtime_mode": spec.get("runtime_mode", "transactional"),
            "artifacts": [],
        }
        report["tailwind_config"] = self._ensure_tailwind_config(project_dir)
        report["tokens_css"] = self._append_token_css(project_dir)
        report["glass"] = self._inject_glass(project_dir)
        report["motion"] = self._inject_motion_profiles(project_dir)
        report["theme"] = self._inject_theme(project_dir)
        report["conformance"] = self._scan_component_hex(project_dir)
        report["doc"] = self._write_design_tokens_doc(project_dir, spec, report)
        report["artifacts"] = [report["doc"]] + self._artifact_files(report)

        agent_logger.info(
            f"DesignSystem: tokens={report['tokens_css'].get('status')} "
            f"theme={report['theme'].get('status')} "
            f"raw_hex={report['conformance'].get('raw_hex_count', 0)}"
        )
        return report

    # ── 1a. tailwind.config.js (semantic color contract) ───────────────────
    def _ensure_tailwind_config(self, project_dir: str) -> Dict[str, Any]:
        cfg = os.path.join(project_dir, "frontend", "tailwind.config.js")
        if os.path.isfile(cfg):
            return {"status": "skip", "reason": "tailwind.config.js exists"}
        FileManager.write_file(cfg, _TAILWIND_CONFIG)
        return {"status": "ok", "file": "frontend/tailwind.config.js"}

    # ── 1b. Semantic token CSS (canvas archetypes + glass spec) ─────────────
    def _append_token_css(self, project_dir: str) -> Dict[str, Any]:
        css_path = os.path.join(project_dir, "frontend", "src", "index.css")
        if not os.path.isfile(css_path):
            return {"status": "skip", "reason": "index.css missing"}
        existing = FileManager.read_file(css_path)
        if _MARKER in existing:
            return {"status": "skip", "reason": "already-present"}
        FileManager.write_file(css_path, existing.rstrip("\n") + "\n" + _TOKEN_CSS)
        return {"status": "ok", "file": "frontend/src/index.css"}

    # ── 2a. Glassmorphism spec component ───────────────────────────────────
    def _inject_glass(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"status": "skip", "reason": "frontend/src missing"}
        path = self._write(
            src, "components", "common", "GlassCard.jsx",
            """/**
 * GlassCard — premium glassmorphism container (TRD #3 glass spec).
 * Exact spec: `backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border
 * border-white/10`. Use the token utility `.glass-md` for the same effect
 * through the design-token pipeline.
 */
export default function GlassCard({ className = '', children, ...props }) {
  return (
    <div
      {...props}
      className={`backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border border-white/10 ${className}`}
    >
      {children}
    </div>
  );
}
""",
        )
        return {"status": "ok", "component": path}

    # ── 2b. Motion profiles (cohesive Framer durations) ────────────────────
    def _inject_motion_profiles(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"status": "skip", "reason": "frontend/src missing"}
        presets = self._write(
            src, "lib", "motionPresets.js",
            """/**
 * motionPresets — cohesive transition metrics (TRD #3 motion profiles).
 * Frozen duration/easing tokens; every animated wrapper reads from here so
 * transition states stay consistent across the product.
 */
export const DURATIONS = {
  instant: 80,
  fast: 140,
  standard: 240,
  expressive: 420,
};

export const EASING = [0.22, 1, 0.36, 1];

export const PRESETS = {
  fade: { hidden: { opacity: 0 }, show: { opacity: 1 } },
  'slide-up': { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } },
  scale: { hidden: { opacity: 0, scale: 0.96 }, show: { opacity: 1, scale: 1 } },
};

export default { DURATIONS, EASING, PRESETS };
""",
        )
        wrapper = self._write(
            src, "components", "motion", "MotionWrapper.jsx",
            """/**
 * MotionWrapper — Framer Motion wrapper configuration (TRD #3 motion profiles).
 * Cohesive duration/easing come from `motionPresets.js`.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { DURATIONS, EASING, PRESETS } from '../../lib/motionPresets';

export default function MotionWrapper({
  variant = 'slide-up',
  duration = 'standard',
  className = '',
  children,
  ...props
}) {
  const reduce = useReducedMotion();
  const preset = PRESETS[variant] || PRESETS['slide-up'];
  return (
    <motion.div
      className={className}
      initial={reduce ? false : 'hidden'}
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      variants={preset}
      transition={{ duration: DURATIONS[duration] ?? DURATIONS.standard, ease: EASING }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
""",
        )
        return {"status": "ok", "presets": presets, "wrapper": wrapper}

    # ── Dark-canvas default (theme.js + App import) ────────────────────────
    def _inject_theme(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"status": "skip", "reason": "frontend/src missing"}
        theme_path = self._write(src, "lib", "theme.js", _THEME_JS)
        app_path = os.path.join(src, "App.jsx")
        attached = None
        if os.path.isfile(app_path):
            content = FileManager.read_file(app_path)
            if _MARKER not in content and "import './lib/theme'" not in content:
                import_line = f"import './lib/theme'; // {_MARKER}\n"
                if "import " in content:
                    idx = content.index("import ")
                    nl = content.index("\n", idx)
                    content = content[: nl + 1] + import_line + content[nl + 1:]
                else:
                    content = import_line + content
                FileManager.write_file(app_path, content)
                attached = app_path
        return {"status": "ok", "theme": theme_path, "app_import": bool(attached)}

    # ── Conformance: raw hex barred in components ─────────────────────────
    def _scan_component_hex(self, project_dir: str) -> Dict[str, Any]:
        comp_dir = os.path.join(project_dir, "frontend", "src", "components")
        if not os.path.isdir(comp_dir):
            return {"status": "skip", "reason": "components dir missing", "pass": True}
        import re

        pattern = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
        hits: List[str] = []
        for root, _, files in os.walk(comp_dir):
            for fname in files:
                if not fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                    continue
                path = os.path.join(root, fname)
                for lineno, line in enumerate(
                    FileManager.read_file(path).splitlines(), start=1
                ):
                    if pattern.search(line):
                        hits.append(f"{os.path.relpath(path, comp_dir)}:{lineno}")
        return {
            "status": "pass" if not hits else "violations",
            "pass": not bool(hits),
            "raw_hex_count": len(hits),
            "violations": hits[:20],
        }

    # ── Design tokens documentation ────────────────────────────────────────
    def _write_design_tokens_doc(self, project_dir: str, spec: Dict[str, Any], report: Dict[str, Any]) -> str:
        project = spec.get("project_name", "This project")
        body = f"""# Design System & Design Tokens — {project}

> Semantic, token-driven UI contract (TRD #3). Raw hex in components is barred —
> always reference the semantic mapping below.

## 1. Semantic Color Mapping

| Token | Light (`:root`) | Dark (`.dark` default) | Role |
|-------|----------------|------------------------|------|
| `primary` | rgb(14 165 233) | rgb(34 211 238) | brand primary action |
| `secondary` | rgb(109 40 217) | rgb(167 139 250) | complementary action |
| `accent` | rgb(245 158 11) | rgb(251 191 36) | highlights / callouts |
| `muted` | rgb(100 116 139) | rgb(148 163 184) | secondary text, disabled |
| `canvas` | `#ffffff` | `#020617` (slate-950) | page background |
| text | `#0f172a` (slate-900) | `#f8fafc` (slate-50) | default foreground |

- Canvas archetypes: **dark default** (`bg-canvas` → slate-950 / text slate-50),
  light alternative (white / slate-900). Toggled by `src/lib/theme.js` `.dark`
  class (honors saved preference + OS scheme).
- Usage: `bg-primary`, `text-secondary`, `border-accent`, opacity modifiers work
  e.g. `bg-primary/70`, `dark:bg-primary`. Tokens live in `tailwind.config.js`
  (`rgb(var(--t-*) / <alpha-value>)`) and `src/index.css` (`--t-*` variables).

## 2. Glassmorphism Spec
- Token utility: `.glass-md` == `backdrop-blur-md` + `bg-white/70`
  (`dark:` `bg-slate-900/70`) + `border border-white/10`.
- React component: `GlassCard` (`src/components/common/GlassCard.jsx`) implements
  the exact class combo. Use for premium containers (cards, modals, nav bars).

## 3. Motion Profiles (cohesive durations)
`src/lib/motionPresets.js` — every transition reads from the frozen `DURATIONS`
metric table (instant 80ms / fast 140ms / standard 240ms / expressive 420ms)
plus the shared `EASING` cubic-bezier(0.22, 1, 0.36, 1):

| Profile | Duration | Easing |
|---------|----------|--------|
| instant | 80ms | cubic-bezier(0.22, 1, 0.36, 1) |
| fast | 140ms | cubic-bezier(0.22, 1, 0.36, 1) |
| standard | 240ms | cubic-bezier(0.22, 1, 0.36, 1) |
| expressive | 420ms | cubic-bezier(0.22, 1, 0.36, 1) |

Wrapper: `MotionWrapper` (`src/components/motion/MotionWrapper.jsx`) with
variants `fade` / `slide-up` / `scale`; respects `prefers-reduced-motion`.

## Conformance
- Raw hex scan (components): {report["conformance"].get("raw_hex_count", "n/a")} violation(s) —
  {'PASS' if report["conformance"].get("pass", True) else 'FIX: move colors into tokens'}.
- Tailwind config: {report["tailwind_config"].get("status", "n/a")}.
- Token CSS: {report["tokens_css"].get("status", "n/a")}.
- Glass spec: {report["glass"].get("status", "n/a")}.
- Motion profiles: {report["motion"].get("status", "n/a")}.
- Dark default theme: {report["theme"].get("status", "n/a")}.
"""
        path = os.path.join(project_dir, "DESIGN-TOKENS.md")
        FileManager.write_file(path, body)
        return path

    @staticmethod
    def _artifact_files(report: Dict[str, Any]) -> List[str]:
        out: List[str] = []
        if report["tailwind_config"].get("file"):
            out.append(report["tailwind_config"]["file"])
        if report["tokens_css"].get("file"):
            out.append(report["tokens_css"]["file"])
        if report["glass"].get("component"):
            out.append(report["glass"]["component"])
        if report["motion"].get("presets"):
            out.append(report["motion"]["presets"])
            out.append(report["motion"]["wrapper"])
        if report["theme"].get("theme"):
            out.append(report["theme"]["theme"])
        return out

    def _write(self, src: str, *rel_pos: str) -> str:
        if len(rel_pos) < 2:
            raise ValueError("_write requires at least (dir, filename, content)")
        content = rel_pos[-1]
        target = os.path.join(src, *rel_pos[:-1])
        FileManager.ensure_dir(os.path.dirname(target))
        FileManager.write_file(target, content)
        return target.replace("\\", "/")


design_system_injector = DesignSystemInjector()