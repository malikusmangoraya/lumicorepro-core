'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useState, useTransition } from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/field';

const SORTS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
  { value: 'mileage-asc', label: 'Lowest mileage' },
];

export function InventoryFilters({ makes }: { makes: string[] }) {
  const router = useRouter();
  const params = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState(params.get('q') ?? '');

  const current = {
    make: params.get('make') ?? '',
    priceMax: params.get('priceMax') ?? '',
    sort: params.get('sort') ?? 'newest',
  };

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

  const activeCount = [current.make, current.priceMax, params.get('q'), params.get('sort')].filter(
    Boolean,
  ).length;

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

        <div className="sm:w-44">
          <label htmlFor="inventory-make" className="mb-1.5 block text-xs font-medium text-muted">
            Make
          </label>
          <Select
            id="inventory-make"
            value={current.make}
            onChange={(event) => apply({ make: event.target.value })}
          >
            <option value="">All makes</option>
            {makes.map((make) => (
              <option key={make} value={make}>
                {make}
              </option>
            ))}
          </Select>
        </div>

        <div className="sm:w-44">
          <label
            htmlFor="inventory-price"
            className="mb-1.5 block text-xs font-medium text-muted"
          >
            Max price (USD)
          </label>
          <Input
            id="inventory-price"
            type="number"
            min={0}
            step={5000}
            inputMode="numeric"
            defaultValue={current.priceMax}
            onBlur={(event) => apply({ priceMax: event.target.value })}
            placeholder="Any"
          />
        </div>

        <div className="sm:w-52">
          <label htmlFor="inventory-sort" className="mb-1.5 block text-xs font-medium text-muted">
            Sort
          </label>
          <Select
            id="inventory-sort"
            value={current.sort}
            onChange={(event) => apply({ sort: event.target.value })}
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <Button type="submit" className="sm:mb-0" aria-busy={isPending}>
          <SlidersHorizontal className="size-4" aria-hidden="true" />
          Apply
        </Button>
      </div>

      {activeCount > 0 && (
        <div className="mt-3 flex items-center gap-2 text-xs text-muted">
          <span>
            {activeCount} filter{activeCount === 1 ? '' : 's'} active
          </span>
          <button
            type="button"
            onClick={() => {
              setQuery('');
              startTransition(() => router.push('/inventory', { scroll: false }));
            }}
            className="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-heading transition-colors hover:border-primary/60"
          >
            <X className="size-3" aria-hidden="true" />
            Clear
          </button>
        </div>
      )}
    </form>
  );
}
