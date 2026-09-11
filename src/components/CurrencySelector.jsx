import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useCurrency } from '../hooks/useCurrency';
import { ChevronDown, Search, Banknote } from 'lucide-react';
import { cn } from '../utils';

/**
 * CurrencySelector - Dropdown component for selecting currency
 * Displays flag + currency code, organized by region with live search
 *
 * Usage: Add to Header/Navigation component
 * <CurrencySelector />
 */
export const CurrencySelector = () => {
  const { currency, setCurrency, CURRENCIES, AVAILABLE_CURRENCIES, loading } = useCurrency();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const menuRef = useRef(null);

  const REGIONS = [
    { name: 'Americas', codes: ['USD', 'CAD', 'MXN', 'BRL'] },
    { name: 'Europe', codes: ['EUR', 'GBP'] },
    { name: 'Middle East', codes: ['AED', 'SAR', 'KWD', 'QAR'] },
    { name: 'Asia-Pacific', codes: ['PKR', 'INR', 'JPY', 'CNY', 'SGD', 'HKD', 'AUD'] },
  ];

  const currentInfo = CURRENCIES[currency];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return AVAILABLE_CURRENCIES.filter(
      (c) =>
        c.toLowerCase().includes(q) ||
        (CURRENCIES[c].name || '').toLowerCase().includes(q) ||
        (CURRENCIES[c].symbol || '').toLowerCase().includes(q)
    );
  }, [query, AVAILABLE_CURRENCIES, CURRENCIES]);

  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setIsOpen(false);
    };
    const handleKey = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [isOpen]);

  const renderOption = (code) => {
    const info = CURRENCIES[code];
    const isSelected = currency === code;
    return (
      <button
        type="button"
        key={code}
        onClick={() => {
          setCurrency(code);
          setIsOpen(false);
          setQuery('');
        }}
        className={cn(
          'w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors flex items-center gap-3',
          isSelected ? 'bg-primary/5 text-primary font-medium' : 'text-foreground'
        )}
        aria-current={isSelected ? 'true' : 'false'}
      >
        <span className="text-base leading-none">{info.flag}</span>
        <div className="flex-1 min-w-0">
          <div className="font-medium">{code}</div>
          <div className="text-xs text-muted-foreground truncate">{info.name}</div>
        </div>
        <span className="text-sm">{info.symbol}</span>
        {isSelected && <span className="text-primary">✓</span>}
      </button>
    );
  };

  return (
    <div ref={menuRef} className="relative inline-block">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted transition-all duration-200 text-sm font-medium text-foreground"
        aria-label={`Select currency, current: ${currentInfo?.name}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title={`Current currency: ${currentInfo?.name}`}
      >
        <span className="text-base leading-none">{currentInfo?.flag}</span>
        <span className="hidden sm:inline">{currency}</span>
        <ChevronDown
          size={16}
          className={cn(
            'text-muted-foreground transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-border text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Banknote className="w-3.5 h-3.5" aria-hidden="true" />
            Currency
          </div>
          <div className="px-3 py-2 border-b border-border">
            <div className="relative">
              <Search
                className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground"
                aria-hidden="true"
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search currency..."
                className="w-full pl-8 pr-3 py-1.5 border border-border rounded-md text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                aria-label="Search currencies"
              />
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto" role="listbox">
            {filtered ? (
              filtered.length ? (
                filtered.map(renderOption)
              ) : (
                <div className="px-3 py-3 text-xs text-muted-foreground text-center">
                  No currencies found
                </div>
              )
            ) : (
              REGIONS.map(({ name, codes }) => {
                const validCodes = codes.filter((c) => AVAILABLE_CURRENCIES.includes(c));
                if (validCodes.length === 0) return null;
                return (
                  <div key={name} className="border-b border-border last:border-b-0">
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-muted/40">
                      {name}
                    </div>
                    {validCodes.map(renderOption)}
                  </div>
                );
              })
            )}
          </div>

          {loading && (
            <div className="px-3 py-2 text-xs text-muted-foreground text-center border-t border-border">
              Updating rates...
            </div>
          )}
        </div>
      )}
    </div>
  );
};
