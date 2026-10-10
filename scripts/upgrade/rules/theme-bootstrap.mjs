/**
 * Rule: theme-bootstrap
 *
 * index.html paints before the JS bundle runs, so a dark-first app flashes the
 * light token sheet on every cold load. A tiny inline script in <head> applies
 * the same resolution order as src/lib/theme.js before first paint.
 *
 * Skipped when the document already declares a Content-Security-Policy (an
 * inline script would be blocked there) or already carries the marker.
 */
const MARK = 'LUMI_THEME_BOOTSTRAP_V8';

const SCRIPT = `    <!-- ${MARK} — applies the saved theme before first paint -->
    <script>
      (function () {
        try {
          var themes = ['dark', 'light', 'auto'];
          var query = new URLSearchParams(window.location.search).get('theme');
          var saved = window.localStorage.getItem('theme');
          var preference =
            themes.indexOf(query) !== -1 ? query : themes.indexOf(saved) !== -1 ? saved : 'dark';
          var dark =
            preference === 'dark' ||
            (preference === 'auto' &&
              window.matchMedia('(prefers-color-scheme: dark)').matches);
          var root = document.documentElement;
          root.classList.toggle('dark', dark);
          root.setAttribute('data-theme', dark ? 'dark' : 'light');
          root.setAttribute('data-theme-preference', preference);
          root.style.colorScheme = dark ? 'dark' : 'light';
        } catch (error) {
          /* the stylesheet default still applies */
        }
      })();
    </script>`;

export default {
  id: 'theme-bootstrap',
  version: '1.0.0',
  title: 'index.html: pre-paint theme bootstrap (no dark-first flash)',
  watch: ['index.html'],
  plan(ctx) {
    const html = ctx.get('index.html');
    if (html === null) {
      ctx.note('no index.html in this app');
      return [];
    }
    if (html.includes(MARK)) return [];
    if (/Content-Security-Policy/i.test(html)) {
      ctx.note('Content-Security-Policy present — inline bootstrap skipped');
      return [];
    }
    if (!html.includes('</head>')) {
      ctx.note('no </head> anchor found — skipped');
      return [];
    }

    const at = html.indexOf('</head>');
    const head = html.slice(0, at).replace(/\s*$/, '');
    const rest = html.slice(at);
    const eol = html.includes('\r\n') ? '\r\n' : '\n';
    const block = eol === '\r\n' ? SCRIPT.replace(/\n/g, '\r\n') : SCRIPT;

    return [
      {
        kind: 'update',
        path: 'index.html',
        content: `${head}${eol}${block}${eol}${eol}${rest}`,
      },
    ];
  },
};
