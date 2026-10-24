"""Full-Stack Ultra Engine — LumicorePro AI Agent
================================================
High-speed autonomous engine that generates clean, production-ready, international-standard
full-stack web applications (React 19 + Tailwind 3 Frontend, Express.js REST API Backend,
Sequelize Database Models, JWT Auth, Docker Infrastructure) in single-digit seconds.
"""

import os
import time
import json
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger
from agent.hyper_unique_site_engine import HyperUniqueSiteEngine
from agent.omni_repair_engine import OmniRepairEngine
from agent.generation_contract import resolve_generation_contract


# ── Generated-project production assets ────────────────────────────────────
# These are plain strings (not f-strings) so JSX braces stay literal; brand and
# colour are substituted with .replace() by _marketing_pages().

_CONTACT_ROUTE_JS = r"""/** routes/contact — public contact form endpoint.
 * The body is validated + sanitised by middleware/validate before it reaches
 * Sequelize (parameterised, so SQL injection is structural, not a filter).
 */
const express = require('express');
const { DataTypes } = require('sequelize');
const { sequelize } = require('../models');
const { validate } = require('../middleware/validate');

const router = express.Router();
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const ContactMessage = sequelize.define('ContactMessage', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING(120), allowNull: false },
  email: { type: DataTypes.STRING(254), allowNull: false },
  message: { type: DataTypes.TEXT, allowNull: false },
}, { tableName: 'contact_messages', underscored: true });

const RULES = {
  name: { required: true, type: 'string', min: 1, max: 120 },
  email: { required: true, type: 'string', max: 254 },
  message: { required: true, type: 'string', min: 10, max: 5000 },
};

router.post('/', validate(RULES), async (req, res, next) => {
  if (!EMAIL_RE.test(String(req.body.email || ''))) {
    return res.status(422).json({
      success: false,
      code: 'VALIDATION_ERROR',
      errors: { email: 'email must be a valid address' },
    });
  }
  try {
    const row = await ContactMessage.create({
      name: req.body.name,
      email: req.body.email,
      message: req.body.message,
    });
    return res.status(201).json({
      success: true,
      message: 'Message received — we will reply within one business day.',
      data: { id: row.id },
    });
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
"""

_CONTACT_MIGRATION_JS = """/** 003: contact_messages — persisted submissions from the public contact form. */
const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('contact_messages', {
      id: { type: DataTypes.UUID, primaryKey: true },
      name: { type: DataTypes.STRING(120), allowNull: false },
      email: { type: DataTypes.STRING(254), allowNull: false },
      message: { type: DataTypes.TEXT, allowNull: false },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });
    await queryInterface.addIndex('contact_messages', ['created_at']);
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('contact_messages');
  },
};
"""

_BACKEND_ENV_EXAMPLE = """# Backend runtime — copy to .env and fill every value.
PORT=5000
NODE_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lumicore_app
DB_USER=postgres
DB_PASSWORD=
# REQUIRED, minimum 32 characters. Generate:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
JWT_SECRET=
# Comma-separated origins allowed by CORS (the frontend origin in production).
CORS_ORIGIN=http://localhost:5173
"""

_BACKEND_SMOKE_TEST_JS = """/** Backend smoke tests — run with `npm test` (node --test), no database needed. */
const test = require('node:test');
const assert = require('node:assert/strict');
const { validate, sanitize } = require('../middleware/validate');

const run = (schema, body) => {
  let outcome = { nextCalled: false, error: null };
  const req = { body };
  const middleware = validate(schema);
  middleware(req, {}, (err) => {
    outcome = { nextCalled: true, error: err || null, body: req.body };
  });
  return outcome;
};

test('validate rejects a missing required field with 422', () => {
  const result = run({ name: { required: true, type: 'string' } }, {});
  assert.equal(result.nextCalled, true);
  assert.equal(result.error.status, 422);
  assert.equal(result.error.code, 'VALIDATION_ERROR');
  assert.match(result.error.errors.name, /required/);
});

test('validate rejects an over-long field', () => {
  const result = run({ name: { required: true, type: 'string', max: 5 } }, { name: 'toolong' });
  assert.equal(result.error.status, 422);
  assert.match(result.error.errors.name, /<= 5/);
});

test('validate passes a clean payload and sanitises it', () => {
  const result = run({ name: { required: true, type: 'string', max: 40 } }, { name: '<script>alert(1)</script>' });
  assert.equal(result.error, null);
  assert.equal(result.body.name, '&lt;script&gt;alert(1)&lt;/script&gt;');
});

test('sanitize escapes every HTML-significant character', () => {
  assert.equal(sanitize(`<>&"'`), '&lt;&gt;&amp;&quot;&#x27;');
});

test('sanitize walks nested objects and arrays', () => {
  const cleaned = sanitize({ a: ['<b>', { c: '<i>' }] });
  assert.equal(cleaned.a[0], '&lt;b&gt;');
  assert.equal(cleaned.a[1].c, '&lt;i&gt;');
});
"""

_MARKETING_PAGES: Dict[str, str] = {
    "Features.jsx": r"""import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ShieldCheck, Globe2, BarChart3, Workflow, Lock } from 'lucide-react';

const FEATURES = [
  {
    icon: Zap,
    title: 'Sub-second workflows',
    body: 'Streaming execution, optimistic UI and background jobs keep every interaction under a second, even at peak load.',
  },
  {
    icon: ShieldCheck,
    title: 'Security by default',
    body: 'JWT sessions, hashed credentials, parameterised queries, input sanitisation and rate limiting ship in every build.',
  },
  {
    icon: Globe2,
    title: 'Global edge delivery',
    body: 'Static assets and API responses are cached at the edge, with automatic regional failover and gzip/brotli compression.',
  },
  {
    icon: BarChart3,
    title: 'Operational analytics',
    body: 'Usage, latency and error budgets are instrumented from day one, so decisions are based on evidence, not guesses.',
  },
  {
    icon: Workflow,
    title: 'Automated pipelines',
    body: 'Build, test, database migration and release verification run on every change with a fail-closed quality gate.',
  },
  {
    icon: Lock,
    title: 'Ownership controls',
    body: 'Role-based access, per-tenant scoping and audited mutations keep every record with the organisation that owns it.',
  },
];

const STEPS = [
  { step: '01', title: 'Create your account', body: 'Register in under a minute — email verification and secure sessions are handled for you.' },
  { step: '02', title: 'Configure your workspace', body: 'Invite your team, connect your data and choose the plan that matches your volume.' },
  { step: '03', title: 'Ship with confidence', body: 'Deploy to production with automated checks, live health monitoring and instant rollback.' },
];

export default function Features() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <section className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[__COLOR__]">Platform capabilities</p>
        <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-white leading-tight">
          Everything __BRAND__ needs to run in production
        </h1>
        <p className="mt-5 text-lg text-slate-400 leading-relaxed">
          A complete platform, not a starter kit: authentication, persistence, APIs, observability
          and deployment workflows are built in from the first commit.
        </p>
        <div className="mt-8 flex flex-wrap gap-4">
          <Link to="/register" className="px-7 py-3.5 rounded-full bg-[__COLOR__] text-white font-semibold hover:opacity-90 transition-opacity">
            Start free
          </Link>
          <Link to="/pricing" className="px-7 py-3.5 rounded-full bg-slate-900 border border-slate-800 text-slate-200 font-semibold hover:bg-slate-800 transition-colors">
            Compare plans
          </Link>
        </div>
      </section>

      <section className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <article key={title} className="p-7 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-[__COLOR__]/40 transition-colors">
            <Icon className="w-9 h-9 text-[__COLOR__]" aria-hidden="true" />
            <h2 className="mt-5 text-lg font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm text-slate-400 leading-relaxed">{body}</p>
          </article>
        ))}
      </section>

      <section className="mt-20">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white text-center">How it works</h2>
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
          {STEPS.map(({ step, title, body }) => (
            <div key={step} className="p-7 rounded-3xl bg-slate-950 border border-slate-800">
              <span className="text-xs font-mono text-[__COLOR__]">{step}</span>
              <h3 className="mt-3 text-lg font-bold text-white">{title}</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-20 rounded-3xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 p-10 text-center">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Ready when you are</h2>
        <p className="mt-3 text-slate-400">Create an account and explore the full platform with no credit card.</p>
        <Link to="/register" className="inline-block mt-7 px-8 py-3.5 rounded-full bg-[__COLOR__] text-white font-semibold hover:opacity-90 transition-opacity">
          Create free account
        </Link>
      </section>
    </div>
  );
}
""",
    "Pricing.jsx": r"""import React from 'react';
import { Link } from 'react-router-dom';
import { Check, Sparkles } from 'lucide-react';

const TIERS = [
  {
    name: 'Starter',
    price: 29,
    blurb: 'For solo builders validating an idea.',
    features: ['1 workspace', 'Up to 5,000 API calls / month', 'Community support', 'Core analytics'],
  },
  {
    name: 'Pro',
    price: 79,
    popular: true,
    blurb: 'For teams shipping to real customers.',
    features: ['5 workspaces', '100,000 API calls / month', 'Priority email support', 'Advanced analytics', 'Custom domains'],
  },
  {
    name: 'Enterprise',
    price: 199,
    blurb: 'For organisations with compliance needs.',
    features: ['Unlimited workspaces', 'Unlimited API calls', 'Dedicated support', 'SSO & audit logs', '99.9% uptime SLA'],
  },
];

const FAQ = [
  ['Can I change plans later?', 'Yes — upgrades and downgrades take effect immediately, and unused time is prorated.'],
  ['Is there a free trial?', 'Every tier starts with a 14-day trial. No credit card is required to explore the platform.'],
  ['What happens to my data if I downgrade?', 'Your data stays intact. Only workspace and API-volume limits change.'],
];

export default function Pricing() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <header className="max-w-2xl mx-auto text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[__COLOR__]">Pricing</p>
        <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-white">Simple, predictable plans</h1>
        <p className="mt-4 text-lg text-slate-400">Start small, scale without renegotiating. Every plan includes the full API.</p>
      </header>

      <section className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {TIERS.map((tier) => (
          <article
            key={tier.name}
            className={`relative flex flex-col p-8 rounded-3xl bg-slate-900 border ${tier.popular ? 'border-[__COLOR__] shadow-2xl shadow-[__COLOR__]/10' : 'border-slate-800'}`}
          >
            {tier.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[__COLOR__] text-white text-xs font-bold">
                <Sparkles className="w-3.5 h-3.5" aria-hidden="true" /> Most popular
              </span>
            )}
            <h2 className="text-xl font-bold text-white">{tier.name}</h2>
            <p className="mt-1 text-sm text-slate-400">{tier.blurb}</p>
            <p className="mt-6 text-4xl font-extrabold text-white">
              ${tier.price}<span className="text-base font-normal text-slate-400">/month</span>
            </p>
            <ul className="mt-7 space-y-3 flex-1">
              {tier.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-slate-300">
                  <Check className="w-4 h-4 mt-0.5 text-[__COLOR__] shrink-0" aria-hidden="true" />
                  {feature}
                </li>
              ))}
            </ul>
            <Link
              to="/register"
              className={`mt-8 block text-center px-6 py-3 rounded-full font-semibold transition-opacity ${tier.popular ? 'bg-[__COLOR__] text-white hover:opacity-90' : 'bg-slate-800 text-slate-100 hover:bg-slate-700'}`}
            >
              Choose {tier.name}
            </Link>
          </article>
        ))}
      </section>

      <section className="mt-20 max-w-3xl mx-auto">
        <h2 className="text-2xl font-extrabold text-white text-center">Frequently asked questions</h2>
        <div className="mt-8 space-y-3">
          {FAQ.map(([question, answer]) => (
            <details key={question} className="group rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <summary className="cursor-pointer list-none flex items-center justify-between text-sm font-semibold text-white">
                {question}
                <span className="text-[__COLOR__] group-open:rotate-45 transition-transform" aria-hidden="true">+</span>
              </summary>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">{answer}</p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
""",
    "About.jsx": r"""import React from 'react';
import { Link } from 'react-router-dom';

const STATS = [
  ['99.9%', 'Uptime target'],
  ['< 200ms', 'Median API latency'],
  ['24/7', 'Health monitoring'],
  ['100%', 'Data ownership'],
];

const VALUES = [
  ['Clarity over noise', 'Every screen answers one question and offers one obvious next step.'],
  ['Security is a feature', 'Least-privilege access, audited mutations and encrypted secrets are non-negotiable.'],
  ['Evidence over opinion', 'Performance budgets, test coverage and live checks decide when a release ships.'],
];

const TIMELINE = [
  ['Foundation', 'The platform starts with a typed API, migrations and a design system — not a blank page.'],
  ['Scale', 'Caching, background jobs and tenant isolation are introduced before they become urgent.'],
  ['Operate', 'Deployments are verified against the live URL, and every release leaves an audit trail.'],
];

export default function About() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <header className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[__COLOR__]">About __BRAND__</p>
        <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-white leading-tight">
          Software that earns trust in production
        </h1>
        <p className="mt-5 text-lg text-slate-400 leading-relaxed">
          __BRAND__ is built for teams who need a dependable platform rather than another prototype.
          We focus on the unglamorous parts — security, observability, migrations and release
          discipline — so your product can grow without rewrites.
        </p>
      </header>

      <section className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4">
        {STATS.map(([value, label]) => (
          <div key={label} className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <p className="text-2xl font-extrabold text-white">{value}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{label}</p>
          </div>
        ))}
      </section>

      <section className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
        {VALUES.map(([title, body]) => (
          <article key={title} className="p-7 rounded-3xl bg-slate-900/60 border border-slate-800">
            <h2 className="text-lg font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm text-slate-400 leading-relaxed">{body}</p>
          </article>
        ))}
      </section>

      <section className="mt-16">
        <h2 className="text-2xl font-extrabold text-white">How we build</h2>
        <ol className="mt-8 space-y-4">
          {TIMELINE.map(([title, body], index) => (
            <li key={title} className="flex gap-5 p-6 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="font-mono text-sm text-[__COLOR__]">{String(index + 1).padStart(2, '0')}</span>
              <div>
                <h3 className="text-base font-bold text-white">{title}</h3>
                <p className="mt-1 text-sm text-slate-400 leading-relaxed">{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-16 text-center">
        <Link to="/contact" className="inline-block px-8 py-3.5 rounded-full bg-[__COLOR__] text-white font-semibold hover:opacity-90 transition-opacity">
          Talk to our team
        </Link>
      </section>
    </div>
  );
}
""",
    "Contact.jsx": r"""import React, { useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const FIELD_CLASS = 'w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:border-[__COLOR__] focus:outline-none';

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState('idle');

  const validate = () => {
    const next = {};
    if (!form.name.trim()) next.name = 'Your name is required.';
    if (!EMAIL_RE.test(form.email.trim())) next.email = 'Enter a valid email address.';
    if (form.message.trim().length < 10) next.message = 'Tell us at least 10 characters.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!validate()) return;
    setStatus('sending');
    try {
      const res = await fetch(`${API}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          message: form.message.trim(),
        }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (json.errors) setErrors(json.errors);
        throw new Error(json.message || `Request failed (${res.status})`);
      }
      setStatus('sent');
      setForm({ name: '', email: '', message: '' });
    } catch (error) {
      setStatus('error');
      setErrors((prev) => ({ ...prev, form: error.message || 'Could not send the message.' }));
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 grid grid-cols-1 lg:grid-cols-2 gap-12">
      <section>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[__COLOR__]">Contact</p>
        <h1 className="mt-4 text-4xl font-extrabold text-white">Let's talk</h1>
        <p className="mt-4 text-slate-400 leading-relaxed">
          Tell us what you are building and we will reply within one business day with next steps,
          pricing guidance and a technical fit assessment.
        </p>
        <dl className="mt-10 space-y-6 text-sm">
          <div>
            <dt className="text-slate-500 uppercase tracking-wide text-xs">Email</dt>
            <dd className="mt-1 text-slate-200">hello@__SLUG__.com</dd>
          </div>
          <div>
            <dt className="text-slate-500 uppercase tracking-wide text-xs">Response time</dt>
            <dd className="mt-1 text-slate-200">Within one business day</dd>
          </div>
          <div>
            <dt className="text-slate-500 uppercase tracking-wide text-xs">Support hours</dt>
            <dd className="mt-1 text-slate-200">Monday – Friday, 09:00–18:00 UTC</dd>
          </div>
        </dl>
      </section>

      <section>
        {status === 'sent' ? (
          <div role="status" className="p-8 rounded-3xl bg-emerald-950/40 border border-emerald-800">
            <h2 className="text-xl font-bold text-emerald-200">Message received</h2>
            <p className="mt-2 text-sm text-emerald-300/80">Thanks — we will reply within one business day.</p>
            <button type="button" onClick={() => setStatus('idle')} className="mt-6 px-5 py-2.5 rounded-full bg-emerald-600 text-white text-sm font-semibold">
              Send another message
            </button>
          </div>
        ) : (
          <form onSubmit={submit} noValidate className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-5">
            <div>
              <label htmlFor="contact-name" className="block text-sm text-slate-400 mb-1.5">Your name</label>
              <input id="contact-name" type="text" autoComplete="name" required className={FIELD_CLASS}
                value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              {errors.name && <p role="alert" className="mt-1.5 text-xs text-rose-400">{errors.name}</p>}
            </div>
            <div>
              <label htmlFor="contact-email" className="block text-sm text-slate-400 mb-1.5">Email</label>
              <input id="contact-email" type="email" autoComplete="email" required className={FIELD_CLASS}
                value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              {errors.email && <p role="alert" className="mt-1.5 text-xs text-rose-400">{errors.email}</p>}
            </div>
            <div>
              <label htmlFor="contact-message" className="block text-sm text-slate-400 mb-1.5">How can we help?</label>
              <textarea id="contact-message" rows={5} required className={FIELD_CLASS}
                value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
              {errors.message && <p role="alert" className="mt-1.5 text-xs text-rose-400">{errors.message}</p>}
            </div>
            {errors.form && <p role="alert" className="text-sm text-rose-400">{errors.form}</p>}
            <button type="submit" disabled={status === 'sending'}
              className="w-full py-3.5 rounded-xl bg-[__COLOR__] text-white font-bold disabled:opacity-50 transition-opacity">
              {status === 'sending' ? 'Sending…' : 'Send message'}
            </button>
            <p className="text-xs text-slate-500">By submitting you agree to our privacy policy. We never share your details.</p>
          </form>
        )}
      </section>
    </div>
  );
}
""",
}


class FullStackUltraEngine:
    """Generates complete, clean, professional full-stack web applications at maximum velocity."""

    def __init__(self):
        self.unique_engine = HyperUniqueSiteEngine()
        self.repair_engine = OmniRepairEngine()

    def generate_project(
        self,
        destination_dir: str,
        prompt: str = "Enterprise AI Cloud Platform",
        brand_name: Optional[str] = None,
        industry: str = "saas",
        primary_color: Optional[str] = None,
        *,
        generation_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates a complete full-stack project in destination_dir concurrently."""
        start_time = time.perf_counter()
        contract = generation_contract or resolve_generation_contract({})
        if contract.get("layout_mode") != "enterprise":
            raise ValueError("FullStackUltraEngine currently supports enterprise full-stack delivery only")
        brand = brand_name or prompt.split()[0].capitalize()
        blueprint = self.unique_engine.synthesize_hyper_unique_blueprint(prompt, brand)
        color = primary_color or blueprint["palette"]["primary"]
        accent = blueprint["palette"]["accent"]
        palette = blueprint["palette"]

        dest = os.path.abspath(destination_dir)
        os.makedirs(dest, exist_ok=True)

        # Plan all files to write concurrently
        files_map: Dict[str, str] = {}

        # ── 1. Frontend Files ─────────────────────────────────────────────
        self._build_frontend_files(files_map, brand, color, accent, palette, industry)

        # ── 2. Backend Files ──────────────────────────────────────────────
        self._build_backend_files(files_map, brand)
        self._configure_postgresql_backend(files_map, brand)

        # ── 3. DevOps & Documentation Files ───────────────────────────────
        self._build_devops_files(files_map, brand, prompt)
        files_map["backend/migrations/001_create_core_tables.js"] = self._postgres_migration()
        files_map["backend/package.json"] = self._fullstack_backend_package(files_map["backend/package.json"])
        files_map["backend/routes/contact.routes.js"] = _CONTACT_ROUTE_JS
        files_map["backend/migrations/003_create_contact_messages.js"] = _CONTACT_MIGRATION_JS
        files_map["backend/.env.example"] = _BACKEND_ENV_EXAMPLE
        files_map["frontend/.gitignore"] = "node_modules/\ndist/\n.env*\n"
        files_map["backend/.gitignore"] = "node_modules/\n.env*\n*.log\n"
        files_map["backend/test/smoke.test.js"] = _BACKEND_SMOKE_TEST_JS
        files_map["LICENSE.md"] = self._generated_license(brand)

        # ── Concurrent Parallel File Writing ──────────────────────────────
        write_errors = []
        def _write_single_file(rel_path: str, content: str):
            full_path = os.path.join(dest, rel_path)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fh:
                    fh.write(content)
            except Exception as exc:
                write_errors.append(f"{rel_path}: {exc}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_write_single_file, rel_p, content) for rel_p, content in files_map.items()]
            concurrent.futures.wait(futures)

        # ── AI Micro-SaaS Kit (Category-1): keyVault, aiClient, SSE stream,
        #    prompt engine, RAG, file routes — every generated project ships it
        try:
            from agent.ai_saas_kit import inject_ai_saas_kit

            kit = inject_ai_saas_kit(dest)
            files_map.update({rel: "" for rel in kit.get("written", [])})
        except Exception as kit_exc:
            agent_logger.warning(f"AI SaaS kit injection skipped: {kit_exc}")

        # ── Production Spec: multi-stage Docker, INSTRUCTIONS.md, TS-ready
        #    types, validation middleware, live CRUD records, real dashboard
        try:
            from agent.production_spec_kit import apply_production_spec

            apply_production_spec(dest, brand=brand_name or brand)
        except Exception as spec_exc:
            agent_logger.warning(f"Production spec kit skipped: {spec_exc}")

        # DDL mirror for the deployment-readiness gate and DBAs (the runtime
        # path is the Umzug migrations above; this file must stay in sync).
        try:
            self._write_database_schema(dest)
        except Exception as schema_exc:
            agent_logger.warning(f"database/schema.sql skipped: {schema_exc}")

        # ── Self-Healing Omni-Repair Pass ─────────────────────────────────
        repair_report = self.repair_engine.scan_and_repair_project(dest)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        agent_logger.info(
            f"FullStackUltraEngine: Generated {len(files_map)} full-stack files in {elapsed_ms}ms"
        )

        return {
            "success": len(write_errors) == 0,
            "brand": brand,
            "industry": industry,
            "destination": dest,
            "total_files": len(files_map),
            "elapsed_ms": elapsed_ms,
            "errors": write_errors,
            "palette": palette,
            "omni_repairs": repair_report.get("repairs_applied", 0),
            "stack": {
                "frontend": "React 19 + Vite + Tailwind CSS + Lucide Icons + Framer Motion",
                "backend": "Express.js + Sequelize + JWT + bcrypt + Helmet + CORS",
                "database": "PostgreSQL",
                "devops": "Docker + docker-compose + Nginx reverse proxy",
            },
        }

    @staticmethod
    def _fullstack_backend_package(package_text: str) -> str:
        package = json.loads(package_text)
        package.setdefault("scripts", {}).update({"db:migrate": "node migrations/run.js", "test": "node --test"})
        dependencies = package.setdefault("dependencies", {})
        dependencies.pop("sqlite3", None)
        dependencies["pg"] = "^8.13.1"
        dependencies["pg-hstore"] = "^2.3.4"
        return json.dumps(package, indent=2)

    @staticmethod
    def _configure_postgresql_backend(files_map: Dict[str, str], brand: str) -> None:
        files_map["backend/models/index.js"] = """const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || 'lumicore_app',
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  logging: false,
});

const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
}, { tableName: 'users', underscored: true });

module.exports = { sequelize, User };
"""

    @staticmethod
    def _postgres_migration() -> str:
        return """const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('users', {
      id: { type: DataTypes.UUID, primaryKey: true },
      name: { type: DataTypes.STRING, allowNull: false },
      email: { type: DataTypes.STRING, allowNull: false, unique: true },
      password: { type: DataTypes.STRING, allowNull: false },
      role: { type: DataTypes.STRING, allowNull: false, defaultValue: 'user' },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('users');
  },
};
"""

    @staticmethod
    def _generated_license(brand: str) -> str:
        return (
            f"# {brand} License\n\n"
            "Commercial use and modification are permitted for the purchaser and their clients. "
            "Redistribution as a competing template is not permitted.\n"
        )

    def _build_frontend_files(self, fmap: Dict[str, str], brand: str, color: str, accent: str, palette: Dict[str, str], industry: str):
        # package.json
        fmap["frontend/package.json"] = json.dumps({
            "name": f"{brand.lower()}-frontend",
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "react-router-dom": "^6.28.0",
                "lucide-react": "^1.31.0",
                "framer-motion": "^11.18.2",
                "clsx": "^2.1.1",
                "tailwind-merge": "^2.6.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.4",
                "vite": "^6.0.0",
                "tailwindcss": "^3.4.17",
                "postcss": "^8.4.49",
                "autoprefixer": "^10.4.20"
            }
        }, indent=2)

        # vite.config.js
        fmap["frontend/vite.config.js"] = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: true },
});
"""

        # tailwind.config.js
        fmap["frontend/tailwind.config.js"] = f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  content: ["./index.html", "./src/**/*.{{js,ts,jsx,tsx}}"],
  darkMode: "class",
  theme: {{
    extend: {{
      colors: {{
        brand: {{
          primary: "{color}",
          accent: "{accent}",
          surface: "{palette.get('surface', '#1e293b')}",
          background: "{palette.get('background', '#0f172a')}",
        }},
      }},
    }},
  }},
  plugins: [],
}};
"""

        # index.html
        fmap["frontend/index.html"] = f"""<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{brand} — Professional Global Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body class="bg-slate-950 text-slate-50 antialiased selection:bg-brand-primary selection:text-white">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

        # src/index.css
        fmap["frontend/src/index.css"] = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
"""

        # src/main.jsx
        fmap["frontend/src/main.jsx"] = """import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
"""

        # src/App.jsx
        fmap["frontend/src/App.jsx"] = f"""import React from 'react';
import {{ Routes, Route }} from 'react-router-dom';
import GlassNavbar from './components/common/GlassNavbar.jsx';
import ModernFooter from './components/common/ModernFooter.jsx';
import Home from './pages/Home.jsx';
import Features from './pages/Features.jsx';
import Pricing from './pages/Pricing.jsx';
import About from './pages/About.jsx';
import Contact from './pages/Contact.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';

export default function App() {{
  const isAuthRoute = /^\\/(?:login|register|forgot-password|reset-password(?:\\/|$)|verify-email(?:\\/|$))\\/?$/.test(window.location.pathname);
  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">
      {{!isAuthRoute && <GlassNavbar brand="{brand}" />}}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={{<Home />}} />
          <Route path="/features" element={{<Features />}} />
          <Route path="/pricing" element={{<Pricing />}} />
          <Route path="/about" element={{<About />}} />
          <Route path="/contact" element={{<Contact />}} />
          <Route path="/login" element={{<Login />}} />
          <Route path="/register" element={{<Register />}} />
          <Route path="/dashboard" element={{<Dashboard />}} />
        </Routes>
      </main>
      {{!isAuthRoute && <ModernFooter brand="{brand}" />}}
    </div>
  );
}}
"""

        # src/components/common/UniqueLogo.jsx
        fmap["frontend/src/components/common/UniqueLogo.jsx"] = f"""import React from 'react';

export default function UniqueLogo({{ size = "w-8 h-8", className = "" }}) {{
  return (
    <div className={{`inline-flex items-center justify-center ${{size}} ${{className}}`}}>
      <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="{color}" />
            <stop offset="100%" stopColor="{accent}" />
          </linearGradient>
        </defs>
        <polygon points="24,4 40,14 40,34 24,44 8,34 8,14" fill="none" stroke="url(#logoGrad)" strokeWidth="3" />
        <circle cx="24" cy="24" r="5" fill="{accent}" />
        <line x1="24" y1="4" x2="24" y2="19" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="40" y1="34" x2="27" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="8" y1="34" x2="21" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
      </svg>
    </div>
  );
}}
"""

        # src/components/common/GlassNavbar.jsx
        fmap["frontend/src/components/common/GlassNavbar.jsx"] = f"""import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Menu, X, Globe, DollarSign, ArrowRight }} from 'lucide-react';
import UniqueLogo from './UniqueLogo.jsx';

export default function GlassNavbar({{ brand = "{brand}" }}) {{
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currency, setCurrency] = useState('USD');

  const navLinks = [
    {{ name: 'Features', path: '/features' }},
    {{ name: 'Pricing', path: '/pricing' }},
    {{ name: 'About', path: '/about' }},
    {{ name: 'Contact', path: '/contact' }},
  ];

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/70 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <UniqueLogo size="w-9 h-9" />
          <span className="text-xl font-extrabold tracking-tight text-white group-hover:text-cyan-400 transition-colors">
            {brand}
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {{navLinks.map((item) => (
            <Link
              key={{item.name}}
              to={{item.path}}
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              {{item.name}}
            </Link>
          ))}}
        </nav>

        <div className="hidden md:flex items-center gap-4">
          <div className="flex items-center gap-1 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded-full">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={{currency}}
              onChange={{(e) => setCurrency(e.target.value)}}
              className="bg-transparent text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="USD" className="bg-slate-900">USD ($)</option>
              <option value="EUR" className="bg-slate-900">EUR (€)</option>
              <option value="GBP" className="bg-slate-900">GBP (£)</option>
              <option value="PKR" className="bg-slate-900">PKR (₨)</option>
            </select>
          </div>

          <Link
            to="/login"
            className="text-sm font-medium text-slate-300 hover:text-white px-3 py-2"
          >
            Sign in
          </Link>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-[{color}] to-cyan-500 hover:opacity-95 shadow-lg shadow-[{color}]/20 transition-all"
          >
            Get Started <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <button
          onClick={{() => setMobileOpen(!mobileOpen)}}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          {{mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}}
        </button>
      </div>

      {{mobileOpen && (
        <div className="md:hidden px-4 pt-2 pb-6 bg-slate-950 border-b border-slate-800 space-y-3">
          {{navLinks.map((item) => (
            <Link
              key={{item.name}}
              to={{item.path}}
              onClick={{() => setMobileOpen(false)}}
              className="block text-base font-medium text-slate-300 hover:text-white py-2"
            >
              {{item.name}}
            </Link>
          ))}}
          <div className="pt-4 border-t border-slate-800 flex flex-col gap-3">
            <Link to="/login" className="text-center py-2 text-slate-300">Sign in</Link>
            <Link to="/register" className="text-center py-2.5 rounded-full bg-[{color}] text-white font-semibold">Get Started</Link>
          </div>
        </div>
      )}}
    </header>
  );
}}
"""

        # src/components/common/ModernFooter.jsx
        fmap["frontend/src/components/common/ModernFooter.jsx"] = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ShieldCheck, Heart }} from 'lucide-react';
import UniqueLogo from './UniqueLogo.jsx';

export default function ModernFooter({{ brand = "{brand}" }}) {{
  return (
    <footer className="bg-slate-950 border-t border-slate-900 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <UniqueLogo size="w-8 h-8" />
              <span className="text-xl font-extrabold text-white">{brand}</span>
            </div>
            <p className="text-slate-400 text-sm max-w-sm mb-6 leading-relaxed">
              Precision-engineered digital infrastructure delivering sub-millisecond experiences for global scale.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Systems Operational
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Product</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><Link to="/features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/features" className="hover:text-white transition-colors">Enterprise</Link></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Console</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Company</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><Link to="/about" className="hover:text-white transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Careers</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">Press</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Legal</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Security Posture</a></li>
              <li><a href="#" className="hover:text-white transition-colors">GDPR Compliance</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 {brand} Inc. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-slate-400" /> ISO 27001 Certified</span>
            <span>Built with precision engineering</span>
          </div>
        </div>
      </div>
    </footer>
  );
}}
"""

        # src/pages/Home.jsx
        fmap["frontend/src/pages/Home.jsx"] = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight, CheckCircle2, Zap, Shield, Globe, Cpu, BarChart3 }} from 'lucide-react';

export default function Home() {{
  return (
    <div className="space-y-24 py-12">
      {{/* Hero Section */}}
      <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center pt-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[{color}]/10 text-[{color}] border border-[{color}]/30 mb-8">
          <Zap className="w-3.5 h-3.5" /> Next-Generation Global Architecture
        </div>
        <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
          Supercharge your business with <span className="bg-clip-text text-transparent bg-gradient-to-r from-[{color}] via-cyan-400 to-indigo-400">{brand}</span>
        </h1>
        <p className="mt-6 text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
          The all-in-one international platform engineered for lightning speed, unmatched resilience, and global scale.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="w-full sm:w-auto px-8 py-4 rounded-full text-base font-bold text-white bg-gradient-to-r from-[{color}] to-cyan-500 shadow-xl shadow-[{color}]/25 hover:opacity-95 transition-all flex items-center justify-center gap-2"
          >
            Start Free Trial <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            to="/features"
            className="w-full sm:w-auto px-8 py-4 rounded-full text-base font-semibold text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors"
          >
            Explore Platform
          </Link>
        </div>
      </section>

      {{/* Bento Grid Section */}}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Built for High-Growth Scale</h2>
          <p className="mt-4 text-slate-400">Everything needed to power modern enterprise operations.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-[{color}]/40 transition-colors">
            <Cpu className="w-10 h-10 text-[{color}] mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Automated Execution</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Sub-second execution pipelines that scale autonomously based on load.</p>
          </div>
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-[{color}]/40 transition-colors">
            <Shield className="w-10 h-10 text-[{color}] mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Enterprise Security</h3>
            <p className="text-slate-400 text-sm leading-relaxed">End-to-end encryption, automated compliance audit logs, and zero-trust perimeter.</p>
          </div>
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-[{color}]/40 transition-colors">
            <Globe className="w-10 h-10 text-[{color}] mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Global CDN Mesh</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Global multi-region replication with automatic failover and sub-15ms edge routing.</p>
          </div>
        </div>
      </section>
    </div>
  );
}}
"""

        # Remaining Pages: Features, Pricing, About, Contact, Login, Register, Dashboard
        pages = {
            "Features.jsx": f"""import React from 'react';
export default function Features() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">Features & Capabilities</h1>
      <p className="text-slate-300 text-lg">Comprehensive tools built for performance, reliability, and precision.</p>
    </div>
  );
}}""",
            "Pricing.jsx": f"""import React from 'react';
export default function Pricing() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-20 text-center">
      <h1 className="text-4xl font-extrabold text-white mb-4">Transparent Pricing</h1>
      <p className="text-slate-300 mb-12">Choose the plan that fits your growth.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-left">
          <h3 className="text-xl font-bold text-white">Starter</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$29<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900 border-2 border-[{color}] text-left">
          <h3 className="text-xl font-bold text-white">Pro</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$79<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-left">
          <h3 className="text-xl font-bold text-white">Enterprise</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$199<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
      </div>
    </div>
  );
}}""",
            "About.jsx": f"""import React from 'react';
export default function About() {{
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">About {brand}</h1>
      <p className="text-slate-300 leading-relaxed">Engineered by a global team dedicated to building top-tier software architecture.</p>
    </div>
  );
}}""",
            "Contact.jsx": f"""import React from 'react';
export default function Contact() {{
  return (
    <div className="max-w-xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">Get in Touch</h1>
      <form className="space-y-4">
        <input type="text" placeholder="Name" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white" />
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white" />
        <textarea rows={{4}} placeholder="Message" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white"></textarea>
        <button type="submit" className="w-full py-3.5 rounded-xl bg-[{color}] text-white font-bold">Send Message</button>
      </form>
    </div>
  );
}}""",
            "Login.jsx": f"""import React from 'react';
export default function Login() {{
  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Sign in to {brand}</h2>
      <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="password" placeholder="Password" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <button className="w-full py-3.5 rounded-xl bg-[{color}] text-white font-bold">Sign In</button>
      </div>
    </div>
  );
}}""",
            "Register.jsx": f"""import React from 'react';
export default function Register() {{
  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Create Your Account</h2>
      <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <input type="text" placeholder="Full Name" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="password" placeholder="Password" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <button className="w-full py-3.5 rounded-xl bg-[{color}] text-white font-bold">Get Started</button>
      </div>
    </div>
  );
}}""",
            "Dashboard.jsx": f"""import React from 'react';
export default function Dashboard() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white mb-8">Control Console</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Total Requests</p>
          <p className="text-2xl font-bold text-white mt-1">1,420,890</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Average Latency</p>
          <p className="text-2xl font-bold text-white mt-1">12.4ms</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Uptime</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">99.99%</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Active Nodes</p>
          <p className="text-2xl font-bold text-white mt-1">48 / 48</p>
        </div>
      </div>
    </div>
  );
}}""",
        }
        for pname, pcontent in pages.items():
            fmap[f"frontend/src/pages/{pname}"] = pcontent

        # Replace the one-line placeholders with real, brand-aware marketing
        # pages. A buyer-facing site cannot ship a page that says only
        # "Comprehensive tools built for performance".
        slug = "".join(ch for ch in brand.lower().replace(" ", "-") if ch.isalnum() or ch == "-")
        for pname, template in _MARKETING_PAGES.items():
            fmap[f"frontend/src/pages/{pname}"] = (
                template.replace("__BRAND__", brand)
                .replace("__COLOR__", color)
                .replace("__SLUG__", slug or "example")
            )

    def _write_database_schema(self, dest: str) -> None:
        """Write database/schema.sql as the DDL mirror of the migrations.

        The deployment-readiness gate requires it, and an operator restoring a
        database needs one file that reproduces the models. Column casing is
        significant: `users`/`contact_messages` use underscored timestamps,
        `records` keeps Sequelize's camelCase defaults (matching the models).
        """
        schema = """-- Generated schema mirror. Runtime authority: backend/migrations/*.js
-- Apply with: psql "$DATABASE_URL" -f database/schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(160) NOT NULL,
  body TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  "userId" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  "createdAt" TIMESTAMPTZ NOT NULL DEFAULT now(),
  "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_records_user ON records ("userId");

CREATE TABLE IF NOT EXISTS contact_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created ON contact_messages (created_at DESC);
"""
        schema_path = Path(dest) / "database"
        schema_path.mkdir(parents=True, exist_ok=True)
        (schema_path / "schema.sql").write_text(schema, encoding="utf-8")

    def _build_backend_files(self, fmap: Dict[str, str], brand: str):
        # backend/package.json
        fmap["backend/package.json"] = json.dumps({
            "name": f"{brand.lower()}-backend",
            "version": "1.0.0",
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js",
                "db:migrate": "node migrations/run.js",
                "test": "node --test"
            },
            "dependencies": {
                "express": "^4.21.2",
                "cors": "^2.8.5",
                "helmet": "^8.0.0",
                "dotenv": "^16.4.7",
                "jsonwebtoken": "^9.0.2",
                "bcryptjs": "^2.4.3",
                "sequelize": "^6.37.5",
                "pg": "^8.13.1",
                "pg-hstore": "^2.3.4",
                "express-rate-limit": "^7.5.0",
                "compression": "^1.7.5"
            }
        }, indent=2)

        # backend/server.js
        fmap["backend/server.js"] = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const authRoutes = require('./routes/auth.routes');
const healthRoutes = require('./routes/health.routes');
const {{ sequelize }} = require('./models');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(helmet());
app.use(cors({{ origin: '*' }}));
app.use(compression());
app.use(express.json());

const limiter = rateLimit({{
  windowMs: 15 * 60 * 1000,
  max: 200,
}});
app.use(limiter);

app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/health', healthRoutes);

sequelize.sync().then(() => {{
  app.listen(PORT, () => {{
    console.log(`{brand} Backend API running on port ${{PORT}}`);
  }});
}}).catch(err => {{
  console.error('Database connection failed:', err);
}});

module.exports = app;
"""

        # backend/models/index.js
        fmap["backend/models/index.js"] = """const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || 'lumicore_app',
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  logging: false,
});

const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
}, { tableName: 'users', underscored: true });

module.exports = { sequelize, User };
"""

        # backend/utils/jwtSecret.js -- fail-closed JWT secret resolution.
        # Plain (non-f) Python string literal: JS braces/$, backticks and
        # newlines below are emitted verbatim, so no brace doubling is needed.
        fmap["backend/utils/jwtSecret.js"] = """/**
 * Fail-closed JWT secret resolution.
 *
 * Refuses to boot when JWT_SECRET is missing, shorter than MIN_LENGTH, or a
 * well-known placeholder, so a publicly known value can never be used to forge
 * tokens (including admin tokens).
 *
 * Generate a secret with:
 *   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
 *   # or: openssl rand -hex 32
 */
const DENIED_SECRETS = [
  'secret',
  'changeme',
  'change_me',
  'change-me-in-production',
  'change_this_secret_in_production',
  'change_this_to_a_random_64_char_string',
  'lumi_jwt_secret',
  'replace-me',
  'replace_with_a_random_64_character_secret',
  'replace_with_secure_random_key',
  'secret_jwt_key',
  'secret_jwt_key_2026',
  'super_secret_production_key_2026',
  'your_jwt_secret_key_here',
  'your_super_secret_key_here_change_this',
  'your-super-secret-jwt-key-change-this',
  'your_super_secret_jwt_key_change_this_minimum_32_characters',
];

const MIN_LENGTH = 32;

function fail(reason) {
  console.error(`[fatal] JWT_SECRET ${reason}. Refusing to start.
Generate a strong secret with one of:
  node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
  # or: openssl rand -hex 32
Then set JWT_SECRET in your .env file.`);
  process.exit(1);
}

function resolveJwtSecret(env) {
  const source = env || process.env;
  const raw = source.JWT_SECRET;
  if (typeof raw !== 'string' || raw.trim() === '') fail('is not set');
  const secret = raw.trim();
  if (secret.length < MIN_LENGTH) {
    fail(`must be at least ${MIN_LENGTH} characters (got ${secret.length})`);
  }
  if (DENIED_SECRETS.indexOf(secret.toLowerCase()) !== -1) {
    fail('is a well-known placeholder value');
  }
  return secret;
}

const jwtSecret = Object.freeze(resolveJwtSecret(process.env));

module.exports = { jwtSecret, MIN_LENGTH };
"""

        # backend/routes/auth.routes.js
        fmap["backend/routes/auth.routes.js"] = """const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { User } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');

const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { name, email, password } = req.body;
    if (!name || !email || !password) return res.status(400).json({ error: 'Missing fields' });

    const hashedPassword = await bcrypt.hash(password, 12);
    const user = await User.create({ name, email, password: hashedPassword });
    const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });

    return res.status(201).json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err) {
    if (err.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ success: false, code: 'EMAIL_TAKEN', message: 'Email already registered' });
    }
    return res.status(500).json({ success: false, message: 'Registration failed' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ where: { email } });
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });
    return res.json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Login failed' });
  }
});

module.exports = router;
"""

        # backend/routes/health.routes.js
        fmap["backend/routes/health.routes.js"] = """const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

module.exports = router;
"""

    def _build_devops_files(self, fmap: Dict[str, str], brand: str, prompt: str):
        fmap["docker-compose.yml"] = f"""version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: lumicore_app
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-postgres}}"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=lumicore_app
      - DB_USER=${{POSTGRES_USER:-postgres}}
      - DB_PASSWORD=${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
      - JWT_SECRET=${{JWT_SECRET:?JWT_SECRET is required - see backend/.env.example}}

volumes:
  postgres_data:
"""

        fmap["backend/migrations/run.js"] = """const { Umzug, SequelizeStorage } = require('umzug');
const { sequelize } = require('../models');

const umzug = new Umzug({
  migrations: { glob: 'migrations/00*.js' },
  context: sequelize.getQueryInterface(),
  storage: new SequelizeStorage({ sequelize }),
  logger: console,
});

module.exports = umzug;
if (require.main === module) {
  umzug.up().then(() => sequelize.close()).catch((error) => {
    console.error('Migration failed:', error.message);
    process.exitCode = 1;
  });
}
"""
        fmap["backend/package.json"] = json.dumps({
            **json.loads(fmap["backend/package.json"]),
            "dependencies": {**json.loads(fmap["backend/package.json"])["dependencies"], "umzug": "^3.8.2"},
        }, indent=2)
        fmap["backend/migrations/001_create_core_tables.js"] = """const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('users', {
      id: { type: DataTypes.UUID, primaryKey: true },
      name: { type: DataTypes.STRING, allowNull: false },
      email: { type: DataTypes.STRING, allowNull: false, unique: true },
      password: { type: DataTypes.STRING, allowNull: false },
      role: { type: DataTypes.STRING, allowNull: false, defaultValue: 'user' },
      createdAt: { type: DataTypes.DATE, allowNull: false },
      updatedAt: { type: DataTypes.DATE, allowNull: false },
    });
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('users');
  },
};
"""

        fmap[".env.example"] = f"""PORT=5000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lumicore_app
DB_USER=postgres
POSTGRES_PASSWORD=
DB_PASSWORD=
# REQUIRED, minimum 32 chars. Generate one with:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
#   # or: openssl rand -hex 32
# The backend refuses to start if this is missing, short, or a known placeholder.
JWT_SECRET=
NODE_ENV=production
"""
        fmap["frontend/.env.example"] = "VITE_API_URL=http://localhost:5000/api/v1\n"

        fmap["README.md"] = f"""# {brand} — Full-Stack Application

Generated autonomously by **LumicorePro AI Agent**.

## Features
- **Database**: PostgreSQL with versioned Sequelize migrations.
- **Frontend**: React 19, Tailwind CSS, Lucide Icons, GlassNavbar, BentoGrid, ModernFooter.
- **Backend**: Express.js REST API, Sequelize ORM, JWT Authentication, Helmet security headers.
- **Infrastructure**: Docker containerization & production reverse-proxy support.

## Getting Started

### 1. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 2. Backend
```bash
cd backend
npm install
npm run dev
```

### 3. Docker Deploy
```bash
cp .env.example .env  # set POSTGRES_PASSWORD and JWT_SECRET first
docker compose up --build
```
"""
