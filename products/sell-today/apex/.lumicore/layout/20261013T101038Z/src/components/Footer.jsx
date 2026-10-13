import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import BrandLogo from './BrandLogo';

export default function Footer() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [sub, setSub] = useState(false);
  return (
    <footer className="text-white" style={{ backgroundColor: 'var(--t-footer)' }}>
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-4">
          <div className="space-y-4">
            <BrandLogo dark />
            <p className="text-sm text-slate-300 leading-relaxed max-w-xs">
              Building exceptional digital products with performance, security, and design
              excellence.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Operational
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>
                <Link to="/services" className="hover:text-white transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-white transition-colors">
                  Case Studies
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">
                  Enterprise
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>
                <Link to="/about" className="hover:text-white transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">
                  Contact
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-white transition-colors">
                  Careers
                </Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-white transition-colors">
                  {t('common.privacy_policy', 'Privacy Policy')}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Stay Updated</h4>
            <p className="text-xs text-slate-300 mb-3">Weekly product updates and insights.</p>
            {sub ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="h-4 w-4" /> {t('forms.form_success', 'Subscribed!')}
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (email) setSub(true);
                }}
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
                  className="w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition-colors"
                  style={{ backgroundColor: '#7c3aed' }}
                >
                  {t('footer.subscribe', 'Subscribe')}
                </button>
              </form>
            )}
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>
            &copy; {new Date().getFullYear()} Apex Digital. {t('footer.all_rights', 'All rights reserved.')}
            <span className="font-semibold text-white">Apex</span>.
          </p>
          <div className="flex items-center gap-4">
            <Link to="/contact" className="hover:text-white">
              Twitter
            </Link>
            <Link to="/contact" className="hover:text-white">
              LinkedIn
            </Link>
            <Link to="/contact" className="hover:text-white">
              GitHub
            </Link>
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
