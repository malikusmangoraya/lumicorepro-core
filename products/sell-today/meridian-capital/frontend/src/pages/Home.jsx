import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { BarChart3, ShieldCheck, TrendingUp, Lock, Quote, Star, ArrowRight, Check, Plus, Minus } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);

  const descs = [
    'Fewer, deeper positions built on in-house fundamental research — conviction over diversification theatre.',
    'Access to direct investments most private clients never see on a platform.',
    'Family office services from a single accountable partner.',
    'Quarterly reporting that names what we own, why, and what changed.',
  ];
  const features = [
    { icon: BarChart3, title: 'Concentrated Portfolios', desc: descs[0] },
    { icon: ShieldCheck, title: 'Direct Research', desc: descs[1] },
    { icon: TrendingUp, title: 'Family Office Advisory', desc: descs[2] },
    { icon: Lock, title: 'Clear Reporting', desc: descs[3] },
  ];
  const stats = [
    { value: '$2.1B', label: 'AUM' },
    { value: '23%', label: 'Annualized since inception' },
    { value: '97%', label: 'Capital retained' },
    { value: '40+', label: 'Partner relationships' },
  ];
  const values = [
    'Long-horizon, low-churn holdings',
    'In-house fundamental research',
    'Quarterly, unfiltered transparency',
  ];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">

        {/* ===== HERO: private capital, elegant split ===== */}
        <section className="relative overflow-hidden pt-14 lg:pt-0">
          <div className="absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,var(--t-primary)_0%,transparent_70%)] opacity-20" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,var(--t-accent)_0%,transparent_70%)] opacity-20" />
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1611974765275-40c4b0a2d4d2?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center bg-no-repeat scale-110" style={{ filter: 'blur(2px) grayscale(20%) brightness(0.7)' }} />
          </div>

          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* left: headline + lead + CTAs */}
            <div className="lg:col-span-7 border-l-2 pl-6" style={{ borderColor: 'var(--t-primary)' }}>
              <span className="section-eyebrow">
                {t('Home.eyebrow', 'PRIVATE CAPITAL')}
              </span>
              <h1 className="mt-5 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]">
                <span style={{ color: 'var(--t-heading)' }}>Capital, deployed</span>{' '}
                <span className="bg-gradient-to-r from-[var(--t-primary)] to-[var(--t-accent)] bg-clip-text text-transparent">
                  with conviction
                </span>
              </h1>
              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">
                {t('Home.lead', 'Concentrated, long-horizon portfolios with transparent quarterly reporting.')}
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm inline-flex items-center gap-2 px-6 py-3">
                  {t('Home.request_access', 'Request Access')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm inline-flex items-center gap-2 px-6 py-3">
                  {t('Home.our_approach', 'Our Approach')}
                </Link>
              </div>
            </div>

            {/* right: allocation snapshot card */}
            <div className="lg:col-span-5" data-reveal>
              <div className="card-panel rounded-2xl bg-surface border border-[var(--t-border)] shadow-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-[var(--t-border)]" style={{ background: 'linear-gradient(to right, var(--t-primary), var(--t-accent))' }}>
                  <p className="text-sm font-semibold text-white">
                    {t('Home.allocation', 'Allocation snapshot')}
                  </p>
                </div>
                <table className="w-full text-sm">
                  <caption className="sr-only">{t('Home.allocation', 'Allocation snapshot')}</caption>
                  <thead>
                    <tr className="border-b border-[var(--t-border)] text-left">
                      <th scope="col" className="py-3 px-6 font-semibold text-slate-500 dark:text-slate-400">
                        {t('Home.metric', 'Metric')}
                      </th>
                      <th scope="col" className="py-3 px-6 font-semibold text-slate-500 dark:text-slate-400 text-right">
                        {t('Home.value', 'Value')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.map((s) => (
                      <tr key={s.label} className="border-b border-[var(--t-border)] data-[revealed=false]:opacity-0" data-reveal>
                        <td className="py-3 px-6 text-left font-medium text-slate-600 dark:text-slate-300">
                          {s.label}
                        </td>
                        <td className="py-3 px-6 text-right font-bold" style={{ color: 'var(--t-primary)' }}>
                          {s.value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* ===== AS SEEN IN STRIP ===== */}
        <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
              <span>{t('Home.as_seen_in', 'As seen in')}</span>
              {['Forbes', 'Bloomberg', 'The Times', 'DesignWeek', 'Monocle'].map((m) => (
                <span key={m} className="opacity-80">{t(`Home.${m.toLowerCase()}`, m)}</span>
              ))}
            </div>
          </div>
        </section>

        {/* ===== PROBLEM / SOLUTION ===== */}
        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-eyebrow">{t('Home.the_problem', 'The problem')}</p>
              <h2 className="section-heading mb-4 text-3xl lg:text-4xl font-black" style={{ color: 'var(--t-heading)' }}>
                Wealth management is built for averages
              </h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                The industry sells diversified hubs and quarterly whatever-the-market-did. Families that want conviction, transparency and a long horizon are told to be patient with the mediocre.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-500 dark:text-slate-400">
                {['Concentrated positions', 'Direct research', 'Named partner', 'Transparent reporting'].map((b) => (
                  <span key={b} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface/60 border border-[var(--t-border)]">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" />
                    {b}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex justify-center lg:justify-end" data-reveal>
              <div className="card-panel rounded-2xl p-8 bg-surface border border-[var(--t-border)] shadow-lg max-w-sm w-full">
                <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <BarChart3 className="h-7 w-7" />
                </div>
                <p className="font-bold text-xl" style={{ color: 'var(--t-heading)' }}>
                  Meridian Capital fixes this
                </p>
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.
                </p>
                <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Conviction
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Access
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Transparency
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== CAPABILITIES ===== */}
        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-12">
              <p className="section-eyebrow">{t('Home.capabilities', 'Capabilities')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                What working with Meridian Capital feels like
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Four disciplines, one standard: international, uncompromising, and completely yours.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {features.map((feature, i) => (
                <div key={i} className="card-panel p-6 h-full flex flex-col rounded-xl border border-[var(--t-border)] bg-surface/60 data-[revealed=false]:opacity-0 data-[revealed=false]:translate-y-2" data-reveal>
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white shadow-md mb-4">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed flex-1">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== WHO IT IS FOR ===== */}
        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-12">
              <p className="section-eyebrow">{t('Home.who_it_is_for', 'Who it is for')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.made_for_people_like_you', 'Made for people like you')}
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                However you come to Meridian Capital, the standard is the same.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                { icon: BarChart3, title: 'Founders', desc: 'Founders whose exits created a concentration and a problem few advisors can actually handle.' },
                { icon: TrendingUp, title: 'Family Offices', desc: 'Offices that want direct research and real positions — not curated beta.' },
                { icon: ShieldCheck, title: 'Institutional Savers', desc: 'Long-horizon savers who would rather own the winners than rent an index.' },
              ].map((item, i) => (
                <div key={i} className="card-panel p-6 h-full flex flex-col rounded-xl border border-[var(--t-border)] bg-surface/60 data-[revealed=false]:opacity-0 data-[revealed=false]:translate-y-2" data-reveal>
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white shadow-md mb-4">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>
                    {item.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed flex-1">
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== BY THE NUMBERS ===== */}
        <section className="py-20 border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <p className="section-eyebrow">{t('Home.by_the_numbers', 'By the numbers')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.results_you_can_put_in_a_report', 'Results you can put in a report')}
              </h2>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              {stats.map((stat, i) => (
                <div key={i} className="text-center card-panel rounded-xl bg-surface/60 border border-[var(--t-border)] data-[revealed=false]:opacity-0" data-reveal>
                  <p
                    className="text-4xl sm:text-5xl font-black tracking-tight"
                    style={{
                      color: 'var(--t-primary)',
                      background: 'linear-gradient(115deg, var(--t-primary), var(--t-accent))',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    {stat.value}
                  </p>
                  <p className="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== PRICING ===== */}
        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-12">
              <p className="section-eyebrow">{t('Home.pricing', 'Pricing')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.clear_pricing_no_surprises', 'Clear pricing, no surprises')}
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Start light, upgrade when the results justify it.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                {
                  title: 'Advisory',
                  desc: 'Quarterly partner-led advice with full transparency.',
                  price: '0.75',
                  unit: t('Home.s', '/ %%'),
                  highlight: false,
                  features: ['Partner-led reviews', 'Full position disclosure', 'Reporting suite'],
                },
                {
                  title: 'Managed',
                  desc: 'Direct investment and concentrated portfolios.',
                  price: '1.15',
                  unit: t('Home.s', '/ %%'),
                  highlight: true,
                  badge: t('Home.most_popular', 'Most popular'),
                  features: ['Everything in Advisory', 'Direct positions', 'Tax-aware trading'],
                },
                {
                  title: 'Family Office',
                  desc: 'The full architecture for complex wealth.',
                  price: t('Home.custom', 'Custom'),
                  unit: ' ',
                  highlight: false,
                  features: ['Everything in Managed', 'Multi-family board', 'Estate & succession'],
                },
              ].map((plan, i) => (
                <div
                  key={i}
                  className={`card-panel p-6 h-full flex flex-col rounded-xl border ${plan.highlight
                    ? 'border-[var(--t-primary)] shadow-lg shadow-[var(--t-primary)]/10'
                    : 'border-[var(--t-border)] bg-surface/60'
                  } data-[revealed=false]:opacity-0 data-[revealed=false]:translate-y-2`}
                  data-reveal
                >
                  {plan.highlight && (
                    <span className="mb-3 self-start rounded-full px-3 py-1 text-[11px] font-bold text-white" style={{ background: 'var(--t-primary)' }}>
                      {plan.badge}
                    </span>
                  )}
                  <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--t-heading)' }}>
                    {plan.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {plan.desc}
                  </p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{ color: 'var(--t-primary)' }}>
                    {plan.price}
                    <span className="text-sm font-semibold text-slate-400">{plan.unit}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-[var(--t-primary)] shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Link
                    to="/pricing"
                    className={`mt-6 text-sm w-full text-center inline-flex items-center justify-center gap-2 ${
                      plan.highlight ? 'btn-primary' : 'btn-outline'
                    }`}
                  >
                    View plan
                  </Link>
                </div>
              ))}
            </div>

            <div className="mt-8 text-center">
              <Link to="/pricing" className="btn-outline text-sm inline-flex items-center gap-2 px-7 py-3">
                Compare all plans <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* ===== COMPARISON TABLE ===== */}
        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-5xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-10">
              <p className="section-eyebrow">{t('Home.why_choose_us', 'Why choose us')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.the_difference_side_by_side', 'The difference, side by side')}
              </h2>
            </div>

            <div className="card-panel overflow-hidden rounded-xl border border-[var(--t-border)] bg-surface/60 data-[revealed=false]:opacity-0" data-reveal>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--t-border)]">
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400"></th>
                    <th className="px-5 py-4 text-base font-bold" style={{ color: 'var(--t-primary)' }}>
                      Meridian Capital
                    </th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">
                      Traditional wealth firms
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Positions', ours: 'Concentrated, direct', theirs: 'Diversified hubs' },
                    { label: 'Research', ours: 'In-house fundamental', theirs: 'Broker sell-side' },
                    { label: 'Reporting', ours: 'Quarterly, unfiltered', theirs: 'Statement shrugs' },
                    { label: 'Access', ours: 'Direct deal flow', theirs: 'Closed to clients' },
                    { label: 'Accountability', ours: 'Named partner', theirs: 'Team roulette' },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-[var(--t-border)] last:border-0">
                      <td className="px-5 py-4 font-medium" style={{ color: 'var(--t-heading)' }}>
                        {row.label}
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                          <Check className="h-4 w-4 text-[var(--t-primary)] shrink-0 mt-0.5" />
                          {row.ours}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                          <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                          {row.theirs}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ===== TESTIMONIAL SPLIT ===== */}
        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="relative data-[revealed=false]:opacity-0" data-reveal>
              <div className="rounded-2xl overflow-hidden shadow-xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src="https://images.unsplash.com/photo-1611974765275-40c4b0a2d4d2?q=80&w=2070&auto=format&fit=crop"
                  alt="Founder reviewing portfolio with Meridian Capital"
                  loading="lazy"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            </div>

            <div>
              <p className="section-eyebrow">The Meridian Capital difference</p>
              <h2 className="section-heading mt-2" style={{ color: 'var(--t-heading)' }}>
                {t('Home.crafted_for_the_people_you_serve', 'Crafted for the people you serve')}
              </h2>

              <div className="card-panel mt-8 p-7 rounded-2xl bg-surface border border-[var(--t-border)] shadow-md data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <Quote className="h-6 w-6" />
                </div>
                <blockquote className="text-xl font-medium leading-relaxed mb-6" style={{ color: 'var(--t-heading)' }}>
                  Our exit made money the average advisor couldn't think about. Meridian built a plan, named the positions, and held us to it.
                </blockquote>
                <div className="flex items-center gap-4">
                  <div className="h-11 w-11 rounded-full bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white text-sm font-bold">
                    RM
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Raj Malhotra</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Founder client, second year</p>
                  </div>
                  <span className="ml-auto flex items-center gap-0.5 text-amber-500">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-current" />
                    ))}
                  </span>
                </div>
              </div>

              <ul className="mt-6 space-y-5">
                {values.map((value, i) => (
                  <li key={i} className="flex items-start gap-4 card-lift data-[revealed=false]:opacity-0 data-[revealed=false]:translate-y-1" data-reveal>
                    <div className="mt-0.5 h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white shrink-0 shadow-sm">
                      <Check className="h-4 w-4" />
                    </div>
                    <p className="text-base font-medium" style={{ color: 'var(--t-heading)' }}>
                      {value}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* ===== FAQ ===== */}
        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-3xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-10">
              <p className="section-eyebrow">{t('Home.faq', 'FAQ')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.questions_answered', 'Questions, answered')}
              </h2>
            </div>

            <div className="space-y-3">
              {[
                {
                  q: 'Do you take every client?',
                  a: 'No. We work with a small number of families and founders whose needs match what we do best — concentrated, long-horizon capital.',
                },
                {
                  q: 'How often do we meet?',
                  a: 'At minimum quarterly, with ad-hoc check-ins whenever a position or the market calls for it.',
                },
                {
                  q: 'Do you trade for us or advise?',
                  a: 'Both. The Managed and Family Office tiers include direct trading with your consent; Advisory is advice and reporting only.',
                },
                {
                  q: 'What happens to my data?',
                  a: 'Your positions, correspondence and reporting are confidential and never shared with third parties without your explicit consent.',
                },
              ].map((faq, i) => (
                <div
                  key={i}
                  className="card-panel overflow-hidden rounded-xl border border-[var(--t-border)] bg-surface/60 data-[revealed=false]:opacity-0"
                  data-reveal
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaq(openFaq === i ? -1 : i)}
                    aria-expanded={openFaq === i}
                    aria-controls={`faq-panel-${i}`}
                    className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                  >
                    <span className="font-semibold" style={{ color: 'var(--t-heading)' }}>
                      {faq.q}
                    </span>
                    {openFaq === i ? (
                      <Minus className="h-5 w-5 shrink-0" style={{ color: 'var(--t-primary)' }} />
                    ) : (
                      <Plus className="h-5 w-5 shrink-0" style={{ color: 'var(--t-primary)' }} />
                    )}
                  </button>
                  {openFaq === i && (
                    <p id={`faq-panel-${i}`} className="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      {faq.a}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== FINAL CTA ===== */}
        <section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 shadow-2xl ring-1 ring-white/10 dark:ring-white/5"
              data-reveal
              style={{
                background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)',
              }}
            >
              <div className="absolute inset-0 -z-10 opacity-10" style={{
                backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 50%, white 1px, transparent 1px)',
                backgroundSize: '24px 24px'
              }} />

              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Start the conversation
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Tell us where you want to go — we will map the route, the milestones, and the first step today.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3 text-sm font-bold text-[var(--t-primary)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
                >
                  Request Access <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  Our Approach
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
