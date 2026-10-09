import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Home, Key, Building2, Calculator, Compass, Eye, Handshake, ArrowRight, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const faqs = [
  { q: t('Services.what_areas_do_you_cover', t('Services.what_areas_do_you_cover', 'What areas do you cover?')), a: t('Services.we_advise_across_prime_urban_markets_and_selected_internatio', t('Services.we_advise_across_prime_urban_markets_and_selected_internatio', 'We advise across prime urban markets and selected international destinations. Book a consultation and we will confirm coverage for your specific property.')) },
  { q: t('Services.how_long_does_a_sale_usually_take', t('Services.how_long_does_a_sale_usually_take', 'How long does a sale usually take?')), a: t('Services.well_presented_properties_typically_go_under_offer_within_fo', t('Services.well_presented_properties_typically_go_under_offer_within_fo', 'Well-presented properties typically go under offer within four to six weeks. Your adviser will give you a realistic timeline at valuation.')) },
  { q: t('Services.do_you_handle_the_legal_side', t('Services.do_you_handle_the_legal_side', 'Do you handle the legal side?')), a: t('Services.we_coordinate_with_your_chosen_solicitor_or_can_introduce_ve', t('Services.we_coordinate_with_your_chosen_solicitor_or_can_introduce_ve', 'We coordinate with your chosen solicitor or can introduce vetted legal partners in each market.')) },
  { q: t('Services.what_are_your_fees', t('Services.what_are_your_fees', 'What are your fees?')), a: t('Services.fees_are_agreed_up_front_and_tiered_by_service_level_there_a', t('Services.fees_are_agreed_up_front_and_tiered_by_service_level_there_a', 'Fees are agreed up front and tiered by service level. There are no hidden charges — the quote you receive is the quote you pay.')) },
];

export default function Services() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(0);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              WHAT WE DO
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Aurelia Estates, in full
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Aurelia Estates brokers the world\'s most distinctive residences — penthouse, villa and heritage homes — with white-glove private client service.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Home className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('Services.buy_sell', t('Services.buy_sell', t('Services.buy_sell', 'Buy & Sell')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">{t('Services.represented_sales_and_acquisitions_of_prime_residential_prop', t('Services.represented_sales_and_acquisitions_of_prime_residential_prop', t('Services.represented_sales_and_acquisitions_of_prime_residential_prop', 'Represented sales and acquisitions of prime residential property, handled end-to-end with discretion.')))}</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Key className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('Services.rentals_lettings', t('Services.rentals_lettings', t('Services.rentals_lettings', 'Rentals & Lettings')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">{t('Services.long_let_and_short_let_management_for_landlords_and_internat', t('Services.long_let_and_short_let_management_for_landlords_and_internat', t('Services.long_let_and_short_let_management_for_landlords_and_internat', 'Long-let and short-let management for landlords and international tenants, fully managed.')))}</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Building2 className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('Services.new_developments', t('Services.new_developments', t('Services.new_developments', 'New Developments')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">{t('Services.off_plan_and_new_build_projects_from_launch_marketing_throug', t('Services.off_plan_and_new_build_projects_from_launch_marketing_throug', t('Services.off_plan_and_new_build_projects_from_launch_marketing_throug', 'Off-plan and new-build projects, from launch marketing through to completion and handover.')))}</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div><div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Calculator className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('Services.valuation_advisory', t('Services.valuation_advisory', t('Services.valuation_advisory', 'Valuation & Advisory')))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">{t('Services.independent_valuations_market_studies_and_investment_advice_', t('Services.independent_valuations_market_studies_and_investment_advice_', t('Services.independent_valuations_market_studies_and_investment_advice_', 'Independent valuations, market studies and investment advice backed by live transaction data.')))}</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">{t('Services.how_it_works', t('Services.how_it_works', t('Services.how_it_works', 'How it works')))}</p>
              <h2 className="section-heading">{t('Services.a_process_built_to_remove_surprises', t('Services.a_process_built_to_remove_surprises', t('Services.a_process_built_to_remove_surprises', 'A process built to remove surprises')))}</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
              <div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Compass className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>{t('Services.1_discover', t('Services.1_discover', '1. Discover'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">{t('Services.we_begin_with_a_private_consultation_to_understand_the_brief', t('Services.we_begin_with_a_private_consultation_to_understand_the_brief', t('Services.we_begin_with_a_private_consultation_to_understand_the_brief', 'We begin with a private consultation to understand the brief, the budget and the timing.')))}</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Eye className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>{t('Services.2_view', t('Services.2_view', '2. View'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">{t('Services.a_shortlist_of_hand_verified_residences_arranged_around_your', t('Services.a_shortlist_of_hand_verified_residences_arranged_around_your', t('Services.a_shortlist_of_hand_verified_residences_arranged_around_your', 'A shortlist of hand-verified residences, arranged around your schedule, in person or virtually.')))}</p>
              </div><div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Handshake className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{ color: 'var(--t-heading)' }}>{t('Services.3_close', t('Services.3_close', '3. Close'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">{t('Services.negotiation_due_diligence_and_completion_coordinated_by_a_si', t('Services.negotiation_due_diligence_and_completion_coordinated_by_a_si', t('Services.negotiation_due_diligence_and_completion_coordinated_by_a_si', 'Negotiation, due diligence and completion coordinated by a single point of contact.')))}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-3xl mx-auto px-6">
            <div className="max-w-2xl mb-10">
              <p className="section-eyebrow">{t('Services.questions', t('Services.questions', 'Questions'))}</p>
              <h2 className="section-heading">{t('Services.answers_before_you_ask', t('Services.answers_before_you_ask', t('Services.answers_before_you_ask', 'Answers before you ask')))}</h2>
            </div>
            <div className="space-y-3">
              {faqs.map((f, i) => (
                <div key={i} className="card-panel overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpen(open === i ? -1 : i)}
                    aria-expanded={open === i}
                    className="w-full flex items-center justify-between gap-4 p-5 text-left"
                  >
                    <span className="font-semibold text-sm" style={{ color: 'var(--t-heading)' }}>{f.q}</span>
                    <span className="text-primary text-xl leading-none">{open === i ? '−' : '+'}</span>
                  </button>
                  {open === i && (
                    <p className="px-5 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{f.a}</p>
                  )}
                </div>
              ))}
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
                  to="/pricing"
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
