'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import { Loader2, Pencil, Trash2 } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function VehicleRowActions({
  slug,
  title,
  status,
}: {
  slug: string;
  title: string;
  status: string;
}) {
  const router = useRouter();
  const { notify } = useSite();
  const [pending, setPending] = useState(false);

  const withdraw = async () => {
    if (!window.confirm(`Withdraw "${title}"? It stops appearing in the storefront.`)) return;
    setPending(true);
    try {
      const response = await fetch(`/api/vehicles/${encodeURIComponent(slug)}`, {
        method: 'DELETE',
      });
      const body = (await response.json().catch(() => ({}))) as { message?: string };
      if (!response.ok) {
        notify(body.message ?? 'Could not withdraw the vehicle');
        return;
      }
      notify(`Withdrew ${title}`);
      router.refresh();
    } catch {
      notify('Network error. Please try again.');
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex items-center justify-end gap-2">
      <Link
        href={`/admin/vehicles/${encodeURIComponent(slug)}/edit`}
        className="inline-flex items-center gap-1.5 rounded-control border border-line px-2.5 py-1.5 text-xs font-semibold text-heading transition-colors hover:border-primary/60 hover:bg-white/5"
      >
        <Pencil className="size-3" aria-hidden="true" />
        Edit
      </Link>
      <button
        type="button"
        onClick={withdraw}
        disabled={pending || status === 'withdrawn'}
        className="inline-flex items-center gap-1.5 rounded-control border border-red-500/40 px-2.5 py-1.5 text-xs font-semibold text-red-300 transition-colors hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {pending ? (
          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
        ) : (
          <Trash2 className="size-3" aria-hidden="true" />
        )}
        Withdraw
      </button>
    </div>
  );
}
