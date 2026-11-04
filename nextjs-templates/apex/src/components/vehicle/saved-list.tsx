'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Heart, Loader2 } from 'lucide-react';
import { VehicleCard } from '@/components/vehicle/vehicle-card';
import { ButtonLink } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/section';
import { useSite } from '@/components/providers/site-provider';
import type { VehicleCardData } from '@/lib/vehicles';

export function SavedList() {
  const { saved, hydrated } = useSite();
  const key = saved.join(',');
  const [loaded, setLoaded] = useState<{ key: string; items: VehicleCardData[] } | null>(null);

  useEffect(() => {
    if (!hydrated || saved.length === 0) return;

    let cancelled = false;
    fetch(`/api/vehicles?slugs=${encodeURIComponent(saved.join(','))}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((body: { data?: { items?: VehicleCardData[] } } | null) => {
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
  const ready = hydrated && (saved.length === 0 || loaded?.key === key);

  if (!ready) {
    return (
      <div className="flex items-center justify-center gap-2 py-20 text-sm text-muted">
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
        Loading your saved cars…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Nothing saved yet"
        description="Tap the heart on any car to keep it here. Saved cars live in this browser, so they survive a refresh without an account."
        action={
          <ButtonLink href="/inventory">
            <Heart className="size-4" aria-hidden="true" />
            Browse the inventory
          </ButtonLink>
        }
      />
    );
  }

  return (
    <>
      <p className="mb-5 text-sm text-muted" aria-live="polite">
        {items.length} saved car{items.length === 1 ? '' : 's'} ·{' '}
        <Link href="/inventory" className="text-accent hover:underline">
          add more
        </Link>
      </p>
      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((vehicle) => (
          <li key={vehicle.id}>
            <VehicleCard vehicle={vehicle} />
          </li>
        ))}
      </ul>
    </>
  );
}
