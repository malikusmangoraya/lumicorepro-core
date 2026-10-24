import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CurrencyContext } from '../../context/CurrencyContext';
import { useCurrency } from '../../hooks/useCurrency';

const contextValue = {
  currency: 'EUR',
  rates: { USD: 1, EUR: 0.92 },
  loading: false,
  setCurrency: vi.fn(),
  formatPrice: vi.fn((amount) => `€${amount}`),
  convertCurrency: vi.fn((amount) => amount * 0.92),
  getCurrencyInfo: vi.fn(() => ({ code: 'EUR', symbol: '€' })),
  CURRENCIES: {},
  AVAILABLE_CURRENCIES: ['USD', 'EUR'],
};

describe('useCurrency', () => {
  it('throws a descriptive error outside CurrencyProvider', () => {
    expect(() => renderHook(() => useCurrency())).toThrow(
      'useCurrency must be used within CurrencyProvider'
    );
  });

  it('returns the context value inside CurrencyProvider', () => {
    const wrapper = ({ children }) => (
      <CurrencyContext.Provider value={contextValue}>{children}</CurrencyContext.Provider>
    );

    const { result } = renderHook(() => useCurrency(), { wrapper });

    expect(result.current.currency).toBe('EUR');
    expect(result.current.formatPrice(10)).toBe('€10');
    expect(result.current.convertCurrency(100)).toBe(92);
    expect(result.current.getCurrencyInfo().symbol).toBe('€');
    expect(result.current.AVAILABLE_CURRENCIES).toEqual(['USD', 'EUR']);
  });

  it('re-renders consumers when the provider value changes', () => {
    let value = contextValue;
    const wrapper = ({ children }) => (
      <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>
    );

    const { result, rerender } = renderHook(() => useCurrency(), { wrapper });
    expect(result.current.currency).toBe('EUR');

    value = { ...contextValue, currency: 'GBP', formatPrice: (amount) => `£${amount}` };
    rerender();

    expect(result.current.currency).toBe('GBP');
    expect(result.current.formatPrice(20)).toBe('£20');
  });

  it('propagates actions from the provider unchanged', () => {
    const wrapper = ({ children }) => (
      <CurrencyContext.Provider value={contextValue}>{children}</CurrencyContext.Provider>
    );

    const { result } = renderHook(() => useCurrency(), { wrapper });

    expect(result.current.setCurrency).toBe(contextValue.setCurrency);
    expect(result.current.loading).toBe(false);
  });
});
