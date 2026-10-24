/**
 * Feature tests — business routes (routes/business.routes.js).
 *
 * Runs the router on a bare Express app with the REAL auth middleware
 * (jsonwebtoken + protect + authorize) and in-memory Sequelize doubles from
 * tests/helpers/sequelizeFakes.js for Order / User / Product / Payment.
 *
 * Two fidelity shims live here (the shared helper is deliberately untouched):
 *   - `expandBetween()` — the helper's `matchColumn` cannot evaluate `Op.between`,
 *     so a test asserting "the window really filtered the rows" would pass even
 *     against an unfiltered query. Rewriting it to gte/lte makes the date
 *     filtering observable instead of decorative.
 *   - a per-model `queries` log of the ORIGINAL options object, so assertions
 *     describe exactly what the route handed to Sequelize (the tenant filter it
 *     carried — or failed to carry).
 */
import express from 'express';
import request from 'supertest';
import jwt from 'jsonwebtoken';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, afterEach, afterAll, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const SECRET = 'business-routes-test-secret';
const NOW_ISO = '2026-06-15T12:00:00.000Z';
const NOW_MS = Date.parse(NOW_ISO);

// ── frozen clock ──────────────────────────────────────────────────────────
// `jest.spyOn(Date, 'now')` does not move `new Date()`, and the route builds its
// windows from `new Date()`, so the constructor itself is pinned for this file.
const RealDate = globalThis.Date;
class FrozenDate extends RealDate {
  constructor(...args) {
    super(...(args.length ? args : [NOW_MS]));
  }
  static now() {
    return NOW_MS;
  }
}
globalThis.Date = FrozenDate;

afterAll(() => {
  globalThis.Date = RealDate;
});

// ── backing stores ────────────────────────────────────────────────────────
const userRows = [];
const orderRows = [];
const productRows = [];
const paymentRows = [];

const User = createFakeModel('User', userRows);
const Order = createFakeModel('Order', orderRows, { paranoidField: 'deleted_at' });
const Product = createFakeModel('Product', productRows, { paranoidField: 'deleted_at' });
const Payment = createFakeModel('Payment', paymentRows);

// ── query-fidelity wrapper ────────────────────────────────────────────────
function expandBetween(where) {
  if (!where || typeof where !== 'object') return where;
  const out = { ...where };
  const extra = [];
  for (const key of Reflect.ownKeys(where)) {
    const val = where[key];
    if (val && typeof val === 'object' && !Array.isArray(val) && Op.between in val) {
      const [lo, hi] = val[Op.between];
      const rest = { ...val };
      delete rest[Op.between];
      out[key] = { ...rest, [Op.gte]: lo };
      extra.push({ [key]: { [Op.lte]: hi } });
    }
  }
  if (extra.length) out[Op.and] = [...(out[Op.and] || []), ...extra];
  return out;
}

const runWhere = (options) => {
  if (!options || !options.where) return options;
  return { ...options, where: expandBetween(options.where) };
};

/** Wraps a fake model, logging the unmodified options the route passed in. */
function withQueryLog(model) {
  const queries = [];
  const wrapped = { ...model, queries, double: model };

  wrapped.findOne = (options = {}) => {
    queries.push({ method: 'findOne', options });
    return model.findOne(runWhere(options));
  };
  wrapped.findAll = (options = {}) => {
    queries.push({ method: 'findAll', options });
    return model.findAll(runWhere(options));
  };
  wrapped.findAndCountAll = (options = {}) => {
    queries.push({ method: 'findAndCountAll', options });
    return model.findAndCountAll(runWhere(options));
  };
  wrapped.count = (options = {}) => {
    queries.push({ method: 'count', options });
    return model.count(runWhere(options));
  };
  wrapped.findByPk = (id, options = {}) => {
    queries.push({ method: 'findByPk', options: { ...options, where: { ...(options.where || {}), id } } });
    return model.findByPk(id, runWhere(options));
  };
  wrapped.create = (values = {}, options = {}) => {
    queries.push({ method: 'create', options: { values, options } });
    return model.create(values, options);
  };
  wrapped.update = (values = {}, options = {}) => {
    queries.push({ method: 'update', options: { values, options } });
    return model.update(values, options);
  };
  wrapped.destroy = (options = {}) => {
    queries.push({ method: 'destroy', options });
    return model.destroy(options);
  };
  return wrapped;
}

const UserDouble = withQueryLog(User);
const OrderDouble = withQueryLog(Order);
const ProductDouble = withQueryLog(Product);
const PaymentDouble = withQueryLog(Payment);

const WRITE_METHODS = ['create', 'update', 'destroy', 'bulkCreate', 'increment', 'decrement'];
const writesOf = (wrapped) => wrapped.queries.filter((q) => WRITE_METHODS.includes(q.method));
/** Instance-level `row.update(...)` calls recorded by the fake. */
const instanceUpdates = (wrapped) =>
  wrapped.double.calls.filter((c) => c.method === 'update' && c.options && 'values' in c.options).map((c) => c.options);

// ── mocks ─────────────────────────────────────────────────────────────────
const logLines = [];
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: {
    info: (m) => logLines.push(`info:${m}`),
    warn: (m) => logLines.push(`warn:${m}`),
    error: (m) => logLines.push(`error:${m}`),
    debug: (m) => logLines.push(`debug:${m}`),
    http: (m) => logLines.push(`http:${m}`),
  },
  withRequestId: () => ({ info: () => {}, warn: () => {}, error: () => {} }),
  redact: (value) => value,
}));

jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: UserDouble }));
jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: OrderDouble }));
jest.unstable_mockModule('../../models/Product.js', () => ({ __esModule: true, default: ProductDouble }));
jest.unstable_mockModule('../../models/Payment.js', () => ({ __esModule: true, default: PaymentDouble }));

const { default: businessRoutes } = await import('../../routes/business.routes.js');

const app = express();
app.use(express.json());
app.use('/api/business', businessRoutes);
app.use((err, _req, res, _next) => {
  res.status(500).json({ success: false, error: 'Internal error', message: err.message });
});

// ── fixtures ──────────────────────────────────────────────────────────────
const d = (iso) => new Date(iso);

function seedUser(overrides = {}) {
  const id = userRows.length + 1;
  const row = {
    id,
    name: `Seed User ${id}`,
    email: `user${id}@example.test`,
    password: 'hashed-secret',
    role: 'user',
    phone: null,
    avatar: '',
    preferences: {},
    // `tenantWhere()` reads `req.user.current_org_id` (the real User model has
    // no `org_id` column), so the fixture must mirror that.
    current_org_id: null,
    createdAt: d('2026-01-01T00:00:00.000Z'),
    updatedAt: d('2026-01-01T00:00:00.000Z'),
    ...overrides,
  };
  // protect() calls dbUser.get({ plain: true })
  row.get = () => {
    const safe = { ...row };
    delete safe.password;
    return safe;
  };
  userRows.push(row);
  return row;
}

function seedOrder(overrides = {}) {
  const row = {
    id: orderRows.length + 1,
    org_id: 1,
    user_id: 1,
    orderNumber: `ORD-${orderRows.length + 1}`,
    totalPrice: 0,
    isPaid: false,
    status: 'pending',
    deleted_at: null,
    createdAt: d('2026-06-01T00:00:00.000Z'),
    updatedAt: d('2026-06-01T00:00:00.000Z'),
    ...overrides,
  };
  orderRows.push(row);
  return row;
}

function seedProduct(overrides = {}) {
  const row = {
    id: productRows.length + 1,
    org_id: 1,
    title: `Product ${productRows.length + 1}`,
    category: 'General',
    price: 10,
    isActive: true,
    deleted_at: null,
    createdAt: d('2026-01-01T00:00:00.000Z'),
    updatedAt: d('2026-01-01T00:00:00.000Z'),
    ...overrides,
  };
  productRows.push(row);
  return row;
}

function seedPayment(overrides = {}) {
  const row = {
    id: paymentRows.length + 1,
    org_id: 1,
    user_id: 1,
    order_id: 1,
    provider: 'stripe',
    amount: 0,
    status: 'succeeded',
    createdAt: d('2026-06-02T00:00:00.000Z'),
    updatedAt: d('2026-06-02T00:00:00.000Z'),
    ...overrides,
  };
  paymentRows.push(row);
  return row;
}

function token(id, secret = SECRET) {
  return `Bearer ${jwt.sign({ id }, secret, { algorithm: 'HS256', expiresIn: '15m' })}`;
}

let currentActor = null;

function call(method, path, { id = 2, query, bodyData, authHeader } = {}) {
  currentActor = id;
  let agent = request(app)[method](path);
  if (query) agent = agent.query(query);
  if (authHeader !== undefined) {
    if (authHeader) agent = agent.set('Authorization', authHeader);
  } else if (id !== null) {
    agent = agent.set('Authorization', token(id));
  }
  if (bodyData !== undefined) agent = agent.send(bodyData);
  return agent;
}

/**
 * protect() issues the request's first User lookup before the handler runs.
 * Drop it so the assertions describe what the route itself did.
 */
function handlerUserQueries() {
  const [first] = UserDouble.queries;
  const isAuthProbe =
    first && first.method === 'findByPk' && String(first.options?.where?.id) === String(currentActor);
  return isAuthProbe ? UserDouble.queries.slice(1) : UserDouble.queries;
}

const row = (id) => userRows.find((u) => u.id === id);

beforeEach(() => {
  process.env.JWT_SECRET = SECRET;

  userRows.length = 0;
  orderRows.length = 0;
  productRows.length = 0;
  paymentRows.length = 0;
  for (const m of [UserDouble, OrderDouble, ProductDouble, PaymentDouble]) {
    m.queries.length = 0;
    m.double.calls.length = 0;
  }
  logLines.length = 0;

  // users — id 2 is the org-1 vendor used as the default actor
  seedUser({ id: 1, name: 'Ada Admin', email: 'ada@example.test', role: 'admin', createdAt: d('2026-01-01T00:00:00.000Z') });
  seedUser({ id: 2, name: 'Vera Vendor', email: 'vera@example.test', role: 'vendor', current_org_id: 1, createdAt: d('2026-06-01T00:00:00.000Z') });
  seedUser({ id: 3, name: 'Gil Other', email: 'gil@other.test', role: 'vendor', current_org_id: 2, createdAt: d('2026-06-10T00:00:00.000Z') });
  seedUser({ id: 4, name: 'Pia Plain', email: 'pia@example.test', role: 'user', current_org_id: 1, createdAt: d('2026-05-01T00:00:00.000Z') });

  // orders
  seedOrder({ id: 1, org_id: 1, totalPrice: 100, isPaid: true, status: 'delivered', createdAt: d('2026-06-01T00:00:00.000Z') });
  seedOrder({ id: 2, org_id: 2, totalPrice: 250, isPaid: true, status: 'pending', createdAt: d('2026-06-05T00:00:00.000Z') });
  seedOrder({ id: 3, org_id: 1, totalPrice: 500, isPaid: false, status: 'processing', createdAt: d('2026-06-06T00:00:00.000Z') });
  seedOrder({ id: 4, org_id: 2, totalPrice: 1000, isPaid: true, status: 'delivered', createdAt: d('2026-04-01T00:00:00.000Z') });
  seedOrder({ id: 5, org_id: 1, totalPrice: 50, isPaid: true, status: 'delivered', createdAt: d('2026-05-01T00:00:00.000Z') });
  seedOrder({ id: 6, org_id: 3, totalPrice: 9999, isPaid: true, status: 'delivered', createdAt: d('2026-06-10T00:00:00.000Z'), deleted_at: d('2026-06-11T00:00:00.000Z') });

  // products
  seedProduct({ id: 1, org_id: 1, category: 'Gear', isActive: true });
  seedProduct({ id: 2, org_id: 1, category: 'Gear', isActive: true });
  seedProduct({ id: 3, org_id: 2, category: 'Games', isActive: true });
  seedProduct({ id: 4, org_id: 1, category: 'Loose', isActive: false });

  // payments
  seedPayment({ id: 1, org_id: 1, provider: 'stripe', amount: 100, status: 'succeeded', createdAt: d('2026-06-02T00:00:00.000Z') });
  seedPayment({ id: 2, org_id: 2, provider: 'razorpay', amount: 40, status: 'succeeded', createdAt: d('2026-06-03T00:00:00.000Z') });
  seedPayment({ id: 3, org_id: 1, provider: 'stripe', amount: 70, status: 'failed', createdAt: d('2026-06-04T00:00:00.000Z') });
  seedPayment({ id: 4, org_id: 1, provider: 'paypal', amount: 500, status: 'succeeded', createdAt: d('2026-03-01T00:00:00.000Z') });
});

afterEach(() => {
  delete process.env.JWT_SECRET;
});

// ── authentication / authorization ────────────────────────────────────────

describe('router.use(protect)', () => {
  it.each([
    ['get', '/api/business/analytics'],
    ['get', '/api/business/reports'],
    ['get', '/api/business/settings'],
    ['put', '/api/business/settings'],
  ])('%s %s rejects an anonymous caller', async (method, path) => {
    const res = await call(method, path, { id: null, bodyData: method === 'put' ? {} : undefined });

    expect(res.status).toBe(401);
    expect(UserDouble.queries).toHaveLength(0);
    expect(OrderDouble.queries).toHaveLength(0);
  });

  it('rejects a token signed with the wrong secret without touching the models', async () => {
    const res = await call('get', '/api/business/analytics', { authHeader: token(2, 'not-the-secret') });

    expect(res.status).toBe(401);
    expect(UserDouble.queries).toHaveLength(0);
  });

  it.each([
    ['get', '/api/business/analytics'],
    ['get', '/api/business/reports'],
    ['get', '/api/business/settings'],
    ['put', '/api/business/settings'],
  ])('%s %s rejects a plain user (authorize admin|vendor)', async (method, path) => {
    const res = await call(method, path, { id: 4, bodyData: method === 'put' ? { currency: 'EUR' } : undefined });

    expect(res.status).toBe(403);
    expect(handlerUserQueries()).toHaveLength(0);
    expect(OrderDouble.queries).toHaveLength(0);
    expect(ProductDouble.queries).toHaveLength(0);
    expect(PaymentDouble.queries).toHaveLength(0);
  });

  it('lets an admin through as well as a vendor', async () => {
    const asAdmin = await call('get', '/api/business/settings', { id: 1 });
    const asVendor = await call('get', '/api/business/settings', { id: 2 });

    expect(asAdmin.status).toBe(200);
    expect(asVendor.status).toBe(200);
  });
});

// ── analytics ─────────────────────────────────────────────────────────────

describe('GET /api/business/analytics', () => {
  it('answers the month window around the pinned clock', async () => {
    const res = await call('get', '/api/business/analytics', { id: 2 });

    expect(res.status).toBe(200);
    expect(res.body.period).toBe('month');
    expect(res.body.startDate).toBe('2026-05-16T12:00:00.000Z');
    expect(res.body.endDate).toBe(NOW_ISO);
  });

  it('sums paid revenue for the caller tenant and the previous window', async () => {
    const res = await call('get', '/api/business/analytics', { id: 2 });

    // org 1, in window & paid: #1 (100); org 2's #2 (250) must not leak in.
    // Previous window: #5 (50).
    expect(res.body.data.revenue).toEqual({ current: 100, previous: 50, changePercent: 100 });
    // unpaid #3 is excluded from revenue but counted as an order
    expect(res.body.data.orders).toMatchObject({ current: 2, previous: 1, changePercent: 100 });
    expect(res.body.data.users).toEqual({ current: 1, previous: 1, changePercent: 0 });
  });

  it('builds the revenue query with isPaid, the tenant and the date range', async () => {
    await call('get', '/api/business/analytics', { id: 2 });

    const [current, previous] = OrderDouble.queries.filter((q) => q.method === 'findOne');
    expect(current.options.where.isPaid).toBe(true);
    expect(current.options.where.org_id).toBe(1);
    expect(current.options.where.createdAt[Op.between][0]).toEqual(d('2026-05-16T12:00:00.000Z'));
    expect(current.options.where.createdAt[Op.between][1]).toEqual(d(NOW_ISO));
    expect(previous.options.where.createdAt[Op.between][0]).toEqual(d('2026-04-16T12:00:00.000Z'));
    expect(previous.options.where.createdAt[Op.between][1]).toEqual(d('2026-05-16T12:00:00.000Z'));
  });

  it('groups order status and payment provider into the shaped response arrays', async () => {
    const res = await call('get', '/api/business/analytics', { id: 2 });

    expect(res.body.data.orders.byStatus).toEqual([
      { status: 'delivered', count: 1 },
      { status: 'processing', count: 1 },
    ]);
    // succeeded, org 1 only: stripe 100 — razorpay 40 belongs to org 2
    expect(res.body.data.paymentMethods).toEqual([
      { provider: 'stripe', total: 100, count: 1 },
    ]);
  });

  it('honours the paranoid default scope: a soft-deleted order is invisible', async () => {
    const res = await call('get', '/api/business/analytics', { id: 2 });

    // order #6 (9999, delivered, in window, soft-deleted) must not appear
    expect(res.body.data.revenue.current).toBe(100);
    expect(res.body.data.orders.byStatus.find((s) => s.status === 'delivered').count).toBe(1);
  });

  it.each([
    ['week', '2026-06-08T12:00:00.000Z'],
    ['quarter', '2026-03-17T12:00:00.000Z'],
    ['year', '2025-06-15T12:00:00.000Z'],
  ])('maps period=%s to the documented day count', async (period, expectedStart) => {
    const res = await call('get', '/api/business/analytics', { id: 2, query: { period } });

    expect(res.body.period).toBe(period);
    expect(res.body.startDate).toBe(expectedStart);
  });

  it('rejects an unknown period instead of echoing it back', async () => {
    const res = await call('get', '/api/business/analytics', { id: 2, query: { period: 'decade' } });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({
      success: false,
      error: 'period must be one of week, month, quarter, year',
    });
    expect(OrderDouble.queries).toHaveLength(0);
  });

  it('honours an explicit startDate/endDate range', async () => {
    const res = await call('get', '/api/business/analytics', {
      id: 2,
      query: { startDate: '2026-04-15T00:00:00.000Z', endDate: '2026-06-06T00:00:00.000Z' },
    });

    expect(res.body.startDate).toBe('2026-04-15T00:00:00.000Z');
    expect(res.body.endDate).toBe('2026-06-06T00:00:00.000Z');
    // org 1, paid inside Apr15..Jun06: #1 100 + #5 50
    expect(res.body.data.revenue.current).toBe(150);
  });

  it('returns a null changePercent when the previous window had no revenue', async () => {
    const res = await call('get', '/api/business/analytics', {
      id: 2,
      query: { period: 'week', startDate: '2026-05-10T00:00:00.000Z' },
    });

    // current: May10..now → #1 (100); previous: May03..May10 → nothing paid
    expect(res.body.data.revenue.current).toBe(100);
    expect(res.body.data.revenue.previous).toBe(0);
    expect(res.body.data.revenue.changePercent).toBeNull();
    expect(res.body.data.users.current).toBe(1);
    expect(res.body.data.users.previous).toBe(0);
    expect(res.body.data.users.changePercent).toBeNull();
  });

  it('performs no writes and issues exactly the documented reads', async () => {
    await call('get', '/api/business/analytics', { id: 2 });

    expect(writesOf(OrderDouble)).toEqual([]);
    expect(writesOf(ProductDouble)).toEqual([]);
    expect(writesOf(PaymentDouble)).toEqual([]);
    expect(writesOf(UserDouble)).toEqual([]);
    expect(instanceUpdates(OrderDouble)).toEqual([]);
    expect(OrderDouble.queries.map((q) => q.method)).toEqual(['findOne', 'findOne', 'count', 'count', 'findAll']);
    expect(PaymentDouble.queries.map((q) => q.method)).toEqual(['findAll']);
    expect(handlerUserQueries().map((q) => q.method)).toEqual(['count', 'count']);
  });

  it('coerces a payment group whose sum is 0 instead of emitting NaN', async () => {
    seedPayment({ provider: 'paypal', amount: 0, status: 'succeeded', org_id: 1, createdAt: d('2026-06-07T00:00:00.000Z') });

    const res = await call('get', '/api/business/analytics', { id: 2 });

    expect(res.body.data.paymentMethods).toContainEqual({ provider: 'paypal', total: 0, count: 1 });
  });

  it('scopes every analytics query to the caller tenant', async () => {
    await call('get', '/api/business/analytics', { id: 2 });

    for (const query of OrderDouble.queries) expect(query.options.where.org_id).toBe(1);
    for (const query of PaymentDouble.queries) expect(query.options.where.org_id).toBe(1);
    for (const query of handlerUserQueries()) expect(query.options.where.current_org_id).toBe(1);

    // org 2's money and payment provider must not appear in org 1's answer.
    const res = await call('get', '/api/business/analytics', { id: 2 });
    expect(res.body.data.revenue.current).toBe(100);
    expect(res.body.data.paymentMethods.map((p) => p.provider)).toEqual(['stripe']);
  });

  it('gives each vendor their own numbers, not a platform-wide SUM', async () => {
    const orgOne = await call('get', '/api/business/analytics', { id: 2 });
    const orgTwo = await call('get', '/api/business/analytics', { id: 3 });
    const globalAdmin = await call('get', '/api/business/analytics', { id: 1 });

    expect(orgOne.body.data.revenue.current).toBe(100);
    expect(orgTwo.body.data.revenue.current).toBe(250);
    expect(orgOne.body.data).not.toEqual(orgTwo.body.data);
    // A platform admin has no active org, so tenantWhere() restricts them to
    // legacy (org_id IS NULL) rows rather than silently aggregating every tenant.
    expect(globalAdmin.body.data.revenue.current).toBe(0);
  });

  it.each([
    ['not-a-date'],
    ['2026-02-30'],
  ])('rejects a malformed startDate (%s) with 400', async (startDate) => {
    const res = await call('get', '/api/business/analytics', { id: 2, query: { startDate } });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(OrderDouble.queries).toHaveLength(0);
  });

  it('rejects an endDate before the startDate', async () => {
    const res = await call('get', '/api/business/analytics', {
      id: 2,
      query: { startDate: '2026-06-10', endDate: '2026-06-01' },
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('startDate must not be after endDate');
  });
});

// ── reports ───────────────────────────────────────────────────────────────

describe('GET /api/business/reports', () => {
  it('summarises revenue, average order value and counts as JSON', async () => {
    const res = await call('get', '/api/business/reports', { id: 2 });

    expect(res.status).toBe(200);
    expect(res.body.data.period).toBe('month');
    expect(res.body.data.generatedAt).toBe(NOW_ISO);
    expect(res.body.data.summary).toEqual({
      // org 1 only: #1 100 paid — org 2's 250 no longer leaks into the report
      revenue: 100,
      avgOrder: 100,
      orders: 2,
      newUsers: 1,
      activeProducts: 2,
    });
    expect(res.body.data.ordersByStatus).toEqual([
      { status: 'delivered', count: 1 },
      { status: 'processing', count: 1 },
    ]);
    expect(res.body.data.topCategories).toEqual([{ category: 'Gear', products: 2 }]);
  });

  it('counts only the tenant active products, and skips soft-deleted orders', async () => {
    const res = await call('get', '/api/business/reports', { id: 2 });

    expect(res.body.data.summary.activeProducts).toBe(2);
    expect(res.body.data.summary.revenue).toBe(100); // order #6 (9999) excluded
    expect(ProductDouble.queries.find((q) => q.method === 'count').options.where).toEqual({ org_id: 1, isActive: true });
  });

  it('queries with a single-sided gte window rather than a range', async () => {
    await call('get', '/api/business/reports', { id: 2 });

    const [revenue] = OrderDouble.queries.filter((q) => q.method === 'findOne');
    expect(revenue.options.where).toEqual({
      org_id: 1,
      isPaid: true,
      createdAt: { [Op.gte]: d('2026-05-16T12:00:00.000Z') },
    });
    expect(revenue.options.attributes.map((a) => (Array.isArray(a) ? a[1] : a))).toEqual(['revenue', 'avgOrder']);
  });

  it.each([
    ['week', 7],
    ['quarter', 90],
    ['year', 365],
  ])('period=%s shifts the report window by %i days', async (period, days) => {
    await call('get', '/api/business/reports', { id: 2, query: { period } });

    const [revenue] = OrderDouble.queries.filter((q) => q.method === 'findOne');
    const expected = new Date(NOW_MS);
    expected.setDate(expected.getDate() - days);
    expect(revenue.options.where.createdAt[Op.gte]).toEqual(expected);
  });

  it('renders CSV with the metric lines, content type and attachment header', async () => {
    const res = await call('get', '/api/business/reports', { id: 2, query: { format: 'csv' } });

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toContain('text/csv');
    expect(res.headers['content-disposition']).toBe('attachment; filename="report-month.csv"');
    expect(res.text.split('\n')).toEqual([
      'Metric,Value',
      'Report Period,month',
      `Generated At,${NOW_ISO}`,
      'Total Revenue,$100',
      'Average Order,$100',
      'Total Orders,2',
      'New Users,1',
      'Active Products,2',
    ]);
  });

  it('treats any format other than csv as JSON', async () => {
    const res = await call('get', '/api/business/reports', { id: 2, query: { format: 'XML' } });

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toContain('application/json');
    expect(res.body.data.summary.orders).toBe(2);
  });

  it('rejects an unvalidated period before it can reach the CSV body or filename', async () => {
    const evil = '=SUM(1|2)*cmd|x';
    const res = await call('get', '/api/business/reports', { id: 2, query: { format: 'csv', period: evil } });

    expect(res.status).toBe(400);
    expect(res.headers['content-disposition']).toBeUndefined();
    expect(res.text).not.toContain(evil);
    expect(OrderDouble.queries).toHaveLength(0);
  });

  it('scopes the report to the caller tenant', async () => {
    const asVendor = await call('get', '/api/business/reports', { id: 2 });
    const vendorOrderQueries = [...OrderDouble.queries];
    const vendorProductQueries = [...ProductDouble.queries];
    const vendorUserQueries = handlerUserQueries();
    OrderDouble.queries.length = 0;
    ProductDouble.queries.length = 0;
    UserDouble.queries.length = 0;

    const asOtherOrg = await call('get', '/api/business/reports', { id: 3 });

    expect(asVendor.body.data.summary.activeProducts).toBe(2);
    expect(asOtherOrg.body.data.summary.activeProducts).toBe(1);
    expect(asVendor.body.data.summary.revenue).toBe(100);
    expect(asOtherOrg.body.data.summary.revenue).toBe(250);
    expect(asVendor.body.data).not.toEqual(asOtherOrg.body.data);

    expect(vendorOrderQueries.length + vendorProductQueries.length).toBeGreaterThan(3);
    for (const query of [...vendorOrderQueries, ...vendorProductQueries]) {
      expect(query.options.where.org_id).toBe(1);
    }
    for (const query of vendorUserQueries) expect(query.options.where.current_org_id).toBe(1);
    for (const query of [...OrderDouble.queries, ...ProductDouble.queries]) {
      expect(query.options.where.org_id).toBe(2);
    }
  });

  it('performs no writes', async () => {
    await call('get', '/api/business/reports', { id: 2 });

    expect(writesOf(OrderDouble)).toEqual([]);
    expect(writesOf(ProductDouble)).toEqual([]);
    expect(writesOf(UserDouble)).toEqual([]);
  });
});

// ── settings read ─────────────────────────────────────────────────────────

describe('GET /api/business/settings', () => {
  it('falls back to hardcoded defaults for a vendor with no preferences', async () => {
    const res = await call('get', '/api/business/settings', { id: 2 });

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({
      businessName: 'Vera Vendor',
      email: 'vera@example.test',
      phone: '',
      avatar: '',
      currency: 'USD',
      timezone: 'UTC',
      language: 'en',
      theme: 'dark',
      notifications: { email: true, push: true },
      taxRate: 8,
      freeShippingMin: 100,
      shippingRate: 9.99,
    });
  });

  it('reads stored preferences when present', async () => {
    row(2).preferences = {
      businessName: 'Vera Toys',
      currency: 'EUR',
      timezone: 'Europe/Berlin',
      taxRate: 19,
      notifications: { email: false },
    };

    const res = await call('get', '/api/business/settings', { id: 2 });

    expect(res.body.data).toMatchObject({
      businessName: 'Vera Toys',
      currency: 'EUR',
      timezone: 'Europe/Berlin',
      taxRate: 19,
      notifications: { email: false },
    });
  });

  it('BUG: a legitimately stored 0 tax rate is replaced by the default 8', async () => {
    row(2).preferences = { taxRate: 0, freeShippingMin: 0, shippingRate: 0 };

    const res = await call('get', '/api/business/settings', { id: 2 });

    expect(res.body.data.taxRate).toBe(8);
    expect(res.body.data.freeShippingMin).toBe(100);
    expect(res.body.data.shippingRate).toBe(9.99);
  });

  it('reads only the caller own row, with an explicit column whitelist', async () => {
    await call('get', '/api/business/settings', { id: 2 });

    const [read] = handlerUserQueries();
    expect(read.method).toBe('findByPk');
    expect(read.options.where).toEqual({ id: 2 });
    expect(read.options.attributes).toEqual(['id', 'name', 'email', 'phone', 'avatar', 'preferences']);
  });

  it('never serialises the password hash or another tenant settings', async () => {
    row(3).preferences = { businessName: 'Globex Shop', currency: 'GBP' };

    const res = await call('get', '/api/business/settings', { id: 2 });

    expect(JSON.stringify(res.body)).not.toContain('hashed-secret');
    expect(JSON.stringify(res.body)).not.toContain('Globex Shop');
    expect(res.body.data.email).toBe('vera@example.test');
  });

  it('treats a NULL preferences column as an empty object', async () => {
    row(2).preferences = null;

    const res = await call('get', '/api/business/settings', { id: 2 });

    expect(res.status).toBe(200);
    expect(res.body.data.businessName).toBe('Vera Vendor');
    expect(res.body.data.currency).toBe('USD');
  });

  it('404s when the bearer row disappears between authentication and the read', async () => {
    const original = UserDouble.findByPk;
    let hits = 0;
    UserDouble.findByPk = (id, options) => {
      hits += 1;
      if (hits === 1) return original(id, options); // protect()
      return Promise.resolve(null);
    };
    try {
      const res = await call('get', '/api/business/settings', { id: 2 });
      expect(res.status).toBe(404);
      expect(res.body.error).toBe('User not found');
    } finally {
      UserDouble.findByPk = original;
    }
  });

  it('performs no writes', async () => {
    await call('get', '/api/business/settings', { id: 2 });

    expect(writesOf(UserDouble)).toEqual([]);
    expect(instanceUpdates(UserDouble)).toEqual([]);
  });
});

// ── settings write ────────────────────────────────────────────────────────

describe('PUT /api/business/settings', () => {
  it('merges into the existing preferences and coerces the numeric fields', async () => {
    row(2).preferences = { language: 'de', untouched: 'keep-me' };

    const res = await call('put', '/api/business/settings', {
      id: 2,
      bodyData: { businessName: 'Vera Toys', currency: 'EUR', taxRate: '19.5', shippingRate: '4.25', freeShippingMin: '25' },
    });

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('Settings updated successfully');
    expect(res.body.data).toEqual({
      language: 'de',
      untouched: 'keep-me',
      businessName: 'Vera Toys',
      currency: 'EUR',
      taxRate: 19.5,
      freeShippingMin: 25,
      shippingRate: 4.25,
    });
    expect(row(2).preferences.untouched).toBe('keep-me');
    expect(logLines.join('\n')).toContain('Business settings updated for user 2');
  });

  it('writes preferences (plus phone/avatar columns) through one instance update', async () => {
    await call('put', '/api/business/settings', { id: 2, bodyData: { theme: 'light', phone: '+49 30', avatar: 'a.png' } });

    const [update] = instanceUpdates(UserDouble);
    expect(update.where).toEqual({ id: 2 });
    expect(update.values).toEqual({
      preferences: { theme: 'light' },
      phone: '+49 30',
      avatar: 'a.png',
    });
  });

  it('deep-merges notifications without dropping sibling keys', async () => {
    row(2).preferences = { notifications: { email: true, sms: false } };

    const res = await call('put', '/api/business/settings', { id: 2, bodyData: { notifications: { email: false } } });

    expect(res.body.data.notifications).toEqual({ email: false, sms: false });
  });

  it('ignores body keys that are not part of the settings contract', async () => {
    const res = await call('put', '/api/business/settings', {
      id: 2,
      bodyData: { role: 'admin', preferences: { businessName: 'Hijack' }, isVerified: true, evil: 1 },
    });

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({});
    expect(instanceUpdates(UserDouble)[0].values).toEqual({ preferences: {} });
    expect(row(2).role).toBe('vendor');
    expect(row(2).isVerified).toBeUndefined();
  });

  it('still writes on an empty body (no-op update)', async () => {
    const res = await call('put', '/api/business/settings', { id: 2, bodyData: {} });

    expect(res.status).toBe(200);
    expect(instanceUpdates(UserDouble)).toHaveLength(1);
  });

  it('trims businessName before storing it', async () => {
    const res = await call('put', '/api/business/settings', { id: 2, bodyData: { businessName: '  Toys  ' } });

    expect(res.body.data.businessName).toBe('Toys');
  });

  it.each([
    ['businessName', { businessName: '   ' }, 'Business name cannot be empty'],
    ['currency too short', { currency: 'EU' }, 'Currency must be a 3-letter code'],
    ['currency too long', { currency: 'EURO' }, 'Currency must be a 3-letter code'],
    ['taxRate above range', { taxRate: '150' }, 'Tax rate must be 0–100'],
    ['taxRate non-numeric', { taxRate: 'free' }, 'Tax rate must be 0–100'],
    ['shippingRate negative', { shippingRate: '-1' }, 'Shipping rate must be non-negative'],
  ])('rejects %s with 400 and writes nothing', async (_label, bodyData, expected) => {
    const res = await call('put', '/api/business/settings', { id: 2, bodyData });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.msg)).toContain(expected);
    expect(instanceUpdates(UserDouble)).toEqual([]);
    expect(row(2).preferences).toEqual({});
  });

  it('reports several validation failures at once', async () => {
    const res = await call('put', '/api/business/settings', {
      id: 2,
      bodyData: { businessName: '', currency: 'X', taxRate: -5, shippingRate: -2 },
    });

    expect(res.status).toBe(400);
    expect(res.body.errors).toHaveLength(4);
  });

  it('BUG: an unvalidated freeShippingMin is parsed to NaN and stored as null', async () => {
    const res = await call('put', '/api/business/settings', { id: 2, bodyData: { freeShippingMin: 'abc' } });

    expect(res.status).toBe(200);
    expect(Number.isNaN(instanceUpdates(UserDouble)[0].values.preferences.freeShippingMin)).toBe(true);
    // JSON has no NaN, so the client silently receives null
    expect(JSON.parse(JSON.stringify(res.body.data)).freeShippingMin).toBeNull();
  });

  it('SECURITY: settings are always self-scoped, even when the body names another user', async () => {
    const res = await call('put', '/api/business/settings', {
      id: 2,
      bodyData: { userId: 3, id: 3, org_id: 2, current_org_id: 2, businessName: 'Globex Shop' },
    });

    expect(res.status).toBe(200);
    const [read] = handlerUserQueries();
    expect(read.options.where).toEqual({ id: 2 });
    expect(instanceUpdates(UserDouble)[0].where).toEqual({ id: 2 });
    expect(row(3).preferences).toEqual({});
    expect(row(3).current_org_id).toBe(2);
    expect(row(2).current_org_id).toBe(1);
    expect(res.body.data).toEqual({ businessName: 'Globex Shop' });
  });

  it('SECURITY: a second vendor reading settings gets their own row, never the first vendor', async () => {
    row(2).preferences = { businessName: 'Vera Toys', currency: 'JPY' };

    const asTwo = await call('get', '/api/business/settings', { id: 2 });
    const readsForTwo = handlerUserQueries().map((q) => q.options.where.id);
    UserDouble.queries.length = 0;

    const asThree = await call('get', '/api/business/settings', { id: 3 });
    const readsForThree = handlerUserQueries().map((q) => q.options.where.id);

    expect(readsForTwo).toEqual([2]);
    expect(readsForThree).toEqual([3]);
    expect(asTwo.body.data.businessName).toBe('Vera Toys');
    expect(asThree.body.data.businessName).toBe('Gil Other');
    expect(asThree.body.data.currency).toBe('USD');
  });

  it('accumulates across repeated PUTs', async () => {
    await call('put', '/api/business/settings', { id: 2, bodyData: { currency: 'GBP' } });
    await call('put', '/api/business/settings', { id: 2, bodyData: { timezone: 'Europe/London' } });

    expect(row(2).preferences).toEqual({ currency: 'GBP', timezone: 'Europe/London' });
  });

  it('stores language and timezone alongside the validated fields', async () => {
    const res = await call('put', '/api/business/settings', {
      id: 2,
      bodyData: { language: 'sw', timezone: 'Africa/Nairobi', currency: 'KES' },
    });

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({ language: 'sw', timezone: 'Africa/Nairobi', currency: 'KES' });
    expect(row(2).preferences.language).toBe('sw');
  });

  it('404s when the bearer row disappears between authentication and the write', async () => {
    const original = UserDouble.findByPk;
    let hits = 0;
    UserDouble.findByPk = (id, options) => {
      hits += 1;
      if (hits === 1) return original(id, options); // protect() still succeeds
      return Promise.resolve(null);
    };
    try {
      const res = await call('put', '/api/business/settings', { id: 2, bodyData: { currency: 'USD' } });

      expect(res.status).toBe(404);
      expect(res.body.error).toBe('User not found');
      expect(instanceUpdates(UserDouble)).toEqual([]);
    } finally {
      UserDouble.findByPk = original;
    }
  });

  it('401s an anonymous caller before any settings read', async () => {
    const res = await call('put', '/api/business/settings', { id: null, bodyData: { currency: 'USD' } });

    expect(res.status).toBe(401);
    expect(instanceUpdates(UserDouble)).toEqual([]);
  });
});

// ── error handling ────────────────────────────────────────────────────────

describe('error handling', () => {
  const patchOnce = (wrapped, method, makeError) => {
    const original = wrapped[method];
    wrapped[method] = async () => {
      throw makeError();
    };
    return () => {
      wrapped[method] = original;
    };
  };

  it('forwards an Order revenue failure to the error handler without leaking SQL', async () => {
    const restore = patchOnce(OrderDouble, 'findOne', () => Object.assign(new Error('connection reset'), { sql: 'SELECT SUM("totalPrice") FROM orders' }));
    try {
      const res = await call('get', '/api/business/analytics', { id: 2 });

      expect(res.status).toBe(500);
      expect(res.body.success).toBe(false);
      expect(res.body.error).toBe('Internal error');
      expect(JSON.stringify(res.body)).not.toContain('SELECT');
    } finally {
      restore();
    }
  });

  it('forwards a Payment grouping failure', async () => {
    const restore = patchOnce(PaymentDouble, 'findAll', () => new Error('deadlock detected'));
    try {
      const res = await call('get', '/api/business/analytics', { id: 2 });
      expect(res.status).toBe(500);
    } finally {
      restore();
    }
  });

  it('forwards a report count failure', async () => {
    const restore = patchOnce(OrderDouble, 'count', () => new Error('timeout'));
    try {
      const res = await call('get', '/api/business/reports', { id: 2 });
      expect(res.status).toBe(500);
    } finally {
      restore();
    }
  });

  it.each(['get', 'put'])('forwards a settings %s failure without writing', async (method) => {
    const original = UserDouble.findByPk;
    let hits = 0;
    UserDouble.findByPk = (id, options) => {
      hits += 1;
      if (hits === 1) return original(id, options); // protect() still succeeds
      return Promise.reject(new Error('relation "users" does not exist'));
    };
    try {
      const res = await call(method, '/api/business/settings', { id: 2, bodyData: { currency: 'USD' } });

      expect(res.status).toBe(500);
      expect(res.body.error).toBe('Internal error');
      expect(instanceUpdates(UserDouble)).toEqual([]);
    } finally {
      UserDouble.findByPk = original;
    }
  });

  it('a failed instance update propagates and leaves the row untouched', async () => {
    const original = UserDouble.findByPk;
    let hits = 0;
    UserDouble.findByPk = async (id, options) => {
      hits += 1;
      const instance = await original(id, options);
      // call #1 is protect()'s bearer read; only the handler's instance may fail
      if (hits === 1 || !instance) return instance;
      return { ...instance, update: () => Promise.reject(new Error('row was locked by another transaction')) };
    };
    try {
      const res = await call('put', '/api/business/settings', { id: 2, bodyData: { currency: 'USD' } });

      expect(res.status).toBe(500);
      expect(res.body.error).toBe('Internal error');
      expect(JSON.stringify(res.body)).not.toContain('SELECT');
      expect(row(2).preferences).toEqual({});
      expect(instanceUpdates(UserDouble)).toEqual([]);
    } finally {
      UserDouble.findByPk = original;
    }
  });
});
