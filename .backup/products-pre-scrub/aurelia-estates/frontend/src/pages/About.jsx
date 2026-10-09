import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ShieldCheck, Users, Award, Check, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const stats = [
  { value: t('About.12k', '12k'), label: t('About.listings_curated', t('About.listings_curated', 'Listings curated')) },
  { value: '$4.8B', label: t('About.portfolio_value', t('About.portfolio_value', 'Portfolio value')) },
  { value: t('About.98', '98%'), label: t('About.client_satisfaction', t('About.client_satisfaction', 'Client satisfaction')) },
  { value: t('About.40', '40+'), label: t('About.countries_served', t('About.countries_served', 'Countries served')) },
];

export default function About() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              LUXURY REAL ESTATE
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Exceptional residences, curated for the discerning.
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Aurelia Estates brokers the world\'s most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
            <div>
              <h2 className="section-heading">{t('About.a_brand_built_on_standards', t('About.a_brand_built_on_standards', t('About.a_brand_built_on_standards', 'A brand built on standards')))}</h2>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">
                <strong style={{ color: 'var(--t-heading)' }}>{t('About.aurelia_estates', t('About.aurelia_estates', t('About.aurelia_estates', 'Aurelia Estates')))}</strong> was founded on a simple belief: that buying a home should feel considered, not transactional. Today we advise private clients, families and investors across prime markets, pairing institutional-grade research with the service of a boutique.
              </p>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">{t('About.we_exist_to_make_real_estate_feel_effortless_and_worth_recom', t('About.we_exist_to_make_real_estate_feel_effortless_and_worth_recom', t('About.we_exist_to_make_real_estate_feel_effortless_and_worth_recom', 'We exist to make real estate feel effortless and worth recommending — measured by results, retained by trust, and built to an international standard.')))}</p>
              <ul className="mt-8 space-y-3">
                <li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.iconic_homes_discreetly_sourced', t('About.iconic_homes_discreetly_sourced', t('About.iconic_homes_discreetly_sourced', 'Iconic homes, discreetly sourced')))}</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.every_residence_hand_verified_by_our_concierge', t('About.every_residence_hand_verified_by_our_concierge', t('About.every_residence_hand_verified_by_our_concierge', 'Every residence hand-verified by our concierge')))}</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.tailored_financing_for_global_buyers', t('About.tailored_financing_for_global_buyers', t('About.tailored_financing_for_global_buyers', 'Tailored financing for global buyers')))}</span>
                </li>
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.12k', t('About.12k', '12k'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.listings_curated', t('About.listings_curated', t('About.listings_curated', 'Listings curated')))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>$4.8B</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.portfolio_value', t('About.portfolio_value', t('About.portfolio_value', 'Portfolio value')))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.98', t('About.98', '98%'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.client_satisfaction', t('About.client_satisfaction', t('About.client_satisfaction', 'Client satisfaction')))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.40', t('About.40', '40+'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.countries_served', t('About.countries_served', t('About.countries_served', 'Countries served')))}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('About.what_guides_us', t('About.what_guides_us', t('About.what_guides_us', 'What guides us')))}</p>
              <h2 className="section-heading">{t('About.principles_we_do_not_trade_away', t('About.principles_we_do_not_trade_away', t('About.principles_we_do_not_trade_away', 'Principles we do not trade away')))}</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <ShieldCheck className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('About.verified_listings', t('About.verified_listings', t('About.verified_listings', 'Verified Listings')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('About.every_residence_is_inspected_and_title_checked_before_it_rea', t('About.every_residence_is_inspected_and_title_checked_before_it_rea', t('About.every_residence_is_inspected_and_title_checked_before_it_rea', 'Every residence is inspected and title-checked before it reaches your shortlist.')))}</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Users className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('About.private_clients', t('About.private_clients', t('About.private_clients', 'Private Clients')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('About.most_of_our_business_comes_from_referrals_discretion_is_the_', t('About.most_of_our_business_comes_from_referrals_discretion_is_the_', t('About.most_of_our_business_comes_from_referrals_discretion_is_the_', 'Most of our business comes from referrals — discretion is the default, not an extra.')))}</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Award className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('About.market_leaders', t('About.market_leaders', t('About.market_leaders', 'Market Leaders')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('About.recognised_across_prime_markets_for_record_setting_sales_and', t('About.recognised_across_prime_markets_for_record_setting_sales_and', t('About.recognised_across_prime_markets_for_record_setting_sales_and', 'Recognised across prime markets for record-setting sales and honest advice.')))}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 card-lift"
              data-reveal
              style={{ background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)', boxShadow: '0 30px 60px rgba(0,0,0,0.25)' }}
            >
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Ready to start with Aurelia Estates?
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Talk to the team, get a clear plan, and see exactly what the first step looks like.
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
                  to="/services"
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
