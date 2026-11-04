"""Pure emitter for the authenticated `web_app` surface.

The app shell is deliberately separate from the marketing website emitter: it
has five authenticated routes, a token guard and no public navigation. Every
value shown comes from the generated API or the local session; the emitter adds
no metrics, roles, prices or testimonials. Tested in `tests/test_app_layouts.py`.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from agent.design_forge import hsl_to_hex


def app_route_expectations(brand: str) -> Dict[str, Dict[str, str]]:
    """Independent visible headings for the app-shell browser QA manifest.

    Headings are fixed product copy, not brand interpolations, so a broken route
    cannot be certified by the brand name appearing in the page chrome.
    """
    return {
        "/login": {"heading": "Sign in"},
        "/register": {"heading": "Create your account"},
        "/dashboard": {"heading": "Your workspace"},
        "/records": {"heading": "All records"},
        "/settings": {"heading": "Account settings"},
    }


def _js(value: str) -> str:
    """JSON is data, never JSX; escape HTML delimiters and JS line separators."""
    return (json.dumps(str(value), ensure_ascii=True).replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _bind(template: str, **values: str) -> str:
    return re.sub(r"@@([A-Z_]+)@@", lambda match: values[match[1]], template)


_APP_JSX = r"""import React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import AppShell from './components/AppShell.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Records from './pages/Records.jsx';
import Settings from './pages/Settings.jsx';

export function AuthGuard({ children }) {
  const location = useLocation();
  if (!localStorage.getItem('token')) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

function Start() {
  return localStorage.getItem('token')
    ? <Navigate to="/dashboard" replace />
    : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<AuthGuard><AppShell /></AuthGuard>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/records" element={<Records />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="/" element={<Start />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
"""

_APP_SHELL = r"""import React from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { currentUser, signOut } from '../auth.js';

const BRAND = @@BRAND@@;
const LINKS = [
  ['Dashboard', '/dashboard'],
  ['Records', '/records'],
  ['Settings', '/settings'],
];

export default function AppShell() {
  const navigate = useNavigate();
  const user = currentUser();
  const label = typeof user.name === 'string' && user.name
    ? user.name
    : typeof user.email === 'string' && user.email
      ? user.email
      : 'Signed-in account';

  const leave = () => {
    signOut();
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-shell">
      <a className="app-skip" href="#app-main">Skip to content</a>
      <header className="app-header">
        <div className="app-header-inner">
          <Link className="app-brand" to="/dashboard">{BRAND}</Link>
          <nav className="app-nav" aria-label="Workspace">
            {LINKS.map(([name, path]) => (
              <NavLink key={path} to={path}>{name}</NavLink>
            ))}
          </nav>
          <div className="app-session">
            <span className="app-session-name">{label}</span>
            <button type="button" className="app-button app-button-quiet" onClick={leave}>
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main id="app-main" className="app-main" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  );
}
"""

_AUTH_JS = r"""const API = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1')
  .replace(/\/$/, '');

export { API };

export function getToken() {
  return localStorage.getItem('token') || '';
}

export function currentUser() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    return user && typeof user === 'object' && !Array.isArray(user) ? user : {};
  } catch (error) {
    return {};
  }
}

export function currentUserId() {
  const user = currentUser();
  const direct = user.id || user.userId || user.sub;
  if (direct !== undefined && direct !== null && String(direct)) {
    return String(direct);
  }
  // The API token is a JWT whose payload carries the account id. Reading the
  // unverified subject is only for scoping local queue rows; the server still
  // verifies the signature on every request.
  const token = getToken();
  const parts = token.split('.');
  if (parts.length !== 3) return '';
  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded));
    const subject = payload && (payload.id || payload.sub || payload.user_id);
    return subject === undefined || subject === null ? '' : String(subject);
  } catch (error) {
    return '';
  }
}

export function storeSession(payload) {
  if (!payload || typeof payload.token !== 'string' || !payload.token) {
    throw new Error('The server did not return a session.');
  }
  localStorage.setItem('token', payload.token);
  localStorage.setItem('user', JSON.stringify(payload.user || {}));
}

export function signOut() {
  const previousUserId = currentUserId();
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  // The app shell listens for this to discard the signed-out user's offline
  // queue before another account can reuse this browser.
  window.dispatchEvent(new CustomEvent('lumicore:signout', {
    detail: { userId: previousUserId },
  }));
}

export class ApiError extends Error {
  constructor(message, status, fieldErrors) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors || {};
  }
}

function messageFor(payload, status) {
  if (status === 401) return 'Your session is not valid. Sign in again.';
  if (payload && typeof payload.message === 'string' && payload.message.trim()) {
    return payload.message.trim();
  }
  return `Request failed (${status}).`;
}

export async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const body = options.body;
  // fetch() stringifies plain objects as "[object Object]"; serialize JSON
  // bodies ourselves. FormData and string bodies keep their native encoding.
  const jsonBody = body && typeof body === 'object' && !(body instanceof FormData);
  if (jsonBody) {
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(`${API}${path}`, {
    ...options,
    body: jsonBody ? JSON.stringify(body) : body,
    headers,
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }
  if (!response.ok || !payload || payload.success !== true) {
    if (response.status === 401) signOut();
    throw new ApiError(
      messageFor(payload, response.status),
      response.status,
      (payload && payload.errors) || {},
    );
  }
  return payload;
}
"""

_LOGIN = r"""import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, request, storeSession } from '../auth.js';

const BRAND = @@BRAND@@;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const payload = { email: form.email.trim(), password: form.password };
    if (!EMAIL_RE.test(payload.email) || !payload.password) {
      setError('Enter a valid email address and your password.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const json = await request('/auth/login', { method: 'POST', body: payload });
      storeSession(json);
      navigate('/dashboard', { replace: true });
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status === 401
        ? 'Email or password is incorrect.'
        : 'We could not sign you in. Check the details and try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app-auth">
      <main className="app-auth-card">
        <p className="app-eyebrow">{BRAND}</p>
        <h1>Sign in</h1>
        <p className="app-lede">Use the account registered for this workspace.</p>
        <form onSubmit={submit} noValidate aria-busy={busy}>
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email" name="email" type="email" autoComplete="email" required
            value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}
            aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined}
          />
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password" name="password" type="password" autoComplete="current-password"
            required value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined}
          />
          {error && <p className="app-error" id="login-error" role="alert">{error}</p>}
          <button type="submit" className="app-button" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="app-switch">
          No account? <Link to="/register">Create your account</Link>
        </p>
      </main>
    </div>
  );
}
"""

_REGISTER = r"""import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, request, storeSession } from '../auth.js';

const BRAND = @@BRAND@@;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    const payload = {
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
    };
    if (!payload.name) {
      setError('Enter your name.');
      return;
    }
    if (!EMAIL_RE.test(payload.email)) {
      setError('Enter a valid email address.');
      return;
    }
    if (payload.password.length < 8) {
      setError('Use at least 8 characters for your password.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const json = await request('/auth/register', { method: 'POST', body: payload });
      storeSession(json);
      navigate('/dashboard', { replace: true });
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status === 409
        ? 'An account with this email already exists. Sign in instead.'
        : 'We could not create your account. Check the details and try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app-auth">
      <main className="app-auth-card">
        <p className="app-eyebrow">{BRAND}</p>
        <h1>Create your account</h1>
        <p className="app-lede">Registration creates a workspace account for this app.</p>
        <form onSubmit={submit} noValidate aria-busy={busy}>
          <label htmlFor="register-name">Full name</label>
          <input
            id="register-name" name="name" type="text" autoComplete="name" required
            value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
          <label htmlFor="register-email">Email</label>
          <input
            id="register-email" name="email" type="email" autoComplete="email" required
            value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}
            aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined}
          />
          <label htmlFor="register-password">Password</label>
          <input
            id="register-password" name="password" type="password" autoComplete="new-password"
            required value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined}
          />
          {error && <p className="app-error" id="register-error" role="alert">{error}</p>}
          <button type="submit" className="app-button" disabled={busy}>
            {busy ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="app-switch">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </main>
    </div>
  );
}
"""

_DASHBOARD = r"""import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { request } from '../auth.js';

const STATUSES = ['draft', 'published', 'archived'];
const LABELS = { draft: 'Draft', published: 'Published', archived: 'Archived' };

function statusOf(record) {
  return STATUSES.includes(record.status) ? record.status : 'draft';
}

export default function Dashboard() {
  const [records, setRecords] = useState([]);
  const [state, setState] = useState('loading');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setState('loading');
    setError('');
    try {
      const json = await request('/records');
      setRecords(Array.isArray(json.data) ? json.data : []);
      setState('ready');
    } catch (failure) {
      setError('We could not load your records.');
      setState('error');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const totals = useMemo(() => records.reduce((result, record) => {
    const status = statusOf(record);
    return { ...result, [status]: result[status] + 1, total: result.total + 1 };
  }, { draft: 0, published: 0, archived: 0, total: 0 }), [records]);

  const recent = useMemo(() => [...records]
    .sort((left, right) => String(right.createdAt || right.updatedAt || '')
      .localeCompare(String(left.createdAt || left.updatedAt || '')))
    .slice(0, 5), [records]);

  return (
    <div className="app-page">
      <header className="app-page-head">
        <div>
          <p className="app-eyebrow">Workspace</p>
          <h1>Your workspace</h1>
          <p className="app-lede">
            These totals are calculated from the records your account can access.
          </p>
        </div>
        <Link className="app-button" to="/records">Manage records</Link>
      </header>

      {state === 'loading' && <p className="app-status" role="status">Loading your records…</p>}

      {state === 'error' && (
        <div className="app-panel" role="alert">
          <p>{error}</p>
          <button type="button" className="app-button" onClick={load}>Try again</button>
        </div>
      )}

      {state === 'ready' && (
        <>
          <section className="app-section" aria-labelledby="totals-title">
            <h2 id="totals-title">Record totals</h2>
            {records.length === 0 ? (
              <p className="app-empty">No records yet. Create the first one from All records.</p>
            ) : (
              <dl className="app-metrics">
                {STATUSES.map((status) => (
                  <div key={status}>
                    <dt>{LABELS[status]}</dt>
                    <dd>{totals[status]}</dd>
                  </div>
                ))}
                <div>
                  <dt>Total</dt>
                  <dd>{totals.total}</dd>
                </div>
              </dl>
            )}
          </section>

          <section className="app-section" aria-labelledby="recent-title">
            <h2 id="recent-title">Recent records</h2>
            {recent.length === 0 ? (
              <p className="app-empty">No recent records yet.</p>
            ) : (
              <ul className="app-list">
                {recent.map((record) => (
                  <li key={record.id}>
                    <span>{record.title}</span>
                    <span className={`app-pill app-pill-${statusOf(record)}`}>
                      {LABELS[statusOf(record)]}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
"""

_RECORDS = r"""import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { request } from '../auth.js';

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

  useEffect(() => {
    load();
  }, [load]);

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
    try {
      if (editingId) {
        await request(`/records/${editingId}`, {
          method: 'PUT',
          body: { title, body, status: form.status },
        });
      } else {
        const id = crypto.randomUUID();
        await request('/records', {
          method: 'POST',
          body: { id, title, body, status: form.status },
        });
      }
      resetForm();
      await load();
    } catch (failure) {
      setFormError('The record was not saved. Check the details and try again.');
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

_SETTINGS = r"""import React from 'react';
import { useNavigate } from 'react-router-dom';
import { currentUser, signOut } from '../auth.js';

function detail(user, key) {
  const value = user[key];
  return typeof value === 'string' && value.trim() ? value.trim() : 'Not provided';
}

export default function Settings() {
  const navigate = useNavigate();
  const user = currentUser();

  const leave = () => {
    signOut();
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-page">
      <header className="app-page-head">
        <div>
          <p className="app-eyebrow">Account</p>
          <h1>Account settings</h1>
          <p className="app-lede">
            These values come from the session created when you signed in.
          </p>
        </div>
      </header>

      <section className="app-panel" aria-labelledby="profile-title">
        <h2 id="profile-title">Profile</h2>
        <div className="app-form">
          <label htmlFor="settings-name">Name</label>
          <input id="settings-name" type="text" readOnly value={detail(user, 'name')} />
          <label htmlFor="settings-email">Email</label>
          <input id="settings-email" type="email" readOnly value={detail(user, 'email')} />
        </div>
        <p className="app-note">
          Profile fields are read-only here. They show what the API returned for this session.
        </p>
      </section>

      <section className="app-panel" aria-labelledby="session-title">
        <h2 id="session-title">Session</h2>
        <p>Signing out removes the token stored in this browser.</p>
        <button type="button" className="app-button" onClick={leave}>Sign out</button>
      </section>
    </div>
  );
}
"""

_APP_CSS = r""":root {
  --app-primary: @@PRIMARY@@;
  --app-accent: @@ACCENT@@;
  --app-surface: @@SURFACE@@;
  --app-raised: @@RAISED@@;
  --app-soft: @@SOFT@@;
  --app-line: @@LINE@@;
  --app-ink: @@INK@@;
  --app-muted: @@MUTED@@;
  --app-action: @@ACTION@@;
  --app-on-action: @@ON_ACTION@@;
  --app-danger: @@DANGER@@;
  --app-radius: @@RADIUS@@;
  --app-font: "@@FONT@@";
  --app-display: "@@DISPLAY@@";
  --app-gutter: clamp(1rem, 4vw, 2rem);
}

* { box-sizing: border-box; }

.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-skip {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
  background: var(--app-action);
  color: var(--app-on-action);
  font-weight: 700;
}

.app-skip:focus {
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 10;
  width: auto;
  height: auto;
  margin: 0;
  padding: 0.75rem 1rem;
  overflow: visible;
  clip-path: none;
  border-radius: var(--app-radius);
}

.app-header {
  border-bottom: 1px solid var(--app-line);
  background: var(--app-surface);
}

.app-header-inner {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 1rem var(--app-gutter);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
  align-items: center;
  justify-content: space-between;
}

.app-brand {
  font-family: var(--app-display), Georgia, serif;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--app-ink);
  text-decoration: none;
}

.app-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.app-nav a {
  display: inline-flex;
  align-items: center;
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  color: var(--app-muted);
  text-decoration: none;
  font-size: 0.925rem;
}

.app-nav a:hover { color: var(--app-ink); background: var(--app-soft); }

.app-nav a.active {
  color: var(--app-ink);
  background: var(--app-soft);
  font-weight: 600;
}

.app-session {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  align-items: center;
  min-width: 0;
}

.app-session-name {
  max-width: 18rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
  color: var(--app-muted);
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 2rem var(--app-gutter) 4rem;
}

.app-page { display: grid; gap: 1.5rem; }

.app-page-head {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  justify-content: space-between;
}

.app-page h1 {
  margin: 0.25rem 0 0.5rem;
  font-family: var(--app-display), Georgia, serif;
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--app-ink);
}

.app-page h2 {
  margin: 0 0 0.75rem;
  font-size: 1.125rem;
  color: var(--app-ink);
}

.app-eyebrow {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--app-accent);
}

.app-lede { margin: 0; max-width: 52ch; color: var(--app-muted); line-height: 1.6; }

.app-auth {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem var(--app-gutter);
}

.app-auth-card {
  width: min(100%, 26rem);
  padding: clamp(1.5rem, 5vw, 2.5rem);
  border: 1px solid var(--app-line);
  border-radius: var(--app-radius);
  background: var(--app-raised);
  box-shadow: 0 24px 60px rgb(0 0 0 / 0.32);
}

.app-auth-card h1 {
  margin: 0.35rem 0 0.5rem;
  font-family: var(--app-display), Georgia, serif;
  font-size: clamp(1.8rem, 5vw, 2.3rem);
  letter-spacing: -0.03em;
  color: var(--app-ink);
}

.app-auth-card form { display: grid; gap: 0.45rem; margin-top: 1.5rem; }

.app-auth-card .app-button { margin-top: 0.75rem; }

.app-switch { margin: 1.25rem 0 0; color: var(--app-muted); font-size: 0.925rem; }

.app-switch a { color: var(--app-accent); }

.app-panel,
.app-section {
  padding: clamp(1.1rem, 3vw, 1.6rem);
  border: 1px solid var(--app-line);
  border-radius: var(--app-radius);
  background: var(--app-raised);
  min-width: 0;
}

.app-section h2 { margin-top: 0; }

.app-form { display: grid; gap: 0.45rem; max-width: 38rem; }

.app-field { display: grid; gap: 0.35rem; min-width: 0; }

label { color: var(--app-muted); font-size: 0.875rem; font-weight: 600; }

input,
select,
textarea {
  width: 100%;
  min-width: 0;
  padding: 0.7rem 0.8rem;
  border: 1px solid var(--app-line);
  border-radius: calc(var(--app-radius) * 0.55);
  background: var(--app-surface);
  color: var(--app-ink);
  font: inherit;
}

textarea { resize: vertical; }

input[readonly] { color: var(--app-muted); }

.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  width: fit-content;
  max-width: 100%;
  padding: 0.7rem 1.1rem;
  border: 1px solid transparent;
  border-radius: calc(var(--app-radius) * 0.55);
  background: var(--app-action);
  color: var(--app-on-action);
  font: inherit;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

.app-button:hover { filter: brightness(1.05); }

.app-button:disabled { opacity: 0.55; cursor: not-allowed; }

.app-button-quiet {
  background: transparent;
  border-color: var(--app-line);
  color: var(--app-ink);
}

.app-button-danger {
  background: transparent;
  border-color: var(--app-danger);
  color: var(--app-danger);
}

.app-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }

.app-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  padding: 1rem;
  border: 1px solid var(--app-line);
  border-radius: var(--app-radius);
  background: var(--app-raised);
}

.app-toolbar .app-field { flex: 1 1 12rem; }

.app-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(8.5rem, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 0;
}

.app-metrics > div {
  padding: 1rem;
  border: 1px solid var(--app-line);
  border-radius: calc(var(--app-radius) * 0.7);
  background: var(--app-surface);
  min-width: 0;
}

.app-metrics dt { color: var(--app-muted); font-size: 0.85rem; }

.app-metrics dd {
  margin: 0.35rem 0 0;
  font-size: 1.9rem;
  font-weight: 800;
  color: var(--app-ink);
}

.app-list,
.app-records {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.75rem;
}

.app-list li {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--app-line);
}

.app-list li:last-child { border-bottom: 0; }

.app-record {
  padding: 1rem;
  border: 1px solid var(--app-line);
  border-radius: calc(var(--app-radius) * 0.7);
  background: var(--app-surface);
  min-width: 0;
  overflow-wrap: anywhere;
}

.app-record-head {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: space-between;
}

.app-record-head h2 { margin: 0; font-size: 1.05rem; }

.app-record-body { margin: 0.6rem 0 0; color: var(--app-muted); line-height: 1.6; }

.app-record .app-actions { margin-top: 0.85rem; }

.app-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--app-line);
  border-radius: 999px;
  font-size: 0.78rem;
  color: var(--app-muted);
}

.app-pill-published { color: var(--app-accent); border-color: var(--app-accent); }

.app-pill-archived { opacity: 0.75; }

.app-status,
.app-empty,
.app-note {
  margin: 0;
  color: var(--app-muted);
  line-height: 1.6;
}

.app-status { padding: 0.75rem 0; }

.app-note { margin-top: 1rem; font-size: 0.9rem; }

.app-error {
  margin: 0.25rem 0;
  color: var(--app-danger);
  font-size: 0.9rem;
}

:focus-visible {
  outline: 2px solid var(--app-accent);
  outline-offset: 3px;
}

@media (max-width: 640px) {
  .app-header-inner { align-items: flex-start; }
  .app-nav { order: 3; width: 100%; }
  .app-session { width: 100%; justify-content: space-between; }
  .app-session-name { max-width: 60%; }
  .app-page-head { align-items: flex-start; }
  .app-button { width: 100%; }
  .app-actions .app-button { width: auto; }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
"""


def _app_css(design: Dict[str, Any]) -> str:
    slate = design["slate"]
    return _bind(
        _APP_CSS,
        PRIMARY=design["primary"],
        ACCENT=design["accent"],
        SURFACE=slate["950"],
        RAISED=slate["900"],
        SOFT=slate["800"],
        LINE=slate["700"],
        INK=design["ink"],
        MUTED=design["muted"],
        ACTION=hsl_to_hex(design["hue"], 68, 80),
        ON_ACTION=slate["950"],
        DANGER=hsl_to_hex(5, 85, 80),
        RADIUS=design["radius"]["2xl"],
        FONT=design["fonts"]["sans"],
        DISPLAY=design["fonts"]["display"],
    )


def render_app_files(brand: str, industry: str, design: Dict[str, Any]) -> Dict[str, str]:
    """Return the complete authenticated app shell, prefixed with `frontend/`.

    `industry` is accepted for pipeline symmetry; app copy stays capability-based
    because the generated backend proves records/auth only.
    """
    del industry  # Copy never claims an industry capability the backend lacks.
    files = {
        "frontend/src/App.jsx": _APP_JSX,
        "frontend/src/components/AppShell.jsx": _bind(_APP_SHELL, BRAND=_js(brand)),
        "frontend/src/auth.js": _AUTH_JS,
        "frontend/src/pages/Login.jsx": _bind(_LOGIN, BRAND=_js(brand)),
        "frontend/src/pages/Register.jsx": _bind(_REGISTER, BRAND=_js(brand)),
        "frontend/src/pages/Dashboard.jsx": _DASHBOARD,
        "frontend/src/pages/Records.jsx": _RECORDS,
        "frontend/src/pages/Settings.jsx": _SETTINGS,
        "frontend/src/app.css": _app_css(design),
    }
    return files


__all__ = ["render_app_files", "app_route_expectations"]
