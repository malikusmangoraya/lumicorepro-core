import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BarChart3,
  Check,
  CheckCircle2,
  FileText,
  History,
  PenLine,
  ShieldCheck,
  Sparkles,
  WandSparkles,
  Zap,
} from 'lucide-react';

const WORKFLOW = [
  {
    icon: PenLine,
    step: '01',
    title: 'Brief the idea',
    body: 'Start with a keyword, audience, tone, and length. No blank-page anxiety.',
  },
  {
    icon: WandSparkles,
    step: '02',
    title: 'Shape the draft',
    body: 'Watch a structured article stream live while you stay in control of the voice.',
  },
  {
    icon: FileText,
    step: '03',
    title: 'Publish anywhere',
    body: 'Export clean Markdown or HTML with SEO metadata ready for your CMS.',
  },
];

const TRUST_POINTS = ['50 evaluation credits', 'No payment checkout', 'Demo mode included'];

export default function Home() {
  return (
    <div className="min-h-screen overflow-hidden">
      <section className="relative isolate px-4 pb-20 pt-16 sm:px-6 sm:pt-24 lg:px-8 lg:pb-28 lg:pt-28">
        <div className="hero-orbit hero-orbit-one" aria-hidden="true" />
        <div className="hero-orbit hero-orbit-two" aria-hidden="true" />
        <div className="mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-[1.04fr_0.96fr] lg:gap-20">
          <div className="relative z-10">
            <div className="eyebrow animate-fade-in">
              <span className="eyebrow-dot"><Sparkles className="h-3.5 w-3.5" /></span>
              AI writing workspace
            </div>
            <h1 className="hero-title mt-7 max-w-3xl animate-fade-in">
              A better way to <span>publish consistently.</span>
              <br />
              Keep your <span>momentum.</span>
            </h1>
            <p className="hero-copy mt-7 max-w-xl animate-fade-in">
              Turn one idea into a structured, search-ready article without starting from a blank page. BlogForge streams the draft, keeps your voice in focus, and leaves you with content ready for your CMS.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row animate-fade-in">
              <Link to="/register" className="button-primary justify-center">
                Generate your first article <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/features" className="button-secondary justify-center">
                See how it works
              </Link>
            </div>
            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-400" aria-label="Evaluation benefits">
              {TRUST_POINTS.map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="relative z-10 lg:translate-y-2">
            <div className="preview-window animate-fade-in" aria-label="Live article preview">
              <div className="preview-window-bar">
                <div className="flex items-center gap-2">
                  <span className="window-dot bg-rose-400" />
                  <span className="window-dot bg-amber-300" />
                  <span className="window-dot bg-emerald-400" />
                </div>
                <span className="preview-status"><span /> Streaming preview</span>
              </div>
              <div className="p-6 sm:p-8">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-accent">SEO article</p>
                    <h2 className="mt-3 text-xl font-bold leading-tight text-white sm:text-2xl">A practical guide to smarter content workflows</h2>
                  </div>
                  <div className="hidden h-11 w-11 shrink-0 place-items-center rounded-2xl bg-brand-primary/15 text-brand-accent sm:grid"><Zap className="h-5 w-5" /></div>
                </div>
                <div className="mt-8 space-y-3" aria-hidden="true">
                  <div className="preview-line w-full" />
                  <div className="preview-line w-11/12" />
                  <div className="preview-line w-4/5" />
                </div>
                <div className="mt-8 flex flex-wrap gap-2">
                  <span className="preview-chip"><Check className="h-3 w-3" /> Structured outline</span>
                  <span className="preview-chip"><Check className="h-3 w-3" /> SEO metadata</span>
                  <span className="preview-chip"><Check className="h-3 w-3" /> Export-ready</span>
                </div>
              </div>
            </div>
            <div className="preview-note"><BarChart3 className="h-4 w-4 text-emerald-400" /> 50 credits included for evaluation</div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-800/80 bg-slate-900/35 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 text-sm text-slate-400">
          <span className="font-semibold text-slate-200">A calmer way to create content</span>
          <div className="flex flex-wrap gap-x-6 gap-y-2"><span>Live streaming</span><span>SEO structure</span><span>Private workspace</span><span>Portable exports</span></div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
        <div className="max-w-2xl">
          <p className="section-kicker">The complete workflow</p>
          <h2 className="section-title mt-3">One article, from brief to publish-ready</h2>
          <p className="sr-only">Built for the whole workflow</p>
          <p className="section-copy mt-4">Every step is designed to remove friction without hiding the decisions that make your content yours.</p>
        </div>
        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {WORKFLOW.map(({ icon: Icon, step, title, body }) => (
            <article key={step} className="feature-card group">
              <div className="flex items-start justify-between"><span className="step-number">{step}</span><Icon className="h-6 w-6 text-brand-accent transition-transform duration-300 group-hover:scale-110" aria-hidden="true" /></div>
              <h3 className="mt-12 text-xl font-bold text-white">{title}</h3>
              <p className="mt-3 leading-relaxed text-slate-400">{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-slate-800/80 bg-slate-900/25 px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <div><p className="section-kicker">Built for trust</p><h2 className="section-title mt-3">Your workflow stays yours.</h2><p className="section-copy mt-4">Save drafts in your workspace, keep your content portable, and export when you are ready. The evaluation build is honest about what is enabled.</p></div>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              [ShieldCheck, 'Private by default', 'JWT auth and a dedicated workspace for your articles.'],
              [History, 'Never lose a draft', 'Return to history, restore a draft, or remove it when finished.'],
              [FileText, 'Clean exports', 'Markdown and standalone HTML that fit your existing publishing stack.'],
              [Zap, 'Fast feedback', 'Stream content as it is generated instead of waiting in the dark.'],
            ].map(([Icon, title, body]) => <div key={title} className="mini-card"><Icon className="h-5 w-5 text-brand-accent" /><div><h3 className="font-semibold text-white">{title}</h3><p className="mt-1 text-sm leading-relaxed text-slate-400">{body}</p></div></div>)}
          </div>
        </div>
      </section>

      <section className="px-4 py-20 text-center sm:px-6 lg:py-28">
        <div className="cta-panel mx-auto max-w-4xl"><p className="section-kicker">A practical writing partner for every team</p><p className="sr-only">Questions, answered</p><h2 className="section-title mt-3">Make your next article easier.</h2><p className="mx-auto mt-4 max-w-2xl text-slate-400">Create an account to test generation, history, and exports with included evaluation credits.</p><Link to="/register" className="button-primary mt-8">Create your account <ArrowRight className="h-4 w-4" /></Link></div>
      </section>
    </div>
  );
}
