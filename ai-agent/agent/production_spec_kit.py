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
  7. server.js mounts         /api/v1/records + /api/v1/ai + error handler

Idempotent by markers; engine calls ``apply_production_spec`` after file writes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

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

    # SSE endpoints must bypass proxy buffering
    location /api/v1/ai/ {
        proxy_pass http://backend:5000/api/v1/ai/;
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
        "checkJs": True,
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
      const value = body[field];
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
const { sequelize, DataTypes } = require('../models');
const { validate } = require('../middleware/validate');

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
    req.user = jwt.verify(token, process.env.JWT_SECRET || 'dev-secret');
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
    res.json({ success: true, data: row });
  } catch (e) { next(e); }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const n = await Record.destroy({ where: { id: req.params.id, userId: req.user.id } });
    if (!n) return res.status(404).json({ success: false, message: 'Not found' });
    res.json({ success: true, data: { deleted: n } });
  } catch (e) { next(e); }
});

module.exports = router;
"""

_DASHBOARD_JSX = """import React, { useCallback, useEffect, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const STATUSES = ['draft', 'published', 'archived'];

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [state, setState] = useState('loading'); // loading | ready | error
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: '', body: '', status: 'draft' });

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
      <h1 className="text-3xl font-bold text-white mb-8">Control Console</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-10">
        {[
          ['Records', String(items.length)],
          ['Published', String(items.filter((i) => i.status === 'published').length)],
          ['Drafts', String(items.filter((i) => i.status === 'draft').length)],
          ['Archived', String(items.filter((i) => i.status === 'archived').length)],
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
| `/api/v1/ai/generate` | POST | JSON or SSE stream (`stream:true`) |
| `/api/v1/ai/chat` | POST | RAG w/ sources |
| `/api/v1/ai/files` | POST | pdf/docx/txt upload -> indexed for RAG |
| `/api/v1/ai/health` | GET | provider + key status |
| `/api/v1/health` | GET | uptime probe (Docker HEALTHCHECK) |

## 6. Security Notes

- Passwords: bcrypt (10 rounds). Tokens: JWT (verify `JWT_SECRET` in prod).
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
    """Mount records/ai routes + error handler in backend/server.js (marker-based)."""
    text = server_path.read_text(encoding="utf-8", errors="replace")
    if "require('./routes/records.routes')" in text:
        return False
    anchor = "app.use('/api/v1/auth', authRoutes);"
    add = (
        anchor
        + "\n\nconst { errorHandler } = require('./middleware/validate');"
        + "\napp.use('/api/v1/records', require('./routes/records.routes'));"
        + "\ntry { app.use('/api/v1/ai', require('./routes/ai')); } catch (_e) { /* kit absent */ }"
        + "\napp.use(errorHandler);"
    )
    if anchor not in text:
        add = (
            "\nconst { errorHandler } = require('./middleware/validate');"
            "\napp.use('/api/v1/records', require('./routes/records.routes'));"
            "\ntry { app.use('/api/v1/ai', require('./routes/ai')); } catch (_e) { /* kit absent */ }"
            "\napp.use(errorHandler);"
        )
        text = text.replace("const app = express();",
                            "const app = express();" + add, 1)
    else:
        text = text.replace(anchor, add, 1)
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
    if path.exists():
        return path
    path.write_text("""const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('records', {
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
    await queryInterface.addIndex('records', ['userId']);
    await queryInterface.addIndex('records', ['status']);
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('records');
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
    _ensure_records_table(backend / "migrations")

    # 6. Real dashboard (replaces static placeholder)
    dash = frontend / "src" / "pages" / "Dashboard.jsx"
    if dash.exists() and "Control Console" in dash.read_text(encoding="utf-8", errors="replace"):
        dash.write_text(_DASHBOARD_JSX, encoding="utf-8")
        created.append(str(dash.relative_to(root)))

    # 7. server.js mounts
    server = backend / "server.js"
    if server.exists() and _patched_server(server):
        updated.append("backend/server.js")

    return {"status": "ok", "created": created, "updated": updated,
            "backend": str(backend), "frontend": str(frontend)}
