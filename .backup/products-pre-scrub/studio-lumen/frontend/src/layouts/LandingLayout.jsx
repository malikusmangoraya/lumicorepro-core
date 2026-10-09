import ButtonMotion from '@/components/ui/ButtonMotion';
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap } from 'lucide-react';

export default function LandingLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-accent-500/20 selection:text-accent-400">
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2 font-bold text-lg text-white">
            <svg viewBox="0 0 48 48" width="28" height="28" fill="none">
              <polygon
                points="24,4 42,14 42,34 24,44 6,34 6,14"
                fill="rgb(6, 182, 212)"
                opacity="0.95"
              />
              <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
            </svg>
            <span>
              Platform<span className="text-accent-400">Pro</span>
            </span>
          </Link>
          <nav
            className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300"
            aria-label="Primary"
          >
            <Link to="/" className="hover:text-accent-400 transition-colors">
              Home
            </Link>
            <Link to="/about" className="hover:text-accent-400 transition-colors">
              About
            </Link>
            <Link to="/services" className="hover:text-accent-400 transition-colors">
              Services
            </Link>
            <Link to="/contact" className="hover:text-accent-400 transition-colors">
              Contact
            </Link>
          </nav>
          <Link
            to="/contact"
            className="inline-flex items-center gap-1.5 rounded-xl bg-accent-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-accent-400 transition-all"
          >
            Get Started <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-slate-800 bg-slate-950 text-slate-400">
        <div className="max-w-7xl mx-auto px-6 py-14">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
            <div className="space-y-3">
              <span className="font-bold text-base text-white">
                Platform<span className="text-accent-400">Pro</span>
              </span>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enterprise fullstack web application platform with high performance and security
                built in.
              </p>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                All systems operational
              </div>
            </div>
            <div>
              <p className="font-semibold text-xs text-white uppercase tracking-wider mb-3">
                Product
              </p>
              <ul className="space-y-2 text-xs">
                <li>
                  <Link to="/services" className="hover:text-accent-400">
                    Features
                  </Link>
                </li>
                <li>
                  <Link to="/services" className="hover:text-accent-400">
                    Solutions
                  </Link>
                </li>
                <li>
                  <Link to="/services" className="hover:text-accent-400">
                    Pricing
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-xs text-white uppercase tracking-wider mb-3">
                Company
              </p>
              <ul className="space-y-2 text-xs">
                <li>
                  <Link to="/about" className="hover:text-accent-400">
                    About Us
                  </Link>
                </li>
                <li>
                  <Link to="/contact" className="hover:text-accent-400">
                    Contact
                  </Link>
                </li>
                <li>
                  <Link to="/privacy" className="hover:text-accent-400">
                    Privacy
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-xs text-white uppercase tracking-wider mb-3">
                Newsletter
              </p>
              <p className="text-xs text-slate-400 mb-2">Subscribe for latest updates.</p>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="work@company.com"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-white"
                />
                <ButtonMotion
                  type="button"
                  className="rounded-lg bg-accent-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-accent-500"
                >
                  Join
                </ButtonMotion>
              </div>
            </div>
          </div>
          <div className="pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <p>&copy; {new Date().getFullYear()} PlatformPro. All rights reserved.</p>
            <span className="flex items-center gap-1">
              <Zap className="h-3 w-3 text-accent-400" /> React 19 + Vite
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
