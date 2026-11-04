'use client';

import { useEffect } from 'react';

/**
 * Registers the service worker in production only.
 *
 * A stale worker is the fastest way to break a live site, so this registers a
 * conservative one: network-first for pages with an offline fallback, cache-first
 * for hashed static assets, nothing cached from /api.
 */
export function ServiceWorkerRegistrar() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') return;
    if (!('serviceWorker' in navigator)) return;

    const register = () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // A failed registration is not worth surfacing: the site works without it.
      });
    };

    if (document.readyState === 'complete') register();
    else window.addEventListener('load', register, { once: true });
  }, []);

  return null;
}
