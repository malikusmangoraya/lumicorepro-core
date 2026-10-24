/**
 * Feature tests — routes/order.routes.js
 *
 * Strategy
 *   - `protect`/`authorize` are stubbed so the caller identity is a test input.
 *   - Order / Notification / User are the in-memory Sequelize doubles from
 *     tests/helpers/sequelizeFakes.js (Order is paranoid on `deleted_at`), so
 *     every query the route sends is recorded and can be asserted.
 *   - `validateRequest` and the Zod schemas are the REAL ones, so what the route
 *     forwards is what a buyer can actually send. The 422 envelope itself is
 *     proved in tests/unit/validateRequestSchemaShape.test.js; here it is asserted
 *     that no service call happens behind it.
 *   - `services/tenantScope.service.js` is the REAL one, so the tenant filter is
 *     proved, not assumed.
 *   - orderService / recovery / queue are mocked: the routes only have to prove
 *     they forward the right actor + org and handle the service's statusCode.
 *     Price recalculation, stock locking and cancel idempotency inside the
 *     service are covered by tests/unit/orderCheckout.test.js.
 *
 * Bug ledger (all verified fixed; each entry has an enforcing test below):
 *   FIXED 2026-10-23 — middleware/validateRequest.js read `{ body, query, params }`
 *            off the Zod schema instance, but Zod keeps them on `schema.shape`, so
 *            both order.routes.js guards (129, 182) were no-ops and unvalidated
 *            input reached checkout. The helper now accepts both shapes.
 *   FIXED 2026-10-23 — order.schema.js documented `product_id` + a per-line
 *            `price`/`title`/`image`, while services/orderService.js looks the
 *            product up by `item.product` and recomputes everything else from the
 *            catalog under a row lock. The schema now states the real contract, so
 *            client price/title/image are stripped instead of forwarded.
 *   FIXED 2026-10-23 — order.routes.js let an admin write `status: 'cancelled'`
 *            without the cancelOrder() transaction (no lock, no stock restore).
 *            Ledger statuses are refused with a pointer to the real route.
 *   FIXED 2026-10-23 — `?limit=-4` only failed the `|| 10` NaN guard and was
 *            forwarded to SQL; page/limit are clamped and `status` is whitelisted.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const BUYER = { id: 5, role: 'user', email: 'buyer@example.com', current_org_id: 7 };
const ADMIN = { id: 1, role: 'admin', email: 'admin@example.com', current_org_id: 7 };

/** Identity the stubbed `protect` middleware attaches to `req.user`. */
let currentUser = { ...BUYER };

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { ...currentUser };
    if (currentUser.orgCtx) req.orgCtx = currentUser.orgCtx;
    next();
  },
  authorize: (...roles) => (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ success: false, error: 'Not authorized' });
    }
    return next();
  },
  optionalProtect: (req, _res, next) => next(),
}));

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

const createOrder = jest.fn();
const createOrderNotification = jest.fn();
const cancelOrder = jest.fn();
jest.unstable_mockModule('../../services/orderService.js', () => ({
  __esModule: true,
  createOrder: (...args) => createOrder(...args),
  createOrderNotification: (...args) => createOrderNotification(...args),
  cancelOrder: (...args) => cancelOrder(...args),
  generateOrderNumber: () => 'ORD-20260101-TEST',
  _setDeps: () => {},
  default: {},
}));

const disarmCartRecovery = jest.fn();
jest.unstable_mockModule('../../services/checkout/recovery.service.js', () => ({
  __esModule: true,
  disarmCartRecovery: (...args) => disarmCartRecovery(...args),
}));

const enqueue = jest.fn();
const QUEUES = { EMAIL: 'email', WHATSAPP: 'whatsapp', SMS: 'sms' };
jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  enqueue: (...args) => enqueue(...args),
  QUEUES,
}));

const item = (overrides = {}) => ({
  product_id: 100,
  title: 'Brass Table Lamp',
  price: 40,
  quantity: 1,
  image: 'lamp.jpg',
  ...overrides,
});

/**
 * A checkout line as a client sends it: a catalog id and a quantity. `item()` is
 * the PERSISTED line shape the service writes, which also carries the resolved
 * title/price/image — the two must not be confused.
 */
const clientLine = (overrides = {}) => ({ product: 100, quantity: 1, ...overrides });

const orderRows = () => [
  {
    id: 1,
    user_id: 5,
    org_id: 7,
    orderNumber: 'ORD-20260101-AAA',
    status: 'pending',
    items: [item()],
    itemsPrice: 40,
    taxPrice: 3.2,
    shippingPrice: 9.99,
    totalPrice: 53.19,
    paymentMethod: 'stripe',
    isDelivered: false,
    deleted_at: null,
    createdAt: new Date('2026-01-01T10:00:00Z'),
  },
  {
    id: 2,
    user_id: 5,
    org_id: 7,
    orderNumber: 'ORD-20260102-BBB',
    status: 'delivered',
    items: [item({ quantity: 3, price: 40 })],
    itemsPrice: 120,
    taxPrice: 9.6,
    shippingPrice: 0,
    totalPrice: 129.6,
    paymentMethod: 'paypal',
    isDelivered: true,
    deleted_at: null,
    createdAt: new Date('2026-01-02T10:00:00Z'),
  },
  {
    id: 3,
    user_id: 6,
    org_id: 7,
    orderNumber: 'ORD-20260103-CCC',
    status: 'processing',
    items: [item({ product_id: 200, title: 'Wall Mirror' })],
    totalPrice: 89.99,
    paymentMethod: 'cod',
    isDelivered: false,
    deleted_at: null,
    createdAt: new Date('2026-01-03T10:00:00Z'),
  },
  {
    id: 4,
    user_id: 5,
    org_id: 3,
    orderNumber: 'ORD-20260104-DDD',
    status: 'pending',
    items: [item({ product_id: 300, title: 'Other Tenant Rug' })],
    totalPrice: 210,
    paymentMethod: 'stripe',
    isDelivered: false,
    deleted_at: null,
    createdAt: new Date('2026-01-04T10:00:00Z'),
  },
  {
    id: 5,
    user_id: 5,
    org_id: null,
    orderNumber: 'LEGACY-20250101-OLD',
    status: 'pending',
    items: [item({ product_id: 400, title: 'Legacy Shelf' })],
    totalPrice: 15,
    paymentMethod: 'cod',
    isDelivered: false,
    deleted_at: null,
    createdAt: new Date('2025-01-01T10:00:00Z'),
  },
];

const Order = createFakeModel('Order', orderRows(), { paranoidField: 'deleted_at' });
const Notification = createFakeModel('Notification', []);
const User = createFakeModel('User', [
  { id: 5, name: 'Buyer', email: 'buyer@example.com' },
  { id: 6, name: 'Neighbour', email: 'n@example.com' },
]);

jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: Order }));
jest.unstable_mockModule('../../models/Notification.js', () => ({ __esModule: true, default: Notification }));
jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: User }));

const { default: orderRoutes } = await import('../../routes/order.routes.js');

const app = express();
app.use(express.json());
app.use('/api/orders', orderRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

/** Options recorded for every call to `method` on a model double. */
const callsOf = (model, method) => model.calls.filter((c) => c.method === method).map((c) => c.options);
const lastWhere = (model, method) => callsOf(model, method).at(-1)?.where;

let forcedFailure = null;
const poisable = (model, method) => {
  const original = model[method];
  model[method] = async (...args) => {
    if (forcedFailure && forcedFailure.target === `${model.name}.${method}`) {
      throw new Error(forcedFailure.message);
    }
    return original(...args);
  };
};
poisable(Order, 'findAndCountAll');
poisable(Order, 'findOne');

const shippingAddress = {
  street: '1 Main St',
  city: 'New York',
  state: 'NY',
  country: 'US',
  zipCode: '10001',
};

const orderPayload = (overrides = {}) => ({
  items: [clientLine()],
  shippingAddress,
  paymentMethod: 'stripe',
  ...overrides,
});

const createdOrder = {
  id: 50,
  user_id: 5,
  org_id: 7,
  orderNumber: 'ORD-20260105-NEW',
  status: 'pending',
  items: [item({ product_id: 100 })],
  itemsPrice: 40,
  taxPrice: 3.2,
  shippingPrice: 9.99,
  discountAmount: 0,
  totalPrice: 53.19,
};

beforeEach(() => {
  Order.rows.length = 0;
  Order.rows.push(...orderRows());
  Order.calls.length = 0;
  Notification.rows.length = 0;
  Notification.calls.length = 0;
  User.calls.length = 0;
  forcedFailure = null;
  currentUser = { ...BUYER };

  createOrder.mockResolvedValue({
    order: createdOrder,
    orderItems: [{ ...item(), product_id: 100 }],
    totalPrice: 53.19,
  });
  createOrderNotification.mockResolvedValue(true);
  disarmCartRecovery.mockResolvedValue(true);
  enqueue.mockResolvedValue({ jobId: 'job-1' });
  cancelOrder.mockResolvedValue({ order: Order.rows[0], alreadyCancelled: false });
});

// ── GET /api/orders ──────────────────────────────────────────────────────────
describe('GET /api/orders', () => {
  it('pins a non-admin caller to their own user_id inside their tenant', async () => {
    const res = await request(app).get('/api/orders');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, count: 2, total: 2, pagination: { page: 1, limit: 10, pages: 1 } });
    // The in-memory double does not re-sort rows — SQL-side ordering is asserted
    // separately from the query options, so only the id set is checked here.
    expect(res.body.data.map((o) => o.id)).toEqual([1, 2]);
    expect(lastWhere(Order, 'findAndCountAll')).toEqual({ org_id: 7, user_id: 5 });
  });

  it('lets an admin see every order of their organization but never another org', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).get('/api/orders');

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(3);
    const where = lastWhere(Order, 'findAndCountAll');
    expect(where.org_id).toBe(7);
    expect(where.user_id).toBeUndefined();
    expect(res.body.data.map((o) => o.orderNumber)).not.toContain('ORD-20260104-DDD');
  });

  it('scopes an org-less caller to legacy rows and ignores a forged x-org-id header', async () => {
    currentUser = { id: 5, role: 'user', email: 'buyer@example.com', current_org_id: null };
    const res = await request(app).get('/api/orders').set('x-org-id', '3');

    expect(res.status).toBe(200);
    const where = lastWhere(Order, 'findAndCountAll');
    expect(where.org_id).toEqual({ [Op.is]: null });
    expect(res.body.data.map((o) => o.orderNumber)).toEqual(['LEGACY-20250101-OLD']);
  });

  it('uses the verified orgCtx (requireOrg) in preference to the stored current_org_id', async () => {
    currentUser = { ...BUYER, current_org_id: 7, orgCtx: { org: { id: 3 } } };
    await request(app).get('/api/orders');

    expect(lastWhere(Order, 'findAndCountAll').org_id).toBe(3);
  });

  it('filters by status but treats "all" as no filter', async () => {
    await request(app).get('/api/orders?status=delivered');
    expect(lastWhere(Order, 'findAndCountAll').status).toBe('delivered');

    Order.calls.length = 0;
    await request(app).get('/api/orders?status=all');
    expect('status' in lastWhere(Order, 'findAndCountAll')).toBe(false);
  });

  it('pages with limit/offset and reports the page count', async () => {
    const res = await request(app).get('/api/orders?page=2&limit=1');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ total: 2, pagination: { page: 2, limit: 1, pages: 2 } });
    expect(res.body.data.map((o) => o.id)).toEqual([2]);
    expect(Order.calls.at(-1).options).toMatchObject({ limit: 1, offset: 1 });
  });

  it('falls back to page 1 / limit 10 for garbage paging values', async () => {
    const res = await request(app).get('/api/orders?page=0&limit=abc');

    expect(res.status).toBe(200);
    expect(res.body.pagination).toEqual({ page: 1, limit: 10, pages: 1 });
    expect(Order.calls.at(-1).options).toMatchObject({ limit: 10, offset: 0 });
  });

  it('clamps a negative limit instead of forwarding `LIMIT -4` to SQL', async () => {
    const res = await request(app).get('/api/orders?limit=-4&page=-2');

    expect(res.status).toBe(200);
    expect(Order.calls.at(-1).options).toMatchObject({ limit: 1, offset: 0 });
    expect(res.body.pagination).toEqual({ page: 1, limit: 1, pages: 2 });
  });

  it('caps the page size at 100 so a huge limit cannot pull the whole table', async () => {
    const res = await request(app).get('/api/orders?limit=5000');

    expect(res.body.pagination.limit).toBe(100);
    expect(Order.calls.at(-1).options).toMatchObject({ limit: 100, offset: 0 });
  });

  it('rejects a status outside the order state machine rather than filtering to nothing', async () => {
    const res = await request(app).get('/api/orders?status=teleported');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Unknown order status: teleported' });
    expect(Order.calls).toHaveLength(0);
  });

  it('joins the buyer identity fields it needs for admin listings', async () => {
    await request(app).get('/api/orders');
    const options = Order.calls.at(-1).options;
    expect(options.include).toEqual([
      { model: User, as: 'user', attributes: ['id', 'name', 'email'], required: false },
    ]);
    expect(options.order).toEqual([['createdAt', 'DESC']]);
  });

  it('hands a database failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findAndCountAll', message: 'orders table unavailable' };
    const res = await request(app).get('/api/orders');

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'orders table unavailable' });
  });
});

// ── GET /api/orders/:id ──────────────────────────────────────────────────────
describe('GET /api/orders/:id', () => {
  it('looks a numeric id up inside the caller tenant', async () => {
    const res = await request(app).get('/api/orders/1');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: expect.objectContaining({ id: 1, orderNumber: 'ORD-20260101-AAA' }) });
    expect(lastWhere(Order, 'findOne')).toEqual({ id: '1', org_id: 7 });
    expect(Order.calls.at(-1).options.include).toEqual([
      { model: User, as: 'user', attributes: ['id', 'name', 'email', 'phone', 'avatar'], required: false },
    ]);
  });

  it('accepts an orderNumber and searches by it instead of the primary key', async () => {
    const res = await request(app).get('/api/orders/ORD-20260101-AAA');

    expect(res.status).toBe(200);
    expect(lastWhere(Order, 'findOne')).toEqual({ orderNumber: 'ORD-20260101-AAA', org_id: 7 });
  });

  it('answers 404 for an unknown id', async () => {
    const res = await request(app).get('/api/orders/9999');
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
  });

  it('answers 404 (not 403) for another organization order so existence is not leaked', async () => {
    const res = await request(app).get('/api/orders/4');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
  });

  it('answers 403 for a same-tenant order owned by somebody else', async () => {
    const res = await request(app).get('/api/orders/3');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Not authorized to view this order' });
  });

  it('lets an admin read another user order in their org', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).get('/api/orders/3');

    expect(res.status).toBe(200);
    expect(res.body.data.user_id).toBe(6);
  });

  it('restricts an unscoped caller to the legacy order via the NULL tenant filter', async () => {
    currentUser = { ...BUYER, current_org_id: null };
    const res = await request(app).get('/api/orders/1');

    expect(res.status).toBe(404);
    expect(lastWhere(Order, 'findOne')).toEqual({ id: '1', org_id: { [Op.is]: null } });
  });

  it('hands a lookup failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findOne', message: 'read replica lagged' };
    const res = await request(app).get('/api/orders/1');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('read replica lagged');
  });
});

// ── POST /api/orders ─────────────────────────────────────────────────────────
describe('POST /api/orders', () => {
  it('creates the order for the caller org and returns the service order (201)', async () => {
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(201);
    expect(res.body).toEqual({ success: true, data: createdOrder });

    const [user, payload] = createOrder.mock.calls[0];
    expect(user).toEqual({ ...BUYER });
    expect(payload).toEqual({
      items: [clientLine()],
      shippingAddress,
      paymentMethod: 'stripe',
      notes: '',
      orgId: 7,
    });
  });

  it('forwards the optional fields (billing address, notes, promo code) untouched', async () => {
    await request(app)
      .post('/api/orders')
      .send(orderPayload({
        billingAddress: { ...shippingAddress, street: '2 Billing Rd' },
        notes: 'Leave at reception',
        promoCode: 'TENOFF',
      }));

    expect(createOrder.mock.calls[0][1]).toMatchObject({
      billingAddress: { ...shippingAddress, street: '2 Billing Rd' },
      notes: 'Leave at reception',
      promoCode: 'TENOFF',
      orgId: 7,
    });
  });

  it('notifies, disarms recovery and queues the confirmation email after commit', async () => {
    await request(app).post('/api/orders').send(orderPayload());

    expect(createOrderNotification).toHaveBeenCalledWith(5, {
      orderNumber: createdOrder.orderNumber,
      totalPrice: 53.19,
      orderItems: [expect.objectContaining({ product_id: 100 })],
    });
    expect(disarmCartRecovery).toHaveBeenCalledWith(5);
    expect(enqueue).toHaveBeenCalledWith(
      QUEUES.EMAIL,
      expect.objectContaining({
        to: 'buyer@example.com',
        subject: `Order Confirmed — ${createdOrder.orderNumber}`,
        html: expect.stringContaining('Total: $53.19'),
      })
    );
  });

  it('still returns 201 when the recovery disarm fails (best effort)', async () => {
    disarmCartRecovery.mockRejectedValue(new Error('redis down'));
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(201);
  });

  it('surfaces the service status code for a failed lookup (404) without a stack leak', async () => {
    createOrder.mockRejectedValue(Object.assign(new Error('Product with ID undefined not found'), { statusCode: 404 }));
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Product with ID undefined not found' });
    expect(createOrderNotification).not.toHaveBeenCalled();
  });

  it('surfaces the service status code for insufficient stock (400)', async () => {
    createOrder.mockRejectedValue(
      Object.assign(new Error("Insufficient stock for product 'Brass Table Lamp' (Available: 2)"), { statusCode: 400 })
    );
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/Insufficient stock/);
    expect(enqueue).not.toHaveBeenCalled();
  });

  it('hands an unexpected checkout failure to the error handler (500)', async () => {
    createOrder.mockRejectedValue(new Error('deadlock detected'));
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('deadlock detected');
  });

  it('turns a queue rejection into a 500 rather than a silent lost email', async () => {
    enqueue.mockRejectedValue(new Error('broker unreachable'));
    const res = await request(app).post('/api/orders').send(orderPayload());

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('broker unreachable');
  });

  it('answers 422 for an empty body and never reaches checkout', async () => {
    const res = await request(app).post('/api/orders').send({});

    expect(res.status).toBe(422);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining(['items', 'shippingAddress', 'paymentMethod'])
    );
    expect(createOrder).not.toHaveBeenCalled();
  });

  it('rejects impossible item values before the transactional checkout runs', async () => {
    const res = await request(app).post('/api/orders').send({
      items: [
        { product: 'lamp', quantity: 1e9 },
        { product: 0, quantity: -2 },
      ],
      shippingAddress: { street: '' },
      paymentMethod: 'bitcoin',
    });

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining([
        'items.0.product',
        'items.0.quantity',
        'items.1.product',
        'items.1.quantity',
        'shippingAddress.street',
        'paymentMethod',
      ])
    );
    expect(createOrder).not.toHaveBeenCalled();
  });

  it('enforces the 50-line cart cap', async () => {
    const items = Array.from({ length: 80 }, (_unused, index) => clientLine({ product: index + 1 }));
    const res = await request(app).post('/api/orders').send(orderPayload({ items }));

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('items');
    expect(createOrder).not.toHaveBeenCalled();
  });

  it('accepts only the documented line and drops everything the service must not read', async () => {
    // A client that follows the old documented field name is now rejected with a
    // path, instead of silently checking out `where.id === undefined`.
    const documented = await request(app)
      .post('/api/orders')
      .send(orderPayload({ items: [item()] }));
    expect(documented.status).toBe(422);
    expect(documented.body.details.map((d) => d.path)).toContain('items.0.product');
    expect(createOrder).not.toHaveBeenCalled();

    const smuggled = await request(app)
      .post('/api/orders')
      .send(orderPayload({ items: [{ product: 999, quantity: 1, product_id: 100, price: 0.01, stock: 9999 }] }));
    expect(smuggled.status).toBe(201);
    expect(createOrder.mock.calls.at(-1)[1].items).toEqual([{ product: 999, quantity: 1 }]);
  });

  it('forwards the caller identity and tenant rather than body-supplied ones', async () => {
    // Two gates now: the schema strips `org_id`/`user_id`/`isAdmin` off the body,
    // and the handler destructures a fixed list, so `status` cannot be smuggled in
    // either.
    currentUser = { ...BUYER, current_org_id: 3 };
    const res = await request(app)
      .post('/api/orders')
      .send(orderPayload({ org_id: 7, user_id: 999, status: 'delivered', isAdmin: true }));

    expect(res.status).toBe(201);
    const payload = createOrder.mock.calls[0][1];
    expect(payload.orgId).toBe(3);
    expect(Object.keys(payload).sort()).toEqual(
      ['billingAddress', 'items', 'notes', 'orgId', 'paymentMethod', 'promoCode', 'shippingAddress'].sort()
    );
  });

  it('never forwards a client price — the money decision belongs to the service', async () => {
    const res = await request(app)
      .post('/api/orders')
      .send(orderPayload({ items: [clientLine({ price: 0.01, title: 'Free for me' })] }));

    expect(res.status).toBe(201);
    expect(createOrder.mock.calls[0][1].items[0]).not.toHaveProperty('price');
    expect(createOrder.mock.calls[0][1].items[0]).not.toHaveProperty('title');
  });

  it('applies the schema defaults before the handler reads the body', async () => {
    await request(app).post('/api/orders').send(orderPayload());

    const payload = createOrder.mock.calls[0][1];
    expect(payload.notes).toBe('');
    expect(payload.promoCode).toBeUndefined();
    expect(payload.billingAddress).toBeUndefined();
  });
});

// ── PATCH /api/orders/:id/status ─────────────────────────────────────────────
describe('PATCH /api/orders/:id/status', () => {
  beforeEach(() => {
    currentUser = { ...ADMIN };
  });

  it('refuses a non-admin before touching the order', async () => {
    currentUser = { ...BUYER };
    const res = await request(app).patch('/api/orders/1/status').send({ status: 'shipped' });

    expect(res.status).toBe(403);
    expect(Order.calls).toHaveLength(0);
  });

  it('refuses an invented status and a non-numeric id with 422, not a write', async () => {
    const bad = await request(app).patch('/api/orders/1/status').send({ status: 'teleported' });
    expect(bad.status).toBe(422);
    expect(bad.body.details).toEqual([{ path: 'status', message: expect.stringContaining('Invalid option') }]);
    expect(Order.rows[0].status).toBe('pending');
    expect(callsOf(Order, 'update')).toHaveLength(0);
    expect(Notification.calls).toHaveLength(0);

    const badId = await request(app).patch('/api/orders/abc/status').send({ status: 'shipped' });
    expect(badId.status).toBe(422);
    expect(badId.body.details).toEqual([{ path: 'id', message: 'Order ID must be a number' }]);
    expect(lastWhere(Order, 'findOne')).toBeUndefined();
  });

  it('refuses to cancel or refund through the status column', async () => {
    // `cancelled` and `refunded` are legal enum values, but writing them here
    // skips the cancelOrder() transaction: no FOR UPDATE lock, no stock restore,
    // and a "refunded" order whose money never moved.
    const cancelled = await request(app).patch('/api/orders/1/status').send({ status: 'cancelled' });
    expect(cancelled.status).toBe(400);
    expect(cancelled.body.error).toContain('PATCH /api/orders/:id/cancel');
    expect(Order.rows[0].status).toBe('pending');
    expect(callsOf(Order, 'update')).toHaveLength(0);
    expect(cancelOrder).not.toHaveBeenCalled();

    const refunded = await request(app).patch('/api/orders/1/status').send({ status: 'refunded' });
    expect(refunded.status).toBe(400);
    expect(refunded.body.error).toContain('POST /api/payments/refund');
    expect(Order.rows[0].status).toBe('pending');
  });

  it('answers 404 for an order outside the caller tenant', async () => {
    currentUser = { ...ADMIN, current_org_id: 9 };
    const res = await request(app).patch('/api/orders/1/status').send({ status: 'shipped' });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
    expect(lastWhere(Order, 'findOne')).toEqual({ id: '1', org_id: 9 });
  });

  it('applies only the whitelisted status/tracking fields and notifies the buyer', async () => {
    const res = await request(app)
      .patch('/api/orders/1/status')
      .send({ status: 'shipped', trackingNumber: '1Z999AA1', carrier: 'UPS', totalPrice: 0.01 });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: expect.objectContaining({ id: 1, status: 'shipped' }) });

    const update = callsOf(Order, 'update').at(-1);
    expect(update.values).toEqual({ status: 'shipped', trackingNumber: '1Z999AA1', carrier: 'UPS' });
    expect(Order.rows[0].totalPrice).toBe(53.19);

    expect(callsOf(Notification, 'create').at(-1).values).toEqual({
      recipient: 5,
      type: 'order',
      title: 'Order Status Updated: SHIPPED',
      message: 'Your order #ORD-20260101-AAA is now shipped.',
      link: '/templates/ecommerce/OrdersHistory',
      metadata: { orderId: 1, status: 'shipped' },
    });
  });

  it('marks the order delivered with a delivery timestamp', async () => {
    const res = await request(app).patch('/api/orders/1/status').send({ status: 'delivered' });

    expect(res.status).toBe(200);
    const values = callsOf(Order, 'update').at(-1).values;
    expect(values.status).toBe('delivered');
    expect(values.isDelivered).toBe(true);
    expect(values.deliveredAt).toBeInstanceOf(Date);
    expect(values).not.toHaveProperty('trackingNumber');
    expect(Order.rows[0].isDelivered).toBe(true);
    expect(callsOf(Notification, 'create').at(-1).values.message).toBe('Your order #ORD-20260101-AAA is now delivered.');
  });

  it('returns the freshly updated order body', async () => {
    const res = await request(app).patch('/api/orders/3/status').send({ status: 'processing' });
    expect(res.status).toBe(200);
    expect(res.body.data.orderNumber).toBe('ORD-20260103-CCC');
  });

  it('hands a write failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findOne', message: 'status write failed' };
    const res = await request(app).patch('/api/orders/1/status').send({ status: 'shipped' });

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('status write failed');
  });
});

// ── PATCH /api/orders/:id/cancel ─────────────────────────────────────────────
describe('PATCH /api/orders/:id/cancel', () => {
  it('passes the actor and tenant to the transactional cancel and reports success', async () => {
    const res = await request(app).patch('/api/orders/1/cancel');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: true,
      message: 'Order cancelled successfully',
      data: expect.objectContaining({ id: 1 }),
    });
    expect(cancelOrder).toHaveBeenCalledWith('1', { orgId: 7, userId: 5, isAdmin: false });
  });

  it('treats a repeat cancel as a no-op with a distinct message (idempotency)', async () => {
    cancelOrder.mockResolvedValue({ order: Order.rows[0], alreadyCancelled: true });
    const res = await request(app).patch('/api/orders/1/cancel');

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('Order was already cancelled');
    expect(mockLogger.info).toHaveBeenCalledWith('Order already cancelled: ORD-20260101-AAA');
  });

  it('grants an admin the cross-owner path through isAdmin', async () => {
    currentUser = { ...ADMIN };
    await request(app).patch('/api/orders/3/cancel');

    expect(cancelOrder).toHaveBeenCalledWith('3', { orgId: 7, userId: 1, isAdmin: true });
  });

  it.each([
    [404, 'Order not found'],
    [403, 'Not authorized to cancel this order'],
    [400, 'Cannot cancel order that has already been shipped'],
  ])('maps a service %i into the same status for the client', async (statusCode, message) => {
    cancelOrder.mockRejectedValue(Object.assign(new Error(message), { statusCode }));
    const res = await request(app).patch('/api/orders/1/cancel');

    expect(res.status).toBe(statusCode);
    expect(res.body).toEqual({ success: false, error: message });
  });

  it('hands an unexpected cancel failure to the error handler (500)', async () => {
    cancelOrder.mockRejectedValue(new Error('transaction aborted'));
    const res = await request(app).patch('/api/orders/1/cancel');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('transaction aborted');
  });

  it('forwards an orderNumber so a client cannot cancel by guessing ids only', async () => {
    await request(app).patch('/api/orders/ORD-20260102-BBB/cancel');
    expect(cancelOrder).toHaveBeenCalledWith('ORD-20260102-BBB', { orgId: 7, userId: 5, isAdmin: false });
  });

  it('cancels a legacy order for an unscoped caller with the NULL org', async () => {
    currentUser = { ...BUYER, current_org_id: null };
    await request(app).patch('/api/orders/5/cancel');

    expect(cancelOrder).toHaveBeenCalledWith('5', { orgId: null, userId: 5, isAdmin: false });
  });
});

// ── DELETE /api/orders/:id ───────────────────────────────────────────────────
describe('DELETE /api/orders/:id', () => {
  beforeEach(() => {
    currentUser = { ...ADMIN };
  });

  it('refuses a non-admin', async () => {
    currentUser = { ...BUYER };
    const res = await request(app).delete('/api/orders/1');

    expect(res.status).toBe(403);
    expect(Order.calls).toHaveLength(0);
  });

  it('soft-deletes the row and keeps it out of later reads', async () => {
    const res = await request(app).delete('/api/orders/1');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Order deleted successfully' });
    expect(Order.rows).toHaveLength(5);
    expect(Order.rows[0].deleted_at).toBeInstanceOf(Date);

    const list = await request(app).get('/api/orders');
    expect(list.body.data.map((o) => o.id)).not.toContain(1);
  });

  it('answers 404 for an id in another tenant and deletes nothing', async () => {
    currentUser = { ...ADMIN, current_org_id: 9 };
    const res = await request(app).delete('/api/orders/1');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
    expect(Order.rows[0].deleted_at).toBeNull();
  });

  it('answers 404 for a row that is already soft-deleted (paranoid default scope)', async () => {
    Order.rows[0].deleted_at = new Date('2026-02-01T00:00:00Z');
    const res = await request(app).delete('/api/orders/1');

    expect(res.status).toBe(404);
  });

  it('hands a delete failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findOne', message: 'delete blocked' };
    const res = await request(app).delete('/api/orders/1');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('delete blocked');
  });
});
