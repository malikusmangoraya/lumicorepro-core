/**
 * Feature tests — routes/wishlist.routes.js
 *
 * Supertest against the real router with the Sequelize doubles from
 * tests/helpers/sequelizeFakes.js behind it, so every assertion about *which
 * rows a query could see* is checked against the options object that actually
 * reached the model (`Wishlist.calls`), not just against the status code.
 */
import express from 'express';
import request from 'supertest';
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

const wishlistRows = () => [
  { id: 1, user_id: 10, product_id: 100, createdAt: new Date('2026-01-01T00:00:00Z') },
  { id: 2, user_id: 10, product_id: 200, createdAt: new Date('2026-01-02T00:00:00Z') },
  { id: 3, user_id: 20, product_id: 100, createdAt: new Date('2026-01-03T00:00:00Z') },
];

const productRows = () => [
  { id: 100, title: 'Nebula Lamp', price: '59.00', stock: 5, isActive: true, org_id: null },
  { id: 200, title: 'Quiet Kettle', price: '39.50', stock: 2, isActive: true, org_id: 3 },
  { id: 300, title: 'Ion Diffuser', price: '12.00', stock: 3, isActive: true, org_id: null },
  { id: 400, title: 'Discontinued Thing', price: '8.00', stock: 0, isActive: false, org_id: null },
  { id: 500, title: 'Rival Roaster', price: '99.00', stock: 4, isActive: true, org_id: 3 },
];

const Wishlist = createFakeModel('Wishlist', wishlistRows());
const Product = createFakeModel('Product', productRows());

jest.unstable_mockModule('../../models/Wishlist.js', () => ({
  __esModule: true,
  default: Wishlist,
}));
jest.unstable_mockModule('../../models/Product.js', () => ({
  __esModule: true,
  default: Product,
}));

const { default: wishlistRoutes } = await import('../../routes/wishlist.routes.js');

const app = express();
app.use(express.json());
app.use('/api/wishlist', wishlistRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const callsOf = (model, method) =>
  model.calls.filter((c) => c.method === method).map((c) => c.options);
const entryFor = (userId, productId) =>
  Wishlist.rows.find((r) => r.user_id === userId && String(r.product_id) === String(productId));

beforeEach(() => {
  Wishlist.rows.length = 0;
  Wishlist.rows.push(...wishlistRows());
  Wishlist.calls.length = 0;
  Product.rows.length = 0;
  Product.rows.push(...productRows());
  Product.calls.length = 0;
  currentUser = { ...BUYER };
});

describe('GET /api/wishlist', () => {
  it('pins the listing to the caller and joins the product', async () => {
    const res = await request(app).get('/api/wishlist');

    expect(res.status).toBe(200);
    const [query] = callsOf(Wishlist, 'findAll');
    expect(query.where).toEqual({ user_id: BUYER.id });
    expect(query.include[0]).toMatchObject({ model: Product, as: 'product' });
    expect(query.order).toEqual([['createdAt', 'DESC']]);
    expect(res.body.success).toBe(true);
    expect(res.body.data.map((i) => i.id)).toEqual([1, 2]);
    expect(res.body.data.every((i) => i.user_id === BUYER.id)).toBe(true);
  });

  it('joins only the whitelisted product columns', async () => {
    await request(app).get('/api/wishlist');

    const [query] = callsOf(Wishlist, 'findAll');
    expect(query.include[0].attributes).toEqual([
      'id',
      'title',
      'price',
      'thumbnail',
      'images',
      'stock',
      'isActive',
    ]);
  });

  it('returns an empty list for a user with no entries', async () => {
    currentUser = { id: 555, role: 'user', email: 'none@example.com' };

    const res = await request(app).get('/api/wishlist');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: [] });
  });
});

describe('POST /api/wishlist', () => {
  it('adds a new entry for the caller and returns 201', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 300 });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.action).toBe('added');
    const [created] = callsOf(Wishlist, 'create');
    expect(created.values).toEqual({ user_id: BUYER.id, product_id: 300 });
    expect(entryFor(10, 300)).toBeDefined();
    expect(mockLogger.info).toHaveBeenCalledWith(expect.stringContaining('added to wishlist'));
  });

  it('accepts an inactive, out-of-stock product (a wishlist is not a stock claim)', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 400 });

    expect(res.status).toBe(201);
    expect(callsOf(Wishlist, 'create')[0].values.product_id).toBe(400);
  });

  it('400s when product_id is missing', async () => {
    const res = await request(app).post('/api/wishlist').send({});

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'product_id is required' });
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
  });

  it('400s on a falsy product_id (0) rather than writing an invalid FK', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 0 });

    expect(res.status).toBe(400);
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
  });

  it('404s for an unknown product and writes nothing', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 999 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Product not found' });
    expect(callsOf(Wishlist, 'findOne')).toHaveLength(0);
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
    expect(callsOf(Wishlist, 'destroy')).toHaveLength(0);
  });

  it('400s for a non-numeric product_id instead of 500ing', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 'not-a-number' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'product_id must be a positive integer' });
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
  });

  it('reports an existing entry instead of removing it', async () => {
    const res = await request(app).post('/api/wishlist').send({ product_id: 100 });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Already in wishlist',
      action: 'exists',
    });
    expect(entryFor(10, 100)).toBeDefined();
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
    expect(callsOf(Wishlist, 'destroy')).toHaveLength(0);
  });

  it('only looks up the CALLER entry — another user saved entry survives', async () => {
    expect(entryFor(20, 100)).toBeDefined();

    const res = await request(app).post('/api/wishlist').send({ product_id: 100 });

    expect(res.status).toBe(200);
    const [lookup] = callsOf(Wishlist, 'findOne');
    expect(lookup.where).toEqual({ user_id: BUYER.id, product_id: 100 });
    expect(entryFor(20, 100)).toBeDefined();
    expect(entryFor(10, 100)).toBeDefined();
  });

  /**
   * FIXED — POST used to toggle, so a double-submit or a retry of a failed
   * request deleted the entry the first request added. It is now an idempotent
   * add; removal lives only on DELETE.
   */
  it('a replayed add keeps the entry (idempotent)', async () => {
    const first = await request(app).post('/api/wishlist').send({ product_id: 300 });
    const replay = await request(app).post('/api/wishlist').send({ product_id: 300 });

    expect(first.status).toBe(201);
    expect(first.body.action).toBe('added');
    expect(replay.status).toBe(200);
    expect(replay.body.action).toBe('exists');
    expect(entryFor(10, 300)).toBeDefined();
    expect(callsOf(Wishlist, 'create')).toHaveLength(1);
  });

  /**
   * FIXED — the product lookup is tenant-scoped now, so a caller in org 7
   * cannot save a product owned by org 3.
   */
  it('refuses a product from another tenant', async () => {
    currentUser = { ...BUYER, current_org_id: 7 };

    const res = await request(app).post('/api/wishlist').send({ product_id: 500 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Product not found' });
    const [lookup] = callsOf(Product, 'findOne');
    expect(lookup.where).toEqual({ id: 500, org_id: 7 });
    expect(callsOf(Wishlist, 'create')).toHaveLength(0);
  });
});

describe('DELETE /api/wishlist/:productId', () => {
  it('removes the caller entry and reports success', async () => {
    const res = await request(app).delete('/api/wishlist/100');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Removed from wishlist' });
    const [lookup] = callsOf(Wishlist, 'findOne');
    expect(lookup.where).toEqual({ user_id: BUYER.id, product_id: 100 });
    expect(entryFor(10, 100)).toBeUndefined();
  });

  it('404s when asked to remove another user entry (no cross-user delete)', async () => {
    currentUser = { ...OTHER };

    const res = await request(app).delete('/api/wishlist/200');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Item not found in wishlist' });
    const [lookup] = callsOf(Wishlist, 'findOne');
    expect(lookup.where).toEqual({ user_id: OTHER.id, product_id: 200 });
    expect(entryFor(10, 200)).toBeDefined();
    expect(callsOf(Wishlist, 'destroy')).toHaveLength(0);
  });

  it('404s on the second delete (removal is not idempotent)', async () => {
    const first = await request(app).delete('/api/wishlist/100');
    const second = await request(app).delete('/api/wishlist/100');

    expect(first.status).toBe(200);
    expect(second.status).toBe(404);
  });

  it('404s for a product that was never wishlisted', async () => {
    const res = await request(app).delete('/api/wishlist/999');

    expect(res.status).toBe(404);
  });

  it('404s a non-numeric id without touching the database', async () => {
    const res = await request(app).delete('/api/wishlist/abc');

    expect(res.status).toBe(404);
    expect(callsOf(Wishlist, 'findOne')).toHaveLength(0);
    expect(callsOf(Wishlist, 'destroy')).toHaveLength(0);
  });
});
