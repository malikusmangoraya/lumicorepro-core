'use client';

import Link from 'next/link';
import { Columns3, Heart } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function TrayLinks() {
  const { saved, compare, hydrated } = useSite();

  if (!hydrated) return null;

  return (
    <div className="hidden items-center gap-1 sm:flex">
      <Link
        href="/saved"
        aria-label={`Saved cars${saved.length ? ` (${saved.length})` : ''}`}
        className="relative inline-flex size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
      >
        <Heart className="size-4" aria-hidden="true" />
        {saved.length > 0 && (
          <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[0.6rem] font-bold leading-4 text-[#0b0616]">
            {saved.length}
          </span>
        )}
      </Link>
      <Link
        href="/compare"
        aria-label={`Compare cars${compare.length ? ` (${compare.length})` : ''}`}
        className="relative inline-flex size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
      >
        <Columns3 className="size-4" aria-hidden="true" />
        {compare.length > 0 && (
          <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[0.6rem] font-bold leading-4 text-[#0b0616]">
            {compare.length}
          </span>
        )}
      </Link>
    </div>
  );
}
