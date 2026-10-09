"""Add niche-specific pages, admin pages (where missing), a GDPR account page
and a demo-credential banner to the four flagship products."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core\products')

# per-product niche page definitions: (file_stem, nav_label_var, title, eyebrow, sub_title, kpis list of (value,label), rows list of (title, detail))
NICHE = {
    'flowpilot': {
        'stem': 'Projects', 'path': '/projects',
        'eyebrow': 'Projects', 'title': 'Every job on one board',
        'sub': 'Track each project from intake to invoice without a spreadsheet.',
        'kpis': [('12', 'Active projects'), ('84%', 'On track'), ('3', 'In review'), ('7', 'Invoiced this month')],
        'rows': [('Redesign checkout', 'In progress · 4 of 6 tasks'), ('API integration', 'Blocked · waiting on keys'), ('Q3 audit', 'In review · 2 comments')],
    },
    'claimflow-ai': {
        'stem': 'Claims', 'path': '/claims',
        'eyebrow': 'Claims', 'title': 'Triage without the queue',
        'sub': 'Intake, review and settle claims in one flow instead of a folder.',
        'kpis': [('27', 'Open claims'), ('41', 'Reviewed this week'), ('6', 'Settled'), ('1.2d', 'Avg to decision')],
        'rows': [('Auto glass claim', 'Pending documents'), ('Water damage', 'Under review'), ('Liability dispute', 'Approved · paying')],
    },
    'resupro': {
        'stem': 'Templates', 'path': '/templates',
        'eyebrow': 'Templates', 'title': 'Pick a look, start writing',
        'sub': 'A dozen honest résumé templates, export-ready for ATS and PDF.',
        'kpis': [('12', 'Templates'), ('3', 'ATS-friendly'), ('2', 'With photo'), ('100%', 'Exportable')],
        'rows': [('Minimal', 'Clean, single column, ATS-safe'), ('Executive', 'Two columns, for senior roles'), ('Creative', 'Accent colour, for design roles')],
    },
    'meridian-capital': {
        'stem': 'Portfolio', 'path': '/portfolio',
        'eyebrow': 'Portfolio', 'title': 'Positions and performance',
        'sub': 'Concentrated holdings, mark-to-market and allocation at a glance.',
        'kpis': [('$4.2M', 'AUM'), ('+14.2%', 'Year to date'), ('8', 'Positions'), ('3', 'New this quarter')],
        'rows': [('Northwind Ventures', '18% · up 22%'), ('Meridian Real Estate', '12% · up 9%'), ('Aurora Health', '10% · up 5%')],
    },
}

NICHE_TEMPLATE = """import React from 'react';
import { useTranslation } from 'react-i18next';
import { Folder, CheckCircle2, Clock, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
__KPIS__
];

const rows = [
__ROWS__
];

export default function __STEM__() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <p className="section-eyebrow">{t('__STEM__.eyebrow', '__EYEBROW__')}</p>
          <h1 className="section-heading mt-1">__TITLE__</h1>
          <p className="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">__SUB__</p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-5" data-reveal>
                <p className="text-2xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 card-panel p-7">
            <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>{t('__STEM__.items', 'Current items')}</h2>
            <ul className="divide-y divide-[var(--t-border)]">
              {rows.map((r, i) => (
                <li key={i} className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium" style={{ color: 'var(--t-heading)' }}>{r.title}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{r.detail}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""

ACCOUNT_TEMPLATE = """import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, Download, Trash2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Account() {
  const { t } = useTranslation();
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  const exportData = async () => {
    try {
      const r = await fetch('/api/auth/account/export', { credentials: 'include' });
      if (!r.ok) throw new Error('unauthorised');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'account-export.json'; a.click();
      URL.revokeObjectURL(url);
    } catch { setMsg(t('Account.exportFailed', 'Sign in to export your data.')); }
  };

  const deleteAccount = async () => {
    if (!window.confirm(t('Account.confirmDelete', 'Permanently delete your account?'))) return;
    try {
      const r = await fetch('/api/auth/account', {
        method: 'DELETE', credentials: 'include',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }),
      });
      const j = await r.json();
      setMsg(r.ok ? t('Account.deleted', 'Account deleted.') : (j.error || t('Account.deleteFailed', 'Could not delete.')));
    } catch { setMsg(t('Account.deleteFailed', 'Could not delete.')); }
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <p className="section-eyebrow">{t('Account.eyebrow', 'Privacy')}</p>
          <h1 className="section-heading mt-1">{t('Account.title', 'Your data')}</h1>
          <div className="card-panel p-7 mt-8 grid gap-6">
            <button onClick={exportData} className="btn-outline inline-flex items-center justify-center gap-2 py-3">
              <Download className="h-4 w-4" /> {t('Account.export', 'Export my data')}
            </button>
            <div>
              <label htmlFor="account-password" className="block text-sm font-medium mb-1" style={{ color: 'var(--t-heading)' }}>
                {t('Account.password', 'Current password')}
              </label>
              <input id="account-password" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-[var(--t-border)] bg-surface px-3 py-2" />
            </div>
            <button onClick={deleteAccount} className="btn-danger inline-flex items-center justify-center gap-2 py-3">
              <Trash2 className="h-4 w-4" /> {t('Account.delete', 'Delete my account')}
            </button>
            {msg && <p className="text-sm text-slate-500">{msg}</p>}
            <p className="text-xs text-slate-400">{t('Account.note', 'Deleting removes the account and its stored data. This cannot be undone.')}</p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""

DEMO_BANNER = """
      {/* demo credentials for the live preview — remove before selling if you do not want them public */}
      <div className="mb-6 rounded-lg border border-[var(--t-border)] bg-surface p-4 text-sm">
        <p className="font-semibold" style={{ color: 'var(--t-heading)' }}>Demo access</p>
        <p className="text-slate-500 dark:text-slate-400">Email: demo@example.com · Password: demo1234</p>
      </div>
"""

ADMIN_TEMPLATE = """import React from 'react';
import { useTranslation } from 'react-i18next';
import { BarChart3, Users, ShoppingBag, TrendingUp, Activity, Clock, ArrowRight, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
__KPIS__
];

export default function Admin() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="section-heading">__BRAND__ control room</h1>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-5" data-reveal>
                <p className="text-2xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""

ADMIN_KPIS = {
    'flowpilot': [('$12.4k', 'MRR'), ('86', 'Seats'), ('4.8', 'CSAT'), ('99.9%', 'Uptime')],
    'claimflow-ai': [('1.2d', 'Avg to decision'), ('91%', 'Straight-through rate'), ('$48k', 'Paid out'), ('0.8%', 'Flagged')],
}

BRAND = {'flowpilot': 'FlowPilot', 'claimflow-ai': 'ClaimFlow', 'resupro': 'ResuPro', 'meridian-capital': 'Meridian'}


def kpi_lines(items):
    return '\n'.join(f"  {{ value: '{v}', label: '{l}' }}," for v, l in items)


def write(path: Path, content: str):
    path.write_text(content, encoding='utf-8')
    print('  wrote', path.name)


def add_route(app_text: str, stem: str, path: str) -> str:
    lazy_import = f"import {stem} from './pages/{stem}';"
    if f"const {stem} = lazy" not in app_text and f"import {stem}" not in app_text:
        m = re.search(r"(const Contact = lazy\(\(\) => import\(\"\./pages/Contact\"\)\);|\nconst NewsletterSignup.*?;)", app_text, re.S)
        anchor = None
        for line in app_text.splitlines(keepends=True):
            if "Contact" in line and "lazy" in line:
                app_text += ""  # noop
        # simpler: insert lazy import after the Contact lazy line
        for i, line in enumerate(app_text.splitlines(keepends=True)):
            if "pages/Contact" in line:
                app_text = "".join(app_text.splitlines(keepends=True)[:i+1]) + \
                    f"const {stem} = lazy(() => import('./pages/{stem}'));\n" + \
                    "".join(app_text.splitlines(keepends=True)[i+1:])
                break
    if f'path="{path}"' not in app_text:
        route_line = f'              <Route path="{path}" element={{<{stem} />}} />\n'
        for i, line in enumerate(app_text.splitlines(keepends=True)):
            if "path=\"/\"" in line:
                lines = app_text.splitlines(keepends=True)
                lines.insert(i, route_line)
                app_text = "".join(lines)
                break
    return app_text


def add_nav_link(nav_text: str, path: str, label: str) -> str:
    entry = f"    {{ path: '{path}', label: t('common.{label.lower()}', '{label}') }},\n"
    if f"'{path}'" in nav_text:
        return nav_text
    idx = nav_text.find("    { path: '/contact'")
    if idx < 0:
        idx = nav_text.find("    { path: '/'")
    if idx < 0:
        return nav_text
    return nav_text[:idx] + entry + nav_text[idx:]


for prod in ('flowpilot', 'claimflow-ai', 'resupro', 'meridian-capital'):
    print('==', prod)
    base = ROOT / prod / 'frontend' / 'src'
    pages = base / 'pages'
    comps = base / 'components'
    appf = base / 'App.jsx'
    navf = comps / 'Navbar.jsx'

    # niche page
    spec = NICHE[prod]
    content = NICHE_TEMPLATE
    content = content.replace('__STEM__', spec['stem'])
    content = content.replace('__EYEBROW__', spec['eyebrow'])
    content = content.replace('__TITLE__', spec['title'])
    content = content.replace('__SUB__', spec['sub'])
    content = content.replace('__KPIS__', kpi_lines(spec['kpis'])) \
                     .replace('__ROWS__', '\n'.join(
        f"  {{ title: '{t}', detail: '{d}' }}," for t, d in spec['rows']))
    write(pages / f"{spec['stem']}.jsx", content)

    # account page
    write(pages / 'Account.jsx', ACCOUNT_TEMPLATE)

    # admin page where missing
    if not (pages / 'Admin.jsx').exists():
        a = ADMIN_TEMPLATE.replace('__BRAND__', BRAND[prod])
        a = a.replace('__KPIS__', kpi_lines(ADMIN_KPIS[prod]))
        write(pages / 'Admin.jsx', a)

    # App.jsx routes
    app = appf.read_text(encoding='utf-8')
    for stem, path in [(spec['stem'], spec['path']), ('Account', '/account')] + (
            [('Admin', '/admin')] if not (pages / 'Admin.jsx').exists() or 'Admin' not in app else []):
        app = add_route(app, stem, path)
    if (pages / 'Admin.jsx').exists() and 'Admin' not in app:
        app = add_route(app, 'Admin', '/admin')
    appf.write_text(app, encoding='utf-8')
    print('  updated App.jsx')

    # Navbar link
    nav = navf.read_text(encoding='utf-8')
    nav = add_nav_link(nav, spec['path'], spec['stem'])
    nav = add_nav_link(nav, '/account', 'Account')
    if 'Admin' not in nav and (pages / 'Admin.jsx').exists():
        nav = add_nav_link(nav, '/admin', 'Admin')
    navf.write_text(nav, encoding='utf-8')
    print('  updated Navbar.jsx')

    # Login demo banner — insert after the first <Navbar /> in each Login.jsx
    login = pages / 'Login.jsx'
    if login.exists():
        t = login.read_text(encoding='utf-8')
        if 'Demo access' not in t:
            idx = t.find('<Navbar />')
            if idx >= 0:
                idx2 = t.find('\n', idx)
                t = t[:idx2+1] + DEMO_BANNER + t[idx2+1:]
                login.write_text(t, encoding='utf-8')
                print('  added demo banner to Login.jsx')

print('done')
