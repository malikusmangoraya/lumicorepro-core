'use client';

import { Globe, Moon, Sun } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';
import { LOCALES, LOCALE_META, type Locale } from '@/lib/i18n/dictionaries';

export function SiteSettings() {
  const { theme, setTheme, locale, setLocale, t, hydrated } = useSite();

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        title={t('common.theme')}
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        className="inline-flex size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
      >
        {theme === 'dark' ? (
          <Sun className="size-4" aria-hidden="true" />
        ) : (
          <Moon className="size-4" aria-hidden="true" />
        )}
      </button>

      <div className="relative hidden items-center sm:flex">
        <Globe
          className="pointer-events-none absolute left-2 size-3.5 text-muted"
          aria-hidden="true"
        />
        <label htmlFor="locale" className="sr-only">
          {t('common.language')}
        </label>
        <select
          id="locale"
          value={hydrated ? locale : 'en'}
          onChange={(event) => setLocale(event.target.value as Locale)}
          className="appearance-none rounded-control border border-line bg-transparent py-1.5 pl-7 pr-1.5 text-xs font-semibold uppercase text-body/80 transition-colors hover:text-heading focus:border-primary focus:outline-none"
        >
          {LOCALES.map((code) => (
            <option key={code} value={code} className="bg-canvas text-body">
              {code} — {LOCALE_META[code].label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
