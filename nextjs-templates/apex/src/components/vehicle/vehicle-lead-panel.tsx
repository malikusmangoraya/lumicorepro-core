'use client';

import Link from 'next/link';
import { useState } from 'react';
import { LeadForm } from '@/components/leads/lead-form';
import type { LeadType } from '@/lib/validation';
import { cn } from '@/lib/utils';

const TABS: { type: LeadType; label: string }[] = [
  { type: 'general', label: 'Enquire' },
  { type: 'test_drive', label: 'Test drive' },
  { type: 'finance', label: 'Finance' },
];

export function VehicleLeadPanel({
  vehicleSlug,
  vehicleTitle,
}: {
  vehicleSlug: string;
  vehicleTitle: string;
}) {
  const [active, setActive] = useState<LeadType>('general');

  return (
    <div>
      <div role="tablist" aria-label="Contact options" className="mb-5 flex gap-1 rounded-control border border-line p-1">
        {TABS.map((tab) => (
          <button
            key={tab.type}
            type="button"
            role="tab"
            aria-selected={active === tab.type}
            aria-controls={`panel-${tab.type}`}
            id={`tab-${tab.type}`}
            onClick={() => setActive(tab.type)}
            className={cn(
              'flex-1 rounded-[0.4rem] px-2 py-1.5 text-xs font-semibold transition-colors',
              active === tab.type
                ? 'bg-primary/15 text-accent'
                : 'text-body/75 hover:bg-white/5 hover:text-heading',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`panel-${active}`} aria-labelledby={`tab-${active}`}>
        <LeadForm key={active} type={active} vehicleSlug={vehicleSlug} vehicleTitle={vehicleTitle} />
      </div>

      <p className="mt-4 border-t border-line/60 pt-3 text-xs text-muted">
        Part-exchanging?{' '}
        <Link href="/trade-in" className="text-accent hover:underline">
          Get a valuation first
        </Link>
        .
      </p>
    </div>
  );
}
