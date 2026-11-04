import { useSyncExternalStore } from 'react';

const STORAGE_KEY = 'blogforge-locale';
const MESSAGES = {
  en: {
    language: 'Language', english: 'English', urdu: 'اردو', skip: 'Skip to main content',
    evaluationBanner: 'Evaluation build — credit top-ups are not paid purchases.',
    evaluationPricing: 'Evaluation credits only. Checkout is not enabled; no payment will be taken.',
    evaluationStarter: 'Free evaluation credits', evaluationCreator: 'Creator evaluation tier',
    evaluationStudio: 'Studio evaluation tier', evaluationCta: 'Evaluation only',
    rtlNotice: 'Urdu interface preview. Some product content is currently available in English.',
  },
  ur: {
    language: 'زبان', english: 'English', urdu: 'اردو', skip: 'مرکزی مواد پر جائیں',
    evaluationBanner: 'جائزاتی ورژن — کریڈٹ ٹاپ اپس ادا شدہ خریداری نہیں ہیں۔',
    evaluationPricing: 'صرف جائزاتی کریڈٹس۔ ادائیگی فعال نہیں؛ کوئی رقم وصول نہیں ہوگی۔',
    evaluationStarter: 'مفت جائزاتی کریڈٹس', evaluationCreator: 'کریئیٹر جائزاتی درجہ',
    evaluationStudio: 'اسٹوڈیو جائزاتی درجہ', evaluationCta: 'صرف جائزے کے لیے',
    rtlNotice: 'اردو انٹرفیس کا پیش نظارہ۔ کچھ مواد فی الحال انگریزی میں دستیاب ہے۔',
  },
};

let locale = getInitialLocale();
const listeners = new Set();

function applyDocumentLocale(localeCode) {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = localeCode === 'ur' ? 'ur' : 'en';
  document.documentElement.dir = localeCode === 'ur' ? 'rtl' : 'ltr';
}

function getInitialLocale() {
  if (typeof window === 'undefined') return 'en';
  try {
    const initialLocale = window.localStorage.getItem(STORAGE_KEY) === 'ur' ? 'ur' : 'en';
    applyDocumentLocale(initialLocale);
    return initialLocale;
  } catch {
    applyDocumentLocale('en');
    return 'en';
  }
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return locale;
}

export function setLocale(nextLocale) {
  if (!Object.hasOwn(MESSAGES, nextLocale) || nextLocale === locale) return;
  locale = nextLocale;
  try {
    window.localStorage.setItem(STORAGE_KEY, nextLocale);
  } catch {
    // Keep language selection available for this session when storage is unavailable.
  }
  applyDocumentLocale(nextLocale);
  listeners.forEach((listener) => listener());
}

export function useLocale() {
  return useSyncExternalStore(subscribe, getSnapshot, () => 'en');
}

export function translate(localeCode, key) {
  return MESSAGES[localeCode]?.[key] ?? MESSAGES.en[key] ?? key;
}

export function formatNumber(value, localeCode = locale) {
  return new Intl.NumberFormat(localeCode === 'ur' ? 'ur-PK' : 'en-US').format(value);
}

export function formatCurrency(value, currency = 'USD', localeCode = locale) {
  return new Intl.NumberFormat(localeCode === 'ur' ? 'ur-PK' : 'en-US', {
    style: 'currency', currency,
  }).format(value);
}
