/**
 * analyticsBus — provider-agnostic event bus for conversion tracking.
 * Auto-generated utility — project primitive. Zero dependencies.
 * Use after analytics-config loads: track('purchase', { value: 12.5, currency: 'USD' });
 */
const providers = () =>
  [
    typeof window.gtag === 'function' && window.gtag,
    window.fathom && window.fathom.trackGoal,
    window.mixpanel && window.mixpanel.track,
    window.plausible && window.plausible,
  ].filter(Boolean);

export function track(name, properties = {}) {
  window.dispatchEvent(new CustomEvent('lumicore:analytics', { detail: { name, properties } }));
  providers().forEach((p) => {
    try {
      p('event', name, properties);
    } catch (e) {
      void e;
    }
  });
}

export function trackConversion(name, value, currency = 'USD', extra = {}) {
  return track(name, { value, currency, ...extra });
}

export default { track, trackConversion };
