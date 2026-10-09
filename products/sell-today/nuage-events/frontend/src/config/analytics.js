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
  /** Account created */
  sign_up: (params) => track('sign_up', params),
  /** User logged in */
  login: (params) => track('login', params),
  /** Free trial started */
  trial_started: (params) => track('trial_started', params),
  /** Trial → paid conversion */
  trial_converted: (params) => track('trial_converted', params),
  /** Pricing page plan click */
  plan_selected: (params) => track('plan_selected', params),
  /** Subscription confirmed */
  subscription_created: (params) => track('subscription_created', params),
  /** Cancellation confirmed */
  subscription_cancelled: (params) => track('subscription_cancelled', params),
  /** Key feature interaction */
  feature_used: (params) => track('feature_used', params),
};

export default analytics;

export { analytics as analytics };
