#!/usr/bin/env python
"""International-grade upgrade engine for all generated projects.

Deterministic, dependency-free pass that brings every generated project up to
international-sellable quality by fixing:

1. Unique branded SVG logo per project (UniqueLogo.jsx + logo.svg + favicon.svg + og-image.svg)
2. Navbar: swap LumicorePro -> UniqueLogo, fix broken markup, proper auth links
3. Footer: swap LumicorePro -> UniqueLogo, fix hardcoded colors -> tokens
4. index.css: deduplicate lumi-motion blocks, replace hardcoded hex -> tokens
5. Scratch projects: inject missing pages + routes for full-stack completeness

Run from repo root:
    python scripts/internationalize_all.py [--dry-run] [--only SLUG,SLUG]
"""

import argparse
import json
import re
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated-projects"

# ---------------------------------------------------------------------------
# Brand definitions - one per project slug
# Each gets a unique geometric SVG symbol + display name + tagline
# ---------------------------------------------------------------------------

BRANDS: Dict[str, Dict[str, Any]] = {
    "aurelia-estates": {
        "name": "Aurelia Estates",
        "tagline": "Luxury Real Estate",
        "industry": "real_estate",
        "symbol": "arch",
        "shape_svg": (
            '<path d="M24 6 C16 6 10 12 10 20 L10 42 L16 42 L16 22 C16 16 19 12 24 12 C29 12 32 16 32 22 L32 42 L38 42 L38 20 C38 12 32 6 24 6Z"/>'
            '<rect x="10" y="42" width="28" height="4" rx="2"/>'
        ),
    },
    "maison-noir": {
        "name": "Maison Noir",
        "tagline": "Haute Couture",
        "industry": "fashion",
        "symbol": "monogram",
        "shape_svg": (
            '<path d="M14 38 L14 10 L20 10 L24 24 L28 10 L34 10 L34 38 L28 38 L28 20 L24 30 L20 20 L20 38Z"/>'
        ),
    },
    "ember-salt": {
        "name": "Ember & Salt",
        "tagline": "Fine Dining",
        "industry": "restaurant",
        "symbol": "flame",
        "shape_svg": (
            '<path d="M24 4 C24 4 12 18 12 28 C12 35 17 40 24 40 C31 40 36 35 36 28 C36 18 24 4 24 4Z"/>'
            '<path d="M24 18 C24 18 18 26 18 30 C18 33 21 36 24 36 C27 36 30 33 30 30 C30 26 24 18 24 18Z" fill="var(--t-primary)"/>'
        ),
    },
    "saffron-voyage": {
        "name": "Saffron Voyage",
        "tagline": "Travel Concierge",
        "industry": "travel",
        "symbol": "compass",
        "shape_svg": (
            '<circle cx="24" cy="24" r="18" fill="none" stroke="var(--t-primary)" stroke-width="3"/>'
            '<circle cx="24" cy="24" r="14" fill="none" stroke="var(--t-accent)" stroke-width="1.5"/>'
            '<polygon points="24,8 26,22 24,24 22,22" fill="var(--t-primary)"/>'
            '<polygon points="24,40 22,26 24,24 26,26" fill="var(--t-accent)"/>'
            '<polygon points="8,24 22,22 24,24 22,26" fill="var(--t-accent)" opacity="0.6"/>'
            '<polygon points="40,24 26,26 24,24 26,22" fill="var(--t-primary)" opacity="0.6"/>'
        ),
    },
    "prestige-studio": {
        "name": "Prestige",
        "tagline": "AI Content Studio",
        "industry": "saas",
        "symbol": "prism",
        "shape_svg": (
            '<polygon points="24,6 40,18 40,36 24,42 8,36 8,18"/>'
            '<polygon points="24,12 34,20 34,32 24,38 14,32 14,20" fill="none" stroke="var(--t-accent)" stroke-width="1.5"/>'
        ),
    },
    "meridian-capital": {
        "name": "Meridian Capital",
        "tagline": "Wealth Management",
        "industry": "fintech",
        "symbol": "bars",
        "shape_svg": (
            '<rect x="8" y="28" width="6" height="12" rx="1.5"/>'
            '<rect x="17" y="20" width="6" height="20" rx="1.5"/>'
            '<rect x="26" y="12" width="6" height="28" rx="1.5"/>'
            '<rect x="35" y="8" width="6" height="32" rx="1.5"/>'
            '<line x1="8" y1="42" x2="41" y2="42" stroke="var(--t-accent)" stroke-width="2" stroke-linecap="round"/>'
        ),
    },
    "voltus-atelier": {
        "name": "Voltus Atelier",
        "tagline": "Electric Vehicles",
        "industry": "automotive",
        "symbol": "bolt",
        "shape_svg": (
            '<polygon points="26,4 14,26 22,26 20,44 34,20 26,20"/>'
        ),
    },
    "aurum-fitness": {
        "name": "Aurum Fitness",
        "tagline": "Elite Wellness",
        "industry": "fitness",
        "symbol": "pulse",
        "shape_svg": (
            '<circle cx="24" cy="24" r="18" fill="none" stroke="var(--t-primary)" stroke-width="2.5"/>'
            '<polyline points="8,24 16,24 19,14 22,34 25,18 28,28 32,24 40,24" fill="none" stroke="var(--t-accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        ),
    },
    "studio-lumen": {
        "name": "Studio Lumen",
        "tagline": "Interior Design",
        "industry": "interior",
        "symbol": "aperture",
        "shape_svg": (
            '<circle cx="24" cy="24" r="18" fill="none" stroke="var(--t-primary)" stroke-width="2.5"/>'
            '<circle cx="24" cy="24" r="6" fill="var(--t-accent)"/>'
            '<line x1="24" y1="6" x2="24" y2="18" stroke="var(--t-primary)" stroke-width="2"/>'
            '<line x1="24" y1="30" x2="24" y2="42" stroke="var(--t-primary)" stroke-width="2"/>'
            '<line x1="6" y1="24" x2="18" y2="24" stroke="var(--t-primary)" stroke-width="2"/>'
            '<line x1="30" y1="24" x2="42" y2="24" stroke="var(--t-primary)" stroke-width="2"/>'
        ),
    },
    "nuage-events": {
        "name": "Nuage Events",
        "tagline": "Event Planning",
        "industry": "events",
        "symbol": "rings",
        "shape_svg": (
            '<ellipse cx="20" cy="24" rx="10" ry="14" fill="none" stroke="var(--t-primary)" stroke-width="2.5"/>'
            '<ellipse cx="28" cy="24" rx="10" ry="14" fill="none" stroke="var(--t-accent)" stroke-width="2.5"/>'
        ),
    },
}

# Generic fallback mark for non-campaign projects
GENERIC_MARKS = [
    (
        "rounded-rect",
        '<rect x="8" y="8" width="32" height="32" rx="8"/>',
    ),
    (
        "hexagon",
        '<polygon points="24,4 42,14 42,34 24,44 6,34 6,14"/>',
    ),
    (
        "diamond",
        '<polygon points="24,4 44,24 24,44 4,24"/>',
    ),
    (
        "octagon",
        '<polygon points="16,4 32,4 42,14 42,32 32,42 16,42 6,32 6,14"/>',
    ),
    (
        "shield",
        '<path d="M24,4 L40,12 L40,28 C40,36 32,42 24,44 C16,42 8,36 8,28 L8,12Z"/>',
    ),
]


def _slug_hash(slug: str) -> int:
    return abs(hash(slug))


def _get_brand(slug: str) -> Dict[str, Any]:
    if slug in BRANDS:
        return BRANDS[slug]
    idx = _slug_hash(slug) % len(GENERIC_MARKS)
    symbol, shape = GENERIC_MARKS[idx]
    display_name = slug.replace("-", " ").title()
    return {
        "name": display_name,
        "tagline": "Digital Platform",
        "industry": "generic",
        "symbol": symbol,
        "shape_svg": shape,
    }


def _render(template: str, **kw: str) -> str:
    """Replace __TOKEN__ markers with values."""
    out = template
    for k, v in kw.items():
        out = out.replace("__%s__" % k, v)
    return out


# ---------------------------------------------------------------------------
# Logo asset generators
# ---------------------------------------------------------------------------

def _logo_svg_content(brand: Dict[str, Any]) -> str:
    mark_id = "%04d" % (_slug_hash(brand["name"]) % 9999)
    return textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" width="400" height="100">
          <defs>
            <linearGradient id="g1_{mark_id}" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="var(--t-primary, #0ea5e9)"/>
              <stop offset="100%" stop-color="var(--t-accent, #6366f1)"/>
            </linearGradient>
          </defs>
          <g transform="translate(12, 8) scale(1.6)" fill="url(#g1_{mark_id})">
            {brand['shape_svg']}
          </g>
          <text x="84" y="60" font-family="system-ui, -apple-system, sans-serif" font-size="36" font-weight="700"
                letter-spacing="-0.5" fill="#0e1116">{brand['name']}</text>
          <text x="84" y="78" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="500"
                letter-spacing="0.5" fill="#64748b">{brand['tagline']}</text>
        </svg>
        """
    )


def _favicon_svg_content(brand: Dict[str, Any]) -> str:
    mark_id = "%04d" % (_slug_hash(brand["name"]) % 9999)
    return textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
          <defs>
            <linearGradient id="fg_{mark_id}" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="var(--t-primary, #0ea5e9)"/>
              <stop offset="100%" stop-color="var(--t-accent, #6366f1)"/>
            </linearGradient>
          </defs>
          <rect width="64" height="64" rx="14" fill="url(#fg_{mark_id})"/>
          <g transform="translate(8, 8) scale(1)" fill="white" opacity="0.95">
            {brand['shape_svg']}
          </g>
        </svg>
        """
    )


def _og_image_svg_content(brand: Dict[str, Any]) -> str:
    mark_id = "%04d" % (_slug_hash(brand["name"]) % 9999)
    return textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
          <defs>
            <linearGradient id="og_{mark_id}" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="var(--t-primary, #0ea5e9)"/>
              <stop offset="100%" stop-color="var(--t-accent, #6366f1)"/>
            </linearGradient>
          </defs>
          <rect width="1200" height="630" fill="#0e1116"/>
          <rect x="60" y="200" width="100" height="100" rx="20" fill="url(#og_{mark_id})"/>
          <g transform="translate(80, 220) scale(2.5)" fill="white" opacity="0.95">
            {brand['shape_svg']}
          </g>
          <text x="190" y="260" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="700"
                fill="white">{brand['name']}</text>
          <text x="190" y="300" font-family="system-ui, -apple-system, sans-serif" font-size="20" font-weight="500"
                fill="#94a3b8">{brand['tagline']}</text>
          <text x="60" y="560" font-family="system-ui, -apple-system, sans-serif" font-size="14" font-weight="400"
                fill="#475569">Powered by LumicorePro</text>
        </svg>
        """
    )


UNIQUE_LOGO_JSX = textwrap.dedent(
    """\
    import React from 'react';
    import { Link } from 'react-router-dom';

    export default function UniqueLogo({ size = 'md' }) {
      const sz = { sm: 24, md: 32, lg: 40 }[size] || 32;
      return (
        <Link
          to="/"
          className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90"
          aria-label="__BRAND_NAME__"
        >
          <div style={{ width: sz, height: sz }} className="shrink-0">
            <svg
              viewBox="0 0 48 48"
              width="100%"
              height="100%"
              fill="var(--t-primary)"
              xmlns="http://www.w3.org/2000/svg"
            >
              __SHAPE_SVG__
            </svg>
          </div>
          <span
            className="font-bold tracking-tight"
            style={{
              color: 'var(--t-heading)',
              fontSize: size === 'lg' ? '1.5rem' : size === 'sm' ? '0.875rem' : '1.125rem',
            }}
          >
            __FIRST_WORD__
          </span>
        </Link>
      );
    }
    """
)

# ---------------------------------------------------------------------------
# Navbar / Footer templates (plain JSX, token-safe)
# ---------------------------------------------------------------------------

NAVBAR_TEMPLATE = """\
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import UniqueLogo from './UniqueLogo';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const links = [
    { path: '/', label: 'Home' },
    { path: '/about', label: 'About' },
    { path: '/services', label: 'Services' },
    { path: '/pricing', label: 'Pricing' },
    { path: '/contact', label: 'Contact' },
  ];
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--t-border)] bg-[var(--t-canvas)]/95 backdrop-blur-lg supports-[backdrop-filter]:bg-[var(--t-canvas)]/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <UniqueLogo />
        <div className="hidden items-center gap-6 md:flex">
          {links.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              className="text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
        </div>
        <div className="hidden items-center gap-3 md:flex">
          <Link
            to="/login"
            className="rounded-full px-5 py-2 text-sm font-semibold transition-all hover:opacity-85"
            style={{ color: 'var(--t-text)', border: '1px solid var(--t-border)' }}
          >
            Sign in
          </Link>
          <Link
            to="/register"
            className="rounded-full px-5 py-2 text-sm font-bold text-white transition-all hover:opacity-90 active:scale-95"
            style={{ background: 'var(--t-primary)' }}
          >
            Get Started
          </Link>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="rounded-lg p-2 text-[var(--t-text)] hover:bg-[var(--t-border)]/30 md:hidden"
          aria-label="Menu"
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="border-t border-[var(--t-border)] bg-[var(--t-canvas)] px-6 pb-4 pt-2 md:hidden">
          {links.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              onClick={() => setOpen(false)}
              className="block py-2.5 text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
          <div className="mt-3 flex gap-3">
            <Link to="/login" onClick={() => setOpen(false)} className="flex-1 rounded-full py-2.5 text-center text-sm font-semibold transition-all" style={{ color: 'var(--t-text)', border: '1px solid var(--t-border)' }}>Sign in</Link>
            <Link to="/register" onClick={() => setOpen(false)} className="flex-1 rounded-full py-2.5 text-center text-sm font-bold text-white transition-all" style={{ background: 'var(--t-primary)' }}>Get Started</Link>
          </div>
        </div>
      )}
    </nav>
  );
}
"""

FOOTER_TEMPLATE = """\
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import UniqueLogo from './UniqueLogo';

export default function Footer() {
  const [email, setEmail] = useState('');
  const [sub, setSub] = useState(false);
  return (
    <footer className="text-white" style={{ backgroundColor: 'var(--t-footer)' }}>
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-4">
          <div className="space-y-4">
            <UniqueLogo size="lg" />
            <p className="max-w-xs text-sm leading-relaxed text-slate-300">
              __BRAND_DESCRIPTION__
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Operational
            </div>
          </div>
          <div>
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Product</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/services" className="transition-colors hover:text-white">Features</Link></li>
              <li><Link to="/pricing" className="transition-colors hover:text-white">Pricing</Link></li>
              <li><Link to="/about" className="transition-colors hover:text-white">Case Studies</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Company</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/about" className="transition-colors hover:text-white">About Us</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">Contact</Link></li>
              <li><Link to="/privacy-policy" className="transition-colors hover:text-white">Privacy Policy</Link></li>
              <li><Link to="/terms-of-service" className="transition-colors hover:text-white">Terms</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Stay Updated</h4>
            <p className="mb-3 text-xs text-slate-300">Weekly product updates and insights.</p>
            {sub ? (
              <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                <CheckCircle2 className="h-4 w-4" /> Subscribed!
              </div>
            ) : (
              <form
                onSubmit={(e) => { e.preventDefault(); if (email) setSub(true); }}
                className="space-y-2"
              >
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email address"
                  className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-slate-400 focus:border-white/40 focus:outline-none"
                />
                <button
                  type="submit"
                  className="w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition-all hover:opacity-90"
                  style={{ background: 'var(--t-primary)' }}
                >
                  Subscribe
                </button>
              </form>
            )}
          </div>
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 text-xs text-slate-400 sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} __BRAND_NAME__. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a href="#" className="transition-colors hover:text-white">Twitter</a>
            <a href="#" className="transition-colors hover:text-white">LinkedIn</a>
            <a href="#" className="transition-colors hover:text-white">GitHub</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
"""

# ---------------------------------------------------------------------------
# Page templates for projects missing full-stack pages
# ---------------------------------------------------------------------------

ABOUT_PAGE = """\
import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function About() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <span className="mb-4 inline-block text-xs font-semibold uppercase tracking-[0.15em]" style={{ color: 'var(--t-primary)' }}>About Us</span>
          <h1 className="mb-6 text-4xl font-extrabold sm:text-5xl lumi-reveal" style={{ color: 'var(--t-heading)' }}>Our Story</h1>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed" style={{ color: 'var(--t-muted)' }}>
            __ABOUT_TEXT__
          </p>
        </section>
        <section className="border-t py-16" style={{ borderColor: 'var(--t-border)' }}>
          <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-6 sm:grid-cols-3 lumi-reveal">
            {[
              { title: 'Mission', desc: 'Deliver world-class products and experiences.' },
              { title: 'Vision', desc: 'Lead the industry through innovation and trust.' },
              { title: 'Values', desc: 'Integrity, quality, and relentless improvement.' },
            ].map((v) => (
              <div key={v.title} className="rounded-2xl p-8" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
                <h3 className="mb-3 text-xl font-bold" style={{ color: 'var(--t-heading)' }}>{v.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--t-muted)' }}>{v.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""

SERVICES_PAGE = """\
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Shield, Zap, Globe, Headphones } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const features = [
  { icon: Shield, title: 'Secure & Reliable', desc: 'Enterprise-grade security with 99.99% uptime guarantee across all services.' },
  { icon: Zap, title: 'Lightning Fast', desc: 'Optimized for performance with sub-second load times and instant interactions.' },
  { icon: Globe, title: 'Global Scale', desc: 'Deployed across multiple regions for worldwide coverage and low latency.' },
  { icon: Headphones, title: '24/7 Support', desc: 'Round-the-clock expert support to keep your operations running smoothly.' },
];

export default function Services() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <span className="mb-4 inline-block text-xs font-semibold uppercase tracking-[0.15em]" style={{ color: 'var(--t-primary)' }}>Our Services</span>
          <h1 className="mb-6 text-4xl font-extrabold sm:text-5xl lumi-reveal" style={{ color: 'var(--t-heading)' }}>Built for Your Success</h1>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed" style={{ color: 'var(--t-muted)' }}>
            Everything you need to launch, scale, and manage your digital presence.
          </p>
        </section>
        <section className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 pb-20 sm:grid-cols-2">
          {features.map((f, i) => (
            <div key={f.title} className="group rounded-2xl p-8 transition-all hover:-translate-y-1 hover:shadow-xl lumi-reveal" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', transitionDelay: `${i * 80}ms` }}>
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white" style={{ background: 'var(--t-primary)' }}>
                <f.icon className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-xl font-bold" style={{ color: 'var(--t-heading)' }}>{f.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--t-muted)' }}>{f.desc}</p>
            </div>
          ))}
        </section>
        <section className="py-16 text-center" style={{ background: 'var(--t-surface)' }}>
          <div className="mx-auto max-w-6xl px-6 lumi-reveal">
            <h2 className="mb-4 text-3xl font-bold" style={{ color: 'var(--t-heading)' }}>Ready to Get Started?</h2>
            <p className="mx-auto mb-8 max-w-xl" style={{ color: 'var(--t-muted)' }}>Choose a plan that works for you, or reach out for a custom solution.</p>
            <Link to="/pricing" className="inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-bold text-white transition-all hover:opacity-90 active:scale-95" style={{ background: 'var(--t-primary)' }}>
              View Pricing <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""

PRICING_PAGE = """\
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const plans = [
  { name: 'Starter', monthly: 29, annual: 290, features: ['5 projects', 'Basic analytics', 'Email support', '1 GB storage'] },
  { name: 'Professional', monthly: 79, annual: 790, features: ['Unlimited projects', 'Advanced analytics', 'Priority support', '50 GB storage', 'Custom domains'] },
  { name: 'Enterprise', monthly: 199, annual: 1990, features: ['Everything in Pro', 'Dedicated account manager', 'Custom integrations', 'Unlimited storage', 'SLA guarantee'] },
];

export default function Pricing() {
  const [annual, setAnnual] = useState(false);
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <span className="mb-4 inline-block text-xs font-semibold uppercase tracking-[0.15em]" style={{ color: 'var(--t-primary)' }}>Pricing</span>
          <h1 className="mb-6 text-4xl font-extrabold sm:text-5xl lumi-reveal" style={{ color: 'var(--t-heading)' }}>Simple, Transparent Pricing</h1>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed mb-8" style={{ color: 'var(--t-muted)' }}>
            No hidden fees. Cancel anytime.
          </p>
          <div className="inline-flex items-center gap-3 rounded-full p-1" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
            <button onClick={() => setAnnual(false)} className={`rounded-full px-5 py-2 text-sm font-semibold transition-all ${!annual ? 'text-white' : ''}`} style={{ background: !annual ? 'var(--t-primary)' : 'transparent', color: !annual ? 'white' : 'var(--t-muted)' }}>Monthly</button>
            <button onClick={() => setAnnual(true)} className={`rounded-full px-5 py-2 text-sm font-semibold transition-all ${annual ? 'text-white' : ''}`} style={{ background: annual ? 'var(--t-primary)' : 'transparent', color: annual ? 'white' : 'var(--t-muted)' }}>Annual <span className="text-xs opacity-80">Save 17%</span></button>
          </div>
        </section>
        <section className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 pb-20 md:grid-cols-3 lumi-reveal">
          {plans.map((p) => (
            <div key={p.name} className="flex flex-col rounded-2xl p-8 transition-all hover:-translate-y-1 hover:shadow-xl" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
              <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--t-heading)' }}>{p.name}</h3>
              <div className="mb-6">
                <span className="text-4xl font-extrabold" style={{ color: 'var(--t-primary)' }}>${annual ? Math.round(p.annual / 12) : p.monthly}</span>
                <span className="text-sm ml-1" style={{ color: 'var(--t-muted)' }}>/mo</span>
              </div>
              <ul className="mb-8 flex-1 space-y-3">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 shrink-0" style={{ color: 'var(--t-primary)' }} /> {f}
                  </li>
                ))}
              </ul>
              <Link to="/register" className="rounded-xl py-3 text-center text-sm font-bold text-white transition-all hover:opacity-90 active:scale-95" style={{ background: 'var(--t-primary)' }}>
                Get Started
              </Link>
            </div>
          ))}
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""

CONTACT_PAGE = """\
import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Contact() {
  const [sent, setSent] = useState(false);
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 py-20 text-center">
          <span className="mb-4 inline-block text-xs font-semibold uppercase tracking-[0.15em]" style={{ color: 'var(--t-primary)' }}>Contact Us</span>
          <h1 className="mb-6 text-4xl font-extrabold sm:text-5xl lumi-reveal" style={{ color: 'var(--t-heading)' }}>Get in Touch</h1>
          <p className="mx-auto max-w-2xl text-lg leading-relaxed" style={{ color: 'var(--t-muted)' }}>
            Have a question or want to work together? We'd love to hear from you.
          </p>
        </section>
        <section className="mx-auto max-w-6xl px-6 pb-20">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lumi-reveal">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold" style={{ color: 'var(--t-heading)' }}>Send us a message</h2>
              {sent ? (
                <div className="flex items-center gap-2 rounded-xl p-4 text-sm font-medium" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', color: 'var(--t-primary)' }}>
                  <CheckCircle2 className="h-5 w-5" /> Message sent! We'll get back to you soon.
                </div>
              ) : (
                <form onSubmit={(e) => { e.preventDefault(); setSent(true); }} className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <input required placeholder="Name" className="rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} />
                    <input required type="email" placeholder="Email" className="rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} />
                  </div>
                  <input placeholder="Subject" className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} />
                  <textarea required rows="5" placeholder="Your message..." className="w-full resize-none rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} />
                  <button type="submit" className="inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-bold text-white transition-all hover:opacity-90 active:scale-95" style={{ background: 'var(--t-primary)' }}>
                    <Send className="h-4 w-4" /> Send Message
                  </button>
                </form>
              )}
            </div>
            <div className="space-y-6 rounded-2xl p-8" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
              <h2 className="text-2xl font-bold" style={{ color: 'var(--t-heading)' }}>Reach Us Directly</h2>
              {[
                { icon: Mail, label: 'Email', value: 'hello@example.com' },
                { icon: Phone, label: 'Phone', value: '+1 (555) 000-0000' },
                { icon: MapPin, label: 'Office', value: '123 Innovation Drive, San Francisco, CA' },
              ].map((c) => (
                <div key={c.label} className="flex items-start gap-4">
                  <div className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white" style={{ background: 'var(--t-primary)' }}>
                    <c.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--t-muted)' }}>{c.label}</div>
                    <div className="text-sm font-medium" style={{ color: 'var(--t-text)' }}>{c.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""

LOGIN_PAGE = """\
import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Login() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="w-full max-w-md rounded-2xl p-8 lumi-reveal" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-extrabold" style={{ color: 'var(--t-heading)' }}>Welcome Back</h1>
            <p className="mt-2 text-sm" style={{ color: 'var(--t-muted)' }}>Sign in to your account</p>
          </div>
          <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Email</label>
              <input type="email" required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="you@example.com" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Password</label>
              <input type="password" required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="********" />
            </div>
            <button type="submit" className="w-full rounded-xl py-3 text-sm font-bold text-white transition-all hover:opacity-90 active:scale-[0.98]" style={{ background: 'var(--t-primary)' }}>
              Sign In
            </button>
          </form>
          <p className="mt-6 text-center text-sm" style={{ color: 'var(--t-muted)' }}>
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold transition-colors hover:opacity-80" style={{ color: 'var(--t-primary)' }}>Create one</Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""

REGISTER_PAGE = """\
import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Register() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <Navbar />
      <main className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="w-full max-w-md rounded-2xl p-8 lumi-reveal" style={{ background: 'var(--t-surface)', border: '1px solid var(--t-border)' }}>
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-extrabold" style={{ color: 'var(--t-heading)' }}>Create Account</h1>
            <p className="mt-2 text-sm" style={{ color: 'var(--t-muted)' }}>Get started in seconds</p>
          </div>
          <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>First Name</label>
                <input required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="John" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Last Name</label>
                <input required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="Doe" />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Email</label>
              <input type="email" required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="you@example.com" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold" style={{ color: 'var(--t-muted)' }}>Password</label>
              <input type="password" required className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all focus:ring-2" style={{ background: 'var(--t-canvas)', border: '1px solid var(--t-border)', color: 'var(--t-text)' }} placeholder="Min 8 characters" />
            </div>
            <button type="submit" className="w-full rounded-xl py-3 text-sm font-bold text-white transition-all hover:opacity-90 active:scale-[0.98]" style={{ background: 'var(--t-primary)' }}>
              Create Account
            </button>
          </form>
          <p className="mt-6 text-center text-sm" style={{ color: 'var(--t-muted)' }}>
            Already have an account?{' '}
            <Link to="/login" className="font-semibold transition-colors hover:opacity-80" style={{ color: 'var(--t-primary)' }}>Sign in</Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""

FULL_APP_JSX = """\
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppProviders from './lib/AppProviders';
import './lib/theme';

const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Services = lazy(() => import('./pages/Services'));
const Pricing = lazy(() => import('./pages/Pricing'));
const Contact = lazy(() => import('./pages/Contact'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--t-canvas)' }}>
      <div className="h-8 w-8 rounded-full animate-pulse" style={{ background: 'var(--t-primary)' }} />
    </div>
  );
}

const basename =
  typeof window !== 'undefined' && window.location.pathname.split('/')[1]
    ? '/' + window.location.pathname.split('/')[1]
    : '/';

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter basename={basename}>
        <Suspense fallback={<Loader />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/services" element={<Services />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AppProviders>
  );
}
"""

APPPROVIDERS_JSX = """\
import React from 'react';

export default function AppProviders({ children }) {
  return <>{children}</>;
}
"""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _find_frontend(project_dir: Path) -> Optional[Path]:
    if (project_dir / "frontend" / "src" / "main.jsx").is_file():
        return project_dir / "frontend"
    if (project_dir / "src" / "main.jsx").is_file():
        return project_dir
    return None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_brand_info(project_dir: Path) -> Dict[str, Any]:
    result = {
        "about_text": "We build exceptional digital products with a focus on performance, security, and design excellence.",
        "brand_description": "Building exceptional digital products with performance, security, and design excellence.",
    }
    tokens_file = project_dir / "frontend" / "src" / "styles" / "design-tokens.json"
    if not tokens_file.exists():
        tokens_file = project_dir / "src" / "styles" / "design-tokens.json"
    if tokens_file.exists():
        try:
            tok = json.loads(tokens_file.read_text(encoding="utf-8"))
            if tok.get("project_name"):
                result["brand_slug"] = tok["project_name"]
        except Exception:
            pass
    return result


def _dedupe_lumi_css(css: str) -> Tuple[str, int]:
    """Collapse repeated lumi-motion blocks to a single one."""
    block_re = re.compile(
        r'/\* ===== lumi-motion.*?/\* ===== end lumi-motion ===== \*/', re.DOTALL
    )
    blocks = block_re.findall(css)
    if len(blocks) <= 1:
        return css, 0
    if not blocks[0].rstrip().endswith("lumi-motion-injected"):
        blocks[0] = blocks[0].rstrip("\n") + "\n/* lumi-motion-injected */\n"
    return css.replace("".join(blocks[1:]), "").replace(
        blocks[0], blocks[0].rstrip("\n") + "\n"
    ), len(blocks) - 1


CSS_TOKEN_MAP = [
    ("background-color: #b8860b;", "background-color: var(--t-primary);"),
    ("color: #5b3200;", "color: var(--t-heading);"),
    ("color: #b8860b;", "color: var(--t-primary);"),
    ("border: 2px solid #5b3200;", "border: 2px solid var(--t-heading);"),
]


def upgrade_project(project_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    slug = project_dir.name
    brand = _get_brand(slug)
    brand_info = _load_brand_info(project_dir)
    report: Dict[str, Any] = {"slug": slug, "actions": []}

    frontend = _find_frontend(project_dir)
    if not frontend:
        report["actions"].append("skipped: no frontend/src/main.jsx")
        return report

    src = frontend / "src"
    components = src / "components"
    pages = src / "pages"

    # 1. UniqueLogo.jsx
    unique_logo_path = components / "UniqueLogo.jsx"
    logo_content = _render(
        UNIQUE_LOGO_JSX,
        BRAND_NAME=brand["name"],
        FIRST_WORD=brand["name"].split()[0],
        SHAPE_SVG=brand["shape_svg"],
    )
    if not dry_run:
        _write(unique_logo_path, logo_content)
    report["actions"].append("UniqueLogo.jsx written")

    # 2-4. SVG assets
    svg_targets = [
        (frontend / "public" / "logo.svg", _logo_svg_content(brand)),
        (frontend / "public" / "favicon.svg", _favicon_svg_content(brand)),
        (frontend / "public" / "og-image.svg", _og_image_svg_content(brand)),
    ]
    for path, content in svg_targets:
        if not dry_run:
            _write(path, content)
    report["actions"].append("logo.svg + favicon.svg + og-image.svg written")

    # 5. Navbar.jsx
    if not dry_run:
        _write(components / "Navbar.jsx", NAVBAR_TEMPLATE)
    report["actions"].append("Navbar.jsx rewritten (UniqueLogo, fixed auth)")

    # 6. Footer.jsx
    footer_content = _render(
        FOOTER_TEMPLATE,
        BRAND_NAME=brand["name"],
        BRAND_DESCRIPTION=brand_info["brand_description"],
    )
    if not dry_run:
        _write(components / "Footer.jsx", footer_content)
    report["actions"].append("Footer.jsx rewritten (UniqueLogo, token colors)")

    # 7. index.css dedup + tokenize
    css_path = src / "index.css"
    if css_path.exists():
        css = _read(css_path)
        css_new, removed = _dedupe_lumi_css(css)
        if removed:
            if not dry_run:
                _write(css_path, css_new)
            report["actions"].append(f"index.css: deduped {removed} lumi-motion block(s)")
        else:
            report["actions"].append("index.css: lumi-motion already clean")

        css2 = _read(css_path)
        replaced = 0
        for old, new in CSS_TOKEN_MAP:
            if old in css2:
                css2 = css2.replace(old, new)
                replaced += 1
        if replaced and not dry_run:
            _write(css_path, css2)
        if replaced:
            report["actions"].append(f"index.css: tokenized {replaced} hardcoded hex value(s)")

    # 8. Inject missing pages
    if pages.exists():
        existing_pages = {p.stem for p in pages.glob("*.jsx")}
        missing_pages = []
        page_map = {
            "About": ABOUT_PAGE,
            "Services": SERVICES_PAGE,
            "Pricing": PRICING_PAGE,
            "Contact": CONTACT_PAGE,
            "Login": LOGIN_PAGE,
            "Register": REGISTER_PAGE,
        }
        about_text = brand_info["about_text"]
        for page_name, template in page_map.items():
            if page_name not in existing_pages:
                content = _render(template, ABOUT_TEXT=about_text)
                if not dry_run:
                    _write(pages / f"{page_name}.jsx", content)
                missing_pages.append(page_name)
        if missing_pages:
            report["actions"].append(f"pages: injected {', '.join(missing_pages)}")

    # 9. App.jsx routing
    app_path = src / "App.jsx"
    if app_path.exists():
        app_content = _read(app_path)
        if "About" not in app_content and "/about" not in app_content:
            if not dry_run:
                _write(app_path, FULL_APP_JSX)
            report["actions"].append("App.jsx: upgraded routing")

    # 10-11. Support libs
    theme_path = src / "lib" / "theme.js"
    if not theme_path.exists():
        if not dry_run:
            _write(theme_path, "// theme loader\n")
        report["actions"].append("lib/theme.js: created")

    providers_path = src / "lib" / "AppProviders.jsx"
    if not providers_path.exists():
        if not dry_run:
            _write(providers_path, APPPROVIDERS_JSX)
        report["actions"].append("lib/AppProviders.jsx: created")

    return report


def build_project(project_dir: Path) -> Tuple[bool, str]:
    frontend = _find_frontend(project_dir)
    if not frontend:
        return False, "no frontend found"
    try:
        if not (frontend / "node_modules").is_dir():
            r = subprocess.run(
                ["npm", "install", "--legacy-peer-deps"],
                cwd=str(frontend), capture_output=True, text=True, timeout=120,
            )
            if r.returncode != 0:
                return False, f"npm install failed: {r.stderr[:500]}"
        r = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(frontend), capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            return True, "build OK"
        return False, f"build failed: {r.stderr[:500]}|{r.stdout[-300:]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:300]


def main():
    ap = argparse.ArgumentParser(description="Internationalize all generated projects")
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    ap.add_argument("--only", default="", help="Comma-separated slugs to process (empty = all)")
    ap.add_argument("--skip-build", action="store_true", help="Skip npm build after upgrade")
    args = ap.parse_args()

    projects = sorted(p for p in GEN.iterdir() if p.is_dir())
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        projects = [p for p in projects if p.name in wanted]

    results = []
    for pdir in projects:
        print(f"\n{'='*60}\n  Upgrading: {pdir.name}\n{'='*60}")
        report = upgrade_project(pdir, dry_run=args.dry_run)
        results.append(report)
        for action in report["actions"]:
            print(f"  + {action}")
        if not report["actions"]:
            print("  (no changes)")

    if not args.dry_run and not args.skip_build:
        print(f"\n{'='*60}\n  BUILDING ALL PROJECTS\n{'='*60}")
        build_ok = build_fail = 0
        for r in results:
            pdir = GEN / r["slug"]
            if r["actions"][:1] and "skipped" in r["actions"][0]:
                continue
            ok, out = build_project(pdir)
            status = "BUILD OK" if ok else f"BUILD FAIL: {out[:100]}"
            print(f"  [{r['slug']}] {status}")
            r["build"] = "ok" if ok else "fail"
            if ok:
                build_ok += 1
            else:
                build_fail += 1
        print(f"\n  Builds: {build_ok} ok, {build_fail} failed")

    report_path = GEN / "INTERNATIONALIZATION_REPORT.md"
    lines = [
        "# Internationalization Report",
        "",
        f"Projects processed: {len(results)}",
        "",
        "| Slug | Actions | Build |",
        "|------|---------|-------|",
    ]
    for r in results:
        build = r.get("build", "skipped")
        lines.append(f"| {r['slug']} | {len(r['actions'])} | {build} |")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()