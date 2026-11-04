'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';
import { nextStatuses, primaryAction } from '@/lib/orders';

export function OrderActions({
  id,
  status,
  carrier,
  trackingNumber,
  notes,
}: {
  id: string;
  status: string;
  carrier: string | null;
  trackingNumber: string | null;
  notes: string | null;
}) {
  const router = useRouter();
  const { notify } = useSite();
  const [current, setCurrent] = useState(status);
  const [pending, setPending] = useState<string | null>(null);
  const [carrierValue, setCarrierValue] = useState(carrier ?? '');
  const [trackingValue, setTrackingValue] = useState(trackingNumber ?? '');
  const [notesValue, setNotesValue] = useState(notes ?? '');

  async function patch(payload: Record<string, unknown>, label: string) {
    setPending(label);
    try {
      const response = await fetch(`/api/orders/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        data?: { status?: string };
      };
      if (!response.ok || !body.success) {
        notify(body.message ?? 'Could not update the order');
        return;
      }
      if (typeof payload.status === 'string') setCurrent(payload.status);
      notify('Order updated');
      router.refresh();
    } catch {
      notify('Network error. Please try again.');
    } finally {
      setPending(null);
    }
  }

  const allowed = nextStatuses(current);
  const primary = primaryAction(current);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-lg font-600 text-heading">Next step</h2>
        <p className="mt-1 text-sm text-muted">
          Status moves in order. Refunds are allowed after payment; a cancelled or refunded order
          cannot be reopened.
        </p>

        {allowed.length === 0 ? (
          <p className="mt-4 rounded-control border border-line bg-canvas/50 px-4 py-3 text-sm text-muted">
            This order is in a terminal state.
          </p>
        ) : (
          <div className="mt-4 flex flex-wrap gap-2">
            {primary && (
              <Button
                onClick={() => patch({ status: primary.to }, primary.label)}
                disabled={pending !== null}
              >
                {pending === primary.label ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : null}
                {primary.label}
              </Button>
            )}
            {allowed
              .filter((option) => option !== primary?.to)
              .map((option) => (
                <Button
                  key={option}
                  variant={option === 'cancelled' || option === 'refunded' ? 'danger' : 'outline'}
                  onClick={() => patch({ status: option }, option)}
                  disabled={pending !== null}
                >
                  {pending === option ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  ) : null}
                  {option === 'refunded' ? 'Refund' : option === 'cancelled' ? 'Cancel order' : option}
                </Button>
              ))}
          </div>
        )}
      </div>

      <div className="border-t border-line/70 pt-5">
        <h2 className="font-display text-lg font-600 text-heading">Shipping</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field id="carrier" label="Carrier">
            <Input
              id="carrier"
              value={carrierValue}
              onChange={(event) => setCarrierValue(event.target.value)}
              placeholder="DHL, FedEx, enclosed transport…"
            />
          </Field>
          <Field id="tracking" label="Tracking number">
            <Input
              id="tracking"
              value={trackingValue}
              onChange={(event) => setTrackingValue(event.target.value)}
              placeholder="1Z…"
            />
          </Field>
        </div>
        <Button
          variant="outline"
          className="mt-3"
          disabled={pending !== null}
          onClick={() => patch({ carrier: carrierValue, trackingNumber: trackingValue }, 'shipping')}
        >
          {pending === 'shipping' ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : null}
          Save shipping
        </Button>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          A tracking number is required before an order can be marked shipped or delivered.
        </p>
      </div>

      <div className="border-t border-line/70 pt-5">
        <h2 className="font-display text-lg font-600 text-heading">Internal notes</h2>
        <div className="mt-3">
          <Field id="order-notes" label="Notes" hint="Not shown to the customer">
            <Textarea
              id="order-notes"
              value={notesValue}
              onChange={(event) => setNotesValue(event.target.value)}
              rows={3}
            />
          </Field>
        </div>
        <Button
          variant="outline"
          className="mt-3"
          disabled={pending !== null}
          onClick={() => patch({ notes: notesValue }, 'notes')}
        >
          {pending === 'notes' ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : null}
          Save notes
        </Button>
      </div>
    </div>
  );
}
