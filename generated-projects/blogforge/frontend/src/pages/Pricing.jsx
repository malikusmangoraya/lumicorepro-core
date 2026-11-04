import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ArrowRight, Sparkles, Coins } from 'lucide-react';
import { translate, useLocale } from '../i18n.js';

const PLANS = [
  {
    name: 'Starter',
    evaluationKey: 'evaluationStarter',
    credits: '50 evaluation credits',
    blurb: 'Enough to run the full workflow and publish your first posts.',
    features: [
      '50 evaluation credits on signup',
      'Full streaming generator',
      'SEO metadata on every draft',
      'Markdown, .md and HTML export',
      'Article history',
    ],
    highlight: false,
  },
  {
    name: 'Creator',
    evaluationKey: 'evaluationCreator',
    credits: '500 evaluation credits',
    blurb: 'An evaluation tier for exploring a steady publishing workflow.',
    features: [
      '500 evaluation credits',
      'Everything in Starter',
      'Long-form (about 2,200-word) articles',
      'Priority streaming queue',
      'Evaluation credit allocation only',
    ],
    highlight: true,
  },
  {
    name: 'Studio',
    evaluationKey: 'evaluationStudio',
    credits: '2,000 evaluation credits',
    blurb: 'An evaluation tier for exploring higher-volume team workflows.',
    features: [
      '2,000 evaluation credits',
      'Everything in Creator',
      'Higher evaluation credit allocation',
      'Unlimited history and exports',
      'Single evaluation workspace',
    ],
    highlight: false,
  },
];

export default function Pricing() {
  const locale = useLocale();

  return (
    <div className="pb-24">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 lg:pt-20 text-center">
        <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
          <Coins className="w-3.5 h-3.5" /> Evaluation credits
        </span>
        <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
          Evaluation credit tiers
        </h1>
        <p className="mt-5 text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          These tiers describe evaluation credits, not products for sale. One credit is one generation
          attempt; payment checkout is not enabled.
        </p>
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-14">
        <p role="status" className="mb-6 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
          {translate(locale, 'evaluationPricing')}
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-3xl p-7 flex flex-col ${
                plan.highlight
                  ? 'bg-slate-900 border-2 border-brand-primary shadow-xl shadow-brand-primary/10'
                  : 'bg-slate-900/60 border border-slate-800'
              }`}
            >
              {plan.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-brand-primary text-white">
                  <Sparkles className="w-3 h-3" /> Evaluation tier
                </span>
              )}
              <h2 className="text-lg font-bold text-white">{plan.name}</h2>
              <p className="mt-3 text-2xl font-extrabold text-white">{plan.credits}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-amber-300">
                {translate(locale, plan.evaluationKey)}
              </p>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">{plan.blurb}</p>

              <ul className="mt-6 space-y-2.5 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                to="/register"
                className={`mt-7 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-bold transition-all duration-200 ${
                  plan.highlight
                    ? 'text-white bg-gradient-to-r from-brand-primary to-cyan-500 hover:opacity-95'
                    : 'text-slate-200 bg-slate-800 hover:bg-slate-700'
                }`}
              >
                {translate(locale, 'evaluationCta')} <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400 leading-relaxed">
          <p>
            <span className="font-semibold text-slate-200">How credits work:</span> one credit is reserved
            atomically before a generation starts and refunded automatically if the provider fails. Your
            balance is visible in the workspace sidebar and on the credits page.
          </p>
          <p className="mt-3">
            <span className="font-semibold text-slate-200">Evaluation notice:</span> credit top-ups are
            granted by this evaluation build and do not trigger payment. These tiers are not available paid
            plans.
          </p>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        <h2 className="text-2xl font-extrabold text-white text-center">Included in the evaluation</h2>
        <div className="mt-8 grid sm:grid-cols-2 gap-4">
          {[
            'Streaming generation with live preview',
            'Meta title, description and keyword extraction',
            'History with reopen and delete',
            'Markdown and standalone HTML export',
            'Demo mode when no provider key is set',
            'JWT auth with per-user data isolation',
          ].map((item) => (
            <div key={item} className="flex items-start gap-2.5 rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
