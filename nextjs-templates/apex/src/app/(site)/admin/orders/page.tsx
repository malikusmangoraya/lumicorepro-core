import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ButtonLink } from '@/components/ui/button';
import { Panel } from '@/components/ui/card';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Prisma } from '@prisma/client';

export const dynamic = 'force-dynamic';

const STATUSES = [
  'pending',
  'paid',
  'processing',
  'shipped',
  'delivered',
  'cancelled',
  'refunded',
] as const;

const TONES: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  pending: 'warning',
  paid: 'primary',
  processing: 'primary',
  shipped: 'success',
  delivered: 'success',
  cancelled: 'danger',
  refunded: 'neutral',
};

export default async function AdminOrdersPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; q?: string }>;
}) {
  const { status, q } = await searchParams;
  const filter = STATUSES.includes(status as (typeof STATUSES)[number])
    ? (status as (typeof STATUSES)[number])
    : undefined;

  let orders: Prisma.OrderGetPayload<{ include: { items: true } }>[] = [];
  let ready = true;

  try {
    orders = await prisma.order.findMany({
      where: {
        ...(filter ? { status: filter } : {}),
        ...(q
          ? {
              OR: [{ orderNumber: { contains: q } }, { customerEmail: { contains: q } }],
            }
          : {}),
      },
      orderBy: { createdAt: 'desc' },
      take: 100,
      include: { items: true },
    });
  } catch {
    ready = false;
  }

  const revenue = orders
    .filter((order) => ['paid', 'processing', 'shipped', 'delivered'].includes(order.status))
    .reduce((sum, order) => sum + order.total, 0);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-700 text-heading">Orders</h2>
          <p className="mt-1 text-sm text-muted">
            {orders.length} order{orders.length === 1 ? '' : 's'} ·{' '}
            {formatCurrency(revenue, 'USD')} collected (paid onwards)
          </p>
        </div>
        <ButtonLink href="/admin/orders/new">
          <Plus className="size-4" aria-hidden="true" />
          New order
        </ButtonLink>
      </div>

      <form action="/admin/orders" method="get" className="flex flex-wrap gap-2" role="search">
        {filter && <input type="hidden" name="status" value={filter} />}
        <label htmlFor="order-search" className="sr-only">
          Search orders
        </label>
        <input
          id="order-search"
          name="q"
          defaultValue={q ?? ''}
          placeholder="Order number or customer email"
          className="w-full max-w-xs rounded-control border border-line bg-canvas/70 px-3 py-2 text-sm text-heading placeholder:text-muted/70 focus:border-primary focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-control border border-line px-3 py-2 text-sm font-semibold text-heading transition-colors hover:border-primary/60 hover:bg-white/5"
        >
          Search
        </button>
      </form>

      <nav aria-label="Filter orders by status">
        <ul className="flex flex-wrap gap-1">
          <li>
            <Link
              href="/admin/orders"
              className={`inline-flex rounded-control px-3 py-1.5 text-xs font-medium ${
                !filter ? 'bg-primary/15 text-accent' : 'text-body/75 hover:bg-white/5'
              }`}
            >
              All
            </Link>
          </li>
          {STATUSES.map((option) => (
            <li key={option}>
              <Link
                href={`/admin/orders?status=${option}`}
                className={`inline-flex rounded-control px-3 py-1.5 text-xs font-medium ${
                  filter === option ? 'bg-primary/15 text-accent' : 'text-body/75 hover:bg-white/5'
                }`}
              >
                {option}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {!ready ? (
        <Panel className="p-6 text-sm text-muted">
          The database is not initialised. Run{' '}
          <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
        </Panel>
      ) : orders.length === 0 ? (
        <Panel className="p-10 text-center">
          <p className="font-600 text-heading">No orders{filter ? ` with status “${filter}”` : ''}</p>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
            Manual orders can be created here; the storefront checkout is the other source.
          </p>
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-line/70">
                  <th scope="col" className="px-5 py-3 font-medium">Order</th>
                  <th scope="col" className="px-5 py-3 font-medium">Customer</th>
                  <th scope="col" className="px-5 py-3 font-medium">Status</th>
                  <th scope="col" className="px-5 py-3 font-medium">Items</th>
                  <th scope="col" className="px-5 py-3 font-medium">Total</th>
                  <th scope="col" className="px-5 py-3 font-medium">Placed</th>
                  <th scope="col" className="px-5 py-3 text-right font-medium">Open</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-5 py-3">
                      <Link
                        href={`/admin/orders/${order.id}`}
                        className="font-medium text-heading hover:text-accent"
                      >
                        {order.orderNumber}
                      </Link>
                      {order.trackingNumber && (
                        <p className="text-xs text-muted">{order.carrier} · {order.trackingNumber}</p>
                      )}
                    </td>
                    <td className="px-5 py-3 text-muted">{order.customerEmail}</td>
                    <td className="px-5 py-3">
                      <Badge tone={TONES[order.status] ?? 'neutral'}>{order.status}</Badge>
                    </td>
                    <td className="px-5 py-3 text-muted">
                      {order.items.reduce((sum, item) => sum + item.quantity, 0)}
                    </td>
                    <td className="px-5 py-3 text-heading">
                      {formatCurrency(order.total, order.currency)}
                    </td>
                    <td className="px-5 py-3 text-muted">{formatDate(order.createdAt)}</td>
                    <td className="px-5 py-3 text-right">
                      <Link
                        href={`/admin/orders/${order.id}`}
                        className="text-xs font-semibold text-accent hover:underline"
                      >
                        Manage
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
