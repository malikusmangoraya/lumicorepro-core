/**
 * Service worker registration.
 *
 * The URL and the scope are both taken from Vite's BASE_URL, because these
 * apps are served from a GitHub Pages subpath: BASE_URL is `/<repo>/` in the
 * Pages workflow. Registering `/sw.js` instead would request the apex domain,
 * where nothing answers, and the default `/` scope would claim control of every
 * repository on that Pages host rather than this one.
 *
 * Registration is skipped outside production on purpose: a cached shell during
 * development serves yesterday's bundle and makes every change look like it did
 * not apply. The worker itself clears old caches on activate, so a redeploy
 * reaches returning visitors without a manual refresh.
 */
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  const base = import.meta.env.BASE_URL || './';
  // './' (a relative base) has to be resolved against the current document;
  // an absolute base such as '/<repo>/' is already a usable path prefix.
  const scope = base.startsWith('.')
    ? new URL(base, document.baseURI).href
    : new URL(base, document.location.origin).href;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(new URL('sw.js', scope).href, { scope })
      .catch(() => {
        // A failed registration must never break the app; caching is an
        // enhancement, not a requirement.
      });
  });
}
