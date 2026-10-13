import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import UniqueLogo from '../common/UniqueLogo';
import { BRAND } from '../brand/BRAND';

/** GlassNavbar — layout-engine generated (glass shell). */
export default function GlassNavbar() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const links = [{"path": "/about", "label": "About"}, {"path": "/services", "label": "Services"}, {"path": "/pricing", "label": "Pricing"}, {"path": "/contact", "label": "Contact"}, {"path": "/privacy", "label": "Privacy"}, {"path": "/terms", "label": "Terms"}, {"path": "/projects", "label": "Projects"}];
  return (
    <header className="sticky top-0 z-50 border-b px-6 py-4" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 80%, transparent)', borderColor: 'var(--t-border)', backdropFilter: 'blur(14px)' }}>
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link to="/" className="inline-flex items-center gap-2.5" aria-label={BRAND.name}>
          <UniqueLogo size={32} />
          <span className="font-bold tracking-tight" style={{ fontFamily: 'var(--t-display-font)', color: 'var(--t-heading)' }}>{BRAND.name}</span>
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <Link key={l.path} to={l.path} className="text-sm font-medium transition-colors" style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}>{l.label}</Link>
          ))}
          <Link to="/pricing" className="btn-primary">Get started <ArrowRight className="h-4 w-4" /></Link>
        </nav>
        <button onClick={() => setOpen(!open)} className="md:hidden p-2" aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="mt-4 flex flex-col gap-3 border-t pt-4 md:hidden" style={{ borderColor: 'var(--t-border)' }}>
          {links.map((l) => (
            <Link key={l.path} to={l.path} onClick={() => setOpen(false)} className="text-sm font-medium" style={{ color: 'var(--t-text)' }}>{l.label}</Link>
          ))}
        </div>
      )}
    </header>
  );
}
