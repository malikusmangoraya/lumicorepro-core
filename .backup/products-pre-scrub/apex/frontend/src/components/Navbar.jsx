import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import LumicorePro from './LumicorePro';

export default function Navbar() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const links = [
    { path: '/', label: t('common.home', 'Home') },
    { path: '/about', label: t('common.about', 'About') },
    { path: '/services', label: t('common.services', 'Services') },
    { path: '/contact', label: t('common.contact', 'Contact') },
  ];
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--t-border)] bg-canvas/95 backdrop-blur supports-[backdrop-filter]:bg-canvas/80">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <LumicorePro />
        <nav aria-label="Primary" className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              className="text-sm font-medium hover:text-primary transition-colors"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
          <span
            className="hidden lg:inline-block text-sm font-bold"
            style={{ color: 'var(--t-primary)' }}
          >
            Apex Digital
          </span>
          <Link to="/contact" className="btn-primary text-sm">
            {t("common.get_started", "Get Started")}
          </Link>
        </nav>
        <button
          onClick={() => setOpen(!open)}
          className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          aria-label={t("accessibility.open_menu", "Menu")}
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-[var(--t-border)] bg-canvas px-6 pb-4 pt-2">
          {links.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              onClick={() => setOpen(false)}
              className="block py-2 text-sm font-medium hover:text-primary transition-colors"
              style={{ color: 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/contact"
            onClick={() => setOpen(false)}
            className="btn-primary mt-2 text-sm text-center w-full"
          >
            {t("common.get_started", "Get Started")}
          </Link>
        </div>
      )}
    </header>
  );
}
