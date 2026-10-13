import React from 'react';
import { ArrowRight, BadgeCheck, BookOpenCheck, Compass, Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const values = [
  { icon: Compass, title: 'Choose with confidence', desc: 'We help buyers compare the details that matter: condition, history, specification and how a car fits the way they drive.' },
  { icon: BookOpenCheck, title: 'Evidence before adjectives', desc: 'Vehicle information is presented with supporting records where available, and known gaps are discussed rather than glossed over.' },
  { icon: Wrench, title: 'Respect the engineering', desc: 'Our specialists take time to understand each vehicle’s character, maintenance needs and intended use.' },
  { icon: BadgeCheck, title: 'A considered handover', desc: 'From your first viewing to collection, we keep the process personal, clear and grounded in the specific vehicle.' },
];

export default function About() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1">
        <section className="grid border-b border-[var(--t-border)] lg:min-h-[480px] lg:grid-cols-12">
          <div className="flex flex-col justify-center px-6 py-16 lg:col-span-7 lg:px-16 lg:py-24">
            <p className="section-eyebrow">About Apex</p>
            <h1 className="section-heading mt-4">A better way to find your next drive.</h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-500">
              Apex Motor Collective brings together distinctive performance and collector vehicles with the people who will value them. We pair a carefully curated collection with clear information and personal guidance, so the decision remains yours—and feels right.
            </p>
            <Link to="/services" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-[var(--t-primary)]">How we help <ArrowRight className="h-4 w-4" /></Link>
          </div>
          <div className="relative min-h-72 bg-surface lg:col-span-5 lg:min-h-full">
            <img src="/images/scene-2.jpg" alt="A performance car prepared for a private showroom viewing" className="absolute inset-0 h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" aria-hidden="true" />
            <p className="absolute bottom-6 left-6 max-w-xs text-sm text-white">The right car is more than a specification. It is a feeling you recognize.</p>
          </div>
        </section>
        <section className="px-6 py-20 lg:px-12 lg:py-24">
          <div className="max-w-2xl"><p className="section-eyebrow">What guides us</p><h2 className="section-heading mt-3">Built on trust, detail and a genuine love of driving.</h2></div>
          <div className="mt-12 grid border-t border-[var(--t-border)] sm:grid-cols-2 lg:grid-cols-4">
            {values.map(({ icon: Icon, title, desc }, index) => <article key={title} className="border-b border-[var(--t-border)] py-7 sm:px-5 sm:nth-[2n]:border-l lg:border-b-0 lg:nth-[2n]:border-l-0 lg:nth-[4n+2]:border-l lg:nth-[4n+3]:border-l"><span className="font-mono text-xs text-slate-400">0{index + 1}</span><Icon className="mt-5 h-6 w-6 text-[var(--t-primary)]" aria-hidden="true"/><h3 className="mt-4 font-semibold text-[var(--t-heading)]">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500">{desc}</p></article>)}
          </div>
        </section>
        <section className="mx-6 mb-20 flex flex-col justify-between gap-6 bg-surface p-8 md:mx-12 md:flex-row md:items-center lg:p-12">
          <div><p className="section-eyebrow">Start a conversation</p><h2 className="mt-3 text-2xl font-bold text-[var(--t-heading)]">Tell us what you would love to drive.</h2></div>
          <Link to="/contact" className="btn-primary shrink-0">Meet your advisor <ArrowRight className="h-4 w-4" /></Link>
        </section>
      </main>
      <Footer />
    </div>
  );
}
