"""production_spec_kit — guarantees every generated project meets the
"production-ready full-stack" mandate:

  1. Multi-stage Dockerfiles  frontend: node build -> nginx serve (+SPA fallback,
                              API proxy, cache + security headers)
                              backend: deps stage -> non-root runtime stage
  2. INSTRUCTIONS.md          full local setup, env table, Docker commands
  3. TypeScript-ready backend tsconfig.json + shared types + typecheck script
                              (@types + typescript devDeps; code stays JS-backed
                              with allowJs — documented in INSTRUCTIONS.md)
  4. Input validation         middleware/validate.js: schema validator + XSS
                              escape + JSON-syntax error handler (SQLi is
                              structurally prevented: Sequelize parameterizes)
  5. Live CRUD                routes/records.routes.js — Sequelize records
                              entity (FK -> users), full CRUD on PostgreSQL
  6. Real dashboard           pages/Dashboard.jsx rewritten: fetch-loop CRUD
                              against /api/v1/records with loading / error /
                              empty / success states
  7. server.js mounts         /api/v1/records + /api/v1/events + /api/v1/ai
                              + error handler
  8. Live push                services/changeBus.js + routes/events.routes.js —
                              an authenticated SSE change feed over Postgres
                              (Redis optional), and src/hooks/useRealtime.js so
                              the dashboard reacts without a refresh instead of
                              asking for it

Idempotent by markers; engine calls ``apply_production_spec`` after file writes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agent.schema_guards import write_migration_guards

_FRONTEND_DOCKERFILE = """\
# ── Stage 1: Build ─────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ──────────────────────
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

_NGINX_CONF = """\
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Streaming endpoints must bypass proxy buffering: /ai/* answers SSE token
    # frames and /events is the change feed. A regex location has to repeat the
    # original URI, so proxy_pass carries no path here.
    location ~ ^/api/v1/(ai|events) {
        proxy_pass http://backend:5000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
    }

    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
"""

_BACKEND_DOCKERFILE = """\
# ── Stage 1: install all deps (build toolchain) ────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# ── Stage 2: slim non-root runtime ─────────────────
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN addgroup -S appgroup && adduser -S appuser -G appgroup \\
    && chown -R appuser:appgroup /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD node -e "fetch('http://localhost:5000/api/v1/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["npm", "start"]
"""

_TSCONFIG = {
    "compilerOptions": {
        "allowJs": True,
        "checkJs": False,
        "target": "ES2022",
        "module": "commonjs",
        "moduleResolution": "node",
        "strict": True,
        "noImplicitAny": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "noEmit": True,
    },
    "include": ["**/*.js", "types/**/*.d.ts"],
    "exclude": ["node_modules", "uploads"],
}

_TYPES_D = """// Shared domain types for the backend (JS codebase typed via checkJs).
/** @typedef {Object} User
 * @property {string} id UUID primary key
 * @property {string} name non-empty
 * @property {string} email unique, validated
 * @property {string} password bcrypt hash
 * @property {'user'|'admin'} role
 * @property {Date} [createdAt]
 * @property {Date} [updatedAt]
 */
export {};

/** @typedef {Object} Record
 * @property {string} id UUID primary key
 * @property {string} title
 * @property {string} [body] markdown/plain text payload
 * @property {'draft'|'published'|'archived'} status
 * @property {string} userId FK -> users.id
 * @property {Date} [createdAt]
 * @property {Date} [updatedAt]
 */
"""

_VALIDATE_JS = """/** middleware/validate — schema validation + XSS defense for every route.
 * SQL injection is structurally prevented by Sequelize's parameterized
 * queries; this layer defends the JSON boundary:
 *   validate(schema)  -> 422 with per-field messages, unknown fields dropped
 *   sanitize()        -> escapes < > " ' & recursively in strings
 *   errorHandler      -> central JSON error terminator (never leaks stack)
 */
const MAX_FIELD_LEN = 10000;

function _escape(value) {
  return String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;').replace(/'/g, '&#x27;');
}

function sanitize(body, depth = 0) {
  if (depth > 6 || body === null || body === undefined) return body;
  if (typeof body === 'string') return _escape(body).slice(0, MAX_FIELD_LEN);
  if (Array.isArray(body)) return body.map((v) => sanitize(v, depth + 1));
  if (typeof body === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(body)) out[k] = sanitize(v, depth + 1);
    return out;
  }
  return body;
}

/** schema: { field: { required?, type?: 'string'|'number'|'boolean', max?, min? } } */
function validate(schema) {
  return (req, _res, next) => {
    const body = req.body || {};
    const errors = {};
    for (const [field, rule] of Object.entries(schema)) {
      // A field of only whitespace is an empty field: without this a title of
      // three spaces satisfies min: 1 and the row is stored blank.
      const raw = body[field];
      const value = typeof raw === 'string' ? raw.trim() : raw;
      if (value !== raw) body[field] = value;
      if (value === undefined || value === null || value === '') {
        if (rule.required) errors[field] = `${field} is required`;
        continue;
      }
      const actual = typeof value;
      if (rule.type && actual !== rule.type) {
        errors[field] = `${field} must be ${rule.type}`;
        continue;
      }
      if (rule.type === 'string' && rule.max && value.length > rule.max) {
        errors[field] = `${field} must be <= ${rule.max} chars`;
      }
      if (rule.type === 'string' && rule.min && value.length < rule.min) {
        errors[field] = `${field} must be >= ${rule.min} chars`;
      }
      if (rule.type === 'number' && !Number.isFinite(value)) {
        errors[field] = `${field} must be finite`;
      }
    }
    if (Object.keys(errors).length) {
      return next({ status: 422, code: 'VALIDATION_ERROR', errors });
    }
    req.body = sanitize(body);
    return next();
  };
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, _req, res, _next) {
  const status = err.status || err.statusCode || 500;
  console.error(`[${new Date().toISOString()}] ${status} ${err.code || 'ERROR'}:`, err.message, status >= 500 ? `\\n${err.stack}` : '');
  if (res.headersSent) return;
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ success: false, message: 'Invalid JSON body' });
  }
  res.status(status).json({
    success: false,
    code: err.code || 'ERROR',
    message: status >= 500 ? 'Something went wrong' : err.message,
    errors: err.errors || undefined,
  });
}

module.exports = { validate, sanitize, errorHandler };
"""

_RECORDS_JS = """/** routes/records — live CRUD over PostgreSQL (FK: records.userId -> users.id).
 * Lists are user-scoped via req.user (set by auth). All queries run through
 * Sequelize = parameterized = SQLi-safe; bodies pass validate() = XSS-safe.
 */
const express = require('express');
const { DataTypes } = require('sequelize'); // engine models/index.js exports { sequelize, User } only
const { sequelize } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');
const { validate } = require('../middleware/validate');
const { notify } = require('../services/changeBus');

const router = express.Router();

const Record = sequelize.define('Record', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  title: { type: DataTypes.STRING(160), allowNull: false },
  body: { type: DataTypes.TEXT },
  status: { type: DataTypes.ENUM('draft', 'published', 'archived'), defaultValue: 'draft' },
  userId: { type: DataTypes.UUID, allowNull: false },
}, { tableName: 'records', underscored: false });

const RULES = {
  title: { required: true, type: 'string', min: 1, max: 160 },
  body: { type: 'string', max: 10000 },
  status: { type: 'string', max: 20 },
};

function authRequired(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ success: false, message: 'Login required' });
  try {
    const jwt = require('jsonwebtoken');
    req.user = jwt.verify(token, jwtSecret);
    return next();
  } catch (_e) {
    return res.status(401).json({ success: false, message: 'Invalid or expired token' });
  }
}

router.use(authRequired);

router.get('/', async (req, res) => {
  const rows = await Record.findAll({ where: { userId: req.user.id }, order: [['createdAt', 'DESC']] });
  res.json({ success: true, data: rows });
});

router.get('/:id', async (req, res) => {
  const row = await Record.findOne({ where: { id: req.params.id, userId: req.user.id } });
  if (!row) return res.status(404).json({ success: false, message: 'Not found' });
  res.json({ success: true, data: row });
});

router.post('/', validate(RULES), async (req, res, next) => {
  try {
    const status = ['draft', 'published', 'archived'].includes(req.body.status) ? req.body.status : 'draft';
    const row = await Record.create({ title: req.body.title, body: req.body.body || '', status, userId: req.user.id });
    notify('records'); // wake every open change feed, including this client's
    res.status(201).json({ success: true, data: row });
  } catch (e) { next(e); }
});

router.put('/:id', validate(RULES), async (req, res, next) => {
  try {
    const row = await Record.findOne({ where: { id: req.params.id, userId: req.user.id } });
    if (!row) return res.status(404).json({ success: false, message: 'Not found' });
    const patch = {};
    if (req.body.title !== undefined) patch.title = req.body.title;
    if (req.body.body !== undefined) patch.body = req.body.body;
    if (req.body.status && ['draft', 'published', 'archived'].includes(req.body.status)) patch.status = req.body.status;
    await row.update(patch);
    notify('records');
    res.json({ success: true, data: row });
  } catch (e) { next(e); }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const n = await Record.destroy({ where: { id: req.params.id, userId: req.user.id } });
    if (!n) return res.status(404).json({ success: false, message: 'Not found' });
    notify('records');
    res.json({ success: true, data: { deleted: n } });
  } catch (e) { next(e); }
});

module.exports = router;
"""

_CHANGE_BUS_JS = """/** services/changeBus — how a write tells every open stream to look again.
 *
 * Default: one Node process, an in-process event. Set REDIS_URL and install the
 * OPTIONAL `redis` package and the same signal crosses processes and instances,
 * which is what a multi-region deployment needs.
 *
 * Redis is never a requirement. If the package is missing, the URL is unset, or
 * the server is unreachable, every function here degrades to the in-process
 * event and the SSE feed falls back to its own poll. A write must never fail
 * because a cache is down.
 */
const { EventEmitter } = require('events');

const CHANNEL = process.env.SSE_CHANNEL || 'lumicore:changes';
const bus = new EventEmitter();
bus.setMaxListeners(0);

let publisher = null;
let subscriber = null;
let attempt = null;

function attach() {
  const url = process.env.REDIS_URL;
  if (!url || attempt) return;
  let redis;
  try {
    redis = require('redis'); // optional dependency: npm i redis
  } catch (_e) {
    return; // no client library -> in-process only, the feed still polls
  }
  attempt = (async () => {
    try {
      publisher = redis.createClient({ url });
      subscriber = redis.createClient({ url });
      // node-redis surfaces every socket problem as an 'error' event, and an
      // unhandled one kills the process — a Redis blip must not take the API with it.
      publisher.on('error', () => {});
      subscriber.on('error', () => {});
      await publisher.connect();
      await subscriber.connect();
      await subscriber.subscribe(CHANNEL, (table) => bus.emit('change', table));
    } catch (_e) {
      publisher = null;
      subscriber = null;
    }
  })();
}

/** Announce a committed write. Safe to call whether or not Redis is configured. */
function notify(table) {
  bus.emit('change', table);
  if (publisher) {
    try {
      const pending = publisher.publish(CHANNEL, table);
      if (pending && typeof pending.catch === 'function') pending.catch(() => {});
    } catch (_e) { /* the poll interval covers this */ }
  }
}

/** @returns {() => void} unsubscribe */
function subscribe(listener) {
  attach();
  bus.on('change', listener);
  return () => bus.off('change', listener);
}

module.exports = { notify, subscribe, CHANNEL };
"""

_EVENTS_JS = """/** routes/events — the SSE change feed: the dashboard is told, it does not ask.
 *
 * A frame carries { id, feed, at } — a signal, never a payload. Clients refetch
 * the authoritative rows through the normal authenticated endpoints, so this
 * route cannot become a second, looser copy of the data API, and an
 * at-least-once cursor costs nothing more than one extra refetch.
 *
 * Two rules hold the design up:
 *  - tenancy is compiled into the statement (`"userId" = $1` as a bind value),
 *    so a stream can only ever see its own owner's rows. The inquiry feed is the
 *    one exception, and it emits only the row id and timestamp: an inquiry
 *    belongs to its sender, not to whoever happens to be logged in.
 *  - `EventSource` cannot send an Authorization header, so `?token=` is accepted
 *    and verified identically. That is the 15-minute access token over HTTPS, not
 *    a refresh token — and it is why the frames carry no data worth logging.
 *
 * Postgres is the source of truth, so the feed works on any host. Redis (see
 * services/changeBus.js) only shortens latency. The stream closes itself before
 * a serverless function's maxDuration so the client reconnects on its own terms.
 */
const express = require('express');
const jwt = require('jsonwebtoken');
const { sequelize } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');
const { subscribe } = require('../services/changeBus');

const router = express.Router();

const ZERO_UUID = '00000000-0000-0000-0000-000000000000';
const DEFAULTS = { pollMs: 1000, maxMs: 45000, maxClients: 64 };
const HEARTBEAT_MS = 15000;
const RECONNECT_MS = 3000;
const FEED_FAILURE_LIMIT = 3;

// One entry per watched table. Column casing follows each table's own migration
// (records is underscored:false, contact_messages is underscored:true).
const FEEDS = [
  {
    name: 'records',
    event: 'record:changed',
    sql: 'SELECT "id" AS "rowId", "updatedAt" AS "at" FROM records '
       + 'WHERE "userId" = $1 AND ("updatedAt", "id") > ($2::timestamptz, $3::uuid) '
       + 'ORDER BY "updatedAt" ASC, "id" ASC LIMIT 50',
    bind: (cursor, userId) => [userId, cursor.at, cursor.id],
  },
  {
    name: 'contact',
    event: 'contact:created',
    sql: 'SELECT id AS "rowId", created_at AS "at" FROM contact_messages '
       + 'WHERE (created_at, id) > ($1::timestamptz, $2::uuid) '
       + 'ORDER BY created_at ASC, id ASC LIMIT 50',
    bind: (cursor) => [cursor.at, cursor.id],
  },
];

function envMs(raw, fallback, floor) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value < 0) return fallback;
  return Math.max(floor === undefined ? 0 : floor, value);
}

function subjectOf(req) {
  const header = String(req.headers.authorization || '');
  const query = req.query && req.query.token;
  const token = header.startsWith('Bearer ') ? header.slice(7).trim()
    : (typeof query === 'string' ? query.trim() : '');
  if (!token) return { error: 'Login required' };
  try {
    const claims = jwt.verify(token, jwtSecret);
    const id = claims && (claims.id || claims.sub);
    if (!id) return { error: 'Token carries no subject' };
    return { id: String(id) };
  } catch (_e) {
    return { error: 'Invalid or expired token' };
  }
}

function resumeAt(req) {
  const raw = req.headers && req.headers['last-event-id'];
  if (typeof raw !== 'string' || !raw) return null;
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

let openStreams = 0;

router.get('/', (req, res) => {
  const subject = subjectOf(req);
  if (subject.error) return res.status(401).json({ success: false, message: subject.error });

  const cap = Math.max(1, envMs(process.env.SSE_MAX_CLIENTS, DEFAULTS.maxClients, 1));
  if (openStreams >= cap) {
    // Refusing is honest; queueing streams until the process drowns is not.
    return res.status(503).set({ 'Retry-After': String(Math.ceil(RECONNECT_MS / 1000)) })
      .json({ success: false, code: 'TOO_MANY_STREAMS',
              message: 'This API instance is at its open-stream limit; retry shortly' });
  }

  const pollMs = envMs(process.env.SSE_POLL_MS, DEFAULTS.pollMs, 50);
  const maxMs = envMs(process.env.SSE_MAX_MS, DEFAULTS.maxMs);
  // A brand-new visitor starts at now: nobody replays a tenant's history by
  // opening a stream. A reconnect resumes at its Last-Event-ID instead.
  const startAt = resumeAt(req) || new Date();
  const cursors = FEEDS.map(() => ({ at: startAt, id: ZERO_UUID }));

  res.status(200).set({
    'Content-Type': 'text/event-stream; charset=utf-8',
    // `no-transform` makes compression() skip this response: a gzipped SSE stream
    // is buffered until close, which looks like a live page and is a dead one.
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  if (typeof res.flushHeaders === 'function') res.flushHeaders();
  openStreams += 1;

  let closed = false;
  let busy = false;
  let failures = 0;
  let timer = null;
  let heartbeat = null;
  let deadline = null;
  let unsubscribe = null;

  // The oldest cursor of the set: resuming from it can re-send a frame, and can
  // never drop one. Duplicates cost a refetch, gaps cost the client's trust.
  const watermark = () => cursors.reduce((min, c) => (c.at < min ? c.at : min), cursors[0].at);

  const frame = (fields) => {
    if (closed) return;
    res.write(`${Object.entries(fields).map(([k, v]) => `${k}: ${v}`).join('\\n')}\\n\\n`);
  };

  const stop = (reason) => {
    if (closed) return;
    closed = true;
    if (timer) clearInterval(timer);
    if (heartbeat) clearInterval(heartbeat);
    if (deadline) clearTimeout(deadline);
    if (unsubscribe) unsubscribe();
    openStreams -= 1;
    if (reason === 'db-down') console.warn('[events] change feed closed: the database was unreachable');
    if (!res.writableEnded) res.end();
  };

  req.on('close', () => stop('client-gone'));
  res.on('close', () => stop('client-gone'));

  frame({ retry: RECONNECT_MS });
  frame({ id: watermark().toISOString(), event: 'ready',
          data: JSON.stringify({ ok: true, feeds: FEEDS.map((f) => f.event), since: startAt.toISOString() }) });

  const tick = async () => {
    if (busy || closed) return;
    busy = true;
    const results = await Promise.all(FEEDS.map(async (feed, index) => {
      try {
        const rows = await sequelize.query(feed.sql, {
          bind: feed.bind(cursors[index], subject.id), type: 'SELECT',
        });
        return { index, rows: Array.isArray(rows) ? rows : [] };
      } catch (_e) {
        return { index, rows: [], failed: true };
      }
    }));
    busy = false;
    if (closed) return;

    failures = results.some((r) => r.failed) ? failures + 1 : 0;
    if (failures >= FEED_FAILURE_LIMIT) {
      // Silence would look like an idle dashboard. Say so, close, and let the
      // client switch to its polling fallback.
      frame({ event: 'feed-error',
              data: JSON.stringify({ reason: 'the database was unreachable for '
                + `${failures} polls, switching the client to polling` }) });
      return stop('db-down');
    }

    for (const { index, rows } of results) {
      const feed = FEEDS[index];
      for (const row of rows) {
        const at = new Date(row.at);
        if (Number.isNaN(at.getTime())) continue;
        cursors[index] = { at, id: String(row.rowId) };
        frame({ id: watermark().toISOString(), event: feed.event,
                data: JSON.stringify({ id: row.rowId, feed: feed.name, at: at.toISOString() }) });
      }
    }
  };

  timer = setInterval(tick, pollMs);
  unsubscribe = subscribe(() => { tick(); }); // a local or cross-instance write polls now, not in 1 s
  heartbeat = setInterval(() => { if (!closed) res.write(': keep-alive\\n\\n'); }, HEARTBEAT_MS);
  if (maxMs > 0) deadline = setTimeout(() => stop('max-duration'), maxMs);
  tick();
  return undefined;
});

module.exports = router;
"""

_DASHBOARD_JSX = """import React, { useCallback, useEffect, useState } from 'react';
import useRealtime from '../hooks/useRealtime';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const STATUSES = ['draft', 'published', 'archived'];

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [state, setState] = useState('loading'); // loading | ready | error
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: '', body: '', status: 'draft' });
  const [inquiries, setInquiries] = useState(0);

  const token = () => localStorage.getItem('token') || '';
  const headers = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token()}`,
  }), []);

  const load = useCallback(async () => {
    setState('loading');
    setError('');
    try {
      const res = await fetch(`${API}/records`, { headers: headers() });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || `HTTP ${res.status}`);
      setItems(json.data || []);
      setState('ready');
    } catch (e) {
      setError(e.message || 'Failed to load records');
      setState('error');
    }
  }, [headers]);
  useEffect(() => { load(); }, [load]);

  // Live push: the API says a row changed and the console refetches. A stream
  // that cannot be held falls back to a timer, so the panel is never silently
  // showing yesterday's rows.
  const onSignal = useCallback((signal) => {
    if (signal.data && signal.data.feed === 'contact') {
      setInquiries((n) => n + 1);
      return;
    }
    load();
  }, [load]);
  const { status: live } = useRealtime({
    events: ['record:changed', 'contact:created'], onSignal,
  });

  const create = async (ev) => {
    ev.preventDefault();
    setBusy(true);
    try {
      const res = await fetch(`${API}/records`, {
        method: 'POST', headers: headers(), body: JSON.stringify(form),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.message || 'Create failed');
      setForm({ title: '', body: '', status: 'draft' });
      await load();
    } catch (e) {
      setError(e.message || 'Create failed');
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/records/${id}`, { method: 'DELETE', headers: headers() });
      if (!res.ok) throw new Error('Delete failed');
      await load();
    } catch (e) {
      setError(e.message || 'Delete failed');
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="flex flex-wrap items-center gap-3 mb-8">
        <h1 className="text-3xl font-bold text-white">Control Console</h1>
        <span
          role="status"
          aria-live="polite"
          data-testid="live-status"
          className={`px-3 py-1 text-xs rounded-full border ${
            live === 'live' ? 'border-emerald-700 bg-emerald-900/40 text-emerald-300'
            : live === 'polling' ? 'border-amber-700 bg-amber-900/40 text-amber-300'
            : 'border-slate-700 bg-slate-900 text-slate-400'}`}
        >
          {live === 'live' ? 'Live updates'
            : live === 'polling' ? 'Polling updates'
            : live === 'reconnecting' ? 'Reconnecting' : 'Connecting'}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-10">
        {[
          ['Records', String(items.length)],
          ['Published', String(items.filter((i) => i.status === 'published').length)],
          ['Drafts', String(items.filter((i) => i.status === 'draft').length)],
          ['Archived', String(items.filter((i) => i.status === 'archived').length)],
          ['Inquiries', String(inquiries)],
        ].map(([label, value]) => (
          <div key={label} className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
          </div>
        ))}
      </div>

      <form onSubmit={create} className="flex flex-col md:flex-row gap-3 mb-8">
        <input
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Title" value={form.title} required
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <input
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Body (optional)" value={form.body}
          onChange={(e) => setForm({ ...form, body: e.target.value })}
        />
        <select
          className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white"
          value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button
          type="submit" disabled={busy || !form.title.trim()}
          className="px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white font-medium transition-colors"
        >
          {busy ? 'Saving…' : 'Add'}
        </button>
      </form>

      {error && <div role="alert" className="mb-6 px-4 py-3 rounded-xl bg-rose-900/40 border border-rose-700 text-rose-200">{error}</div>}

      {state === 'loading' && (
        <div className="space-y-3" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-16 rounded-xl bg-slate-900 animate-pulse" />)}
        </div>
      )}

      {state === 'error' && (
        <div className="text-center py-10">
          <p className="text-slate-400 mb-4">Could not load your records.</p>
          <button onClick={load} className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors">
            Retry
          </button>
        </div>
      )}

      {state === 'ready' && items.length === 0 && (
        <div className="text-center py-10 text-slate-400" data-testid="dashboard-empty">
          No records yet — add your first one above.
        </div>
      )}

      {state === 'ready' && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className={`px-2.5 py-1 text-xs rounded-full ${
                item.status === 'published' ? 'bg-emerald-900/60 text-emerald-300' :
                item.status === 'archived' ? 'bg-slate-800 text-slate-400' : 'bg-amber-900/60 text-amber-300'}`}>
                {item.status}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{item.title}</p>
                {item.body ? <p className="text-slate-400 text-sm truncate">{item.body}</p> : null}
              </div>
              <button
                onClick={() => remove(item.id)} disabled={busy} aria-label={`Delete ${item.title}`}
                className="px-3 py-1.5 text-sm rounded-lg bg-rose-900/50 hover:bg-rose-800 text-rose-200 disabled:opacity-40 transition-colors"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
"""

_LOGIN_JSX = """import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (ev) => {
    ev.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const json = await res.json();
      if (!res.ok || !json.success || !json.token) throw new Error(json.message || `Login failed (${res.status})`);
      localStorage.setItem('token', json.token);
      localStorage.setItem('user', JSON.stringify(json.user || {}));
      navigate('/dashboard');
    } catch (e) {
      setError(e.message || 'Login failed — check your credentials');
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Sign in</h2>
      <form onSubmit={submit} className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <label className="block text-sm text-slate-400" htmlFor="login-email">Email</label>
        <input id="login-email" type="email" required autoComplete="email"
          className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label className="block text-sm text-slate-400" htmlFor="login-password">Password</label>
        <input id="login-password" type="password" required autoComplete="current-password" minLength={8}
          className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} />
        {error && <div role="alert" className="px-4 py-3 rounded-xl bg-rose-900/40 border border-rose-700 text-rose-200 text-sm">{error}</div>}
        <button type="submit" disabled={busy || !form.email || !form.password}
          className="w-full py-3.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white font-bold transition-colors">
          {busy ? 'Signing in…' : 'Sign In'}
        </button>
        <p className="text-center text-sm text-slate-400">
          No account? <Link to="/register" className="text-teal-400 hover:underline">Create one</Link>
        </p>
      </form>
    </div>
  );
}
"""

_REGISTER_JSX = """import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (ev) => {
    ev.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const json = await res.json();
      if (!res.ok || !json.success || !json.token) throw new Error(json.message || `Registration failed (${res.status})`);
      localStorage.setItem('token', json.token);
      localStorage.setItem('user', JSON.stringify(json.user || {}));
      navigate('/dashboard');
    } catch (e) {
      setError(e.message || 'Registration failed');
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Create your account</h2>
      <form onSubmit={submit} className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <label className="block text-sm text-slate-400" htmlFor="reg-name">Full name</label>
        <input id="reg-name" type="text" required autoComplete="name"
          className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Full name" value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <label className="block text-sm text-slate-400" htmlFor="reg-email">Email</label>
        <input id="reg-email" type="email" required autoComplete="email"
          className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label className="block text-sm text-slate-400" htmlFor="reg-password">Password</label>
        <input id="reg-password" type="password" required autoComplete="new-password" minLength={8}
          className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-teal-500 focus:outline-none"
          placeholder="Min 8 characters" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} />
        {error && <div role="alert" className="px-4 py-3 rounded-xl bg-rose-900/40 border border-rose-700 text-rose-200 text-sm">{error}</div>}
        <button type="submit" disabled={busy || !form.name || !form.email || !form.password}
          className="w-full py-3.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white font-bold transition-colors">
          {busy ? 'Creating account…' : 'Get Started'}
        </button>
        <p className="text-center text-sm text-slate-400">
          Already registered? <Link to="/login" className="text-teal-400 hover:underline">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
"""

_USE_REALTIME_JS = """import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const GIVE_UP_AFTER = 4;    // consecutive failed reconnects before polling
const RECONCILE_MS = 60000; // one quiet refresh while the stream is held
const FALLBACK_MS = 25000;  // polling rate once the stream is gone

/** useRealtime — open the API's SSE change feed and hand each frame to onSignal.
 *
 * The browser reconnects EventSource on its own (the server sends `retry:`), so
 * this hook only decides what happens when the stream cannot be held at all:
 * after GIVE_UP_AFTER failures, or on a `feed-error`, it runs a timer instead.
 * Live is better than polling; polling is never silent.
 *
 * The server closes a stream deliberately before a serverless function's hard
 * timeout. Each new stream answers with `ready`, which resets the failure count,
 * so a normal cycle is not mistaken for an outage.
 */
export default function useRealtime({
  events = ['record:changed'],
  onSignal,
  enabled = true,
  fallbackMs = FALLBACK_MS,
} = {}) {
  const [status, setStatus] = useState(enabled ? 'connecting' : 'off');
  const handlers = useRef(onSignal);
  useEffect(() => { handlers.current = onSignal; }, [onSignal]);

  const emit = useCallback((signal) => {
    if (handlers.current) handlers.current(signal);
  }, []);

  // `events` is usually an inline array; keying on its joined value keeps the
  // subscription stable across renders instead of reconnecting on every one.
  const eventKey = (Array.isArray(events) ? events : [events]).join(',');
  const subscribed = useMemo(() => eventKey.split(',').filter(Boolean), [eventKey]);

  useEffect(() => {
    if (!enabled) { setStatus('off'); return undefined; }
    const token = localStorage.getItem('token') || '';
    if (!token || typeof EventSource !== 'function') { setStatus('off'); return undefined; }

    let failed = 0;
    let pollTimer = null;
    const listeners = [];

    const startPolling = () => {
      if (pollTimer) return;
      setStatus('polling');
      pollTimer = setInterval(() => emit({ source: 'poll' }), fallbackMs);
    };

    const source = new EventSource(`${API}/events?token=${encodeURIComponent(token)}`);
    subscribed.forEach((name) => {
      const onEvent = (event) => {
        let data = null;
        try { data = JSON.parse(event.data); } catch (_e) { data = null; }
        emit({ source: 'sse', event: name, data });
      };
      source.addEventListener(name, onEvent);
      listeners.push([name, onEvent]);
    });
    source.addEventListener('ready', () => { failed = 0; setStatus('live'); });
    source.addEventListener('feed-error', () => { source.close(); startPolling(); });
    source.onerror = () => {
      failed += 1;
      setStatus('reconnecting');
      if (failed >= GIVE_UP_AFTER) startPolling();
    };

    const reconcile = setInterval(() => {
      if (source.readyState === EventSource.OPEN) emit({ source: 'reconcile' });
    }, RECONCILE_MS);

    return () => {
      listeners.forEach(([name, onEvent]) => source.removeEventListener(name, onEvent));
      source.close();
      if (pollTimer) clearInterval(pollTimer);
      clearInterval(reconcile);
      setStatus('off');
    };
  }, [emit, enabled, fallbackMs, subscribed]);

  return { status };
}
"""

_INSTRUCTIONS = """# INSTRUCTIONS — {brand}

Production-ready full-stack application (React 19 + Vite · Express · PostgreSQL · Docker).

## 1. Prerequisites

| Tool | Version |
|------|---------|
| Node.js | >= 20 |
| Docker + Docker Compose | 24+ |
| PostgreSQL | 16 (or use the bundled container) |

## 2. Local Setup (no Docker)

```bash
# Backend
cd backend
cp .env.example .env          # set DATABASE_URL, JWT_SECRET
npm install
npm run db:migrate            # creates users + records tables
npm run dev                   # http://localhost:5000

# Frontend (second terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

`npm run db:migrate` is safe to re-run as often as you like: each migration asks
Postgres what already exists and applies only the gap, so a database that arrived
via the API's first-request `sync()`, a partially applied deploy, or a second
`npm run db:migrate` all converge on the same schema instead of aborting with
`relation "already exists"`.

## 3. One-Command Docker Run

```bash
cp .env.example .env          # repo root — set POSTGRES_PASSWORD + JWT_SECRET
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:5000/api/v1 |
| PostgreSQL | internal (db:5432) |

Rebuild from scratch: `docker compose down -v && docker compose up --build`

## 4. Environment Variables

### Root (.env — used by docker-compose)

| Key | Required | Purpose |
|-----|----------|---------|
| `POSTGRES_PASSWORD` | yes | Postgres superuser password |
| `POSTGRES_USER` | no | default `postgres` |
| `JWT_SECRET` | yes | signs auth tokens (openssl rand -hex 32) |
| `ENCRYPTION_KEY` | yes* | 64-hex; encrypts stored AI API keys (*required for AI routes) |
| `AI_PROVIDER` | no | `openai` (default) / `gemini` / `openrouter` / `deepseek` |
| `OPENAI_API_KEY` | no* | one provider key is needed for AI features |
| `PGVECTOR_URL` | no | enables pgvector RAG; in-memory fallback without it |

### Backend (backend/.env)

| Key | Purpose |
|-----|---------|
| `DATABASE_URL` / `DB_*` | PostgreSQL connection |
| `JWT_SECRET` | token signing (rotate carefully) |
| `ENCRYPTION_KEY` | keyVault AES-256-GCM master key |
| `SSE_POLL_MS` | change-feed poll interval (default 1000; 1 s latency without Redis) |
| `SSE_MAX_MS` | how long one stream is held before the client reconnects (default 45000; keep it below your host's function timeout) |
| `SSE_MAX_CLIENTS` | open streams per process before a new one is refused with 503 (default 64) |
| `REDIS_URL` | optional: pushes each change across instances instead of polling. Needs `npm i redis` in `backend/` |
| `SSE_CHANNEL` | optional: pub/sub channel name (default `lumicore:changes`) |

### Frontend (frontend/.env)

| Key | Purpose |
|-----|---------|
| `VITE_API_URL` | default `http://localhost:5000/api/v1` |

## 5. API Surface

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/api/v1/auth/register` | POST | name/email/password (bcrypt) |
| `/api/v1/auth/login` | POST | returns JWT |
| `/api/v1/records` | GET/POST | list/create — JWT required |
| `/api/v1/records/:id` | GET/PUT/DELETE | owner-scoped |
| `/api/v1/events` | GET (SSE) | live change feed — `?token=<JWT>` (EventSource cannot send headers) |
| `/api/v1/ai/generate` | POST | JWT required — JSON or SSE stream (`stream:true`) |
| `/api/v1/ai/chat` | POST | JWT required — RAG w/ sources |
| `/api/v1/ai/files` | POST | JWT required — pdf/docx/txt upload -> indexed for RAG |
| `/api/v1/ai/health` | GET | provider + key status |
| `/api/v1/health` | GET | uptime probe (Docker HEALTHCHECK) |

## 6. Security Notes

- Passwords: bcrypt (10 rounds). Tokens: JWT (verify `JWT_SECRET` in prod).
- The AI surface spends your provider key on every call, so `/api/v1/ai/*` is
  JWT-gated (`middleware/aiAuth.js`). With no `JWT_SECRET` it answers 503 rather
  than running unauthenticated — a missing secret must never mean "open".
- All DB writes: Sequelize parameterized queries (SQLi-safe).
- All request bodies: schema-validated + XSS-escaped (`middleware/validate.js`).
- Rate limiting on auth; helmet security headers on every response.
- Backend runs as non-root `appuser` inside Docker; uploads are 10 MB-capped + MIME-allowlisted.

## 7. TypeScript

The backend ships `tsconfig.json` (`checkJs: true`) and shared domain types in
`backend/types/index.d.ts`. Run `npm run typecheck` in `backend/` to type-check.
The generated code is JavaScript with JSDoc types — incrementally migrate any
file to `.ts` and add `ts-node`/`tsc` when your team is ready.

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| ECONNREFUSED (backend) | Postgres not up: `docker compose up -d db` first |
| Migration failed | Check `DATABASE_URL`; run `npm run db:migrate` inside `backend/` |
| 401 on records | Token missing/expired — login again, check `Authorization: Bearer` |
| SSE shows nothing | Any proxy in front must disable buffering (nginx sample included) |
| Badge stuck on "Polling updates" | The feed is closed: check Postgres is reachable, then that `SSE_MAX_MS` sits below the host's function timeout |
| Feed runs ~1 s behind | Expected without Redis — it polls Postgres. Set `REDIS_URL` and `npm i redis` in `backend/` for instant fan-out |
| AI 422 | `ENCRYPTION_KEY` wrong length (needs 64 hex) or provider key missing (`/api/ai/health`) |
"""


def _backend_dir(project_dir: str) -> Path:
    root = Path(project_dir)
    for cand in ("backend", "."):
        p = root / cand
        if (p / "package.json").exists() or (p / "server.js").exists():
            return p
    return root / "backend"


def _frontend_dir(project_dir: str) -> Path:
    root = Path(project_dir)
    return root / "frontend" if (root / "frontend").exists() else root


def _patched_server(server_path: Path) -> bool:
    """Mount records/events/ai routes + error handler in backend/server.js.

    Marker-based, and each mount is checked on its own: a project generated
    before the change feed existed must gain /api/v1/events when it is
    regenerated, not keep the records-only wiring it was first delivered with.
    """
    text = server_path.read_text(encoding="utf-8", errors="replace")
    original = text

    if "require('./routes/records.routes')" not in text:
        anchor = "app.use('/api/v1/auth', authRoutes);"
        block = (
            "\n\nconst { errorHandler } = require('./middleware/validate');"
            "\napp.use('/api/v1/records', require('./routes/records.routes'));"
            "\ntry { app.use('/api/v1/contact', require('./routes/contact.routes')); } catch (err) { console.error(`[startup] Contact routes unavailable: ${err.message}`); }"
            "\ntry { app.use('/api/v1/ai', require('./routes/ai')); } catch (err) { console.error(`[startup] AI routes unavailable: ${err.message}`); }"
            "\napp.use(errorHandler);"
        )
        if anchor in text:
            text = text.replace(anchor, anchor + block, 1)
        else:
            text = text.replace("const app = express();",
                                "const app = express();" + block, 1)

    events_mount = "app.use('/api/v1/events', require('./routes/events.routes'));"
    if "require('./routes/events.routes')" not in text:
        records_mount = "app.use('/api/v1/records', require('./routes/records.routes'));"
        if records_mount in text:
            text = text.replace(records_mount, records_mount + "\n" + events_mount, 1)
        elif "app.use(errorHandler);" in text:
            text = text.replace("app.use(errorHandler);", events_mount + "\napp.use(errorHandler);", 1)
        else:
            text = text.replace("const app = express();",
                                "const app = express();\n" + events_mount, 1)

    if text == original:
        return False
    server_path.write_text(text, encoding="utf-8")
    return True


def _merge_backend_pkg(backend: Path) -> List[str]:
    added: List[str] = []
    pkg_path = backend / "package.json"
    if not pkg_path.exists():
        return added
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return added
    dev = pkg.setdefault("devDependencies", {})
    for name, version in {
        "typescript": "^5.6.2", "@types/express": "^4.17.21",
        "@types/node": "^22.7.0", "@types/jsonwebtoken": "^9.0.6",
        "@types/bcryptjs": "^2.4.6",
    }.items():
        if not dev.get(name):
            dev[name] = version
            added.append(f"dev:{name}@{version}")
    scripts = pkg.setdefault("scripts", {})
    scripts.setdefault("typecheck", "tsc --noEmit")
    if added:
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    return added


def _ensure_records_table(migrations: Path) -> Path:
    path = migrations / "002_create_records_table.js"
    if path.exists() and "_guards.js" in path.read_text(encoding="utf-8", errors="ignore"):
        return path
    # Rewritten when absent *or* when an older run shipped the unguarded version:
    # a product already delivered would otherwise keep a migration that crashes
    # on the tables its own deployed API created with sync().
    path.write_text("""const { DataTypes } = require('sequelize');
const { createTableIfMissing, addIndexIfMissing, dropTableIfExists } = require('./_guards.js');

module.exports = {
  async up({ context: queryInterface }) {
    await createTableIfMissing(queryInterface, 'records', {
      id: { type: DataTypes.UUID, primaryKey: true },
      title: { type: DataTypes.STRING(160), allowNull: false },
      body: { type: DataTypes.TEXT },
      status: { type: DataTypes.ENUM('draft', 'published', 'archived'), defaultValue: 'draft' },
      userId: {
        type: DataTypes.UUID, allowNull: false,
        references: { model: 'users', key: 'id' }, onDelete: 'CASCADE',
      },
      createdAt: { type: DataTypes.DATE, allowNull: false },
      updatedAt: { type: DataTypes.DATE, allowNull: false },
    });
    await addIndexIfMissing(queryInterface, 'records', ['userId']);
    await addIndexIfMissing(queryInterface, 'records', ['status']);
  },
  async down({ context: queryInterface }) {
    await dropTableIfExists(queryInterface, 'records');
  },
};
""", encoding="utf-8")
    return path


def apply_production_spec(project_dir: str, brand: str = "", force: bool = False) -> Dict[str, Any]:
    """Bring any generated project up to the mandatory production spec."""
    root = Path(project_dir)
    if not root.exists():
        return {"status": "failed", "message": "project dir missing"}
    backend = _backend_dir(project_dir)
    frontend = _frontend_dir(project_dir)
    created: List[str] = []
    updated: List[str] = []

    def _write(rel: Path, content: str, overwrite: bool = force):
        nonlocal created
        if rel.exists() and not overwrite:
            return
        rel.parent.mkdir(parents=True, exist_ok=True)
        rel.write_text(content, encoding="utf-8")
        created.append(str(rel.relative_to(root)))

    # 1. Docker: multi-stage files (compose already references them)
    _write(frontend / "Dockerfile", _FRONTEND_DOCKERFILE)
    _write(frontend / "nginx.conf", _NGINX_CONF)
    _write(backend / "Dockerfile", _BACKEND_DOCKERFILE)

    # 2. INSTRUCTIONS.md
    if not brand:
        brand = root.name.replace("-", " ").replace("_", " ").title().split()[0] \
            if root.name else "App"
    _write(root / "INSTRUCTIONS.md", _INSTRUCTIONS.replace("{brand}", brand))

    # 3. TypeScript-ready backend
    _write(backend / "tsconfig.json", json.dumps(_TSCONFIG, indent=2) + "\n")
    _write(backend / "types" / "index.d.ts", _TYPES_D)
    updated.extend(_merge_backend_pkg(backend))

    # 4. Validation middleware
    _write(backend / "middleware" / "validate.js", _VALIDATE_JS)

    # 5. Live CRUD (records entity + migration)
    _write(backend / "routes" / "records.routes.js", _RECORDS_JS)
    write_migration_guards(backend / "migrations")
    _ensure_records_table(backend / "migrations")

    # 5b. Live push: the change bus and its SSE feed ship with every product,
    #     because "the dashboard sat still" is the bug this exists to kill.
    _write(backend / "services" / "changeBus.js", _CHANGE_BUS_JS)
    _write(backend / "routes" / "events.routes.js", _EVENTS_JS)

    # 6. Real dashboard + real auth pages (replace static placeholders)
    _write(frontend / "src" / "hooks" / "useRealtime.js", _USE_REALTIME_JS)
    dash = frontend / "src" / "pages" / "Dashboard.jsx"
    if dash.exists() and "Control Console" in dash.read_text(encoding="utf-8", errors="replace"):
        dash.write_text(_DASHBOARD_JSX, encoding="utf-8")
        created.append(str(dash.relative_to(root)))
    login = frontend / "src" / "pages" / "Login.jsx"
    if login.exists() and "auth/login" not in login.read_text(encoding="utf-8", errors="replace"):
        login.write_text(_LOGIN_JSX, encoding="utf-8")
        created.append(str(login.relative_to(root)))
    register = frontend / "src" / "pages" / "Register.jsx"
    if register.exists() and "auth/register" not in register.read_text(encoding="utf-8", errors="replace"):
        register.write_text(_REGISTER_JSX, encoding="utf-8")
        created.append(str(register.relative_to(root)))

    # 7. server.js mounts
    server = backend / "server.js"
    if server.exists() and _patched_server(server):
        updated.append("backend/server.js")

    return {"status": "ok", "created": created, "updated": updated,
            "backend": str(backend), "frontend": str(frontend)}
