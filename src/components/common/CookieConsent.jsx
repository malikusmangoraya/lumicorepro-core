/**
 * CookieConsent — GDPR / CCPA compliant consent banner.
 * Shows on first visit, stores the decision in localStorage, and emits a
 * `cookieConsentUpdated` event so analytics can respect the choice.
 */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';

const STORAGE_KEY = 'lumicorepro_cookie_consent';

function getStoredConsent() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch (e) {
    return null;
  }
}

/**
 * CookieConsent root component — mounts once, renders a banner until a choice is made.
 */
export default function CookieConsent() {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (!getStoredConsent()) setVisible(true);
    setMounted(true);
  }, []);

  const decide = (analytics, marketing) => {
    const consent = { essential: true, analytics, marketing };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
    setVisible(false);
    window.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: consent }));
  };

  if (!mounted || !visible) return null;

  return (
    <div
      role="dialog"
      aria-modal="false"
      aria-label={t('consent.title')}
      className="fixed inset-x-4 bottom-4 z-50 mx-auto max-w-xl rounded-xl border border-slate-200 bg-white p-4 shadow-2xl md:left-auto md:right-4 transition-all duration-200 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {t('consent.title')}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
            {t('consent.description')}{' '}
            <a
              href="/privacy"
              className="text-primary underline-offset-2 hover:underline"
            >
              {t('consent.privacyPolicy')}
            </a>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setVisible(false)}
          aria-label={t('common.close')}
          className="rounded p-1 text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => decide(true, true)}
          className="flex-1 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground transition-colors duration-200 hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          {t('consent.acceptAll')}
        </button>
        <button
          type="button"
          onClick={() => decide(true, false)}
          className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 transition-colors duration-200 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {t('consent.essentialOnly')}
        </button>
      </div>
    </div>
  );
}