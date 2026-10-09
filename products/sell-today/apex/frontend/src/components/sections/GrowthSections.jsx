import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Quote, Check, ChevronDown, ArrowRight, ShieldCheck } from 'lucide-react';

/**
 * Conversion sections for Apex Digital.
 *
 * Generated from the product's own brand entry, so the numbers and the feature
 * copy always match the rest of the identity. Every section is exported
 * separately and takes no props - drop them into any page, in any order.
 */

const STATS = [{ value: '38%', label: 'More qualified pipeline', numeric: '38', prefix: '', suffix: '%' }, { value: '2.4x', label: 'Faster lead response', numeric: '2.4', prefix: '', suffix: 'x' }, { value: '11 days', label: 'Faster time to first value', numeric: '11', prefix: '', suffix: ' days' }, { value: '99.98%', label: 'Platform uptime', numeric: '99.98', prefix: '', suffix: '%' }];

const FEATURES = [{ title: 'Account Intent Scoring', desc: 'Scored on the signals that actually close' }, { title: 'Sequence Automation', desc: 'Sequences that stop the moment a deal goes quiet' }, { title: 'Multi-Touch Attribution', desc: 'One attribution model everyone agrees on' }, { title: 'Revenue Forecasting', desc: 'Apex Digital turns scattered intent data into a forecast the whole revenue team trusts - account scoring, sequence automation and attribution in one workspace.' }];

const USE_CASES = [{ title: 'Teams already doing the work by hand', desc: 'You have a process that works. It just runs on one person\'s memory and a spreadsheet nobody else can read.' }, { title: 'Buyers comparing three vendors', desc: 'When a decision takes weeks, the deal is usually lost to whoever answered first. Speed is the differentiator.' }, { title: 'Multi-market operations', desc: 'Different regions, currencies and rules. One workspace, one source of truth, no per-market spreadsheet.' }, { title: 'Anyone who needs the numbers to hold up', desc: 'Board packs, audits, client reporting - figures that survive being questioned, with the source one click away.' }];

const RESULTS = [{ title: 'Time to first value', desc: 'One working session, not one quarter. Import what you have and the first useful report builds itself.' }, { title: 'Hours returned per month', desc: 'The reconciliation, chasing and re-keying that used to eat the first week of every month.' }, { title: 'Confidence in the number', desc: 'One definition, agreed once and applied everywhere, so nobody argues about the figure again.' }];

const TIERS = [{ name: 'Starter', blurb: 'For one team proving the workflow end to end.', price: '$29', points: ['1 workspace', 'Up to 3 seats', '1,000 records', 'Community support'] }, { name: 'Growth', blurb: 'For teams running the whole pipeline every day.', price: '$89', points: ['Everything in Starter', 'Up to 15 seats', 'Unlimited records', 'Automation workflows', 'Priority email support'] }, { name: 'Scale', blurb: 'For organisations with compliance and audit needs.', price: '$249', points: ['Everything in Growth', 'Unlimited seats', 'SSO & audit log', 'Custom data retention', 'Dedicated success manager'] }];

const FAQS = [{ q: 'How long does setup take?', a: 'Most teams are live in a single afternoon. Connect the tools you already use, import what you have, and the first report builds itself.' }, { q: 'Do I need a credit card to start?', a: 'No. The free tier covers a real workload and never expires, so you can prove value before spending anything.' }, { q: 'Can I cancel at any time?', a: 'Yes. Cancel from billing settings and you keep access until the end of the period you paid for. No cancellation fee, no minimum term.' }, { q: 'Is my data portable?', a: 'Export everything to CSV or JSON whenever you want, including schema and history. No lock-in, no proprietary formats.' }, { q: 'What happens to my data if I leave?', a: 'It is yours. We export on request and delete it on a published schedule after your account closes - never silently, and never before the notice period you are entitled to.' }, { q: 'What support is included?', a: 'Every plan includes email support with a one-business-day target, plus the documentation and migration guides. Priority support is included from Growth upwards.' }];

const TESTIMONIALS = [{ quote: 'We replaced three tools with Apex Digital and cut our reporting time in half. The team actually enjoys using it.', name: 'Amara Osei', role: 'Head of Operations', company: 'Series B fintech' }, { quote: 'Onboarding took an afternoon. By Friday the leadership team had answers it had been waiting months for.', name: 'Daniel Reyes', role: 'Revenue Director', company: 'B2B software' }, { quote: 'The clearest product in this category. It does the job, it does not try to be everything to everyone.', name: 'Priya Raman', role: 'Product Lead', company: 'Professional services' }];

const SHELL = 'max-w-7xl mx-auto px-6';

/** Trust bar: the numbers a buyer checks before the first click. */
export function Stats() {
  return (
    <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
      <div className={SHELL}>
        <dl className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          {STATS.map((s) => (
            <div key={s.label}>
              <dt className="sr-only">{s.label}</dt>
              <dd
                className="text-3xl sm:text-4xl font-black tracking-tight"
                style={{ color: 'var(--t-heading)' }}
                data-count={s.numeric}
                data-count-prefix={s.prefix}
                data-count-suffix={s.suffix}
                data-count-final={s.value}
              >
                {s.value}
              </dd>
              <dd className="mt-2 text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">
                {s.label}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

/** Name the problem in the buyer's own words before offering the fix. */
export function Problem() {
  return (
    <section className="py-20 lg:py-24">
      <div className={SHELL}>
        <div className="max-w-3xl">
          <p className="section-eyebrow">The problem</p>
          <h2 className="section-heading">The tools are bought, the results never arrive</h2>
          <p className="mt-4 text-slate-500 dark:text-slate-400 leading-relaxed">
            Most teams buy a new platform, spend a quarter wiring it up, and go quietly back to the spreadsheet it was meant to replace. The gap between signing and first value is where the churn happens - and it is almost always a data problem, not a people problem.
          </p>
        </div>
      </div>
    </section>
  );
}

/** What the product does, stated as outcomes rather than features. */
export function Features() {
  return (
    <section className="py-20 lg:py-28" id="features">
      <div className={SHELL}>
        <p className="section-eyebrow">Capabilities</p>
        <h2 className="section-heading">What working with Apex Digital looks like</h2>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="card-panel p-7 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-white mb-4"
                style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
              >
                <Check className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                {f.title}
              </h3>
              <p className="mt-2 text-slate-500 dark:text-slate-400 leading-relaxed">
                {f.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Who it is for. Narrowing the audience is what makes the page convert. */
export function UseCases() {
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="use-cases">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">Who it is for</p>
          <h2 className="section-heading">Made for teams like yours</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {USE_CASES.map((u) => (
            <article
              key={u.title}
              className="card-panel p-6 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <h3 className="font-bold" style={{ color: 'var(--t-heading)' }}>
                {u.title}
              </h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {u.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Results a buyer can take to a board meeting. */
export function Results() {
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="results">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">By the numbers</p>
          <h2 className="section-heading">Results you can put in a report</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {RESULTS.map((r) => (
            <article
              key={r.title}
              className="card-panel p-7 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <h3
                className="font-black tracking-tight text-lg"
                style={{ color: 'var(--t-primary)' }}
              >
                {r.title}
              </h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {r.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Named social proof - quotes and a visible rating. */
export function Testimonials() {
  return (
    <section className="py-20 lg:py-24" id="customers">
      <div className={SHELL}>
        <div className="text-center max-w-2xl mx-auto">
          <p className="section-eyebrow">Customer stories</p>
          <h2 className="section-heading">Teams ship faster with Apex Digital</h2>
          <div
            className="mt-4 flex items-center justify-center gap-1"
            aria-label="Rated 4.9 out of 5"
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <Star key={i} className="h-5 w-5 fill-current text-amber-400" aria-hidden="true" />
            ))}
            <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
              4.9 / 5 average
            </span>
          </div>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((q) => (
            <figure
              key={q.name}
              className="card-panel p-6 h-full flex flex-col"
              style={{ border: '1px solid var(--t-border)' }}
            >
              <Quote className="h-6 w-6 mb-4 text-slate-400" aria-hidden="true" />
              <blockquote className="flex-1 leading-relaxed text-slate-500 dark:text-slate-300">
                &ldquo;{q.quote}&rdquo;
              </blockquote>
              <figcaption className="mt-5 text-sm">
                <span className="font-semibold" style={{ color: 'var(--t-heading)' }}>
                  {q.name}
                </span>
                <span className="block text-slate-500 dark:text-slate-400">
                  {q.role}, {q.company}
                </span>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

/** The close: pricing is the offer, with the guarantee stated, not implied. */
export function Pricing() {
  return (
    <section className="py-20 lg:py-24" id="pricing">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">Pricing</p>
          <h2 className="section-heading">Clear pricing, no surprises</h2>
          <p className="mt-3 text-slate-500 dark:text-slate-400">
            Start light, upgrade when the results justify it. Every plan is monthly,
            per seat, and cancellable from inside the product.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((t, i) => (
            <div
              key={t.name}
              className="card-panel p-7 h-full flex flex-col"
              style={{ border: i === 1 ? '2px solid var(--t-primary)' : '1px solid var(--t-border)' }}
            >
              {i === 1 && (
                <span
                  className="mb-4 self-start rounded-full px-3 py-1 text-[11px] font-bold text-white"
                  style={{ background: 'var(--t-primary)' }}
                >
                  Most popular
                </span>
              )}
              <h3 className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                {t.name}
              </h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t.blurb}</p>
              <p className="mt-4 text-3xl font-black tracking-tight" style={{ color: 'var(--t-primary)' }}>
                {t.price}
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">
                  {' '}
                  / seat / month
                </span>
              </p>
              <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                {t.points.map((p) => (
                  <li key={p} className="flex items-center gap-2">
                    <Check className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                    {p}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className={i === 1 ? 'btn-primary mt-6 text-sm w-full text-center' : 'btn-outline mt-6 text-sm w-full text-center'}
              >
                {i === 1 ? 'Start free trial' : 'View plan'}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          30-day money-back guarantee on every paid plan
        </p>
      </div>
    </section>
  );
}

/** Objection handling - the questions a buyer asks before paying. */
export function Faq() {
  const [open, setOpen] = useState(0);
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="faq">
      <div className="max-w-3xl mx-auto px-6">
        <p className="section-eyebrow">FAQ</p>
        <h2 className="section-heading">Questions, answered</h2>
        <div className="mt-10 divide-y divide-[var(--t-border)]">
          {FAQS.map((f, i) => (
            <div key={f.q}>
              <button
                type="button"
                onClick={() => setOpen(open === i ? -1 : i)}
                aria-expanded={open === i}
                className="flex w-full items-center justify-between gap-4 py-5 text-left font-semibold"
                style={{ color: 'var(--t-heading)' }}
              >
                <span>{f.q}</span>
                <ChevronDown
                  className={'h-5 w-5 shrink-0 transition-transform ' + (open === i ? 'rotate-180' : '')}
                  aria-hidden="true"
                />
              </button>
              {open === i && (
                <p className="pb-5 text-slate-500 dark:text-slate-400 leading-relaxed">{f.a}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/** The last thing on the page: one decision, two ways to make it. */
export function Cta() {
  return (
    <section className="py-20">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2
          className="text-3xl sm:text-4xl font-black tracking-tight"
          style={{ color: 'var(--t-heading)' }}
        >
          Start free. Upgrade when it pays for itself.
        </h2>
        <p className="mt-4 text-slate-500 dark:text-slate-400">
          No card required, no minimum term, cancel from inside the product whenever
          you like.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/register" className="btn-primary">
            Create a free account <ArrowRight className="h-4 w-4" />
          </Link>
          <Link to="/pricing" className="btn-outline">
            Compare plans
          </Link>
        </div>
      </div>
    </section>
  );
}

export default { Stats, Problem, Features, UseCases, Results, Testimonials, Pricing, Faq, Cta };
