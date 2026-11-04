import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Feather, Layers, Lock, Gauge } from 'lucide-react';

const PRINCIPLES = [
  {
    icon: Gauge,
    title: 'Speed is a feature',
    body: 'A draft you can read while it is being written beats a spinner followed by a wall of text. Streaming is the default, not an add-on.',
  },
  {
    icon: Lock,
    title: 'Your content stays yours',
    body: 'Articles live in your database, under your account. There is no shared content pool and no lock-in on export formats.',
  },
  {
    icon: Layers,
    title: 'Boring where it matters',
    body: 'Credits are reserved atomically, JWTs are verified server-side, and every query is scoped to its owner. The interesting part is the writing.',
  },
];

export default function About() {
  return (
    <div className="pb-24">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 lg:pt-24">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
            <Feather className="w-3.5 h-3.5" /> About BlogForge
          </span>
          <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            A writing tool that respects the writer
          </h1>
          <p className="mt-6 text-lg text-slate-300 leading-relaxed">
            Most AI writing tools are a text box with a subscription attached. BlogForge started from a
            narrower question: what would a content engine look like if it were built like the rest of
            your stack — versioned schema, real auth, metered usage, exports that fit your CMS?
          </p>
          <p className="mt-4 text-slate-400 leading-relaxed">
            The result is a full-stack application you can run yourself. The generator is fast and
            focused, the metadata is structured instead of buried in prose, and every article is a
            first-class record you own.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        <div className="grid md:grid-cols-3 gap-6">
          {PRINCIPLES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="p-7 rounded-2xl bg-slate-900/60 border border-slate-800">
              <Icon className="w-7 h-7 text-brand-accent mb-4" />
              <h2 className="text-lg font-bold text-white mb-2">{title}</h2>
              <p className="text-sm text-slate-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        <div className="grid lg:grid-cols-2 gap-10 items-start">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">What is actually inside</h2>
            <p className="mt-4 text-slate-400 leading-relaxed">
              The package is not a demo shell. It contains the complete pipeline, documented and
              deployable on Vercel with a managed Postgres.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-slate-300">
              <li><span className="font-semibold text-white">Frontend</span> — React 19, Vite, Tailwind CSS, marked, lucide-react.</li>
              <li><span className="font-semibold text-white">API</span> — Express 4, Sequelize 6, Umzug migrations, JWT and bcrypt.</li>
              <li><span className="font-semibold text-white">Streaming</span> — Server-Sent Events with a documented frame contract.</li>
              <li><span className="font-semibold text-white">Database</span> — PostgreSQL with three versioned migrations and cascade-safe relations.</li>
              <li><span className="font-semibold text-white">AI</span> — one provider abstraction over OpenAI, OpenRouter, DeepSeek and Gemini, plus a keyless demo engine.</li>
            </ul>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-7">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Honest status</h3>
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="font-semibold text-white">Generation, history, credits</dt>
                <dd className="text-slate-400">Live and verified against the deployed API.</dd>
              </div>
              <div>
                <dt className="font-semibold text-white">Payments</dt>
                <dd className="text-slate-400">Top-ups are granted instantly in this build; connect a payment provider before charging.</dd>
              </div>
              <div>
                <dt className="font-semibold text-white">AI providers</dt>
                <dd className="text-slate-400">Demo mode is always available. Add a provider key for real model output.</dd>
              </div>
              <div>
                <dt className="font-semibold text-white">Data</dt>
                <dd className="text-slate-400">Stored in your PostgreSQL instance; deleting an article removes it permanently.</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        <div className="rounded-3xl border border-brand-primary/30 bg-gradient-to-br from-brand-primary/15 via-slate-900 to-slate-950 p-10 text-center">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Try it before you judge it</h2>
          <p className="mt-3 text-slate-300">No key, no card. Generate a full article in demo mode and export it.</p>
          <Link
            to="/register"
            className="mt-7 inline-flex items-center gap-2 px-7 py-3.5 rounded-full font-bold text-white bg-gradient-to-r from-brand-primary to-cyan-500 hover:opacity-95 transition-all duration-200"
          >
            Open the workspace <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
