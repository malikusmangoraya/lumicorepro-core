/**
 * theme.js - dark-canvas default (TRD #3 canvas archetypes).
 * Applies `.dark` on <html> by default, honoring a saved preference, then the
 * operating-system scheme. Runs on import.
 */
(function applyTheme() {
  try {
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    const pref = saved
      ? saved === 'dark'
      : window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.classList.toggle('dark', pref === true || saved === 'dark');
    if (!saved) root.classList.add('dark'); // dark default per design tokens
  } catch (e) {
    void e;
  }
})();

export default function theme() {
  return document.documentElement.classList.contains('dark');
}

export const designTokens = `/* ===== APP_DESIGN_TOKENS_V7 ===== */

:root {{
  --t-brand: #be662c;
  --t-brand-soft: #eaded5;
  --t-surface-lux-bg: #0b0c10;
  --t-surface-lux-2: #14161c;
  --t-surface-lux-3: #1d2026;
  --t-glass-blur: 6px;
  --t-glass-opacity: 0.55;
  --t-accent-gold: #d18d60;
  --t-accent-cyan: #824116;
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
}}
/* ===== end APP_DESIGN_TOKENS_V7 ===== */`;

export const lumiMotionCss = `/* ===== LUMI_MOTION_V7 ===== */

[data-reveal] {{ opacity: 0; transform: translateY(18px); transition: opacity 0.6s ease, transform 0.6s ease; }}
[data-reveal].visible {{ opacity: 1; transform: translateY(0); }}
.card-lift {{ transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), box-shadow 0.4s ease; }}
.card-lift:hover {{ transform: translateY(-6px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }}
.shimmer {{ background: linear-gradient(110deg, transparent 33%, rgba(255,255,255,0.08) 50%, transparent 67%); background-size: 200% 100%; animation: shimmer 2s infinite; }}
@keyframes shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}
/* ===== end LUMI_MOTION_V7 ===== */`;
