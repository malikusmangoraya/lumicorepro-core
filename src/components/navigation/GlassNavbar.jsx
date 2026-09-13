import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sparkles, ArrowRight } from 'lucide-react';
import UniqueLogo from '../common/UniqueLogo';

export default function GlassNavbar({ projectName = 'LuminaCore' }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const links = [
    { path: '/', label: 'Home' },
    { path: '/features', label: 'Features' },
    { path: '/pricing', label: 'Pricing' },
    { path: '/marketplace', label: 'Marketplace' },
    { path: '/about', label: 'About' },
    { path: '/contact', label: 'Contact' },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <UniqueLogo name={projectName} size="md" />

        <div className="hidden md:flex items-center gap-8">
          <div className="flex items-center gap-6">
            {links.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={location.pathname === link.path
                  ? "text-sm font-semibold text-cyan-400"
                  : "text-sm font-medium text-slate-300 hover:text-white transition-colors"}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <Link
            to="/pricing"
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all active:scale-95"
          >
            Get Started <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden mt-4 pt-4 border-t border-slate-800 flex flex-col gap-3">
          {links.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileOpen(false)}
              className="px-2 py-1.5 text-slate-300 hover:text-cyan-400 font-medium"
            >
              {link.label}
            </Link>
          ))}
          <Link
            to="/pricing"
            onClick={() => setMobileOpen(false)}
            className="mt-2 text-center rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-white"
          >
            Get Started
          </Link>
        </div>
      )}
    </nav>
  );
}