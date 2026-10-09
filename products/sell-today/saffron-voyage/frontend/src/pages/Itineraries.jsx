import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
  { value: '9', label: 'Current itineraries' },
  { value: '4', label: 'Destinations' },
  { value: '2', label: 'Group sizes capped' },
  { value: '18', label: 'Average rating' },
];

const rows = [
  { title: 'Amalfi Coast, 6 days', detail: 'Departing May 3' },
  { title: 'Atlas Mountain trek', detail: 'Departing October 11' },
  { title: 'Kerala backwaters', detail: 'Departing December 2' },
];

export default function Itineraries() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <p className="section-eyebrow">{t('Itineraries.eyebrow', 'Itineraries')}</p>
          <h1 className="section-heading mt-1">Journeys with a point of view</h1>
          <p className="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">Small-group travel, curated itineraries and booking inquiries.</p>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-5" data-reveal>
                <p className="text-2xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 card-panel p-7">
            <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>{t('Itineraries.items', 'Current items')}</h2>
            <ul className="divide-y divide-[var(--t-border)]">
              {rows.map((r, i) => (
                <li key={i} className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium" style={{ color: 'var(--t-heading)' }}>{r.title}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{r.detail}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
