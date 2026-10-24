import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const CONSENT_KEY = 'lumicorepro_cookie_consent';

async function loadAnalytics({ enabled = true, provider = 'plausible' } = {}) {
  vi.resetModules();
  vi.stubEnv('VITE_ENABLE_ANALYTICS', enabled ? 'true' : 'false');
  vi.stubEnv('VITE_ANALYTICS_PROVIDER', provider);
  if (enabled) vi.stubEnv('PROD', 'true');
  return import('../../utils/analytics');
}

function grantConsent() {
  localStorage.setItem(CONSENT_KEY, JSON.stringify({ essential: true, analytics: true }));
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe('trackEvent', () => {
  it('does nothing when analytics is not enabled in the environment', async () => {
    grantConsent();
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);

    const { trackEvent } = await loadAnalytics({ enabled: false });
    trackEvent('generate_click', { provider: 'gemini' });

    expect(plausible).not.toHaveBeenCalled();
  });

  it('does nothing without cookie consent', async () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);

    const { trackEvent } = await loadAnalytics();
    trackEvent('generate_click');

    expect(plausible).not.toHaveBeenCalled();
  });

  it('requires both essential and analytics consent', async () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ essential: true, analytics: false }));

    const { trackEvent } = await loadAnalytics();
    trackEvent('generate_click');

    expect(plausible).not.toHaveBeenCalled();
  });

  it('sends a Plausible event when analytics is enabled and consented', async () => {
    grantConsent();
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);

    const { trackEvent } = await loadAnalytics();
    trackEvent('generate_success', { provider: 'gemini' });

    expect(plausible).toHaveBeenCalledWith('generate_success', {
      props: { provider: 'gemini' },
    });
  });

  it('routes events to gtag when the Google provider is selected', async () => {
    grantConsent();
    const gtag = vi.fn();
    const plausible = vi.fn();
    vi.stubGlobal('gtag', gtag);
    vi.stubGlobal('plausible', plausible);

    const { trackEvent } = await loadAnalytics({ provider: 'google' });
    trackEvent('signup', { plan: 'pro' });

    expect(gtag).toHaveBeenCalledWith('event', 'signup', { plan: 'pro' });
    expect(plausible).not.toHaveBeenCalled();
  });

  it('never throws on corrupt consent or a failing analytics bridge', async () => {
    localStorage.setItem(CONSENT_KEY, '{not-json');
    const { trackEvent } = await loadAnalytics();
    expect(() => trackEvent('page_view')).not.toThrow();

    grantConsent();
    vi.stubGlobal('plausible', () => {
      throw new Error('script blocked');
    });
    const { trackEvent: trackWithConsent } = await loadAnalytics();
    expect(() => trackWithConsent('page_view')).not.toThrow();
  });
});

describe('AnalyticsEvents', () => {
  it('exposes the documented event names', async () => {
    const { AnalyticsEvents } = await loadAnalytics();
    expect(AnalyticsEvents).toMatchObject({
      SIGNUP: 'signup',
      GENERATE_CLICK: 'generate_click',
      GENERATE_SUCCESS: 'generate_success',
      GENERATE_FAIL: 'generate_fail',
      GENERATE_DAILY_LIMIT: 'generate_daily_limit',
      PAGE_VIEW: 'page_view',
    });
  });
});
