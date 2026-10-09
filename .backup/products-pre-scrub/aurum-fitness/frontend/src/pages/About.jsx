import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Trophy, Users, Clock, Check, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const stats = [
  { value: t('About.92', '92%'), label: t('About.goal_attainment', 'Goal attainment') },
  { value: t('About.1_1', '1:1'), label: t('About.coach_ratio', 'Coach ratio') },
  { value: '14', label: t('About.coach_credentials', 'Coach credentials') },
  { value: t('About.60m', '60m'), label: t('About.member_facilities', 'Member facilities') },
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
              PERFORMANCE CLUB
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Train like the clock is watching.
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Aurum Fitness fuses olympic methodology with private training floors — coached, measured, relentless.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
            <div>
              <h2 className="section-heading">{t('About.a_brand_built_on_standards', t('About.a_brand_built_on_standards', 'A brand built on standards'))}</h2>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">
                <strong style={{ color: 'var(--t-heading)' }}>{t('About.aurum_fitness', t('About.aurum_fitness', 'Aurum Fitness'))}</strong> was built for people who are serious about training but tired of gyms that sell memberships rather than results. Our floors are coached, our programmes are written down, and progress is measured — not assumed.
              </p>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">{t('About.we_exist_to_make_sports_feel_effortless_and_worth_recommendi', t('About.we_exist_to_make_sports_feel_effortless_and_worth_recommendi', 'We exist to make sports feel effortless and worth recommending — measured by results, retained by trust, and built to an international standard.'))}</p>
              <ul className="mt-8 space-y-3">
                <li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.programming_built_on_data', t('About.programming_built_on_data', 'Programming built on data'))}</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.recovery_treated_like_training', t('About.recovery_treated_like_training', 'Recovery treated like training'))}</span>
                </li><li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{t('About.a_floor_that_smells_like_work', t('About.a_floor_that_smells_like_work', 'A floor that smells like work'))}</span>
                </li>
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.92', t('About.92', '92%'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.goal_attainment', t('About.goal_attainment', 'Goal attainment'))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.1_1', t('About.1_1', '1:1'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.coach_ratio', t('About.coach_ratio', 'Coach ratio'))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>14</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.coach_credentials', t('About.coach_credentials', 'Coach credentials'))}</p>
              </div><div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>{t('About.60m', t('About.60m', '60m'))}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{t('About.member_facilities', t('About.member_facilities', 'Member facilities'))}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">{t('About.what_guides_us', t('About.what_guides_us', 'What guides us'))}</p>
              <h2 className="section-heading">{t('About.principles_we_do_not_trade_away', t('About.principles_we_do_not_trade_away', 'Principles we do not trade away'))}</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Trophy className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('About.proven_results', t('About.proven_results', 'Proven Results'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{t('About.members_hit_measurable_goals_we_publish_the_numbers_rather_t', t('About.members_hit_measurable_goals_we_publish_the_numbers_rather_t', 'Members hit measurable goals — we publish the numbers rather than the hype.'))}</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Users className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>{t('About.expert_coaches', t('About.expert_coaches', 'Expert Coaches'))}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Qualified coaches on every floor, correcting form before it becomes injury.</p>
              </div><div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Clock className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>Open Access</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Train when it suits you, with early, late and weekend hours.</p>
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
                Ready to start with Aurum Fitness?
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
                  Start Training <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/services"
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
