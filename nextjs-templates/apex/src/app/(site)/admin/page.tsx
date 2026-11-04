import Link from 'next/link';
import { Car, CircleDollarSign, Inbox, Mail, MessageSquare } from 'lucide-react';
import { Panel } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

async function loadMetrics() {
  const empty = {
    vehicles: 0,
    active: 0,
    draft: 0,
    withdrawn: 0,
    inquiries: 0,
    newInquiries: 0,
    subscribers: 0,
    inventoryValue: 0,
    recent: [] as { id: string; name: string; email: string; status: string; createdAt: Date }[],
    ready: false,
  };

  try {
    const [
      vehicles,
      active,
      draft,
      withdrawn,
      inquiries,
      newInquiries,
      subscribers,
      value,
      recent,
    ] = await Promise.all([
      prisma.vehicle.count(),
      prisma.vehicle.count({ where: { status: 'active' } }),
      prisma.vehicle.count({ where: { status: 'draft' } }),
      prisma.vehicle.count({ where: { status: 'withdrawn' } }),
      prisma.inquiry.count(),
      prisma.inquiry.count({ where: { status: 'new' } }),
      prisma.newsletterSubscriber.count({ where: { isActive: true } }),
      prisma.vehicle.aggregate({ where: { status: 'active' }, _sum: { price: true } }),
      prisma.inquiry.findMany({
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: { id: true, name: true, email: true, status: true, createdAt: true },
      }),
    ]);

    return {
      vehicles,
      active,
      draft,
      withdrawn,
      inquiries,
      newInquiries,
      subscribers,
      inventoryValue: value._sum.price ?? 0,
      recent,
      ready: true,
    };
  } catch {
    return empty;
  }
}

export default async function AdminOverviewPage() {
  const metrics = await loadMetrics();

  const cards = [
    {
      icon: Car,
      label: 'Vehicles',
      value: String(metrics.vehicles),
      hint: `${metrics.active} active · ${metrics.draft} draft · ${metrics.withdrawn} withdrawn`,
      href: '/admin/vehicles',
    },
    {
      icon: Inbox,
      label: 'Enquiries',
      value: String(metrics.inquiries),
      hint: `${metrics.newInquiries} new`,
      href: '/admin/inquiries',
    },
    {
      icon: Mail,
      label: 'Subscribers',
      value: String(metrics.subscribers),
      hint: 'active newsletter',
      href: '/admin/newsletter',
    },
    {
      icon: CircleDollarSign,
      label: 'Active inventory value',
      value: formatCurrency(metrics.inventoryValue, 'USD'),
      hint: 'sum of asking prices',
      href: '/admin/vehicles',
    },
  ];

  return (
    <div className="space-y-8">
      {!metrics.ready && (
        <Panel className="border-amber-500/30 bg-amber-500/5 p-5">
          <p className="text-sm text-amber-200">
            The database is not initialised. Run{' '}
            <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code> to create the
            tables and seed the demo data.
          </p>
        </Panel>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Link key={card.label} href={card.href} className="group">
            <Panel className="h-full p-5 transition-colors group-hover:border-primary/50">
              <card.icon className="size-5 text-accent" aria-hidden="true" />
              <p className="mt-4 font-display text-2xl font-700 text-heading">{card.value}</p>
              <p className="mt-1 text-sm text-muted">{card.label}</p>
              <p className="mt-0.5 text-xs text-muted/70">{card.hint}</p>
            </Panel>
          </Link>
        ))}
      </div>

      <Panel className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line/70 px-5 py-4">
          <h2 className="flex items-center gap-2 font-display text-base font-600 text-heading">
            <MessageSquare className="size-4 text-accent" aria-hidden="true" />
            Latest enquiries
          </h2>
          <Link href="/admin/inquiries" className="text-xs font-medium text-accent hover:underline">
            View the queue
          </Link>
        </div>
        {metrics.recent.length === 0 ? (
          <p className="px-5 py-8 text-sm text-muted">No enquiries yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-line/60">
                  <th scope="col" className="px-5 py-3 font-medium">Name</th>
                  <th scope="col" className="px-5 py-3 font-medium">Email</th>
                  <th scope="col" className="px-5 py-3 font-medium">Status</th>
                  <th scope="col" className="px-5 py-3 font-medium">Received</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/50">
                {metrics.recent.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-3 text-heading">{row.name}</td>
                    <td className="px-5 py-3 text-muted">{row.email}</td>
                    <td className="px-5 py-3">
                      <Badge tone={row.status === 'new' ? 'primary' : 'neutral'}>{row.status}</Badge>
                    </td>
                    <td className="px-5 py-3 text-muted">{formatDate(row.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
