import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

/** Home — LUMI_LAYOUT_V1 layout-engine generated for Meridian Capital. */
export default function Home() {
  const features = [{"title": "Case studies", "detail": "Problem, approach and outcome"}, {"title": "Process", "detail": "How the work actually gets made"}, {"title": "Capabilities", "detail": "What I can do for your team"}, {"title": "Contact", "detail": "Start a conversation"}];
  const stats = [{"value": "99.99%", "label": "Uptime"}, {"value": "<2s", "label": "Load Time"}, {"value": "10K+", "label": "Users"}, {"value": "4.9/5", "label": "Rating"}];
  const sections = ["Hero", "Skills", "Projects", "Experience", "Resume", "Testimonials", "Contact", "Social"];
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--t-canvas)', color: 'var(--t-text)' }}>
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Navbar />
      <main id="main-content">
        <section className="hero-aurora relative overflow-hidden">
          <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-24 lg:grid-cols-12 lg:py-32">
            <div className="lg:col-span-7">
              <p className="section-eyebrow">SELECTED WORK</p>
              <h1 className="mt-5 max-w-3xl text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl" style={{ color: 'var(--t-heading)' }}>
                Craft, evidence and impact
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed" style={{ color: 'var(--t-muted)' }}>A focused portfolio from Meridian Capital, showing process, craft and measurable results.</p>
              <div className="mt-9 flex flex-wrap gap-4">
                <Link to="/pricing" className="btn-primary">Get started <ArrowRight className="h-4 w-4" /></Link>
                <Link to="/contact" className="btn-outline">Talk to us</Link>
              </div>
            </div>
            <div className="lg:col-span-5">
              <div className="card-panel p-6">
                <p className="text-xs uppercase tracking-[.25em]" style={{ color: 'var(--t-primary)' }}>Meridian Capital</p>
                <ul className="mt-4 space-y-3">
                  {features.slice(0, 4).map((f) => (
                    <li key={f.title} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" style={{ color: 'var(--t-primary)' }} />{f.title}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>
        <section className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
          <div className="mb-10 max-w-2xl">
            <p className="section-eyebrow">What we build</p>
            <h2 className="section-heading mt-2" style={{ color: 'var(--t-heading)' }}>Everything you need, in one place.</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <article key={f.title} className="card-panel p-6">
                <h3 className="text-lg font-bold" style={{ color: 'var(--t-heading)' }}>{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--t-muted)' }}>{f.detail}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="py-16" style={{ backgroundColor: 'var(--t-surface)' }}>
          <div className="mx-auto grid max-w-7xl gap-8 px-6 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{s.value}</div>
                <div className="mt-1 text-sm" style={{ color: 'var(--t-muted)' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </section>
        <section className="mx-auto max-w-7xl px-6 py-20">
          <p className="section-eyebrow">Platform</p>
          <h2 className="section-heading mt-2 mb-8" style={{ color: 'var(--t-heading)' }}>Built as a complete system.</h2>
          <div className="flex flex-wrap gap-3">
            {sections.map((s) => (
              <span key={s} className="rounded-full border px-4 py-2 text-sm" style={{ borderColor: 'var(--t-border)', color: 'var(--t-muted)' }}>{s}</span>
            ))}
          </div>
        </section>
        <section className="mx-auto max-w-5xl px-6 py-20 text-center">
          <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>Ready to get started?</h2>
          <p className="mx-auto mt-4 max-w-xl" style={{ color: 'var(--t-muted)' }}>A focused portfolio from Meridian Capital, showing process, craft and measurable results.</p>
          <Link to="/pricing" className="btn-primary mt-7">Get started <ArrowRight className="h-4 w-4" /></Link>
        </section>
      </main>
      <Footer />
    </div>
  );
}
