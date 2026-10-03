import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { updateDocumentDirection } from './rtlHelper';

// Only the fallback locale ships in the entry chunk; the other twelve are
// ~20 KB of JSON each and are fetched on demand.
import en from './locales/en.json';

const LOCALE_LOADERS = {
  es: () => import('./locales/es.json'),
  fr: () => import('./locales/fr.json'),
  de: () => import('./locales/de.json'),
  ar: () => import('./locales/ar.json'),
  zh: () => import('./locales/zh.json'),
  ja: () => import('./locales/ja.json'),
  ur: () => import('./locales/ur.json'),
  ko: () => import('./locales/ko.json'),
  pt: () => import('./locales/pt.json'),
  it: () => import('./locales/it.json'),
  hi: () => import('./locales/hi.json'),
  tr: () => import('./locales/tr.json'),
};

const loadedLocales = new Set(['en']);

// Resolves true only when a new bundle was registered, so callers can re-emit
// languageChanged exactly once per locale and never loop.
const loadLocale = (lng) => {
  const base = String(lng || 'en').split('-')[0].toLowerCase();
  const loader = LOCALE_LOADERS[base];
  if (!loader || loadedLocales.has(base)) return Promise.resolve(false);
  return loader().then((mod) => {
    i18n.addResourceBundle(base, 'translation', mod.default || mod, true, true);
    loadedLocales.add(base);
    return true;
  });
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en } },
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false, // React already escapes by default
    },
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
    supportedLngs: ['en', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'ur', 'pt', 'it', 'hi', 'tr', 'ko'],
  });

// Handle initial and dynamic RTL direction
updateDocumentDirection(i18n.language || 'en');
i18n.on('languageChanged', (lng) => {
  updateDocumentDirection(lng);
  loadLocale(lng).then((added) => {
    if (added) i18n.changeLanguage(i18n.language);
  });
});

// i18n.init() already emitted languageChanged before the listener existed
loadLocale(i18n.language).then((added) => {
  if (added) i18n.changeLanguage(i18n.language);
});

export default i18n;
