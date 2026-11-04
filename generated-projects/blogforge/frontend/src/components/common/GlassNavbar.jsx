import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowRight, Menu, PenLine, X } from 'lucide-react';
import UniqueLogo from './UniqueLogo.jsx';
import { setLocale, translate, useLocale } from '../../i18n.js';

export default function GlassNavbar({ brand = 'BlogForge' }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const locale = useLocale();
  const location = useLocation();
  const signedIn = Boolean(localStorage.getItem('token'));
  const navLinks = [
    { name: 'Features', path: '/features' },
    { name: 'Pricing', path: '/pricing' },
    { name: 'About', path: '/about' },
    { name: 'Contact', path: '/contact' },
  ];

  const languageSelect = (id, className) => (
    <>
      <label className="sr-only" htmlFor={id}>{translate(locale, 'language')}</label>
      <select id={id} value={locale} onChange={(event) => setLocale(event.target.value)} className={className}>
        <option value="en">{translate(locale, 'english')}</option>
        <option value="ur">{translate(locale, 'urdu')}</option>
      </select>
    </>
  );

  const closeMobile = () => setMobileOpen(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex min-w-0 items-center gap-3" aria-label={`${brand} home`}>
          <UniqueLogo size="h-9 w-9" />
          <span className="truncate text-xl font-extrabold tracking-tight text-white transition-colors group-hover:text-brand-accent">{brand}</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex" aria-label="Marketing">
          {navLinks.map((item) => {
            const active = location.pathname === item.path;
            return <Link key={item.name} to={item.path} aria-current={active ? 'page' : undefined} className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${active ? 'bg-brand-primary/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}>{item.name}</Link>;
          })}
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          {languageSelect('locale-select', 'rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-2 text-sm text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary')}
          {signedIn ? <Link to="/generate" className="button-primary min-h-10 px-4 py-2"><PenLine className="h-4 w-4" /> Open workspace</Link> : <><Link to="/login" className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-300 hover:text-white">Sign in</Link><Link to="/register" className="button-primary min-h-10 px-4 py-2">Get started <ArrowRight className="h-4 w-4" /></Link></>}
        </div>
        <button type="button" onClick={() => setMobileOpen((open) => !open)} className="rounded-lg p-2 text-slate-300 hover:bg-white/10 hover:text-white md:hidden" aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={mobileOpen} aria-controls="mobile-navigation">
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {mobileOpen && <div id="mobile-navigation" className="border-t border-slate-800 bg-slate-950 px-4 pb-6 pt-4 md:hidden">
        <div className="mb-4">{languageSelect('locale-select-mobile', 'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-slate-200')}</div>
        <nav className="grid gap-1" aria-label="Mobile marketing">
          {navLinks.map((item) => <Link key={item.name} to={item.path} onClick={closeMobile} className="rounded-lg px-3 py-3 text-base font-semibold text-slate-300 hover:bg-white/5 hover:text-white">{item.name}</Link>)}
        </nav>
        <div className="mt-4 grid gap-2 border-t border-slate-800 pt-4">{signedIn ? <Link to="/generate" onClick={closeMobile} className="button-primary justify-center">Open workspace</Link> : <><Link to="/login" onClick={closeMobile} className="button-secondary justify-center">Sign in</Link><Link to="/register" onClick={closeMobile} className="button-primary justify-center">Get started <ArrowRight className="h-4 w-4" /></Link></>}</div>
      </div>}
    </header>
  );
}
