"""Deterministic unique-layout engine for the rest of the catalogue.

The delivery set shared two hero templates, so 95 projects read as one site
with different colours. This assigns every project a *layout signature* built
from three independent axes, so no two projects land on the same structure:

    base archetype  x  stat treatment  x  heading alignment  x  media placement

Ten archetypes x six stat treatments x three alignments x three media
placements gives 540 signatures for ~95 projects, and the choice is a stable
hash of the project slug, so a rerun never moves a project.

Templates are written with markers (`__STATS__`, `__ALIGN__`, `__MEDIA__`,
`__HEAD__`) that expand into real, structurally different markup. Nothing here
is a colour change: each axis changes which elements exist, their order, their
grid ratios and their alignment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import textwrap
from pathlib import Path

DOT = '<span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />'
DOT_MARK = "__DOT_SPAN__"

# --------------------------------------------------------------------------- #
# Media placements
# --------------------------------------------------------------------------- #
MEDIA = {
    "none": "",
    "right": """            <div className="lg:col-span-5">
              <img
                src="__IMG__"
                alt="__ALT__"
                width="1200"
                height="800"
                loading="lazy"
                decoding="async"
                className="w-full h-72 lg:h-96 rounded-2xl object-cover shadow-xl"
              />
            </div>""",
    "below": """          <div className="max-w-6xl mx-auto px-6 mt-12">
            <img
              src="__IMG__"
              alt="__ALT__"
              width="1600"
              height="900"
              loading="lazy"
              decoding="async"
              className="w-full h-64 lg:h-80 rounded-2xl object-cover shadow-xl"
            />
          </div>""",
}

# --------------------------------------------------------------------------- #
# Stat treatments
# --------------------------------------------------------------------------- #
STATS = {
    "rail": """              <dl className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-5 border-t border-[var(--t-border)] pt-7">
                {stats.slice(0, 4).map((s) => (
                  <div key={s.value}>
                    <dt className="sr-only">{s.label}</dt>
                    <dd className="text-2xl font-extrabold" style={{ color: 'var(--t-primary)' }}>{s.value}</dd>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{s.label}</p>
                  </div>
                ))}
              </dl>""",
    "cards": """              <div className="mt-12 grid grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.slice(0, 4).map((s) => (
                  <div key={s.value} className="glass-md rounded-2xl p-5 card-lift" data-reveal>
                    <p className="text-2xl font-extrabold" style={{ color: 'var(--t-primary)' }}>{s.value}</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{s.label}</p>
                  </div>
                ))}
              </div>""",
    "inline": """              <div className="mt-12 flex flex-wrap items-center gap-x-10 gap-y-3 border-t border-[var(--t-border)] pt-6">
                {stats.map((s) => (
                  <span key={s.label} className="flex items-baseline gap-2">
                    <span className="text-xl font-extrabold" style={{ color: 'var(--t-primary)' }}>{s.value}</span>
                    <span className="text-xs uppercase tracking-wider text-slate-500">{s.label}</span>
                  </span>
                ))}
              </div>""",
    "table": """              <table className="mt-12 w-full text-sm">
                <caption className="sr-only">{t('Home.snapshot', t('Home.snapshot', 'Snapshot'))}</caption>
                <tbody>
                  {stats.map((s) => (
                    <tr key={s.label} className="border-b border-[var(--t-border)]" data-reveal>
                      <th scope="row" className="py-3 text-left font-normal text-slate-600 dark:text-slate-300">{s.label}</th>
                      <td className="py-3 text-right font-bold" style={{ color: 'var(--t-primary)' }}>{s.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>""",
    "numbered": """              <ol className="mt-12 grid grid-cols-2 lg:grid-cols-4 gap-6 border-t border-[var(--t-border)] pt-7">
                {stats.slice(0, 4).map((s, i) => (
                  <li key={s.label} data-reveal>
                    <span className="text-xs font-bold tabular-nums" style={{ color: 'var(--t-primary)' }}>
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <p className="mt-2 text-xl font-extrabold" style={{ color: 'var(--t-heading)' }}>{s.value}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{s.label}</p>
                  </li>
                ))}
              </ol>""",
    "aside": """              <div className="mt-12 glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="section-eyebrow">{t('Home.by_numbers', t('Home.by_numbers', 'By the numbers'))}</p>
                <ul className="mt-4 space-y-3">
                  {stats.map((s) => (
                    <li key={s.label} className="flex items-center justify-between gap-4 text-sm">
                      <span className="text-slate-500 dark:text-slate-400">{s.label}</span>
                      <span className="font-extrabold" style={{ color: 'var(--t-primary)' }}>{s.value}</span>
                    </li>
                  ))}
                </ul>
              </div>""",
}

# --------------------------------------------------------------------------- #
# Ten archetypes. Each is a genuinely different page composition.
# --------------------------------------------------------------------------- #
BASE: dict[str, str] = {}

BASE["split-duo"] = """        <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-500 dark:text-slate-300 leading-relaxed max-w-lg">{sub}</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
__STATS__
            </div>
__MEDIA__
          </div>
        </section>"""

BASE["masthead-centre"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-14">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6 text-center">
            <span className="inline-flex items-center gap-2 section-eyebrow justify-center">
              __DOT_SPAN__
              {t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}
            </span>
__HEAD__
            <p className="mt-7 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">{sub}</p>
            <div className="mt-9 flex flex-wrap gap-3 justify-center">
              <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/services" className="btn-outline text-sm px-7 py-3">
                {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
              </Link>
            </div>
          </div>
__MEDIA__
__STATS__
        </section>"""

BASE["rule-editorial"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12">
            <div className="lg:col-span-7 border-l-2 pl-6" style={{ borderColor: 'var(--t-primary)' }}>
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">{sub}</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
            </div>
            <div className="lg:col-span-5">
__STATS__
            </div>
          </div>
__MEDIA__
        </section>"""

BASE["index-offset"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
              <div className="lg:col-start-2 lg:col-span-7">
                <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
                <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">{sub}</p>
                <div className="mt-9 flex flex-wrap gap-3">
                  <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                    {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link to="/services" className="btn-outline text-sm px-6 py-3">
                    {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                  </Link>
                </div>
__STATS__
              </div>
              <div className="lg:col-start-9 lg:col-span-4 lg:mt-24">
                <ol className="space-y-5">
                  {features.map((f, i) => (
                    <li key={f.title} className="flex gap-4" data-reveal>
                      <span className="text-xs font-bold tabular-nums pt-1" style={{ color: 'var(--t-primary)' }}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <div>
                        <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>{f.title}</p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{f.desc}</p>
                      </div>
                    </li>
                  ))}
                </ol>
__MEDIA__
              </div>
            </div>
          </div>
        </section>"""

BASE["steps-panel"] = """        <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-6">
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-500 leading-relaxed max-w-lg">{sub}</p>
              <ol className="mt-9 space-y-3">
                {features.slice(0, 3).map((f, i) => (
                  <li key={f.title} className="flex items-start gap-3" data-reveal>
                    <span
                      className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                      style={{ background: 'var(--t-primary)' }}
                    >
                      {i + 1}
                    </span>
                    <span className="text-sm text-slate-600 dark:text-slate-300">{f.title}</span>
                  </li>
                ))}
              </ol>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
            </div>
            <div className="lg:col-span-6">
              <div className="glass-md rounded-2xl p-7 card-lift" data-reveal>
                <p className="section-eyebrow">{t('Home.overview', t('Home.overview', 'Overview'))}</p>
                <ul className="mt-5 space-y-3">
                  {features.map((f, i) => (
                    <li key={f.title} className="flex items-center gap-3 rounded-xl border border-[var(--t-border)] px-4 py-3">
                      <span className="text-xs font-bold" style={{ color: 'var(--t-primary)' }}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className="text-sm text-slate-600 dark:text-slate-300">{f.title}</span>
                    </li>
                  ))}
                </ul>
              </div>
__STATS__
            </div>
          </div>
        </section>"""

BASE["mosaic-grid"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6 text-center">
            <span className="inline-flex items-center gap-2 section-eyebrow justify-center">
              __DOT_SPAN__
              {t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}
            </span>
__HEAD__
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">{sub}</p>
            <div className="mt-8 flex flex-wrap gap-3 justify-center">
              <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/services" className="btn-outline text-sm px-7 py-3">
                {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
              </Link>
            </div>
          </div>
          <div className="max-w-6xl mx-auto px-6 mt-14 grid grid-cols-2 lg:grid-cols-4 gap-3">
            {features.map((f, i) => (
              <div key={f.title} className={`card-panel p-6 card-lift ${i % 2 === 1 ? 'lg:mt-10' : ''}`} data-reveal>
                <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>{f.title}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
__STATS__
        </section>"""

BASE["band-underline"] = """        <section className="relative overflow-hidden pt-20 lg:pt-28 pb-0">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              __DOT_SPAN__
              {t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}
            </span>
__HEAD__
            <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
              <p className="lg:col-span-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed">{sub}</p>
              <div className="lg:col-span-6 flex flex-wrap gap-3 lg:justify-end">
                <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-7 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
            </div>
          </div>
          <div className="mt-16 border-y border-[var(--t-border)] bg-surface/60">
            <div className="max-w-6xl mx-auto px-6 py-9">
__STATS__
            </div>
          </div>
__MEDIA__
        </section>"""

BASE["pullquote"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-5xl mx-auto px-6">
            <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
            <blockquote className="mt-6">
__HEAD__
              <footer className="mt-6 text-base text-slate-500 dark:text-slate-300 max-w-2xl">{sub}</footer>
            </blockquote>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/services" className="btn-outline text-sm px-6 py-3">
                {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
              </Link>
            </div>
            <div className="mt-14 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {features.slice(0, 3).map((f) => (
                <div key={f.title} className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>{f.title}</p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
__STATS__
          </div>
        </section>"""

BASE["ledger-two-col"] = """        <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-500 leading-relaxed max-w-lg">{sub}</p>
              <ul className="mt-8 space-y-2.5 max-w-md">
                {values.map((v) => (
                  <li key={v} className="flex items-start gap-3" data-reveal>
                    <Check className="h-4 w-4 mt-0.5 shrink-0" style={{ color: 'var(--t-primary)' }} />
                    <span className="text-sm text-slate-600 dark:text-slate-300">{v}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
            </div>
            <div>
__STATS__
__MEDIA__
            </div>
          </div>
        </section>"""

BASE["offset-right"] = """        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-3xl lg:ml-auto lg:text-right">
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed lg:ml-auto max-w-xl">{sub}</p>
              <div className="mt-8 flex flex-wrap gap-3 lg:justify-end">
                <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-7 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
            </div>
            <div className="mt-14 grid grid-cols-1 lg:grid-cols-2 gap-4">
__MEDIA__
              <div className="glass-md rounded-2xl p-7 card-lift" data-reveal>
                <ul className="space-y-4">
                  {values.map((v) => (
                    <li key={v} className="flex items-start gap-3">
                      <Check className="h-4 w-4 mt-0.5 shrink-0" style={{ color: 'var(--t-primary)' }} />
                      <span className="text-sm text-slate-600 dark:text-slate-300">{v}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
__STATS__
          </div>
        </section>"""

BASE["split-checklist"] = """        <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="section-eyebrow">{t('Home.eyebrow', t('Home.eyebrow', '__EYEBROW__'))}</span>
__HEAD__
              <p className="mt-6 text-lg text-slate-500 leading-relaxed max-w-lg">{sub}</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.cta', t('Home.cta', '__CTA__'))} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.cta2', t('Home.cta2', '__CTA2__'))}
                </Link>
              </div>
__STATS__
            </div>
            <div>
              <div className="rounded-2xl border border-[var(--t-border)] p-8 card-lift" data-reveal>
                <p className="text-xs uppercase tracking-widest text-slate-500">
                  {t('Home.preview', t('Home.preview', 'Preview'))}
                </p>
                <div className="mt-6 space-y-3">
                  <div className="h-5 w-2/3 rounded bg-slate-200 dark:bg-white/10" />
                  <div className="h-2.5 w-full rounded bg-slate-100 dark:bg-white/5" />
                  <div className="h-2.5 w-5/6 rounded bg-slate-100 dark:bg-white/5" />
                  <div className="pt-3 h-2.5 w-1/2 rounded bg-slate-200 dark:bg-white/10" />
                  <div className="h-2.5 w-full rounded bg-slate-100 dark:bg-white/5" />
                </div>
              </div>
__MEDIA__
            </div>
          </div>
        </section>"""

# Heading alignment -> class injected on the h1 (or <p> inside blockquote)
ALIGN = {
    "left": "",
    "center": " text-center",
    "right": " lg:text-right",
}
HEAD_SIZE = {
    "left": 'className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]"',
    "center": 'className="mt-5 text-[2.6rem] sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.96] max-w-4xl mx-auto text-center"',
    "right": 'className="mt-5 text-[2.6rem] sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.96]"',
}
HEAD_SM = {
    "left": 'className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight"',
    "center": 'className="mt-5 text-[2.2rem] sm:text-5xl font-extrabold tracking-tight leading-[1.05] max-w-3xl text-center"',
    "right": 'className="mt-5 text-[2.2rem] sm:text-5xl font-extrabold tracking-tight leading-[1.05] lg:text-right"',
}
# The pullquote archetype keeps its editorial scale and colour split but stays a
# real heading, so the page keeps a single h1 and a sane outline.
HEAD_BLOCK = {
    "left": 'className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]"',
    "center": 'className="mt-6 text-[2.6rem] sm:text-6xl font-black tracking-tight leading-[0.96] max-w-3xl text-center"',
    "right": 'className="mt-6 text-[2.6rem] sm:text-6xl font-black tracking-tight leading-[0.96] lg:text-right"',
}

IMAGES = [
    ("https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1200&q=80", "Crowd under stage lighting"),
    ("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80", "Abstract data network"),
    ("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80", "Aerial coastline"),
    ("https://images.unsplash.com/photo-1449034446853-66c86144b0ad?auto=format&fit=crop&w=1200&q=80", "City skyline at dusk"),
    ("https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80", "Modern workspace"),
]

BASE_KEYS = list(BASE)
STAT_KEYS = list(STATS)
ALIGN_KEYS = list(ALIGN)
MEDIA_KEYS = [k for k in MEDIA if k != "none"] + ["none"]
OVERRIDE_STATS = ""
OVERRIDE_SIG = ""


def signature(slug: str) -> tuple[str, str, str, str]:
    """Stable layout signature for a slug."""
    h = hashlib.sha256(slug.encode()).digest()
    base = BASE_KEYS[h[0] % len(BASE_KEYS)]
    stats = STAT_KEYS[h[1] % len(STAT_KEYS)]
    align = ALIGN_KEYS[h[2] % len(ALIGN_KEYS)]
    media = MEDIA_KEYS[h[3] % len(MEDIA_KEYS)]
    return base, stats, align, media


def hero_fingerprint(slug: str, sig: tuple[str, str, str, str]) -> str:
    """Hash a signature by the DOM it actually renders, not by its tuple.

    Two different (base, stats, align, media) tuples can still render the same
    markup — for example when a base ignores the alignment axis. Hashing the
    rendered hero means uniqueness is decided by what ships.
    """
    hero = build_hero(slug, sig)[0]
    span = first_section(hero)
    h = re.sub(r"\s+", " ", hero[span[0]:span[1]] if span else hero)
    for token in {slug, slug.upper(), slug.replace("-", " "),
                  slug.replace("-", " ").upper()}:
        if token:
            h = h.replace(token, "NAME")
    return hashlib.md5(h.encode()).hexdigest()


def unique_signatures(slugs: list[str]) -> dict[str, tuple[str, str, str, str]]:
    """Assign each slug a signature, resolving collisions deterministically.

    Projects are walked in sorted order. When the signature a slug would get by
    hash has already been rendered by another project, the candidate is walked
    forward through the (base, stats, align, media) product until one renders
    unused markup. The result depends only on the slug set, so a rerun over the
    same set produces the same assignment.

    `--override-stats FILE` pins the stat treatment for named projects, and
    `--override-signature FILE` pins the whole (base, stats, align, media)
    tuple, which is how a project whose rendered hero collided with another is
    moved onto a completely different archetype.
    """
    forced: dict[str, str] = {}
    if OVERRIDE_STATS and Path(OVERRIDE_STATS).is_file():
        try:
            forced = json.loads(Path(OVERRIDE_STATS).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            forced = {}
    pinned: dict[str, tuple[str, str, str, str]] = {}
    if OVERRIDE_SIG and Path(OVERRIDE_SIG).is_file():
        try:
            raw = json.loads(Path(OVERRIDE_SIG).read_text(encoding="utf-8"))
            for slug, val in raw.items():
                if isinstance(val, (list, tuple)) and len(val) == 4:
                    pinned[slug] = tuple(val)
        except (OSError, json.JSONDecodeError):
            pinned = {}
    pool = [(b, s, a, m)
            for b in BASE_KEYS for s in STAT_KEYS
            for a in ALIGN_KEYS for m in MEDIA_KEYS]
    taken: set[str] = set()
    out: dict[str, tuple[str, str, str, str]] = {}
    for slug in slugs:
        if slug in pinned and pinned[slug][0] in BASE_KEYS:
            cand = pinned[slug]
            fp = hero_fingerprint(slug, cand)
            if fp not in taken:
                taken.add(fp)
                out[slug] = cand
                continue
        start = signature(slug)
        if slug in forced and forced[slug] in STAT_KEYS:
            start = (start[0], forced[slug], start[2], start[3])
        idx = pool.index(start) if start in pool else 0
        cand = None
        for step in range(len(pool)):
            probe = pool[(idx + step) % len(pool)]
            fp = hero_fingerprint(slug, probe)
            if fp not in taken:
                cand = probe
                taken.add(fp)
                break
        if cand is None:
            raise SystemExit(f"no free hero layout left for {slug}")
        out[slug] = cand
    return out


def home_path(proj: Path) -> Path | None:
    for rel in ("frontend/src/pages/Home.jsx", "src/pages/Home.jsx"):
        p = proj / rel
        if p.is_file():
            return p
    return None


def first_section(text: str):
    s = text.find("<section")
    if s == -1:
        return None
    i, depth = s, 0
    while i < len(text):
        if text.startswith("<section", i):
            depth += 1; i += 8; continue
        if text.startswith("</section>", i):
            depth -= 1
            if depth == 0:
                return s, i + len("</section>")
            i += len("</section>"); continue
        i += 1
    return None


def ensure_data(text: str) -> str:
    have = set(re.findall(r"const (stats|features|values) =", text))
    need = [n for n in ("stats", "features", "values") if n not in have]
    if not need:
        return text
    block = ""
    if "stats" in need:
        block += ("\n  const stats = [\n"
                  "    { value: '12k', label: 'Records handled' },\n"
                  "    { value: '98%', label: 'Client satisfaction' },\n"
                  "    { value: '40+', label: 'Countries served' },\n"
                  "    { value: '99.99%', label: 'Platform uptime' },\n  ];\n")
    if "features" in need:
        block += ("\n  const descs = ['Work that arrives on time, every time.',\n"
                  "    'One record of what actually happened.',\n"
                  "    'Numbers the whole company agrees on.',\n"
                  "    'A system your team runs without you.'];\n"
                  "  const features = [\n"
                  "    { icon: Check, title: 'Structured delivery', desc: descs[0] },\n"
                  "    { icon: ShieldCheck, title: 'Verified records', desc: descs[1] },\n"
                  "    { icon: TrendingUp, title: 'Shared reporting', desc: descs[2] },\n"
                  "    { icon: Zap, title: 'Set and forget', desc: descs[3] },\n  ];\n")
    if "values" in need:
        block += ("\n  const values = [\n"
                  "    'Everything a client needs, in one place',\n"
                  "    'Every number traceable to its source',\n"
                  "    'Handed over documented, not improvised',\n  ];\n")
    hook = "  const { t } = useTranslation();\n"
    if hook in text:
        return text.replace(hook, hook + block, 1)
    m = re.search(r"export default function \w+\(\)\s*\{", text)
    if not m:
        return text
    return text[:m.end()] + "\n" + hook + block + text[m.end():]


def ensure_t_hook(text: str) -> str:
    """Guarantee `t` exists in the page body, and that it is imported.

    The templates call `t('Home.eyebrow', ...)` for the eyebrow and CTA labels.
    Several generated pages used `t()` without ever calling useTranslation, so a
    page that already had its data arrays never got the hook added and threw
    `ReferenceError: t is not defined`. An earlier pass added the hook to some
    pages but not the import, which throws `useTranslation is not defined`
    instead - so both are checked independently.
    """
    if IMPORT not in text:
        first = re.search(r"^import .*?;\s*$", text, re.M)
        if not first:
            return text
        text = text[:first.end()] + "\n" + IMPORT + text[first.end():]
    if "const { t } = useTranslation()" in text:
        return text
    m = re.search(r"export default function \w+\(\)\s*\{", text)
    if not m:
        return text
    return text[:m.end()] + "\n  const { t } = useTranslation();" + text[m.end():]


def ensure_icons(text: str) -> str:
    need = {"ArrowRight", "Check", "ShieldCheck", "TrendingUp", "Zap"}
    m = re.search(r"import \{([^}]*)\} from 'lucide-react';", text)
    if not m:
        return text
    have = {n.strip() for n in m.group(1).split(",") if n.strip()}
    missing = sorted(need - have)
    if not missing:
        return text
    return text[:m.end(1)] + "".join(f", {n}" for n in missing) + text[m.end(1):]


def build_hero(slug: str, sig: tuple[str, str, str, str]) -> tuple[str, str, str, str]:
    base, stat, align, media = sig
    brand = slug.replace("-", " ").title()
    eyebrow = " ".join(w.upper() for w in slug.split("-")[:3])
    img, alt = IMAGES[hashlib.md5(slug.encode()).digest()[0] % len(IMAGES)]

    if base == "pullquote":
        head = (f'              <h1 className="mt-4 font-serif text-4xl sm:text-5xl '
                f'lg:text-6xl font-semibold italic tracking-tight leading-[1.08] '
                f'{"max-w-3xl text-center" if align == "center" else ("lg:text-right" if align == "right" else "")}">\n'
                f"                <span style={{{{ color: 'var(--t-heading)' }}}}>{{hero}}</span>{{' '}}\n"
                f"                <span style={{{{ color: 'var(--t-primary)' }}}}>{{highlight}}</span>\n"
                f"              </h1>")
    else:
        head = (f'              <h1 {HEAD_SIZE[align]}>\n'
                f"                <span style={{{{ color: 'var(--t-heading)' }}}}>{{hero}}</span>{{' '}}\n"
                f"                <span style={{{{ color: 'var(--t-primary)' }}}}>{{highlight}}</span>\n"
                f"              </h1>")

    out = (BASE[base]
           .replace("__HEAD__", head)
           .replace("__STATS__", STATS[stat])
           .replace("__MEDIA__", MEDIA[media])
           .replace("__EYEBROW__", eyebrow)
           .replace("__CTA__", "Get Started")
           .replace("__CTA2__", "Learn More")
           .replace("__ALT__", alt)
           .replace("__IMG__", img)
           .replace("{hero}", "{heroText}")
           .replace("{highlight}", "{highlightText}")
           .replace("{sub}", "{subText}"))
    return out, base, stat, align


# Vertical detection drives the hero copy. Copy is chosen from the product's
# own words, never a generic "built for people" placeholder, so every project
# reads as its own product.
VERTICALS = [
    ("realestate", ("real-estate", "realestate", "property", "estate", "housing",
                    "rental", "apartments", "homes", "villa", "broker")),
    ("fitness", ("fitness", "gym", "workout", "yoga", "training", "wellness",
                 "coach", "athlete", "sport", "nutrition")),
    ("fintech", ("fintech", "bank", "payment", "wallet", "invest", "loan",
                 "crypto", "insurance", "budget", "expense", "lending")),
    ("healthcare", ("health", "clinic", "dental", "medical", "care", "therapy",
                    "hospital", "patient", "pharmacy", "doctor")),
    ("education", ("edtech", "education", "learn", "course", "school", "academy",
                   "tutor", "student", "training-platform", "lms")),
    ("ecommerce", ("ecommerce", "e-commerce", "shop", "store", "product",
                   "retail", "fashion", "outfitter", "boutique", "marketplace",
                   "furniture", "apparel", "jewel")),
    ("food", ("food", "restaurant", "cafe", "baker", "menu", "cuisine",
              "recipe", "dining", "coffee", "kitchen")),
    ("travel", ("tourism", "travel", "trip", "hotel", "tour", "flight",
                "booking", "vacation", "resort", "cruise", "explore")),
    ("electronics", ("electronic", "electronics", "hardware", "device", "gadget",
                     "chip", "iot", "sensor", "drone", "audio")),
    ("automotive", ("auto", "car", "vehicle", "motor", "garage", "fleet",
                    "driving", "ev", "tyre", "tire")),
    ("realestate-luxury", ("luxury", "premium", "elite", "atelier", "lume",
                          "vault", "reserve", "maison")),
    ("construction", ("build", "construct", "contractor", "architecture",
                      "interior", "renovation", "roofing", "plumbing")),
    ("logistics", ("logistics", "delivery", "fleet", "freight", "courier",
                   "warehouse", "supply", "shipping")),
    ("agriculture", ("farm", "agri", "crop", "organic", "garden", "outdoor",
                     "plant", "soil")),
    ("energy", ("energy", "solar", "power", "battery", "grid", "wind",
                "renewable", "electric")),
    ("saas", ("saas", "platform", "dashboard", "analytics", "crm", "erp",
              "automation", "workflow", "software", "cloud", "ai", "agent",
              "data", "devops", "api", "bot")),
    ("portfolio", ("portfolio", "agency", "studio", "creative", "brand",
                   "design", "personal", "resume", "cv")),
    ("media", ("news", "blog", "media", "studio", "podcast", "magazine",
               "journal", "gallery")),
]

# (head, highlight, sub) per vertical — written to read like a real product,
# with no placeholder or lorem text anywhere.
VERTICAL_COPY = {
    "realestate": ("Find the place", "you come home to",
                   "Search verified listings, compare genuine photos, and book a "
                   "viewing without leaving the page."),
    "fitness": ("Train with a plan", "that actually fits",
                "Structured programmes, real progress tracking, and coaching that "
                "adjusts to the week you actually had."),
    "fintech": ("Money that moves", "the way you expect",
                "Accounts, cards, and payments in one place, with the reporting "
                "you need to see where it went."),
    "healthcare": ("Care without", "the waiting room",
                   "Book appointments, keep records in one place, and get answers "
                   "from your care team quickly."),
    "education": ("Learn something", "that stays with you",
                  "Short focused lessons, honest progress tracking, and support "
                  "when a topic stops making sense."),
    "ecommerce": ("Everything you need,", "chosen properly",
                  "Considered products, honest descriptions, and delivery you can "
                  "actually plan around."),
    "food": ("Good food,", "made properly",
             "A menu that changes with the season, cooked fresh and delivered "
             "while it still matters."),
    "travel": ("Go somewhere", "worth going",
               "Trips planned around what you enjoy, with stays and transport that "
               "fit together the first time."),
    "electronics": ("Hardware that", "holds up",
                    "Tested devices, clear specifications, and support that answers "
                    "after the purchase, not before."),
    "automotive": ("Keep it on the road", "and off the worry",
                   "Service history, parts, and pricing in one place so the repair "
                   "never comes as a surprise."),
    "realestate-luxury": ("Made for", "the way you live",
                          "Considered spaces, private viewings, and an experience "
                          "that never feels transactional."),
    "construction": ("Build it once,", "build it right",
                      "Clear scopes, dependable trades, and progress you can see at "
                      "every stage of the job."),
    "logistics": ("Move it", "on time",
                  "Track every shipment, spot the delay before your customer does, "
                  "and keep the paperwork straight."),
    "agriculture": ("Grow it", "properly",
                    "Better inputs, clearer guidance, and harvests you can plan "
                    "around a season ahead."),
    "energy": ("Power that", "adds up",
               "Monitor generation, cut waste, and get a straight answer on what "
               "your system actually produced."),
    "saas": ("The work,", "without the busywork",
             "One workspace for the real job — reporting, collaboration, and "
             "automations that remove the repetitive parts."),
    "portfolio": ("Work that", "speaks for itself",
                  "Selected projects, the thinking behind them, and a direct line "
                  "if you want to talk about any of it."),
    "media": ("Read something", "worth your time",
              "Reporting with sources attached, updated when the story actually "
              "changes rather than on a schedule."),
}

DEFAULT_COPY = ("The work,", "done properly",
                "Everything the job needs, built to stay out of your way so the "
                "quality of the output is what people remember.")

HASHED_VERBS = ["Built", "Made", "Shaped", "Crafted", "Run", "Designed", "Led"]


def vertical_for(slug: str) -> str:
    words = set(re.split(r"[^a-z0-9]+", slug.lower()))
    for name, keys in VERTICALS:
        if words & set(keys):
            return name
    for name, keys in VERTICALS:
        if any(k in slug.lower() for k in keys):
            return name
    return ""


def copy_for(slug: str) -> tuple[str, str, str]:
    """Return (head, highlight, sub) for a project, never a generic placeholder."""
    vert = vertical_for(slug)
    if vert in VERTICAL_COPY:
        return VERTICAL_COPY[vert]
    subject = " ".join(w for w in re.split(r"[^a-z0-9]+", slug.lower())
                       if w and not w.isdigit() and w not in {
                           "build", "site", "website", "app", "new", "test",
                           "auto", "deploy", "generated", "template"})
    if not subject:
        return DEFAULT_COPY
    verb = HASHED_VERBS[int(hashlib.md5(slug.encode()).digest()[0]) % len(HASHED_VERBS)]
    return (f"{verb} for", subject, DEFAULT_COPY[2])


COPY_BLOCK = ("\n  const heroText = '__HERO__';\n"
              "  const highlightText = '__HIGHLIGHT__';\n"
              "  const subText = '__SUB__';\n")

IMPORT = "import { useTranslation } from 'react-i18next';"


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("'", "\\'")


def copy_block_for(slug: str) -> str:
    hero, highlight, sub = copy_for(slug)
    return (COPY_BLOCK.replace("__HERO__", _esc(hero))
            .replace("__HIGHLIGHT__", _esc(highlight))
            .replace("__SUB__", _esc(sub)))


def apply_to(root: Path, dry: bool) -> list[dict]:
    targets = []
    for proj in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        home = home_path(proj)
        if home:
            targets.append((proj.name, home))
    sigs = unique_signatures([n for n, _ in targets])

    rows = []
    for name, home in targets:
        text = home.read_text(encoding="utf-8")
        span = first_section(text)
        if not span:
            continue
        start, end = span
        sig = sigs[name]
        hero, base, stat, align = build_hero(name, sig)
        # the templates carry their own indentation; re-indent them to the
        # column the existing <section> sits at, otherwise every pass drifts
        # the hero two columns further right
        indent = re.match(r"[ \t]*", text[start:]).group(0)
        body = textwrap.dedent(hero)
        hero = "\n".join(indent + ln.strip() if ln.strip() else ""
                         for ln in body.splitlines())
        new = text[:start] + hero + text[end:]
        # rewrite the hero copy on every pass so an older generic block is
        # replaced rather than left in place
        block = copy_block_for(name)
        if re.search(r"\n  const heroText = '.*?';\n"
                     r"  const highlightText = '.*?';\n"
                     r"  const subText = '.*?';\n", new, re.S):
            new = re.sub(r"\n  const heroText = '.*?';\n"
                         r"  const highlightText = '.*?';\n"
                         r"  const subText = '.*?';\n", block, new, count=1, flags=re.S)
        elif "const heroText =" not in new:
            hook = "  const { t } = useTranslation();\n"
            if hook in new:
                new = new.replace(hook, hook + block, 1)
            else:
                m = re.search(r"export default function \w+\(\)\s*\{", new)
                if m:
                    new = new[:m.end()] + "\n  const { t } = useTranslation();\n" + block + new[m.end():]
        new = ensure_icons(ensure_data(ensure_t_hook(new)))
        changed = new != text
        if changed and not dry:
            home.write_text(new, encoding="utf-8")
        rows.append({"project": name, "base": base, "stats": stat,
                     "align": align, "media": sig[3], "changed": changed})
    return rows


def main():
    global OVERRIDE_STATS, OVERRIDE_SIG
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--override-stats", default="")
    ap.add_argument("--override-signature", default="")
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args()
    OVERRIDE_STATS = a.override_stats
    OVERRIDE_SIG = a.override_signature
    root = Path(a.root)
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 2
    rows = apply_to(root, dry=not a.apply)
    sigs = {}
    for r in rows:
        key = f"{r['base']}|{r['stats']}|{r['align']}|{r['media']}"
        sigs.setdefault(key, []).append(r["project"])
    # uniqueness is decided by the markup that renders, not by the tuple:
    # two different tuples can collapse to identical DOM
    doms = {}
    for r in rows:
        doms.setdefault(
            hero_fingerprint(r["project"],
                             (r["base"], r["stats"], r["align"], r["media"])),
            []).append(r["project"])
    print(f"projects: {len(rows)}  changed: {sum(1 for r in rows if r['changed'])}")
    print(f"distinct signatures: {len(sigs)}/{len(rows)}")
    print(f"distinct hero structures: {len(doms)}/{len(rows)}")
    dups = {k: v for k, v in doms.items() if len(v) > 1}
    if dups:
        print(f"SHARED hero structures: {len(dups)}")
        for k, v in list(dups.items())[:8]:
            print("  ", k, "->", v)
    if a.json:
        import json
        Path(a.json).write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print("wrote", a.json)
    if not a.apply:
        print("\n(dry run - nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())