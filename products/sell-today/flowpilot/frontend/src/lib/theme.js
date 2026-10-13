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
