'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Minus, Plus, ShoppingBag, Trash2 } from 'lucide-react';
import { ButtonLink } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/section';
import { useSite } from '@/components/providers/site-provider';
import { formatCurrency } from '@/lib/utils';

export function CartView() {
  const { cart, cartCount, cartSubtotal, setQuantity, removeFromCart, hydrated, notify, t } =
    useSite();

  if (!hydrated) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 2 }).map((_, index) => (
          <div key={index} className="h-28 animate-pulse rounded-panel border border-line bg-surface/40" />
        ))}
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <EmptyState
        title={t('cart.empty')}
        description="Browse the shop for care kits and driving gear, or reserve a car from the inventory."
        action={
          <ButtonLink href="/shop">
            <ShoppingBag className="size-4" aria-hidden="true" />
            Go to the shop
          </ButtonLink>
        }
      />
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
      <ul className="space-y-3">
        {cart.map((item) => (
          <li
            key={`${item.kind}-${item.slug}`}
            className="flex flex-wrap items-center gap-4 rounded-panel border border-line bg-surface/60 p-4"
          >
            <div className="relative size-20 shrink-0 overflow-hidden rounded-lg border border-line bg-canvas">
              {item.image ? (
                <Image src={item.image} alt={item.title} fill sizes="80px" className="object-cover" />
              ) : null}
            </div>

            <div className="min-w-0 flex-1">
              <p className="font-medium text-heading">{item.title}</p>
              <p className="text-xs text-muted">
                {item.kind === 'vehicle' ? 'Vehicle reservation' : 'Shop product'} ·{' '}
                {formatCurrency(item.price, item.currency)}
              </p>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                aria-label={`Decrease quantity of ${item.title}`}
                onClick={() => setQuantity(item.slug, item.quantity - 1)}
                className="inline-flex size-8 items-center justify-center rounded-control border border-line text-heading hover:border-primary/60"
              >
                <Minus className="size-3.5" aria-hidden="true" />
              </button>
              <span className="w-8 text-center text-sm text-heading" aria-live="polite">
                {item.quantity}
              </span>
              <button
                type="button"
                aria-label={`Increase quantity of ${item.title}`}
                onClick={() => setQuantity(item.slug, item.quantity + 1)}
                disabled={item.kind === 'vehicle'}
                className="inline-flex size-8 items-center justify-center rounded-control border border-line text-heading hover:border-primary/60 disabled:opacity-40"
              >
                <Plus className="size-3.5" aria-hidden="true" />
              </button>
            </div>

            <p className="w-24 text-right font-display text-base font-600 text-heading">
              {formatCurrency(item.price * item.quantity, item.currency)}
            </p>

            <button
              type="button"
              aria-label={`Remove ${item.title}`}
              onClick={() => {
                removeFromCart(item.slug);
                notify(`Removed ${item.title}`);
              }}
              className="rounded p-1.5 text-muted transition-colors hover:text-red-300"
            >
              <Trash2 className="size-4" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>

      <aside className="h-fit rounded-panel border border-line bg-surface/60 p-6 lg:sticky lg:top-24">
        <h2 className="font-display text-lg font-600 text-heading">Summary</h2>
        <dl className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted">{t('cart.subtotal')}</dt>
            <dd className="text-heading">{cartCount}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">Subtotal</dt>
            <dd className="text-heading">{formatCurrency(cartSubtotal, 'USD')}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">{t('cart.shipping')}</dt>
            <dd className="text-muted">Quoted after order</dd>
          </div>
          <div className="flex justify-between border-t border-line/60 pt-2 text-base">
            <dt className="font-600 text-heading">{t('cart.total')}</dt>
            <dd className="font-700 text-accent">{formatCurrency(cartSubtotal, 'USD')}</dd>
          </div>
        </dl>

        <ButtonLink href="/checkout" fullWidth className="mt-5">
          {t('cart.checkout')}
        </ButtonLink>
        <Link href="/shop" className="mt-3 block text-center text-xs text-muted hover:text-heading">
          {t('cart.continue')}
        </Link>
      </aside>
    </div>
  );
}
