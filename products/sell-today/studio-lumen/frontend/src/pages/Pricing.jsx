import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Check, ArrowRight, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Pricing() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              PRICING
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Clear pricing, no surprises
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Choose the portfolio plan that fits — upgrade, downgrade or cancel at any time.
            </p>
          </div>
        </section>

        <section className="pb-16">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
            <div className="card-panel p-8 h-full flex flex-col card-lift" data-reveal>
              
              <p className="section-eyebrow">Sprint</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>$9,000</span>
                <span className="text-sm text-slate-500 dark:text-slate-400 mb-1">per project</span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">A focused design sprint</p>
              <ul className="mt-6 space-y-3 grow">
                <li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Discovery workshop</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">One direction, refined</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Core brand kit</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Landing page design</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Two review rounds</span>
                </li>
              </ul>
              <Link
                to="/contact"
                className="btn-outline mt-8 inline-flex items-center justify-center gap-2 text-sm px-6 py-3"
              >
                Commission a Shoot <ArrowRight className="h-4 w-4" />
              </Link>
            </div><div className="card-panel p-8 h-full flex flex-col relative card-lift ring-2 ring-[var(--t-primary)]" data-reveal>
              <span
                className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full px-3 py-1 text-xs font-bold text-white"
                style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
              >
                Most popular
              </span>
              <p className="section-eyebrow">{t('Pricing.studio', t('Pricing.studio', 'Studio'))}</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>$28,000</span>
                <span className="text-sm text-slate-500 dark:text-slate-400 mb-1">per project</span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{t('Pricing.our_most_chosen_service', t('Pricing.our_most_chosen_service', 'Our most-chosen service'))}</p>
              <ul className="mt-6 space-y-3 grow">
                <li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Everything in Sprint</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Full identity system</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Website design & build</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Motion & asset library</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Brand guidelines</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">30-day post-launch support</span>
                </li>
              </ul>
              <Link
                to="/contact"
                className="btn-primary mt-8 inline-flex items-center justify-center gap-2 text-sm px-6 py-3"
              >
                Commission a Shoot <ArrowRight className="h-4 w-4" />
              </Link>
            </div><div className="card-panel p-8 h-full flex flex-col card-lift" data-reveal>
              
              <p className="section-eyebrow">Partner</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>{t('Pricing.custom', t('Pricing.custom', 'Custom'))}</span>
                <span className="text-sm text-slate-500 dark:text-slate-400 mb-1">retainer</span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Ongoing creative partner</p>
              <ul className="mt-6 space-y-3 grow">
                <li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Everything in Studio</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Embedded senior team</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Continuous design & QA</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Quarterly strategy</span>
                </li><li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">Priority scheduling</span>
                </li>
              </ul>
              <Link
                to="/contact"
                className="btn-outline mt-8 inline-flex items-center justify-center gap-2 text-sm px-6 py-3"
              >
                Commission a Shoot <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-4xl mx-auto px-6">
            <div className="glass-md rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-4 justify-center text-center sm:text-left" data-reveal>
              <ShieldCheck className="h-6 w-6 text-primary shrink-0" />
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Prices shown in USD and exclude local taxes. Every plan is backed by a
                straightforward guarantee — if it is not right for you, we will make it right.
              </p>
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
                Ready to start with Studio Lumen?
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
                  Commission a Shoot <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/services"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  View Galleries
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
