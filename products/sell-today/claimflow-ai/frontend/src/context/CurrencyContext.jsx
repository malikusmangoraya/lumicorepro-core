import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export const CURRENCIES = ['USD', 'EUR', 'GBP', 'PKR', 'INR', 'AED', 'SAR'];

const CurrencyContext = createContext(null);

export function CurrencyProvider({ children }) {
  const [currency, setCurrency] = useState(() => {
    try {
      return localStorage.getItem('lumi-currency') || 'USD';
    } catch (e) {
      return 'USD';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('lumi-currency', currency);
    } catch (e) { /* storage unavailable */ }
  }, [currency]);

  const formatPrice = (amount) => {
    const n = Number(amount || 0);
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
    } catch (e) {
      return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${currency}`;
    }
  };

  const value = useMemo(
    () => ({ currency, setCurrency, formatPrice, CURRENCIES }),
    [currency]
  );

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
}

export function useCurrency() {
  return useContext(CurrencyContext);
}
