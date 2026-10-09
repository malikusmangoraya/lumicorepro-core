import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Award, Zap, Users, Check, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const stats = [
  { value: '350+', label: 'Events produced' },
  { value: '48h', label: 'Fastest turnaround' },
  { value: '99%', label: 'On-time openings' },
  { value: '12', label: 'Awards' },
];

export default function About() {
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
              EVENT PRODUCTION
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Unforgettable is the minimum.
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Nuage Events designs and produces live experiences — launches, festivals and galas — where every second is choreographed.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
            <div>
              <h2 className="section-heading">{t('About.a_brand_built_on_standards', t('About.a_brand_built_on_standards', 'A brand built on standards'))}</h2>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">
                <strong style={{ color: 'var(--t-heading)' }}>Nuage Events</strong> produces live experiences where the audience leaves having felt something. We take on the impossible logistics, choreograph them to the second, and hand you a show that runs whether or not the lights decide to cooperate.
              </p>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">We exist to make entertainment feel effortless and worth recommending — measured by results, retained by trust, and built to an international standard.</p>
              <ul className="mt-8 space-y-3">
                <li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>Choreographed to the second</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>Production palettes of light</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>Logistics that never break</span>
                </li>
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>350+</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Events produced</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>48h</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Fastest turnaround</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>99%</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">On-time openings</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>12</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Awards</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('About.what_guides_us', t('About.what_guides_us', 'What guides us'))}</p>
              <h2 className="section-heading">{t('About.principles_we_do_not_trade_away', t('About.principles_we_do_not_trade_away', 'Principles we do not trade away'))}</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Award className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Award-Winning</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Recognised productions across launches, festivals and galas.</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Zap className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>On-Time, Every Time</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Doors open when we say they will — programming rehearsed to the cue.</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Users className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Specialist Crew</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Sound, light and stage specialists who have worked the biggest stages.</p>
              </div>
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
                Ready to start with Nuage Events?
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
                  Plan an Event <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/services"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  See Past Events
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
