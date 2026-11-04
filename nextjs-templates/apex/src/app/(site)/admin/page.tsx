import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { Car, CircleDollarSign, Inbox, Users } from 'lucide-react';
import { Section, SectionHeading } from '@/components/ui/section';
import { Panel } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { formatCurrency, formatDate } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Admin',
  robots: { index: false, follow: false },
};

type Metrics = {
  vehicles: number;
  activeVehicles: number;
  inquiries: number;
  newInquiries: number;
  customers: number;
  inventoryValue: number;
  recent: { id: string; name: string; email: string; status: string; createdAt: Date }[];
  ready: boolean;
};

async function loadMetrics(): Promise<Metrics> {
  const empty: Metrics = {
    vehicles: 0,
    activeVehicles: 0,
    inquiries: 0,
    newInquiries: 0,
    customers: 0,
    inventoryValue: 0,
    recent: [],
    ready: false,
  };

  try {
    const [vehicles, activeVehicles, inquiries, newInquiries, customers, value, recent] =
      await Promise.all([
        prisma.vehicle.count(),
        prisma.vehicle.count({ where: { status: 'active' } }),
        prisma.inquiry.count(),
        prisma.inquiry.count({ where: { status: 'new' } }),
        prisma.user.count({ where: { role: 'customer' } }),
        prisma.vehicle.aggregate({ where: { status: 'active' }, _sum: { price: true } }),
        prisma.inquiry.findMany({
          orderBy: { createdAt: 'desc' },
          take: 6,
          select: { id: true, name: true, email: true, status: true, createdAt: true },
        }),
      ]);

    return {
      vehicles,
      activeVehicles,
      inquiries,
      newInquiries,
      customers,
      inventoryValue: value._sum.price ?? 0,
      recent,
      ready: true,
    };
  } catch {
    return empty;
  }
}

export default async function AdminPage() {
  const session = await getSession().catch(() => null);
  if (!session) redirect('/login?next=/admin');
  if (session.role !== 'admin') redirect('/account');

  const metrics = await loadMetrics();

  const cards = [
    { icon: Car, label: 'Vehicles', value: String(metrics.vehicles), hint: `${metrics.activeVehicles} active` },
    { icon: Inbox, label: 'Enquiries', value: String(metrics.inquiries), hint: `${metrics.newInquiries} new` },
    { icon: Users, label: 'Customers', value: String(metrics.customers), hint: 'registered' },
    {
      icon: CircleDollarSign,
      label: 'Active inventory value',
      value: formatCurrency(metrics.inventoryValue, 'USD'),
      hint: 'sum of asking prices',
    },
  ];

  return (
    <Section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <SectionHeading as="h1"
          eyebrow="Control room"
          title="Apex operations"
          description="Live figures from the inventory and enquiry tables. Nothing here is a static mock-up."
        />
        <Badge tone="primary">{session.email}</Badge>
      </div>

      {!metrics.ready && (
        <Panel className="mt-8 border-amber-500/30 bg-amber-500/5 p-5">
          <p className="text-sm text-amber-200">
            The database is not initialised. Run <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>{' '}
            to create the tables and seed the demo data.
          </p>
        </Panel>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Panel key={card.label} className="p-5">
            <card.icon className="size-5 text-accent" aria-hidden="true" />
            <p className="mt-4 font-display text-2xl font-700 text-heading">{card.value}</p>
            <p className="mt-1 text-sm text-muted">{card.label}</p>
            <p className="mt-0.5 text-xs text-muted/70">{card.hint}</p>
          </Panel>
        ))}
      </div>

      <Panel className="mt-8 overflow-hidden">
        <div className="border-b border-line/70 px-5 py-4">
          <h2 className="font-display text-base font-600 text-heading">Latest enquiries</h2>
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

      <p className="mt-6 text-xs text-muted">
        Vehicle create/edit and enquiry status changes are exposed as API routes; wire them into
        this page when you need a full CMS. The template ships the read dashboard.
      </p>
    </Section>
  );
}
