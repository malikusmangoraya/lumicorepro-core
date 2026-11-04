'use client';

import { useEffect, useSyncExternalStore } from 'react';
import Link from 'next/link';
import { Cookie } from 'lucide-react';
import { getString, setString, subscribe } from '@/lib/local-store';

const KEY = 'apex:consent';
const GA_ID = process.env.NEXT_PUBLIC_GA_ID ?? '';

/**
 * Consent gate for analytics. No tag is loaded — not even a stub — until the
 * visitor accepts, which is what GDPR and the ePrivacy directive actually ask
 * for. Rejecting is as easy as accepting.
 *
 * The stored choice is read through useSyncExternalStore rather than copied
 * into state in an effect, so there is no cascading render and no banner flash
 * for visitors who already decided.
 */
export function ConsentBanner() {
  const ready = useSyncExternalStore(subscribe, () => true, () => false);
  const stored = useSyncExternalStore(subscribe, () => getString(KEY), () => null);
  const choice = stored === 'accepted' || stored === 'rejected' ? stored : null;

  // Loading the tag is a DOM concern (not React state), so it belongs in an
  // effect: the effect only touches document.head and is idempotent.
  useEffect(() => {
    if (choice !== 'accepted' || !GA_ID) return;
    if (document.getElementById('ga4')) return;

    const script = document.createElement('script');
    script.id = 'ga4';
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(script);

    const inline = document.createElement('script');
    inline.id = 'ga4-init';
    inline.textContent = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${GA_ID}',{anonymize_ip:true});`;
    document.head.appendChild(inline);
  }, [choice]);

  // Nothing renders until hydration, and nothing renders once a choice exists.
  if (!ready || choice !== null) return null;

  return (
    <div
      role="dialog"
      aria-live="polite"
      aria-label="Cookie choice"
      className="fixed inset-x-3 bottom-3 z-[95] mx-auto max-w-2xl rounded-panel border border-line bg-surface/95 p-4 shadow-[0_18px_50px_-20px_rgb(0_0_0/0.9)] backdrop-blur sm:inset-x-4 sm:bottom-4"
    >
      <div className="flex flex-wrap items-start gap-3">
        <Cookie className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="text-sm text-heading">Cookies</p>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            We set one session cookie when you sign in, and nothing else unless you allow analytics.
            See the{' '}
            <Link href="/privacy" className="text-accent hover:underline">
              privacy policy
            </Link>
            .
          </p>
        </div>
        <div className="flex w-full gap-2 sm:w-auto">
          <button
            type="button"
            onClick={() => setString(KEY, 'rejected')}
            className="flex-1 rounded-control border border-line px-3 py-2 text-xs font-semibold text-heading transition-colors hover:border-primary/60 sm:flex-none"
          >
            Essential only
          </button>
          <button
            type="button"
            onClick={() => setString(KEY, 'accepted')}
            className="flex-1 rounded-control bg-primary px-3 py-2 text-xs font-semibold text-[#0b0616] transition-colors hover:bg-accent sm:flex-none"
          >
            Allow analytics
          </button>
        </div>
      </div>
    </div>
  );
}
