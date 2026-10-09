import React, { useEffect, useState } from 'react';
import { BadgeCheck } from 'lucide-react';
import { cn } from '../../utils';

const CURRENCIES = [
  { code: 'USD', label: 'US Dollar' },
  { code: 'EUR', label: 'Euro' },
  { code: 'GBP', label: 'British Pound' },
  { code: 'AED', label: 'UAE Dirham' },
  { code: 'SAR', label: 'Saudi Riyal' },
  { code: 'PKR', label: 'Pakistani Rupee' },
  { code: 'INR', label: 'Indian Rupee' },
  { code: 'CNY', label: 'Chinese Yuan' },
  { code: 'JPY', label: 'Japanese Yen' },
];

const CurrencySelector = ({
  value = 'USD',
  onChange,
  storageKey = 'currency',
  compact = false,
  className = '',
}) => {
  const [currency, setCurrency] = useState(() => {
    try {
      return localStorage.getItem(storageKey) || value;
    } catch (e) {
      return value;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, currency);
    } catch (e) {
      /* storage unavailable */
    }
  }, [currency, storageKey]);

  const update = (code) => {
    setCurrency(code);
    if (typeof onChange === 'function') onChange(code);
    document.dispatchEvent(new CustomEvent('currency:changed', { detail: { currency: code } }));
  };

  return (
    <label className={cn('relative inline-flex items-center', className)}>
      <span className="sr-only">Select currency</span>
      <BadgeCheck
        className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground"
        aria-hidden="true"
      />
      <select
        value={currency}
        onChange={(e) => update(e.target.value)}
        className={cn(
          'cursor-pointer appearance-none rounded-lg border bg-background py-2 pr-8 pl-9 text-sm text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30',
          compact ? 'w-24' : 'w-auto'
        )}
      >
        {CURRENCIES.map((c) => (
          <option key={c.code} value={c.code}>
            {c.code} {compact ? '' : `- ${c.label}`}
          </option>
        ))}
      </select>
      <span
        className="pointer-events-none absolute right-3 text-muted-foreground"
        aria-hidden="true"
      >
        ▾
      </span>
    </label>
  );
};

export default CurrencySelector;
