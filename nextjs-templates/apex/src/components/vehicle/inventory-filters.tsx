'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useState, useTransition } from 'react';
import { RotateCcw, Search, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/field';
import type { VehicleFacets } from '@/lib/vehicles';

const SORTS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
  { value: 'mileage-asc', label: 'Lowest mileage' },
  { value: 'year-desc', label: 'Newest model year' },
];

const YEARS = ['2015', '2017', '2019', '2021'];

export function InventoryFilters({ facets }: { facets: VehicleFacets }) {
  const router = useRouter();
  const params = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState(params.get('q') ?? '');

  const apply = useCallback(
    (next: Record<string, string>) => {
      const search = new URLSearchParams(params.toString());
      for (const [key, value] of Object.entries(next)) {
        if (value) search.set(key, value);
        else search.delete(key);
      }
      // Any filter change resets pagination, otherwise page 4 of a narrower
      // result set renders as "no results" even though matches exist.
      search.delete('page');
      startTransition(() => router.push(`/inventory?${search.toString()}`, { scroll: false }));
    },
    [params, router],
  );

  const value = (key: string) => params.get(key) ?? '';
  const activeCount = ['q', 'make', 'bodyStyle', 'fuelType', 'transmission', 'yearMin', 'mileageMax', 'priceMax', 'sort']
    .filter((key) => params.get(key)).length;

  return (
    <form
      className="rounded-panel border border-line bg-surface/60 p-4 sm:p-5"
      onSubmit={(event) => {
        event.preventDefault();
        apply({ q: query.trim() });
      }}
      role="search"
      aria-label="Filter inventory"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="inventory-search" className="mb-1.5 block text-xs font-medium text-muted">
            Search
          </label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted"
              aria-hidden="true"
            />
            <Input
              id="inventory-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Porsche 911, Ferrari, GT3…"
              className="pl-9"
              autoComplete="off"
            />
          </div>
        </div>
        <Button type="submit" aria-busy={isPending}>
          <SlidersHorizontal className="size-4" aria-hidden="true" />
          Search
        </Button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label htmlFor="f-make" className="mb-1.5 block text-xs font-medium text-muted">
            Make
          </label>
          <Select id="f-make" value={value('make')} onChange={(e) => apply({ make: e.target.value })}>
            <option value="">All makes</option>
            {facets.makes.map((make) => (
              <option key={make} value={make}>
                {make}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="f-body" className="mb-1.5 block text-xs font-medium text-muted">
            Body style
          </label>
          <Select
            id="f-body"
            value={value('bodyStyle')}
            onChange={(e) => apply({ bodyStyle: e.target.value })}
          >
            <option value="">Any body</option>
            {facets.bodyStyles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="f-fuel" className="mb-1.5 block text-xs font-medium text-muted">
            Fuel
          </label>
          <Select
            id="f-fuel"
            value={value('fuelType')}
            onChange={(e) => apply({ fuelType: e.target.value })}
          >
            <option value="">Any fuel</option>
            {facets.fuelTypes.map((fuel) => (
              <option key={fuel} value={fuel}>
                {fuel}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="f-transmission" className="mb-1.5 block text-xs font-medium text-muted">
            Transmission
          </label>
          <Select
            id="f-transmission"
            value={value('transmission')}
            onChange={(e) => apply({ transmission: e.target.value })}
          >
            <option value="">Any gearbox</option>
            {facets.transmissions.map((transmission) => (
              <option key={transmission} value={transmission}>
                {transmission}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="f-year" className="mb-1.5 block text-xs font-medium text-muted">
            From year
          </label>
          <Select
            id="f-year"
            value={value('yearMin')}
            onChange={(e) => apply({ yearMin: e.target.value })}
          >
            <option value="">Any year</option>
            {YEARS.map((year) => (
              <option key={year} value={year}>
                {year} or newer
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="f-mileage" className="mb-1.5 block text-xs font-medium text-muted">
            Max mileage
          </label>
          <Input
            id="f-mileage"
            type="number"
            min={0}
            step={1000}
            inputMode="numeric"
            defaultValue={value('mileageMax')}
            onBlur={(e) => apply({ mileageMax: e.target.value })}
            placeholder="Any"
          />
        </div>

        <div>
          <label htmlFor="f-price" className="mb-1.5 block text-xs font-medium text-muted">
            Max price (USD)
          </label>
          <Input
            id="f-price"
            type="number"
            min={0}
            step={5000}
            inputMode="numeric"
            defaultValue={value('priceMax')}
            onBlur={(e) => apply({ priceMax: e.target.value })}
            placeholder="Any"
          />
        </div>

        <div>
          <label htmlFor="f-sort" className="mb-1.5 block text-xs font-medium text-muted">
            Sort
          </label>
          <Select
            id="f-sort"
            value={value('sort') || 'newest'}
            onChange={(e) => apply({ sort: e.target.value })}
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {activeCount > 0 && (
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-line/60 pt-3 text-xs text-muted">
          <span>
            {activeCount} filter{activeCount === 1 ? '' : 's'} active
          </span>
          <button
            type="button"
            onClick={() => {
              setQuery('');
              startTransition(() => router.push('/inventory', { scroll: false }));
            }}
            className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1 text-heading transition-colors hover:border-primary/60"
          >
            <RotateCcw className="size-3" aria-hidden="true" />
            Clear all
          </button>
        </div>
      )}
    </form>
  );
}
