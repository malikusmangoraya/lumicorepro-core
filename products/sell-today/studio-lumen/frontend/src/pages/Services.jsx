import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { PenTool, Code, Film, Camera, MessagesSquare, Layers, Rocket, ArrowRight, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const faqs = [
  { q: 'How long does a project take?', a: 'A sprint runs two to three weeks. Full identity and site projects typically run six to ten weeks.' },
  { q: 'Who owns the work?', a: 'You do — full IP transfers on final payment, along with source files and guidelines.' },
  { q: 'Do you work with startups?', a: 'Yes. We reserve capacity each quarter for early-stage founders and can stage payments.' },
  { q: 'Can you work with our in-house team?', a: 'Often the best arrangement. We embed alongside your team and hand over cleanly.' },
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
              Studio Lumen, in full
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Studio Lumen is a photographer\'s collective documenting architecture, people and wilderness in the warmest hour of the day.
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
                  <PenTool className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Brand & Identity</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Naming, identity systems and guidelines that hold up from a favicon to a billboard.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Code className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Web & Product</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Design and build of marketing sites and product interfaces, shipped by the team that designed them.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Film className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Motion & Film</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Brand films, product motion and social cutdowns directed end to end.</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Camera className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Photography</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">Art-directed stills for launch campaigns, product and editorial.</p>
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
                  <MessagesSquare className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>{t('Services.1_discover', t('Services.1_discover', '1. Discover'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">We interrogate the brief, the market and the competition before a single pixel moves.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Layers className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>2. Design</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Concepts, systems and iterations, reviewed with you in the open — no big reveal.</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Rocket className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>3. Launch</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">Build, handover and support, so the work survives contact with the real world.</p>
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
                  to="/pricing"
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
