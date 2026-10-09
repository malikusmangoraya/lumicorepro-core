import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { CheckCircle2, Mail, Globe, Rss, MessageCircle } from 'lucide-react';
import BrandLogo from './BrandLogo';
import CurrencySelector from './ui/CurrencySelector';
import LanguageSelector from './ui/LanguageSelector';

const SOCIALS = [
  { label: 'Website', icon: Globe, href: '#' },
  { label: 'Email', icon: Mail, href: 'mailto:hello@saffron-voyage' },
  { label: 'RSS', icon: Rss, href: '#' },
  { label: 'Message', icon: MessageCircle, href: '#' },
];

export default function Footer() {
  const { t } = useTranslation();
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
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
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
            <BrandLogo dark />
            <p className="text-sm leading-relaxed text-slate-400 max-w-xs">
              Journeys woven from local story.
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
              <li><Link to="/privacy" className="transition-colors hover:text-white">{t('common.privacy_policy', 'Privacy Policy')}</Link></li>
              <li><Link to="/terms" className="transition-colors hover:text-white">{t('common.terms', 'Terms of Service')}</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">GDPR & Compliance</Link></li>
              <li><Link to="/contact" className="transition-colors hover:text-white">Cookie Settings</Link></li>
            </ul>
          </nav>

          <div>
            <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider">Stay Updated</h4>
            <p className="mb-3 text-xs text-slate-400">Monthly notes on new work, offers and events. No noise.</p>
            {status === 'success' ? (
              <div role="status" className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                <CheckCircle2 className="h-4 w-4" /> {t('footer.subscribe', 'Subscribe')}d — see you soon.
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
                  {t('footer.subscribe', 'Subscribe')}
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
            &copy; {new Date().getFullYear()} Saffron Voyage. {t('footer.all_rights', 'All rights reserved.')}
            <span className="font-semibold text-white">Saffron Voyage</span>.
          </p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <Link to="/privacy" className="transition-colors hover:text-white">Privacy</Link>
            <Link to="/terms" className="transition-colors hover:text-white">{t('common.terms', 'Terms of Service')}</Link>
            <Link to="/contact" className="transition-colors hover:text-white">Support</Link>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              Systems operational
            </span>
          </div>
        </div>
        <p className="mt-6 text-center text-[11px] text-slate-500">
          Designed &amp; built by{' '}
          <a
            href="https://github.com/malikusmangoraya"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-slate-400 underline underline-offset-2 hover:text-white"
          >
            Lumicore
          </a>
        </p>
      </div>
    </footer>
  );
}
