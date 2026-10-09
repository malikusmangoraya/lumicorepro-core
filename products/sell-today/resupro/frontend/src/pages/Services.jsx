import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Rocket, BarChart3, ShieldCheck, LayoutDashboard, Zap, Code, TrendingUp, ArrowRight, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const faqs = [
  { q: 'Is there a free plan?', a: 'Yes — the Starter plan is free forever, with no credit card required and no trial clock.' },
  { q: 'Can I self-host?', a: 'Enterprise customers can run the platform in their own cloud or on-premises environment.' },
  { q: 'How does billing work?', a: 'Per-seat monthly or annual billing. Annual plans save 20%, and you can change plans at any time.' },
  { q: 'What support is included?', a: 'Team includes priority support with published SLAs; Enterprise adds a named solutions engineer.' },
];

export default function Services() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(0);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              WHAT WE DO
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              ResuPro, in full
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              ResuPro turns outlines into investor-ready decks with smart layouts, brand systems and live analytics on every slide.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Rocket className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Deployment</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Ship from any CI to production in seconds, with rollback one click away.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <BarChart3 className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Analytics</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Real-time metrics that answer questions instead of just drawing charts.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <ShieldCheck className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Security</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">SSO, audit logs and role-based access enforced by default.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <LayoutDashboard className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Dashboards</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Custom views for every team, shareable and governed without friction.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">{t('Services.how_it_works', t('Services.how_it_works', 'How it works'))}</p>
              <h2 className="section-heading">{t('Services.a_process_built_to_remove_surprises', t('Services.a_process_built_to_remove_surprises', 'A process built to remove surprises'))}</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
              <div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Zap className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>1. Connect</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Connect your repo and existing tools in minutes — no migration project.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Code className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>2. Integrate</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Use the API and webhooks to fit the platform into how your team works.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <TrendingUp className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>3. Scale</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Grow from a side project to enterprise load without re-platforming.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-3xl mx-auto px-6">
            <div className="max-w-2xl mb-10">
              <p className="section-eyebrow">{t('Services.questions', t('Services.questions', 'Questions'))}</p>
              <h2 className="section-heading">{t('Services.answers_before_you_ask', t('Services.answers_before_you_ask', 'Answers before you ask'))}</h2>
            </div>
            <div className="space-y-3">
              {faqs.map((f, i) => (
                <div key={i} className="card-panel overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpen(open === i ? -1 : i)}
                    aria-expanded={open === i}
                    className="w-full flex items-center justify-between gap-4 p-5 text-left"
                  >
                    <span className="font-semibold text-sm" style={{ color: 'var(--t-heading)' }}>{f.q}</span>
                    <span className="text-primary text-xl leading-none">{open === i ? '−' : '+'}</span>
                  </button>
                  {open === i && (
                    <p className="px-5 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{f.a}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 card-lift"
              data-reveal
              style={{ background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)', boxShadow: '0 30px 60px rgba(0,0,0,0.25)' }}
            >
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Ready to start with ResuPro?
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Talk to the team, get a clear plan, and see exactly what the first step looks like.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3 text-sm font-bold transition-all duration-200 hover:-translate-y-0.5"
                  style={{ color: 'var(--t-primary)' }}
                >
                  Start Building <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/pricing"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  Templates
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
