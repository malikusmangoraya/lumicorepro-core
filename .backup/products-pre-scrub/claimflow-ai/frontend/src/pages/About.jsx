import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Heart, Target, Users, Award, CheckCircle2, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

const values = [
  {
    icon: Heart,
    title: 'Client-Centric',
    desc: t('About.we_place_your_mission_and_customer_satisfaction_at_the_heart', 'We place your mission and customer satisfaction at the heart of everything we build.'),
  },
  {
    icon: Target,
    title: t('About.data_driven', 'Data Driven'),
    desc: t('About.precision_crafted_strategies_supported_by_real_world_metrics', 'Precision-crafted strategies supported by real-world metrics and analytics.'),
  },
  {
    icon: Users,
    title: t('About.collaborative_spirit', 'Collaborative Spirit'),
    desc: t('About.transparent_partnership_fostering_innovation_and_rapid_itera', 'Transparent partnership fostering innovation and rapid iteration.'),
  },
  {
    icon: Award,
    title: 'Craftsmanship',
    desc: t('About.pixel_perfect_ui_design_accessible_markup_and_uncompromising', 'Pixel-perfect UI design, accessible markup, and uncompromising quality.'),
  },
];

export default function About() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 px-6 py-16 max-w-6xl mx-auto w-full">
        <section className="text-center max-w-3xl mx-auto mb-20 space-y-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
            Our Story
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Dedicated to Building the Future
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            claimflow-ai-002 combines technical precision with thoughtful design to deliver digital
            products that scale reliably and inspire trust.
          </p>
        </section>

        <section className="mb-20">
          <h2 className="text-2xl font-bold text-center mb-10">{t('About.our_guiding_values', t('About.our_guiding_values', 'Our Guiding Values'))}</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {values.map((v) => (
              <div
                key={v.title}
                className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-center"
              >
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <v.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-white">{v.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
