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
  /** Products page load */
  view_item_list: (params) => track('view_item_list', params),
  /** Product detail page load */
  view_item: (params) => track('view_item', params),
  /** Add to cart button click */
  add_to_cart: (params) => track('add_to_cart', params),
  /** Remove from cart */
  remove_from_cart: (params) => track('remove_from_cart', params),
  /** Cart page view */
  view_cart: (params) => track('view_cart', params),
  /** Checkout step 1 */
  begin_checkout: (params) => track('begin_checkout', params),
  /** Payment info entered */
  add_payment_info: (params) => track('add_payment_info', params),
  /** Order confirmed */
  purchase: (params) => track('purchase', params),
};

export default analytics;

export { analytics as analytics };
