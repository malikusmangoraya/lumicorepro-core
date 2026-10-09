/**
 * AppLayout — brand shell for signed-in / console routes.
 *
 * Layout arrangement: overlay-ticker. Colours come from the same --t-* tokens as the marketing
 * shell, so the console cannot drift away from the brand.
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BarChart3, Bell, Menu, Settings, Users } from 'lucide-react';
import BrandLockup from '../components/brand/BrandLockup';
import { BRAND } from '../components/brand/BRAND';

export default function AppLayout({ children }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const items = [
    { to: '/admin', label: t('common.overview', 'Overview'), icon: BarChart3 },
    { to: '/account', label: t('common.account', 'Account'), icon: Users },
    { to: '/admin', label: t('common.settings', 'Settings'), icon: Settings },
  ];

  return (
    <div className="flex min-h-screen flex-col" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <header className="border-b" style={{ borderColor: 'var(--t-border)' }}>
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-3">
            <BrandLockup size={28} />
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ backgroundColor: 'var(--t-primary)', color: '#fff' }}
            >
              {t('common.console', 'Event production console')}
            </span>
          </div>
          <button
            type="button"
            className="md:hidden"
            aria-expanded={open}
            aria-label={t('common.toggle_nav', 'Toggle navigation')}
            onClick={() => setOpen((value) => !value)}
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <nav aria-label="Console" className="hidden items-center gap-1 md:flex">
            {items.map(({ to, label, icon: Icon }) => (
              <Link key={label} to={to} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:opacity-80">
                <Icon className="h-4 w-4" aria-hidden="true" />
                {label}
              </Link>
            ))}
            <span className="ml-3 flex items-center gap-2 border-l pl-4 text-sm" style={{ borderColor: 'var(--t-border)' }}>
              <Bell className="h-4 w-4" aria-hidden="true" />
              {BRAND.initials}
            </span>
          </nav>
        </div>
        {open && (
          <nav aria-label="Console" className="border-t px-6 py-3 md:hidden" style={{ borderColor: 'var(--t-border)' }}>
            <ul className="space-y-2 text-sm">
              {items.map(({ to, label }) => (
                <li key={label}>
                  <Link to={to}>{label}</Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>
      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        {children}
      </main>
    </div>
  );
}
