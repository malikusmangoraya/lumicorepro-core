/**
 * Rule: theme-controller
 *
 * Replaces the fire-and-forget IIFE in src/lib/theme.js with a controller that
 *
 *  - applies BOTH `.dark` (Tailwind `dark:` variants) and `data-theme`
 *    (token selectors), so the two theming mechanisms can no longer drift;
 *  - resolves the theme from `?theme=dark|light|auto` first, then the saved
 *    preference, then the app's dark-first default;
 *  - exposes setTheme / toggleTheme / applyTheme so UI can switch themes
 *    programmatically instead of reloading;
 *  - follows the OS only while the visitor has not chosen explicitly.
 *
 * The brand-owned `designTokens` / `lumiMotionCss` string exports that follow
 * the controller are detected and re-emitted verbatim — they differ per brand
 * and must never be rewritten by a codemod.
 */
const MARK = 'LUMI_THEME_CONTROLLER_V8';
const TAIL_ANCHORS = ['export const designTokens', 'export const lumiMotionCss'];

const CONTROLLER = `/**
 * ${MARK}
 *
 * Applies the resolved theme to <html> as BOTH the \`.dark\` class (Tailwind
 * \`dark:\` variants) and \`data-theme\` (design-token and CSS selectors), so the
 * two mechanisms cannot drift apart.
 *
 * Resolution order: \`?theme=\` in the URL > saved preference > brand default.
 * These canvases are dark-first, which is why the fallback is \`dark\`.
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
`;

export default {
  id: 'theme-controller',
  version: '1.0.0',
  title: 'theme.js: .dark + data-theme, ?theme= param, programmatic API',
  watch: ['src/lib/theme.js'],
  plan(ctx) {
    const source = ctx.get('src/lib/theme.js');
    if (source === null) {
      ctx.note('this app has no src/lib/theme.js');
      return [];
    }
    if (source.includes(MARK)) return [];

    const tailAt = TAIL_ANCHORS.map((anchor) => source.indexOf(anchor))
      .filter((index) => index !== -1)
      .sort((a, b) => a - b)[0];

    if (tailAt === undefined) {
      // No brand-owned exports to carry over: replace the whole module.
      ctx.note('previous theme.js is replaced (no brand token exports to preserve)');
      return [{ kind: 'update', path: 'src/lib/theme.js', content: CONTROLLER }];
    }

    const tail = source.slice(tailAt).replace(/\s*$/, '');
    return [
      {
        kind: 'update',
        path: 'src/lib/theme.js',
        content: `${CONTROLLER}\n${tail}\n`,
      },
    ];
  },
};
