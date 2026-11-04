import { describe, expect, it } from 'vitest';
import { bucketByDay, dayKey, isRevenueStatus, percentageChange } from '@/lib/analytics';

const now = new Date('2026-11-04T12:00:00.000Z');

describe('bucketByDay', () => {
  it('returns one bucket per day, oldest first', () => {
    const buckets = bucketByDay([], 7, now);
    expect(buckets).toHaveLength(7);
    expect(buckets[0].date).toBe('2026-10-29');
    expect(buckets[6].date).toBe('2026-11-04');
  });

  it('fills gaps with zero instead of skipping days', () => {
    const buckets = bucketByDay([], 3, now);
    expect(buckets.every((bucket) => bucket.revenue === 0 && bucket.orders === 0)).toBe(true);
  });

  it('counts an order on its own day', () => {
    const buckets = bucketByDay(
      [{ createdAt: '2026-11-04T09:30:00.000Z', total: 100, status: 'paid' }],
      3,
      now,
    );
    expect(buckets[2].orders).toBe(1);
    expect(buckets[2].revenue).toBe(100);
  });

  it('counts orders but not revenue for unpaid or cancelled orders', () => {
    const buckets = bucketByDay(
      [
        { createdAt: '2026-11-03T10:00:00.000Z', total: 500, status: 'pending' },
        { createdAt: '2026-11-03T11:00:00.000Z', total: 900, status: 'cancelled' },
      ],
      3,
      now,
    );
    expect(buckets[1].orders).toBe(2);
    expect(buckets[1].revenue).toBe(0);
  });

  it('ignores orders outside the window', () => {
    const buckets = bucketByDay(
      [{ createdAt: '2026-01-01T00:00:00.000Z', total: 1000, status: 'paid' }],
      7,
      now,
    );
    expect(buckets.reduce((sum, bucket) => sum + bucket.revenue, 0)).toBe(0);
  });
});

describe('isRevenueStatus', () => {
  it('counts every post-payment status', () => {
    for (const status of ['paid', 'processing', 'shipped', 'delivered']) {
      expect(isRevenueStatus(status)).toBe(true);
    }
    for (const status of ['pending', 'cancelled', 'refunded']) {
      expect(isRevenueStatus(status)).toBe(false);
    }
  });
});

describe('dayKey', () => {
  it('uses UTC so two timezones agree', () => {
    expect(dayKey(new Date('2026-11-04T23:30:00.000Z'))).toBe('2026-11-04');
    expect(dayKey(new Date('2026-11-05T00:30:00.000Z'))).toBe('2026-11-05');
  });
});

describe('percentageChange', () => {
  it('computes a normal change', () => {
    expect(percentageChange(150, 100)).toBe(50);
    expect(percentageChange(50, 100)).toBe(-50);
  });

  it('returns null when the baseline is zero and the value is not', () => {
    expect(percentageChange(10, 0)).toBeNull();
    expect(percentageChange(0, 0)).toBe(0);
  });
});
