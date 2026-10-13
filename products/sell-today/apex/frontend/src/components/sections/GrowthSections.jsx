import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Quote, Check, ChevronDown, ArrowRight, ShieldCheck } from 'lucide-react';

/**
 * Optional conversion sections retained for routes that import them.
 * Apex is a vehicle concierge, so its marketing sections avoid invented
 * customer outcomes, pricing and performance guarantees.
 */

const STATS = [{ value: 'Every car', label: 'Reviewed individually', numeric: '', prefix: '', suffix: '' }, { value: 'Clear records', label: 'Shared where available', numeric: '', prefix: '', suffix: '' }, { value: 'One advisor', label: 'Personal guidance', numeric: '', prefix: '', suffix: '' }, { value: 'Your decision', label: 'No pressure to proceed', numeric: '', prefix: '', suffix: '' }];

const FEATURES = [{ title: 'Curated collection', desc: 'A focused selection of performance, grand touring and collector vehicles.' }, { title: 'Condition explained', desc: 'Inspection findings and known vehicle details are discussed before you decide.' }, { title: 'History reviewed', desc: 'Available service and ownership documentation is organized for your review.' }, { title: 'Personal guidance', desc: 'An automotive advisor helps coordinate questions, viewings and next steps.' }];

const USE_CASES = [{ title: 'Drivers seeking a special car', desc: 'Explore distinctive vehicles selected for their character, condition and specification.' }, { title: 'Collectors building thoughtfully', desc: 'Review provenance information and discuss the details that matter to your collection.' }, { title: 'Enthusiasts comparing options', desc: 'Get help understanding the differences between models, histories and ownership needs.' }, { title: 'Buyers who value a personal process', desc: 'Arrange a private viewing and speak directly with an advisor throughout your search.' }];

const RESULTS = [{ title: 'A clearer shortlist', desc: 'Compare the vehicles that fit your preferences, with details laid out for a considered decision.' }, { title: 'A more informed viewing', desc: 'Know which records and inspection details are available before you arrange to see a car.' }, { title: 'A confident handover', desc: 'Understand agreed preparation, collection and delivery arrangements before committing.' }];

const TIERS = [{ name: 'Collection enquiry', blurb: 'For a first conversation about a specific vehicle.', price: 'Ask', points: ['Vehicle availability', 'Specification details', 'Viewing options'] }, { name: 'Private viewing', blurb: 'For buyers ready to see a shortlisted vehicle.', price: 'By appointment', points: ['Advisor-led walkaround', 'Available records discussed', 'Test drive requirements explained'] }, { name: 'Ownership planning', blurb: 'For buyers coordinating the next steps.', price: 'Vehicle-specific', points: ['Preparation items agreed', 'Collection or delivery options', 'Written next steps'] }];

const FAQS = [{ q: 'Are all vehicles available to view?', a: 'Availability can change. Contact our team to confirm a vehicle’s status and arrange a suitable viewing.' }, { q: 'What does an inspection cover?', a: 'The inspection scope and findings are specific to each vehicle. Ask your advisor for the current report and any limitations before proceeding.' }, { q: 'Can I arrange a test drive?', a: 'Test drives may be available for eligible vehicles. Licensing, insurance and scheduling requirements are confirmed in advance.' }, { q: 'Are finance options provided?', a: 'We can discuss finance introductions where available, but eligibility, terms and approval depend on the provider and your circumstances.' }, { q: 'Can a vehicle be delivered?', a: 'Collection and delivery options vary by vehicle and destination. The cost, timing and coverage are confirmed before any booking.' }, { q: 'Is an enquiry a commitment to buy?', a: 'No. An enquiry or viewing request does not reserve a vehicle or create a purchase obligation. Any reservation terms are provided separately in writing.' }];

const TESTIMONIALS = [];

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
          <p className="section-eyebrow">Buying thoughtfully</p>
          <h2 className="section-heading">A remarkable car deserves a closer look.</h2>
          <p className="mt-4 leading-relaxed text-slate-500 dark:text-slate-400">
            Photographs and specifications are only the beginning. We help you understand a vehicle’s condition, available history and ownership details, then make space for the questions that matter before you choose.
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
        <h2 className="section-heading">What the Apex experience includes</h2>
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
          <h2 className="section-heading">Made for drivers who care about the details</h2>
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
          <p className="section-eyebrow">The process</p>
          <h2 className="section-heading">Thoughtful from first question to handover</h2>
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
  if (!TESTIMONIALS.length) return null;
  return (
    <section className="py-20 lg:py-24" id="customers">
      <div className={SHELL}>
        <div className="text-center max-w-2xl mx-auto">
          <p className="section-eyebrow">Customer stories</p>
          <h2 className="section-heading">Experiences from Apex owners</h2>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((q) => (
            <figure key={q.name} className="card-panel p-6 h-full flex flex-col" style={{ border: '1px solid var(--t-border)' }}>
              <Quote className="h-6 w-6 mb-4 text-slate-400" aria-hidden="true" />
              <blockquote className="flex-1 leading-relaxed text-slate-500 dark:text-slate-300">&ldquo;{q.quote}&rdquo;</blockquote>
              <figcaption className="mt-5 text-sm"><span className="font-semibold" style={{ color: 'var(--t-heading)' }}>{q.name}</span><span className="block text-slate-500 dark:text-slate-400">{q.role}, {q.company}</span></figcaption>
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
          <p className="section-eyebrow">Next steps</p>
          <h2 className="section-heading">A clear process for every vehicle.</h2>
          <p className="mt-3 text-slate-500 dark:text-slate-400">
            Pricing and terms are specific to each vehicle and are shared by an advisor before you make a decision.
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
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{' '}{t.name === 'Collection enquiry' ? 'only' : ''}</span>
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
                to="/contact"
                className={i === 1 ? 'btn-primary mt-6 text-sm w-full text-center' : 'btn-outline mt-6 text-sm w-full text-center'}
              >
                {i === 0 ? 'Make an enquiry' : i === 1 ? 'Arrange a viewing' : 'Discuss next steps'}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          Vehicle-specific terms are provided in writing before any reservation
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
          Find the car that stays with you.
        </h2>
        <p className="mt-4 text-slate-500 dark:text-slate-400">
          Tell us what you are looking for and we will help you explore the collection, one considered step at a time.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/contact" className="btn-primary">
            Enquire about a vehicle <ArrowRight className="h-4 w-4" />
          </Link>
          <Link to="/services" className="btn-outline">Explore ownership services</Link>
        </div>
      </div>
    </section>
  );
}

export default { Stats, Problem, Features, UseCases, Results, Testimonials, Pricing, Faq, Cta };
