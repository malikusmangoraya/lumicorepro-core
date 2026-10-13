import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import BrandLockup from './brand/BrandLockup';
import { BRAND } from './brand/BRAND';

/** Footer — layout-engine generated (multi-column, live status). */
export default function Footer() {
  const sections = ["Hero", "Features", "Pricing", "Comparison", "Dashboard", "Integrations"];
  return (
    <footer className="text-white" style={{ backgroundColor: 'var(--t-footerBg)' }}>
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-16 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-4">
          <BrandLockup size={30} dark />
          <p className="max-w-xs text-sm leading-relaxed text-white/70">Software that scales with you</p>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />99.99% Operational
          </div>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">Product</h4>
          <ul className="space-y-2 text-sm text-white/70">
            {sections.slice(0, 4).map((s) => (<li key={s}><Link to="/" className="hover:text-white">{s}</Link></li>))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">Company</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/about" className="hover:text-white">About</Link></li>
            <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
            <li><Link to="/privacy" className="hover:text-white">Privacy</Link></li>
            <li><Link to="/terms" className="hover:text-white">Terms</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider">Stay updated</h4>
          <p className="mb-3 text-xs text-white/60">Product news and insights.</p>
          <form onSubmit={(e) => e.preventDefault()} className="flex gap-2">
            <input type="email" required placeholder="Email address" aria-label="Email address"
              className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-white/50 focus:outline-none" />
            <button type="submit" className="rounded-lg bg-white/15 px-3 py-2 text-xs font-semibold text-white">Join</button>
          </form>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-300"><CheckCircle2 className="h-4 w-4" /> GDPR-ready</div>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-white/60">
          <span>© 2026 Flowpilot — Software that scales with you</span>
          <span>React 19 · Vite · Tailwind</span>
        </div>
      </div>
    </footer>
  );
}
