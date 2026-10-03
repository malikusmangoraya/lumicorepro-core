"""Pass-3 international templates — DEP-FREE (only i18next + react-i18next, which
every generated project already depends on; no languagedetector package).

Exports exactly what internationalize_pass3.py imports:
  I18N_INDEX, CURRENCY_CONTEXT, CURRENCY_SELECTOR, LANGUAGE_SELECTOR, FOOTER_STRIP
"""

I18N_INDEX = r'''/* LumicorePro pass-3 i18n bootstrap — dep-free.
   Uses ONLY i18next + react-i18next (present in every generated project).
   Lazily imports locale JSON + a small RTL-aware dir/lang bootstrap that
   respects the existing scaffolded src/i18n/locales directory. */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const RTL_LANGUAGES = ['ar', 'fa', 'he', 'ps', 'sd', 'ur'];
export const AVAILABLE_LANGUAGES = [
  'ar', 'de', 'en', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt', 'ru', 'tr',
];

function detectLang(available) {
  /* dep-free detection: localStorage, then navigator, then en */
  try {
    const saved = localStorage.getItem('i18nextLng');
    if (saved && available.includes(saved)) return saved;
  } catch (e) { /* ignore */ }
  if (typeof navigator !== 'undefined') {
    const nav = (navigator.language || 'en').split('-')[0];
    if (available.includes(nav)) return nav;
  }
  return 'en';
}

function loadLocales() {
  /* eager glob of src/i18n/locales/*.json */
  const ctx = import.meta.glob('./locales/*.json', { eager: true });
  const resources = {};
  for (const path in ctx) {
    const lang = path.replace('./locales/', '').replace('.json', '');
    resources[lang] = { translation: ctx[path].default || ctx[path] };
  }
  return resources;
}

function applyDir(lng) {
  if (typeof document === 'undefined') return;
  const isRtl = RTL_LANGUAGES.includes(lng);
  document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lng);
}

i18n
  .use(initReactI18next)
  .init({
    resources: loadLocales(),
    fallbackLng: 'en',
    supportedLngs: AVAILABLE_LANGUAGES,
    lng: detectLang(AVAILABLE_LANGUAGES),
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    returnNull: false,
  });

i18n.on('languageChanged', applyDir);
applyDir(i18n.language || 'en');

export default i18n;
'''

CURRENCY_CONTEXT = r'''import React, { createContext, useContext, useEffect, useState } from 'react';

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
    } catch (e) { /* ignore */ }
  }, [currency]);

  const formatPrice = (amount) => {
    const n = Number(amount || 0);
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
    } catch (e) {
      return n.toLocaleString(undefined, { maximumFractionDigits: 2 }) + ' ' + currency;
    }
  };

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, formatPrice, CURRENCIES }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  return useContext(CurrencyContext);
}
'''

CURRENCY_SELECTOR = r'''import React from 'react';
import { useCurrency, CURRENCIES } from '../../context/CurrencyContext';

export default function CurrencySelector({ className = '' }) {
  const { currency, setCurrency } = useCurrency();
  return (
    <select
      value={currency}
      onChange={(e) => setCurrency(e.target.value)}
      aria-label="Select currency"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs text-slate-300 transition-colors focus:border-white/40 focus:outline-none ' + className}
    >
      {CURRENCIES.map((c) => (
        <option key={c} value={c}>
          {c}
        </option>
      ))}
    </select>
  );
}
'''

LANGUAGE_SELECTOR = r'''import React from 'react';
import { useTranslation } from 'react-i18next';
import { AVAILABLE_LANGUAGES } from '../../i18n';

export default function LanguageSelector({ className = '' }) {
  const { i18n } = useTranslation();
  return (
    <select
      value={i18n.resolvedLanguage || i18n.language || 'en'}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
      aria-label="Select language"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs text-slate-300 transition-colors focus:border-white/40 focus:outline-none ' + className}
    >
      {AVAILABLE_LANGUAGES.map((l) => (
        <option key={l} value={l}>
          {l.toUpperCase()}
        </option>
      ))}
    </select>
  );
}
'''

FOOTER_STRIP = r'''      <div className="mt-8 flex flex-wrap items-center justify-center gap-x-3 gap-y-2 border-t border-white/10 pt-5 text-xs text-slate-400">
        <LanguageSelector />
        <CurrencySelector />
      </div>
'''
