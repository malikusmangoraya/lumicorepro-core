'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Loader2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';

type Option = { slug: string; label: string; price: number; currency: string };

export function OrderCreateForm({
  vehicles,
  products,
}: {
  vehicles: Option[];
  products: Option[];
}) {
  const router = useRouter();
  const { notify } = useSite();
  const [kind, setKind] = useState<'vehicle' | 'product'>('vehicle');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const options = kind === 'vehicle' ? vehicles : products;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) ?? '').trim();
    const number = (key: string) => Number(form.get(key) ?? 0);
    const slug = text('slug');

    const payload: Record<string, unknown> = {
      customerEmail: text('customerEmail'),
      quantity: number('quantity') || 1,
      shipping: number('shipping'),
      discount: number('discount'),
      notes: text('notes') || undefined,
      ...(kind === 'vehicle' ? { vehicleSlug: slug } : { productSlug: slug }),
    };
    const override = text('unitPrice');
    if (override) payload.unitPrice = Number(override);

    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        data?: { id?: string };
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success || !body.data?.id) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setError(first ?? body.message ?? 'Could not create the order.');
        setPending(false);
        return;
      }

      notify('Order created');
      router.push(`/admin/orders/${body.data.id}`);
      router.refresh();
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  if (options.length === 0) {
    return (
      <p className="rounded-panel border border-dashed border-line bg-surface/40 px-5 py-8 text-sm text-muted">
        There are no {kind === 'vehicle' ? 'vehicles' : 'products'} to sell yet. Add one first.
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6" noValidate>
      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Customer</h2>
        <div className="mt-4 max-w-md">
          <Field id="customerEmail" label="Email" hint="Links the order to an account if one exists">
            <Input
              id="customerEmail"
              name="customerEmail"
              type="email"
              required
              placeholder="buyer@example.com"
            />
          </Field>
        </div>
      </section>

      <section className="rounded-panel border border-line bg-surface/50 p-6">
        <h2 className="font-display text-lg font-600 text-heading">Line item</h2>

        <div className="mt-4 flex gap-2" role="group" aria-label="Item type">
          {(['vehicle', 'product'] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setKind(option)}
              aria-pressed={kind === option}
              className={
                kind === option
                  ? 'rounded-control border border-primary/60 bg-primary/10 px-3.5 py-2 text-sm font-semibold text-accent'
                  : 'rounded-control border border-line px-3.5 py-2 text-sm font-medium text-body/80 hover:bg-white/5'
              }
            >
              {option === 'vehicle' ? 'Vehicle' : 'Shop product'}
            </button>
          ))}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field id="slug" label={kind === 'vehicle' ? 'Vehicle' : 'Product'}>
            <Select id="slug" name="slug" required>
              {options.map((option) => (
                <option key={option.slug} value={option.slug}>
                  {option.label} — {option.currency} {option.price.toLocaleString()}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="quantity" label="Quantity">
            <Input id="quantity" name="quantity" type="number" min={1} max={99} defaultValue={1} />
          </Field>
          <Field id="unitPrice" label="Unit price override" hint="Optional">
            <Input id="unitPrice" name="unitPrice" type="number" min={1} step="0.01" />
          </Field>
          <Field id="discount" label="Discount">
            <Input id="discount" name="discount" type="number" min={0} step="0.01" defaultValue={0} />
          </Field>
          <Field id="shipping" label="Shipping">
            <Input id="shipping" name="shipping" type="number" min={0} step="0.01" defaultValue={0} />
          </Field>
        </div>

        <div className="mt-4">
          <Field id="notes" label="Internal notes">
            <Textarea id="notes" name="notes" rows={2} placeholder="Phone order, agreed delivery…" />
          </Field>
        </div>
      </section>

      {error && (
        <p role="alert" className="rounded-control border border-red-500/40 bg-red-500/5 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <Button type="submit" disabled={pending}>
          {pending ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Creating…
            </>
          ) : (
            <>
              <Plus className="size-4" aria-hidden="true" />
              Create order
            </>
          )}
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.push('/admin/orders')}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
