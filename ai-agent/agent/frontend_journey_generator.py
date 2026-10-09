"""Generate accessible account and contact journeys for full-stack React projects."""

import os
import re
from pathlib import Path
from typing import Dict

from utils.file_manager import FileManager


def generate_frontend_journeys(frontend_dir: Path, brand_name: str) -> Dict[str, bool]:
    """Create API-backed auth/contact components and route auth pages where possible."""
    src_dir = frontend_dir / "src"
    pages_dir = src_dir / "pages"
    services_dir = src_dir / "services"
    forms_dir = src_dir / "components" / "forms"
    for directory in (pages_dir, services_dir, forms_dir):
        directory.mkdir(parents=True, exist_ok=True)

    api_path = services_dir / "api.js"
    if not api_path.exists():
        FileManager.write_file(str(api_path), """const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\\/$/, '');

async function request(path, options = {}, retry = true) {
  const token = typeof localStorage === 'undefined' ? null : localStorage.getItem('auth_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token && !path.startsWith('/auth/')) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}/api${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });
  const payload = await response.json().catch(() => ({}));

  if (response.status === 401 && retry && token &&
      !['/auth/login', '/auth/register', '/auth/refresh'].includes(path)) {
    const refreshed = await request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({}),
    }, false);
    const accessToken = refreshed.data?.data?.accessToken;
    if (!accessToken) throw new Error('Your session has expired. Please sign in again.');
    localStorage.setItem('auth_token', accessToken);
    return request(path, options, false);
  }

  if (!response.ok) {
    const error = new Error(payload.message || 'The request could not be completed.');
    error.response = { status: response.status, data: payload };
    throw error;
  }
  return { data: payload };
}

const api = {
  get: (path) => request(path),
  post: (path, data) => request(path, { method: 'POST', body: JSON.stringify(data) }),
};

export default api;
""")

    login_page = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function GeneratedLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email.trim()) || !password) {
      setError('Enter a valid email address and password.');
      return;
    }
    setSubmitting(true);
    try {
      const response = await api.post('/auth/login', { email: email.trim(), password });
      const accessToken = response.data?.data?.accessToken;
      if (!accessToken) throw new Error('The server did not return an access token.');
      localStorage.setItem('auth_token', accessToken);
      setSuccess('You are signed in.');
    } catch (requestError) {
      setError(requestError.response?.data?.message || requestError.message || 'Sign in failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-md items-center px-4 py-12">
      <section className="w-full rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl sm:p-8">
        <h1 className="text-2xl font-bold text-white">Sign in to __BRAND__</h1>
        <p className="mt-2 text-sm text-slate-400">Use your account details to continue.</p>
        {error && <p id="login-error" className="mt-4 rounded-lg bg-red-950/50 p-3 text-sm text-red-200" role="alert">{error}</p>}
        {success && <p className="mt-4 rounded-lg bg-emerald-950/50 p-3 text-sm text-emerald-200" role="status">{success}</p>}
        <form className="mt-6 space-y-4" onSubmit={handleSubmit} aria-busy={submitting}>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="login-email">Email address</label>
            <input id="login-email" name="email" type="email" autoComplete="email" required
              value={email} onChange={(event) => setEmail(event.target.value)}
              aria-describedby={error ? 'login-error' : undefined} aria-invalid={Boolean(error)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="login-password">Password</label>
            <input id="login-password" name="password" type="password" autoComplete="current-password" required
              value={password} onChange={(event) => setPassword(event.target.value)}
              aria-describedby={error ? 'login-error' : undefined} aria-invalid={Boolean(error)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
          </div>
          <button type="submit" disabled={submitting}
            className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition-colors hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-slate-400">New here? <Link className="text-cyan-300 underline" to="/register">Create an account</Link></p>
      </section>
    </main>
  );
}
""".replace("__BRAND__", brand_name)
    FileManager.write_file(str(pages_dir / "GeneratedLogin.jsx"), login_page)

    register_page = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function GeneratedRegister() {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (form.name.trim().length < 2 || form.name.trim().length > 100) {
      setError('Enter a name between 2 and 100 characters.');
      return;
    }
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(form.email.trim())) {
      setError('Enter a valid email address.');
      return;
    }
    if (form.password.length < 10 || new TextEncoder().encode(form.password).length > 72) {
      setError('Choose a password between 10 and 72 bytes.');
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      const response = await api.post('/auth/register', {
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      const accessToken = response.data?.data?.accessToken;
      if (!accessToken) throw new Error('The server did not return an access token.');
      localStorage.setItem('auth_token', accessToken);
      setSuccess('Your account was created successfully.');
      setForm((current) => ({ ...current, password: '', confirmPassword: '' }));
    } catch (requestError) {
      setError(requestError.response?.data?.message || requestError.message || 'Account creation failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-md items-center px-4 py-12">
      <section className="w-full rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl sm:p-8">
        <h1 className="text-2xl font-bold text-white">Create your __BRAND__ account</h1>
        <p className="mt-2 text-sm text-slate-400">Your details are sent securely to the account service.</p>
        {error && <p id="register-error" className="mt-4 rounded-lg bg-red-950/50 p-3 text-sm text-red-200" role="alert">{error}</p>}
        {success && <p className="mt-4 rounded-lg bg-emerald-950/50 p-3 text-sm text-emerald-200" role="status">{success}</p>}
        <form className="mt-6 space-y-4" onSubmit={handleSubmit} aria-busy={submitting}>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="register-name">Full name</label>
            <input id="register-name" name="name" type="text" autoComplete="name" required minLength={2} maxLength={100}
              value={form.name} onChange={updateField} aria-describedby={error ? 'register-error' : undefined} aria-invalid={Boolean(error)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="register-email">Email address</label>
            <input id="register-email" name="email" type="email" autoComplete="email" required
              value={form.email} onChange={updateField} aria-describedby={error ? 'register-error' : undefined} aria-invalid={Boolean(error)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="register-password">Password</label>
            <input id="register-password" name="password" type="password" autoComplete="new-password" required minLength={10} maxLength={128}
              value={form.password} onChange={updateField} aria-describedby="register-password-hint"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
            <p id="register-password-hint" className="mt-1 text-xs text-slate-400">Use 10 or more characters; passwords above 72 bytes are not accepted.</p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="register-confirm-password">Confirm password</label>
            <input id="register-confirm-password" name="confirmPassword" type="password" autoComplete="new-password" required
              value={form.confirmPassword} onChange={updateField} aria-describedby={error ? 'register-error' : undefined} aria-invalid={Boolean(error)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
          </div>
          <button type="submit" disabled={submitting}
            className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition-colors hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-slate-400">Already registered? <Link className="text-cyan-300 underline" to="/login">Sign in</Link></p>
      </section>
    </main>
  );
}
""".replace("__BRAND__", brand_name)
    FileManager.write_file(str(pages_dir / "GeneratedRegister.jsx"), register_page)

    contact_form = """import React, { useState } from 'react';
import api from '../../services/api';

export default function GeneratedContactForm() {
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [succeeded, setSucceeded] = useState(false);

  const updateField = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSucceeded(false);
    const values = { name: form.name.trim(), email: form.email.trim(), message: form.message.trim() };
    if (values.name.length < 2 || values.name.length > 100) {
      setError('Enter a name between 2 and 100 characters.');
      return;
    }
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(values.email)) {
      setError('Enter a valid email address.');
      return;
    }
    if (values.message.length < 10 || values.message.length > 5000) {
      setError('Enter a message between 10 and 5000 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/contact', values);
      setSucceeded(true);
      setForm({ name: '', email: '', message: '' });
    } catch (requestError) {
      setError(requestError.response?.data?.message || requestError.message || 'Your message could not be sent. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (succeeded) {
    return <p className="rounded-lg bg-emerald-950/50 p-4 text-sm text-emerald-200" role="status">Your message was received. Thank you for getting in touch.</p>;
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} aria-busy={submitting}>
      {error && <p id="contact-error" className="rounded-lg bg-red-950/50 p-3 text-sm text-red-200" role="alert">{error}</p>}
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="contact-name">Your name</label>
        <input id="contact-name" name="name" type="text" autoComplete="name" required minLength={2} maxLength={100}
          value={form.name} onChange={updateField} aria-describedby={error ? 'contact-error' : undefined} aria-invalid={Boolean(error)}
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="contact-email">Email address</label>
        <input id="contact-email" name="email" type="email" autoComplete="email" required
          value={form.email} onChange={updateField} aria-describedby={error ? 'contact-error' : undefined} aria-invalid={Boolean(error)}
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-200" htmlFor="contact-message">How can we help?</label>
        <textarea id="contact-message" name="message" rows={5} required minLength={10} maxLength={5000}
          value={form.message} onChange={updateField} aria-describedby={error ? 'contact-error' : undefined} aria-invalid={Boolean(error)}
          className="w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500" />
      </div>
      <button type="submit" disabled={submitting}
        className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition-colors hover:bg-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">
        {submitting ? 'Sending…' : 'Send message'}
      </button>
    </form>
  );
}
"""
    FileManager.write_file(str(forms_dir / "GeneratedContactForm.jsx"), contact_form)

    generated_contact_page = """import React from 'react';
import GeneratedContactForm from '../components/forms/GeneratedContactForm';

export default function GeneratedContactPage() {
  return (
    <main className="mx-auto min-h-[70vh] w-full max-w-2xl px-4 py-12">
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Contact</p>
        <h1 className="mt-2 text-3xl font-bold text-white">How can we help?</h1>
        <p className="mt-2 text-sm text-slate-400">Send us a message and we will get back to you.</p>
        <div className="mt-6"><GeneratedContactForm /></div>
      </section>
    </main>
  );
}
"""
    generated_contact_page_path = pages_dir / "GeneratedContactPage.jsx"
    if not generated_contact_page_path.exists():
        FileManager.write_file(str(generated_contact_page_path), generated_contact_page)

    app_file = src_dir / "App.jsx"
    if not app_file.is_file():
        return {"auth_routes": False, "contact_form": False}
    original_source = FileManager.read_file(str(app_file))
    app_source = original_source
    contact_component = "GeneratedContactPage"
    contact_module = "./pages/GeneratedContactPage.jsx"
    contact_form_wired = False
    contact_imports = re.finditer(
        r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]""",
        app_source,
    )
    for match in contact_imports:
        module_path = match.group(2)
        if "contact" not in module_path.lower():
            continue
        candidate_base = (src_dir / module_path).resolve()
        candidates = (
            candidate_base,
            candidate_base.with_suffix(".jsx"),
            candidate_base.with_suffix(".js"),
            candidate_base / "index.jsx",
        )
        contact_page_path = next((path for path in candidates if path.is_file()), None)
        if contact_page_path is None:
            continue
        contact_page_source = FileManager.read_file(str(contact_page_path))
        form_pattern = re.compile(r"<form\b[^>]*>[\s\S]*?</form>", re.IGNORECASE)
        if not form_pattern.search(contact_page_source):
            continue
        has_contact_form_import = bool(
            re.search(r"""import\s+GeneratedContactForm\s+from\s+['"]""", contact_page_source)
        )
        contact_page_source = form_pattern.sub("<GeneratedContactForm />", contact_page_source, count=1)
        relative_import = os.path.relpath(
            forms_dir / "GeneratedContactForm.jsx",
            contact_page_path.parent,
        ).replace(os.sep, "/")
        relative_import = re.sub(r"\.jsx$", "", relative_import)
        import_line = f"import GeneratedContactForm from '{relative_import}';"
        if not has_contact_form_import:
            existing_imports = list(re.finditer(r"(?m)^import\s+[^\n;]+;\s*$", contact_page_source))
            if existing_imports:
                insert_at = existing_imports[-1].end()
                contact_page_source = (
                    contact_page_source[:insert_at] + "\n" + import_line + contact_page_source[insert_at:]
                )
            else:
                contact_page_source = import_line + "\n" + contact_page_source
        FileManager.write_file(str(contact_page_path), contact_page_source)
        contact_component = match.group(1)
        contact_module = module_path
        contact_form_wired = True
        break

    route_entries = (
        ("/login", "GeneratedLogin", "./pages/GeneratedLogin.jsx"),
        ("/register", "GeneratedRegister", "./pages/GeneratedRegister.jsx"),
        ("/contact", contact_component, contact_module),
    )
    missing_routes = []
    for route_path, component, module_path in route_entries:
        route_pattern = re.compile(rf"""path\s*=\s*['"]{re.escape(route_path)}['"]""")
        route_index = next(
            (
                index for index, line in enumerate(app_source.splitlines())
                if "<Route" in line and route_pattern.search(line)
            ),
            None,
        )
        if route_index is None:
            missing_routes.append((route_path, component))
        else:
            lines = app_source.splitlines()
            element = f"element={{<{component} />}}"
            if re.search(r"element\s*=\s*\{[^}]*\}", lines[route_index]):
                lines[route_index] = re.sub(
                    r"element\s*=\s*\{[^}]*\}",
                    lambda _: element,
                    lines[route_index],
                    count=1,
                )
            else:
                lines[route_index] = re.sub(
                    r"(<Route\b[^>]*)(/?>)",
                    lambda match: f"{match.group(1)} {element}{match.group(2)}",
                    lines[route_index],
                    count=1,
                )
            app_source = "\n".join(lines) + ("\n" if app_source.endswith("\n") else "")
        if component not in app_source:
            import_line = f"import {component} from '{module_path}';"
            imports = list(re.finditer(r"(?m)^import\s+[^\n;]+;\s*$", app_source))
            if imports:
                insert_at = imports[-1].end()
                app_source = app_source[:insert_at] + "\n" + import_line + app_source[insert_at:]
            else:
                app_source = import_line + "\n" + app_source

    route_close = app_source.rfind("</Routes>")
    route_container = "<Routes" in app_source and route_close >= 0
    route_tags = list(re.finditer(r"<Route\b", app_source))
    auth_routes_wired = bool(route_tags and route_container)
    if auth_routes_wired and missing_routes:
        route_markup = "\n".join(
            f'          <Route key="{component}" path="{route_path}" element={{<{component} />}} />'
            for route_path, component in missing_routes
        )
        app_source = app_source[:route_close] + route_markup + "\n        " + app_source[route_close:]
    if app_source != original_source:
        FileManager.write_file(str(app_file), app_source)
    contact_route_wired = bool(
        auth_routes_wired
        and re.search(r"""<Route\b[^>]*path\s*=\s*['"]/contact['"]""", app_source)
        and contact_component in app_source
    )
    return {
        "auth_routes": auth_routes_wired,
        "contact_form": contact_form_wired or contact_route_wired,
    }
