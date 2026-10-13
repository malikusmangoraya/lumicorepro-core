import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import BrandLockup from './brand/BrandLockup';

/** Navbar — layout-engine generated. */
export default function Navbar() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const links = [{"path": "/about", "label": "About"}, {"path": "/services", "label": "Services"}, {"path": "/pricing", "label": "Pricing"}, {"path": "/contact", "label": "Contact"}, {"path": "/privacy", "label": "Privacy"}, {"path": "/terms", "label": "Terms"}, {"path": "/claims", "label": "Claims"}];
  return (
    <header className="sticky top-0 z-50 border-b" style={{ backgroundColor: 'color-mix(in srgb, var(--t-canvas) 88%, transparent)', borderColor: 'var(--t-border)', backdropFilter: 'blur(12px)' }}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <BrandLockup size={30} />
        <nav aria-label="Primary" className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <Link key={l.path} to={l.path} className="text-sm font-medium transition-opacity hover:opacity-80"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}>{l.label}</Link>
          ))}
        </nav>
        <Link to="/pricing" className="btn-primary hidden md:inline-flex">Get started <ArrowRight className="h-4 w-4" /></Link>
        <button onClick={() => setOpen(!open)} className="md:hidden p-2" aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="border-t px-6 py-3 md:hidden" style={{ borderColor: 'var(--t-border)' }}>
          {links.map((l) => (
            <Link key={l.path} to={l.path} onClick={() => setOpen(false)} className="block py-2 text-sm font-medium" style={{ color: 'var(--t-text)' }}>{l.label}</Link>
          ))}
        </div>
      )}
    </header>
  );
}
