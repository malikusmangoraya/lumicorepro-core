/**
 * Cache layer for Apex Digital.
 *
 * Strategy per request type:
 *   navigations      network-first, fall back to the cached shell, then offline.html
 *   hashed assets    cache-first (the filename changes when the file changes)
 *   other same-origin stale-while-revalidate
 *   the API and any cross-origin request  never cached
 *
 * Everything here is resolved relative to this worker's own location rather
 * than to the domain root. These demos are served from a GitHub Pages
 * *subpath* (`/<repo>/`), so a leading-slash URL like `/sw.js` or `/offline.html`
 * points at the apex domain and 404s - and a worker registered at scope `/`
 * would try to control every repo on that Pages host.
 *
 * CACHE_VERSION is baked in at build time; bumping it deletes every previous
 * cache on activate, which is what makes a redeploy take effect immediately
 * instead of leaving buyers on a stale shell.
 */
const CACHE_VERSION = 'v1-apex';
const SHELL_CACHE = `shell-${CACHE_VERSION}`;
const ASSET_CACHE = `assets-${CACHE_VERSION}`;

// sw.js is emitted at the app root, so './' relative to it is the app root.
const BASE = new URL('./', self.location.href).pathname;
const OFFLINE_URL = BASE + 'offline.html';

const SHELL = [BASE, BASE + 'index.html', OFFLINE_URL];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      // A shell entry that fails to fetch must not abort the whole install.
      .then((cache) => Promise.allSettled(SHELL.map((url) => cache.add(url))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k.startsWith('shell-') || k.startsWith('assets-'))
            .filter((k) => k !== SHELL_CACHE && k !== ASSET_CACHE)
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

function isAsset(url) {
  return url.pathname.startsWith(BASE + 'assets/') ||
    /\.[a-z0-9]{2,5}$/i.test(url.pathname);
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Never cache the API or anything cross-origin - a stale response to a
  // mutation is worse than a slow one. The API path is base-relative for the
  // same reason the shell is: it lives under '/<repo>/api/', not '/api/'.
  if (
    url.origin !== self.location.origin ||
    url.pathname.startsWith(BASE + 'api/')
  ) {
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((c) => c.put(request, copy));
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL)),
        ),
    );
    return;
  }

  if (isAsset(url)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const network = fetch(request)
          .then((response) => {
            if (response && response.status === 200 && response.type === 'basic') {
              const copy = response.clone();
              caches.open(ASSET_CACHE).then((c) => c.put(request, copy));
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      }),
    );
  }
});
