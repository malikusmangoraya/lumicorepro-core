"""Pass 2b — normalise src/i18n/index.js to the canonical, dep-free implementation.

Replaces the older variant (which imported i18next-browser-languagedetector,
hardcoded supportedLngs, exported no AVAILABLE_LANGUAGES, and only handled
2 RTL languages) with a single canonical module that:
  * exports RTL_LANGUAGES (full set) + AVAILABLE_LANGUAGES (single source of truth)
  * uses only i18next + react-i18next
  * sets <html dir> and <html lang> on boot and on every language change
  * ?lang= query param wins, then localStorage, then navigator, then en

Idempotent: skips files that already export AVAILABLE_LANGUAGES and import
only i18next + react-i18next.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

CANONICAL = '''/* LumicorePro canonical i18n bootstrap — dependency-free.
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
'''


def needs_fix(t: str) -> bool:
    if "export const AVAILABLE_LANGUAGES" in t and "i18next-browser-languagedetector" not in t:
        return False
    return True


def main():
    targets = sys.argv[1:] or [d.name for d in sorted(PROJECTS.iterdir())]
    fixed = 0
    for slug in targets:
        f = PROJECTS / slug / "frontend" / "src" / "i18n" / "index.js"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        if not needs_fix(t):
            continue
        f.write_text(CANONICAL, encoding="utf-8")
        fixed += 1
        # drop the now-unused detector dependency if present
        pkg = PROJECTS / slug / "frontend" / "package.json"
        if pkg.exists():
            pt = pkg.read_text(encoding="utf-8", errors="ignore")
            if "i18next-browser-languagedetector" in pt:
                pt = re.sub(r'\s*"i18next-browser-languagedetector":\s*"[^"]*",?', "", pt)
                pt = re.sub(r',\s*([}\]])', r"\1", pt)  # tidy trailing comma
                pkg.write_text(pt, encoding="utf-8")
    print(f"i18n normalised: {fixed}")


if __name__ == "__main__":
    main()