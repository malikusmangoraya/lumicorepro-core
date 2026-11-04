'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

type Session = { name: string; role: 'customer' | 'admin' } | null;

/**
 * The header must not read cookies, or every marketing page becomes dynamic.
 * This island fetches the session once on mount instead, so the rest of the
 * tree can stay statically rendered.
 */
export function SessionMenu() {
  const [session, setSession] = useState<Session | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    fetch('/api/auth/me', { credentials: 'same-origin' })
      .then((response) => (response.ok ? response.json() : null))
      .then(
        (body: { data?: { user?: { name: string; role: string } | null } } | null) => {
          if (cancelled) return;
          const user = body?.data?.user;
          setSession(
            user
              ? { name: user.name, role: user.role === 'admin' ? 'admin' : 'customer' }
              : null,
          );
        },
      )
      .catch(() => {
        if (!cancelled) setSession(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Reserve the same width while the session resolves so the header does not
  // reflow after hydration.
  if (session === undefined) {
    return <span className="h-9 w-24 animate-pulse rounded-control bg-white/5" aria-hidden="true" />;
  }

  if (!session) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="hidden rounded-control px-3 py-2 text-sm font-medium text-body/80 transition-colors hover:text-heading sm:block"
        >
          Sign in
        </Link>
        <Link
          href="/inventory"
          className="rounded-control bg-primary px-4 py-2 text-sm font-semibold text-[#0b0616] transition-colors hover:bg-accent"
        >
          Browse inventory
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {session.role === 'admin' && (
        <Link
          href="/admin"
          className="hidden rounded-control px-3 py-2 text-sm font-medium text-body/80 transition-colors hover:text-heading sm:block"
        >
          Admin
        </Link>
      )}
      <Link
        href="/account"
        className="rounded-control border border-line px-4 py-2 text-sm font-semibold text-heading transition-colors hover:border-primary/60 hover:bg-white/5"
      >
        {session.name.split(' ')[0] || 'Account'}
      </Link>
    </div>
  );
}
