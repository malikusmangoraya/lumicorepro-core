import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Panel } from '@/components/ui/card';
import { OrderActions } from '@/components/admin/order-actions';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate, parseJson } from '@/lib/utils';

export const dynamic = 'force-dynamic';

function AddressBlock({ raw, title }: { raw: string; title: string }) {
  const address = parseJson<Record<string, string>>(raw, {});
  const lines = [address.line1, address.line2, address.city, address.region, address.postalCode, address.country]
    .filter(Boolean);

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{title}</h3>
      {lines.length === 0 ? (
        <p className="mt-1 text-sm text-muted">Not provided</p>
      ) : (
        <p className="mt-1 text-sm leading-relaxed text-body/85">{lines.join(', ')}</p>
      )}
    </div>
  );
}

export default async function AdminOrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let order;
  try {
    order = await prisma.order.findUnique({
      where: { id },
      include: { items: true, payments: true, user: { select: { name: true, email: true } } },
    });
  } catch {
    order = null;
  }

  if (!order) notFound();

  return (
    <div className="space-y-5">
      <div>
        <Link
          href="/admin/orders"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-heading"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to orders
        </Link>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <h2 className="font-display text-xl font-700 text-heading">{order.orderNumber}</h2>
          <Badge tone={order.status === 'cancelled' || order.status === 'refunded' ? 'danger' : 'primary'}>
            {order.status}
          </Badge>
          <span className="text-sm text-muted">Placed {formatDate(order.createdAt)}</span>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-5">
          <Panel className="overflow-hidden">
            <div className="border-b border-line/70 px-5 py-4">
              <h2 className="font-display text-base font-600 text-heading">Items</h2>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-line/60">
                  <th scope="col" className="px-5 py-3 font-medium">Item</th>
                  <th scope="col" className="px-5 py-3 font-medium">Unit</th>
                  <th scope="col" className="px-5 py-3 font-medium">Qty</th>
                  <th scope="col" className="px-5 py-3 text-right font-medium">Line</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {order.items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-3 text-heading">{item.title}</td>
                    <td className="px-5 py-3 text-muted">
                      {formatCurrency(item.unitPrice, order.currency)}
                    </td>
                    <td className="px-5 py-3 text-muted">{item.quantity}</td>
                    <td className="px-5 py-3 text-right text-heading">
                      {formatCurrency(item.lineTotal, order.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <dl className="space-y-2 border-t border-line/70 px-5 py-4 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Subtotal</dt>
                <dd className="text-heading">{formatCurrency(order.subtotal, order.currency)}</dd>
              </div>
              {order.discount > 0 && (
                <div className="flex justify-between">
                  <dt className="text-muted">Discount</dt>
                  <dd className="text-emerald-300">
                    −{formatCurrency(order.discount, order.currency)}
                  </dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-muted">Tax</dt>
                <dd className="text-heading">{formatCurrency(order.tax, order.currency)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Shipping</dt>
                <dd className="text-heading">{formatCurrency(order.shipping, order.currency)}</dd>
              </div>
              <div className="flex justify-between border-t border-line/60 pt-2 text-base">
                <dt className="font-600 text-heading">Total</dt>
                <dd className="font-700 text-accent">
                  {formatCurrency(order.total, order.currency)}
                </dd>
              </div>
            </dl>
          </Panel>

          <Panel className="p-5">
            <h2 className="font-display text-base font-600 text-heading">Customer</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Email</h3>
                <p className="mt-1 text-sm text-body/85">{order.customerEmail}</p>
                {order.user && (
                  <p className="mt-1 text-xs text-muted">Account: {order.user.name}</p>
                )}
              </div>
              <AddressBlock raw={order.shippingAddress} title="Shipping address" />
              <AddressBlock raw={order.billingAddress} title="Billing address" />
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Payment</h3>
                <p className="mt-1 text-sm text-body/85">
                  {order.paymentMethod ?? 'Not recorded'} · {order.isPaid ? 'paid' : 'unpaid'}
                </p>
                {order.payments.length > 0 && (
                  <ul className="mt-1 space-y-0.5 text-xs text-muted">
                    {order.payments.map((payment) => (
                      <li key={payment.id}>
                        {payment.provider} · {payment.status} ·{' '}
                        {formatCurrency(payment.amount, payment.currency)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            {order.notes && (
              <p className="mt-4 border-t border-line/60 pt-3 text-sm leading-relaxed text-muted">
                {order.notes}
              </p>
            )}
          </Panel>
        </div>

        <Panel className="h-fit p-5">
          <OrderActions
            id={order.id}
            status={order.status}
            carrier={order.carrier}
            trackingNumber={order.trackingNumber}
            notes={order.notes}
          />
        </Panel>
      </div>
    </div>
  );
}
