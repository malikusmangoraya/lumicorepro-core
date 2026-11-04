'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn, formatCurrency } from '@/lib/utils';
import {
  maxSavingPercent,
  PRICING_CURRENCY,
  PRICING_TIERS,
  savingPercent,
} from '@/lib/pricing';

export function PricingTable() {
  const [annual, setAnnual] = useState(true);
  const bestSaving = maxSavingPercent();

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-center justify-center gap-3">
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
            Save up to {bestSaving}%
          </span>
        </span>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {PRICING_TIERS.map((tier) => {
          const price = annual ? tier.annualMonthly : tier.monthly;
          const saving = savingPercent(tier);

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
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-display text-xl font-700 text-heading">{tier.name}</h3>
                {annual && saving > 0 && (
                  <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[0.65rem] font-semibold text-emerald-300">
                    −{saving}%
                  </span>
                )}
              </div>
              <p className="mt-2 min-h-10 text-sm leading-relaxed text-muted">{tier.description}</p>
              <p className="mt-5 flex items-baseline gap-1.5">
                <span className="font-display text-4xl font-700 text-heading">
                  {formatCurrency(price, PRICING_CURRENCY)}
                </span>
                <span className="text-sm text-muted">/ month</span>
              </p>
              <p className="mt-1 text-xs text-muted">
                {annual
                  ? `Billed annually at ${formatCurrency(price * 12, PRICING_CURRENCY)} — ${saving}% less than monthly`
                  : `Billed monthly at ${formatCurrency(price, PRICING_CURRENCY)}`}
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
                  // A hosted checkout needs a configured store; the template says
                  // so instead of pretending the button worked.
                  window.alert(
                    'Membership checkout is not configured in this template. Connect your billing provider and wire this button to it.',
                  )
                }
              >
                Choose {tier.name}
              </Button>
            </div>
          );
        })}
      </div>

      <p className="mt-6 text-center text-xs text-muted">
        Prices in {PRICING_CURRENCY}, set by the operator. Card payment is collected by the billing
        provider you connect, never by this site.
      </p>
    </div>
  );
}
