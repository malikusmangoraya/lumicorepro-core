import type { Metadata } from 'next';
import { Section, SectionHeading } from '@/components/ui/section';
import { Stat } from '@/components/ui/card';

export const metadata: Metadata = {
  title: 'Market insights',
  description: 'What the collector market is doing this quarter, in plain numbers.',
  alternates: { canonical: '/insights' },
};

const kpis = [
  { value: '+8.4%', label: 'Median asking price, 12 months' },
  { value: '31 days', label: 'Average time to sell' },
  { value: '62%', label: 'Sold at or above ask' },
  { value: '1.9%', label: 'Of listings withdrawn' },
];

const rows = [
  {
    segment: 'Air-cooled Porsche 911',
    movement: 'Up',
    detail: 'Scarcity of documented cars is pushing clean examples above the wider market.',
  },
  {
    segment: 'Modern GT cars',
    movement: 'Flat',
    detail: 'Supply has caught up with demand; prices are stable but negotiation has returned.',
  },
  {
    segment: 'Youngtimer saloons',
    movement: 'Down',
    detail: 'Running costs and parts availability are weighing on asking prices.',
  },
];

export default function InsightsPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Market insights"
        title="Intent into forecast"
        description="A quarterly read of the collector market, based on our own transaction data and the listings we track."
      />

      <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <Stat key={kpi.label} value={kpi.value} label={kpi.label} />
        ))}
      </div>

      <div className="mt-8 divide-y divide-line/70 rounded-panel border border-line bg-surface/40">
        {rows.map((row) => (
          <div key={row.segment} className="flex flex-col gap-2 p-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="font-display text-base font-600 text-heading">{row.segment}</h2>
              <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted">{row.detail}</p>
            </div>
            <span
              className={
                row.movement === 'Up'
                  ? 'shrink-0 rounded-full border border-emerald-500/35 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300'
                  : row.movement === 'Down'
                    ? 'shrink-0 rounded-full border border-red-500/35 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-300'
                    : 'shrink-0 rounded-full border border-line bg-white/5 px-3 py-1 text-xs font-semibold text-body/80'
              }
            >
              {row.movement}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-6 text-xs leading-relaxed text-muted">
        These figures describe our own inventory and tracked listings, not the entire market. They
        are not investment advice.
      </p>
    </Section>
  );
}
