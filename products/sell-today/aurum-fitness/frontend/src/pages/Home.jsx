import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Zap, TrendingUp, Users, Award, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus, Dumbbell, Clock, Heart } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">

        {/* ===== HERO: split layout, distinct fitness treatment ===== */}
        <section className="relative overflow-hidden pt-14 lg:pt-0">
          {/* ambient background */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,var(--t-primary)_0%,transparent_60%)] opacity-20" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,var(--t-accent)_0%,transparent_60%)] opacity-20" />
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1534438327255-205eec384c0b?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center bg-no-repeat scale-110" style={{ filter: 'blur(2px) grayscale(20%) brightness(0.85)' }} />
          </div>

          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* left: headline + lead + CTAs */}
            <div>
              <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.4em] text-[var(--t-primary)] section-eyebrow">
                <span className="h-1 w-1 rounded-full bg-[var(--t-primary)]" />
                {t('Home.eyebrow', 'PERFORMANCE CLUB')}
              </span>

              <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black leading-[1.04] tracking-[-0.02em]">
                <span style={{ color: 'var(--t-heading)' }}>Stronger</span>
                <br />
                <span className="bg-gradient-to-r from-[var(--t-primary)] to-[var(--t-accent)] bg-clip-text text-transparent">
                  by design
                </span>
              </h1>

              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">
                {t('Home.lead', 'Olympic methodology on a private training floor — coached, measured, relentless.')}
              </p>

              <div className="mt-8 flex flex-wrap gap-4">
                <Link to="/contact" className="btn-primary text-sm inline-flex items-center gap-2 px-7 py-3">
                  {t('Home.start_training', 'Start Training')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm inline-flex items-center gap-2 px-7 py-3">
                  {t('Home.programs', 'View Programs')}
                </Link>
              </div>

              {/* trust strip (minimal, real) */}
              <div className="mt-10 flex flex-wrap items-center gap-6 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.coach_ratio', '1:1 coach ratio')}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.member_facilities', '60m recovery zones')}
                </span>
                <span className="flex items-center gap-1.5">
                  <Heart className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.recovery_treated_like_training', 'Recovery = training')}
                </span>
              </div>
            </div>

            {/* right: real-image hero block */}
            <div className="relative" data-reveal>
              <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src="https://images.unsplash.com/photo-1534438327255-205eec384c0b?q=80&w=2070&auto=format&fit=crop"
                  alt="Private training floor at Aurum Fitness"
                  loading="eager"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '520px' }}
                />
                {/* overlay badge */}
                <div className="absolute bottom-0 left-0 right-0 p-5 bg-gradient-to-t from-black/60 to-transparent">
                  <div className="flex items-center gap-3 text-white">
                    <div className="h-10 w-10 rounded-full bg-[var(--t-primary)] flex items-center justify-center text-white text-sm font-bold">
                      AF
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Aurum Fitness</p>
                      <p className="text-xs opacity-80">Built for the serious few</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* floating micro card */}
              <div className="absolute -bottom-4 -left-4 rounded-xl bg-surface/90 backdrop-blur p-4 shadow-lg border border-[var(--t-border)] flex items-center gap-3 data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-10 w-10 rounded-lg bg-[var(--t-primary)] flex items-center justify-center text-white">
                  <Dumbbell className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>92% goal attainment</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">measured, not guessed</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== STAT BAR ===== */}
        <div className="border-y border-[var(--t-border)] bg-surface/70">
          <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-2 lg:grid-cols-4 gap-y-6 gap-x-6 text-center lg:text-left">
            {[
              { value: '92%', label: t('Home.goal_attainment', 'Goal attainment') },
              { value: t('Home.1_1', '1:1'), label: t('Home.coach_ratio', 'Coach ratio') },
              { value: '14', label: t('Home.coach_credentials', 'Coach credentials') },
              { value: '60m', label: t('Home.member_facilities', 'Member facilities') },
            ].map((s, i) => (
              <div key={i} className="data-[revealed=false]:opacity-0" data-reveal>
                <p className="text-3xl sm:text-4xl font-black" style={{ color: 'var(--t-primary)' }}>
                  {s.value}
                </p>
                <p className="mt-1 text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* ===== AS SEEN IN STRIP (minimal) ===== */}
        <section className="border-y border-[var(--t-border)] bg-surface/60 py-5">
          <div className="max-w-7xl mx-auto px-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
            <span>{t('Home.as_seen_in', 'As seen in')}</span>
            {['Forbes', 'Bloomberg', 'The Times', 'DesignWeek', 'Monocle'].map((m) => (
              <span key={m} className="opacity-80">{t(`Home.${m.toLowerCase()}`, m)}</span>
            ))}
          </div>
        </section>

        {/* ===== PROBLEM / SOLUTION SPLIT ===== */}
        <section className="py-20 lg:py-24 border-t border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-eyebrow">{t('Home.the_problem', 'The problem')}</p>
              <h2 className="section-heading mb-4 text-3xl lg:text-4xl font-black" style={{ color: 'var(--t-heading)' }}>
                Gyms sell access to machines, not progress
              </h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                Membership means a floor and a spotter if you're lucky. Nobody measures, nobody corrects, and progress is whatever the mirror says this month.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-500 dark:text-slate-400">
                {['Unmeasured sessions', 'Template programming', 'Recovery as an upcharge', 'Slow feedback loop'].map((b) => (
                  <span key={b} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface/60 border border-[var(--t-border)]">
                    <Minus className="h-3.5 w-3.5 text-slate-400" />
                    {b}
                  </span>
                ))}
              </div>
            </div>

            <div className="data-[revealed=false]:opacity-0" data-reveal>
              <div className="card-panel rounded-2xl p-8 bg-surface border border-[var(--t-border)] shadow-lg max-w-sm w-full">
                <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <Dumbbell className="h-7 w-7" />
                </div>
                <p className="font-bold text-xl" style={{ color: 'var(--t-heading)' }}>
                  Aurum Fitness fixes this
                </p>
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Olympic methodology fused with private training floors — coached, measured, relentless.
                </p>
                <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Coached
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Measured
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Relentless
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== CAPABILITIES: 4 cards, distinct framing ===== */}
        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-12">
              <p className="section-eyebrow">{t('Home.capabilities', 'Capabilities')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                What working with Aurum Fitness feels like
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Four disciplines, one standard: international, uncompromising, and completely yours.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {[
                { icon: Zap, title: 'Private Coaching', desc: '1:1 coach ratio and programming built on your data.' },
                { icon: TrendingUp, title: 'Strength Systems', desc: 'Systems that prescribe, correct and progress the movement.' },
                { icon: Users, title: 'Recovery Lab', desc: 'A recovery lab treated with the same respect as the training floor.' },
                { icon: Award, title: 'Performance Metrics', desc: 'Metrics that put a number on every session.' },
              ].map((feature, i) => (
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
                However you come to Aurum Fitness, the standard is the same.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                { icon: Dumbbell, title: 'Serious Trainers', desc: 'Athletes who want a program, a coach and a tracking sheet — not a key card.' },
                { icon: TrendingUp, title: 'Busy Professionals', desc: 'People who need every session to count because free time is scarce.' },
                { icon: Award, title: 'Comeback Lifters', desc: 'Returners rebuilding strength who need load managed, not restored by memory.' },
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
              {[
                { value: '92%', label: t('Home.goal_attainment', 'Goal attainment') },
                { value: t('Home.1_1', '1:1'), label: t('Home.coach_ratio', 'Coach ratio') },
                { value: '14', label: t('Home.coach_credentials', 'Coach credentials') },
                { value: '60m', label: t('Home.member_facilities', 'Member facilities') },
              ].map((stat, i) => (
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
        <section className="py-20 lg:py-28">
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
                  title: 'Floor',
                  desc: 'Access and the basics.',
                  price: 'From 89',
                  unit: '/ USD/mo',
                  highlight: false,
                  features: ['24/7 floor', 'Group classes', '2 guest passes'],
                },
                {
                  title: 'Coaching',
                  desc: 'The program, measured.',
                  price: 'From 249',
                  unit: '/ USD/mo',
                  highlight: true,
                  badge: 'Most popular',
                  features: ['Everything in Floor', '1:1 coach programming', 'Monthly testing'],
                },
                {
                  title: 'Athlete',
                  desc: 'For the serious clock.',
                  price: 'From 449',
                  unit: '/ USD/mo',
                  highlight: false,
                  features: ['Everything in Coaching', 'Daily coaching touch', 'Full recovery protocol'],
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
                      {t('Home.aurum_fitness', 'Aurum Fitness')}
                    </th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">Chain gyms</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Coaching', ours: '1:1, measured', theirs: 'Optional add-on', oursOk: true },
                    { label: 'Programming', ours: 'Data-driven', theirs: 'Classes by template', oursOk: true },
                    { label: 'Recovery', ours: 'Full lab in membership', theirs: 'Cryo upcharge', oursOk: true },
                    { label: 'Metrics', ours: 'Monthly testing', theirs: 'Guesswork', oursOk: true },
                    { label: 'Ratio', ours: 'Coach per member', theirs: 'Nobody watching', oursOk: true },
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
            {/* left: image block */}
            <div className="relative data-[revealed=false]:opacity-0" data-reveal>
              <div className="rounded-2xl overflow-hidden shadow-xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src="https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=2073&auto=format&fit=crop"
                  alt="Athlete completing a coached session at Aurum Fitness"
                  loading="lazy"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            </div>

            {/* right: testimonial */}
            <div>
              <p className="section-eyebrow">The Aurum Fitness difference</p>
              <h2 className="section-heading mt-2" style={{ color: 'var(--t-heading)' }}>
                {t('Home.crafted_for_the_people_you_serve', 'Crafted for the people you serve')}
              </h2>

              <div className="card-panel mt-8 p-7 rounded-2xl bg-surface border border-[var(--t-border)] shadow-md data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <Quote className="h-6 w-6" />
                </div>
                <blockquote className="text-xl font-medium leading-relaxed mb-6" style={{ color: 'var(--t-heading)' }}>
                  Ninety-two percent of my cohort hit their goal in the year. The coaching floor is the difference between membership and a method.
                </blockquote>
                <div className="flex items-center gap-4">
                  <div className="h-11 w-11 rounded-full bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white text-sm font-bold">
                    SM
                  </div>
                  <div>
                    <p className="font-semibold text-sm">Sofia Marchetti</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Program member, second year</p>
                  </div>
                  <span className="ml-auto flex items-center gap-0.5 text-amber-500">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-current" />
                    ))}
                  </span>
                </div>
              </div>

              <ul className="mt-6 space-y-5">
                {[
                  'Programming built on data',
                  'Recovery treated like training',
                  'A floor that smells like work',
                ].map((value, i) => (
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
                  q: 'Do I get a coach on the floor?',
                  a: 'At the two upper tiers, yes — a 1:1 ratio with programming reviewed weekly and tested monthly.',
                },
                {
                  q: 'Is there a recovery lab?',
                  a: 'Yes: sauna, ice, compression and massage lanes, booked like training sessions.',
                },
                {
                  q: 'How is progress measured?',
                  a: 'Monthly performance testing with a permanent record — weights, times and body comp numbers you own.',
                },
                {
                  q: 'Can I freeze or cancel?',
                  a: 'Yes, from the app, without a front-desk theatre.',
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
              {/* subtle pattern overlay */}
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
                  Start Training <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  View Programs
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
