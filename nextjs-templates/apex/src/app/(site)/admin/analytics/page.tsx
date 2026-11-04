import { Panel } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Stars } from '@/components/ui/stars';
import { prisma } from '@/lib/prisma';
import { bucketByDay, isRevenueStatus, percentageChange } from '@/lib/analytics';
import { formatCurrency } from '@/lib/utils';

export const dynamic = 'force-dynamic';

const DAYS = 14;
const WINDOW_MS = DAYS * 24 * 60 * 60 * 1000;

async function loadAnalytics() {
  const since = new Date(Date.now() - WINDOW_MS * 2);

  try {
    const [orders, byStatus, inquiries, topVehicles, topProducts, subscribers, reviewStats] =
      await Promise.all([
        prisma.order.findMany({
          where: { createdAt: { gte: since } },
          select: { createdAt: true, total: true, status: true },
        }),
        prisma.order.groupBy({
          by: ['status'],
          _count: { _all: true },
          _sum: { total: true },
        }),
        prisma.inquiry.count(),
        prisma.inquiry.groupBy({
          by: ['vehicleId'],
          where: { vehicleId: { not: null } },
          _count: { _all: true },
          orderBy: { _count: { vehicleId: 'desc' } },
          take: 5,
        }),
        prisma.orderItem.groupBy({
          by: ['title'],
          where: { order: { status: { in: ['paid', 'processing', 'shipped', 'delivered'] } } },
          _sum: { quantity: true },
          orderBy: { _sum: { quantity: 'desc' } },
          take: 5,
        }),
        prisma.newsletterSubscriber.count({ where: { isActive: true } }),
        prisma.review.aggregate({
          where: { status: 'approved' },
          _avg: { rating: true },
          _count: { _all: true },
        }),
      ]);

    const vehicleIds = topVehicles.map((row) => row.vehicleId).filter(Boolean) as string[];
    const vehicles = vehicleIds.length
      ? await prisma.vehicle.findMany({
          where: { id: { in: vehicleIds } },
          select: { id: true, title: true, slug: true },
        })
      : [];
    const vehicleById = new Map(vehicles.map((vehicle) => [vehicle.id, vehicle]));

    const cutoff = Date.now() - WINDOW_MS;
    const currentOrders = orders.filter((order) => order.createdAt.getTime() >= cutoff);
    const previousOrders = orders.filter((order) => order.createdAt.getTime() < cutoff);

    const sum = (rows: typeof orders) =>
      rows.filter((order) => isRevenueStatus(order.status)).reduce((total, order) => total + order.total, 0);

    const currentRevenue = sum(currentOrders);
    const previousRevenue = sum(previousOrders);
    const paidCurrent = currentOrders.filter((order) => isRevenueStatus(order.status));

    return {
      ready: true,
      buckets: bucketByDay(currentOrders, DAYS),
      currentRevenue,
      revenueChange: percentageChange(currentRevenue, previousRevenue),
      currentOrders: currentOrders.length,
      orderChange: percentageChange(currentOrders.length, previousOrders.length),
      averageOrder: paidCurrent.length ? currentRevenue / paidCurrent.length : 0,
      byStatus: byStatus.map((row) => ({
        status: row.status,
        count: row._count._all,
        value: row._sum.total ?? 0,
      })),
      inquiries,
      topVehicles: topVehicles.map((row) => ({
        title: vehicleById.get(row.vehicleId as string)?.title ?? 'Removed vehicle',
        slug: vehicleById.get(row.vehicleId as string)?.slug ?? null,
        count: row._count._all,
      })),
      topProducts: topProducts.map((row) => ({
        title: row.title,
        units: row._sum.quantity ?? 0,
      })),
      subscribers,
      reviewAverage: reviewStats._avg.rating ? Math.round(reviewStats._avg.rating * 10) / 10 : null,
      reviewCount: reviewStats._count._all,
    };
  } catch {
    return { ready: false } as const;
  }
}

function Chart({ buckets }: { buckets: { date: string; label: string; revenue: number; orders: number }[] }) {
  const max = Math.max(...buckets.map((bucket) => bucket.revenue), 1);
  const width = 640;
  const height = 180;
  const gap = 6;
  const barWidth = (width - gap * (buckets.length - 1)) / buckets.length;

  return (
    <svg
      viewBox={`0 0 ${width} ${height + 28}`}
      role="img"
      aria-label="Revenue over the last 14 days"
      className="mt-5 w-full"
    >
      {[0.25, 0.5, 0.75, 1].map((line) => (
        <line
          key={line}
          x1={0}
          x2={width}
          y1={height - height * line}
          y2={height - height * line}
          stroke="currentColor"
          className="text-line/60"
          strokeWidth="1"
        />
      ))}
      {buckets.map((bucket, index) => {
        const barHeight = bucket.revenue === 0 ? 2 : Math.max(4, (bucket.revenue / max) * (height - 10));
        return (
          <g key={bucket.date}>
            <rect
              x={index * (barWidth + gap)}
              y={height - barHeight}
              width={barWidth}
              height={barHeight}
              rx={3}
              className="fill-primary"
            >
              <title>{`${bucket.date}: ${bucket.orders} order(s)`}</title>
            </rect>
            <text
              x={index * (barWidth + gap) + barWidth / 2}
              y={height + 16}
              textAnchor="middle"
              className="fill-current text-[9px] text-muted"
            >
              {bucket.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default async function AdminAnalyticsPage() {
  const data = await loadAnalytics();

  if (!data.ready) {
    return (
      <Panel className="p-6 text-sm text-muted">
        The database is not initialised. Run{' '}
        <code className="rounded bg-canvas px-1.5 py-0.5">npm run db:setup</code>.
      </Panel>
    );
  }

  const kpis = [
    {
      label: 'Revenue',
      value: formatCurrency(data.currentRevenue, 'USD'),
      change: data.revenueChange,
      hint: `last ${DAYS} days, paid onwards`,
    },
    {
      label: 'Orders',
      value: String(data.currentOrders),
      change: data.orderChange,
      hint: `last ${DAYS} days`,
    },
    {
      label: 'Average order',
      value: formatCurrency(data.averageOrder, 'USD'),
      change: null,
      hint: 'paid orders only',
    },
    {
      label: 'Subscribers',
      value: String(data.subscribers),
      change: null,
      hint: 'active newsletter',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-xl font-700 text-heading">Analytics</h2>
        <p className="mt-1 text-sm text-muted">
          Measured from this database only. Unpaid and cancelled orders count as orders but not as
          revenue.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <Panel key={kpi.label} className="p-5">
            <p className="text-xs uppercase tracking-[0.14em] text-muted">{kpi.label}</p>
            <p className="mt-2 font-display text-2xl font-700 text-heading">{kpi.value}</p>
            <p className="mt-1 text-xs text-muted">{kpi.hint}</p>
            {kpi.change !== null && (
              <p
                className={
                  kpi.change >= 0 ? 'mt-2 text-xs font-medium text-emerald-400' : 'mt-2 text-xs font-medium text-red-400'
                }
              >
                {kpi.change >= 0 ? '+' : ''}
                {kpi.change}% vs previous {DAYS} days
              </p>
            )}
          </Panel>
        ))}
      </div>

      <Panel className="p-6">
        <h3 className="font-display text-base font-600 text-heading">Revenue, last {DAYS} days</h3>
        <Chart buckets={data.buckets} />
      </Panel>

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel className="p-5">
          <h3 className="font-display text-base font-600 text-heading">Orders by status</h3>
          {data.byStatus.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No orders yet.</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {data.byStatus.map((row) => (
                <li key={row.status} className="flex items-center justify-between gap-3 text-sm">
                  <span className="flex items-center gap-2">
                    <Badge tone={row.status === 'pending' ? 'warning' : 'neutral'}>{row.status}</Badge>
                  </span>
                  <span className="text-muted">
                    {row.count} · {formatCurrency(row.value, 'USD')}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel className="p-5">
          <h3 className="font-display text-base font-600 text-heading">Most enquired vehicles</h3>
          {data.topVehicles.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No enquiries yet.</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {data.topVehicles.map((row) => (
                <li key={row.title} className="flex items-center justify-between gap-3 text-sm">
                  <span className="truncate text-heading">{row.title}</span>
                  <span className="shrink-0 text-muted">{row.count}</span>
                </li>
              ))}
            </ul>
          )}

          <h3 className="mt-6 font-display text-base font-600 text-heading">Best selling products</h3>
          {data.topProducts.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No paid orders yet.</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {data.topProducts.map((row) => (
                <li key={row.title} className="flex items-center justify-between gap-3 text-sm">
                  <span className="truncate text-heading">{row.title}</span>
                  <span className="shrink-0 text-muted">{row.units} units</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-display text-base font-600 text-heading">Trust signals</h3>
          <span className="text-sm text-muted">
            {data.reviewCount} approved review{data.reviewCount === 1 ? '' : 's'}
          </span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          {data.reviewAverage !== null ? (
            <>
              <Stars rating={data.reviewAverage} size={16} />
              <span className="text-sm text-heading">{data.reviewAverage} / 5</span>
            </>
          ) : (
            <span className="text-sm text-muted">No approved reviews yet.</span>
          )}
          <span className="text-sm text-muted">· {data.inquiries} enquiries all time</span>
        </div>
      </Panel>
    </div>
  );
}
