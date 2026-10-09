/**
 * useAnalytics — React hook for analytics tracking
 *
 * Usage:
 *   const { trackEvent, trackConversion } = useAnalytics();
 *   trackEvent('add_to_cart', { value: 29.99 });
 */

import { useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import analytics from '@/config/analytics';
import { ANALYTICS_CONFIG } from '@/config/analytics-config';

export const CONVERSION_EVENTS = ['purchase', 'add_to_cart', 'begin_checkout', 'sign_up'];

export function useAnalytics() {
  const location = useLocation();

  // Auto-track page views on route change
  useEffect(() => {
    analytics.page(location.pathname + location.search, document.title);
  }, [location]);

  const trackEvent = useCallback((eventName, properties = {}) => {
    analytics.track(eventName, properties);
  }, []);

  const trackConversion = useCallback((eventName, value, currency = 'USD', extra = {}) => {
    analytics.track(eventName, { value, currency, ...extra });
    // Mark as conversion in all providers
    if (window.gtag && ANALYTICS_CONFIG.primary.ga4MeasurementId) {
      window.gtag('event', 'conversion', {
        send_to: ANALYTICS_CONFIG.primary.ga4MeasurementId,
        value,
        currency,
      });
    }
  }, []);

  const identifyUser = useCallback((userId, traits) => {
    analytics.identify(userId, traits);
  }, []);

  return { trackEvent, trackConversion, identifyUser };
}

export default useAnalytics;
