import React from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
  { value: '1.2d', label: 'Avg to decision' },
  { value: '91%', label: 'Straight-through rate' },
  { value: '$48k', label: 'Paid out' },
  { value: '0.8%', label: 'Flagged' },
];

export default function Admin() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="section-heading">ClaimFlow control room</h1>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-5" data-reveal>
                <p className="text-2xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
