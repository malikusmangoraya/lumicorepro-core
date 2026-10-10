import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { LayoutDashboard, Zap, ShieldCheck, TrendingUp, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus, Layers, Rocket, Briefcase } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import shotOutline from '../assets/images/workspace-desk.jpg';
import shotLayouts from '../assets/images/designer-desk.jpg';
import shotPreview from '../assets/images/laptop-setup.jpg';
import shotComments from '../assets/images/team.jpg';

// Shipped assets, imported so the bundler fingerprints them and they resolve under
// the GitHub Pages project subpath.
const workspace = [
  {
    src: shotOutline,
    alt: 'A desk with notes being worked into an outline',
    title: 'Outline first',
    caption: 'Write the content in plain text; the layout follows your structure instead of fighting it.',
  },
  {
    src: shotLayouts,
    alt: 'A designer working on layout at a desk',
    title: 'Smart layouts',
    caption: 'Type, spacing and colour come from the system, so nothing you send out looks template-white.',
  },
  {
    src: shotPreview,
    alt: 'A laptop showing a document open in an editor',
    title: 'Live preview',
    caption: 'The finished page is on screen while you edit it, not after you export.',
  },
  {
    src: shotComments,
    alt: 'A small team reviewing work together',
    title: 'Team comments',
    caption: 'Feedback lands on the part it belongs to, instead of in a thread somewhere else.',
  },
];

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);
  const descs = ['Smart layouts that take an outline to a designed deck — brand-true, not template-white.', 'Brand kits that keep every stakeholder deck on-voice.', 'Slide-level analytics that show what actually held the room.', 'Comments that don\'t derail the narrative thread.'];
  const features = [
    { icon: LayoutDashboard, title: 'Smart Layouts', desc: descs[0] },
    { icon: Zap, title: 'Brand Kits', desc: descs[1] },
    { icon: ShieldCheck, title: 'Slide Analytics', desc: descs[2] },
    { icon: TrendingUp, title: 'Team Comments', desc: descs[3] },
  ];
  const stats = [
    { value: '80k', label: 'Decks made' },
    { value: t('Home.4_9', '4.9'), label: 'Creator rating' },
    { value: '10x', label: 'Faster decks' },
    { value: '99.9%', label: 'Uptime' },
  ];
  const values = ['Great design, no designer', 'Know every slide\'s attention', 'Comments that don\'t derail'];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
                <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <span className="section-eyebrow">
                {t('Home.eyebrow', t('Home.eyebrow', 'RESUME BUILDER'))}
              </span>
              <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">
                <span style={{ color: 'var(--t-heading)' }}>Resumes that get</span>{' '}
                <span style={{ color: 'var(--t-primary)' }}>you the interview</span>
              </h1>
              <p className="mt-6 text-lg text-slate-500 leading-relaxed max-w-lg">
                {t('Home.lead', t('Home.lead', 'A guided builder, ATS-ready templates and exports that take one afternoon.'))}
              </p>
              <ul className="mt-8 space-y-2.5 max-w-md">
                {values.map((v) => (
                  <li key={v} className="flex items-start gap-3" data-reveal>
                    <Check className="h-4 w-4 mt-0.5 shrink-0" style={{ color: 'var(--t-primary)' }} />
                    <span className="text-sm text-slate-600 dark:text-slate-300">{v}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.build_now', t('Home.build_now', 'Build Your Resume'))}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.templates', t('Home.templates', 'See Templates'))}
                </Link>
              </div>
            </div>
            <div>
              <div className="rounded-2xl border border-[var(--t-border)] bg-white dark:bg-[var(--t-card)] p-8 card-lift" data-reveal>
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-widest text-slate-500">
                    {t('Home.preview', t('Home.preview', 'Live preview'))}
                  </p>
                  <div className="flex gap-1.5" aria-hidden="true">
                    <span className="h-2 w-2 rounded-full bg-[var(--t-border)]" />
                    <span className="h-2 w-2 rounded-full bg-[var(--t-border)]" />
                    <span className="h-2 w-2 rounded-full bg-[var(--t-primary)]" />
                  </div>
                </div>
                <div className="mt-6 space-y-3">
                  <div className="h-5 w-2/3 rounded bg-slate-200 dark:bg-white/10" />
                  <div className="h-2.5 w-full rounded bg-slate-100 dark:bg-white/5" />
                  <div className="h-2.5 w-5/6 rounded bg-slate-100 dark:bg-white/5" />
                  <div className="h-2.5 w-4/6 rounded bg-slate-100 dark:bg-white/5" />
                  <div className="pt-3 h-2.5 w-1/2 rounded bg-slate-200 dark:bg-white/10" />
                  <div className="h-2.5 w-full rounded bg-slate-100 dark:bg-white/5" />
                  <div className="h-2.5 w-3/4 rounded bg-slate-100 dark:bg-white/5" />
                </div>
                <div className="mt-7 grid grid-cols-2 gap-3 border-t border-[var(--t-border)] pt-5">
                  {stats.slice(0, 2).map((s) => (
                    <div key={s.label}>
                      <p className="text-xl font-extrabold" style={{ color: 'var(--t-primary)' }}>
                        {s.value}
                      </p>
                      <p className="text-[0.7rem] text-slate-500 dark:text-slate-400">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
              <span>{t('Home.as_seen_in', t('Home.as_seen_in', 'As seen in'))}</span>
              <span className="opacity-80">{t('Home.forbes', t('Home.forbes', 'Forbes'))}</span>
              <span className="opacity-80">{t('Home.bloomberg', t('Home.bloomberg', 'Bloomberg'))}</span>
              <span className="opacity-80">{t('Home.the_times', t('Home.the_times', 'The Times'))}</span>
              <span className="opacity-80">{t('Home.designweek', t('Home.designweek', 'DesignWeek'))}</span>
              <span className="opacity-80">{t('Home.monocle', t('Home.monocle', 'Monocle'))}</span>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-eyebrow">{t('Home.the_problem', t('Home.the_problem', 'The problem'))}</p>
              <h2 className="section-heading mb-4">Founders are wasting their story on slides</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                A pitch is ninety percent narrative and ten percent design, but founders spend it backwards. Beautiful decks take weeks; ugly ones sink the meeting.
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Layers className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  ResuPro fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  ResuPro turns outlines into investor-ready decks with smart layouts, brand systems and live analytics on every slide.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24 border-t border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.inside_the_tool', 'Inside the tool')}</p>
              <h2 className="section-heading">Four steps from outline to something shareable</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                The part of the process most document tools make you do by hand.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {workspace.map((shot) => (
                <figure
                  key={shot.title}
                  className="card-panel rounded-2xl overflow-hidden border border-[var(--t-border)] bg-surface/60 h-full flex flex-col card-lift"
                  data-reveal
                >
                  <img
                    src={shot.src}
                    alt={shot.alt}
                    loading="lazy"
                    decoding="async"
                    width="900"
                    height="600"
                    className="h-44 w-full object-cover"
                  />
                  <figcaption className="p-6 flex-1">
                    <p className="font-bold" style={{ color: 'var(--t-heading)' }}>
                      {shot.title}
                    </p>
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      {shot.caption}
                    </p>
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.capabilities', t('Home.capabilities', 'Capabilities'))}</p>
              <h2 className="section-heading">What working with ResuPro feels like</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Four disciplines, one standard: international, uncompromising, and completely yours.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, i) => (
                <div key={i} className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{
                      background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))',
                      boxShadow: '0 10px 24px rgba(0,0,0,0.18)',
                    }}
                  >
                    <feature.icon className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.who_it_is_for', t('Home.who_it_is_for', 'Who it is for'))}</p>
              <h2 className="section-heading">{t('Home.made_for_people_like_you', t('Home.made_for_people_like_you', 'Made for people like you'))}</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                However you come to ResuPro, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Layers className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Founders</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Founders building the deck that carries the round.</p>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Rocket className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Pre-Seed Teams</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Teams who need investor-ready in days, not designer months.</p>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Briefcase className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Internal Teams</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Anyone who presents weekly and resents the formatting time.</p>
                </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">{t('Home.by_the_numbers', t('Home.by_the_numbers', 'By the numbers'))}</p>
              <h2 className="section-heading">{t('Home.results_you_can_put_in_a_report', t('Home.results_you_can_put_in_a_report', 'Results you can put in a report'))}</h2>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
              {stats.map((stat, i) => (
                <div key={i} className="text-center card-lift" data-reveal>
                  <p
                    className="text-4xl lg:text-5xl font-black tracking-tight"
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

        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.pricing', t('Home.pricing', 'Pricing'))}</p>
              <h2 className="section-heading">{t('Home.clear_pricing_no_surprises', t('Home.clear_pricing_no_surprises', 'Clear pricing, no surprises'))}</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Start light, upgrade when the results justify it.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>{t('Home.starter', t('Home.starter', 'Starter'))}</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Decks, quickly.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    0 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Smart layouts
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      3 brand kits
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Free forever
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '2px solid var(--t-primary)'}}>
                    <span
                      className="mb-4 self-start rounded-full px-3 py-1 text-[11px] font-bold text-white"
                      style={{ background: 'var(--t-primary)' }}
                    >
                      Most popular
                    </span>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Pro</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">The founder standard.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    19 <span className="text-sm font-semibold text-slate-400">/ USD/mo</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Starter
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Unlimited brand kits
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Slide analytics
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Team</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Decks at company scale.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 39 <span className="text-sm font-semibold text-slate-400">/ USD/mo</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Pro
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Shared kits & review
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Admin & export HTML
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
            </div>
            <div className="mt-10 text-center">
              <Link to="/pricing" className="btn-outline text-sm px-7 py-3">
                Compare all plans <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

                <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-5xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <p className="section-eyebrow">{t('Home.why_choose_us', t('Home.why_choose_us', 'Why choose us'))}</p>
              <h2 className="section-heading">{t('Home.the_difference_side_by_side', t('Home.the_difference_side_by_side', 'The difference, side by side'))}</h2>
            </div>
            <div className="card-panel overflow-hidden" data-reveal>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--t-border)]">
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400"></th>
                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>ResuPro</th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">Legacy presentation tools</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Design</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Smart layouts, brand-true
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Manual formatting
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Analytics</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Slide-level attention
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Nothing
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Speed</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Outlines to decks
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Weeks of rounds
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Consistency</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Brand kits everywhere
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Per-file drift
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Turnaround</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Same-day
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Designer queue
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            <div className="relative">
              <div
                className="absolute inset-0 -z-10 rounded-3xl opacity-40"
                style={{
                  background:
                    'radial-gradient(circle at 30% 30%, var(--t-primary), transparent 55%), radial-gradient(circle at 70% 70%, var(--t-accent), transparent 55%)',
                }}
              />
              <div className="glass-md rounded-3xl p-10" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-6"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Quote className="h-6 w-6" />
                </span>
                <blockquote
                  className="text-xl font-medium leading-relaxed mb-6"
                  style={{ color: 'var(--t-heading)' }}
                >
                  We went from two weeks of designer rounds to a deck built in an afternoon — and the analytics showed the story was holding.
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    YK
                  </span>
                  <div>
                    <p className="font-semibold text-sm">Yusuf Karim</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Co-founder, pre-seed startup</p>
                  </div>
                  <span className="ml-auto flex items-center gap-0.5 text-amber-500">
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                  </span>
                </div>
              </div>
            </div>
            <div>
              <p className="section-eyebrow">The ResuPro difference</p>
              <h2 className="section-heading">{t('Home.crafted_for_the_people_you_serve', t('Home.crafted_for_the_people_you_serve', 'Crafted for the people you serve'))}</h2>
              <ul className="mt-8 space-y-6">
                {values.map((value, i) => (
                  <li key={i} className="flex items-start gap-4 card-lift" data-reveal>
                    <span
                      className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                      style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                    >
                      <Check className="h-4 w-4" />
                    </span>
                    <p className="text-base font-medium" style={{ color: 'var(--t-heading)' }}>
                      {value}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-3xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <p className="section-eyebrow">{t('Home.faq', t('Home.faq', 'FAQ'))}</p>
              <h2 className="section-heading">{t('Home.questions_answered', t('Home.questions_answered', 'Questions, answered'))}</h2>
            </div>
            <div className="space-y-4">
              
              <div key="0" className="card-panel overflow-hidden" data-reveal>
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === 0 ? -1 : 0)}
                  aria-expanded={openFaq === 0}
                  aria-controls="faq-panel-0"
                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                >
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Do I still need a designer?</span>
                  {openFaq === 0 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 0 && (
                  <p id="faq-panel-0" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    For an investor deck, no. Smart layouts handle the design; your story is the asset. A designer helps only if you need a fully bespoke brand build.
                  </p>
                )}
              </div>
              <div key="1" className="card-panel overflow-hidden" data-reveal>
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === 1 ? -1 : 1)}
                  aria-expanded={openFaq === 1}
                  aria-controls="faq-panel-1"
                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                >
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>What are slide analytics?</span>
                  {openFaq === 1 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 1 && (
                  <p id="faq-panel-1" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Attention heat by slide and section, so you know which ten seconds lost the room.
                  </p>
                )}
              </div>
              <div key="2" className="card-panel overflow-hidden" data-reveal>
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === 2 ? -1 : 2)}
                  aria-expanded={openFaq === 2}
                  aria-controls="faq-panel-2"
                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                >
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Can I export for offline presentations?</span>
                  {openFaq === 2 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 2 && (
                  <p id="faq-panel-2" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Yes — PDF, PPT and live HTML export, with speaker notes built in.
                  </p>
                )}
              </div>
              <div key="3" className="card-panel overflow-hidden" data-reveal>
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === 3 ? -1 : 3)}
                  aria-expanded={openFaq === 3}
                  aria-controls="faq-panel-3"
                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
                >
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Is it just for pitch decks?</span>
                  {openFaq === 3 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 3 && (
                  <p id="faq-panel-3" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    No — board updates, sales decks and internal kick-offs use the same brand-kept system.
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 card-lift"
              data-reveal
              style={{
                background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)',
                boxShadow: '0 30px 60px rgba(0,0,0,0.25)',
              }}
            >
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Start the conversation
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Tell us where you want to go — we will map the route, the milestones, and the
                first step today.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3 text-sm font-bold transition-all duration-200 hover:-translate-y-0.5"
                  style={{ color: 'var(--t-primary)' }}
                >
                  Start Building <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  Templates
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
