/* LumicorePro canonical i18n bootstrap — dependency-free.
   Only i18next + react-i18next. Exports the language + RTL lists so selectors
   and any component can import them instead of duplicating literals. */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const RTL_LANGUAGES = ['ar', 'fa', 'he', 'ps', 'sd', 'ur'];
export const AVAILABLE_LANGUAGES = [
  'ar', 'de', 'en', 'es', 'fr', 'hi', 'id', 'ja', 'ko', 'pt', 'ru', 'tr',
  'ur', 'zh',
];

function detectLang(available) {
  try {
    const q = new URLSearchParams(window.location.search).get('lang');
    if (q && available.includes(q)) return q;
  } catch (e) { /* not a browser or no search params */ }
  try {
    const saved = localStorage.getItem('i18nextLng');
    if (saved && available.includes(saved)) return saved;
  } catch (e) { /* storage unavailable */ }
  if (typeof navigator !== 'undefined') {
    const nav = (navigator.language || 'en').split('-')[0];
    if (available.includes(nav)) return nav;
  }
  return 'en';
}

function loadLocales() {
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
