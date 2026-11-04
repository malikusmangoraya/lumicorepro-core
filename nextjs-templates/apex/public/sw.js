/*
 * A deliberately conservative service worker.
 *
 * Rules that keep it from breaking a live site:
 *  - only GET requests are touched;
 *  - /api and anything with a query string is never cached;
 *  - pages are network-first, so a deploy is picked up immediately and the
 *    offline page is a fallback, not the default;
 *  - only hashed static assets are cached, so a stale entry cannot outlive its
 *    filename.
 */

const CACHE = 'apex-v1';
const OFFLINE = '/offline';
const PRECACHE = [OFFLINE, '/icons/icon-192.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE).then((hit) => hit || Response.error())),
    );
    return;
  }

  if (/\.(css|js|woff2?|png|jpe?g|webp|avif|svg)$/.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then((hit) => {
        if (hit) return hit;
        return fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        });
      }),
    );
  }
});
