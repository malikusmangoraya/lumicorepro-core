import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Cookie } from 'lucide-react';

const CONSENT_KEY = 'bf_cookie_consent';

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let decided;
    try {
      decided = window.localStorage.getItem(CONSENT_KEY);
    } catch (_e) {
      decided = null;
    }
    if (decided !== 'true' && decided !== 'false') setVisible(true);
  }, []);

  const decide = (value) => {
    try {
      window.localStorage.setItem(CONSENT_KEY, value);
    } catch (_e) { /* storage blocked: banner re-appears next visit */ }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div role="region" aria-label="Cookie consent" data-testid="cookie-consent"
      className="fixed bottom-4 inset-x-4 sm:inset-x-auto sm:right-4 sm:max-w-md z-50 rounded-2xl border border-slate-800 bg-slate-900/95 p-4 shadow-2xl">
      <div className="flex items-start gap-3">
        <Cookie className="h-5 w-5 text-brand-accent shrink-0" aria-hidden="true" />
        <p className="text-sm text-slate-300 leading-relaxed">
          We set one preference cookie to remember your language and this consent choice. No analytics,
          tracking or advertising cookies are used. See the{' '}
          <Link to="/privacy#cookies" className="text-brand-accent underline hover:text-white">cookie policy</Link>.
        </p>
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <button type="button" onClick={() => decide('false')}
          className="px-4 py-2 rounded-full text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors duration-200">
          Decline
        </button>
        <button type="button" onClick={() => decide('true')}
          className="px-4 py-2 rounded-full text-xs font-bold bg-brand-primary text-white hover:opacity-90 transition-opacity duration-200">
          Accept all
        </button>
      </div>
    </div>
  );
}
