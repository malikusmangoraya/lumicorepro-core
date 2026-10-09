import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import fallback from './locales/en.json';

export const RTL_LANGUAGES = ['ar', 'fa', 'he', 'ps', 'sd', 'ur'];
export const AVAILABLE_LANGUAGES = [
'ar', 'de', 'en', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt', 'ru', 'tr', 'ur', 'zh'
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

/* One code-split chunk per locale, loaded on demand. */
const localeModules = import.meta.glob('./locales/*.json');
const loaded = new Set(['en']);

async function loadLocale(lang) {
  if (!lang || loaded.has(lang)) return;
  const loader = localeModules[`./locales/${lang}.json`];
  if (!loader) return;
  try {
    const mod = await loader();
    i18n.addResourceBundle(lang, 'translation', mod.default || mod, true, true);
    loaded.add(lang);
  } catch (e) { /* keep the fallback language visible */ }
}

function applyDir(lng) {
  if (typeof document === 'undefined') return;
  const isRtl = RTL_LANGUAGES.includes(lng);
  document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lng);
}

const initial = detectLang(AVAILABLE_LANGUAGES);

i18n
  .use(initReactI18next)
  .init({
    resources: { en: { translation: fallback } },
    fallbackLng: 'en',
    supportedLngs: AVAILABLE_LANGUAGES,
    lng: initial,
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    returnNull: false,
  });

/* Pull the visitor's language in behind the fallback, then keep every later
   switch on demand. */
if (initial !== 'en') loadLocale(initial);
i18n.on('languageChanged', (lng) => {
  loadLocale(lng);
  applyDir(lng);
});
applyDir(i18n.language || 'en');

export default i18n;
