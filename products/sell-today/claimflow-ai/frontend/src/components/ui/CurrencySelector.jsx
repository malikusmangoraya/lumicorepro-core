import React from 'react';
import { useCurrency, CURRENCIES } from '../../context/CurrencyContext';

export default function CurrencySelector({ className = '' }) {
  const { currency, setCurrency } = useCurrency();
  return (
    <select
      value={currency}
      onChange={(e) => setCurrency(e.target.value)}
      aria-label="Select currency"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs transition-colors focus:outline-none ' + className}
    >
      {CURRENCIES.map((c) => (
        <option key={c} value={c}>{c}</option>
      ))}
    </select>
  );
}
