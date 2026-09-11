/**
 * Locale-aware formatting helpers (dates, numbers).
 * Uses the active i18n language + region so dates & numbers match the user's
 * language/region — a core part of international-market readiness.
 */

const SUPPORTED_INTL = [
  'en',
  'es',
  'fr',
  'de',
  'it',
  'pt',
  'ar',
  'ur',
  'zh',
  'ja',
  'ko',
  'hi',
  'tr',
];

const REGION_BY_LANG = {
  en: 'US',
  es: 'ES',
  fr: 'FR',
  de: 'DE',
  it: 'IT',
  pt: 'BR',
  ar: 'SA',
  ur: 'PK',
  zh: 'CN',
  ja: 'JP',
  ko: 'KR',
  hi: 'IN',
  tr: 'TR',
};

/**
 * Build a full BCP-47 locale tag from a base i18n language code.
 * @param {string} lang - Base language code (e.g. 'en', 'fr', 'zh')
 * @returns {string} Full locale tag (e.g. 'en-US')
 */
export function toLocaleTag(lang = 'en') {
  const base = (lang || 'en').split('-')[0].toLowerCase();
  if (!SUPPORTED_INTL.includes(base)) return 'en-US';
  const region = REGION_BY_LANG[base];
  return region ? `${base}-${region}` : base;
}

/**
 * Format a date using the active locale.
 * @param {string|number|Date} date — Value accepted by Date constructor
 * @param {Object} options — Intl.DateTimeFormat options (defaults to sensible preset)
 * @param {string} lang — Override language (defaults to current i18n language)
 * @returns Formatted date string
 */
export function formatDate(date, options = {}, lang) {
  const i18nLang = typeof window !== 'undefined' ? document.documentElement.lang || 'en' : 'en';
  const locale = toLocaleTag(lang || i18nLang);
  const dateObj = new Date(date);
  if (Number.isNaN(dateObj.getTime())) return '';

  const defaults = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };
  try {
    return new Intl.DateTimeFormat(locale, { ...defaults, ...options }).format(dateObj);
  } catch {
    return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(dateObj);
  }
}

/**
 * Format a datetime with time using the active locale.
 */
export function formatDateTime(date, options = {}, lang) {
  return formatDate(
    date,
    {
      hour: '2-digit',
      minute: '2-digit',
      ...options,
    },
    lang
  );
}

/**
 * Format a number with the active locale's grouping + decimal separators.
 * @param {number} value
 * @param {Object} options — Intl.NumberFormat options
 */
export function formatNumber(value, options = {}, lang) {
  const i18nLang = typeof window !== 'undefined' ? document.documentElement.lang || 'en' : 'en';
  const locale = toLocaleTag(lang || i18nLang);
  try {
    return new Intl.NumberFormat(locale, options).format(value);
  } catch {
    return new Intl.NumberFormat('en-US', options).format(value);
  }
}

/**
 * Format a number as a percentage (e.g. 12.5%).
 */
export function formatPercent(value, options = {}, lang) {
  return formatNumber(value, { style: 'percent', ...options }, lang);
}

export default {
  toLocaleTag,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercent,
};
