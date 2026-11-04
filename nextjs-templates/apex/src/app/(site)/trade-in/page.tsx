import type { Metadata } from 'next';
import { BadgeCheck, Clock, Gauge, PoundSterling } from 'lucide-react';
import { Section, SectionHeading } from '@/components/ui/section';
import { Panel } from '@/components/ui/card';
import { LeadForm } from '@/components/leads/lead-form';

export const metadata: Metadata = {
  title: 'Value your part-exchange',
  description:
    'Tell us about your car and a specialist returns a realistic trade-in figure within one business day.',
  alternates: { canonical: '/trade-in' },
};

const steps = [
  { icon: Gauge, title: 'You describe the car', body: 'Registration, mileage, condition and history. Two minutes, no photos needed yet.' },
  { icon: BadgeCheck, title: 'We check the market', body: 'Trade values, current retail and recent sales for that exact model and spec.' },
  { icon: PoundSterling, title: 'You get a figure', body: 'A realistic range, not a headline number that shrinks at the viewing.' },
  { icon: Clock, title: 'It holds for 7 days', body: 'Enough time to decide, with no obligation to buy from us.' },
];

export default function TradeInPage() {
  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Part exchange"
        title="What is your car worth?"
        description="A trade-in figure backed by real market data, held for a week. No obligation to buy from us."
      />

      <div className="mt-10 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-3">
          {steps.map((step) => (
            <Panel key={step.title} className="p-5">
              <step.icon className="size-4 text-accent" aria-hidden="true" />
              <h2 className="mt-3 font-display text-base font-600 text-heading">{step.title}</h2>
              <p className="mt-1 text-sm leading-relaxed text-muted">{step.body}</p>
            </Panel>
          ))}
        </div>

        <Panel className="p-6 sm:p-8">
          <h2 className="font-display text-lg font-600 text-heading">Tell us about your car</h2>
          <p className="mt-1 mb-6 text-sm leading-relaxed text-muted">
            A specialist replies with a range and the reasoning behind it.
          </p>
          <LeadForm type="trade_in" />
        </Panel>
      </div>
    </Section>
  );
}
