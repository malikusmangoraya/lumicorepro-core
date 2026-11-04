import React from 'react';
import { Activity, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import UniqueLogo from './UniqueLogo.jsx';

const HEALTH_URL = 'https://blogforge-api.vercel.app/api/v1/health';

export default function ModernFooter({ brand = 'BlogForge' }) {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 pt-16 pb-10" aria-label="Site footer">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.35fr_0.8fr_0.8fr_0.8fr]">
          <div>
            <Link to="/" className="inline-flex items-center gap-3" aria-label={`${brand} home`}><UniqueLogo size="h-8 w-8" /><span className="text-xl font-extrabold text-white">{brand}</span></Link>
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-slate-400">An AI writing workspace for structured articles, live drafting, and portable publishing exports.</p>
            <a href={HEALTH_URL} target="_blank" rel="noreferrer" className="mt-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition-colors hover:bg-emerald-500/20"><span className="h-2 w-2 rounded-full bg-emerald-400" /><Activity className="h-3.5 w-3.5" /> API health check <ArrowUpRight className="h-3 w-3" /></a>
          </div>
          <FooterColumn title="Product" links={[["Generator", '/generate'], ['History', '/generate/history'], ['Credits', '/generate/credits'], ['Features', '/features'], ['Pricing', '/pricing']]} />
          <FooterColumn title="Company" links={[["About", '/about'], ['Contact', '/contact'], ['Privacy policy', '/privacy'], ['Terms of service', '/terms']]} />
          <div><h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Trust</h2><div className="mt-5 space-y-3 text-sm text-slate-400"><p className="flex gap-2"><ShieldCheck className="h-4 w-4 shrink-0 text-slate-500" /> JWT auth and parameterized SQL</p><p>Evaluation credits only. No paid checkout is enabled.</p></div></div>
        </div>
        <div className="mt-14 flex flex-col gap-3 border-t border-slate-800 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between"><p>© 2026 {brand}. All rights reserved.</p><p>React · Express · PostgreSQL</p></div>
      </div>
    </footer>
  );
}

function FooterColumn({ title, links }) {
  return <div><h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{title}</h2><ul className="mt-5 space-y-3 text-sm text-slate-400">{links.map(([label, href]) => <li key={href}><Link to={href} className="transition-colors hover:text-white">{label}</Link></li>)}</ul></div>;
}
