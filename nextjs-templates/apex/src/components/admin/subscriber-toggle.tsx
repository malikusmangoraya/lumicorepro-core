'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useSite } from '@/components/providers/site-provider';

export function SubscriberToggle({ id, isActive }: { id: string; isActive: boolean }) {
  const router = useRouter();
  const { notify } = useSite();
  const [active, setActive] = useState(isActive);
  const [pending, setPending] = useState(false);

  return (
    <button
      type="button"
      disabled={pending}
      aria-pressed={active}
      onClick={async () => {
        const next = !active;
        setPending(true);
        try {
          const response = await fetch(`/api/newsletter/${encodeURIComponent(id)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ isActive: next }),
          });
          const body = (await response.json().catch(() => ({}))) as { message?: string };
          if (!response.ok) {
            notify(body.message ?? 'Could not update the subscriber');
            return;
          }
          setActive(next);
          notify(next ? 'Subscriber reactivated' : 'Subscriber unsubscribed');
          router.refresh();
        } catch {
          notify('Network error. Please try again.');
        } finally {
          setPending(false);
        }
      }}
      className={
        active
          ? 'inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-300'
          : 'inline-flex items-center gap-1.5 rounded-full border border-line bg-white/5 px-2.5 py-1 text-xs font-semibold text-muted'
      }
    >
      {pending && <Loader2 className="size-3 animate-spin" aria-hidden="true" />}
      {active ? 'Active' : 'Unsubscribed'}
    </button>
  );
}
