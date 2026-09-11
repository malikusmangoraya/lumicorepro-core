/**
 * trackEvent — privacy-first analytics events for Plausible + GA4.
 * No-ops unless analytics is enabled AND the user accepted analytics
 * cookies (cookieConsentUpdated). That keeps the funnel GDPR-clean.
 *
 * Usage:
 *   trackEvent('generate_success', { provider: 'gemini' });
 */
const ENABLED = import.meta.env.VITE_ENABLE_ANALYTICS === 'true' && import.meta.env.PROD;
const PROVIDER = import.meta.env.VITE_ANALYTICS_PROVIDER || 'plausible';

function consentAllows() {
  try {
    const raw = localStorage.getItem('lumicorepro_cookie_consent');
    if (!raw) return false;
    const consent = JSON.parse(raw);
    return Boolean(consent.essential && consent.analytics);
  } catch {
    return false;
  }
}

export function trackEvent(name, props = {}) {
  if (!ENABLED || !consentAllows()) return;

  if (PROVIDER === 'google' && typeof window.gtag === 'function') {
    try {
      window.gtag('event', name, props);
    } catch {
      /* analytics must never break the app */
    }
    return;
  }

  if (typeof window.plausible === 'function') {
    try {
      window.plausible(name, { props });
    } catch {
      /* no-op */
    }
  }
}

export const AnalyticsEvents = {
  SIGNUP: 'signup',
  GENERATE_CLICK: 'generate_click',
  GENERATE_SUCCESS: 'generate_success',
  GENERATE_FAIL: 'generate_fail',
  GENERATE_DAILY_LIMIT: 'generate_daily_limit',
  PAGE_VIEW: 'page_view',
};