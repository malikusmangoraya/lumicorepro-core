'use client';

import Link from 'next/link';
import { Columns3, Heart, ShoppingBag } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function TrayLinks() {
  const { saved, compare, cartCount, hydrated, t } = useSite();

  if (!hydrated) return null;

  return (
    <div className="flex items-center gap-1">
      <Link
        href="/cart"
        aria-label={`${t('tray.bag')}${cartCount ? ` (${cartCount})` : ''}`}
        className="relative inline-flex size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading"
      >
        <ShoppingBag className="size-4" aria-hidden="true" />
        {cartCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[0.6rem] font-bold leading-4 text-[#0b0616]">
            {cartCount}
          </span>
        )}
      </Link>
      <Link
        href="/saved"
        aria-label={`${t('tray.saved')}${saved.length ? ` (${saved.length})` : ''}`}
        className="relative hidden size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading sm:inline-flex"
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
        aria-label={`${t('tray.compare')}${compare.length ? ` (${compare.length})` : ''}`}
        className="relative hidden size-9 items-center justify-center rounded-control text-body/80 transition-colors hover:bg-white/5 hover:text-heading sm:inline-flex"
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
