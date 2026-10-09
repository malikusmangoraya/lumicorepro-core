import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { MapPin, Star, Users, Sparkles, Quote, ArrowRight, CheckCircle2, Check, Plus, Minus, Plane, HeartHandshake } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import HeroVideo from '../components/media/HeroVideo';

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);
  const descs = ['Groups of twelve or fewer, sized so the story can breathe.', 'Briefings and kitchens led by locals — the narrator is from the place.', 'Itineraries built from your dates, tastes and pace — never copied.', 'Stays with owners and operators who keep guest money in the district.'];
  const features = [
    { icon: MapPin, title: 'Small-Group Journeys', desc: descs[0] },
    { icon: Star, title: 'Local Storytellers', desc: descs[1] },
    { icon: Users, title: 'Bespoke Itineraries', desc: descs[2] },
    { icon: Sparkles, title: 'Sustainable Stays', desc: descs[3] },
  ];
  const stats = [
    { value: '60+', label: 'Curated journeys' },
    { value: '8', label: 'Destinations' },
    { value: t('Home.4_9', '4.9'), label: 'Traveler rating' },
    { value: '0.5%', label: 'Carbon-footprint pledge' },
  ];
  const values = ['Itineraries designed by locals', 'Small groups, maximum authenticity', 'Travel that gives back'];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
                <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-3xl lg:ml-auto lg:text-right">
              <span className="section-eyebrow">
                {t('Home.eyebrow', t('Home.eyebrow', 'BOUTIQUE TRAVEL'))}
              </span>
              <h1 className="mt-5 text-[2.6rem] sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.96]">
                <span style={{ color: 'var(--t-primary)' }}>Travel the way</span>{' '}
                <span style={{ color: 'var(--t-heading)' }}>it once felt</span>
              </h1>
              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed lg:ml-auto max-w-xl">
                {t('Home.lead', t('Home.lead', 'Small-group journeys through local kitchens, stories and landscapes.'))}
              </p>
              <div className="mt-8 flex flex-wrap gap-3 lg:justify-end">
                <Link to="/contact" className="btn-primary text-sm px-7 py-3">
                  {t('Home.plan_journey', t('Home.plan_journey', 'Plan Your Journey'))}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-7 py-3">
                  {t('Home.itineraries', t('Home.itineraries', 'View Itineraries'))}
                </Link>
              </div>
            </div>
            <div className="mt-14">
              <HeroVideo
                src="media/hero.mp4"
                poster="media/hero-poster.jpg"
                alt="Aerial view of waves meeting a tropical beach"
                caption="Aerial over the Saffron coast"
                aspect="21 / 9"
              />
            </div>
            <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((f) => (
                <div key={f.title} data-reveal>
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
              <h2 className="section-heading mb-4">Travel sells the picture, not the place</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                Group travel is a bus at sunrise and a hotel chain at dusk. Travellers are asking for rooms with a story — and the industry keeps answering with itineraries.
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Plane className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  Saffron Voyage fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Saffron Voyage curates small-group journeys through the stories, kitchens and landscapes of South Asia — led by local storytellers.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.capabilities', t('Home.capabilities', 'Capabilities'))}</p>
              <h2 className="section-heading">What working with Saffron Voyage feels like</h2>
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
                However you come to Saffron Voyage, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Plane className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Experience Seekers</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Travellers who will pay for the morning of a real village over another monument photo.</p>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Users className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Small Groups</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Friends and families travelling together, who want space without being a coach party.</p>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <HeartHandshake className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>Ethical Travellers</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Guests who want their money to stay in the place they visit.</p>
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Journey Light</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Five days, one region, one story well told.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 1,400 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Group of 8-12
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Local narrator
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Owner-run stays
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
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>{t('Home.signature', t('Home.signature', 'Signature'))}</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">The full story arc: two regions, seven days.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 2,800 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Journey Light
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Private kitchens & craft visits
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Flexible pace
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>Private</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">An itinerary drawn for your travel party alone.</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    From 6,500 <span className="text-sm font-semibold text-slate-400">{t('Home.usd', t('Home.usd', '/ USD'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Your own narrator & driver
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Every stay owner-run
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      24/7 trip lead
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
                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>Saffron Voyage</th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">Mass group travel</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Group size</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        8-12, story-friendly
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Coach, 40+
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Narrator</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Local storyteller
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Distant guide
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Stays</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Owner-run, memorable
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Chain hotels
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Money flow</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Stays in the district
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Leaves the district
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>Pace</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Yours
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Itinerary's
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
                  We expected a tour. We got a villa with a grandmother's kitchen, a village feast and a morning that no brochure will ever hold.
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    AR
                  </span>
                  <div>
                    <p className="font-semibold text-sm">Ayesha Rahman</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Returning traveller, Dubai</p>
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
              <p className="section-eyebrow">The Saffron Voyage difference</p>
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>How large are the groups?</span>
                  {openFaq === 0 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 0 && (
                  <p id="faq-panel-0" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Twelve maximum, and most journeys sit at eight. The story needs room to breathe.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Who leads the travel?</span>
                  {openFaq === 1 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 1 && (
                  <p id="faq-panel-1" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Local storytellers — the person who grew up in the place narrates it.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>Can you help with visas and flights?</span>
                  {openFaq === 2 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 2 && (
                  <p id="faq-panel-2" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Our trip leads coordinate documentation and routing alongside the itinerary.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>How does the money flow?</span>
                  {openFaq === 3 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 3 && (
                  <p id="faq-panel-3" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Owner-run stays and local operators keep the majority of every fare in the district you visit.
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
                  Plan Your Journey <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  View Itineraries
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
