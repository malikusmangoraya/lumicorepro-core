import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Layers, Sparkles, Zap, Award, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus, Users } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import shotWilderness from '../assets/images/forest-rays.jpg';
import shotAltitude from '../assets/images/peak.jpg';
import shotArchitecture from '../assets/images/arch-modern.jpg';
import shotInteriors from '../assets/images/interior-lux.jpg';
import shotWeather from '../assets/images/fog-forest.jpg';
import shotAfterDark from '../assets/images/night-mtn.jpg';

// Shipped assets, imported so the bundler fingerprints them and they resolve under
// the GitHub Pages project subpath.
const selectedFrames = [
  {
    src: shotWilderness,
    alt: 'Sunlight through trees in a forest',
    title: 'Wilderness',
    caption: 'Landscape work is shot on location and timed to the hour the light actually arrives.',
  },
  {
    src: shotAltitude,
    alt: 'A mountain summit above cloud',
    title: 'Altitude',
    caption: 'Mountain commissions are planned around weather windows rather than fixed shoot dates.',
  },
  {
    src: shotArchitecture,
    alt: 'A modern building photographed from the street',
    title: 'Architecture',
    caption: 'Buildings are photographed for the angle they were designed to be seen from, not the nearest pavement.',
  },
  {
    src: shotInteriors,
    alt: 'A light-filled interior room',
    title: 'Interiors',
    caption: 'Rooms are lit to show materials as they are, without flattening the surfaces that sell them.',
  },
  {
    src: shotWeather,
    alt: 'A forested valley under low cloud',
    title: 'Weather',
    caption: 'Fog and rain are treated as conditions to work with, not days to write off.',
  },
  {
    src: shotAfterDark,
    alt: 'Mountains photographed after dark',
    title: 'After dark',
    caption: 'Long exposures for the hours most commissions do not stay for.',
  },
];

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);
  const descs = ['Architecture photographed in the natural hour the building was designed for.', 'Editorial work that reads as story, not spec sheet.', 'Wilderness and landscape shot with patience, not stock coverage.', 'Archival prints, editions, and frames worth the wall.'];
  const features = [
    { icon: Layers, title: 'Architectural', desc: descs[0] },
    { icon: Sparkles, title: 'Editorial', desc: descs[1] },
    { icon: Zap, title: 'Wilderness', desc: descs[2] },
    { icon: Award, title: 'Print Sales', desc: descs[3] },
  ];
  const stats = [
    { value: '250', label: 'Published shoots' },
    { value: '19', label: 'Exhibitions' },
    { value: '1.5m', label: 'Print admirers' },
    { value: '8', label: 'Print editions' },
  ];
  const values = ['Shot on medium format film', 'Lit only by the natural hour', 'Archival, exhibition-grade prints'];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
                <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center">
              <span className="inline-flex items-center gap-2 section-eyebrow justify-center">
                <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
                {t('Home.eyebrow', t('Home.eyebrow', 'PHOTOGRAPHY'))}
              </span>
              <h1 className="mt-5 text-[2.4rem] sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.02] max-w-3xl mx-auto">
                <span style={{ color: 'var(--t-heading)' }}>Chasing the hour</span>{' '}
                <span style={{ color: 'var(--t-primary)' }}>the light turns</span>
              </h1>
              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">
                {t('Home.lead', t('Home.lead', 'Architecture, people and wilderness, photographed in the warmest hour of the day.'))}
              </p>
              <div className="mt-8 flex flex-wrap gap-3 justify-center">
                <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                  {t('Home.commission', t('Home.commission', 'Commission a Shoot'))}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-7 py-3">
                  {t('Home.galleries', t('Home.galleries', 'View Galleries'))}
                </Link>
              </div>
            </div>
            <div className="mt-14 grid grid-cols-2 lg:grid-cols-4 gap-3">
              {features.map((f, i) => (
                <div
                  key={f.title}
                  className={`card-panel p-6 card-lift ${i % 2 === 1 ? 'lg:mt-10' : ''}`}
                  data-reveal
                >
                  <f.icon className="h-5 w-5" style={{ color: 'var(--t-primary)' }} aria-hidden="true" />
                  <p className="mt-3 text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>
                    {f.title}
                  </p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    {f.desc}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-14 flex flex-wrap items-center justify-center gap-x-12 gap-y-4 border-t border-[var(--t-border)] pt-8">
              {stats.map((s) => (
                <div key={s.label} className="text-center">
                  <p className="text-2xl font-extrabold" style={{ color: 'var(--t-primary)' }}>
                    {s.value}
                  </p>
                  <p className="text-xs uppercase tracking-wider text-slate-500">{s.label}</p>
                </div>
              ))}
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
              <h2 className="section-heading mb-4">Photography is sold by the lens, not the light</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                Clients are quoted resolutions, sensors and backdrops. The pictures that move people are made in the hour of light and the patience to wait for it.
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Sparkles className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  Studio Lumen fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Studio Lumen is a photographer's collective documenting architecture, people and wilderness in the warmest hour of the day.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24 border-t border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.selected_frames', 'Selected frames')}</p>
              <h2 className="section-heading">Wilderness and architecture, at the hour that suits them</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Six frames from the three kinds of commission Studio Lumen takes on.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {selectedFrames.map((shot) => (
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
                    className="h-48 w-full object-cover"
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
              <h2 className="section-heading">What working with Studio Lumen feels like</h2>
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
                However you come to Studio Lumen, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Sparkles className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Architectural Firms</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Studios that want their buildings photographed with the quiet light they designed for.</p>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Award className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Editorial Teams</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Magazines commissioning warmth, not corporate crispness.</p>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Users className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Collection Buyers</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Print buyers who are collecting the hour itself.</p>
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Commission</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">A defined shoot, one location, the warm hour.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 2,500 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Full-day golden-hour shoot
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Edited selects
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Usage licence
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Editorial</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">A story, told in sequence.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 6,000 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Multi-day coverage
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Story selects & edits
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Broad licence
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Print Series</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Edition prints from the archive.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 900 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Archival paper
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Numbered edition
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Certificate + frame option
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
                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>Studio Lumen</th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">Commercial studios</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Moment</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Golden hour, waited for
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Booked window, any light
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Process</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Medium format film
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Batch digital
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Story</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Sequence and warmth
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        One-off crisp shots
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Prints</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Archival editions
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Print-on-demand
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Patience</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        The work's core
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        The invoice's enemy
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
                  The building finally exists in pictures the way the morning designed it. Our clients see the project as an experience now, not a file.
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    MD
                  </span>
                  <div>
                    <p className="font-semibold text-sm">Marc Dubois</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Principal architect</p>
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
              <p className="section-eyebrow">The Studio Lumen difference</p>
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Why 'the warmest hour'?</span>
                  {openFaq === 0 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 0 && (
                  <p id="faq-panel-0" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    The work is built around golden hour and the light it makes. That discipline is the studio's signature — not filters.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>What film and process do you use?</span>
                  {openFaq === 1 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 1 && (
                  <p id="faq-panel-1" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Primarily medium format film, scanned and printed archivally. Digital is used where the story requires it.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Can we licence work broadly?</span>
                  {openFaq === 2 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 2 && (
                  <p id="faq-panel-2" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Yes — editorial and commission pricing includes clear, honest usage licences.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Are prints really archival?</span>
                  {openFaq === 3 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 3 && (
                  <p id="faq-panel-3" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Fibre-based paper, archival inks, numbered editions with certificates.
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
                  Commission a Shoot <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  View Galleries
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
