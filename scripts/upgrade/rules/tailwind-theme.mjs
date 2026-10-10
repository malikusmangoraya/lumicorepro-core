/**
 * Rule: tailwind-theme
 *
 * Tailwind's array form of `darkMode` accepts a second element: the selector
 * that switches the dark variant. Adding `[data-theme="dark"]` keeps every
 * existing `.dark` toggle working while letting markup, a query param, or a
 * token build step drive theming. Only the `darkMode` line is touched, so each
 * brand keeps its own colour palette untouched.
 */
export default {
  id: 'tailwind-theme',
  version: '1.0.0',
  title: 'dark: variants respond to [data-theme="dark"] as well as .dark',
  watch: ['tailwind.config.js'],
  plan(ctx) {
    const config = ctx.get('tailwind.config.js');
    if (config === null) {
      ctx.note('no tailwind.config.js in this app');
      return [];
    }
    if (/darkMode:\s*\[/.test(config)) return [];

    const next = config.replace(
      /darkMode:\s*'class'\s*,?/,
      "darkMode: ['class', '[data-theme=\"dark\"]'],"
    );
    if (next === config) {
      ctx.note('darkMode is not the plain \'class\' string — left as-is');
      return [];
    }
    return [{ kind: 'update', path: 'tailwind.config.js', content: next }];
  },
};
