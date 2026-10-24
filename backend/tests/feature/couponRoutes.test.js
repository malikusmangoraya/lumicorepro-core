/**
 * Feature tests — POST /api/coupons/validate
 *
 * Exercises the route against the REAL services/couponService.js (the route used
 * to re-implement the rules inline, so this is the regression guard for that
 * duplication) with the Coupon and Order models replaced by the in-memory
 * doubles. `optionalProtect` is stubbed: an `x-test-user` header means "signed
 * in", no header means "anonymous", which is exactly the distinction the
 * per-user limit depends on.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() },
  withRequestId: () => ({ info: jest.fn(), warn: jest.fn(), error: jest.fn() }),
  redact: (value) => value,
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    const id = req.headers['x-test-user'];
    if (id) req.user = { id: Number(id), role: req.headers['x-test-role'] || 'user', email: `buyer${id}@example.test` };
    next();
  },
  optionalProtect: (req, _res, next) => {
    const id = req.headers['x-test-user'];
    if (id) req.user = { id: Number(id), role: req.headers['x-test-role'] || 'user', email: `buyer${id}@example.test` };
    next();
  },
  authorize:
    (...roles) =>
    (req, res, next) => {
      if (!req.user || !roles.includes(req.user.role)) {
        return res.status(403).json({ success: false, error: 'Not authorized' });
      }
      return next();
    },
}));

const baseCoupon = (overrides = {}) => ({
  id: 1,
  code: 'SAVE10',
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
});

const couponRows = () => [
  baseCoupon(),
  baseCoupon({ id: 2, code: 'CAP5', value: '50.00', maxDiscount: '5.00' }),
  baseCoupon({ id: 3, code: 'FLAT25', type: 'fixed', value: '25.00' }),
  baseCoupon({ id: 4, code: 'SHIP', type: 'free_shipping', value: '0.00' }),
  baseCoupon({ id: 5, code: 'EXPIRED', expiresAt: new Date('2026-01-01T00:00:00Z') }),
  baseCoupon({ id: 6, code: 'FUTURE', startsAt: new Date('2027-01-01T00:00:00Z') }),
  baseCoupon({ id: 7, code: 'MAXED', usageLimit: 2, usageCount: 2 }),
  baseCoupon({ id: 8, code: 'MIN50', minSubtotal: '50.00' }),
  baseCoupon({ id: 9, code: 'ONCE', perUserLimit: 1 }),
  baseCoupon({ id: 10, code: 'OFF', isActive: false }),
  baseCoupon({ id: 11, code: 'ROUND', value: '10.00' }),
];

const orderRows = () => [
  { id: 1, user_id: 42, promoCode: 'ONCE', status: 'delivered' },
  { id: 2, user_id: 43, promoCode: 'ONCE', status: 'cancelled' },
];

const Coupon = createFakeModel('Coupon', couponRows());
const Order = createFakeModel('Order', orderRows());

jest.unstable_mockModule('../../models/Coupon.js', () => ({ __esModule: true, default: Coupon }));
jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: Order }));

const { default: couponRoutes } = await import('../../routes/coupon.routes.js');

const app = express();
app.use(express.json());
app.use('/api/coupons', couponRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const validate = (bodyData, { userId } = {}) => {
  const agent = request(app).post('/api/coupons/validate');
  if (userId) agent.set('x-test-user', String(userId));
  return agent.send(bodyData);
};

beforeEach(() => {
  Coupon.rows.length = 0;
  Coupon.rows.push(...couponRows());
  Coupon.calls.length = 0;
  Order.rows.length = 0;
  Order.rows.push(...orderRows());
  Order.calls.length = 0;
});

describe('POST /api/coupons/validate — request validation', () => {
  it.each([
    ['a missing code', {}],
    ['a blank code', { code: '   ' }],
    ['a negative subtotal', { code: 'SAVE10', subtotal: -5 }],
    ['a non-numeric subtotal', { code: 'SAVE10', subtotal: 'lots' }],
  ])('rejects %s with 400 before any coupon lookup', async (_label, bodyData) => {
    const res = await validate(bodyData);

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(Coupon.calls).toHaveLength(0);
  });
});

describe('POST /api/coupons/validate — lookup failures', () => {
  it('404s an unknown code', async () => {
    const res = await validate({ code: 'NOPE', subtotal: 100 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Coupon not found or inactive' });
  });

  it('404s an inactive coupon', async () => {
    const res = await validate({ code: 'OFF', subtotal: 100 });

    expect(res.status).toBe(404);
  });

  it('400s an expired coupon', async () => {
    const res = await validate({ code: 'EXPIRED', subtotal: 100 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'This coupon has expired' });
  });

  it('400s a coupon that is not active yet', async () => {
    const res = await validate({ code: 'FUTURE', subtotal: 100 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'This coupon is not yet active' });
  });

  it('400s a coupon whose usage limit is spent', async () => {
    const res = await validate({ code: 'MAXED', subtotal: 100 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'This coupon has reached its usage limit' });
  });
});

describe('POST /api/coupons/validate — discounts', () => {
  it('applies a percentage coupon and projects the coupon fields', async () => {
    const res = await validate({ code: 'SAVE10', subtotal: 200 });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      coupon: {
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        maxDiscount: null,
      },
      discount: 20,
    });
  });

  it('is case-insensitive and trims the submitted code', async () => {
    const res = await validate({ code: '  save10 ', subtotal: 100 });

    expect(res.status).toBe(200);
    expect(Coupon.calls.find((c) => c.method === 'findOne').options.where.code).toBe('SAVE10');
    expect(res.body.discount).toBe(10);
  });

  it('rounds a percentage discount to cents', async () => {
    const res = await validate({ code: 'ROUND', subtotal: 33.33 });

    expect(res.body.discount).toBe(3.33);
  });

  it('caps a percentage discount at maxDiscount', async () => {
    const res = await validate({ code: 'CAP5', subtotal: 1000 });

    expect(res.body.discount).toBe(5);
    expect(res.body.coupon.maxDiscount).toBe(5);
  });

  it('clamps a fixed discount to the subtotal', async () => {
    const res = await validate({ code: 'FLAT25', subtotal: 10 });

    expect(res.body.discount).toBe(10);
  });

  it('reports a free-shipping coupon with a zero item discount', async () => {
    const res = await validate({ code: 'SHIP', subtotal: 80 });

    expect(res.status).toBe(200);
    expect(res.body.coupon.type).toBe('free_shipping');
    expect(res.body.discount).toBe(0);
  });

  it('enforces the minimum subtotal and names the threshold', async () => {
    const below = await validate({ code: 'MIN50', subtotal: 49.99 });
    expect(below.status).toBe(400);
    expect(below.body).toEqual({
      success: false,
      error: 'Minimum order subtotal of $50.00 required',
    });

    const at = await validate({ code: 'MIN50', subtotal: 50 });
    expect(at.status).toBe(200);
    expect(at.body.discount).toBe(5);
  });

  it('a code-only preview skips the minimum-spend rule and reports 0', async () => {
    const res = await validate({ code: 'MIN50' });

    expect(res.status).toBe(200);
    expect(res.body.discount).toBe(0);
    expect(res.body.coupon.code).toBe('MIN50');
  });
});

describe('POST /api/coupons/validate — per-user limit', () => {
  it('refuses a signed-in buyer who already consumed the coupon', async () => {
    const res = await validate({ code: 'ONCE', subtotal: 100 }, { userId: 42 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'You have already used this coupon' });
    const [count] = Order.calls.filter((c) => c.method === 'count');
    expect(count.options.where.user_id).toBe(42);
    expect(count.options.where.promoCode).toBe('ONCE');
    expect(count.options.where.status[Op.notIn]).toEqual(['cancelled', 'refunded']);
  });

  it('lets a buyer whose only order was cancelled reuse the coupon', async () => {
    const res = await validate({ code: 'ONCE', subtotal: 100 }, { userId: 43 });

    expect(res.status).toBe(200);
    expect(res.body.discount).toBe(10);
  });

  it('does not consult orders for an anonymous preview', async () => {
    const res = await validate({ code: 'ONCE', subtotal: 100 });

    expect(res.status).toBe(200);
    expect(Order.calls.filter((c) => c.method === 'count')).toHaveLength(0);
  });
});

describe('POST /api/coupons/validate — failures', () => {
  it('hands a database failure to the error handler as a 500', async () => {
    jest.spyOn(Coupon, 'findOne').mockRejectedValueOnce(new Error('coupons table unavailable'));

    const res = await validate({ code: 'SAVE10', subtotal: 100 });

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'coupons table unavailable' });
  });
});

// ── admin CRUD ────────────────────────────────────────────────────────────

const call = (method, path, { role = 'admin', bodyData, query } = {}) => {
  let agent = request(app)[method](path).set('x-test-user', '1').set('x-test-role', role);
  if (query) agent = agent.query(query);
  if (bodyData !== undefined) agent = agent.send(bodyData);
  return agent;
};

describe('admin coupon CRUD', () => {
  it('refuses a vendor: coupons are platform-wide and have no org column', async () => {
    const res = await call('get', '/api/coupons', { role: 'vendor' });

    expect(res.status).toBe(403);
    expect(Coupon.calls).toHaveLength(0);
  });

  it('lists coupons newest-first with clamped pagination', async () => {
    const res = await call('get', '/api/coupons', { query: { page: '-2', limit: '500' } });

    expect(res.status).toBe(200);
    expect(res.body.pagination).toMatchObject({ page: 1, limit: 100 });
    expect(res.body.data).toHaveLength(11);
    const [query] = Coupon.calls.filter((c) => c.method === 'findAndCountAll').map((c) => c.options);
    expect(query.order).toEqual([['createdAt', 'DESC']]);
  });

  it.each([
    ['a missing code', { type: 'percentage', value: 10 }],
    ['an unknown type', { code: 'NEW10', type: 'bogus', value: 10 }],
    ['a negative value', { code: 'NEW10', type: 'fixed', value: -1 }],
  ])('rejects %s with 400', async (_label, bodyData) => {
    const res = await call('post', '/api/coupons', { bodyData });

    expect(res.status).toBe(400);
    expect(Coupon.calls.filter((c) => c.method === 'create')).toHaveLength(0);
  });

  it('rejects a duplicate code case-insensitively', async () => {
    const res = await call('post', '/api/coupons', {
      bodyData: { code: 'save10', type: 'percentage', value: 5 },
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('A coupon with this code already exists');
  });

  it('creates a coupon with an uppercased code and ignores server-owned fields', async () => {
    const res = await call('post', '/api/coupons', {
      bodyData: {
        code: '  new15 ',
        type: 'percentage',
        value: 15,
        id: 999,
        usageCount: 50,
      },
    });

    expect(res.status).toBe(201);
    const [created] = Coupon.calls.filter((c) => c.method === 'create').map((c) => c.options.values);
    expect(created.code).toBe('NEW15');
    expect(created).not.toHaveProperty('id');
    expect(created).not.toHaveProperty('usageCount');
    expect(res.body.data.code).toBe('NEW15');
  });

  it('404s a non-numeric id on update', async () => {
    const res = await call('put', '/api/coupons/abc', { bodyData: { value: 5 } });

    expect(res.status).toBe(404);
    expect(Coupon.calls.filter((c) => c.method === 'findByPk')).toHaveLength(0);
  });

  it.each([
    ['an unknown type', { type: 'bogus' }],
    ['a negative value', { value: -3 }],
    ['a blank code', { code: '   ' }],
  ])('rejects %s on update with 400', async (_label, bodyData) => {
    const res = await call('put', '/api/coupons/1', { bodyData });

    expect(res.status).toBe(400);
    expect(Coupon.rows.find((c) => c.id === 1).code).toBe('SAVE10');
  });

  it('updates whitelisted fields only and normalises the code', async () => {
    const res = await call('put', '/api/coupons/1', {
      bodyData: { code: 'save12', value: 12, usageCount: 0, id: 5 },
    });

    expect(res.status).toBe(200);
    const row = Coupon.rows.find((c) => c.id === 1);
    expect(row.code).toBe('SAVE12');
    expect(row.value).toBe(12);
    // usageCount is the redemption ledger: a body must not reset it.
    expect(row.usageCount).toBe(0);
    expect(Coupon.calls.filter((c) => c.method === 'update').at(-1).options.values).toEqual({
      code: 'SAVE12',
      value: 12,
    });
  });

  it('404s an unknown coupon on delete and removes a real one', async () => {
    const missing = await call('delete', '/api/coupons/999');
    expect(missing.status).toBe(404);

    const res = await call('delete', '/api/coupons/2');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Coupon deleted' });
    expect(Coupon.rows.find((c) => c.id === 2)).toBeUndefined();
  });
});
