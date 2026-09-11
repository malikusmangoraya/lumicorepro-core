import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { updateDocumentDirection } from './rtlHelper';

// Import translation files
import en from './locales/en.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import ar from './locales/ar.json';
import zh from './locales/zh.json';
import ja from './locales/ja.json';
import ur from './locales/ur.json';
import ko from './locales/ko.json';
import pt from './locales/pt.json';
import it from './locales/it.json';
import hi from './locales/hi.json';
import tr from './locales/tr.json';

const resources = {
  en: { translation: en },
  es: { translation: es },
  fr: { translation: fr },
  de: { translation: de },
  ar: { translation: ar },
  zh: { translation: zh },
  ja: { translation: ja },
  ur: { translation: ur },
  ko: { translation: ko },
  pt: { translation: pt },
  it: { translation: it },
  hi: { translation: hi },
  tr: { translation: tr },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
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
});

export default i18n;
