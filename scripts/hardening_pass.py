#!/usr/bin/env python3
"""Add the two layers the catalogue is missing: CSP and a real cache.

Surveying the ten products turned up that the hardening is half-done:

* `_headers` sets HSTS, nosniff, X-Frame-Options, Referrer-Policy,
  Permissions-Policy and the COOP/COEP/CORP trio, and the backend runs helmet,
  rate limiting and `httpOnly`/`secure`/`sameSite` cookies. All good.
* **No Content-Security-Policy anywhere** - not in `_headers`, not configured on
  helmet, not as a meta tag.
* **No service worker**, so the demos get no offline shell and no cache
  strategy, only whatever the host happens to send.
* `_headers` is a Cloudflare/Netlify convention. **GitHub Pages ignores it** -
  and GitHub Pages is where these ten are published. So the demo deployments
  ship with *no* security headers at all today, and a meta tag is the only
  header mechanism that actually reaches a Pages visitor.

This adds, per product:

1. A `<meta http-equiv="Content-Security-Policy">` in `index.html`, which works
   on GitHub Pages, Cloudflare and Netlify alike.
2. The same policy in `_headers`, for the hosts that do honour it.
3. `public/sw.js` - a versioned service worker: app shell precached, hashed
   assets served stale-while-revalidate, navigations network-first with an
   offline fallback, and `/api` never cached.
4. `public/offline.html` - the offline fallback page.
5. `src/sw-register.js` - registration that only runs in production.

Two deliberate choices, both about not breaking a buyer's deployment:

* `connect-src` allows any https origin, because `VITE_API_URL` is the buyer's
  to set. Locking it to a fixed allowlist would break every deployment that
  points the frontend at its own API.
* `script-src` keeps `'unsafe-inline'`. Vite injects an inline module preload
  helper into the built HTML, and a CSP that blocks it breaks the app silently.
  Remove it once you can build and test the bundle - see DEPLOYMENT.md.

Usage:  python scripts/hardening_pass.py [--dry-run] [--only slug ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

TARGETS = [
    "apex", "aurelia-estates", "aurum-fitness", "claimflow-ai",
    "meridian-capital", "nuage-events", "prestige-studio", "resupro",
    "saffron-voyage", "studio-lumen",
]

# Directives that cannot break a reasonable deployment:
#   base-uri      - stops a <base> tag hijacking every relative URL
#   object-src    - stops plugin content (the classic XSS vector)
#   frame-ancestors - clickjacking
#   form-action   - stops credentials being posted to an attacker's origin
# 'unsafe-inline' on style is required: Tailwind and React inline styles are
# used throughout. See the module docstring for the script-src caveat.
CSP_DIRECTIVES = [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "form-action 'self' https://*.lemonsqueezy.com",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data: https://fonts.gstatic.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "script-src 'self' 'unsafe-inline' https://app.posthog.com https://plausible.io",
    "connect-src 'self' https: https://app.posthog.com https://plausible.io https://*.lemonsqueezy.com",
    "worker-src 'self' blob:",
    "manifest-src 'self'",
]

# `upgrade-insecure-requests` and `frame-ancestors` are deliberately NOT in the
# meta policy:
#   upgrade-insecure-requests rewrites http://localhost subresource requests to
#   https and breaks `npm run dev` on a plain http origin. HSTS in `_headers`
#   already covers the real deployments, and GitHub Pages is https-only.
#   frame-ancestors is ignored by spec when delivered as a meta tag, so putting
#   it there only looks like protection. It is set in `_headers` instead, where
#   it is actually honoured.
HEADER_ONLY_DIRECTIVES = [
    "frame-ancestors 'none'",
    "upgrade-insecure-requests",
]

META_TAG = '<meta http-equiv="Content-Security-Policy" content="{policy}" />'

SERVICE_WORKER = Template("""/**
 * Cache layer for $name.
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
const CACHE_VERSION = '$version';
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
    /\\.[a-z0-9]{2,5}$/i.test(url.pathname);
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
""")

OFFLINE_PAGE = Template("""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Offline — $name</title>
    <style>
      :root { color-scheme: light dark; }
      * { box-sizing: border-box; }
      body {
        margin: 0; min-height: 100vh; display: grid; place-items: center;
        font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
        background: #f7f3ea; color: #26292f; padding: 24px;
      }
      @media (prefers-color-scheme: dark) {
        body { background: #0e1116; color: #e8eaed; }
      }
      main { max-width: 32rem; text-align: center; }
      h1 { font-size: 1.5rem; margin: 0 0 0.5rem; letter-spacing: -0.02em; }
      p { margin: 0 0 1.5rem; opacity: 0.75; }
      button {
        font: inherit; font-weight: 600; cursor: pointer;
        padding: 0.7rem 1.4rem; border-radius: 0.75rem;
        border: 1px solid currentColor; background: transparent; color: inherit;
      }
      button:hover { background: color-mix(in srgb, currentColor 10%, transparent); }
    </style>
  </head>
  <body>
    <main>
      <h1>You are offline</h1>
      <p>
        This page needs a connection. Reconnect and try again — anything you had
        already loaded will still be here.
      </p>
      <button type="button" onclick="window.location.reload()">Retry</button>
    </main>
  </body>
</html>
""")

SW_REGISTER = """/**
 * Service worker registration.
 *
 * The URL and the scope are both taken from Vite's BASE_URL, because these
 * apps are served from a GitHub Pages subpath: BASE_URL is `/<repo>/` in the
 * Pages workflow. Registering `/sw.js` instead would request the apex domain,
 * where nothing answers, and the default `/` scope would claim control of every
 * repository on that Pages host rather than this one.
 *
 * Registration is skipped outside production on purpose: a cached shell during
 * development serves yesterday's bundle and makes every change look like it did
 * not apply. The worker itself clears old caches on activate, so a redeploy
 * reaches returning visitors without a manual refresh.
 */
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  const base = import.meta.env.BASE_URL || './';
  // './' (a relative base) has to be resolved against the current document;
  // an absolute base such as '/<repo>/' is already a usable path prefix.
  const scope = base.startsWith('.')
    ? new URL(base, document.baseURI).href
    : new URL(base, document.location.origin).href;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(new URL('sw.js', scope).href, { scope })
      .catch(() => {
        // A failed registration must never break the app; caching is an
        // enhancement, not a requirement.
      });
  });
}
"""


def brand_name(slug: str) -> str:
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from brand_map import BRANDS
        return BRANDS.get(slug, {}).get("name", slug)
    except Exception:
        return slug


def add_meta(html: str, policy: str) -> str:
    """Insert, or bring up to date, the CSP meta tag.

    Replacing rather than skipping on a second run means a policy change
    actually reaches the product instead of leaving a stale directive behind.
    """
    tag = META_TAG.format(policy=policy)
    existing = re.search(
        r"[ \t]*<meta http-equiv=\"Content-Security-Policy\"[^>]*/>\n?", html)
    if existing:
        return html[:existing.start()] + "    " + tag + "\n" + html[existing.end():]

    # After the viewport meta, before anything that can be blocked.
    anchor = '<meta name="viewport"'
    i = html.find(anchor)
    if i < 0:
        return html
    end = html.find(">", i) + 1
    return html[:end] + "\n    " + tag + html[end:]


def add_headers_block(text: str, policy: str) -> str:
    # Hosts that honour `_headers` additionally get the two directives that a
    # meta tag cannot express.
    full = "; ".join(CSP_DIRECTIVES + HEADER_ONLY_DIRECTIVES)
    line = f"  Content-Security-Policy: {full}\n"
    existing = re.search(r"[ \t]*Content-Security-Policy: .*\n", text)
    if existing:
        return text[:existing.start()] + line + text[existing.end():]

    block = (
        "\n# Content-Security-Policy\n"
        "# GitHub Pages ignores this file; the same policy ships as a <meta> tag\n"
        "# in index.html so Pages visitors are covered too. This block adds\n"
        "# frame-ancestors and upgrade-insecure-requests, which a meta tag\n"
        "# cannot carry.\n"
        "/*\n"
    )
    return text.rstrip("\n") + "\n" + block + line
    # Hosts that honour `_headers` additionally get the two directives that a
    # meta tag cannot express.
    full = "; ".join(CSP_DIRECTIVES + HEADER_ONLY_DIRECTIVES)
    block = (
        "\n# Content-Security-Policy\n"
        "# GitHub Pages ignores this file; the same policy ships as a <meta> tag\n"
        "# in index.html so Pages visitors are covered too. This block adds\n"
        "# frame-ancestors and upgrade-insecure-requests, which a meta tag\n"
        "# cannot carry.\n"
        "/*\n"
        f"  Content-Security-Policy: {full}\n"
    )
    return text.rstrip("\n") + "\n" + block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    slugs = args.only or TARGETS
    policy = "; ".join(CSP_DIRECTIVES)
    problems, changed = [], []

    for slug in slugs:
        fe = PRODUCTS_DIR / slug / "frontend"
        index = fe / "index.html"
        if not index.is_file():
            problems.append(f"{slug}: no frontend/index.html")
            continue

        name = brand_name(slug)
        version = f"v1-{slug}"

        writes: dict[Path, str] = {}

        html = index.read_text(encoding="utf-8", errors="replace")
        new_html = add_meta(html, policy)
        if new_html != html:
            writes[index] = new_html

        headers = fe / "public/_headers"
        if headers.is_file():
            h = headers.read_text(encoding="utf-8", errors="replace")
            new_h = add_headers_block(h, policy)
            if new_h != h:
                writes[headers] = new_h

        writes[fe / "public/sw.js"] = SERVICE_WORKER.safe_substitute(
            name=name, version=version)
        writes[fe / "public/offline.html"] = OFFLINE_PAGE.safe_substitute(name=name)
        writes[fe / "src/sw-register.js"] = SW_REGISTER

        main_jsx = fe / "src/main.jsx"
        if main_jsx.is_file():
            m = main_jsx.read_text(encoding="utf-8", errors="replace")
            if "sw-register" not in m:
                if "import './index.css';" not in m:
                    problems.append(f"{slug}: cannot find the import anchor in main.jsx")
                else:
                    m = m.replace(
                        "import './index.css';",
                        "import './index.css';\nimport './sw-register.js';",
                        1,
                    )
                    writes[main_jsx] = m

        written = []
        for path, body in writes.items():
            if path.is_file() and path.read_text(encoding="utf-8", errors="replace") == body:
                continue
            written.append(path)
            if not args.dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")

        if written:
            changed.append(slug)
            print(f"  [{slug}] {len(written)} file(s): "
                  + ", ".join(p.name for p in sorted(written)))

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1

    verb = "would change" if args.dry_run else "updated"
    print(f"\n{verb}: {', '.join(changed) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())