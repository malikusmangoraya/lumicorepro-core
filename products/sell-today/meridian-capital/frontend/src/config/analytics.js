/**
 * Analytics Abstraction Layer — Provider-agnostic tracking API
 *
 * Usage:
 *   import analytics from '@/config/analytics';
 *   analytics.track('purchase', { value: 99.99, currency: 'USD' });
 *   analytics.page('/products');
 *   analytics.identify(userId, { email, plan });
 */

import { ANALYTICS_CONFIG, EVENTS } from './analytics-config';

// ── Core tracking functions ────────────────────────────────────────────────
export function track(eventName, properties = {}) {
  if (ANALYTICS_CONFIG.options.respectDoNotTrack && navigator.doNotTrack === '1') return;

  const cfg = ANALYTICS_CONFIG.primary;
  const props = { ...properties, timestamp: new Date().toISOString() };

  // GA4
  if (cfg.ga4MeasurementId && window.gtag) {
    window.gtag('event', eventName, props);
  }

  // PostHog
  if (cfg.posthogKey && window.__posthog) {
    window.__posthog.capture(eventName, props);
  }

  // Plausible
  if (cfg.plausibleDomain && window.plausible) {
    window.plausible(eventName, { props });
  }

  // Mixpanel
  if (cfg.mixpanelToken && window.mixpanel) {
    window.mixpanel.track(eventName, props);
  }

  // Fathom
  if (cfg.fathomSiteId && window.fathom) {
    window.fathom.trackEvent(eventName, { _value: properties.value || 0 });
  }

  if (ANALYTICS_CONFIG.options.debug) {
    console.log(`[Analytics] ${eventName}`, props);
  }
}

export function page(url, title) {
  const cfg = ANALYTICS_CONFIG.primary;
  if (cfg.ga4MeasurementId && window.gtag) {
    window.gtag('event', 'page_view', { page_location: url, page_title: title });
  }
  if (cfg.plausibleDomain && window.plausible) {
    window.plausible('pageview');
  }
  if (cfg.posthogKey && window.__posthog) {
    window.__posthog.capture('$pageview', { $current_url: url });
  }
}

export function identify(userId, traits = {}) {
  const cfg = ANALYTICS_CONFIG.primary;
  if (cfg.posthogKey && window.__posthog) {
    window.__posthog.identify(userId, traits);
  }
  if (cfg.mixpanelToken && window.mixpanel) {
    window.mixpanel.identify(userId);
    window.mixpanel.people.set(traits);
  }
  if (cfg.ga4MeasurementId && window.gtag) {
    window.gtag('set', 'user_properties', traits);
  }
}

export function reset() {
  if (window.__posthog) window.__posthog.reset();
  if (window.mixpanel) window.mixpanel.reset();
}

// ── Typed event helpers ────────────────────────────────────────────────────
const analytics = {
  track,
  page,
  identify,
  reset,
  /** Page load */
  page_view: (params) => track('page_view', params),
  /** 25/50/75/90% scroll depth */
  scroll: (params) => track('scroll', params),
  /** Link/button click */
  click: (params) => track('click', params),
  /** Site search */
  search: (params) => track('search', params),
  /** Contact form submitted */
  contact_submitted: (params) => track('contact_submitted', params),
  /** Newsletter/account signup */
  sign_up: (params) => track('sign_up', params),
  /** Social share button click */
  share: (params) => track('share', params),
};

export default analytics;

export { analytics as analytics };
