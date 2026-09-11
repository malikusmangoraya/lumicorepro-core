import { describe, it, expect, beforeEach, afterAll } from '@jest/globals';
import orderService, { _setDeps } from '../../services/orderService.js';

// Plain fakes with an explicit call log — immune to Jest's restoreMocks/resetMocks
// which would otherwise wipe jest.fn implementations between tests.
const calls = { findOne: [], update: [], create: [], notification: [] };

const t = { LOCK: { UPDATE: 'UPDATE' } };

const fakeSequelize = {
  transaction: (fn) => Promise.resolve(fn(t)),
};

const fakeProduct = {
  id: 10, title: 'Headphones', price: 99.99, stock: 5,
  thumbnail: '', images: [],
  update: async (values, opts) => { calls.update.push({ values, opts }); },
};

const fakeModels = {
  Product: {
    findOne: async (opts) => { calls.findOne.push(opts); return fakeProduct; },
  },
  Order: {
    create: async (data, opts) => { calls.create.push({ data, opts }); return { id: 100, ...data }; },
  },
  Notification: {
    create: async (data) => { calls.notification.push(data); return { id: 1 }; },
  },
};

describe('Order service — transactional checkout', () => {
  beforeEach(() => {
    calls.findOne.length = 0;
    calls.update.length = 0;
    calls.create.length = 0;
    calls.notification.length = 0;
  });

  afterAll(() => {
    _setDeps({ sequelize: null, Product: null, Order: null, Notification: null });
  });

  it('creates an order and decrements stock in one transaction', async () => {
    _setDeps({ sequelize: fakeSequelize, Product: fakeModels.Product, Order: fakeModels.Order });

    const result = await orderService.createOrder(
      { id: 1 },
      {
        items: [{ product: 10, quantity: 2 }],
        shippingAddress: { city: 'KHI' },
        paymentMethod: 'stripe',
      },
    );

    expect(calls.findOne[0]).toEqual(expect.objectContaining({ lock: t.LOCK.UPDATE, transaction: t }));
    expect(calls.update[0].values).toEqual({ stock: 3 });
    expect(calls.update[0].opts).toEqual({ transaction: t });
    expect(result.orderItems[0].quantity).toBe(2);
  });

  it('throws 400 with a clear message on insufficient stock (no decrement)', async () => {
    const lowStock = { ...fakeProduct, stock: 1, update: fakeProduct.update };
    _setDeps({
      sequelize: fakeSequelize,
      Product: { findOne: async () => lowStock },
      Order: fakeModels.Order,
    });

    await expect(
      orderService.createOrder(
        { id: 1 },
        { items: [{ product: 10, quantity: 5 }], shippingAddress: {}, paymentMethod: 'stripe' },
      ),
    ).rejects.toThrow(/Insufficient stock/);

    expect(calls.update.length).toBe(0);
  });

  it('throws 404 when product not found', async () => {
    _setDeps({
      sequelize: fakeSequelize,
      Product: { findOne: async () => null },
      Order: fakeModels.Order,
    });

    await expect(
      orderService.createOrder(
        { id: 1 },
        { items: [{ product: 99, quantity: 1 }], shippingAddress: {}, paymentMethod: 'stripe' },
      ),
    ).rejects.toThrow(/not found/);
  });
});