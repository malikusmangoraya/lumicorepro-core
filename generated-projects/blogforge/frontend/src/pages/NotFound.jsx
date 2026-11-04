import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowRight } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-6 py-24 text-center">
      <span className="inline-flex w-14 h-14 rounded-2xl items-center justify-center bg-brand-primary/15 border border-brand-primary/30 text-brand-accent mb-6">
        <Compass className="w-7 h-7" />
      </span>
      <p className="text-sm font-mono text-slate-500">404</p>
      <h1 className="mt-2 text-3xl font-extrabold text-white">This page was not generated</h1>
      <p className="mt-4 text-slate-400">
        The link may be outdated, or the page may have moved. The generator, history and credits are
        one click away.
      </p>
      <div className="mt-8 flex flex-col sm:flex-row justify-center gap-3">
        <Link
          to="/generate"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full font-semibold text-white bg-gradient-to-r from-brand-primary to-cyan-500 hover:opacity-95 transition-all duration-200"
        >
          Open workspace <ArrowRight className="w-4 h-4" />
        </Link>
        <Link
          to="/"
          className="inline-flex items-center justify-center px-6 py-3 rounded-full font-semibold text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors"
        >
          Back home
        </Link>
      </div>
    </div>
  );
}
