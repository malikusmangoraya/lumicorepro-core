import React from 'react';
import { useSearchParams } from 'react-router-dom';

export default function InventoryFilters() {
  const [params, setParams] = useSearchParams();
  const update = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete('page');
    setParams(next);
  };

  return (
    <form className="grid gap-4 border-y border-[var(--t-border)] py-5 sm:grid-cols-2 lg:grid-cols-4" onSubmit={(event) => event.preventDefault()} aria-label="Filter vehicle inventory">
      <label className="text-sm font-medium">Search
        <input type="search" value={params.get('q') || ''} onChange={(event) => update('q', event.target.value)} className="mt-1 block w-full rounded border border-[var(--t-border)] bg-surface px-3 py-2" placeholder="Make, model, location" />
      </label>
      <label className="text-sm font-medium">Make
        <input value={params.get('make') || ''} onChange={(event) => update('make', event.target.value)} className="mt-1 block w-full rounded border border-[var(--t-border)] bg-surface px-3 py-2" />
      </label>
      <label className="text-sm font-medium">Maximum price
        <input inputMode="decimal" value={params.get('priceMax') || ''} onChange={(event) => update('priceMax', event.target.value)} className="mt-1 block w-full rounded border border-[var(--t-border)] bg-surface px-3 py-2" />
      </label>
      <label className="text-sm font-medium">Sort by
        <select value={params.get('sort') || 'newest'} onChange={(event) => update('sort', event.target.value === 'newest' ? '' : event.target.value)} className="mt-1 block w-full rounded border border-[var(--t-border)] bg-surface px-3 py-2">
          <option value="newest">Recently added</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="year_desc">Year: newest first</option>
          <option value="mileage_asc">Mileage: lowest first</option>
        </select>
      </label>
    </form>
  );
}
