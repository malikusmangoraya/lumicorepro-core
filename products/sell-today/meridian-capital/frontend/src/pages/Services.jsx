import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Wallet, TrendingUp, CreditCard, ShieldCheck, FileText, BadgeCheck, Zap, ArrowRight, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const faqs = [
  { q: 'Is my money protected?', a: 'Eligible deposits are protected under the relevant deposit-guarantee scheme, up to the statutory limit.' },
  { q: 'How long does opening an account take?', a: 'Most applications are approved within minutes; verification may add a short delay at peak times.' },
  { q: 'Are there fees for spending abroad?', a: 'Plus and Private customers spend fee-free worldwide at the interbank rate.' },
  { q: 'Can I close my account easily?', a: 'Yes — in-app, at any time, with balances transferred to an account of your choice.' },
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
              Meridian Capital, in full
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.
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
                  <Wallet className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Accounts & Savings</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Everyday accounts with automated savings rules and no hidden monthly fees.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <TrendingUp className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Investments</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Low-cost portfolios built around your goals, not a sales target.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <CreditCard className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Payments & Cards</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Instant virtual cards, real-time controls and spending insights that land immediately.</p>
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
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Bank-grade encryption, biometric access and proactive fraud monitoring.</p>
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
                  <FileText className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>1. Apply</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">A short online application — most customers are approved in minutes.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <BadgeCheck className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>2. Verify</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Identity checks handled securely, once, so you can move without friction later.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Zap className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>3. Activate</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Your account and card go live straight away, with support one tap away.</p>
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
                Ready to start with Meridian Capital?
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
                  Request Access <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/pricing"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  Our Approach
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
