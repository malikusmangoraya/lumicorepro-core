import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import UniqueLogo from './UniqueLogo';

export default function Footer() {
  const [email, setEmail] = useState('');
  const [sub, setSub] = useState(false);
  return (
    <footer className="text-white" style={{ backgroundColor: '#1f2937' }}>
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-4">
          <div className="space-y-4">
            <UniqueLogo />
            <p className="text-sm text-slate-300 leading-relaxed max-w-xs">
              Building exceptional digital products with performance, security, and design excellence.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Operational
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/services" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">Case Studies</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Enterprise</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/about" className="hover:text-white transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Stay Updated</h4>
            <p className="text-xs text-slate-300 mb-3">Weekly product updates and insights.</p>
            {sub ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="h-4 w-4" /> Subscribed!
              </div>
            ) : (
              <form onSubmit={e => { e.preventDefault(); if (email) setSub(true); } } className="space-y-2">
                <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="Email address" className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-slate-400 focus:border-white/40 focus:outline-none" />
                <button type="submit" className="w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition-colors" style={{ backgroundColor: '#dc2626' }}>
                  Subscribe
                </button>
              </form>
            )}
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>&copy; {new Date().getFullYear()} FoodExpress. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-white">Twitter</a>
            <a href="#" className="hover:text-white">LinkedIn</a>
            <a href="#" className="hover:text-white">GitHub</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
