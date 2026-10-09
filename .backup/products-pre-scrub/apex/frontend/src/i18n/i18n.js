/* SRS quality gate scaffolding — i18n bootstrap + RTL (LUMICORE_I18N) */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

export const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur', 'ps', 'ku', 'sd'];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {},
    fallbackLng: 'en',
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    detection: { order: ['localStorage', 'navigator', 'htmlTag'], caches: ['localStorage'] },
  });

i18n.on('languageChanged', (lng) => {
  document.documentElement.dir = RTL_LANGUAGES.includes(lng) ? 'rtl' : 'ltr';
  document.documentElement.lang = lng;
});

export default i18n;
