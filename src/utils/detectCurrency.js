/**
 * Detect a user's likely currency from browser locale / timezone / geo hints.
 * Used for first-visit localization when the user has no saved preference.
 */

const COUNTRY_CURRENCY = {
  US: 'USD',
  CA: 'CAD',
  MX: 'MXN',
  BR: 'BRL',
  AR: 'ARS',
  CL: 'CLP',
  CO: 'COP',
  AU: 'AUD',
  NZ: 'NZD',
  SG: 'SGD',
  HK: 'HKD',
  IN: 'INR',
  PK: 'PKR',
  BD: 'BDT',
  JP: 'JPY',
  KR: 'KRW',
  CN: 'CNY',
  TW: 'TWD',
  MY: 'MYR',
  TH: 'THB',
  ID: 'IDR',
  PH: 'PHP',
  VN: 'VND',
  AE: 'AED',
  SA: 'SAR',
  QA: 'QAR',
  KW: 'KWD',
  BH: 'BHD',
  OM: 'OMR',
  JO: 'JOD',
  LB: 'LBP',
  EG: 'EGP',
  TR: 'TRY',
  IL: 'ILS',
  IQ: 'IQD',
  GB: 'GBP',
  EU: 'EUR',
  DE: 'EUR',
  FR: 'EUR',
  ES: 'EUR',
  IT: 'EUR',
  NL: 'EUR',
  BE: 'EUR',
  AT: 'EUR',
  IE: 'EUR',
  PT: 'EUR',
  GR: 'EUR',
  FI: 'EUR',
  SE: 'SEK',
  NO: 'NOK',
  DK: 'DKK',
  CH: 'CHF',
  PL: 'PLN',
  CZ: 'CZK',
  HU: 'HUF',
  RO: 'RON',
  UA: 'UAH',
  RU: 'RUB',
  ZA: 'ZAR',
  NG: 'NGN',
  KE: 'KES',
  MA: 'MAD',
};

const TIMEZONE_FALLBACK = {
  'America/New_York': 'USD',
  'America/Chicago': 'USD',
  'America/Denver': 'USD',
  'America/Los_Angeles': 'USD',
  'America/Toronto': 'CAD',
  'America/Vancouver': 'CAD',
  'America/Mexico_City': 'MXN',
  'America/Sao_Paulo': 'BRL',
  'America/Argentina/Buenos_Aires': 'ARS',
  'Europe/London': 'GBP',
  'Europe/Paris': 'EUR',
  'Europe/Berlin': 'EUR',
  'Europe/Madrid': 'EUR',
  'Europe/Rome': 'EUR',
  'Europe/Amsterdam': 'EUR',
  'Europe/Dublin': 'EUR',
  'Europe/Stockholm': 'SEK',
  'Europe/Oslo': 'NOK',
  'Europe/Copenhagen': 'DKK',
  'Europe/Zurich': 'CHF',
  'Europe/Warsaw': 'PLN',
  'Europe/Prague': 'CZK',
  'Europe/Budapest': 'HUF',
  'Asia/Karachi': 'PKR',
  'Asia/Kolkata': 'INR',
  'Asia/Dhaka': 'BDT',
  'Asia/Tokyo': 'JPY',
  'Asia/Seoul': 'KRW',
  'Asia/Shanghai': 'CNY',
  'Asia/Taipei': 'TWD',
  'Asia/Singapore': 'SGD',
  'Asia/Hong_Kong': 'HKD',
  'Asia/Kuala_Lumpur': 'MYR',
  'Asia/Bangkok': 'THB',
  'Asia/Jakarta': 'IDR',
  'Asia/Manila': 'PHP',
  'Asia/Ho_Chi_Minh': 'VND',
  'Asia/Dubai': 'AED',
  'Asia/Riyadh': 'SAR',
  'Asia/Qatar': 'QAR',
  'Asia/Kuwait': 'KWD',
  'Asia/Bahrain': 'BHD',
  'Asia/Muscat': 'OMR',
  'Asia/Amman': 'JOD',
  'Asia/Beirut': 'LBP',
  'Africa/Cairo': 'EGP',
  'Africa/Johannesburg': 'ZAR',
  'Africa/Lagos': 'NGN',
  'Africa/Nairobi': 'KES',
  'Africa/Casablanca': 'MAD',
  'Europe/Istanbul': 'TRY',
  'Asia/Jerusalem': 'ILS',
  'Asia/Baghdad': 'IQD',
  'Europe/Kyiv': 'UAH',
  'Europe/Moscow': 'RUB',
};

const SUPPORTED = [
  'USD',
  'EUR',
  'GBP',
  'PKR',
  'AED',
  'SAR',
  'INR',
  'JPY',
  'CNY',
  'BRL',
  'MXN',
  'CAD',
  'AUD',
  'SGD',
  'HKD',
  'KWD',
  'QAR',
];

/** Currency from the browser's locale (Intl resolvedOptions). */
export function detectCurrencyFromLocale(localeArg) {
  try {
    const locale =
      localeArg || (typeof navigator !== 'undefined' ? navigator.language : '') || 'en-US';
    const resolved = new Intl.NumberFormat(locale).resolvedOptions();
    if (resolved && resolved.currency) {
      const normalized = resolved.currency.toUpperCase();
      if (SUPPORTED.includes(normalized)) return normalized;
    }
  } catch {
    // ignore — fall through to next detection strategy
  }
  return null;
}

/** Currency from the user's timezone. */
export function detectCurrencyFromTimezone(tzArg) {
  try {
    const tz =
      tzArg ||
      (typeof Intl !== 'undefined' && Intl.DateTimeFormat().resolvedOptions().timeZone) ||
      '';
    if (tz) {
      const found = TIMEZONE_FALLBACK[tz];
      if (found && SUPPORTED.includes(found)) return found;
    }
  } catch {
    // ignore
  }
  return null;
}

/**
 * Best-effort currency detection with optional geolocation (IP) lookup.
 * Returns a supported currency code or null.
 */
export async function detectCurrency({ useGeo = true } = {}) {
  let currency = detectCurrencyFromLocale() || detectCurrencyFromTimezone();

  if (!currency && useGeo && typeof fetch !== 'undefined') {
    try {
      const res = await fetch('https://ipapi.co/json/');
      if (res.ok) {
        const data = await res.json();
        const country = (data.country_code || '').toUpperCase();
        const geoCurrency = COUNTRY_CURRENCY[country] || detectCurrencyFromTimezone(data.timezone);
        if (geoCurrency && SUPPORTED.includes(geoCurrency)) {
          currency = geoCurrency;
        }
      }
    } catch {
      // network failure — keep prior result
    }
  }

  return currency;
}

/** Detect the full region (country) hint for locale-aware defaults. */
export function detectRegion() {
  try {
    const locale = (typeof navigator !== 'undefined' ? navigator.language : '') || '';
    const region = locale.split('-')[1]?.toUpperCase();
    if (region) return region;
  } catch {
    // ignore
  }
  return null;
}

export const COUNTRY_TO_CURRENCY = COUNTRY_CURRENCY;
