import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { BarChart3, ShieldCheck, TrendingUp, Lock, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);
  const descs = ['Fewer, deeper positions built on in-house fundamental research — conviction over diversification theatre.', 'Access to direct investments most private clients never see on a platform.', 'Family office services from a single accountable partner.', 'Quarterly reporting that names what we own, why, and what changed.'];
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
  const values = ['Long-horizon, low-churn holdings', 'In-house fundamental research', 'Quarterly, unfiltered transparency'];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-20 lg:pb-28">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6 flex flex-col items-center text-center">
            <div className="max-w-3xl mx-auto flex flex-col items-center">
              <span className="inline-flex items-center gap-2 section-eyebrow">
                <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
                PRIVATE CAPITAL
              </span>
              <h1
                className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.98] mb-6 mt-3"
                style={{
                  color: 'var(--t-heading)',
                  background: 'linear-gradient(115deg, var(--t-heading) 40%, var(--t-primary) 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Capital, deployed with conviction
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-8 max-w-xl">
                Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  Request Access <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  Our Approach
                </Link>
              </div>
              <ul className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                <li className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <CheckCircle2 className="h-4 w-4 text-primary" /> Internationally ranked, 4.9/5
                </li>
                <li className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <CheckCircle2 className="h-4 w-4 text-primary" /> Trusted in 40+ countries
                </li>
              </ul>
            </div>
            <div className="hidden lg:flex flex-col gap-6">
              <div className="glass-md rounded-2xl p-8 card-lift" data-reveal>
                <p className="section-eyebrow mb-3">Why Meridian Capital</p>
                <p className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>
                  $2.1B
                  <span className="text-xl font-bold text-primary"> AUM</span>
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>23%</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Annualized since inception</p>
                </div>
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>97%</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Capital retained</p>
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
              <h2 className="section-heading mb-4">Wealth management is built for averages</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                The industry sells diversified hubs and quarterly whatever-the-market-did. Families that want conviction, transparency and a long horizon are told to be patient with the mediocre.
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <BarChart3 className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  Meridian Capital fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Meridian Capital manages concentrated, long-horizon portfolios for founders and family offices, with transparent, quarterly reporting.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.capabilities', t('Home.capabilities', 'Capabilities'))}</p>
              <h2 className="section-heading">What working with Meridian Capital feels like</h2>
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
                However you come to Meridian Capital, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <BarChart3 className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Founders</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Founders whose exits created a concentration and a problem few advisors can actually handle.</p>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <TrendingUp className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Family Offices</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Offices that want direct research and real positions — not curated beta.</p>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <ShieldCheck className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Institutional Savers</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Long-horizon savers who would rather own the winners than rent an index.</p>
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Advisory</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Quarterly partner-led advice with full transparency.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    0.75 <span className="text-sm font-semibold text-slate-400">{t('Home.s', t('Home.s', '/ %%'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Partner-led reviews
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Full position disclosure
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Reporting suite
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Managed</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Direct investment and concentrated portfolios.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    1.15 <span className="text-sm font-semibold text-slate-400">{t('Home.s', t('Home.s', '/ %%'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Advisory
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Direct positions
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Tax-aware trading
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Family Office</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">The full architecture for complex wealth.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    Custom <span className="text-sm font-semibold text-slate-400">/ </span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Managed
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Multi-family board
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Estate & succession
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
                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>Meridian Capital</th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">Traditional wealth firms</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Positions</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Concentrated, direct
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Diversified hubs
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Research</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        In-house fundamental
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Broker sell-side
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Reporting</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Quarterly, unfiltered
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Statement shrugs
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Access</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Direct deal flow
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Closed to clients
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Accountability</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Named partner
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Team roulette
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
                  Our exit made money the average advisor couldn't think about. Meridian built a plan, named the positions and has never once hedged a conversation.
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    GV
                  </span>
                  <div>
                    <p className="font-semibold text-sm">Ghana Vetri</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Founder, post-exit</p>
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
              <p className="section-eyebrow">The Meridian Capital difference</p>
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>What do you mean by concentrated?</span>
                  {openFaq === 0 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 0 && (
                  <p id="faq-panel-0" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    We take meaningful positions in the businesses we understand best. Diversification is a byproduct of humility, not the strategy.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Who sees our holdings?</span>
                  {openFaq === 1 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 1 && (
                  <p id="faq-panel-1" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    A single named partner and a defined team. We operate under strict confidentiality agreements.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>What are the fees?</span>
                  {openFaq === 2 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 2 && (
                  <p id="faq-panel-2" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    A flat percentage of assets under management — no commissions, no hidden entrail percentages.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Is client money segregated?</span>
                  {openFaq === 3 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 3 && (
                  <p id="faq-panel-3" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Yes, with an independent custodian and quarterly reconciliation you can verify.
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
