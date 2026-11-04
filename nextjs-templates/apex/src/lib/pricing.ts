/**
 * Membership pricing.
 *
 * These are the demo values the template ships with. Change them here — the
 * table, the card copy and the saving percentage all read from this one list,
 * so a price can never disagree with the label beside it.
 */

export type PricingTier = {
  name: string;
  monthly: number;
  /** Per-month price when billed annually. */
  annualMonthly: number;
  description: string;
  features: string[];
  highlight?: boolean;
};

export const PRICING_CURRENCY = 'USD';

export const PRICING_TIERS: PricingTier[] = [
  {
    name: 'Starter',
    monthly: 29,
    annualMonthly: 24,
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
    annualMonthly: 64,
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
    annualMonthly: 159,
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

/** Percentage saved by paying annually, rounded — never hard-coded in copy. */
export function savingPercent(tier: PricingTier): number {
  if (tier.monthly <= 0) return 0;
  return Math.round((1 - tier.annualMonthly / tier.monthly) * 100);
}

/** The best saving on offer, for the billing toggle. */
export function maxSavingPercent(): number {
  return Math.max(...PRICING_TIERS.map(savingPercent));
}
