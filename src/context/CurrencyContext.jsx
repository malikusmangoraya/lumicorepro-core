import React, { createContext, useState, useCallback, useEffect } from 'react';
import { detectCurrency } from '../utils/detectCurrency';

/**
 * CurrencyContext - Global currency state management
 * Tracks user's selected currency, exchange rates, and currency metadata
 */
export const CurrencyContext = createContext(null);

// Currency registry with metadata
const CURRENCIES = {
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', flag: '🇺🇸', decimal: 2 },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', flag: '🇪🇺', decimal: 2 },
  GBP: { code: 'GBP', symbol: '£', name: 'British Pound', flag: '🇬🇧', decimal: 2 },
  PKR: { code: 'PKR', symbol: 'Rs', name: 'Pakistani Rupee', flag: '🇵🇰', decimal: 0 },
  AED: { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham', flag: '🇦🇪', decimal: 2 },
  SAR: { code: 'SAR', symbol: '﷼', name: 'Saudi Riyal', flag: '🇸🇦', decimal: 2 },
  INR: { code: 'INR', symbol: '₹', name: 'Indian Rupee', flag: '🇮🇳', decimal: 0 },
  JPY: { code: 'JPY', symbol: '¥', name: 'Japanese Yen', flag: '🇯🇵', decimal: 0 },
  CNY: { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', flag: '🇨🇳', decimal: 2 },
  BRL: { code: 'BRL', symbol: 'R$', name: 'Brazilian Real', flag: '🇧🇷', decimal: 2 },
  MXN: { code: 'MXN', symbol: '$', name: 'Mexican Peso', flag: '🇲🇽', decimal: 2 },
  CAD: { code: 'CAD', symbol: '$', name: 'Canadian Dollar', flag: '🇨🇦', decimal: 2 },
  AUD: { code: 'AUD', symbol: '$', name: 'Australian Dollar', flag: '🇦🇺', decimal: 2 },
  SGD: { code: 'SGD', symbol: '$', name: 'Singapore Dollar', flag: '🇸🇬', decimal: 2 },
  HKD: { code: 'HKD', symbol: '$', name: 'Hong Kong Dollar', flag: '🇭🇰', decimal: 2 },
  KWD: { code: 'KWD', symbol: 'د.ك', name: 'Kuwaiti Dinar', flag: '🇰🇼', decimal: 3 },
  QAR: { code: 'QAR', symbol: 'ر.ق', name: 'Qatari Riyal', flag: '🇶🇦', decimal: 2 },
};

// Default exchange rates (relative to USD)
// In production, fetch from Open Exchange Rates API or similar
const DEFAULT_RATES = {
  USD: 1.0,
  EUR: 0.92,
  GBP: 0.79,
  PKR: 278.5,
  AED: 3.67,
  SAR: 3.75,
  INR: 83.12,
  JPY: 149.5,
  CNY: 7.24,
  BRL: 4.97,
  MXN: 17.05,
  CAD: 1.36,
  AUD: 1.52,
  SGD: 1.34,
  HKD: 7.81,
  KWD: 0.31,
  QAR: 3.64,
};

export const CurrencyProvider = ({ children }) => {
  const [currency, setCurrencyState] = useState('USD');
  const [rates, setRates] = useState(DEFAULT_RATES);
  const [loading, setLoading] = useState(false);

  // On first visit (no saved preference), auto-detect the user's likely currency
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const saved = localStorage.getItem('userCurrency');
      if (saved && CURRENCIES[saved]) {
        setCurrencyState(saved);
        return;
      }
      const detected = await detectCurrency();
      if (!cancelled && detected && CURRENCIES[detected]) {
        setCurrencyState(detected);
        localStorage.setItem('userCurrency', detected);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch live exchange rates from API
  const fetchExchangeRates = useCallback(async () => {
    setLoading(true);
    try {
      // Using exchange-api.com free tier (no key required)
      const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD', {
        headers: { Accept: 'application/json' },
        cache: 'force-cache',
      });
      const data = await response.json();
      if (data.rates) {
        setRates(data.rates);
      }
    } catch {
      // Keep using default rates if API fails
    } finally {
      setLoading(false);
    }
  }, []);

  // Call fetchExchangeRates on mount and every hour
  useEffect(() => {
    fetchExchangeRates();
    const interval = setInterval(fetchExchangeRates, 3600000); // 1 hour
    return () => clearInterval(interval);
  }, [fetchExchangeRates]);

  const setCurrency = useCallback((newCurrency) => {
    if (CURRENCIES[newCurrency]) {
      setCurrencyState(newCurrency);
      localStorage.setItem('userCurrency', newCurrency);
    }
  }, []);

  /**
   * Convert amount from one currency to another
   * @param amount - Amount to convert
   * @param fromCurrency - Source currency code (default: USD)
   * @param toCurrency - Target currency code (default: current currency)
   * @returns Converted amount
   */
  const convertCurrency = useCallback(
    (amount, fromCurrency = 'USD', toCurrency = currency) => {
      if (fromCurrency === toCurrency) return amount;
      const rate = rates[toCurrency] || 1;
      const baseRate = rates[fromCurrency] || 1;
      return (amount * rate) / baseRate;
    },
    [currency, rates]
  );

  /**
   * Format price with symbol and appropriate decimal places
   * @param {number} amount - Amount to format
   * @param {string} currencyCode - Currency code (default: current currency)
   * @param {boolean} showCode - Include currency code in output
   * @returns Formatted price string
   */
  const formatPrice = useCallback(
    (amount, currencyCode = currency, showCode = false) => {
      const curr = CURRENCIES[currencyCode];
      if (!curr) return `$${amount}`;

      const converted = convertCurrency(amount, 'USD', currencyCode);
      const locale = (typeof navigator !== 'undefined' && navigator.language) || 'en-US';
      try {
        const formatted = new Intl.NumberFormat(locale, {
          style: 'currency',
          currency: currencyCode,
          minimumFractionDigits: curr.decimal,
          maximumFractionDigits: curr.decimal,
        }).format(converted);
        return showCode ? `${formatted} ${currencyCode}` : formatted;
      } catch {
        const fallback = converted.toLocaleString('en-US', {
          minimumFractionDigits: curr.decimal,
          maximumFractionDigits: curr.decimal,
        });
        return showCode ? `${curr.symbol}${fallback} ${currencyCode}` : `${curr.symbol}${fallback}`;
      }
    },
    [currency, convertCurrency]
  );

  /**
   * Get currency metadata
   * @param currencyCode - Currency code (default: current currency)
   * @returns Currency object with code, symbol, name, flag, decimal
   */
  const getCurrencyInfo = useCallback(
    (currencyCode = currency) => {
      return CURRENCIES[currencyCode] || CURRENCIES.USD;
    },
    [currency]
  );

  const value = {
    // State
    currency,
    rates,
    loading,

    // Actions
    setCurrency,
    fetchExchangeRates,

    // Utilities
    convertCurrency,
    formatPrice,
    getCurrencyInfo,

    // Constants
    CURRENCIES,
    AVAILABLE_CURRENCIES: Object.keys(CURRENCIES),
  };

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
};
