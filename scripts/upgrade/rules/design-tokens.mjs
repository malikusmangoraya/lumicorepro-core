/**
 * Rule: design-tokens
 *
 * Makes the token sheet answer to a `data-theme` attribute (programmatic
 * theming, query-param theming, token build steps) and guarantees a
 * keyboard-only focus ring that reads the brand token instead of a hardcoded
 * colour. Both additions are marker-delimited and appended once.
 */
import { appendBlock } from '../util.mjs';

const MARK = '/* ===== LUMI_TOKENS_V8 ===== */';
const END = '/* ===== end LUMI_TOKENS_V8 ===== */';

const BLOCK = `${MARK}
/* Programmatic theming. src/lib/theme.js sets data-theme on <html> alongside
   the .dark class, so a theme can be driven from a query param, a saved
   preference, or a design-token build step — not just the .dark class. */
[data-theme] {
  color-scheme: light;
}
[data-theme='dark'] {
  color-scheme: dark;
}

/* Keyboard-only focus ring (WCAG 2.4.7). Uses the brand token so every app
   inherits its own colour, and never shows on a mouse click. */
:where(a, area, button, input, select, summary, textarea, [tabindex]:not([tabindex='-1'])):focus-visible {
  outline: 2px solid var(--t-primary);
  outline-offset: 2px;
  border-radius: var(--t-radius-md, 0.5rem);
}
${END}`;

export default {
  id: 'design-tokens',
  version: '1.0.0',
  title: 'data-theme token support + token-driven focus ring',
  watch: ['src/index.css'],
  plan(ctx) {
    const css = ctx.get('src/index.css');
    if (css === null) {
      ctx.note('no src/index.css to extend');
      return [];
    }
    if (css.includes(MARK)) return [];
    return [
      {
        kind: 'update',
        path: 'src/index.css',
        content: appendBlock(css, BLOCK),
      },
    ];
  },
};
