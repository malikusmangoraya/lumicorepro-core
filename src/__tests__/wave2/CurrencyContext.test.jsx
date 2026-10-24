import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CurrencyProvider } from '../../context/CurrencyContext';
import { useCurrency } from '../../hooks/useCurrency';
import { detectCurrency } from '../../utils/detectCurrency';

vi.mock('../../utils/detectCurrency', () => ({
  detectCurrency: vi.fn(),
}));

const wrapper = ({ children }) => <CurrencyProvider>{children}</CurrencyProvider>;

/** Renders the provider and waits for the initial rates request to settle. */
async function renderCurrency() {
  const hook = renderHook(() => useCurrency(), { wrapper });
  await waitFor(() => expect(hook.result.current.loading).toBe(false));
  return hook;
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  detectCurrency.mockResolvedValue(null);
  // Default: live-rate request fails so the provider keeps its bundled rates.
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('CurrencyContext — initial state', () => {
  it('defaults to USD when nothing is stored and detection finds nothing', async () => {
    const { result } = await renderCurrency();

    expect(result.current.currency).toBe('USD');
    expect(result.current.getCurrencyInfo().name).toBe('US Dollar');

    await waitFor(() => expect(detectCurrency).toHaveBeenCalled());
    expect(result.current.currency).toBe('USD');
  });

  it('restores the saved currency without running detection', async () => {
    localStorage.setItem('userCurrency', 'EUR');

    const { result } = await renderCurrency();

    expect(result.current.currency).toBe('EUR');
    expect(result.current.getCurrencyInfo().symbol).toBe('€');
    expect(detectCurrency).not.toHaveBeenCalled();
  });

  it('adopts a detected currency and persists it', async () => {
    detectCurrency.mockResolvedValue('GBP');

    const { result } = await renderCurrency();

    await waitFor(() => expect(result.current.currency).toBe('GBP'));
    expect(localStorage.getItem('userCurrency')).toBe('GBP');
    expect(result.current.getCurrencyInfo().name).toBe('British Pound');
  });
});

describe('CurrencyContext — switching and persistence', () => {
  it('switches currency and writes the preference to localStorage', async () => {
    const { result } = await renderCurrency();

    act(() => result.current.setCurrency('JPY'));

    expect(result.current.currency).toBe('JPY');
    expect(localStorage.getItem('userCurrency')).toBe('JPY');
    expect(result.current.getCurrencyInfo()).toMatchObject({ code: 'JPY', decimal: 0 });
  });

  it('ignores unknown currency codes', async () => {
    const { result } = await renderCurrency();

    act(() => result.current.setCurrency('XYZ'));

    expect(result.current.currency).toBe('USD');
    expect(localStorage.getItem('userCurrency')).toBeNull();
  });

  it('formats prices with Intl using the active currency', async () => {
    const { result } = await renderCurrency();

    expect(result.current.formatPrice(1234.5)).toBe('$1,234.50');

    act(() => result.current.setCurrency('EUR'));
    expect(result.current.formatPrice(100)).toBe('€92.00');
    expect(result.current.formatPrice(100, 'EUR', true)).toBe('€92.00 EUR');
  });

  it('uses zero decimals for PKR and falls back for unknown currencies', async () => {
    const { result } = await renderCurrency();

    const pkr = result.current.formatPrice(100, 'PKR');
    expect(pkr).toContain('27,850');
    expect(pkr).not.toContain('.');

    expect(result.current.formatPrice(50, 'XYZ')).toBe('$50');
  });
});

describe('CurrencyContext — conversion and rates', () => {
  it('converts between currencies using the bundled rates', async () => {
    const { result } = await renderCurrency();

    expect(result.current.convertCurrency(100)).toBe(100);
    expect(result.current.convertCurrency(100, 'USD', 'EUR')).toBeCloseTo(92, 5);
    expect(result.current.convertCurrency(100, 'EUR', 'GBP')).toBeCloseTo(85.869565, 4);
  });

  it('replaces bundled rates when the rates API succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ rates: { USD: 1, EUR: 2, GBP: 4 } }),
      })
    );

    const { result } = await renderCurrency();

    expect(result.current.rates.EUR).toBe(2);
    expect(result.current.convertCurrency(10, 'USD', 'EUR')).toBe(20);
  });

  it('keeps bundled rates and clears loading when the rates API fails', async () => {
    const { result } = await renderCurrency();

    expect(result.current.rates.EUR).toBe(0.92);
    expect(result.current.convertCurrency(100, 'USD', 'EUR')).toBeCloseTo(92, 5);
  });

  it('does not clobber rates when the payload has no rates field', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ base: 'USD' }) })
    );

    const { result } = await renderCurrency();

    expect(result.current.rates.GBP).toBe(0.79);
  });

  it('re-fetches rates on demand through fetchExchangeRates', async () => {
    const { result } = await renderCurrency();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ rates: { USD: 1, EUR: 3 } }) })
    );

    await act(async () => {
      await result.current.fetchExchangeRates();
    });

    expect(result.current.rates.EUR).toBe(3);
    expect(result.current.loading).toBe(false);
  });
});

describe('CurrencyContext — registry', () => {
  it('exposes metadata for known currencies and falls back to USD', async () => {
    const { result } = await renderCurrency();

    expect(result.current.AVAILABLE_CURRENCIES).toHaveLength(17);
    expect(result.current.AVAILABLE_CURRENCIES).toEqual(
      expect.arrayContaining(['USD', 'EUR', 'GBP', 'PKR', 'INR', 'AED', 'SAR'])
    );
    expect(result.current.getCurrencyInfo('KWD').decimal).toBe(3);
    expect(result.current.getCurrencyInfo('NOPE')).toEqual(result.current.CURRENCIES.USD);
  });
});
