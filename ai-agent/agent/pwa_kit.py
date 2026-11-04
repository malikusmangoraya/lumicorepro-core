"""Pure PWA emitter for generated web surfaces (Task 4).

The kit owns only the artifacts a browser needs to install the app, render a
last-resort offline page and replay record writes. It never claims that an
offline write reached the server: queued records are reported as queued.

`pwa_files` is deterministic: the same brand and design system produce the same
icons and the same versioned cache name, so regeneration does not churn assets.
"""
from __future__ import annotations

import io
import json
import re
from typing import Any, Dict, Union


PWA_FILE_TYPE = Union[str, bytes]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "app"


def _icon_png(design: Dict[str, Any], size: int) -> bytes:
    """Render a flat, deterministic brand mark; no fonts or remote assets."""
    from PIL import Image, ImageDraw

    primary = design["primary"]
    surface = design["slate"]["950"]
    accent = design["accent"]
    image = Image.new("RGB", (size, size), primary)
    draw = ImageDraw.Draw(image)
    inset = max(6, int(size * 0.14))
    draw.rounded_rectangle(
        [inset, inset, size - inset, size - inset],
        radius=max(8, int(size * 0.18)),
        fill=surface,
    )
    stroke = max(4, int(size * 0.075))
    draw.line(
        [
            (int(size * 0.30), int(size * 0.66)),
            (int(size * 0.50), int(size * 0.32)),
            (int(size * 0.70), int(size * 0.66)),
        ],
        fill=accent,
        width=stroke,
        joint="curve",
    )
    draw.rectangle(
        [int(size * 0.30), int(size * 0.68), int(size * 0.70), int(size * 0.73)],
        fill=primary,
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _manifest(brand: str, design: Dict[str, Any]) -> str:
    manifest = {
        "name": brand,
        "short_name": (brand[:12] if len(brand) > 12 else brand),
        "description": f"{brand} workspace",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "theme_color": design["primary"],
        "background_color": design["slate"]["950"],
        "icons": [
            {
                "src": "/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
        ],
    }
    return json.dumps(manifest, indent=2) + "\n"


def _service_worker(brand: str, design: Dict[str, Any]) -> str:
    version = f"lumicore-{_slug(brand)}-{int(float(design['hue']))}-v1"
    return r"""'use strict';

const VERSION = '__VERSION__';
const SHELL_CACHE = `${VERSION}-shell`;
const STATIC_CACHE = `${VERSION}-static`;
const PRECACHE = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// A new worker installs and waits: the page owns the visible update prompt
// and activates it explicitly with SKIP_WAITING. Silent skipWaiting would
// replace the worker without ever telling the user.
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(PRECACHE)),
  );
});

self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (data.type === 'GET_VERSION' && event.ports && event.ports[0]) {
    event.ports[0].postMessage({ version: VERSION });
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith('lumicore-') && !key.startsWith(VERSION))
          .map((key) => caches.delete(key)),
      ))
      .then(() => self.clients.claim()),
  );
});

function store(cacheName, request, response) {
  if (!response || !response.ok) return response;
  const copy = response.clone();
  caches.open(cacheName)
    .then((cache) => cache.put(request, copy))
    .catch(() => {});
  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Private API responses are network-only and bypass Cache Storage entirely.
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request, { cache: 'no-store' }).catch(() => new Response(
        JSON.stringify({ success: false, message: 'You are offline.' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } },
      )),
    );
    return;
  }

  // Navigation is network-first with the offline shell as the fallback.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(async () => (
        (await caches.match('/offline.html')) ||
        (await caches.match('/index.html')) ||
        new Response('You are offline.', {
          status: 503,
          headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        })
      )),
    );
    return;
  }

  // Same-origin static assets are cache-first, then refreshed in the background.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => store(STATIC_CACHE, request, response));
    }),
  );
});
""".replace("__VERSION__", version)


def _offline_html(brand: str, design: Dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="{design['primary']}">
    <title>{brand} — Offline</title>
    <style>
      :root {{
        color-scheme: dark;
        --surface: {design['slate']['950']};
        --raised: {design['slate']['900']};
        --line: {design['slate']['700']};
        --ink: {design['ink']};
        --muted: {design['muted']};
        --action: {design['accent']};
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 2rem;
        background: var(--surface);
        color: var(--ink);
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      }}
      main {{
        width: min(100%, 34rem);
        padding: clamp(1.5rem, 5vw, 2.5rem);
        border: 1px solid var(--line);
        border-radius: 1.25rem;
        background: var(--raised);
      }}
      p {{ color: var(--muted); line-height: 1.6; }}
      button {{
        margin-top: 1.25rem;
        padding: 0.7rem 1.1rem;
        border: 1px solid transparent;
        border-radius: 0.65rem;
        background: var(--action);
        color: {design['slate']['950']};
        font: inherit;
        font-weight: 700;
        cursor: pointer;
      }}
      :focus-visible {{ outline: 2px solid var(--action); outline-offset: 3px; }}
    </style>
  </head>
  <body>
    <main>
      <p>{brand}</p>
      <h1>You're offline</h1>
      <p>This device cannot reach the workspace right now. Reconnect, then retry.</p>
      <button type="button" onclick="location.reload()">Retry connection</button>
    </main>
  </body>
</html>
"""


_OFFLINE_QUEUE_JS = r"""import { API, currentUserId, getToken } from './auth.js';

const DB_NAME = 'lumicore-queue';
const STORE_NAME = 'records';
const DB_VERSION = 2;
const MAX_RECORDS = 50;
const FLUSH_ATTEMPTS = 3;
const RETRY_DELAY_MS = 800;
const QUEUE_EVENT = 'lumicore:queue';
const STATUSES = ['draft', 'published', 'archived'];
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
let flushPromise = null;

function notify() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(QUEUE_EVENT));
  }
}

export function queueOwner() {
  const value = currentUserId();
  return value === null || value === undefined ? '' : String(value);
}

function wait(milliseconds) {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      // The queue is keyed by owner first: a record can never be read or
      // flushed by a different signed-in account. Legacy unscoped rows are
      // discarded rather than adopted by whoever is signed in next.
      if (database.objectStoreNames.contains(STORE_NAME)) {
        database.deleteObjectStore(STORE_NAME);
      }
      database.createObjectStore(STORE_NAME, { keyPath: ['owner', 'id'] });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function rows() {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const request = database
      .transaction(STORE_NAME, 'readonly')
      .objectStore(STORE_NAME)
      .getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

function forOwner(all, owner) {
  return all.filter((row) => row.owner === owner);
}

function validate(record, owner) {
  if (!owner) {
    throw new Error('Sign in to queue records');
  }
  if (!record || typeof record !== 'object' || Array.isArray(record)) {
    throw new Error('Invalid queued record');
  }
  if (!UUID_RE.test(String(record.id || ''))) {
    throw new Error('Invalid queued record id');
  }
  const title = typeof record.title === 'string' ? record.title.trim() : '';
  const body = typeof record.body === 'string' ? record.body : '';
  const status = STATUSES.includes(record.status) ? record.status : 'draft';
  const method = record.method === 'PUT' ? 'PUT' : 'POST';
  if (!title || title.length > 160 || body.length > 10000) {
    throw new Error('Invalid queued record body');
  }
  return { owner, id: record.id, method, title, body, status, queuedAt: Date.now() };
}

export async function enqueue(record) {
  const owner = queueOwner();
  const item = validate(record, owner);
  const existing = forOwner(await rows(), owner);
  if (!existing.some((row) => row.id === item.id) && existing.length >= MAX_RECORDS) {
    throw new Error('Offline queue is full');
  }
  const database = await openDatabase();
  await new Promise((resolve, reject) => {
    const request = database
      .transaction(STORE_NAME, 'readwrite')
      .objectStore(STORE_NAME)
      .put(item);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
  notify();
  return item;
}

export async function count() {
  const owner = queueOwner();
  if (!owner) return 0;
  return forOwner(await rows(), owner).length;
}

async function remove(owner, id) {
  const database = await openDatabase();
  await new Promise((resolve, reject) => {
    const request = database
      .transaction(STORE_NAME, 'readwrite')
      .objectStore(STORE_NAME)
      .delete([owner, id]);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function send(item, session) {
  // Refuse to send after sign-out or a token swap. Comparing the live token
  // and owner on every item is what keeps another user's session from
  // replaying the previous user's queue.
  if (item.owner !== session.owner || queueOwner() !== session.owner
      || !session.token || getToken() !== session.token) {
    throw new Error('Queue owner changed');
  }
  const method = item.method === 'PUT' ? 'PUT' : 'POST';
  const url = method === 'PUT'
    ? `${API}/records/${encodeURIComponent(item.id)}`
    : `${API}/records`;
  const payload = method === 'PUT'
    ? { title: item.title, body: item.body, status: item.status }
    : { id: item.id, title: item.title, body: item.body, status: item.status };
  const response = await fetch(url, {
    method,
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session.token}`,
    },
    body: JSON.stringify(payload),
  });
  let json = null;
  try {
    json = await response.json();
  } catch (error) {
    json = null;
  }
  if (!response.ok || !json || json.success !== true) {
    throw new Error('Queued record was not accepted');
  }
}

async function drain() {
  const owner = queueOwner();
  const token = getToken();
  if (!owner || !token) {
    return { sent: 0, remaining: 0 };
  }
  const session = { owner, token };
  const queued = forOwner(await rows(), owner);
  let sent = 0;
  for (const item of queued) {
    await send(item, session);
    await remove(owner, item.id);
    sent += 1;
  }
  return { sent, remaining: forOwner(await rows(), owner).length };
}

async function drainWithRetry() {
  const owner = queueOwner();
  if (!owner) {
    return { sent: 0, remaining: 0 };
  }
  let lastError = null;
  for (let attempt = 0; attempt < FLUSH_ATTEMPTS; attempt += 1) {
    if (queueOwner() !== owner) {
      throw new Error('Queue owner changed');
    }
    try {
      return await drain();
    } catch (error) {
      lastError = error;
      if (attempt + 1 < FLUSH_ATTEMPTS) {
        await wait(RETRY_DELAY_MS * (attempt + 1));
      }
    }
  }
  throw lastError || new Error('Queued records were not sent');
}

export async function flush() {
  if (!flushPromise) {
    flushPromise = drainWithRetry()
      .finally(() => {
        flushPromise = null;
        notify();
      });
  }
  return flushPromise;
}

export async function clearQueue(owner) {
  const ownerId = owner === undefined || owner === null ? queueOwner() : String(owner || '');
  if (!ownerId) return 0;
  const queued = forOwner(await rows(), ownerId);
  for (const item of queued) {
    await remove(ownerId, item.id);
  }
  notify();
  return queued.length;
}
"""


_PWA_BANNER_JS = r"""import { clearQueue, count, flush } from './offlineQueue.js';

const BANNER_ID = 'pwa-connection-banner';

function ensureBanner() {
  let banner = document.getElementById(BANNER_ID);
  if (banner) return banner;
  banner = document.createElement('div');
  banner.id = BANNER_ID;
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  banner.dataset.pwaQueueCount = '0';
  Object.assign(banner.style, {
    position: 'fixed',
    insetInline: '0',
    bottom: '0',
    zIndex: '60',
    padding: '0.7rem 1rem',
    background: '#0b1020',
    color: '#f8fafc',
    borderTop: '1px solid rgba(148, 163, 184, 0.4)',
    font: '600 0.9rem/1.4 system-ui, -apple-system, "Segoe UI", sans-serif',
    textAlign: 'center',
  });
  document.body.appendChild(banner);
  return banner;
}

async function refresh() {
  const banner = ensureBanner();
  let queued = 0;
  try {
    queued = await count();
  } catch (error) {
    queued = 0;
  }
  banner.dataset.pwaQueueCount = String(queued);
  const offline = !navigator.onLine;
  banner.hidden = !offline && queued === 0;
  banner.textContent = offline
    ? `You're offline. ${queued} record(s) queued on this device.`
    : `${queued} record(s) queued. Sync pending.`;
}

async function sync() {
  try {
    await flush();
  } catch (error) {
    // The queue keeps unsent records; the banner still reports the count.
  }
  await refresh();
}

async function discardPreviousQueue(event) {
  const detail = event && event.detail ? event.detail : {};
  try {
    await clearQueue(detail.userId || '');
  } catch (error) {
    // Best effort: owner-scoped reads still hide another user's rows.
  }
  await refresh();
}

function boot() {
  ensureBanner();
  refresh();
  window.addEventListener('online', sync);
  window.addEventListener('offline', refresh);
  window.addEventListener('lumicore:queue', refresh);
  window.addEventListener('lumicore:signout', discardPreviousQueue);
  if (navigator.onLine) {
    // A queued write from a previous visit must not wait for the browser to
    // fire another online event before it is sent.
    sync();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
"""


_PWA_UPDATE_JS = r"""const SW_URL = '/sw.js';
const PROMPT_ID = 'pwa-update-prompt';
let reloadRequested = false;

function showPrompt(registration) {
  if (!registration || !registration.waiting || !navigator.serviceWorker.controller
      || document.getElementById(PROMPT_ID)) {
    return;
  }
  const region = document.createElement('div');
  region.id = PROMPT_ID;
  region.setAttribute('role', 'status');
  region.setAttribute('aria-live', 'polite');
  region.setAttribute('aria-label', 'Application update available');
  Object.assign(region.style, {
    position: 'fixed',
    top: '0',
    insetInline: '0',
    zIndex: '70',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem 1rem',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.7rem 1rem',
    background: '#0b1020',
    color: '#f8fafc',
    borderBottom: '1px solid rgba(148, 163, 184, 0.4)',
    font: '600 0.9rem/1.4 system-ui, -apple-system, "Segoe UI", sans-serif',
    textAlign: 'center',
  });

  const message = document.createElement('span');
  message.textContent = 'A new version of this app is ready.';

  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Reload to update';
  Object.assign(button.style, {
    padding: '0.35rem 0.8rem',
    border: '1px solid #f8fafc',
    borderRadius: '0.5rem',
    background: '#f8fafc',
    color: '#0b1020',
    font: 'inherit',
    fontWeight: '700',
    cursor: 'pointer',
  });
  button.addEventListener('click', () => {
    if (reloadRequested) return;
    const waiting = registration.waiting;
    reloadRequested = true;
    button.disabled = true;
    button.textContent = 'Updating…';
    if (waiting) {
      waiting.postMessage({ type: 'SKIP_WAITING' });
    } else {
      window.location.reload();
    }
  });

  region.append(message, button);
  document.body.appendChild(region);
}

function watch(registration) {
  if (!registration) return;
  // A worker may already be waiting from an earlier visit.
  showPrompt(registration);
  registration.addEventListener('updatefound', () => {
    const installing = registration.installing;
    if (!installing) return;
    installing.addEventListener('statechange', () => {
      if (installing.state === 'installed') {
        showPrompt(registration);
      }
    });
  });
}

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(SW_URL)
      .then(watch)
      .catch(() => {});
    // Only a user-requested activation reloads the page; the first install's
    // clients.claim() must not force a reload.
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (reloadRequested) {
        window.location.reload();
      }
    });
  });
}
"""


_PWA_RECORDS_JSX = r"""import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { request } from '../auth.js';
import { count, enqueue, flush } from '../offlineQueue.js';

const STATUSES = ['draft', 'published', 'archived'];
const LABELS = { draft: 'Draft', published: 'Published', archived: 'Archived' };
const EMPTY_FORM = { title: '', body: '', status: 'draft' };

function normalize(record) {
  const status = STATUSES.includes(record.status) ? record.status : 'draft';
  return {
    id: String(record.id || ''),
    title: String(record.title || ''),
    body: String(record.body || ''),
    status,
  };
}

export default function Records() {
  const [records, setRecords] = useState([]);
  const [state, setState] = useState('loading');
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState('');
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [queued, setQueued] = useState(0);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setState('loading');
    setError('');
    try {
      const json = await request('/records');
      const rows = Array.isArray(json.data) ? json.data : [];
      setRecords(rows.map(normalize));
      setState('ready');
    } catch (failure) {
      setError('We could not load your records.');
      setState('error');
    }
  }, []);

  const refreshQueue = useCallback(async () => {
    try {
      setQueued(await count());
    } catch (failure) {
      setQueued(0);
    }
  }, []);

  useEffect(() => {
    load();
    refreshQueue();
  }, [load, refreshQueue]);

  useEffect(() => {
    const onOnline = async () => {
      setOnline(true);
      try {
        await flush();
      } catch (failure) {
        // Unsent records stay in IndexedDB and remain visibly queued.
      }
      await refreshQueue();
      await load();
    };
    const onOffline = () => setOnline(false);
    const onQueue = () => refreshQueue();
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    window.addEventListener('lumicore:queue', onQueue);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
      window.removeEventListener('lumicore:queue', onQueue);
    };
  }, [load, refreshQueue]);

  const visible = useMemo(() => {
    const term = search.trim().toLowerCase();
    return records.filter((record) => {
      if (statusFilter !== 'all' && record.status !== statusFilter) return false;
      if (!term) return true;
      return record.title.toLowerCase().includes(term)
        || record.body.toLowerCase().includes(term);
    });
  }, [records, search, statusFilter]);

  const resetForm = () => {
    setEditingId('');
    setForm(EMPTY_FORM);
    setFormError('');
  };

  const beginEdit = (record) => {
    setEditingId(record.id);
    setForm({ title: record.title, body: record.body, status: record.status });
    setFormError('');
    setNotice('');
    window.scrollTo({ top: 0 });
  };

  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const title = form.title.trim();
    const body = form.body.trim();
    if (!title) {
      setFormError('Add a title before saving.');
      return;
    }
    if (title.length > 160) {
      setFormError('Keep the title at 160 characters or fewer.');
      return;
    }
    if (body.length > 10000) {
      setFormError('Keep the description at 10000 characters or fewer.');
      return;
    }
    setBusy(true);
    setFormError('');
    setNotice('');
    const wasEditing = Boolean(editingId);
    const recordId = editingId || crypto.randomUUID();
    const queueWrite = async () => {
      await enqueue({
        id: recordId, method: wasEditing ? 'PUT' : 'POST',
        title, body, status: form.status,
      });
      await refreshQueue();
      setNotice('Queued on this device. It will sync automatically.');
      resetForm();
    };
    try {
      if (!navigator.onLine) {
        await queueWrite();
        return;
      }
      if (wasEditing) {
        await request(`/records/${recordId}`, {
          method: 'PUT',
          body: { title, body, status: form.status },
        });
      } else {
        await request('/records', {
          method: 'POST',
          body: { id: recordId, title, body, status: form.status },
        });
      }
      resetForm();
      await load();
      await refreshQueue();
    } catch (failure) {
      if (!navigator.onLine || failure instanceof TypeError) {
        try {
          await queueWrite();
        } catch (queueFailure) {
          setFormError(queueFailure && queueFailure.message === 'Sign in to queue records'
            ? 'Sign in again to queue records.'
            : 'The offline queue is full. Reconnect and try again.');
        }
      } else {
        setFormError('The record was not saved. Check the details and try again.');
      }
    } finally {
      setBusy(false);
    }
  };

  const remove = async (record) => {
    if (!window.confirm(`Delete "${record.title}"? This cannot be undone.`)) return;
    try {
      await request(`/records/${record.id}`, { method: 'DELETE' });
      await load();
    } catch (failure) {
      setError('The record was not deleted. Try again.');
      setState('error');
    }
  };

  return (
    <div className="app-page">
      <header className="app-page-head">
        <div>
          <p className="app-eyebrow">Records</p>
          <h1>All records</h1>
          <p className="app-lede">Search, filter, and manage the records in your account.</p>
        </div>
      </header>

      <p
        id="record-queue"
        className="app-panel"
        role="status"
        aria-live="polite"
        data-queue-count={queued}
        hidden={online && queued === 0}
      >
        {online
          ? `${queued} record(s) queued on this device. Sync pending.`
          : `You're offline. ${queued} record(s) queued on this device.`}
      </p>
      {notice && <p id="record-notice" className="app-note" role="status">{notice}</p>}

      <section className="app-panel" aria-labelledby="record-form-title">
        <h2 id="record-form-title">{editingId ? 'Edit record' : 'Create a record'}</h2>
        <form className="app-form" onSubmit={submit} noValidate aria-busy={busy}>
          <label htmlFor="record-title">Title</label>
          <input
            id="record-title" name="title" type="text" required maxLength={160}
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <label htmlFor="record-body">Description</label>
          <textarea
            id="record-body" name="body" rows={4} maxLength={10000}
            value={form.body}
            onChange={(event) => setForm({ ...form, body: event.target.value })}
          />
          <label htmlFor="record-status">Status</label>
          <select
            id="record-status" name="status" value={form.status}
            onChange={(event) => setForm({ ...form, status: event.target.value })}
          >
            {STATUSES.map((status) => (
              <option key={status} value={status}>{LABELS[status]}</option>
            ))}
          </select>
          {formError && <p className="app-error" role="alert">{formError}</p>}
          <div className="app-actions">
            <button type="submit" className="app-button" disabled={busy}>
              {busy ? 'Saving…' : editingId ? 'Save changes' : 'Create record'}
            </button>
            {editingId && (
              <button type="button" className="app-button app-button-quiet" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="app-toolbar" aria-label="Record filters">
        <div className="app-field">
          <label htmlFor="record-search">Search records</label>
          <input
            id="record-search" name="search" type="search"
            placeholder="Search by title or description"
            value={search} onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="app-field">
          <label htmlFor="record-filter">Status</label>
          <select
            id="record-filter" name="statusFilter" value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All statuses</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>{LABELS[status]}</option>
            ))}
          </select>
        </div>
      </section>

      {state === 'loading' && <p className="app-status" role="status">Loading records…</p>}

      {state === 'error' && (
        <div className="app-panel" role="alert">
          <p>{error}</p>
          <button type="button" className="app-button" onClick={load}>Try again</button>
        </div>
      )}

      {state === 'ready' && (
        visible.length === 0 ? (
          <p className="app-empty">
            {records.length
              ? 'No records match your search.'
              : 'No records yet. Create your first record above.'}
          </p>
        ) : (
          <ul className="app-records" aria-label="Records">
            {visible.map((record) => (
              <li className="app-record" key={record.id}>
                <div className="app-record-head">
                  <h2>{record.title}</h2>
                  <span className={`app-pill app-pill-${record.status}`}>
                    {LABELS[record.status]}
                  </span>
                </div>
                {record.body && <p className="app-record-body">{record.body}</p>}
                <div className="app-actions">
                  <button type="button" className="app-button app-button-quiet"
                    onClick={() => beginEdit(record)}>
                    Edit {record.title}
                  </button>
                  <button type="button" className="app-button app-button-danger"
                    onClick={() => remove(record)}>
                    Delete {record.title}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}
"""


def pwa_files(brand: str, design: Dict[str, Any], *,
              web_app: bool = False) -> Dict[str, PWA_FILE_TYPE]:
    """Return installable PWA assets keyed under `frontend/`.

    `web_app` adds the authenticated offline write queue and the queue-aware
    Records page. A marketing website gets only the offline shell; every
    surface gets a network-only API rule in the service worker.
    """
    files: Dict[str, PWA_FILE_TYPE] = {
        "frontend/public/manifest.webmanifest": _manifest(brand, design),
        "frontend/public/sw.js": _service_worker(brand, design),
        "frontend/public/offline.html": _offline_html(brand, design),
        "frontend/public/icons/icon-192.png": _icon_png(design, 192),
        "frontend/public/icons/icon-512.png": _icon_png(design, 512),
        "frontend/src/pwaUpdate.js": _PWA_UPDATE_JS,
    }
    if web_app:
        files["frontend/src/offlineQueue.js"] = _OFFLINE_QUEUE_JS
        files["frontend/src/pwa.js"] = _PWA_BANNER_JS
        files["frontend/src/pages/Records.jsx"] = _PWA_RECORDS_JSX
    return files


__all__ = ["pwa_files"]
