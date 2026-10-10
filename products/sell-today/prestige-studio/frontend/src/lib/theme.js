/**
 * LUMI_THEME_CONTROLLER_V8
 *
 * Applies the resolved theme to <html> as BOTH the `.dark` class (Tailwind
 * `dark:` variants) and `data-theme` (design-token and CSS selectors), so the
 * two mechanisms cannot drift apart.
 *
 * Resolution order: `?theme=` in the URL > saved preference > brand default.
 * These canvases are dark-first, which is why the fallback is `dark`.
 */
export const THEME_STORAGE_KEY = 'theme';
export const THEMES = ['dark', 'light', 'auto'];

export function getThemePreference() {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('theme');
    if (THEMES.includes(fromUrl)) return fromUrl;
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (THEMES.includes(saved)) return saved;
  } catch (error) {
    void error;
  }
  return 'dark';
}

export function resolveTheme(preference = getThemePreference()) {
  if (preference === 'dark' || preference === 'light') return preference;
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch (error) {
    void error;
  }
  return 'dark';
}

export function applyTheme(preference = getThemePreference()) {
  const resolved = resolveTheme(preference);
  const root = document.documentElement;
  root.classList.toggle('dark', resolved === 'dark');
  root.setAttribute('data-theme', resolved);
  root.setAttribute('data-theme-preference', preference);
  root.style.colorScheme = resolved;
  return resolved;
}

export function setTheme(preference) {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch (error) {
    void error;
  }
  return applyTheme(preference);
}

export function toggleTheme() {
  return setTheme(resolveTheme() === 'dark' ? 'light' : 'dark');
}

export default function theme() {
  return document.documentElement.getAttribute('data-theme') !== 'light';
}

applyTheme();

/* Follow the operating system only while the visitor has made no choice. */
try {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (getThemePreference() === 'auto') applyTheme('auto');
  });
} catch (error) {
  void error;
}

export const designTokens = `/* ===== APP_DESIGN_TOKENS_V7 ===== */

:root {{
  --t-brand: #88be2c;
  --t-brand-soft: #e3ead5;
  --t-surface-lux-bg: #0b0c10;
  --t-surface-lux-2: #14161c;
  --t-surface-lux-3: #1d2026;
  --t-glass-blur: 6px;
  --t-glass-opacity: 0.55;
  --t-accent-gold: #a7d160;
  --t-accent-cyan: #5a8216;
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
