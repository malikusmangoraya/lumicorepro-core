'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { Button, ButtonLink } from '@/components/ui/button';
import { Field, Input, Textarea } from '@/components/ui/field';
import { useSite } from '@/components/providers/site-provider';
import { formatCurrency } from '@/lib/utils';

type Confirmation = { id: string; orderNumber: string; total: number; email: string };

function PayNowButton({ orderId, email }: { orderId: string; email: string }) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  return (
    <div className="mt-4">
      <Button
        disabled={pending}
        onClick={async () => {
          setPending(true);
          setMessage(null);
          try {
            const response = await fetch('/api/payments/checkout', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ orderId, email }),
            });
            const body = (await response.json().catch(() => ({}))) as {
              success?: boolean;
              message?: string;
              data?: { url?: string };
            };
            if (!response.ok || !body.success || !body.data?.url) {
              setMessage(body.message ?? 'Card payment is unavailable right now.');
              setPending(false);
              return;
            }
            window.location.href = body.data.url;
          } catch {
            setMessage('Network error. Please try again.');
            setPending(false);
          }
        }}
      >
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Opening Stripe…
          </>
        ) : (
          'Pay by card'
        )}
      </Button>
      {message && (
        <p className="mt-2 text-xs leading-relaxed text-muted" role="status">
          {message}
        </p>
      )}
    </div>
  );
}

export function CheckoutForm() {
  const router = useRouter();
  const { cart, cartSubtotal, cartCount, clearCart, hydrated, notify, t } = useSite();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<Confirmation | null>(null);
  const [coupon, setCoupon] = useState<{ code: string; discount: number } | null>(null);
  const [couponError, setCouponError] = useState<string | null>(null);
  const [couponPending, setCouponPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) ?? '').trim();

    const payload = {
      email: text('email'),
      name: text('name'),
      phone: text('phone'),
      notes: text('notes') || undefined,
      couponCode: coupon?.code ?? '',
      address: {
        line1: text('line1'),
        line2: text('line2'),
        city: text('city'),
        region: text('region'),
        postalCode: text('postalCode'),
        country: text('country'),
      },
      items: cart.map((item) => ({
        kind: item.kind,
        slug: item.slug,
        quantity: item.quantity,
      })),
    };

    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        data?: { id: string; orderNumber: string; total: number; email: string };
        details?: { fieldErrors?: Record<string, string[]> };
      };

      if (!response.ok || !body.success || !body.data) {
        const first = body.details?.fieldErrors
          ? Object.values(body.details.fieldErrors)[0]?.[0]
          : undefined;
        setError(first ?? body.message ?? 'Could not place the order.');
        setPending(false);
        return;
      }

      clearCart();
      setDone(body.data);
      notify('Order placed');
      router.refresh();
    } catch {
      setError('Network error. Please try again.');
      setPending(false);
    }
  }

  async function applyCoupon(raw: string) {
    const code = raw.trim();
    if (!code) {
      setCoupon(null);
      setCouponError(null);
      return;
    }
    setCouponPending(true);
    setCouponError(null);
    try {
      const response = await fetch(
        `/api/coupons/validate?code=${encodeURIComponent(code)}&subtotal=${cartSubtotal}`,
      );
      const body = (await response.json().catch(() => ({}))) as {
        success?: boolean;
        message?: string;
        data?: { code: string; discount: number };
      };
      if (!response.ok || !body.success || !body.data) {
        setCoupon(null);
        setCouponError(body.message ?? 'That code cannot be used');
        return;
      }
      setCoupon({ code: body.data.code, discount: body.data.discount });
    } catch {
      setCouponError('Network error. Please try again.');
    } finally {
      setCouponPending(false);
    }
  }

  if (done) {
    return (
      <div className="mx-auto max-w-lg rounded-panel border border-emerald-500/30 bg-emerald-500/5 p-8 text-center">
        <CheckCircle2 className="mx-auto size-10 text-emerald-400" aria-hidden="true" />
        <h2 className="mt-4 font-display text-2xl font-700 text-heading">Order placed</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Reference <span className="font-semibold text-heading">{done.orderNumber}</span> for{' '}
          {formatCurrency(done.total, 'USD')}. We emailed a copy to {done.email}.
        </p>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          No email is sent by this template — a specialist would confirm the order and arrange
          delivery.
        </p>
        <PayNowButton orderId={done.id} email={done.email} />
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/shop">Back to the shop</ButtonLink>
          <ButtonLink href="/inventory" variant="outline">
            Browse inventory
          </ButtonLink>
        </div>
      </div>
    );
  }

  if (!hydrated) {
    return <div className="h-64 animate-pulse rounded-panel border border-line bg-surface/40" />;
  }

  if (cart.length === 0) {
    return (
      <div className="rounded-panel border border-dashed border-line bg-surface/40 px-6 py-14 text-center">
        <h2 className="font-600 text-heading">Nothing to check out</h2>
        <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
          Your bag is empty. Add something from the shop, or reserve a car from the inventory.
        </p>
        <div className="mt-5 flex justify-center gap-3">
          <ButtonLink href="/shop">Shop products</ButtonLink>
          <ButtonLink href="/inventory" variant="outline">
            Inventory
          </ButtonLink>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]" noValidate>
      <div className="space-y-6">
        <section className="rounded-panel border border-line bg-surface/50 p-6">
          <h2 className="font-display text-lg font-600 text-heading">{t('checkout.contact')}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Field id="name" label="Full name">
              <Input id="name" name="name" required autoComplete="name" />
            </Field>
            <Field id="email" label="Email">
              <Input id="email" name="email" type="email" required autoComplete="email" />
            </Field>
            <Field id="phone" label="Phone" hint="Optional">
              <Input id="phone" name="phone" type="tel" autoComplete="tel" />
            </Field>
          </div>
        </section>

        <section className="rounded-panel border border-line bg-surface/50 p-6">
          <h2 className="font-display text-lg font-600 text-heading">{t('checkout.address')}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Field id="line1" label="Address line 1">
                <Input id="line1" name="line1" required autoComplete="address-line1" />
              </Field>
            </div>
            <div className="sm:col-span-2">
              <Field id="line2" label="Address line 2" hint="Optional">
                <Input id="line2" name="line2" autoComplete="address-line2" />
              </Field>
            </div>
            <Field id="city" label="City">
              <Input id="city" name="city" required autoComplete="address-level2" />
            </Field>
            <Field id="region" label="State / region">
              <Input id="region" name="region" autoComplete="address-level1" />
            </Field>
            <Field id="postalCode" label="Postal code">
              <Input id="postalCode" name="postalCode" autoComplete="postal-code" />
            </Field>
            <Field id="country" label="Country">
              <Input id="country" name="country" required defaultValue="United States" autoComplete="country-name" />
            </Field>
          </div>
          <div className="mt-4">
            <Field id="notes" label="Delivery notes" hint="Optional">
              <Textarea id="notes" name="notes" rows={2} placeholder="Gate code, preferred time…" />
            </Field>
          </div>
        </section>

        {error && (
          <p role="alert" className="rounded-control border border-red-500/40 bg-red-500/5 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={pending}>
            {pending ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                {t('checkout.placing')}
              </>
            ) : (
              t('checkout.place')
            )}
          </Button>
          <Link href="/cart" className="text-sm text-muted hover:text-heading">
            Back to bag
          </Link>
        </div>
      </div>

      <aside className="h-fit rounded-panel border border-line bg-surface/60 p-6 lg:sticky lg:top-24">
        <h2 className="font-display text-lg font-600 text-heading">{t('checkout.summary')}</h2>
        <ul className="mt-4 space-y-2 text-sm">
          {cart.map((item) => (
            <li key={`${item.kind}-${item.slug}`} className="flex justify-between gap-3">
              <span className="text-muted">
                {item.title} <span className="text-muted/70">× {item.quantity}</span>
              </span>
              <span className="shrink-0 text-heading">
                {formatCurrency(item.price * item.quantity, item.currency)}
              </span>
            </li>
          ))}
        </ul>
        <div className="mt-4 border-t border-line/60 pt-3">
          <label htmlFor="coupon" className="block text-xs font-medium text-muted">
            Discount code
          </label>
          <div className="mt-1.5 flex gap-2">
            <input
              id="coupon"
              defaultValue={coupon?.code ?? ''}
              placeholder="APEX10"
              className="w-full rounded-control border border-line bg-canvas/70 px-3 py-2 text-sm uppercase text-heading placeholder:normal-case placeholder:text-muted/70 focus:border-primary focus:outline-none"
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault();
                  void applyCoupon((event.target as HTMLInputElement).value);
                }
              }}
            />
            <button
              type="button"
              disabled={couponPending}
              onClick={(event) => {
                const input = (event.currentTarget.parentElement?.querySelector('#coupon') ??
                  null) as HTMLInputElement | null;
                void applyCoupon(input?.value ?? '');
              }}
              className="shrink-0 rounded-control border border-line px-3 py-2 text-xs font-semibold text-heading transition-colors hover:border-primary/60 disabled:opacity-60"
            >
              {couponPending ? '…' : 'Apply'}
            </button>
          </div>
          {coupon && (
            <p className="mt-2 text-xs text-emerald-300">
              {coupon.code} applied · −{formatCurrency(coupon.discount, 'USD')}
            </p>
          )}
          {couponError && (
            <p role="alert" className="mt-2 text-xs text-red-400">
              {couponError}
            </p>
          )}
        </div>

        <dl className="mt-4 space-y-2 border-t border-line/60 pt-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted">Items</dt>
            <dd className="text-heading">{cartCount}</dd>
          </div>
          {coupon && (
            <div className="flex justify-between">
              <dt className="text-muted">Discount</dt>
              <dd className="text-emerald-300">−{formatCurrency(coupon.discount, 'USD')}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-muted">{t('cart.shipping')}</dt>
            <dd className="text-muted">Quoted after order</dd>
          </div>
          <div className="flex justify-between border-t border-line/60 pt-2 text-base">
            <dt className="font-600 text-heading">{t('cart.total')}</dt>
            <dd className="font-700 text-accent">
              {formatCurrency(Math.max(0, cartSubtotal - (coupon?.discount ?? 0)), 'USD')}
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-xs leading-relaxed text-muted">
          {t('checkout.note')}
        </p>
      </aside>
    </form>
  );
}
