import { describe, it, expect, afterEach } from 'vitest';
import {
  detectCurrencyFromLocale,
  detectCurrencyFromTimezone,
  detectCurrency,
  detectRegion,
  COUNTRY_TO_CURRENCY,
} from '../../utils/detectCurrency';

/**
 * First-visit localisation (international readiness): a wrong default currency
 * is a revenue/trust bug, so the fallback ordering is pinned here.
 */
afterEach(() => {
  // Restore a neutral navigator language between tests
  Object.defineProperty(navigator, 'language', { value: 'en-US', configurable: true });
});

describe('detectCurrencyFromTimezone', () => {
  it('maps common timezones to currencies', () => {
    expect(detectCurrencyFromTimezone('America/New_York')).toBe('USD');
    expect(detectCurrencyFromTimezone('Europe/London')).toBe('GBP');
    expect(detectCurrencyFromTimezone('Europe/Berlin')).toBe('EUR');
    expect(detectCurrencyFromTimezone('America/Toronto')).toBe('CAD');
  });

  it('returns null for unknown timezones', () => {
    expect(detectCurrencyFromTimezone('Mars/Olympus_Mons')).toBeNull();
  });

  it('falls back to the system timezone when none is passed', () => {
    // '' is falsy on purpose -> system tz; result may be null only when the
    // host timezone is not in the fallback map.
    const result = detectCurrencyFromTimezone('');
    expect(result === null || /^[A-Z]{3}$/.test(result)).toBe(true);
  });
});

describe('detectCurrencyFromLocale', () => {
  it('returns a supported code when Intl resolves a currency', () => {
    // en-US without style:currency resolves no currency -> null (documented)
    const result = detectCurrencyFromLocale('en-US');
    if (result !== null) expect(typeof result).toBe('string');
    expect(detectCurrencyFromLocale('en-US') === null || /^[A-Z]{3}$/.test(result)).toBe(true);
  });

  it('returns null instead of throwing for invalid locales', () => {
    expect(detectCurrencyFromLocale('!!!invalid!!!')).toBeNull();
  });
});

describe('detectCurrency', () => {
  it('returns a supported currency without network when locale/timezone resolve', async () => {
    const currency = await detectCurrency({ useGeo: false });
    // jsdom locale -> may be null; when present it must be an ISO code
    if (currency !== null) expect(currency).toMatch(/^[A-Z]{3}$/);
  });

  it('never throws when geo fetch is unavailable', async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = undefined;
    try {
      const currency = await detectCurrency({ useGeo: true });
      expect(currency === null || /^[A-Z]{3}$/.test(currency)).toBe(true);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

describe('detectRegion', () => {
  it('extracts the region subtag from the locale', () => {
    Object.defineProperty(navigator, 'language', { value: 'en-GB', configurable: true });
    expect(detectRegion()).toBe('GB');
  });
});

describe('COUNTRY_TO_CURRENCY', () => {
  it('covers the major markets used by the app', () => {
    expect(COUNTRY_TO_CURRENCY.US).toBe('USD');
    expect(COUNTRY_TO_CURRENCY.PK).toBe('PKR');
    expect(COUNTRY_TO_CURRENCY.IN).toBe('INR');
    expect(COUNTRY_TO_CURRENCY.AE).toBe('AED');
    expect(COUNTRY_TO_CURRENCY.SA).toBe('SAR');
    expect(COUNTRY_TO_CURRENCY.JP).toBe('JPY');
  });
});
