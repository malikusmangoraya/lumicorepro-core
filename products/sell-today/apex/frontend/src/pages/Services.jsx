import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BadgeCheck, ClipboardCheck, Gauge, KeyRound, Truck, Wrench } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const services = [
  { icon: ClipboardCheck, title: 'Independent inspection', desc: 'A qualified technician reviews the mechanical condition, roadworthiness and visible wear before a vehicle is presented.', perks: ['Written condition report', 'Inspection date recorded', 'Open findings explained'] },
  { icon: BadgeCheck, title: 'Provenance review', desc: 'We organize available ownership, service and vehicle-history records so you can review the evidence before making a decision.', perks: ['Documented service history', 'Ownership records reviewed', 'Known gaps disclosed'] },
  { icon: KeyRound, title: 'Private viewings', desc: 'Meet an advisor, inspect your shortlist and take the time to understand each vehicle in a considered setting.', perks: ['Appointment-led showroom', 'Vehicle walkaround', 'Questions answered in person'] },
  { icon: Gauge, title: 'Test-drive coordination', desc: 'Arrange a drive for eligible vehicles after confirming availability, licensing and insurance requirements.', perks: ['Availability confirmed first', 'Requirements shared in advance', 'Route planned with your advisor'] },
  { icon: Wrench, title: 'Ownership preparation', desc: 'Before collection, we coordinate agreed preparation items and explain what has been completed and what remains.', perks: ['Agreed work itemized', 'Completion status shared', 'No undisclosed modifications'] },
  { icon: Truck, title: 'Delivery coordination', desc: 'Discuss collection or delivery options with your advisor; timing, coverage and cost are confirmed before booking.', perks: ['Options for your location', 'Costs confirmed upfront', 'Handover checklist'] },
];

export default function Services() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1 px-6 py-16 lg:py-24">
        <section className="mb-14 max-w-3xl">
          <p className="section-eyebrow">Apex ownership</p>
          <h1 className="section-heading mt-3">The details matter as much as the drive.</h1>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-slate-500">
            From first inspection to handover, our team makes the information and next steps clear. Every vehicle and service is subject to availability and a vehicle-specific agreement.
          </p>
        </section>
        <section aria-label="Vehicle services" className="grid gap-0 border-y border-[var(--t-border)] md:grid-cols-2 lg:grid-cols-3">
          {services.map(({ icon: Icon, title, desc, perks }, index) => (
            <article key={title} className="border-b border-[var(--t-border)] py-8 md:px-7 md:even:border-l lg:nth-[3n+2]:border-l lg:nth-[3n+3]:border-l">
              <div className="flex items-start justify-between">
                <Icon className="h-6 w-6 text-[var(--t-primary)]" aria-hidden="true" />
                <span className="font-mono text-xs text-slate-400">0{index + 1}</span>
              </div>
              <h2 className="mt-6 text-xl font-semibold text-[var(--t-heading)]">{title}</h2>
              <p className="mt-3 min-h-20 text-sm leading-relaxed text-slate-500">{desc}</p>
              <ul className="mt-5 space-y-2 border-t border-[var(--t-border)] pt-4">
                {perks.map((perk) => <li key={perk} className="flex items-center gap-2 text-sm text-slate-600"><span className="h-1.5 w-1.5 rounded-full bg-[var(--t-primary)]" aria-hidden="true" />{perk}</li>)}
              </ul>
            </article>
          ))}
        </section>
        <section className="mt-16 flex flex-col items-start justify-between gap-6 bg-surface p-8 md:flex-row md:items-center lg:p-12">
          <div><p className="section-eyebrow">A conversation, not a commitment</p><h2 className="mt-3 text-2xl font-bold text-[var(--t-heading)]">Tell us what you are looking for.</h2><p className="mt-2 max-w-xl text-sm text-slate-500">Share your preferred model, budget and timing. An advisor will help you understand the next steps.</p></div>
          <Link to="/contact" className="btn-primary shrink-0">Speak with an advisor <ArrowRight className="h-4 w-4" /></Link>
        </section>
      </main>
      <Footer />
    </div>
  );
}
