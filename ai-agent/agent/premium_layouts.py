"""Pure public React emitter for the existing full-stack generator file map.

Composition/tokens belong to design_forge. Auth, records and backend behavior
remain owned by production_spec_kit; this module never replaces those files.
"""
from __future__ import annotations

import json
import re
from typing import Any


def route_expectations(brand: str) -> dict[str, dict[str, str]]:
    """Independent visible-main headings for the generated public QA manifest."""
    return {
        "/": {"heading": brand},
        "/features": {"heading": "What you can do"},
        "/pricing": {"heading": "Choose your next step"},
        "/about": {"heading": "Built for your work"},
        "/contact": {"heading": "Let's talk"},
        "/login": {"heading": "Sign in"},
        "/register": {"heading": "Create your account"},
    }


def _js(value: str) -> str:
    # JSON is data, never JSX. Escape HTML delimiters and JS line separators too.
    return (json.dumps(value, ensure_ascii=True).replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("&", "\\u0026"))


def _bind(template: str, **values: str) -> str:
    # Single pass: owner content containing another token cannot be substituted.
    return re.sub(r"@@([A-Z_]+)@@", lambda match: values[match[1]], template)


_ACTIONS = """<div className="action-row">
  <Link className="public-button" to="/register">Create your account <span aria-hidden="true">&rarr;</span></Link>
  <Link className="public-button secondary" to="/features">Explore features</Link>
</div>"""

_INTRO = """<p className="eyebrow">{CONTEXT}</p>
<h1 className="hero-brand">{BRAND}</h1>
<p className="hero-statement">A clear place for the work that matters.</p>
<p className="hero-description">Keep your records together. Add the details, make changes,
  and return to your work with a personal account.</p>"""

_ART = """<figure className="hero-art">
  <p className="eyebrow">From first note to next step</p>
  <img src={`${import.meta.env.BASE_URL}assets/workflow.svg`} width="640" height="480"
    alt="Illustration of connected record sheets, from an initial note to an organized collection" />
  <figcaption>Workflow illustration &mdash; create a record, add context, and update it as your work develops.</figcaption>
</figure>"""

_HEROES = {
    "split-asymmetric": '<header className="hero-split"><div>' + _INTRO + _ACTIONS + '</div>' + _ART + '</header>',
    "divided-reading": '<header className="hero-editorial"><div>' + _INTRO + _ACTIONS + """</div>
  <aside className="editorial-note" aria-label="A considered starting point">
    <p className="eyebrow">A considered starting point</p>
    <h2>Less searching.<br />More perspective.</h2>
    <p>A title for the essentials. A description for the context. A workspace you can return to.</p>
    <Link className="text-link" to="/about">Read our approach</Link>
  </aside>
</header>""",
    "stacked-stepped": '<header className="hero-kinetic">' + _INTRO + _ACTIONS + """
  <ol className="kinetic-strip" aria-label="Your starting sequence">
    <li><span>01</span>Create an account</li>
    <li><span>02</span>Capture a record</li>
    <li><span>03</span>Make your next edit</li>
  </ol>
</header>""",
    "compact-columns": '<header className="hero-precision"><div>' + _INTRO + _ACTIONS + """</div>
  <dl className="precision-details" aria-label="Workspace essentials">
    <div><dt>Access</dt><dd>A personal account and sign-in</dd></div>
    <div><dt>Records</dt><dd>Titles, descriptions, and saved changes</dd></div>
    <div><dt>Next step</dt><dd><Link className="text-link" to="/register">Open registration</Link></dd></div>
  </dl>
</header>""",
}

_CAPABILITIES = """<section id="capabilities" className="public-section" aria-labelledby="capabilities-title">
  <div className="section-heading">
    <h2 id="capabilities-title">Room for the details.<br />Clarity for the next step.</h2>
    <p>Start with the essentials already in your workspace.</p>
  </div>
  <div className="@@CAPABILITY_CLASS@@">
    <article className="capability-card">
      <p className="eyebrow">Your workspace</p><h3>Pick up where you left off</h3>
      <p>Sign in to reach your dashboard and the records available to your account.</p>
      <Link className="text-link" to="/login">Sign in to your workspace</Link>
    </article>
    <article className="capability-card">
      <p className="eyebrow">Your records</p><h3>Give your work context</h3>
      <p>Create records with a title and description. Edit the details or remove records you no longer need.</p>
    </article>
    <article className="capability-card">
      <p className="eyebrow">Your next step</p><h3>Ask a specific question</h3>
      <p>Use the contact form to share your needs before deciding how to proceed.</p>
      <Link className="text-link" to="/contact">Start a conversation</Link>
    </article>
  </div>
</section>"""

_WORKFLOW = """<section id="workflow" className="public-section" aria-labelledby="workflow-title">
  <div className="section-heading"><h2 id="workflow-title">A straightforward way to begin</h2>
    <p>No elaborate setup story. Just the steps you can take here.</p></div>
  <ol className="workflow-list @@WORKFLOW_CLASS@@">
    <li><span className="workflow-number" aria-hidden="true">01</span><div>
      <h3>Create your account</h3><p>Register with your name, email, and password.</p></div></li>
    <li><span className="workflow-number" aria-hidden="true">02</span><div>
      <h3>Make your first record</h3><p>Open the dashboard and add a title and description.</p></div></li>
    <li><span className="workflow-number" aria-hidden="true">03</span><div>
      <h3>Return and refine</h3><p>Review what you saved, update the details, or remove what is no longer relevant.</p></div></li>
  </ol>
</section>"""

_PRINCIPLES = """<section id="principles" className="public-section" aria-labelledby="principles-title">
  <div className="principles-reading"><p className="eyebrow">A little more intention</p>
    <h2 id="principles-title">The work comes first.</h2>
    <p>Useful software gives the details a place to live. {BRAND} brings account access,
      record editing, and a way to get in touch into one focused experience.</p>
    <Link className="text-link" to="/about">Get to know the approach</Link>
  </div>
</section>"""

_CLOSING = """<section className="closing-note" aria-label="Next steps">
  <div><h2>Make room for your next idea.</h2><p>Explore the workspace or tell us what you need.</p></div>
  <div className="action-row"><Link className="public-button" to="/register">Create your account</Link>
    <Link className="public-button secondary" to="/contact">Contact us</Link></div>
</section>"""

_APP = r"""import React, { lazy, Suspense, useEffect, useRef } from 'react';
import { Link, Routes, Route, useLocation } from 'react-router-dom';
import GlassNavbar from './components/common/GlassNavbar.jsx';
import ModernFooter from './components/common/ModernFooter.jsx';

const Home = lazy(() => import('./pages/Home.jsx'));
const Features = lazy(() => import('./pages/Features.jsx'));
const Pricing = lazy(() => import('./pages/Pricing.jsx'));
const About = lazy(() => import('./pages/About.jsx'));
const Contact = lazy(() => import('./pages/Contact.jsx'));
const Login = lazy(() => import('./pages/Login.jsx'));
const Register = lazy(() => import('./pages/Register.jsx'));
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));

export default function App() {
  const location = useLocation();
  const mainRef = useRef(null);
  const previousPath = useRef(location.pathname);
  const isAuthRoute = /^\/(?:login|register|forgot-password|reset-password|verify-email)(?:\/|$)/.test(location.pathname);
  useEffect(() => {
    if (previousPath.current !== location.pathname) {
      window.scrollTo({ top: 0, behavior: 'instant' });
      mainRef.current?.focus();
      previousPath.current = location.pathname;
    }
  }, [location.pathname]);

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      {!isAuthRoute && <GlassNavbar />}
      {isAuthRoute && <div className="public-container"><Link className="text-link nav-signin" to="/">Back to home</Link></div>}
      <main id="main-content" tabIndex={-1} ref={mainRef}>
        <Suspense fallback={<p className="route-loading" role="status">Loading page&hellip;</p>}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/features" element={<Features />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<div className="public-container public-page">
              <h1>Page not found</h1><Link className="text-link" to="/">Return home</Link>
            </div>} />
          </Routes>
        </Suspense>
      </main>
      {!isAuthRoute && <ModernFooter />}
    </div>
  );
}
"""

_NAV = """import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';

const BRAND = @@BRAND@@;
const LINKS = [['Features', '/features'], ['Pricing', '/pricing'], ['About', '/about'], ['Contact', '/contact']];

export default function GlassNavbar({ brand = BRAND }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const toggleRef = useRef(null);
  const location = useLocation();
  useEffect(() => { setMobileOpen(false); }, [location]);
  useEffect(() => {
    if (!mobileOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setMobileOpen(false);
        toggleRef.current?.focus();
      }
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [mobileOpen]);

  return (
    <header className="public-header">
      <div className="public-container nav-row">
        <Link className="brand-link" to="/" onClick={() => setMobileOpen(false)}>
          <svg className="brand-mark" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <path d="M16 2 30 16 16 30 2 16Z" stroke="currentColor" strokeWidth="2" />
            <path d="M10 21V11h5l7 10V11" stroke="currentColor" strokeWidth="2" />
          </svg><span>{brand}</span>
        </Link>
        <button className="menu-toggle" ref={toggleRef} type="button"
          aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={mobileOpen} aria-controls="public-navigation"
          onClick={() => setMobileOpen((open) => !open)}>{mobileOpen ? 'Close' : 'Menu'}</button>
        <nav id="public-navigation" aria-label="Main navigation"
          className={`public-navigation${mobileOpen ? ' is-open' : ''}`}>
          <div className="nav-links">{LINKS.map(([label, path]) => (
            <NavLink key={path} to={path} onClick={() => setMobileOpen(false)}>{label}</NavLink>
          ))}</div>
          <div className="nav-actions">
            <Link className="nav-signin" to="/login" onClick={() => setMobileOpen(false)}>Sign in</Link>
            <Link className="public-button" to="/register" onClick={() => setMobileOpen(false)}>Create account</Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
"""

_FOOTER = """import React from 'react';
import { Link } from 'react-router-dom';
const BRAND = @@BRAND@@;

export default function ModernFooter({ brand = BRAND }) {
  return (
    <footer className="public-footer">
      <div className="public-container">
        <div className="footer-grid">
          <div><Link className="brand-link" to="/">{brand}</Link>
            <p>A focused place for your records, your context, and your next step.</p></div>
          <nav aria-label="Explore"><h2>Explore</h2><ul>
            <li><Link to="/features">Features</Link></li><li><Link to="/pricing">Your next step</Link></li>
            <li><Link to="/about">About</Link></li><li><Link to="/contact">Contact</Link></li>
          </ul></nav>
          <nav aria-label="Your workspace"><h2>Your workspace</h2><ul>
            <li><Link to="/register">Create an account</Link></li><li><Link to="/login">Sign in</Link></li>
            <li><Link to="/dashboard">Open dashboard</Link></li>
          </ul></nav>
        </div>
        <p className="footer-bottom">&copy; {new Date().getFullYear()} {brand}</p>
      </div>
    </footer>
  );
}
"""

_PRICING = """<header className="page-intro"><p className="eyebrow">Getting started</p>
  <h1>Choose your next step</h1>
  <p>Explore the workspace or discuss your requirements. Registration creates an account;
    it does not purchase a subscription.</p></header>
<div className="choice-grid">
  <section className="choice-card"><p className="eyebrow">Explore on your own</p>
    <h2>Start with an account</h2><p>Register to open your dashboard, create records, and edit their details.</p>
    <Link className="public-button" to="/register">Create your account</Link></section>
  <section className="choice-card"><p className="eyebrow">Talk it through</p>
    <h2>Discuss your requirements</h2><p>Tell us about your intended use and ask about scope and pricing.</p>
    <Link className="public-button secondary" to="/contact">Ask about pricing</Link></section>
</div>
<section className="public-faq" aria-labelledby="pricing-questions"><h2 id="pricing-questions">Before you begin</h2>
  <details><summary>Where are the plan prices?</summary>
    <p>Plan prices are not published here. Use the contact form to request pricing information.</p></details>
  <details><summary>What does registration do?</summary>
    <p>It creates your account and opens the workspace. You can then add and manage your records.</p></details>
  <details><summary>Can I ask about a specific workflow?</summary>
    <p>Yes. Describe what you need through the contact form. Capabilities beyond those described here need to be discussed.</p></details>
</section>"""

_ABOUT = """<header className="page-intro"><p className="eyebrow">About {BRAND}</p>
  <h1>Built for your work</h1><p>{CONTEXT}. A simpler starting point for keeping useful details together.</p></header>
<section className="principles-reading" aria-labelledby="approach-title"><h2 id="approach-title">Context deserves a place.</h2>
  <p>{BRAND} centers on a simple workflow: sign in, create a record, and return to refine it.
    Each record has a title and description, so the key detail stays with the bigger picture.</p>
  <p>Use the dashboard for your records and the contact form for questions about your needs.
    The features page describes what is available today.</p>
  <Link className="text-link" to="/features">See what you can do</Link></section>"""

_CONTACT = r"""import React, { useRef, useState } from 'react';

const API = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1').replace(/\/$/, '');
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const EMPTY = { name: '', email: '', message: '' };

export default function Contact() {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState('idle');
  const sending = useRef(false);
  const formRef = useRef(null);

  const submit = async (event) => {
    event.preventDefault();
    if (sending.current) return;
    const payload = { name: form.name.trim(), email: form.email.trim(), message: form.message.trim() };
    const next = {};
    if (!payload.name || payload.name.length > 120) next.name = 'Enter your name (up to 120 characters).';
    if (!EMAIL_RE.test(payload.email) || payload.email.length > 254) next.email = 'Enter a valid email address.';
    if (payload.message.length < 10 || payload.message.length > 5000) next.message = 'Write between 10 and 5000 characters.';
    setErrors(next);
    if (Object.keys(next).length) {
      formRef.current?.elements.namedItem(Object.keys(next)[0])?.focus();
      return;
    }
    sending.current = true;
    setStatus('sending');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const res = await fetch(`${API}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success !== true) {
        // Do not render arbitrary server messages or traces. Preserve field identity.
        const serverErrors = {};
        for (const field of ['name', 'email', 'message']) {
          if (json.errors?.[field]) serverErrors[field] = `Please check your ${field} and try again.`;
        }
        setErrors({ ...serverErrors, form: 'Your message was not accepted. Check the details and try again.' });
        setStatus('error');
        return;
      }
      setForm(EMPTY);
      setStatus('sent');
    } catch {
      setErrors({ form: 'We could not confirm receipt. Your message is still here; please try again.' });
      setStatus('error');
    } finally {
      clearTimeout(timer);
      sending.current = false;
    }
  };

  return (
    <div className="public-container public-page contact-grid">
      <header className="page-intro"><p className="eyebrow">Get in touch</p>
        <h1>Let's talk</h1><p>Share what you need, ask about pricing, or describe your intended workflow.</p>
        <p className="form-note">Include enough context to explain your question. Do not send passwords or sensitive account details.</p>
      </header>
      <section aria-label="Contact form">
        {status === 'sent' ? (
          <div className="contact-result" role="status"><h2>Message received</h2>
            <p>Your message has been saved. Thank you for sharing the details.</p>
            <button type="button" className="public-button" onClick={() => { setStatus('idle'); setErrors({}); }}>
              Send another message</button>
          </div>
        ) : (
          <form ref={formRef} onSubmit={submit} noValidate className="contact-form" aria-busy={status === 'sending'}>
            <div className="contact-field"><label htmlFor="contact-name">Your name</label>
              <input id="contact-name" name="name" type="text" autoComplete="name" required maxLength={120}
                value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })}
                aria-invalid={Boolean(errors.name)} aria-describedby={errors.name ? 'name-error' : undefined} />
              {errors.name && <p id="name-error" className="field-error" role="alert">{errors.name}</p>}
            </div>
            <div className="contact-field"><label htmlFor="contact-email">Email</label>
              <input id="contact-email" name="email" type="email" autoComplete="email" required maxLength={254}
                value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}
                aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? 'email-error' : undefined} />
              {errors.email && <p id="email-error" className="field-error" role="alert">{errors.email}</p>}
            </div>
            <div className="contact-field"><label htmlFor="contact-message">How can we help?</label>
              <textarea id="contact-message" name="message" rows={6} required minLength={10} maxLength={5000}
                value={form.message} onChange={(event) => setForm({ ...form, message: event.target.value })}
                aria-invalid={Boolean(errors.message)} aria-describedby={errors.message ? 'message-error' : 'message-hint'} />
              <p id="message-hint" className="form-note">Between 10 and 5000 characters.</p>
              {errors.message && <p id="message-error" className="field-error" role="alert">{errors.message}</p>}
            </div>
            {errors.form && <p className="form-error" role="alert">{errors.form}</p>}
            <button type="submit" className="public-button" disabled={status === 'sending'}>
              {status === 'sending' ? 'Sending…' : status === 'error' ? 'Try again' : 'Send message'}</button>
          </form>
        )}
      </section>
    </div>
  );
}
"""


def _page(name: str, body: str, brand: str, context: str, scene: bool = False) -> str:
    imports = "import React from 'react';\nimport { Link } from 'react-router-dom';\n"
    if scene:
        imports = imports.replace("import React", "import React, { lazy, Suspense }")
        imports += "const Modern3DScene = lazy(() => import('../components/motion/Modern3DScene.jsx'));\n"
    return (imports + f"const BRAND = {_js(brand)};\nconst CONTEXT = {_js(context)};\n\n"
            + f"export default function {name}() {{\n  return (\n"
            + '    <div className="public-container public-page">\n' + body
            + "\n    </div>\n  );\n}\n")


def _workflow_svg(design: dict[str, Any]) -> str:
    """Original static vector artwork: abstract record sheets, not fake live data."""
    # Only derived hex tokens are allowed into XML attributes.
    def color(key: str) -> str:
        value = design["slate"][key]
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Invalid illustration color token")
        return value

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" fill="none">
  <title>Connected record sheets</title>
  <desc>An original workflow illustration with layered sheets and connecting paths.</desc>
  <circle cx="330" cy="245" r="192" stroke="{color('700')}" />
  <circle cx="330" cy="245" r="136" stroke="{color('700')}" stroke-dasharray="4 12" />
  <path d="M120 320H240V160H505" stroke="{color('300')}" stroke-width="2" />
  <rect x="72" y="190" width="174" height="218" rx="16" fill="{color('800')}" stroke="{color('500')}" />
  <rect x="240" y="110" width="180" height="240" rx="16" fill="{color('900')}" stroke="{color('400')}" />
  <rect x="428" y="62" width="134" height="166" rx="16" fill="{color('800')}" stroke="{color('500')}" />
  <path d="M100 230h78m-78 22h116m-116 22h96m-96 80h55M270 156h64m-64 25h120m-120 24h105m-105 24h85M452 108h80m-80 23h58"
    stroke="{color('400')}" stroke-width="6" stroke-linecap="round" />
  <path d="m285 285 16 16 30-35m136-93 10 10 22-26" stroke="{color('100')}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" />
  <circle cx="120" cy="320" r="8" fill="{color('100')}" />
  <circle cx="420" cy="378" r="30" stroke="{color('300')}" stroke-width="2" />
  <path d="M408 378h24m-10-10 10 10-10 10" stroke="{color('100')}" stroke-width="2" />
</svg>
'''


def render_public_files(
    brand: str, industry: str, design: dict[str, Any], scene_enabled: bool = False,
) -> dict[str, str]:
    """Return frontend-prefixed replacements, with no I/O or auth/backend changes.

    Uses build_design's composition. The optional scene module must be supplied
    by the scene injector; ordinary output has no scene imports or dependencies.
    """
    composition = design["composition"]
    hero = _HEROES[composition["hero"]]
    surface_class = {
        "layered": "capability-asymmetric", "divided": "capability-divided",
        "offset": "capability-alternating", "outlined": "capability-grid",
    }[composition["surface"]]
    capabilities = _bind(_CAPABILITIES, CAPABILITY_CLASS=surface_class)
    workflow = _bind(_WORKFLOW, WORKFLOW_CLASS=(
        "workflow-stepped" if composition["hero"] == "stacked-stepped" else "workflow-linear"
    ))
    sections = {"capabilities": capabilities, "workflow": workflow, "principles": _PRINCIPLES}
    context = {
        "saas": "For your everyday work", "legal": "For legal work", "gaming": "For gaming projects",
        "finance": "For financial work", "fintech": "For financial work",
        "healthcare": "For healthcare work", "education": "For education work",
        "real-estate": "For real estate work", "entertainment": "For creative work",
        "travel": "For travel projects",
    }.get((industry or "").strip().lower(), "For your everyday work")
    scene = """<div className="scene-slot">
  <Suspense fallback={<p role="status">Loading interactive scene controls&hellip;</p>}>
    <Modern3DScene />
  </Suspense>
</div>""" if scene_enabled else ""
    home = hero + scene + "\n" + "\n".join(sections[key] for key in composition["section_order"]) + _CLOSING
    features = """<header className="page-intro"><p className="eyebrow">The essentials, together</p>
<h1>What you can do</h1><p>Account access, editable records, and a direct contact form.
  Start with the capabilities available in {BRAND} today.</p></header>""" + capabilities + workflow + _CLOSING
    return {
        "frontend/src/App.jsx": _APP,
        "frontend/src/components/common/GlassNavbar.jsx": _bind(_NAV, BRAND=_js(brand)),
        "frontend/src/components/common/ModernFooter.jsx": _bind(_FOOTER, BRAND=_js(brand)),
        "frontend/src/pages/Home.jsx": _page("Home", home, brand, context, scene_enabled),
        "frontend/src/pages/Features.jsx": _page("Features", features, brand, context),
        "frontend/src/pages/Pricing.jsx": _page("Pricing", _PRICING, brand, context),
        "frontend/src/pages/About.jsx": _page("About", _ABOUT + _CLOSING, brand, context),
        "frontend/src/pages/Contact.jsx": _CONTACT,
        "frontend/public/assets/workflow.svg": _workflow_svg(design),
    }


__all__ = ["render_public_files", "route_expectations"]
