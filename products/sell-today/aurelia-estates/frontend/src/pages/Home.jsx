import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { MapPin, Building2, ShieldCheck, TrendingUp, Quote, Star, ArrowRight, CheckCircle2, Check, Plus, Minus, Search, Globe, Key, Sparkles, ChevronRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import heroImage from '../assets/images/hero.jpg';
import heroBackdrop from '../assets/images/luxury-villa.jpg';
import shotInteriors from '../assets/images/interior-lux.jpg';
import shotCity from '../assets/images/modern-home.jpg';
import shotViews from '../assets/images/condo-view.jpg';
import shotClientDesk from '../assets/images/agent.jpg';

// Shipped assets, imported so the bundler fingerprints them and they resolve under
// the GitHub Pages project subpath.
const gallery = [
  {
    src: shotInteriors,
    alt: 'A furnished interior of a residence',
    title: 'Interiors',
    caption: 'Rooms are documented the way they will be lived in, rather than at the widest angle a lens allows.',
  },
  {
    src: shotCity,
    alt: 'A contemporary house photographed from outside',
    title: 'City residences',
    caption: 'Penthouses and townhouses are shown to the clients they suit — nothing reaches a portal first.',
  },
  {
    src: shotViews,
    alt: 'A view out over a city from an upper floor',
    title: 'Outlook',
    caption: 'Aspect, light and sightlines are recorded as part of the valuation, not left to the viewing.',
  },
  {
    src: shotClientDesk,
    alt: 'A private client advisor',
    title: 'Private client desk',
    caption: 'One named advisor for viewings, financing introductions and relocation.',
  },
];

export default function Home() {
  const { t } = useTranslation();
  const [openFaq, setOpenFaq] = useState(0);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">

        {/* ===== HERO: elegant split, real penthouse/heritage imagery ===== */}
        <section className="relative overflow-hidden pt-14 lg:pt-0">
          {/* depth layer */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,var(--t-primary)_0%,transparent_65%)] opacity-15" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,var(--t-accent)_0%,transparent_65%)] opacity-15" />
            <img
              src={heroBackdrop}
              alt=""
              aria-hidden="true"
              className="absolute inset-0 h-full w-full object-cover object-center scale-110"
              style={{ filter: 'blur(2px) grayscale(15%) brightness(0.8)' }}
            />
          </div>

          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* left: headline + lead + CTAs */}
            <div>
              <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.4em] text-[var(--t-primary)] section-eyebrow">
                <span className="h-1 w-1 rounded-full bg-[var(--t-primary)]" />
                {t('Home.eyebrow', 'LUXURY REAL ESTATE')}
              </span>

              <h1 className="mt-6 text-5xl sm:text-6xl lg:text-7xl font-black leading-[1.05] tracking-tight">
                <span style={{ color: 'var(--t-heading)' }}>Find a home</span>
                <br />
                <span className="bg-gradient-to-r from-[var(--t-primary)] to-[var(--t-accent)] bg-clip-text text-transparent">
                  worthy of your story
                </span>
              </h1>

              <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">
                {t('Home.lead', 'Distinctive residences — penthouse, villa and heritage — with white-glove private client service.')}
              </p>

              <div className="mt-8 flex flex-wrap gap-4">
                <Link to="/contact" className="btn-primary text-sm inline-flex items-center gap-2 px-7 py-3">
                  {t('Home.book_viewing', 'Book a Private Viewing')}
                  <ChevronRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm inline-flex items-center gap-2 px-7 py-3">
                  {t('Home.explore', 'Explore Residences')}
                </Link>
              </div>

              {/* elegance strip */}
              <div className="mt-10 flex flex-wrap items-center gap-6 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Globe className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.countries_served', '40+ countries')}
                </span>
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.anonymised_negotiations_and_strict_privacy_for_high_profile_', 'Strict confidentiality')}
                </span>
                <span className="flex items-center gap-1.5">
                  <Key className="h-4 w-4 text-[var(--t-primary)]" />
                  {t('Home.dedicated_concierge_covering_viewings_financing_introduction', 'Dedicated concierge')}
                </span>
              </div>
            </div>

            {/* right: real imagery hero block */}
            <div className="relative" data-reveal>
              <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src={heroImage}
                  alt="A modern residence represented by Aurelia Estates"
                  loading="eager"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '520px' }}
                />
                <div className="absolute bottom-0 left-0 right-0 p-5 bg-gradient-to-t from-black/60 to-transparent">
                  <div className="flex items-center gap-3 text-white">
                    <div className="h-10 w-10 rounded-full bg-[var(--t-primary)] flex items-center justify-center text-white text-sm font-bold">
                      AE
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Aurelia Estates</p>
                      <p className="text-xs opacity-80">Private client service</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-4 -left-4 rounded-xl bg-surface/90 backdrop-blur p-4 shadow-lg border border-[var(--t-border)] flex items-center gap-3 data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-10 w-10 rounded-lg bg-[var(--t-primary)] flex items-center justify-center text-white">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>Off-market first</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Before it hits any portal</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== STAT BAR ===== */}
        <div className="border-y border-[var(--t-border)] bg-surface/70">
          <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-2 lg:grid-cols-4 gap-y-6 gap-x-6 text-center lg:text-left">
            {[
              { value: '12k', label: t('Home.listings_curated', 'Listings curated') },
              { value: '$4.8B', label: t('Home.portfolio_value', 'Portfolio value') },
              { value: t('Home.98', '98%'), label: t('Home.client_satisfaction', 'Client satisfaction') },
              { value: '40+', label: t('Home.countries_served', 'Countries served') },
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

        {/* ===== AS SEEN IN STRIP ===== */}
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
                {t('Home.the_right_home_is_out_there_most_buyers_never_see_it', 'The right home is out there — most buyers never see it')}
              </h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                Prime residences rarely reach the open market. They trade quietly between collectors, and the buyer who waits for a listing ends up with what is left over, not what they wanted.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-500 dark:text-slate-400">
                {['Off-market first', 'Discreet viewings', 'Senior advisor', 'Cross-border coordination'].map((b) => (
                  <span key={b} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface/60 border border-[var(--t-border)]">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" />
                    {b}
                  </span>
                ))}
              </div>
            </div>

            <div className="data-[revealed=false]:opacity-0" data-reveal>
              <div className="card-panel rounded-2xl p-8 bg-surface border border-[var(--t-border)] shadow-lg max-w-sm w-full">
                <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <Search className="h-7 w-7" />
                </div>
                <p className="font-bold text-xl" style={{ color: 'var(--t-heading)' }}>
                  Aurelia Estates fixes this
                </p>
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We broker the world's most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.
                </p>
                <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Off-market
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Discreet
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Check className="h-3.5 w-3.5 text-[var(--t-primary)]" /> Senior-led
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
                {t('Home.what_working_with_aurelia_estates_feels_like', 'What working with Aurelia Estates feels like')}
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Four disciplines, one standard: international, uncompromising, and completely yours.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {[
                { icon: MapPin, title: t('Home.private_off_market_listings', 'Private Off-Market Listings'), desc: t('Home.off_market_inventory_shared_only_with_pre_vetted_clients_bef', 'Off-market inventory shared only with pre-vetted clients, before it ever touches a portal.') },
                { icon: Building2, title: t('Home.bespoke_concierge_service', 'Bespoke Concierge Service'), desc: t('Home.dedicated_concierge_covering_viewings_financing_introduction', 'Dedicated concierge covering viewings, financing introductions and relocation logistics.') },
                { icon: ShieldCheck, title: t('Home.prime_international_portfolios', 'Prime International Portfolios'), desc: t('Home.a_curated_portfolio_across_40_countries_coordinated_by_a_sin', 'A curated portfolio across 40+ countries, coordinated by a single senior advisor.') },
                { icon: TrendingUp, title: t('Home.discreet_sales_advisory', 'Discreet Sales Advisory'), desc: t('Home.anonymised_negotiations_and_strict_privacy_for_high_profile_', 'Anonymised negotiations and strict privacy for high-profile sellers and buyers.') },
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
                However you come to Aurelia Estates, the standard is the same.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                { icon: Building2, title: t('Home.homeowners', 'Homeowners'), desc: t('Home.owners_of_one_of_one_residences_who_want_discreet_high_trust', 'Owners of one-of-one residences who want discreet, high-trust representation when they sell.') },
                { icon: TrendingUp, title: t('Home.investors', 'Investors'), desc: t('Home.portfolio_buyers_chasing_yield_across_borders_who_need_trans', 'Portfolio buyers chasing yield across borders, who need transparent structuring and tax-aware advice.') },
                { icon: Globe, title: t('Home.international_buyers', 'International Buyers'), desc: t('Home.global_families_relocating_or_acquiring_a_foothold_without_v', 'Global families relocating or acquiring a foothold — without visibility into local market quirks.') },
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
                { value: '12k', label: t('Home.listings_curated', 'Listings curated') },
                { value: '$4.8B', label: t('Home.portfolio_value', 'Portfolio value') },
                { value: t('Home.98', '98%'), label: t('Home.client_satisfaction', 'Client satisfaction') },
                { value: '40+', label: t('Home.countries_served', 'Countries served') },
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
                  title: t('Home.essential', 'Essential'),
                  desc: t('Home.for_owners_ready_to_list_with_market_intelligence_behind_the', 'For owners ready to list with market intelligence behind them.'),
                  price: '3',
                  unit: t('Home.s', '/ %%'),
                  highlight: false,
                  features: [t('Home.valuation_and_strategy', 'Valuation & strategy'), t('Home.professional_photography_and_staging_advice', 'Professional photography & staging advice'), t('Home.portal_and_private_network_listing', 'Portal + private network listing')],
                },
                {
                  title: t('Home.signature', 'Signature'),
                  desc: t('Home.the_private_client_standard_for_homes_that_deserve_quiet_han', 'The private-client standard, for homes that deserve quiet handling.'),
                  price: '1.25',
                  unit: t('Home.s', '/ %%'),
                  highlight: true,
                  badge: t('Home.most_popular', 'Most popular'),
                  features: [t('Home.everything_in_essential', 'Everything in Essential'), t('Home.off_market_positioning_and_outreach', 'Off-market positioning & outreach'), t('Home.dedicated_transaction_advisor', 'Dedicated transaction advisor')],
                },
                {
                  title: t('Home.portfolio', 'Portfolio'),
                  desc: t('Home.for_multi_asset_portfolios_across_borders_and_tax_regimes', 'For multi-asset portfolios across borders and tax regimes.'),
                  price: t('Home.custom', 'Custom'),
                  unit: ' ',
                  highlight: false,
                  features: [t('Home.everything_in_signature', 'Everything in Signature'), t('Home.portfolio_wide_strategy_and_phasing', 'Portfolio-wide strategy & phasing'), t('Home.cross_border_tax_structuring', 'Cross-border tax structuring')],
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
                      {t('Home.aurelia_estates', 'Aurelia Estates')}
                    </th>
                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">
                      {t('Home.typical_agency', 'Typical agency')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: t('Home.off_market_inventory', 'Off-market inventory'), ours: t('Home.pre_vetted_private_network', 'Pre-vetted private network'), theirs: t('Home.public_portal_only', 'Public portal only') },
                    { label: t('Home.confidentiality', 'Confidentiality'), ours: t('Home.nda_guided_anonymised', 'NDA-guided, anonymised'), theirs: t('Home.publicised_marketing_push', 'Publicised marketing push') },
                    { label: t('Home.senior_advisor', 'Senior advisor'), ours: t('Home.one_dedicated_partner', 'One dedicated partner'), theirs: t('Home.rotating_agents', 'Rotating agents') },
                    { label: t('Home.cross_border_reach', 'Cross-border reach'), ours: t('Home._40_countries_coordinated', '40+ countries coordinated'), theirs: t('Home.single_city_single_office', 'Single city, single office') },
                    { label: t('Home.provenance_research', 'Provenance research'), ours: t('Home.hand_verified_histories', 'Hand-verified histories'), theirs: t('Home.rarely_verified', 'Rarely verified') },
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

        {/* ===== PORTFOLIO SNAPSHOT: real local imagery ===== */}
        <section className="py-20 lg:py-24 border-b border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-12">
              <p className="section-eyebrow">{t('Home.inside_the_portfolio', 'Inside the portfolio')}</p>
              <h2 className="section-heading" style={{ color: 'var(--t-heading)' }}>
                {t('Home.how_a_residence_is_represented', 'How a residence is represented')}
              </h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Interiors, exterior, outlook and the advisor who handles the file — the four things a private buyer asks about first.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {gallery.map((shot) => (
                <figure
                  key={shot.title}
                  className="card-panel rounded-xl overflow-hidden border border-[var(--t-border)] bg-surface/60 h-full flex flex-col"
                  data-reveal
                >
                  <img
                    src={shot.src}
                    alt={shot.alt}
                    loading="lazy"
                    decoding="async"
                    width="900"
                    height="500"
                    className="h-44 w-full object-cover"
                  />
                  <figcaption className="p-5">
                    <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>
                      {shot.title}
                    </p>
                    <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                      {shot.caption}
                    </p>
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>

        {/* ===== TESTIMONIAL SPLIT ===== */}
        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="relative data-[revealed=false]:opacity-0" data-reveal>
              <div className="rounded-2xl overflow-hidden shadow-xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src={heroBackdrop}
                  alt="A villa represented by Aurelia Estates"
                  loading="lazy"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            </div>

            <div>
              <p className="section-eyebrow">The Aurelia Estates difference</p>
              <h2 className="section-heading mt-2" style={{ color: 'var(--t-heading)' }}>
                {t('Home.crafted_for_the_people_you_serve', 'Crafted for the people you serve')}
              </h2>

              <div className="card-panel mt-8 p-7 rounded-2xl bg-surface border border-[var(--t-border)] shadow-md data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white mb-5 shadow-md">
                  <Quote className="h-6 w-6" />
                </div>
                <blockquote className="text-xl font-medium leading-relaxed mb-6" style={{ color: 'var(--t-heading)' }}>
                  We sold in eleven days through a private channel we never knew existed. Aurelia handled everything with total discretion.
                </blockquote>
                <div className="flex items-center gap-4">
                  <div className="h-11 w-11 rounded-full bg-gradient-to-br from-[var(--t-primary)] to-[var(--t-accent)] flex items-center justify-center text-white text-sm font-bold">
                    IM
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{t('Home.isabelle_marchand', 'Isabelle Marchand')}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{t('Home.european_family_office_principal', 'European family office principal')}</p>
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
                  t('Home.iconic_homes_discreetly_sourced', 'Iconic homes, discreetly sourced'),
                  t('Home.every_residence_hand_verified_by_our_concierge', 'Every residence hand-verified by our concierge'),
                  t('Home.tailored_financing_for_global_buyers', 'Tailored financing for global buyers'),
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
                  q: t('Home.are_your_listings_public', 'Are your listings public?'),
                  a: t('Home.only_a_fraction_of_our_inventory_is_ever_listed_publicly_most_residences_are_shared_privately_with_matched_buyers_for_days_before_any_marketing', 'Only a fraction of our inventory is ever listed publicly. Most residences are shared privately with matched buyers for days before any marketing.'),
                },
                {
                  q: t('Home.how_do_you_keep_a_sale_confidential', 'How do you keep a sale confidential?'),
                  a: t('Home.we_sign_non_disclosure_agreements_with_every_party_run_anonymised_viewings_and_never_publish_addresses_or_photography_without_consent', 'We sign non-disclosure agreements with every party, run anonymised viewings and never publish addresses or photography without consent.'),
                },
                {
                  q: t('Home.do_you_work_with_international_buyers', 'Do you work with international buyers?'),
                  a: t('Home.around_40_of_our_closings_involve_an_international_buyer_we_coordinate_currency_legal_and_relocation_timelines_end_to_end', 'Around 40% of our closings involve an international buyer. We coordinate currency, legal and relocation timelines end to end.'),
                },
                {
                  q: t('Home.what_makes_your_valuation_credible', 'What makes your valuation credible?'),
                  a: t('Home.we_benchmark_every_property_against_comparable_private_transactions_not_just_portal_asking_prices_and_share_the_reasoning_with_you', 'We benchmark every property against comparable private transactions — not just portal asking prices — and share the reasoning with you.'),
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
                  Book a Private Viewing <ChevronRight className="h-4 w-4" />
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
