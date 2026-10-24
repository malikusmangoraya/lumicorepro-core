/**
 * Resolve the API base URL without making local development depend on a second
 * origin being reachable from the browser.
 *
 * No configured origin → relative `/api`. In development Vite proxies that to
 * Express; in a single-service production deploy (Render/Railway/Fly) the same
 * container answers it. The previous `http://localhost:5000` fallback made an
 * unconfigured production build call the VISITOR's own machine, which can never
 * work, so it was removed.
 *
 * @param {string|undefined} configuredUrl
 * @param {boolean} isDev Kept for backwards compatibility; the result is the
 *   same relative path in both modes when no origin is configured.
 * @returns {string}
 */
export function resolveApiBaseUrl(configuredUrl, isDev = false) {
  const value = configuredUrl?.trim();
  if (!value) return '/api';
  const raw = value;
  return raw.endsWith('/api') ? raw : `${raw.replace(/\/+$/, '')}/api`;
}
