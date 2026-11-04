import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';
import { ArrowLeft, Check, Package, Truck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { Section } from '@/components/ui/section';
import { getSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate, parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Order',
  robots: { index: false, follow: false },
};

const FLOW = ['pending', 'paid', 'processing', 'shipped', 'delivered'] as const;

const LABELS: Record<string, string> = {
  pending: 'Order placed',
  paid: 'Payment received',
  processing: 'Being prepared',
  shipped: 'On its way',
  delivered: 'Delivered',
};

export default async function CustomerOrderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await getSession().catch(() => null);
  if (!session) redirect('/login');

  const { id } = await params;

  let order;
  try {
    order = await prisma.order.findUnique({ where: { id }, include: { items: true } });
  } catch {
    order = null;
  }
  if (!order) notFound();

  // An order belongs to the customer who placed it; admins can see everything.
  if (session.role !== 'admin' && order.userId !== session.id) {
    redirect('/account/orders');
  }

  const terminal = ['cancelled', 'refunded'].includes(order.status);
  const reachedIndex = FLOW.indexOf(order.status as (typeof FLOW)[number]);
  const address = parseJson<Record<string, string>>(order.shippingAddress, {});

  return (
    <Section>
      <Link
        href="/account/orders"
        className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-heading"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to your orders
      </Link>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <h1 className="font-display text-2xl font-700 text-heading">{order.orderNumber}</h1>
        <Badge tone={terminal ? 'danger' : 'primary'}>{order.status}</Badge>
        <span className="text-sm text-muted">Placed {formatDate(order.createdAt)}</span>
      </div>

      {!terminal ? (
        <ol className="mt-8 grid gap-3 sm:grid-cols-5">
          {FLOW.map((step, index) => {
            const done = index <= reachedIndex;
            return (
              <li
                key={step}
                className={
                  done
                    ? 'rounded-panel border border-primary/40 bg-primary/10 p-4'
                    : 'rounded-panel border border-line bg-surface/40 p-4'
                }
              >
                <span
                  className={
                    done
                      ? 'inline-flex size-6 items-center justify-center rounded-full bg-primary text-[#0b0616]'
                      : 'inline-flex size-6 items-center justify-center rounded-full border border-line text-muted'
                  }
                  aria-hidden="true"
                >
                  {done ? <Check className="size-3.5" /> : index + 1}
                </span>
                <p className={done ? 'mt-2 text-sm font-medium text-heading' : 'mt-2 text-sm text-muted'}>
                  {LABELS[step]}
                </p>
              </li>
            );
          })}
        </ol>
      ) : (
        <Panel className="mt-8 border-red-500/30 bg-red-500/5 p-4">
          <p className="text-sm text-red-200">
            This order was {order.status}. If money was taken, the refund is handled by the payment
            provider and can take a few working days.
          </p>
        </Panel>
      )}

      {order.trackingNumber && (
        <Panel className="mt-4 flex flex-wrap items-center gap-3 p-4">
          <Truck className="size-4 text-accent" aria-hidden="true" />
          <p className="text-sm text-heading">
            {order.carrier ?? 'Carrier'} · tracking {order.trackingNumber}
          </p>
        </Panel>
      )}

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <Panel className="overflow-hidden">
          <div className="border-b border-line/70 px-5 py-4">
            <h2 className="font-display text-base font-600 text-heading">Items</h2>
          </div>
          <ul className="divide-y divide-line/50">
            {order.items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-4 px-5 py-3 text-sm">
                <span className="flex items-center gap-2 text-heading">
                  <Package className="size-4 text-muted" aria-hidden="true" />
                  {item.title} <span className="text-muted">× {item.quantity}</span>
                </span>
                <span className="text-heading">{formatCurrency(item.lineTotal, order.currency)}</span>
              </li>
            ))}
          </ul>
          <dl className="space-y-2 border-t border-line/70 px-5 py-4 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted">Subtotal</dt>
              <dd className="text-heading">{formatCurrency(order.subtotal, order.currency)}</dd>
            </div>
            {order.discount > 0 && (
              <div className="flex justify-between">
                <dt className="text-muted">Discount{order.couponCode ? ` (${order.couponCode})` : ''}</dt>
                <dd className="text-emerald-300">−{formatCurrency(order.discount, order.currency)}</dd>
              </div>
            )}
            <div className="flex justify-between border-t border-line/60 pt-2 text-base">
              <dt className="font-600 text-heading">Total</dt>
              <dd className="font-700 text-accent">{formatCurrency(order.total, order.currency)}</dd>
            </div>
          </dl>
        </Panel>

        <Panel className="h-fit p-5">
          <h2 className="font-display text-base font-600 text-heading">Delivery</h2>
          <p className="mt-2 text-sm leading-relaxed text-body/85">
            {[address.line1, address.line2, address.city, address.region, address.postalCode, address.country]
              .filter(Boolean)
              .join(', ') || 'No address on file'}
          </p>
          <p className="mt-3 text-xs text-muted">
            Shipping is quoted separately: {formatCurrency(order.shipping, order.currency)} recorded.
          </p>
        </Panel>
      </div>
    </Section>
  );
}
