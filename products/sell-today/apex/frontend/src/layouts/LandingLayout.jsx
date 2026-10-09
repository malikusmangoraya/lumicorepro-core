/**
 * LandingLayout — brand shell for marketing routes.
 *
 * Reads this product's BRAND.js, its --t-* tokens and i18n. It is registered through
 * lib/LazyLayouts.jsx as an alternative to a page composing Navbar/Footer itself.
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import BrandLockup from '../components/brand/BrandLockup';
import { BRAND } from '../components/brand/BRAND';

export default function LandingLayout({ children }) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <a href="#main-content" className="skip-link">
        {t('common.skip_to_content', 'Skip to content')}
      </a>
    <header className="sticky top-0 z-40 backdrop-blur" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 88%, transparent)', color: nav === 'bold-band' || nav === 'overlay-ticker' ? '#fff' : 'var(--t-text)' }}>
      <div className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-2 text-xs" style={{ color: 'var(--t-muted)' }}>
          <span>{t('common.status', 'All systems operational')}</span>
          <span>{BRAND.name}</span>
        </div>
      </div>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <BrandLockup size={32} />
        <nav aria-label="Primary">
          <ul className="hidden items-center gap-7 text-sm font-medium md:flex">
          <li>
            <Link to="/" className="hover:opacity-80 transition-opacity">
              {t('common.home', 'Home')}
            </Link>
          </li>
          <li>
            <Link to="/about" className="hover:opacity-80 transition-opacity">
              {t('common.about', 'About')}
            </Link>
          </li>
          <li>
            <Link to="/services" className="hover:opacity-80 transition-opacity">
              {t('common.services', 'Services')}
            </Link>
          </li>
          <li>
            <Link to="/pricing" className="hover:opacity-80 transition-opacity">
              {t('common.pricing', 'Pricing')}
            </Link>
          </li>
          <li>
            <Link to="/contact" className="hover:opacity-80 transition-opacity">
              {t('common.contact', 'Contact')}
            </Link>
          </li>
          </ul>
        </nav>
        <Link to="/register" className="btn-primary">{t('common.get_started', 'Start free')}</Link>
      </div>
    </header>
      <main id="main-content" className="flex-1">
        {children}
      </main>
    <footer style={{ backgroundColor: 'var(--t-footer)' }} className="mt-auto text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-3">
          <BrandLockup size={30} dark />
          <p className="max-w-xs text-sm leading-relaxed text-white/70">
            {t('footer.blurb', 'Conversion engineering — built for people who care about the details.')}
          </p>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.product', 'Product')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/services" className="hover:text-white">{t('common.services', 'Services')}</Link></li>
            <li><Link to="/pricing" className="hover:text-white">{t('common.pricing', 'Pricing')}</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.company', 'Company')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/about" className="hover:text-white">{t('common.about', 'About')}</Link></li>
            <li><Link to="/contact" className="hover:text-white">{t('common.contact', 'Contact')}</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">{t('footer.legal', 'Legal')}</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/privacy" className="hover:text-white">{t('common.privacy', 'Privacy')}</Link></li>
            <li><Link to="/terms" className="hover:text-white">{t('common.terms', 'Terms')}</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-white/60">
          <span>© {new Date().getFullYear()} {BRAND.name} — {t('common.tagline', 'Conversion engineering')}</span>
          <span>{t('footer.built_with', 'React 19 · Vite · Tailwind')}</span>
        </div>
      </div>
    </footer>
    </div>
  );
}
