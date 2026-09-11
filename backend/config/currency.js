/**
 * Currency configuration registry
 * Used by the no-code Admin Settings panel and the Setup Wizard to validate
 * and persist the site's base currency at runtime (DB-backed, not .env).
 */

export const CURRENCY_LIST = {
  USD: { code: 'USD', symbol: '$', name: 'US Dollar', locale: 'en-US' },
  EUR: { code: 'EUR', symbol: '€', name: 'Euro', locale: 'de-DE' },
  GBP: { code: 'GBP', symbol: '£', name: 'British Pound', locale: 'en-GB' },
  PKR: { code: 'PKR', symbol: 'Rs', name: 'Pakistani Rupee', locale: 'ur-PK' },
  INR: { code: 'INR', symbol: '₹', name: 'Indian Rupee', locale: 'hi-IN' },
  AED: { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham', locale: 'ar-AE' },
  SAR: { code: 'SAR', symbol: '﷼', name: 'Saudi Riyal', locale: 'ar-SA' },
  JPY: { code: 'JPY', symbol: '¥', name: 'Japanese Yen', locale: 'ja-JP' },
  CNY: { code: 'CNY', symbol: '¥', name: 'Chinese Yuan', locale: 'zh-CN' },
  BRL: { code: 'BRL', symbol: 'R$', name: 'Brazilian Real', locale: 'pt-BR' },
  MXN: { code: 'MXN', symbol: '$', name: 'Mexican Peso', locale: 'es-MX' },
  CAD: { code: 'CAD', symbol: '$', name: 'Canadian Dollar', locale: 'en-CA' },
  AUD: { code: 'AUD', symbol: '$', name: 'Australian Dollar', locale: 'en-AU' },
  SGD: { code: 'SGD', symbol: '$', name: 'Singapore Dollar', locale: 'en-SG' },
  HKD: { code: 'HKD', symbol: '$', name: 'Hong Kong Dollar', locale: 'zh-HK' },
  KWD: { code: 'KWD', symbol: 'د.ك', name: 'Kuwaiti Dinar', locale: 'ar-KW' },
  QAR: { code: 'QAR', symbol: 'ر.ق', name: 'Qatari Riyal', locale: 'ar-QA' },
  UAH: { code: 'UAH', symbol: '₴', name: 'Ukrainian Hryvnia', locale: 'uk-UA' },
  BDT: { code: 'BDT', symbol: '৳', name: 'Bangladeshi Taka', locale: 'bn-BD' },
  TRY: { code: 'TRY', symbol: '₺', name: 'Turkish Lira', locale: 'tr-TR' },
};

export const SUPPORTED_CURRENCIES = Object.values(CURRENCY_LIST).map((c) => c.code);

export const getCurrencySymbol = (code = 'USD') => {
  const entry = CURRENCY_LIST[(code || 'USD').toUpperCase()];
  return entry ? entry.symbol : '$';
};

export default CURRENCY_LIST;