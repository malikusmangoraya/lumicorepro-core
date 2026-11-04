'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Clock } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';
import { formatCurrency } from '@/lib/utils';
import type { VehicleCardData } from '@/lib/vehicles';

export function RecentlyViewed({ excludeSlug }: { excludeSlug?: string }) {
  const { recent, hydrated } = useSite();
  const slugs = recent.filter((slug) => slug !== excludeSlug).slice(0, 6);
  const key = slugs.join(',');
  const [loaded, setLoaded] = useState<{ key: string; items: VehicleCardData[] } | null>(null);

  useEffect(() => {
    if (!hydrated || slugs.length === 0) return;

    let cancelled = false;
    fetch(`/api/vehicles?slugs=${encodeURIComponent(slugs.join(','))}`)
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
  if (items.length === 0) return null;

  return (
    <section aria-labelledby="recently-viewed" className="border-t border-line/60 bg-surface/20">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="flex items-center gap-2">
          <Clock className="size-4 text-accent" aria-hidden="true" />
          <h2 id="recently-viewed" className="font-display text-lg font-600 text-heading">
            Recently viewed
          </h2>
        </div>

        <ul className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {items.map((vehicle) => (
            <li key={vehicle.id}>
              <Link
                href={`/inventory/${vehicle.slug}`}
                className="group block overflow-hidden rounded-xl border border-line bg-canvas/60 transition-colors hover:border-primary/50"
              >
                <div className="relative aspect-[16/10] bg-canvas">
                  {vehicle.media[0] ? (
                    <Image
                      src={vehicle.media[0].url}
                      alt={vehicle.media[0].alt || vehicle.title}
                      fill
                      sizes="(max-width: 640px) 50vw, 16vw"
                      className="object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  ) : null}
                </div>
                <div className="p-2.5">
                  <p className="truncate text-xs font-medium text-heading">
                    {vehicle.year} {vehicle.make} {vehicle.model}
                  </p>
                  <p className="mt-0.5 text-xs text-accent">
                    {formatCurrency(vehicle.price, vehicle.currency)}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
