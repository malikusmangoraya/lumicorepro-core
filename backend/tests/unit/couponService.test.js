/**
 * Coupon service tests.
 *
 * `applyCoupon` is the money path that decides how much a buyer actually pays,
 * so every rejection branch (inactive, not-yet-started, expired, usage limit,
 * minimum subtotal) and every discount formula is pinned here against the real
 * service and the in-memory Sequelize doubles.
 *
 * Services under test enforce two invariants: a discount is always finite and
 * inside [0, subtotal], and a limited coupon is consumed with a compare-and-set
 * rather than read-then-write. Every behaviour here is asserted, not pinned as
 * an expected failure — do not reintroduce `it.failing` in this repo.
 */
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { Op } from 'sequelize';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const models = {};

jest.unstable_mockModule('../../models/Coupon.js', () => ({
  __esModule: true,
  default: {
    findOne: (options) => models.Coupon.findOne(options),
    update: (values, options) => models.Coupon.update(values, options),
  },
}));

// applyCoupon reads the buyer's order history for the per-user limit.
jest.unstable_mockModule('../../models/Order.js', () => ({
  __esModule: true,
  default: {
    count: (options) => models.Order.count(options),
  },
}));

const { default: Coupon } = await import('../../models/Coupon.js');
const couponService = await import('../../services/couponService.js');
const { applyCoupon, markCouponUsed } = couponService;

/** Coupon rows carry no Sequelize `increment`, so the double gets a real one. */
function withIncrement(model) {
  const originalFindOne = model.findOne;
  model.findOne = async (options) => {
    const instance = await originalFindOne(options);
    if (!instance) return null;
    instance.increment = async (field, byOrOptions = 1) => {
      const by = typeof byOrOptions === 'number' ? byOrOptions : 1;
      const row = instance._row;
      model.calls.push({ method: 'increment', options: { where: { id: row.id }, field, by } });
      row[field] = Number(row[field] || 0) + by;
      return instance;
    };
    return instance;
  };
  return model;
}

function seedCoupon(overrides = {}) {
  const row = {
    id: 1,
    code: 'SPRING24',
    type: 'percentage',
    value: '10.00',
    minSubtotal: '0.00',
    maxDiscount: null,
    usageLimit: 0,
    usageCount: 0,
    perUserLimit: 1,
    startsAt: null,
    expiresAt: null,
    isActive: true,
    ...overrides,
  };
  models.Coupon = withIncrement(createFakeModel('Coupon', [row]));
  return row;
}

const inHours = (hours) => new Date(Date.now() + hours * 60 * 60 * 1000);

/** Prior purchases are the per-user redemption ledger. */
function seedOrders(rows = []) {
  models.Order = createFakeModel('Order', rows);
  return models.Order;
}

const priorOrder = (overrides = {}) => ({
  id: 40,
  user_id: 7,
  promoCode: 'SPRING24',
  status: 'delivered',
  deleted_at: null,
  ...overrides,
});

beforeEach(() => {
  seedCoupon();
  seedOrders();
});

describe('applyCoupon — lookup and rejection branches', () => {
  it('short-circuits an empty code without touching the database', async () => {
    const result = await applyCoupon('', 100);

    expect(result).toEqual({ applied: false, discount: 0 });
    expect(models.Coupon.calls).toEqual([]);
  });

  it('reports an unknown code as not found', async () => {
    const result = await applyCoupon('NOPE', 100);

    expect(result.applied).toBe(false);
    expect(result.discount).toBe(0);
    expect(result.error).toBe('Coupon not found or inactive');
  });

  it('ignores inactive coupons', async () => {
    seedCoupon({ code: 'DEAD', isActive: false });

    const result = await applyCoupon('DEAD', 100);

    expect(result.applied).toBe(false);
    expect(result.error).toBe('Coupon not found or inactive');
  });

  it('normalises case and whitespace before querying', async () => {
    seedCoupon({ code: 'SPRING24' });

    const result = await applyCoupon('  spring24  ', 200);

    expect(result.applied).toBe(true);
    expect(result.discount).toBe(20);
    const where = models.Coupon.whereCalls('findOne')[0].where;
    expect(where.code).toBe('SPRING24');
    expect(where.isActive).toBe(true);
  });

  it('rejects a coupon whose window has not started', async () => {
    seedCoupon({ startsAt: inHours(24) });

    const result = await applyCoupon('SPRING24', 200);

    expect(result).toMatchObject({ applied: false, discount: 0, error: 'This coupon is not yet active' });
  });

  it('rejects an expired coupon', async () => {
    seedCoupon({ expiresAt: inHours(-1) });

    const result = await applyCoupon('SPRING24', 200);

    expect(result).toMatchObject({ applied: false, discount: 0, error: 'This coupon has expired' });
  });

  it('accepts a coupon that expires in the future', async () => {
    seedCoupon({ startsAt: inHours(-24), expiresAt: inHours(24) });

    const result = await applyCoupon('SPRING24', 200);

    expect(result.applied).toBe(true);
    expect(result.discount).toBe(20);
  });

  it('rejects once the global usage limit is reached', async () => {
    seedCoupon({ usageLimit: 5, usageCount: 5 });

    const result = await applyCoupon('SPRING24', 200);

    expect(result).toMatchObject({ applied: false, error: 'This coupon has reached its usage limit' });
  });

  it('treats usageLimit 0 as unlimited', async () => {
    seedCoupon({ usageLimit: 0, usageCount: 9999 });

    const result = await applyCoupon('SPRING24', 200);

    expect(result.applied).toBe(true);
  });

  it('rejects a basket below the minimum subtotal', async () => {
    seedCoupon({ minSubtotal: '150.00' });

    const result = await applyCoupon('SPRING24', 149.99);

    expect(result.applied).toBe(false);
    expect(result.error).toBe('Minimum order subtotal of $150.00 required');
  });

  it('honours the coupon exactly at the minimum subtotal', async () => {
    seedCoupon({ minSubtotal: '150.00' });

    const result = await applyCoupon('SPRING24', 150);

    expect(result.applied).toBe(true);
  });
});

describe('applyCoupon — discount maths', () => {
  it('takes a percentage of the subtotal', async () => {
    seedCoupon({ type: 'percentage', value: '10.00' });

    expect((await applyCoupon('SPRING24', 200)).discount).toBe(20);
  });

  it('caps a percentage discount at maxDiscount', async () => {
    seedCoupon({ type: 'percentage', value: '50.00', maxDiscount: '30.00' });

    expect((await applyCoupon('SPRING24', 200)).discount).toBe(30);
  });

  it('rounds the discount to whole cents', async () => {
    seedCoupon({ type: 'percentage', value: '15.00' });

    expect((await applyCoupon('SPRING24', 33.33)).discount).toBe(5);
  });

  it('never lets a fixed discount exceed the subtotal', async () => {
    seedCoupon({ type: 'fixed', value: '500.00' });

    expect((await applyCoupon('SPRING24', 100)).discount).toBe(100);
  });

  it('applies a fixed discount smaller than the subtotal', async () => {
    seedCoupon({ type: 'fixed', value: '25.50' });

    expect((await applyCoupon('SPRING24', 100)).discount).toBe(25.5);
  });

  it('applies free-shipping coupons with a zero item discount', async () => {
    seedCoupon({ type: 'free_shipping', value: '0.00' });

    const result = await applyCoupon('SPRING24', 100);

    expect(result).toMatchObject({ applied: true, discount: 0 });
  });

  it('returns no discount for an unrecognised coupon type', async () => {
    seedCoupon({ type: 'mystery', value: '10.00' });

    const result = await applyCoupon('SPRING24', 100);

    expect(result).toMatchObject({ applied: true, discount: 0 });
  });

  it('returns the coupon row alongside the discount', async () => {
    seedCoupon({ code: 'BRAND', value: '5.00' });

    const result = await applyCoupon('BRAND', 100);

    expect(result.coupon.code).toBe('BRAND');
  });
});

describe('markCouponUsed', () => {
  it('increments the stored usage counter', async () => {
    const row = seedCoupon({ usageCount: 2 });
    const coupon = await Coupon.findOne({ where: { code: 'SPRING24' } });

    await markCouponUsed(coupon);

    expect(row.usageCount).toBe(3);
    const increment = models.Coupon.calls.find((c) => c.method === 'increment');
    expect(increment.options.where.id).toBe(1);
    expect(increment.options.field).toBe('usageCount');
  });

  it('is a no-op without a coupon', async () => {
    await expect(markCouponUsed(null)).resolves.toBe(false);
    expect(models.Coupon.calls).toEqual([]);
  });
});


/* ══════════════════════════════════════════════════════════════════════
 * Money invariants — each of these was once an `it.failing` placeholder.
 * They are enforced now; a regression here fails the suite.
 * ══════════════════════════════════════════════════════════════════════ */

describe('applyCoupon — clamp and per-user rules', () => {
  it('caps a percentage discount at the subtotal, not only at maxDiscount', async () => {
    seedCoupon({ type: 'percentage', value: '150.00' });

    const { discount } = await applyCoupon('SPRING24', 100);

    expect(discount).toBe(100);
  });

  it('never returns a NaN discount when the row carries a null value', async () => {
    seedCoupon({ type: 'percentage', value: null });

    const { applied, discount } = await applyCoupon('SPRING24', 100);

    expect(applied).toBe(true);
    expect(Number.isFinite(discount)).toBe(true);
    expect(discount).toBe(0);
  });

  it('clamps a negative coupon value to 0 instead of raising the basket price', async () => {
    seedCoupon({ type: 'percentage', value: '-50.00' });

    const { discount } = await applyCoupon('SPRING24', 100);

    expect(discount).toBe(0);
  });

  it('skips the minimum-spend rule and reports 0 for a code-only check', async () => {
    seedCoupon({ minSubtotal: '150.00' });

    const result = await applyCoupon('SPRING24', null);

    expect(result).toMatchObject({ applied: true, discount: 0 });
  });
});

describe('applyCoupon — perUserLimit', () => {
  it('refuses a single-use coupon the buyer already redeemed', async () => {
    seedCoupon({ perUserLimit: 1 });
    seedOrders([priorOrder()]);

    const withUser = await couponService.applyCoupon('SPRING24', 100, { userId: 7 });

    expect(withUser).toMatchObject({ applied: false, discount: 0, error: 'You have already used this coupon' });
  });

  it('counts only that buyer and only redemptions that still stand', async () => {
    seedCoupon({ perUserLimit: 1 });

    const other = await applyCoupon('SPRING24', 100, { userId: 8 });
    expect(other.applied).toBe(true);

    seedOrders([priorOrder({ status: 'cancelled' })]);
    const afterCancel = await applyCoupon('SPRING24', 100, { userId: 7 });
    expect(afterCancel.applied).toBe(true);

    const where = models.Order.whereCalls('count').at(-1).where;
    expect(where.user_id).toBe(7);
    expect(where.promoCode).toBe('SPRING24');
    expect(where.status[Op.notIn]).toEqual(['cancelled', 'refunded']);
  });

  it('leaves a guest check unchanged — there is no buyer to count', async () => {
    seedCoupon({ perUserLimit: 1 });
    seedOrders([priorOrder()]);

    const result = await applyCoupon('SPRING24', 100);

    expect(result.applied).toBe(true);
    expect(models.Order.calls).toEqual([]);
  });

  it('treats perUserLimit 0 as unlimited', async () => {
    seedCoupon({ perUserLimit: 0 });
    seedOrders([priorOrder(), priorOrder({ id: 41 })]);

    const result = await applyCoupon('SPRING24', 100, { userId: 7 });

    expect(result.applied).toBe(true);
  });
});

describe('markCouponUsed — atomic consumption', () => {
  it('consumes the last unit with a compare-and-set, never both callers', async () => {
    seedCoupon({ usageLimit: 1, usageCount: 0 });
    const { coupon } = await applyCoupon('SPRING24', 100);

    const results = await Promise.all([markCouponUsed(coupon), markCouponUsed(coupon)]);

    expect(results.filter(Boolean)).toHaveLength(1);
    expect(models.Coupon.rows[0].usageCount).toBe(1);
  });

  it('writes the guard into the UPDATE, not only the read', async () => {
    seedCoupon({ usageLimit: 3, usageCount: 1 });
    const { coupon } = await applyCoupon('SPRING24', 100);

    await markCouponUsed(coupon, { transaction: 'tx-1' });

    const update = models.Coupon.calls.filter((c) => c.method === 'update').at(-1).options;
    expect(update.values).toEqual({ usageCount: 2 });
    expect(update.options.where).toEqual({ id: 1, usageCount: 1 });
    expect(update.options.transaction).toBe('tx-1');
  });

  it('refuses a coupon whose limit the row already reached', async () => {
    seedCoupon({ usageLimit: 2, usageCount: 2 });
    const coupon = await Coupon.findOne({ where: { code: 'SPRING24' } });

    await expect(markCouponUsed(coupon)).resolves.toBe(false);
    expect(models.Coupon.calls.filter((c) => c.method === 'update')).toEqual([]);
  });

  it('increments freely when the coupon has no limit', async () => {
    const row = seedCoupon({ usageLimit: 0, usageCount: 4 });
    const coupon = await Coupon.findOne({ where: { code: 'SPRING24' } });

    await expect(markCouponUsed(coupon)).resolves.toBe(true);
    expect(row.usageCount).toBe(5);
  });
});
