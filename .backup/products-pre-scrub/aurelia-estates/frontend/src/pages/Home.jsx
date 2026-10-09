import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { MapPin, Building2, ShieldCheck, TrendingUp, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus, Search, Globe } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);
  const descs = [t('Home.off_market_inventory_shared_only_with_pre_vetted_clients_bef', t('Home.off_market_inventory_shared_only_with_pre_vetted_clients_bef', 'Off-market inventory shared only with pre-vetted clients, before it ever touches a portal.')), t('Home.dedicated_concierge_covering_viewings_financing_introduction', t('Home.dedicated_concierge_covering_viewings_financing_introduction', 'Dedicated concierge covering viewings, financing introductions and relocation logistics.')), t('Home.a_curated_portfolio_across_40_countries_coordinated_by_a_sin', t('Home.a_curated_portfolio_across_40_countries_coordinated_by_a_sin', 'A curated portfolio across 40+ countries, coordinated by a single senior advisor.')), t('Home.anonymised_negotiations_and_strict_privacy_for_high_profile_', t('Home.anonymised_negotiations_and_strict_privacy_for_high_profile_', 'Anonymised negotiations and strict privacy for high-profile sellers and buyers.'))];
  const features = [
    { icon: MapPin, title: t('Home.private_off_market_listings', t('Home.private_off_market_listings', 'Private Off-Market Listings')), desc: descs[0] },
    { icon: Building2, title: t('Home.bespoke_concierge_service', t('Home.bespoke_concierge_service', 'Bespoke Concierge Service')), desc: descs[1] },
    { icon: ShieldCheck, title: t('Home.prime_international_portfolios', t('Home.prime_international_portfolios', 'Prime International Portfolios')), desc: descs[2] },
    { icon: TrendingUp, title: t('Home.discreet_sales_advisory', t('Home.discreet_sales_advisory', 'Discreet Sales Advisory')), desc: descs[3] },
  ];
  const stats = [
    { value: '12k', label: t('Home.listings_curated', t('Home.listings_curated', 'Listings curated')) },
    { value: '$4.8B', label: t('Home.portfolio_value', t('Home.portfolio_value', 'Portfolio value')) },
    { value: t('Home.98', '98%'), label: t('Home.client_satisfaction', t('Home.client_satisfaction', 'Client satisfaction')) },
    { value: '40+', label: t('Home.countries_served', t('Home.countries_served', 'Countries served')) },
  ];
  const values = [t('Home.iconic_homes_discreetly_sourced', t('Home.iconic_homes_discreetly_sourced', 'Iconic homes, discreetly sourced')), t('Home.every_residence_hand_verified_by_our_concierge', t('Home.every_residence_hand_verified_by_our_concierge', 'Every residence hand-verified by our concierge')), t('Home.tailored_financing_for_global_buyers', t('Home.tailored_financing_for_global_buyers', 'Tailored financing for global buyers'))];

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
                LUXURY REAL ESTATE
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
                Find a home worthy of your story
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-8 max-w-xl">
                Aurelia Estates brokers the world's most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  Book a Private Viewing <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  Explore Residences
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
                <p className="section-eyebrow mb-3">{t('Home.why_aurelia_estates', t('Home.why_aurelia_estates', t('Home.why_aurelia_estates', 'Why Aurelia Estates')))}</p>
                <p className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>
                  12k
                  <span className="text-xl font-bold text-primary"> Listings curated</span>
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Aurelia Estates brokers the world's most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>$4.8B</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{t('Home.portfolio_value', t('Home.portfolio_value', t('Home.portfolio_value', 'Portfolio value')))}</p>
                </div>
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('Home.98', t('Home.98', '98%'))}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{t('Home.client_satisfaction', t('Home.client_satisfaction', t('Home.client_satisfaction', 'Client satisfaction')))}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
              <span>{t('Home.as_seen_in', t('Home.as_seen_in', t('Home.as_seen_in', 'As seen in')))}</span>
              <span className="opacity-80">{t('Home.forbes', t('Home.forbes', 'Forbes'))}</span>
              <span className="opacity-80">{t('Home.bloomberg', t('Home.bloomberg', 'Bloomberg'))}</span>
              <span className="opacity-80">{t('Home.the_times', t('Home.the_times', t('Home.the_times', 'The Times')))}</span>
              <span className="opacity-80">{t('Home.designweek', t('Home.designweek', 'DesignWeek'))}</span>
              <span className="opacity-80">{t('Home.monocle', t('Home.monocle', 'Monocle'))}</span>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-eyebrow">{t('Home.the_problem', t('Home.the_problem', t('Home.the_problem', 'The problem')))}</p>
              <h2 className="section-heading mb-4">{t('Home.the_right_home_is_out_there_most_buyers_never_see_it', t('Home.the_right_home_is_out_there_most_buyers_never_see_it', t('Home.the_right_home_is_out_there_most_buyers_never_see_it', 'The right home is out there — most buyers never see it')))}</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                Prime residences rarely reach the open market. They trade quietly between collectors, and the buyer who waits for a listing ends up with what is left over, not what they wanted.
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Search className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  Aurelia Estates fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Aurelia Estates brokers the world's most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('Home.capabilities', t('Home.capabilities', 'Capabilities'))}</p>
              <h2 className="section-heading">{t('Home.what_working_with_aurelia_estates_feels_like', t('Home.what_working_with_aurelia_estates_feels_like', t('Home.what_working_with_aurelia_estates_feels_like', 'What working with Aurelia Estates feels like')))}</h2>
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
              <p className="section-eyebrow">{t('Home.who_it_is_for', t('Home.who_it_is_for', t('Home.who_it_is_for', 'Who it is for')))}</p>
              <h2 className="section-heading">{t('Home.made_for_people_like_you', t('Home.made_for_people_like_you', t('Home.made_for_people_like_you', 'Made for people like you')))}</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                However you come to Aurelia Estates, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Building2 className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>{t('Home.homeowners', t('Home.homeowners', 'Homeowners'))}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('Home.owners_of_one_of_one_residences_who_want_discreet_high_trust', t('Home.owners_of_one_of_one_residences_who_want_discreet_high_trust', t('Home.owners_of_one_of_one_residences_who_want_discreet_high_trust', 'Owners of one-of-one residences who want discreet, high-trust representation when they sell.')))}</p>
                </div>
                <div key="1" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <TrendingUp className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>{t('Home.investors', t('Home.investors', 'Investors'))}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('Home.portfolio_buyers_chasing_yield_across_borders_who_need_trans', t('Home.portfolio_buyers_chasing_yield_across_borders_who_need_trans', t('Home.portfolio_buyers_chasing_yield_across_borders_who_need_trans', 'Portfolio buyers chasing yield across borders, who need transparent structuring and tax-aware advice.')))}</p>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <Globe className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>{t('Home.international_buyers', t('Home.international_buyers', t('Home.international_buyers', 'International Buyers')))}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('Home.global_families_relocating_or_acquiring_a_foothold_without_v', t('Home.global_families_relocating_or_acquiring_a_foothold_without_v', t('Home.global_families_relocating_or_acquiring_a_foothold_without_v', 'Global families relocating or acquiring a foothold — without visibility into local market quirks.')))}</p>
                </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">{t('Home.by_the_numbers', t('Home.by_the_numbers', t('Home.by_the_numbers', 'By the numbers')))}</p>
              <h2 className="section-heading">{t('Home.results_you_can_put_in_a_report', t('Home.results_you_can_put_in_a_report', t('Home.results_you_can_put_in_a_report', 'Results you can put in a report')))}</h2>
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
              <h2 className="section-heading">{t('Home.clear_pricing_no_surprises', t('Home.clear_pricing_no_surprises', t('Home.clear_pricing_no_surprises', 'Clear pricing, no surprises')))}</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Start light, upgrade when the results justify it.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div key="0" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>{t('Home.essential', t('Home.essential', 'Essential'))}</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t('Home.for_owners_ready_to_list_with_market_intelligence_behind_the', t('Home.for_owners_ready_to_list_with_market_intelligence_behind_the', t('Home.for_owners_ready_to_list_with_market_intelligence_behind_the', 'For owners ready to list with market intelligence behind them.')))}</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    3 <span className="text-sm font-semibold text-slate-400">{t('Home.s', t('Home.s', '/ %%'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Valuation & strategy
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Professional photography & staging advice
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Portal + private network listing
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
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t('Home.the_private_client_standard_for_homes_that_deserve_quiet_han', t('Home.the_private_client_standard_for_homes_that_deserve_quiet_han', t('Home.the_private_client_standard_for_homes_that_deserve_quiet_han', 'The private-client standard, for homes that deserve quiet handling.')))}</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    1.25 <span className="text-sm font-semibold text-slate-400">{t('Home.s', t('Home.s', '/ %%'))}</span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Essential
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Off-market positioning & outreach
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Dedicated transaction advisor
                    </li>
                  </ul>
                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">
                    View plan
                  </Link>
                </div>
                <div key="2" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{border: '1px solid var(--t-border)'}}>
                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>{t('Home.portfolio', t('Home.portfolio', 'Portfolio'))}</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t('Home.for_multi_asset_portfolios_across_borders_and_tax_regimes', t('Home.for_multi_asset_portfolios_across_borders_and_tax_regimes', t('Home.for_multi_asset_portfolios_across_borders_and_tax_regimes', 'For multi-asset portfolios across borders and tax regimes.')))}</p>
                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>
                    Custom <span className="text-sm font-semibold text-slate-400">/ </span>
                  </p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Everything in Signature
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Portfolio-wide strategy & phasing
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      Cross-border tax structuring
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
              <p className="section-eyebrow">{t('Home.why_choose_us', t('Home.why_choose_us', t('Home.why_choose_us', 'Why choose us')))}</p>
              <h2 className="section-heading">{t('Home.the_difference_side_by_side', t('Home.the_difference_side_by_side', t('Home.the_difference_side_by_side', 'The difference, side by side')))}</h2>
            </div>
            <div className="card-panel overflow-hidden" data-reveal>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--t-border)]">
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400"></th>
                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>{t('Home.aurelia_estates', t('Home.aurelia_estates', t('Home.aurelia_estates', 'Aurelia Estates')))}</th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">{t('Home.typical_agency', t('Home.typical_agency', t('Home.typical_agency', 'Typical agency')))}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>{t('Home.off_market_inventory', t('Home.off_market_inventory', t('Home.off_market_inventory', 'Off-market inventory')))}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Pre-vetted private network
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Public portal only
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>{t('Home.confidentiality', t('Home.confidentiality', 'Confidentiality'))}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        NDA-guided, anonymised
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Publicised marketing push
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>{t('Home.senior_advisor', t('Home.senior_advisor', t('Home.senior_advisor', 'Senior advisor')))}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        One dedicated partner
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Rotating agents
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>{t('Home.cross_border_reach', t('Home.cross_border_reach', t('Home.cross_border_reach', 'Cross-border reach')))}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        40+ countries coordinated
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Single city, single office
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-[var(--t-border)] last:border-0">
                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>{t('Home.provenance_research', t('Home.provenance_research', t('Home.provenance_research', 'Provenance research')))}</td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        Hand-verified histories
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">
                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />
                        Rarely verified
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
                  We sold in eleven days through a private channel we never knew existed. Aurelia handled everything with total discretion.
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    IM
                  </span>
                  <div>
                    <p className="font-semibold text-sm">{t('Home.isabelle_marchand', t('Home.isabelle_marchand', t('Home.isabelle_marchand', 'Isabelle Marchand')))}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{t('Home.european_family_office_principal', t('Home.european_family_office_principal', t('Home.european_family_office_principal', 'European family office principal')))}</p>
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
              <p className="section-eyebrow">{t('Home.the_aurelia_estates_difference', t('Home.the_aurelia_estates_difference', t('Home.the_aurelia_estates_difference', 'The Aurelia Estates difference')))}</p>
              <h2 className="section-heading">{t('Home.crafted_for_the_people_you_serve', t('Home.crafted_for_the_people_you_serve', t('Home.crafted_for_the_people_you_serve', 'Crafted for the people you serve')))}</h2>
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
              <h2 className="section-heading">{t('Home.questions_answered', t('Home.questions_answered', t('Home.questions_answered', 'Questions, answered')))}</h2>
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>{t('Home.are_your_listings_public', t('Home.are_your_listings_public', t('Home.are_your_listings_public', 'Are your listings public?')))}</span>
                  {openFaq === 0 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 0 && (
                  <p id="faq-panel-0" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Only a fraction of our inventory is ever listed publicly. Most residences are shared privately with matched buyers for days before any marketing.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>{t('Home.how_do_you_keep_a_sale_confidential', t('Home.how_do_you_keep_a_sale_confidential', t('Home.how_do_you_keep_a_sale_confidential', 'How do you keep a sale confidential?')))}</span>
                  {openFaq === 1 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 1 && (
                  <p id="faq-panel-1" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    We sign non-disclosure agreements with every party, run anonymised viewings and never publish addresses or photography without consent.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>{t('Home.do_you_work_with_international_buyers', t('Home.do_you_work_with_international_buyers', t('Home.do_you_work_with_international_buyers', 'Do you work with international buyers?')))}</span>
                  {openFaq === 2 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 2 && (
                  <p id="faq-panel-2" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Around 40%% of our closings involve an international buyer. We coordinate currency, legal and relocation timelines end to end.
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
                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>{t('Home.what_makes_your_valuation_credible', t('Home.what_makes_your_valuation_credible', t('Home.what_makes_your_valuation_credible', 'What makes your valuation credible?')))}</span>
                  {openFaq === 3 ? (
                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />
                  )}
                </button>
                {openFaq === 3 && (
                  <p id="faq-panel-3" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    We benchmark every property against comparable private transactions — not just portal asking prices — and share the reasoning with you.
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
                  Book a Private Viewing <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  Explore Residences
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
