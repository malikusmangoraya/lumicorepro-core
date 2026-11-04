'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Columns3, Loader2, Trash2 } from 'lucide-react';
import { Button, ButtonLink } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/section';
import { useSite } from '@/components/providers/site-provider';
import { formatCurrency, formatMileage } from '@/lib/utils';
import type { VehicleDetailData } from '@/lib/vehicles';

type Row = { label: string; value: (vehicle: VehicleDetailData) => string };

const ROWS: Row[] = [
  { label: 'Price', value: (v) => formatCurrency(v.price, v.currency) },
  { label: 'Year', value: (v) => String(v.year) },
  { label: 'Mileage', value: (v) => formatMileage(v.mileage, v.mileageUnit) },
  { label: 'Body style', value: (v) => v.bodyStyle },
  { label: 'Fuel', value: (v) => v.fuelType },
  { label: 'Transmission', value: (v) => v.transmission },
  { label: 'Location', value: (v) => `${v.locationRegion}, ${v.locationCountry}` },
  { label: 'Provenance', value: (v) => (v.provenanceVerified ? 'Verified' : 'Not verified') },
  { label: 'Status', value: (v) => v.status },
];

export function CompareTable() {
  const { compare, hydrated, toggleCompare, clearCompare, notify } = useSite();
  const key = compare.join(',');
  // One state holding both the key it belongs to and the rows: every update
  // happens inside the fetch callbacks, so the effect never triggers a
  // cascading render.
  const [loaded, setLoaded] = useState<{ key: string; items: VehicleDetailData[] } | null>(null);

  useEffect(() => {
    if (!hydrated || compare.length === 0) return;

    let cancelled = false;
    fetch(`/api/vehicles?slugs=${encodeURIComponent(compare.join(','))}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((body: { data?: { items?: VehicleDetailData[] } } | null) => {
        if (!cancelled) setLoaded({ key, items: body?.data?.items ?? [] });
      })
      .catch(() => {
        if (!cancelled) setLoaded({ key, items: [] });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, hydrated]);

  const items = loaded?.key === key ? loaded.items : [];
  const ready = hydrated && (compare.length === 0 || loaded?.key === key);

  if (!ready) {
    return (
      <div className="flex items-center justify-center gap-2 py-20 text-sm text-muted">
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
        Building the comparison…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Nothing to compare yet"
        description="Add up to three cars with the compare button on any listing, then return here for a side-by-side spec table."
        action={
          <ButtonLink href="/inventory">
            <Columns3 className="size-4" aria-hidden="true" />
            Pick cars to compare
          </ButtonLink>
        }
      />
    );
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">
          Comparing {items.length} car{items.length === 1 ? '' : 's'}
          {items.length < 3 && (
            <>
              {' · '}
              <Link href="/inventory" className="text-accent hover:underline">
                add another
              </Link>
            </>
          )}
        </p>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            clearCompare();
            notify('Comparison cleared');
          }}
        >
          <Trash2 className="size-3.5" aria-hidden="true" />
          Clear all
        </Button>
      </div>

      <div className="overflow-x-auto rounded-panel border border-line">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <caption className="sr-only">Side-by-side vehicle comparison</caption>
          <thead>
            <tr>
              <th scope="col" className="w-40 border-b border-line bg-surface/70 p-4 text-left text-xs uppercase tracking-wide text-muted">
                Spec
              </th>
              {items.map((vehicle) => (
                <th key={vehicle.slug} scope="col" className="border-b border-line bg-surface/70 p-4 text-left align-top">
                  <div className="relative mb-3 aspect-[16/10] overflow-hidden rounded-lg border border-line bg-canvas">
                    {vehicle.media[0] ? (
                      <Image
                        src={vehicle.media[0].url}
                        alt={vehicle.media[0].alt || vehicle.title}
                        fill
                        sizes="240px"
                        className="object-cover"
                      />
                    ) : null}
                  </div>
                  <Link href={`/inventory/${vehicle.slug}`} className="font-display text-sm font-600 text-heading hover:text-accent">
                    {vehicle.title}
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      toggleCompare(vehicle.slug);
                      notify(`Removed ${vehicle.title} from compare`);
                    }}
                    className="mt-2 block text-xs text-muted underline-offset-2 hover:text-red-300 hover:underline"
                  >
                    Remove
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row, index) => (
              <tr key={row.label} className={index % 2 === 0 ? 'bg-canvas/30' : ''}>
                <th scope="row" className="border-b border-line/50 p-4 text-left text-xs font-medium uppercase tracking-wide text-muted">
                  {row.label}
                </th>
                {items.map((vehicle) => (
                  <td key={vehicle.slug} className="border-b border-line/50 p-4 text-heading">
                    {row.value(vehicle)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
