/**
 * Feature tests — routes/cart.routes.js
 *
 * Server-side cart: one Cart row per user, CartItem rows priced from the
 * database, tenant-scoped product lookups, and cart-recovery arming.
 *
 * The models are the in-memory doubles from tests/helpers/sequelizeFakes.js
 * (`Cart` needs `findOrCreate`, added locally below), `protect` is stubbed so
 * the caller identity/org is a test input, and the recovery service is mocked
 * so the arm/disarm contract is asserted instead of its Redis side effects.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const BUYER = { id: 10, role: 'user', email: 'buyer@example.com' };
const OTHER = { id: 20, role: 'user', email: 'other@example.com' };

let currentUser = { ...BUYER };

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { ...currentUser };
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

const armCartRecovery = jest.fn();
const disarmCartRecovery = jest.fn();
jest.unstable_mockModule('../../services/checkout/recovery.service.js', () => ({
  __esModule: true,
  armCartRecovery,
  disarmCartRecovery,
  recoverCart: jest.fn(),
  default: { armCartRecovery, disarmCartRecovery, recoverCart: jest.fn() },
}));

const cartRows = () => [{ id: 1, user_id: 10, org_id: null }];

const cartItemRows = () => [
  {
    id: 5,
    cart_id: 1,
    product_id: 100,
    quantity: 2,
    price: '59.00',
    title: 'Nebula Lamp',
    thumbnail: 'lamp.jpg',
    selectedColor: null,
    selectedSize: null,
    createdAt: new Date('2026-01-01T00:00:00Z'),
  },
  {
    id: 6,
    cart_id: 1,
    product_id: 300,
    quantity: 1,
    price: '12.00',
    title: 'Ion Diffuser',
    thumbnail: '',
    selectedColor: 'teal',
    selectedSize: 'M',
    createdAt: new Date('2026-01-02T00:00:00Z'),
  },
  {
    id: 7,
    cart_id: 99,
    product_id: 100,
    quantity: 4,
    price: '59.00',
    title: 'Nebula Lamp',
    thumbnail: '',
    selectedColor: null,
    selectedSize: null,
    createdAt: new Date('2026-01-03T00:00:00Z'),
  },
];

const productRows = () => [
  { id: 100, title: 'Nebula Lamp', slug: 'nebula-lamp', price: '59.00', stock: 10, isActive: true, thumbnail: 'lamp.jpg', org_id: null },
  { id: 300, title: 'Ion Diffuser', slug: 'ion-diffuser', price: '12.00', stock: 5, isActive: true, thumbnail: '', org_id: null },
  { id: 400, title: 'Discontinued Thing', slug: 'old', price: '8.00', stock: 20, isActive: false, thumbnail: '', org_id: null },
  { id: 500, title: 'Rival Roaster', slug: 'rival', price: '99.00', stock: 4, isActive: true, thumbnail: '', org_id: 3 },
  { id: 600, title: 'Copper Pot', slug: 'copper-pot', price: '45.50', stock: 7, isActive: true, thumbnail: 'pot.jpg', org_id: null },
];

const Cart = createFakeModel('Cart', cartRows());
const CartItem = createFakeModel('CartItem', cartItemRows());
const Product = createFakeModel('Product', productRows());

/** Sequelize's findOrCreate contract: `[instance, created]`. */
Cart.findOrCreate = async (options = {}) => {
  Cart.calls.push({ method: 'findOrCreate', options });
  const existing = await Cart.findOne({ where: options.where || {} });
  if (existing) return [existing, false];
  const created = await Cart.create(options.defaults || options.where || {});
  return [created, true];
};

jest.unstable_mockModule('../../models/Cart.js', () => ({ __esModule: true, default: Cart }));
jest.unstable_mockModule('../../models/CartItem.js', () => ({
  __esModule: true,
  default: CartItem,
}));
jest.unstable_mockModule('../../models/Product.js', () => ({
  __esModule: true,
  default: Product,
}));

const { default: cartRoutes } = await import('../../routes/cart.routes.js');

const app = express();
app.use(express.json());
app.use('/api/cart', cartRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const callsOf = (model, method) =>
  model.calls.filter((c) => c.method === method).map((c) => c.options);
const itemRow = (id) => CartItem.rows.find((r) => r.id === id);
const otherUserCart = () =>
  Cart.rows.push({ id: 99, user_id: OTHER.id, org_id: null });

beforeEach(() => {
  Cart.rows.length = 0;
  Cart.rows.push(...cartRows());
  Cart.calls.length = 0;
  CartItem.rows.length = 0;
  CartItem.rows.push(...cartItemRows());
  CartItem.calls.length = 0;
  Product.rows.length = 0;
  Product.rows.push(...productRows());
  Product.calls.length = 0;
  currentUser = { ...BUYER };
  // jest.config.js resets mock implementations between tests — restore them.
  armCartRecovery.mockResolvedValue({ armed: true });
  disarmCartRecovery.mockResolvedValue({ disarmed: true });
});

describe('GET /api/cart', () => {
  it('reuses the caller cart and totals only its own items', async () => {
    const res = await request(app).get('/api/cart');

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.cartId).toBe(1);
    expect(res.body.data.items.map((i) => i.id)).toEqual([5, 6]);
    // 59.00 * 2 + 12.00 * 1
    expect(res.body.data.subtotal).toBe(130);
    expect(res.body.data.count).toBe(3);
    const [query] = callsOf(CartItem, 'findAll');
    expect(query.where).toEqual({ cart_id: 1 });
  });

  it('lazily creates the cart, stamped with the caller tenant', async () => {
    Cart.rows.length = 0;

    const res = await request(app).get('/api/cart');

    expect(res.status).toBe(200);
    const [options] = callsOf(Cart, 'findOrCreate');
    expect(options.where).toEqual({ user_id: BUYER.id });
    expect(options.defaults).toEqual({ user_id: BUYER.id, org_id: null });
    expect(res.body.data.items).toEqual([]);
    expect(res.body.data.subtotal).toBe(0);
  });

  it('stamps a new cart with the caller active org', async () => {
    Cart.rows.length = 0;
    currentUser = { ...BUYER, current_org_id: 7 };

    await request(app).get('/api/cart');

    expect(callsOf(Cart, 'findOrCreate')[0].defaults).toEqual({
      user_id: BUYER.id,
      org_id: 7,
    });
  });

  it('keeps one cart per user across orgs (the lookup is not org-scoped)', async () => {
    currentUser = { ...BUYER, current_org_id: 7 };

    const res = await request(app).get('/api/cart');

    expect(callsOf(Cart, 'findOrCreate')[0].where).toEqual({ user_id: BUYER.id });
    expect(res.body.data.cartId).toBe(1);
    expect(Cart.rows.filter((r) => r.user_id === BUYER.id)).toHaveLength(1);
  });

  it('joins the whitelisted product columns', async () => {
    await request(app).get('/api/cart');

    const [query] = callsOf(CartItem, 'findAll');
    expect(query.include[0]).toMatchObject({ model: Product, as: 'product', required: false });
    expect(query.include[0].attributes).toEqual([
      'id',
      'title',
      'slug',
      'price',
      'comparePrice',
      'thumbnail',
      'stock',
      'isActive',
    ]);
    expect(query.order).toEqual([['createdAt', 'ASC']]);
  });

  it('treats a missing item price as zero instead of NaN', async () => {
    CartItem.rows.push({ id: 8, cart_id: 1, product_id: 999, quantity: 3, price: null });

    const res = await request(app).get('/api/cart');

    expect(res.body.data.subtotal).toBe(130);
    expect(res.body.data.count).toBe(6);
  });
});

describe('POST /api/cart/items', () => {
  it('creates the line item priced from the database row', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 600, quantity: 2 });

    expect(res.status).toBe(201);
    const [created] = callsOf(CartItem, 'create');
    expect(created.values).toEqual({
      cart_id: 1,
      product_id: 600,
      quantity: 2,
      price: 45.5,
      title: 'Copper Pot',
      thumbnail: 'pot.jpg',
      selectedColor: null,
      selectedSize: null,
    });
    expect(armCartRecovery).toHaveBeenCalled();
    expect(mockLogger.info).toHaveBeenCalledWith(expect.stringContaining('Cart item added'));
  });

  it('defaults the quantity to 1', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 600 });

    expect(res.status).toBe(201);
    expect(callsOf(CartItem, 'create')[0].values.quantity).toBe(1);
  });

  it('snapshots the chosen variant', async () => {
    const res = await request(app)
      .post('/api/cart/items')
      .send({ productId: 100, quantity: 1, selectedColor: 'red', selectedSize: 'L' });

    expect(res.status).toBe(201);
    const { values } = callsOf(CartItem, 'create')[0];
    expect(values.selectedColor).toBe('red');
    expect(values.selectedSize).toBe('L');
  });

  it('rejects a missing product id with 400', async () => {
    const res = await request(app).post('/api/cart/items').send({ quantity: 1 });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(res.body.errors[0]).toMatchObject({ path: 'productId' });
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('rejects a non-integer or non-positive product id with 400', async () => {
    for (const productId of ['abc', 0, -3]) {
      const res = await request(app).post('/api/cart/items').send({ productId });
      expect(res.status).toBe(400);
    }
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('rejects quantities outside 1-100 (the per-line cap)', async () => {
    for (const quantity of [0, 101, 'two']) {
      const res = await request(app)
        .post('/api/cart/items')
        .send({ productId: 100, quantity });
      expect(res.status).toBe(400);
      expect(res.body.errors[0]).toMatchObject({ path: 'quantity' });
    }
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('404s for a product that is not in the caller tenant', async () => {
    currentUser = { ...BUYER, current_org_id: 7 };

    const res = await request(app).post('/api/cart/items').send({ productId: 500, quantity: 1 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Product not found or unavailable' });
    expect(callsOf(Product, 'findOne')[0].where).toMatchObject({ id: 500, org_id: 7 });
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('404s for an inactive product', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 400, quantity: 1 });

    expect(res.status).toBe(404);
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('400s when the requested quantity exceeds stock', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 300, quantity: 6 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Only 5 unit(s) in stock' });
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
  });

  it('increments the existing line rather than duplicating it', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 100, quantity: 3 });

    expect(res.status).toBe(201);
    expect(callsOf(CartItem, 'create')).toHaveLength(0);
    const [lookup] = callsOf(CartItem, 'findOne');
    expect(lookup.where).toEqual({ cart_id: 1, product_id: 100 });
    expect(itemRow(5).quantity).toBe(5);
    expect(res.body.data.quantity).toBe(5);
  });

  it('caps the increment at the remaining stock', async () => {
    const res = await request(app).post('/api/cart/items').send({ productId: 100, quantity: 9 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({
      success: false,
      error: 'Cannot add 9 more — only 8 unit(s) available',
    });
    expect(itemRow(5).quantity).toBe(2);
  });

  it('keeps different variants of one product on separate lines', async () => {
    const res = await request(app)
      .post('/api/cart/items')
      .send({ productId: 300, quantity: 1, selectedColor: 'teal', selectedSize: 'M' });

    expect(res.status).toBe(201);
    const [lookup] = callsOf(CartItem, 'findOne');
    expect(lookup.where).toEqual({
      cart_id: 1,
      product_id: 300,
      selectedColor: 'teal',
      selectedSize: 'M',
    });
    expect(itemRow(6).quantity).toBe(2);
  });

  it('reuses the existing cart row rather than creating a second one', async () => {
    await request(app).post('/api/cart/items').send({ productId: 100, quantity: 1 });

    const [options] = callsOf(Cart, 'findOrCreate');
    expect(options.where).toEqual({ user_id: BUYER.id });
    expect(Cart.rows.filter((r) => r.user_id === BUYER.id)).toHaveLength(1);
  });

  it('swallows a cart-recovery failure without failing the request', async () => {
    armCartRecovery.mockRejectedValue(new Error('redis down'));

    const res = await request(app).post('/api/cart/items').send({ productId: 100, quantity: 1 });

    expect(res.status).toBe(201);
    expect(armCartRecovery).toHaveBeenCalled();
  });
});

describe('PUT /api/cart/items/:itemId', () => {
  it('updates the quantity of the caller line', async () => {
    const res = await request(app).put('/api/cart/items/5').send({ quantity: 4 });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(itemRow(5).quantity).toBe(4);
    expect(armCartRecovery).toHaveBeenCalled();
  });

  it('rejects a quantity outside 0-100', async () => {
    for (const quantity of [-1, 101, 'lots']) {
      const res = await request(app).put('/api/cart/items/5').send({ quantity });
      expect(res.status).toBe(400);
      expect(res.body.errors[0]).toMatchObject({ path: 'quantity' });
    }
    expect(itemRow(5).quantity).toBe(2);
  });

  it('404s for a line that lives in another user cart (IDOR guard)', async () => {
    otherUserCart();

    const res = await request(app).put('/api/cart/items/7').send({ quantity: 1 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Cart item not found' });
    const [lookup] = callsOf(CartItem, 'findOne');
    expect(lookup.where).toEqual({ id: '7', cart_id: 1 });
    expect(itemRow(7).quantity).toBe(4);
  });

  it('404s for an unknown line', async () => {
    const res = await request(app).put('/api/cart/items/999').send({ quantity: 1 });

    expect(res.status).toBe(404);
  });

  it('removes the line when the quantity is 0', async () => {
    const res = await request(app).put('/api/cart/items/5').send({ quantity: 0 });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Item removed from cart', removed: true });
    expect(itemRow(5)).toBeUndefined();
    expect(disarmCartRecovery).toHaveBeenCalledWith(BUYER.id);
    expect(armCartRecovery).not.toHaveBeenCalled();
  });

  it('400s when the new quantity exceeds tenant stock', async () => {
    const res = await request(app).put('/api/cart/items/6').send({ quantity: 6 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Only 5 unit(s) in stock' });
    expect(itemRow(6).quantity).toBe(1);
  });

  /**
   * FIXED — the stock guard used to be `if (product && …)`, so a line pointing
   * at a product the caller cannot see skipped the check and grew to the cap.
   * The lookup now fails closed.
   */
  it('refuses to update a line whose product is no longer visible', async () => {
    CartItem.rows.push({ id: 9, cart_id: 1, product_id: 500, quantity: 1, price: '99.00' });

    const res = await request(app).put('/api/cart/items/9').send({ quantity: 100 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Product not found' });
    expect(itemRow(9).quantity).toBe(1);
    const [lookup] = callsOf(Product, 'findOne');
    expect(lookup.where.id).toBe(500);
    expect(lookup.where.org_id[Op.is]).toBeNull();
  });

  it('400s when the new quantity exceeds the legacy (org-less) product stock', async () => {
    const res = await request(app).put('/api/cart/items/5').send({ quantity: 11 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Only 10 unit(s) in stock' });
    expect(itemRow(5).quantity).toBe(2);
  });
});

describe('DELETE /api/cart/items/:itemId', () => {
  it('removes the caller line', async () => {
    const res = await request(app).delete('/api/cart/items/5');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Item removed from cart' });
    expect(itemRow(5)).toBeUndefined();
    expect(itemRow(6)).toBeDefined();
    expect(disarmCartRecovery).toHaveBeenCalledWith(BUYER.id);
  });

  it('404s for another user line', async () => {
    otherUserCart();

    const res = await request(app).delete('/api/cart/items/7');

    expect(res.status).toBe(404);
    expect(itemRow(7)).toBeDefined();
    expect(disarmCartRecovery).not.toHaveBeenCalled();
  });

  it('404s on a second delete', async () => {
    await request(app).delete('/api/cart/items/5');
    const res = await request(app).delete('/api/cart/items/5');

    expect(res.status).toBe(404);
  });
});

describe('DELETE /api/cart', () => {
  it('clears every line of the caller cart only', async () => {
    const res = await request(app).delete('/api/cart');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Cart cleared successfully' });
    const [options] = callsOf(CartItem, 'destroy');
    expect(options.where).toEqual({ cart_id: 1 });
    expect(itemRow(5)).toBeUndefined();
    expect(itemRow(6)).toBeUndefined();
    expect(itemRow(7)).toBeDefined();
    expect(disarmCartRecovery).toHaveBeenCalledWith(BUYER.id);
  });

  it('still answers 200 when the user has no cart yet (lazily creates, then clears)', async () => {
    Cart.rows.length = 0;

    const res = await request(app).delete('/api/cart');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Cart cleared successfully' });
    expect(Cart.rows.filter((r) => r.user_id === BUYER.id)).toHaveLength(1);
    expect(callsOf(CartItem, 'destroy')[0].where).toEqual({
      cart_id: Cart.rows.find((r) => r.user_id === BUYER.id).id,
    });
  });
});

describe('GET /api/cart/count', () => {
  it('sums the caller quantities', async () => {
    const res = await request(app).get('/api/cart/count');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, count: 3 });
    expect(Cart.whereCalls('findOne')[0].where).toEqual({ user_id: BUYER.id });
    expect(callsOf(CartItem, 'findAll')[0].where).toEqual({ cart_id: 1 });
  });

  it('returns 0 without a second query when the user has no cart', async () => {
    Cart.rows.length = 0;

    const res = await request(app).get('/api/cart/count');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, count: 0 });
    expect(callsOf(CartItem, 'findAll')).toHaveLength(0);
  });

  it('never lazily creates a cart (it is a read-only badge endpoint)', async () => {
    Cart.rows.length = 0;

    await request(app).get('/api/cart/count');

    expect(callsOf(Cart, 'findOrCreate')).toHaveLength(0);
    expect(Cart.rows.filter((r) => r.user_id === BUYER.id)).toHaveLength(0);
  });

  it('counts 0 for an empty cart', async () => {
    CartItem.rows.length = 0;

    const res = await request(app).get('/api/cart/count');

    expect(res.body).toEqual({ success: true, count: 0 });
  });
});
