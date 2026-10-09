/* LumicorePro pass-3 i18n bootstrap — dep-free.
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
