/**
 * Sentry error tracking (frontend).
 *
 * The SDK is loaded on demand: without VITE_SENTRY_DSN configured, not a
 * single byte of @sentry/react is fetched. A static import here put the
 * whole SDK (~30 KB gzip) on the initial payload — the 2026-10 regression
 * that broke the 200 KB first-paint gate (`npm run size`, AGENTS.md §7).
 * With a DSN set, the SDK is fetched once at boot and captures unhandled
 * errors, failed API responses (5xx), and slow navigations — the frontend
 * half of the observability story (backend Sentry lives in backend/server.js).
 *
 * Every function is async and safe to call fire-and-forget: before the SDK
 * has loaded (or when no DSN is set) they resolve to no-ops.
 */

let sdkPromise = null;
let enabled = false;

const dsn = () => import.meta.env.VITE_SENTRY_DSN || '';

function loadSdk() {
  if (!sdkPromise) {
    sdkPromise = import('@sentry/react');
  }
  return sdkPromise;
}

/** Call at boot. Resolves true only when a DSN is configured and init ran. */
export async function initSentry() {
  if (enabled) return true;
  if (!dsn()) return false;
  const Sentry = await loadSdk();
  Sentry.init({
    dsn: dsn(),
    environment: import.meta.env.VITE_ENV || import.meta.env.MODE || 'development',
    release: `lumicorepro@${import.meta.env.VITE_APP_VERSION || '7.13.0'}`,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.2,
    beforeSend(event) {
      // Never ship potential credentials in breadcrumbs/URLs.
      if (event.request?.url) {
        event.request.url = event.request.url.replace(
          /([?&])(api_key|token)=[^&]*/gi,
          '$1$2=[redacted]'
        );
      }
      return event;
    },
  });
  enabled = true;
  return true;
}

/** Report a caught error. Resolves null when tracking is off. */
export async function captureError(err, context = {}) {
  if (!dsn() || !enabled) return null;
  const Sentry = await loadSdk();
  return Sentry.captureException(err, { extra: context });
}

/** Identify the current user (or clear on logout). */
export async function setSentryUser(user) {
  if (!dsn() || !enabled) return;
  const Sentry = await loadSdk();
  Sentry.setUser(user ? { id: String(user.id), email: user.email } : null);
}

/**
 * Tag the current Sentry scope with the distributed trace id returned by
 * the API (X-Trace-Id). Support can then jump from a user complaint to
 * the exact backend/FastAPI trace.
 */
export async function setTraceId(traceId) {
  if (!dsn() || !enabled || !traceId) return;
  const Sentry = await loadSdk();
  Sentry.setTag('trace_id', String(traceId));
}
