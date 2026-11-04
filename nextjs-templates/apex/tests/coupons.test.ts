import { describe, expect, it } from 'vitest';
import { discountFor, type CouponLike } from '@/lib/coupons';

const base: CouponLike = {
  code: 'APEX10',
  type: 'percent',
  value: 10,
  minSubtotal: null,
  maxDiscount: null,
  usageLimit: null,
  usedCount: 0,
  startsAt: null,
  expiresAt: null,
  isActive: true,
};

describe('discountFor', () => {
  it('takes a percentage off the subtotal', () => {
    const result = discountFor(base, 500);
    expect(result).toMatchObject({ ok: true, discount: 50 });
  });

  it('takes a fixed amount, never more than the subtotal', () => {
    const result = discountFor({ ...base, type: 'fixed', value: 200 }, 150);
    expect(result).toMatchObject({ ok: true, discount: 150 });
  });

  it('caps a percentage discount at maxDiscount', () => {
    const result = discountFor({ ...base, maxDiscount: 25 }, 500);
    expect(result).toMatchObject({ ok: true, discount: 25 });
  });

  it('refuses below the minimum subtotal', () => {
    const result = discountFor({ ...base, minSubtotal: 1000 }, 500);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toContain('at least');
  });

  it('refuses an inactive, expired or not-yet-active code', () => {
    expect(discountFor({ ...base, isActive: false }, 500).ok).toBe(false);
    expect(discountFor({ ...base, expiresAt: new Date('2020-01-01') }, 500).ok).toBe(false);
    expect(discountFor({ ...base, startsAt: new Date('2099-01-01') }, 500).ok).toBe(false);
  });

  it('refuses a code that has hit its usage limit', () => {
    const result = discountFor({ ...base, usageLimit: 5, usedCount: 5 }, 500);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toContain('fully redeemed');
  });

  it('refuses a code worth nothing', () => {
    expect(discountFor({ ...base, value: 0 }, 500).ok).toBe(false);
  });

  it('rounds to cents', () => {
    const result = discountFor({ ...base, value: 33.333 }, 100);
    expect(result).toMatchObject({ ok: true, discount: 33.33 });
  });
});
