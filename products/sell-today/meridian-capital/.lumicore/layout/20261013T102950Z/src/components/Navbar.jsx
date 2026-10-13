import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import BrandLogo from './BrandLogo';

const buildNAV_LINKS = (t) => [
  { path: '/', label: t('common.home', 'Home') },
  { path: '/about', label: t('common.about', 'About') },
  { path: '/services', label: t('common.services', 'Services') },
  { path: '/pricing', label: 'Pricing' },
  { path: '/contact', label: t('common.contact', 'Contact') },
];

export default function Navbar() {
  const { t } = useTranslation();

  const NAV_LINKS = buildNAV_LINKS(t);
  const [open, setOpen] = useState(false);
  const loc = useLocation();

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [loc.pathname]);

  return (
    <header
      className="sticky top-0 z-50 border-b border-[var(--t-border)] backdrop-blur-xl"
      style={{ backgroundColor: 'var(--t-canvas)' }}
    >
      <a href="#main-content" className="skip-link">{t('common.skip_to_content', 'Skip to content')}</a>
      <div className="fluid-container mx-auto flex items-center justify-between py-4">
        <BrandLogo />

        <nav
          className="hidden items-center gap-8 lg:flex"
          aria-label="Primary navigation"
        >
          {NAV_LINKS.map((l) => {
            const active = loc.pathname === l.path;
            return (
              <Link
                key={l.path}
                to={l.path}
                aria-current={active ? 'page' : undefined}
                className="text-sm font-medium transition-colors"
                style={{
                  color: active ? 'var(--t-primary)' : 'var(--t-text)',
                  fontWeight: active ? 600 : 500,
                }}
              >
                {l.label}
              </Link>
            );
          })}
          <span className="h-5 w-px" style={{ backgroundColor: 'var(--t-border)' }} />
          <Link
            to="/login"
            className="text-sm font-medium transition-colors"
            style={{ color: 'var(--t-text)' }}
          >
            Login
          </Link>
          <Link to="/contact" className="btn-primary text-sm">
            Request Access
            <ArrowRight className="h-4 w-4" />
          </Link>
        </nav>

        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? 'Close menu' : 'Open menu'}
          className="lg:hidden rounded-lg p-2 transition-colors"
          style={{ color: 'var(--t-text)' }}
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <nav
          id="mobile-menu"
          aria-label="Mobile navigation"
          className="lg:hidden border-t px-6 pb-6 pt-2"
          style={{ backgroundColor: 'var(--t-canvas)', borderColor: 'var(--t-border)' }}
        >
          {NAV_LINKS.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              onClick={() => setOpen(false)}
              className="block py-3 text-sm font-medium"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
          <div className="mt-3 flex flex-col gap-3 border-t pt-4" style={{ borderColor: 'var(--t-border)' }}>
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="btn-outline w-full text-sm text-center"
            >
              Login
            </Link>
            <Link
              to="/contact"
              onClick={() => setOpen(false)}
              className="btn-primary w-full text-sm text-center"
            >
              Request Access
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}
