import type { Metadata } from 'next';
import { WifiOff } from 'lucide-react';
import Link from 'next/link';
import { BrandLockup } from '@/components/brand/brand-mark';

export const metadata: Metadata = {
  title: 'Offline',
  robots: { index: false, follow: false },
};

/** Served by the service worker when a page request fails without a network. */
export default function OfflinePage() {
  return (
    <div className="relative flex min-h-dvh flex-col">
      <header className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">
        <BrandLockup />
      </header>

      <main className="mx-auto flex flex-1 flex-col items-center justify-center px-4 pb-20 text-center sm:px-6">
        <WifiOff className="size-10 text-accent" aria-hidden="true" />
        <h1 className="mt-4 font-display text-3xl font-700 text-heading">You are offline</h1>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-muted">
          The page you asked for needs a connection. Everything you already loaded still works, and
          the inventory will refresh when you are back online.
        </p>
        <Link
          href="/"
          className="mt-8 rounded-control bg-primary px-5 py-2.5 text-sm font-semibold text-[#0b0616] transition-colors hover:bg-accent"
        >
          Try the home page
        </Link>
      </main>
    </div>
  );
}
