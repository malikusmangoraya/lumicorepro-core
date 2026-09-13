import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Mail, CheckCircle2, Zap, ArrowUp } from 'lucide-react';
import UniqueLogo from '../common/UniqueLogo';

export default function ModernFooter({ projectName = 'LuminaCore' }) {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-5">
          <div className="lg:col-span-2 space-y-4">
            <UniqueLogo name={projectName} size="lg" />
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              Empowering next-generation digital experiences. Built with performance, security, and world-class design in mind.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              All systems operational &bull; 99.99%
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/pricing" className="hover:text-cyan-400 transition-colors">Pricing & Plans</Link></li>
              <li><Link to="/features" className="hover:text-cyan-400 transition-colors">Features & Solutions</Link></li>
              <li><Link to="/case-studies" className="hover:text-cyan-400 transition-colors">Case Studies</Link></li>
              <li><Link to="/enterprise" className="hover:text-cyan-400 transition-colors">Enterprise SLA</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/about" className="hover:text-cyan-400 transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-cyan-400 transition-colors">Contact</Link></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Privacy Policy</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Stay Updated</h4>
            <p className="text-xs text-slate-400 mb-3">Join our newsletter for weekly product updates and insights.</p>
            {subscribed ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="h-4 w-4" /> Subscribed successfully!
              </div>
            ) : (
              <form onSubmit={handleSubscribe} className="space-y-2">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter work email"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <button
                  type="submit"
                  className="w-full rounded-lg bg-cyan-600 px-3 py-2 text-xs font-semibold text-white hover:bg-cyan-500 transition-colors"
                >
                  Subscribe
                </button>
              </form>
            )}
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>&copy; {new Date().getFullYear()} {projectName}. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1"><Zap className="h-3.5 w-3.5 text-cyan-400" /> Powered by React 19 + Vite</span>
            <button onClick={scrollToTop} className="p-1.5 rounded-lg border border-slate-800 hover:text-white" aria-label="Scroll to top">
              <ArrowUp className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}