import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import { ButtonLink } from '@/components/ui/button';
import { Panel } from '@/components/ui/card';
import { Section, SectionHeading } from '@/components/ui/section';
import { getSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Your orders',
  robots: { index: false, follow: false },
};

const TONES: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'neutral'> = {
  pending: 'warning',
  paid: 'primary',
  processing: 'primary',
  shipped: 'success',
  delivered: 'success',
  cancelled: 'danger',
  refunded: 'neutral',
};

export default async function AccountOrdersPage() {
  const session = await getSession().catch(() => null);
  if (!session) redirect('/login?next=/account/orders');

  let orders: { id: string; orderNumber: string; status: string; total: number; currency: string; createdAt: Date }[] = [];
  let ready = true;

  try {
    orders = await prisma.order.findMany({
      where: { userId: session.id },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        orderNumber: true,
        status: true,
        total: true,
        currency: true,
        createdAt: true,
      },
    });
  } catch {
    ready = false;
  }

  return (
    <Section>
      <SectionHeading as="h1"
        eyebrow="Account"
        title="Your orders"
        description="Everything you have ordered from the shop or reserved from the inventory."
      />

      <p className="mt-4">
        <Link href="/account" className="text-sm text-muted hover:text-heading">
          ← Back to account
        </Link>
      </p>

      <div className="mt-8">
        {!ready ? (
          <Panel className="p-6 text-sm text-muted">
            The database is not initialised. Run{' '}
            <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
          </Panel>
        ) : orders.length === 0 ? (
          <Panel className="p-10 text-center">
            <p className="font-600 text-heading">No orders yet</p>
            <p className="mx-auto mt-2 max-w-sm text-sm text-muted">
              Orders you place with this account show up here.
            </p>
            <div className="mt-5 flex justify-center gap-3">
              <ButtonLink href="/shop">Shop</ButtonLink>
              <ButtonLink href="/inventory" variant="outline">
                Inventory
              </ButtonLink>
            </div>
          </Panel>
        ) : (
          <Panel className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-muted">
                  <tr className="border-b border-line/70">
                    <th scope="col" className="px-5 py-3 font-medium">Order</th>
                    <th scope="col" className="px-5 py-3 font-medium">Status</th>
                    <th scope="col" className="px-5 py-3 font-medium">Total</th>
                    <th scope="col" className="px-5 py-3 font-medium">Placed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/50">
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td className="px-5 py-3 font-medium text-heading">{order.orderNumber}</td>
                      <td className="px-5 py-3">
                        <Badge tone={TONES[order.status] ?? 'neutral'}>{order.status}</Badge>
                      </td>
                      <td className="px-5 py-3 text-heading">
                        {formatCurrency(order.total, order.currency)}
                      </td>
                      <td className="px-5 py-3 text-muted">{formatDate(order.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        )}
      </div>
    </Section>
  );
}
