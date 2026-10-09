import React from 'react';
import { useTranslation } from 'react-i18next';
import { BarChart3, Users, ShoppingBag, TrendingUp, Activity, Clock, ArrowRight, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
  { icon: BarChart3, label: 'Decks made', value: '80k', trend: '+12%' },
  { icon: Users, label: 'Creator rating', value: '4.9', trend: '+4%' },
  { icon: ShoppingBag, label: 'Faster decks', value: '10x', trend: '+8%' },
  { icon: TrendingUp, label: 'Uptime', value: '99.9%', trend: '+3%' },
];

const buildactivity = (t) => [
  { icon: Activity, text: 'New saas enquiry received', time: '2m ago' },
  { icon: ShieldCheck, text: t('Admin.payment_verified_and_settled', 'Payment verified and settled'), time: '18m ago' },
  { icon: Users, text: t('Admin.new_team_member_invited', 'New team member invited'), time: '1h ago' },
  { icon: Clock, text: t('Admin.weekly_performance_report_generated', 'Weekly performance report generated'), time: '3h ago' },
];

export default function Admin() {
  const { t } = useTranslation();

  const activity = buildactivity(t);
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-end justify-between gap-4 mb-10">
            <div>
              <p className="section-eyebrow">{t('Admin.dashboard', t('Admin.dashboard', 'Dashboard'))}</p>
              <h1 className="section-heading mt-1">ResuPro control room</h1>
            </div>
            <span className="glass-md rounded-xl px-4 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400" data-reveal>
              Live · updated moments ago
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-6 card-lift" data-reveal>
                <div className="flex items-center justify-between mb-4">
                  <span
                    className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-white"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <k.icon className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-bold text-primary">{k.trend}</span>
                </div>
                <p className="text-3xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card-panel p-7" data-reveal>
              <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>{t('Admin.revenue_overview', t('Admin.revenue_overview', 'Revenue overview'))}</h2>
              <div className="flex items-end gap-3 h-48">
                {[42, 58, 49, 71, 63, 84, 76, 92, 88, 96, 90, 100].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t-lg" style={{ height: h + '%', background: 'linear-gradient(180deg, var(--t-primary), var(--t-accent))', opacity: 0.35 + (h / 150) }} />
                ))}
              </div>
              <div className="mt-3 flex justify-between text-[10px] uppercase tracking-widest text-slate-400">
                <span>{t('Admin.jan', t('Admin.jan', 'Jan'))}</span><span>{t('Admin.jun', t('Admin.jun', 'Jun'))}</span><span>{t('Admin.dec', t('Admin.dec', 'Dec'))}</span>
              </div>
            </div>

            <div className="card-panel p-7" data-reveal>
              <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>{t('Admin.recent_activity', t('Admin.recent_activity', 'Recent activity'))}</h2>
              <ul className="space-y-4">
                {activity.map((a, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface text-primary">
                      <a.icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{a.text}</p>
                      <p className="text-xs text-slate-400">{a.time}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <button className="btn-outline mt-6 inline-flex w-full items-center justify-center gap-2 py-2.5 text-sm">
                View all <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
