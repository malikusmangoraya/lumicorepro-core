'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Check, Loader2, Trash2, X } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function ReviewModeration({ id, status }: { id: string; status: string }) {
  const router = useRouter();
  const { notify } = useSite();
  const [current, setCurrent] = useState(status);
  const [pending, setPending] = useState<string | null>(null);

  async function act(action: 'approved' | 'rejected' | 'delete') {
    setPending(action);
    try {
      const response = await fetch(`/api/reviews/${encodeURIComponent(id)}`, {
        method: action === 'delete' ? 'DELETE' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: action === 'delete' ? undefined : JSON.stringify({ status: action }),
      });
      const body = (await response.json().catch(() => ({}))) as { message?: string };
      if (!response.ok) {
        notify(body.message ?? 'Could not update the review');
        return;
      }
      if (action !== 'delete') setCurrent(action);
      notify(action === 'delete' ? 'Review deleted' : `Review ${action}`);
      router.refresh();
    } catch {
      notify('Network error. Please try again.');
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        disabled={pending !== null || current === 'approved'}
        onClick={() => act('approved')}
        className="inline-flex items-center gap-1 rounded-control border border-emerald-500/40 px-2.5 py-1.5 text-xs font-semibold text-emerald-300 transition-colors hover:bg-emerald-500/10 disabled:opacity-40"
      >
        {pending === 'approved' ? (
          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
        ) : (
          <Check className="size-3" aria-hidden="true" />
        )}
        Approve
      </button>
      <button
        type="button"
        disabled={pending !== null || current === 'rejected'}
        onClick={() => act('rejected')}
        className="inline-flex items-center gap-1 rounded-control border border-amber-500/40 px-2.5 py-1.5 text-xs font-semibold text-amber-300 transition-colors hover:bg-amber-500/10 disabled:opacity-40"
      >
        {pending === 'rejected' ? (
          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
        ) : (
          <X className="size-3" aria-hidden="true" />
        )}
        Reject
      </button>
      <button
        type="button"
        disabled={pending !== null}
        onClick={() => {
          if (window.confirm('Delete this review permanently?')) void act('delete');
        }}
        aria-label="Delete review"
        className="inline-flex size-8 items-center justify-center rounded-control border border-red-500/40 text-red-300 transition-colors hover:bg-red-500/10 disabled:opacity-40"
      >
        {pending === 'delete' ? (
          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
        ) : (
          <Trash2 className="size-3" aria-hidden="true" />
        )}
      </button>
    </div>
  );
}
