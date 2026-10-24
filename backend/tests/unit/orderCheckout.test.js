/**
 * Unit tests — services/orderService.js (checkout money + stock + ownership)
 *
 * routes/order.routes.js delegates the whole transaction to this service, so the
 * owner's requirements "price recalculation from the DB rather than trusting
 * client prices", "stock checks" and "ownership on every orderId a client sends"
 * are only provable here. The service ships a dependency seam (`_setDeps`,
 * orderService.js:32), so these tests run the REAL logic against the in-memory
 * Sequelize doubles — no production file is touched.
 *
 * Bug ledger (all verified fixed 2026-10-23; each entry has an enforcing test):
 *   FIXED — middleware/validations/order.schema.js documented `product_id` while
 *           orderService.js resolves the line with `item.product`, so a payload
 *           that followed the schema reached `Product.findOne({ where: { id:
 *           undefined } })`. The schema now states the service's real contract.
 *   FIXED — orderService.js preferred `item.image` (client-supplied) over the
 *           product thumbnail, so an order line's picture was attacker controlled
 *           while its title and price were not. Imagery is catalog-only now.
 *   FIXED — an `orgId` of `undefined` (as opposed to `null`) dropped the tenant
 *           filter entirely in createOrder and cancelOrder. Both treat a missing
 *           orgId as the legacy `org_id IS NULL` scope.
 */
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel, createFakeSequelize } from '../helpers/sequelizeFakes.js';

const fakeDb = createFakeSequelize();

jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: fakeDb,
  default: async () => fakeDb,
}));

const applyCoupon = jest.fn();
const markCouponUsed = jest.fn();
jest.unstable_mockModule('../../services/couponService.js', () => ({
  __esModule: true,
  applyCoupon: (...args) => applyCoupon(...args),
  markCouponUsed: (...args) => markCouponUsed(...args),
  default: {
    applyCoupon: (...args) => applyCoupon(...args),
    markCouponUsed: (...args) => markCouponUsed(...args),
  },
}));

const bust = jest.fn();
jest.unstable_mockModule('../../services/cache/cache.service.js', () => ({
  __esModule: true,
  default: { bust: (...args) => bust(...args) },
  cache: { bust: (...args) => bust(...args) },
}));

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

const productRows = () => [
  { id: 100, org_id: 7, title: 'Brass Table Lamp', price: '40.00', stock: 5, thumbnail: 'lamp.jpg', images: null },
  { id: 101, org_id: 7, title: 'Gift Tag', price: '0.00', stock: 100, thumbnail: null, images: ['gift.jpg'] },
  { id: 200, org_id: 3, title: 'Other Tenant Rug', price: '210.00', stock: 4, thumbnail: 'rug.jpg', images: null },
  { id: 300, org_id: null, title: 'Legacy Shelf', price: '15.00', stock: 2, thumbnail: null, images: null },
];

const orderRows = () => [
  {
    id: 1,
    user_id: 5,
    org_id: 7,
    orderNumber: 'ORD-20260101-AAA',
    status: 'pending',
    items: [{ product_id: 100, quantity: 2, title: 'Brass Table Lamp', price: 40 }],
    totalPrice: 80,
    deleted_at: null,
  },
];

const Product = createFakeModel('Product', productRows());
const Order = createFakeModel('Order', orderRows(), { paranoidField: 'deleted_at' });
const Notification = createFakeModel('Notification', []);
const Coupon = createFakeModel('Coupon', []);

jest.unstable_mockModule('../../models/Product.js', () => ({ __esModule: true, default: Product }));
jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: Order }));
jest.unstable_mockModule('../../models/Notification.js', () => ({ __esModule: true, default: Notification }));
jest.unstable_mockModule('../../models/Coupon.js', () => ({ __esModule: true, default: Coupon }));

const { createOrder, cancelOrder, createOrderNotification, generateOrderNumber, _setDeps } = await import(
  '../../services/orderService.js'
);

const callsOf = (model, method) => model.calls.filter((c) => c.method === method).map((c) => c.options);
const buyer = { id: 5, email: 'buyer@example.com' };

const checkout = (items, extra = {}) =>
  createOrder(buyer, {
    items,
    shippingAddress: { street: '1 Main St', city: 'New York', country: 'US' },
    paymentMethod: 'stripe',
    orgId: 7,
    ...extra,
  });

beforeEach(() => {
  Product.rows.length = 0;
  Product.rows.push(...productRows());
  Order.rows.length = 0;
  Order.rows.push(...orderRows());
  Notification.rows.length = 0;
  for (const model of [Product, Order, Notification, Coupon]) model.calls.length = 0;

  _setDeps({ sequelize: fakeDb, Order, Product, Notification, Coupon });
  applyCoupon.mockResolvedValue({ applied: false, discount: 0, coupon: null });
  markCouponUsed.mockResolvedValue(true);
  bust.mockResolvedValue(true);
});

// ── createOrder: money comes from the database ───────────────────────────────
describe('createOrder price recalculation', () => {
  it('uses the DB price and ignores the client price', async () => {
    const { order, totalPrice } = await checkout([{ product: 100, price: 0.01, quantity: 2 }]);

    const values = callsOf(Order, 'create').at(-1).values;
    expect(values.items).toEqual([
      {
        product_id: 100,
        title: 'Brass Table Lamp',
        price: 40,
        quantity: 2,
        image: 'lamp.jpg',
        selectedColor: null,
        selectedSize: null,
      },
    ]);
    expect(values.itemsPrice).toBe(80);
    expect(values.taxPrice).toBe(6.4);
    expect(values.shippingPrice).toBe(9.99);
    expect(values.totalPrice).toBe(96.39);
    expect(totalPrice).toBe(96.39);
    expect(order.user_id).toBe(5);
  });

  it('rejects a client-forged title and keeps the catalog one', async () => {
    await checkout([{ product: 100, title: 'FREE FLAT SCREEN', price: 1, quantity: 1 }]);

    expect(callsOf(Order, 'create').at(-1).values.items[0].title).toBe('Brass Table Lamp');
  });

  it('ignores a client-supplied image and snapshots the catalog one', async () => {
    await checkout([{ product: 100, quantity: 1, image: 'https://evil.example/spam.gif' }]);

    const line = callsOf(Order, 'create').at(-1).values.items[0];
    expect(line.image).toBe('lamp.jpg');
    expect(line.image).not.toContain('evil.example');
  });

  it('falls back to the product gallery when there is no thumbnail', async () => {
    await checkout([{ product: 101, quantity: 1 }]);

    const line = callsOf(Order, 'create').at(-1).values.items[0];
    expect(line.image).toBe('gift.jpg');
    expect(line.price).toBe(0);
  });

  it('waives shipping above the threshold and always charges 8% tax', async () => {
    await checkout([{ product: 100, quantity: 3 }]);

    const values = callsOf(Order, 'create').at(-1).values;
    expect(values).toMatchObject({ itemsPrice: 120, taxPrice: 9.6, shippingPrice: 0, totalPrice: 129.6 });
  });

  it('writes the caller tenant and identity onto the order, never a client value', async () => {
    await checkout([{ product: 200, quantity: 1, org_id: 7, user_id: 999 }], { orgId: 3 });

    const values = callsOf(Order, 'create').at(-1).values;
    expect(values).toMatchObject({ org_id: 3, user_id: 5, status: 'pending' });
    expect(values.items[0].product_id).toBe(200);
  });
});

// ── createOrder: stock, locking and tenant ───────────────────────────────────
describe('createOrder stock integrity', () => {
  it('locks the product row FOR UPDATE inside the transaction before checking', async () => {
    await checkout([{ product: 100, quantity: 1 }]);

    const find = callsOf(Product, 'findOne').at(-1);
    expect(find.lock).toBe('UPDATE');
    expect(find.transaction).toBe(fakeDb._transaction);
    const stockUpdate = callsOf(Product, 'update').at(-1);
    expect(stockUpdate.values).toEqual({ stock: 4 });
    expect(stockUpdate.options).toEqual({ transaction: fakeDb._transaction });
  });

  it('refuses an oversell with 400 and changes nothing', async () => {
    await expect(checkout([{ product: 100, quantity: 6 }])).rejects.toMatchObject({
      statusCode: 400,
      message: "Insufficient stock for product 'Brass Table Lamp' (Available: 5)",
    });

    expect(Product.rows[0].stock).toBe(5);
    expect(callsOf(Order, 'create')).toHaveLength(0);
  });

  it('compares stock numerically when the driver returns it as a string', async () => {
    // PostgreSQL INTEGER columns can arrive as strings through some drivers and
    // raw queries; `'8' < 10` is true, `'8' < '10'` is false (string order).
    Product.rows[0].stock = '8';

    await expect(checkout([{ product: 100, quantity: 10 }])).rejects.toMatchObject({
      statusCode: 400,
      message: "Insufficient stock for product 'Brass Table Lamp' (Available: 8)",
    });
    expect(Product.rows[0].stock).toBe('8');
  });

  it('rolls the whole cart back on the first bad line by throwing before create', async () => {
    await expect(
      checkout([
        { product: 100, quantity: 1 },
        { product: 200, quantity: 1 },
      ])
    ).rejects.toMatchObject({ statusCode: 404, message: 'Product with ID 200 not found' });

    // The first line already decremented; only the surrounding transaction can
    // undo it — asserted at the SQL layer, so record the mutation this far.
    expect(Product.rows[0].stock).toBe(4);
    expect(callsOf(Order, 'create')).toHaveLength(0);
  });

  it('answers 404 for a product that belongs to another organization', async () => {
    await expect(checkout([{ product: 200, quantity: 1 }], { orgId: 7 })).rejects.toMatchObject({ statusCode: 404 });

    expect(callsOf(Product, 'findOne').at(-1).where).toEqual({ id: 200, org_id: 7 });
    expect(callsOf(Product, 'update')).toHaveLength(0);
  });

  it('matches legacy NULL-org products for an unscoped caller', async () => {
    await checkout([{ product: 300, quantity: 1 }], { orgId: null });

    expect(callsOf(Product, 'findOne').at(-1).where).toEqual({ id: 300, org_id: { [Op.is]: null } });
    expect(callsOf(Order, 'create').at(-1).values.org_id).toBeNull();
  });

  it('treats an omitted orgId as the legacy scope, never as every tenant', async () => {
    await expect(checkout([{ product: 200, quantity: 1 }], { orgId: undefined })).rejects.toMatchObject({
      statusCode: 404,
      message: 'Product with ID 200 not found',
    });

    // Another org's product is invisible without an explicit scope.
    expect(callsOf(Product, 'findOne').at(-1).where).toEqual({ id: 200, org_id: { [Op.is]: null } });
    expect(callsOf(Order, 'create')).toHaveLength(0);
  });

  it('refuses a line that does not name a catalog product', async () => {
    const error = await checkout([
      { product_id: 100, title: 'Brass Table Lamp', price: 40, quantity: 1 },
    ]).catch((err) => err);

    // The lookup never happens at all: under Sequelize an `id: undefined`
    // where-value is dropped, which would turn the locked read into "any product
    // of this tenant" and decrement the wrong stock counter.
    expect(error).toMatchObject({ statusCode: 400, message: 'Every order line must reference a catalog product id' });
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
    expect(callsOf(Order, 'create')).toHaveLength(0);
    expect(Product.rows.map((r) => r.stock)).toEqual([5, 100, 4, 2]);
  });

  it('refuses a line without a whole positive quantity', async () => {
    for (const quantity of [0, -2, 1.5, 'many']) {
      const error = await checkout([{ product: 100, quantity }]).catch((err) => err);
      expect(error).toMatchObject({ statusCode: 400, message: 'Every order line needs a whole quantity of at least 1' });
    }
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
    expect(Product.rows.map((r) => r.stock)).toEqual([5, 100, 4, 2]);
  });

  it('accepts a numeric-string quantity and snapshots it as a number', async () => {
    await checkout([{ product: 100, quantity: '2' }]);

    expect(callsOf(Order, 'create').at(-1).values.items[0].quantity).toBe(2);
    expect(Product.rows[0].stock).toBe(3);
  });

  it('validates the currency before touching inventory', async () => {
    await expect(checkout([{ product: 100, quantity: 1 }], { currency: 'EU' })).rejects.toMatchObject({
      statusCode: 400,
      message: 'Unsupported currency: EU',
    });
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
  });

  it('normalises a lowercase currency and stamps it on the order', async () => {
    await checkout([{ product: 100, quantity: 1 }], { currency: ' eur ' });

    expect(callsOf(Order, 'create').at(-1).values.currency).toBe('EUR');
  });
});

// ── createOrder: promo codes ─────────────────────────────────────────────────
describe('createOrder promo handling', () => {
  it('subtracts the discount and marks the coupon used after create', async () => {
    applyCoupon.mockResolvedValue({ applied: true, discount: 10, coupon: { id: 9, code: 'tenoff' } });

    await checkout([{ product: 100, quantity: 1 }], { promoCode: 'tenoff' });

    // The buyer travels to applyCoupon: per-user limits are only checkable there.
    expect(applyCoupon).toHaveBeenCalledWith('tenoff', 40, { userId: 5 });
    const values = callsOf(Order, 'create').at(-1).values;
    expect(values).toMatchObject({ discountAmount: 10, promoCode: 'TENOFF', totalPrice: 43.19 });
    // Consumption runs inside the order transaction, so a rollback gives the
    // redemption back instead of burning a coupon on an order that does not exist.
    expect(markCouponUsed).toHaveBeenCalledWith(
      { id: 9, code: 'tenoff' },
      { transaction: expect.anything() }
    );
  });

  it('aborts checkout when the coupon unit was already taken by a rival order', async () => {
    applyCoupon.mockResolvedValue({ applied: true, discount: 10, coupon: { id: 9, code: 'tenoff' } });
    markCouponUsed.mockResolvedValue(false);

    await expect(checkout([{ product: 100, quantity: 1 }], { promoCode: 'tenoff' })).rejects.toMatchObject({
      statusCode: 400,
      message: 'This coupon has just reached its usage limit',
    });
    expect(markCouponUsed).toHaveBeenCalledTimes(1);
  });

  it('rejects an unusable code with 400 and creates no order', async () => {
    applyCoupon.mockResolvedValue({ applied: false, discount: 0, coupon: null, error: 'Coupon expired' });

    await expect(checkout([{ product: 100, quantity: 1 }], { promoCode: 'OLD' })).rejects.toMatchObject({
      statusCode: 400,
      message: 'Coupon expired',
    });
    expect(callsOf(Order, 'create')).toHaveLength(0);
    expect(markCouponUsed).not.toHaveBeenCalled();
  });

  it('leaves discountAmount at 0 and promoCode null when no code is applied', async () => {
    applyCoupon.mockResolvedValue({ applied: false, discount: 0, coupon: null });

    await checkout([{ product: 100, quantity: 1 }]);

    expect(callsOf(Order, 'create').at(-1).values).toMatchObject({ discountAmount: 0, promoCode: null });
  });
});

// ── notification ─────────────────────────────────────────────────────────────
describe('createOrderNotification', () => {
  it('records the buyer notification and busts the dashboard cache', async () => {
    await expect(
      createOrderNotification(5, { orderNumber: 'ORD-20260101-AAA', totalPrice: 96.39, orderItems: [{}] })
    ).resolves.toBe(true);

    expect(callsOf(Notification, 'create').at(-1).values).toEqual({
      recipient: 5,
      type: 'order',
      title: 'Order Placed Successfully',
      message: 'Your order #ORD-20260101-AAA for $96.39 has been placed.',
      link: '/templates/ecommerce/OrdersHistory',
      metadata: { orderNumber: 'ORD-20260101-AAA' },
    });
    expect(bust).toHaveBeenCalledWith('dashboard');
  });
});

// ── cancelOrder: ownership, tenancy, idempotency ─────────────────────────────
describe('cancelOrder', () => {
  it('restores every line under a row lock on the first cancel', async () => {
    const { order, alreadyCancelled } = await cancelOrder('1', { orgId: 7, userId: 5 });

    expect(alreadyCancelled).toBe(false);
    expect(order.status).toBe('cancelled');
    expect(callsOf(Product, 'findOne').at(-1)).toMatchObject({
      where: { id: 100 },
      lock: 'UPDATE',
      transaction: fakeDb._transaction,
    });
    expect(callsOf(Product, 'update').at(-1).values).toEqual({ stock: 7 });
    expect(Product.rows[0].stock).toBe(7);
  });

  it('pins the lookup to the caller tenant before checking ownership', async () => {
    await expect(cancelOrder('1', { orgId: 3, userId: 5 })).rejects.toMatchObject({
      statusCode: 404,
      message: 'Order not found',
    });

    expect(callsOf(Order, 'findOne').at(-1).where).toEqual({ id: '1', org_id: 3 });
    expect(Order.rows[0].status).toBe('pending');
  });

  it('refuses a cross-owner cancel with 403 and restores nothing', async () => {
    Order.rows[0].user_id = 6;

    await expect(cancelOrder('1', { orgId: 7, userId: 5 })).rejects.toMatchObject({
      statusCode: 403,
      message: 'Not authorized to cancel this order',
    });
    expect(callsOf(Product, 'update')).toHaveLength(0);
  });

  it('lets an admin cancel another owner order in the same org', async () => {
    Order.rows[0].user_id = 6;
    const { order } = await cancelOrder('1', { orgId: 7, userId: 1, isAdmin: true });

    expect(order.status).toBe('cancelled');
  });

  it('treats a repeat cancel as a no-op so stock is never restored twice', async () => {
    Order.rows[0].status = 'cancelled';

    const { alreadyCancelled } = await cancelOrder('1', { orgId: 7, userId: 5 });

    expect(alreadyCancelled).toBe(true);
    expect(callsOf(Order, 'update')).toHaveLength(0);
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
    expect(Product.rows[0].stock).toBe(5);
  });

  it('also treats a refunded order as terminal', async () => {
    Order.rows[0].status = 'refunded';

    await expect(cancelOrder('1', { orgId: 7, userId: 5 })).resolves.toMatchObject({ alreadyCancelled: true });
  });

  it.each([
    ['shipped', 400],
    ['delivered', 400],
  ])('refuses a %s order with %i — cancellation windows are enforced', async (status) => {
    Order.rows[0].status = status;

    await expect(cancelOrder('1', { orgId: 7, userId: 5 })).rejects.toMatchObject({
      statusCode: 400,
      message: `Cannot cancel order that has already been ${status}`,
    });
    expect(Order.rows[0].status).toBe(status);
  });

  it('resolves an orderNumber instead of a numeric id', async () => {
    await cancelOrder('ORD-20260101-AAA', { orgId: 7, userId: 5 });

    expect(callsOf(Order, 'findOne').at(-1).where).toEqual({
      orderNumber: 'ORD-20260101-AAA',
      org_id: 7,
    });
  });

  it('uses the NULL tenant scope for a legacy caller', async () => {
    await cancelOrder('1', { orgId: null, userId: 5 }).catch(() => {});

    expect(callsOf(Order, 'findOne').at(-1).where).toEqual({ id: '1', org_id: { [Op.is]: null } });
  });

  it('scopes a cancel to the legacy org when no orgId is given', async () => {
    // Org 7's order is unreachable without naming that tenant: a missing orgId is
    // the legacy scope, not "search every tenant".
    await expect(cancelOrder('1', { userId: 5 })).rejects.toMatchObject({
      statusCode: 404,
      message: 'Order not found',
    });
    expect(callsOf(Order, 'findOne').at(-1).where).toEqual({ id: '1', org_id: { [Op.is]: null } });
  });

  it('tolerates a line whose product no longer exists and skips zero quantities', async () => {
    Order.rows[0].items = [
      { product_id: 999, quantity: 3 },
      { product_id: 100, quantity: 0 },
      { quantity: 5 },
      { product_id: 100 },
    ];

    const { order } = await cancelOrder('1', { orgId: 7, userId: 5 });

    expect(order.status).toBe('cancelled');
    expect(callsOf(Product, 'findOne').map((o) => o.where.id)).toEqual([999]);
    expect(Product.rows[0].stock).toBe(5);
  });

  it('locks the order row for the whole transaction', async () => {
    await cancelOrder('1', { orgId: 7, userId: 5 });

    const find = callsOf(Order, 'findOne').at(-1);
    expect(find.lock).toBe('UPDATE');
    expect(find.transaction).toBe(fakeDb._transaction);
  });

  it('rejects an empty or whitespace order id with 404 instead of matching everything', async () => {
    await expect(cancelOrder('   ', { orgId: 7, userId: 5 })).rejects.toMatchObject({ statusCode: 404 });
    expect(callsOf(Order, 'findOne').at(-1).where.orderNumber).toBe('');
  });
});

describe('generateOrderNumber', () => {
  it('is date-prefixed and unique enough for a receipt id', () => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const first = generateOrderNumber();
    expect(first).toMatch(new RegExp(`^ORD-${today}-[0-9A-Z]{5}$`));
    expect(new Set([first, generateOrderNumber(), generateOrderNumber()]).size).toBeGreaterThan(1);
  });
});
