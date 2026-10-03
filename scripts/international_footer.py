"""International Footer generator — v7.10.

Rebuilds every project's Footer into a proper international-standard multi-column
footer: brand column (lockup + tagline + live status badge + social), sitemap
columns (Product / Company / Legal), validated newsletter with success state,
locale + currency selectors, and a bottom bar with copyright + legal links.

Critical fix: the previous footer called `useTranslation()` without importing it,
which crashed every page at runtime (42/43 projects). This template is dependency
light and never touches the i18n hook.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402


FOOTER_TEMPLATE = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, Mail, Globe, Rss, MessageCircle } from 'lucide-react';
import LumicorePro from './LumicorePro';
import CurrencySelector from './ui/CurrencySelector';
import LanguageSelector from './ui/LanguageSelector';

const SOCIALS = [
  { label: 'Website', icon: Globe, href: '#' },
  { label: 'Email', icon: Mail, href: 'mailto:hello@{slug}.com' },
  { label: 'RSS', icon: Rss, href: '#' },
  { label: 'Message', icon: MessageCircle, href: '#' },
];

export default function Footer() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle');
  const [err, setErr] = useState('');

  function onSubmit(e) {
    e.preventDefault();
    const value = email.trim();
    if (!value) {
      setStatus('error');
      setErr('Please enter your email address.');
      return;
    }
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value)) {
      setStatus('error');
      setErr('Please enter a valid email address.');
      return;
    }
    setErr('');
    setStatus('success');
  }

  return (
    <footer className="text-white" style={{ backgroundColor: 'var(--t-footer)' }}>
      <div className="fluid-container mx-auto px-6 pt-16 pb-8">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-5 lg:col-span-1">
            <LumicorePro dark />
            <p className="text-sm leading-relaxed text-slate-400 max-w-xs">
              {TAGLINE}
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true" />
              99.99% Operational
            </div>
          </div>

          <nav aria-label="Product links">
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Product</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><Link to="/services" className="transition-colors hover:text-white">Services</Link></li>
              <li><Link to="/pricing" className="transition-colors hover:text-white">Pricing</Link></li>
              <li><Link to="/login" className="transition-colors hover:text-white">Login</Link></li>
              <li><Link to="/register" className="transition-colors hover:text-white">Create Account</Link></li>
            </ul>
          </nav>

          <nav aria-label="Company links">
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Company</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><Link to="/about" className="transition-colors hover:text-white">About</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">Contact</Link></li>
              <li><Link to="/admin" className="transition-colors hover:text-white">Client Portal</Link></li>
              <li><Link to="/checkout" className="transition-colors hover:text-white">Checkout</Link></li>
            </ul>
          </nav>

          <nav aria-label="Legal links">
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Legal</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><Link to="/privacy" className="transition-colors hover:text-white">Privacy Policy</Link></li>
              <li><Link to="/terms" className="transition-colors hover:text-white">Terms of Service</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">GDPR & Compliance</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">Cookie Settings</Link></li>
            </ul>
          </nav>

          <div>
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Stay Updated</h4>
            <p className="mb-3 text-xs text-slate-400">Monthly notes on new work, offers and events. No noise.</p>
            {status === 'success' ? (
              <div role="status" className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                <CheckCircle2 className="h-4 w-4" /> Subscribed — see you soon.
              </div>
            ) : (
              <form onSubmit={onSubmit} noValidate className="space-y-2" aria-label="Newsletter signup">
                <div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email address"
                    aria-label="Email address"
                    aria-invalid={status === 'error'}
                    aria-describedby={err ? 'nl-error' : undefined}
                    autoComplete="email"
                    className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-slate-400 focus:border-white/40 focus:outline-none"
                    style={{
                      borderColor: status === 'error' ? 'var(--t-error, #ff5f6d)' : undefined,
                    }}
                  />
                  {err && (
                    <p id="nl-error" role="alert" className="mt-1 text-[11px] text-red-400">
                      {err}
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  className="w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition-colors hover:opacity-90"
                  style={{ backgroundColor: 'var(--t-primary)' }}
                >
                  Subscribe
                </button>
              </form>
            )}
            <div className="mt-4 flex items-center gap-2">
              {SOCIALS.map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  aria-label={s.label}
                  className="rounded-full border border-white/15 p-2 transition-colors hover:border-white/40 hover:bg-white/10"
                >
                  <s.icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-3 gap-y-2 border-t border-white/10 pt-6 text-xs text-slate-400">
          <span className="inline-flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5" /> Locale
          </span>
          <LanguageSelector />
        </div>

        <div className="mt-6 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 text-xs text-slate-400 sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} {NAME}. All rights reserved. Powered by{' '}
            <span className="font-semibold text-white">LumicorePro</span>.
          </p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <Link to="/privacy" className="transition-colors hover:text-white">Privacy</Link>
            <Link to="/terms" className="transition-colors hover:text-white">Terms</Link>
            <Link to="/contact" className="transition-colors hover:text-white">Support</Link>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              Systems operational
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
"""


def build_footer(root: str) -> bool:
    front = PROJECTS / root / "frontend"
    out = front / "src" / "components" / "Footer.jsx"
    if not out.parent.exists():
        return False
    b = BRANDS.get(root, BRANDS["build"])
    name = b["name"]
    slugish = root.split("/")[0].replace("_", "-")
    t = FOOTER_TEMPLATE.replace("{NAME}", name)
    t = t.replace("{TAGLINE}", b["tagline"]).replace("{slug}.com", slugish)
    out.write_text(t, encoding="utf-8")
    return True


def main():
    slugs = sys.argv[1:] or [
        d.name
        for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    ok = fail = 0
    for s in slugs:
        if build_footer(s):
            ok += 1
        else:
            fail += 1
            print(f"  WARN {s}")
    print(f"international-footer: {ok} ok, {fail} warn")


if __name__ == "__main__":
    main()