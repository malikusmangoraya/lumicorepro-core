'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const tiers = [
  {
    name: 'Starter',
    monthly: 29,
    annual: 24,
    description: 'For first-time buyers who want a second opinion before they commit.',
    features: [
      'Two vehicle history reports a month',
      'Pre-purchase checklist library',
      'Email support within 48 hours',
      'Saved shortlist (up to 10 cars)',
    ],
  },
  {
    name: 'Pro',
    monthly: 79,
    annual: 64,
    description: 'For collectors buying more than once a year, with inspection coordination.',
    features: [
      'Unlimited vehicle history reports',
      'Independent inspection coordination',
      'Private viewing scheduling',
      'Price alerts on saved searches',
      'Priority support within 4 hours',
    ],
    highlight: true,
  },
  {
    name: 'Enterprise',
    monthly: 199,
    annual: 159,
    description: 'For dealers and collections that need provenance research at volume.',
    features: [
      'Everything in Pro',
      'Bulk provenance research',
      'Dedicated account specialist',
      'Enclosed transport booking',
      'Custom reporting exports',
    ],
  },
];

export function PricingTable() {
  const [annual, setAnnual] = useState(true);

  return (
    <div>
      <div className="mb-8 flex items-center justify-center gap-3">
        <span className={cn('text-sm', !annual ? 'text-heading' : 'text-muted')}>Monthly</span>
        <button
          type="button"
          role="switch"
          aria-checked={annual}
          aria-label="Bill annually"
          onClick={() => setAnnual((value) => !value)}
          className={cn(
            'relative h-7 w-13 rounded-full border transition-colors',
            annual ? 'border-primary bg-primary/30' : 'border-line bg-surface',
          )}
        >
          <span
            className={cn(
              'absolute top-0.5 size-5 rounded-full bg-primary transition-transform',
              annual ? 'translate-x-7' : 'translate-x-0.5',
            )}
          />
        </button>
        <span className={cn('text-sm', annual ? 'text-heading' : 'text-muted')}>
          Annual
          <span className="ml-1.5 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-300">
            Save 20%
          </span>
        </span>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {tiers.map((tier) => {
          const price = annual ? tier.annual : tier.monthly;
          return (
            <div
              key={tier.name}
              className={cn(
                'relative flex flex-col rounded-panel border p-6',
                tier.highlight
                  ? 'border-primary/60 bg-primary/5 shadow-glow'
                  : 'border-line bg-surface/60',
              )}
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-6 rounded-full bg-primary px-3 py-1 text-[0.65rem] font-bold uppercase tracking-wide text-[#0b0616]">
                  Most popular
                </span>
              )}
              <h3 className="font-display text-xl font-700 text-heading">{tier.name}</h3>
              <p className="mt-2 min-h-10 text-sm leading-relaxed text-muted">
                {tier.description}
              </p>
              <p className="mt-5 flex items-baseline gap-1.5">
                <span className="font-display text-4xl font-700 text-heading">${price}</span>
                <span className="text-sm text-muted">/ month</span>
              </p>
              <p className="mt-1 text-xs text-muted">
                {annual ? `Billed annually at $${price * 12}` : 'Billed monthly'}
              </p>

              <ul className="mt-6 flex-1 space-y-2.5">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-body/85">
                    <Check className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
                    {feature}
                  </li>
                ))}
              </ul>

              <Button
                variant={tier.highlight ? 'primary' : 'outline'}
                fullWidth
                className="mt-6"
                onClick={() =>
                  // A hosted checkout needs a configured store; the template
                  // says so instead of pretending the button worked.
                  window.alert(
                    'Checkout is not configured in this template. Set LEMONSQUEEZY_STORE_ID and API key in .env to enable it.',
                  )
                }
              >
                Choose {tier.name}
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
