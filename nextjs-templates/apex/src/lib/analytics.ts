/**
 * Analytics helpers.
 *
 * Bucketing is done in JavaScript rather than SQL so the same code runs on
 * SQLite and Postgres without a dialect branch. The pure functions are tested;
 * loadAnalytics() is the only part that touches Prisma.
 */

export type DayBucket = { date: string; label: string; revenue: number; orders: number };

const REVENUE_STATUSES = ['paid', 'processing', 'shipped', 'delivered'];

export function isRevenueStatus(status: string): boolean {
  return REVENUE_STATUSES.includes(status);
}

/** YYYY-MM-DD in UTC, so a server in one zone and a viewer in another agree. */
export function dayKey(value: Date | string): string {
  const date = typeof value === 'string' ? new Date(value) : value;
  return date.toISOString().slice(0, 10);
}

/**
 * Bucket orders into the last `days` days, oldest first, filling gaps with
 * zeros so the chart has one bar per day rather than a jagged line.
 */
export function bucketByDay(
  orders: { createdAt: Date | string; total: number; status: string }[],
  days: number,
  now: Date = new Date(),
): DayBucket[] {
  const buckets: DayBucket[] = [];
  const index = new Map<string, DayBucket>();

  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const date = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
    date.setUTCDate(date.getUTCDate() - offset);
    const key = dayKey(date);
    const bucket: DayBucket = {
      date: key,
      label: `${date.getUTCDate()}/${date.getUTCMonth() + 1}`,
      revenue: 0,
      orders: 0,
    };
    buckets.push(bucket);
    index.set(key, bucket);
  }

  for (const order of orders) {
    const bucket = index.get(dayKey(order.createdAt));
    if (!bucket) continue;
    bucket.orders += 1;
    if (isRevenueStatus(order.status)) bucket.revenue = Math.round((bucket.revenue + order.total) * 100) / 100;
  }

  return buckets;
}

export function percentageChange(current: number, previous: number): number | null {
  if (previous === 0) return current === 0 ? 0 : null;
  return Math.round(((current - previous) / previous) * 1000) / 10;
}
