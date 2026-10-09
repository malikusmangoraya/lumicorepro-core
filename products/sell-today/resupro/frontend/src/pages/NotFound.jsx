/**
 * 404 — rendered for any path that matches no route.
 *
 * Without this the catch-all route silently rendered the homepage, which hides broken
 * links from the user and reports a 200 to crawlers for a URL that does not exist.
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Compass, Home, LifeBuoy } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { BRAND } from '../components/brand/BRAND';

export default function NotFound() {
  const { t } = useTranslation();

  const destinations = [
    { to: '/', label: t('common.home', 'Home'), icon: Home },
    { to: '/templates', label: t('common.templates', 'Templates'), icon: Compass },
    { to: '/contact', label: t('common.contact', 'Contact'), icon: LifeBuoy },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main id="main-content" className="flex-1 fluid-container py-16 sm:py-24">
        <section className="max-w-3xl">
        <p className="section-eyebrow">{BRAND.name}</p>
        <p
          className="text-[6rem] font-extrabold leading-none sm:text-[9rem]"
          style={{ color: 'var(--t-primary)' }}
          aria-hidden="true"
        >
          404
        </p>
        <h1 className="section-heading mt-2">
          {t('common.not_found_heading', 'This page could not be found')}
        </h1>
        <p className="mt-4 max-w-xl" style={{ color: 'var(--t-muted)' }}>
          {t(
            'common.not_found_body',
            'The link may be out of date, or the page may have moved. Everything else is still where you left it.'
          )}
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          {destinations.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className="btn-outline">
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </Link>
          ))}
          <button type="button" className="btn-primary" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t('common.go_back', 'Go back')}
          </button>
        </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
