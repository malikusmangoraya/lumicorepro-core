import type { Metadata } from 'next';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { InventoryFilters } from '@/components/vehicle/inventory-filters';
import { VehicleCard } from '@/components/vehicle/vehicle-card';
import { EmptyState, ErrorState, Section, SectionHeading } from '@/components/ui/section';
import { ButtonLink } from '@/components/ui/button';
import { listVehicles } from '@/lib/vehicles';
import { vehicleQuerySchema } from '@/lib/validation';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Inventory',
  description:
    'Every car currently in the Apex collective, with provenance status, mileage and location.',
  alternates: { canonical: '/inventory' },
};

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function InventoryPage({ searchParams }: { searchParams: SearchParams }) {
  const raw = await searchParams;
  const parsed = vehicleQuerySchema.safeParse({
    q: firstValue(raw.q) || undefined,
    make: firstValue(raw.make) || undefined,
    priceMax: firstValue(raw.priceMax) || undefined,
    sort: firstValue(raw.sort) || undefined,
    page: firstValue(raw.page) || undefined,
  });

  if (!parsed.success) {
    return (
      <Section>
        <ErrorState
          description="Those filters are not valid. Clear them and try again."
          action={<ButtonLink href="/inventory">Reset filters</ButtonLink>}
        />
      </Section>
    );
  }

  const result = await listVehicles(parsed.data);
  const buildPageHref = (page: number) => {
    const search = new URLSearchParams();
    for (const key of ['q', 'make', 'priceMax', 'sort'] as const) {
      const value = raw[key];
      const single = firstValue(value);
      if (single) search.set(key, single);
    }
    if (page > 1) search.set('page', String(page));
    const query = search.toString();
    return query ? `/inventory?${query}` : '/inventory';
  };

  return (
    <Section>
      <SectionHeading
        eyebrow="Inventory"
        title="Every car, with its history attached"
        description="Filter by make, budget or mileage. Prices are shown in each listing's own currency and are never converted at display time."
      />

      <div className="mt-8 space-y-5">
        <InventoryFilters makes={result.makes} />

        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
          <p aria-live="polite">
            {result.databaseReady
              ? `${result.total} car${result.total === 1 ? '' : 's'} available`
              : 'Inventory unavailable'}
            {result.total > 0 && (
              <span className="text-muted/70">
                {' '}
                · page {result.page} of {result.pages}
              </span>
            )}
          </p>
          <p className="text-xs">Photos are of the actual car, not stock imagery.</p>
        </div>

        {!result.databaseReady ? (
          <ErrorState
            title="The inventory database is not ready"
            description="Create and seed it with `npm run db:setup`, then reload. The storefront stays up without a database, but there is nothing to list yet."
          />
        ) : result.items.length === 0 ? (
          <EmptyState
            title="No cars match those filters"
            description="Try widening the budget, clearing the make, or searching for a model name instead."
            action={<ButtonLink href="/inventory" variant="outline">Clear all filters</ButtonLink>}
          />
        ) : (
          <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {result.items.map((vehicle) => (
              <li key={vehicle.id}>
                <VehicleCard vehicle={vehicle} />
              </li>
            ))}
          </ul>
        )}

        {result.pages > 1 && (
          <nav aria-label="Pagination" className="flex items-center justify-center gap-2 pt-4">
            {result.page > 1 ? (
              <Link
                href={buildPageHref(result.page - 1)}
                className="inline-flex items-center gap-1 rounded-control border border-line px-3 py-2 text-sm text-heading transition-colors hover:border-primary/60"
                rel="prev"
              >
                <ChevronLeft className="size-4" aria-hidden="true" />
                Previous
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-control border border-line/40 px-3 py-2 text-sm text-muted/50">
                <ChevronLeft className="size-4" aria-hidden="true" />
                Previous
              </span>
            )}

            <span className="px-2 text-sm text-muted">
              {result.page} / {result.pages}
            </span>

            {result.page < result.pages ? (
              <Link
                href={buildPageHref(result.page + 1)}
                className="inline-flex items-center gap-1 rounded-control border border-line px-3 py-2 text-sm text-heading transition-colors hover:border-primary/60"
                rel="next"
              >
                Next
                <ChevronRight className="size-4" aria-hidden="true" />
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-control border border-line/40 px-3 py-2 text-sm text-muted/50">
                Next
                <ChevronRight className="size-4" aria-hidden="true" />
              </span>
            )}
          </nav>
        )}
      </div>
    </Section>
  );
}
