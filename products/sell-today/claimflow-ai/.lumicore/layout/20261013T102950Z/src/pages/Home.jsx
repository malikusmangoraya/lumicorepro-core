import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, ClipboardCheck, FileText, ShieldCheck } from 'lucide-react';
import claimDesk from '../assets/images/hero-desk.jpg';
import claimTeam from '../assets/images/office-team.jpg';
import claimPapers from '../assets/images/cards.jpg';
import claimReview from '../assets/images/finance.jpg';
import Navbar from '../components/Navbar';
import {
  Cta,
  Faq,
  Features,
  Pricing,
  Problem,
  Results,
  Stats,
  Testimonials,
  UseCases,
} from '../components/sections/GrowthSections';
import Footer from '../components/Footer';

const workflow = [
  { icon: FileText, title: 'Guided claim intake', image: claimDesk, description: 'Collect the details relevant to the reported loss with a clear, policy-aware intake.' },
  { icon: ClipboardCheck, title: 'Evidence checklist', image: claimPapers, description: 'Show claimants and reviewers which documents are received and what is still needed.' },
  { icon: Bell, title: 'Status updates', image: claimTeam, description: 'Make progress and requested next steps easier for claimants to understand.' },
  { icon: ShieldCheck, title: 'Adjuster handoff', image: claimReview, description: 'Organize the claim file for review while keeping decisions with authorized professionals.' },
];

export default function Home() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
        <section className="relative isolate overflow-hidden py-16 lg:py-24">
          <div className="absolute inset-0 -z-10" aria-hidden="true">
            <img src={claimDesk} alt="" className="h-full w-full object-cover opacity-15" />
            <div className="absolute inset-0 bg-gradient-to-r from-[var(--t-background)] via-[var(--t-background)]/95 to-transparent" />
          </div>
          <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 lg:grid-cols-2">
            <div>
              <p className="section-eyebrow">Claims operations</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-extrabold leading-tight tracking-tight text-[var(--t-heading)] sm:text-5xl lg:text-6xl">
                {t('Home.headline', 'Move claims forward, with clarity at every step.')}
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600 dark:text-slate-300">
                {t('Home.lead', 'Guide claim intake, organize evidence and keep claimants informed in one understandable workflow.')}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary">Talk to our team <ArrowRight className="h-4 w-4" /></Link>
                <Link to="/services" className="btn-outline">Explore the workflow</Link>
              </div>
              <p className="mt-5 max-w-lg text-xs leading-relaxed text-slate-500">ClaimFlow supports claims operations. Coverage and settlement decisions remain with authorized insurance professionals.</p>
            </div>
            <div className="border border-[var(--t-border)] bg-surface/95 p-6 shadow-xl sm:p-8">
              <div className="flex items-center justify-between gap-4 border-b border-[var(--t-border)] pb-5">
                <div><p className="text-xs font-semibold uppercase tracking-widest text-[var(--t-primary)]">Example workflow</p><h2 className="mt-1 text-xl font-bold text-[var(--t-heading)]">A clear path to review</h2></div>
                <ClipboardCheck className="h-7 w-7 text-[var(--t-primary)]" aria-hidden="true" />
              </div>
              <ol className="mt-5 space-y-4">
                {workflow.map(({ title }, index) => <li key={title} className="flex items-center gap-4"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--t-primary)] text-sm font-bold text-white">{index + 1}</span><span className="text-sm font-medium text-[var(--t-heading)]">{title}</span></li>)}
              </ol>
              <p className="mt-6 border-t border-[var(--t-border)] pt-4 text-sm text-slate-500">One connected process. Clear ownership of every next step.</p>
            </div>
          </div>
        </section>

        <Stats />
        <Problem />
        <section className="mx-auto max-w-7xl px-6 py-20 lg:py-24" id="workflow">
          <div className="max-w-2xl"><p className="section-eyebrow">From first notice to review</p><h2 className="section-heading mt-3">A workflow people can follow.</h2><p className="mt-4 leading-relaxed text-slate-500 dark:text-slate-400">Give claimants a clear next step and help reviewers work from a more organized file.</p></div>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {workflow.map(({ icon: Icon, title, image, description }) => <article key={title} className="overflow-hidden border border-[var(--t-border)] bg-surface"><img src={image} alt="" className="h-40 w-full object-cover" loading="lazy"/><div className="p-5"><Icon className="h-6 w-6 text-[var(--t-primary)]" aria-hidden="true"/><h3 className="mt-4 font-semibold text-[var(--t-heading)]">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{description}</p></div></article>)}
          </div>
        </section>
        <section className="bg-surface py-16"><div className="mx-auto grid max-w-5xl gap-8 px-6 md:grid-cols-3"><div><p className="section-eyebrow">Designed for</p><h2 className="mt-3 text-2xl font-bold text-[var(--t-heading)]">Claim teams and the people they serve.</h2></div><p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">Help operations teams coordinate intake and evidence without relying on scattered email threads.</p><p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">Give claimants clearer progress updates and make requests easier to understand and respond to.</p></div></section>
        <Features />
        <UseCases />
        <Results />
        <Testimonials />
        <Pricing />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </div>
  );
}
