'use client';

import { useSyncExternalStore } from 'react';
import { X } from 'lucide-react';
import { getString, setString, subscribe } from '@/lib/local-store';
import { site } from '@/lib/site-config';

const KEY = 'apex:promo-dismissed';

/**
 * A promo strip that only exists when an operator sets NEXT_PUBLIC_PROMO.
 * Nothing is invented: an empty value renders no banner at all.
 */
export function PromoBanner() {
  // Server snapshot is "not dismissed" so the strip is server-rendered and the
  // page does not shift after hydration.
  const dismissed = useSyncExternalStore(
    subscribe,
    () => getString(KEY) === '1',
    () => false,
  );

  if (!site.promo || dismissed) return null;

  return (
    <div className="relative border-b border-primary/30 bg-primary/10 px-4 py-2 text-center text-xs font-medium text-accent">
      <span className="pr-8">{site.promo}</span>
      <button
        type="button"
        aria-label="Dismiss announcement"
        onClick={() => setString(KEY, '1')}
        className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-accent/80 transition-colors hover:text-accent"
      >
        <X className="size-3.5" aria-hidden="true" />
      </button>
    </div>
  );
}
