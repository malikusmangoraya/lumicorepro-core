/**
 * Feature tests — routes/search.routes.js
 *
 * Search is public, so the tenant scope comes from either the signed-in user's
 * active org or the storefront `x-org-id` header (services/tenantScope.service.js).
 * These tests assert the where clause each query carried and that the cache key
 * is tenant-specific — a shared key served one org's results to another.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  optionalProtect: (req, _res, next) => {
    const id = req.headers['x-test-user'];
    if (id) req.user = { id: Number(id), role: 'user', current_org_id: 3 };
    next();
  },
  protect: (_req, _res, next) => next(),
  authorize: () => (_req, _res, next) => next(),
}));

jest.unstable_mockModule('../../services/cache/cache.service.js', () => ({
  __esModule: true,
  default: {
    get: jest.fn(async () => null),
    set: jest.fn(async () => undefined),
    TTL: { SEARCH: 600 },
  },
}));

const productRows = () => [
  { id: 1, title: 'Wireless Headphones', slug: 'wireless-headphones', description: 'Bluetooth', category: 'Audio', price: '99.00', comparePrice: null, thumbnail: 'a.jpg', rating: 4.5, stock: 5, isActive: true, org_id: null },
  { id: 2, title: 'Wireless Keyboard', slug: 'wireless-keyboard', description: 'Mechanical', category: 'Gear', price: '79.00', comparePrice: null, thumbnail: 'b.jpg', rating: 4.2, stock: 8, isActive: true, org_id: 7 },
  { id: 3, title: 'Wired Mouse', slug: 'wired-mouse', description: 'USB', category: 'Gear', price: '19.00', comparePrice: null, thumbnail: 'c.jpg', rating: 4.0, stock: 2, isActive: true, org_id: 7 },
  { id: 4, title: 'Wireless Router', slug: 'wireless-router', description: 'Wi-Fi 6', category: 'Network', price: '120.00', comparePrice: null, thumbnail: 'd.jpg', rating: 4.1, stock: 3, isActive: true, org_id: 3 },
];

const userRows = () => [
  { id: 1, name: 'Ada Wireless', email: 'ada@org3.test', role: 'user', avatar: '', current_org_id: 3 },
  { id: 2, name: 'Bob Wireless', email: 'bob@org7.test', role: 'user', avatar: '', current_org_id: 7 },
];

const Product = createFakeModel('Product', productRows());
const User = createFakeModel('User', userRows());

jest.unstable_mockModule('../../models/Product.js', () => ({ __esModule: true, default: Product }));
jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: User }));

const { default: searchRoutes } = await import('../../routes/search.routes.js');
const { default: cache } = await import('../../services/cache/cache.service.js');

const app = express();
app.use(express.json());
app.use('/api/search', searchRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const search = (query = {}, headers = {}) => {
  let agent = request(app).get('/api/search');
  if (headers.orgId) agent = agent.set('x-org-id', String(headers.orgId));
  if (headers.userId) agent = agent.set('x-test-user', String(headers.userId));
  return agent.query(query);
};

const productCalls = () => Product.calls.filter((c) => c.method === 'findAll').map((c) => c.options);

beforeEach(() => {
  Product.rows.length = 0;
  Product.rows.push(...productRows());
  Product.calls.length = 0;
  User.rows.length = 0;
  User.rows.push(...userRows());
  User.calls.length = 0;
  cache.get.mockClear();
  cache.get.mockResolvedValue(null);
  cache.set.mockClear();
});

describe('GET /api/search — validation and caching', () => {
  it('400s without a query string', async () => {
    const res = await search({});

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Query string q is required' });
    expect(Product.calls).toHaveLength(0);
  });

  it('returns a cache hit with meta.cached and touches no model', async () => {
    cache.get.mockResolvedValueOnce({ products: [{ id: 1 }] });

    const res = await search({ q: 'wireless' });

    expect(res.body.meta).toEqual({ cached: true });
    expect(Product.calls).toHaveLength(0);
  });

  it('keeps the tenant in the cache key', async () => {
    await search({ q: 'wireless', type: 'products' }, { orgId: 7 });

    const [namespace, key] = cache.set.mock.calls[0];
    expect(namespace).toBe('search');
    expect(key).toContain('org:7');
    expect(key).toContain('u0');
  });

  it('clamps the limit to 1..50', async () => {
    await search({ q: 'a', type: 'products', limit: '999' });
    expect(productCalls()[0].limit).toBe(50);

    Product.calls.length = 0;
    await search({ q: 'a', type: 'products', limit: '-4' });
    expect(productCalls()[0].limit).toBe(1);

    Product.calls.length = 0;
    await search({ q: 'a', type: 'products', limit: 'lots' });
    expect(productCalls()[0].limit).toBe(10);
  });
});

describe('GET /api/search — tenant scope', () => {
  it('scopes an anonymous storefront search to the x-org-id tenant', async () => {
    const res = await search({ q: 'wireless' }, { orgId: 7 });

    expect(res.status).toBe(200);
    const [products] = productCalls();
    expect(products.where.org_id).toBe(7);
    expect(res.body.data.products.map((p) => p.id)).toEqual([2]);
    // Anonymous callers never get the user index.
    expect(User.calls).toHaveLength(0);
    expect(res.body.data.users).toBeUndefined();
  });

  it('falls back to legacy (org_id IS NULL) products when no tenant is known', async () => {
    const res = await search({ q: 'wireless', type: 'products' });

    expect(productCalls()[0].where.org_id).toEqual({ [Op.is]: null });
    expect(res.body.data.products.map((p) => p.id)).toEqual([1]);
  });

  it('uses the signed-in user active org and scopes user search too', async () => {
    const res = await search({ q: 'wireless' }, { userId: 1 });

    const [products] = productCalls();
    expect(products.where.org_id).toBe(3);
    expect(res.body.data.products.map((p) => p.id)).toEqual([4]);

    const [users] = User.calls.map((c) => c.options);
    expect(users.where.current_org_id).toBe(3);
    expect(users.where[Op.or]).toHaveLength(2);
    expect(res.body.data.users.map((u) => u.id)).toEqual([1]);
  });
});

describe('GET /api/search — shaping', () => {
  it('applies a category filter alongside the text match', async () => {
    const res = await search({ q: 'wireless', type: 'products', category: 'Gear' }, { orgId: 7 });

    const [products] = productCalls();
    expect(products.where.category).toEqual({ [Op.iLike]: 'Gear' });
    expect(res.body.data.products.map((p) => p.id)).toEqual([2]);
  });

  it('returns distinct categories for type=categories', async () => {
    const res = await search({ q: 'ea', type: 'categories' }, { orgId: 7 });

    expect(res.body.data.categories.sort()).toEqual(['Gear']);
    expect(productCalls()).toHaveLength(1);
  });

  it('treats a user-index failure as an empty user list, not a 500', async () => {
    jest.spyOn(User, 'findAll').mockRejectedValueOnce(new Error('users table unavailable'));

    const res = await search({ q: 'wireless' }, { userId: 1 });

    expect(res.status).toBe(200);
    expect(res.body.data.users).toBeUndefined();
    expect(res.body.data.products).toHaveLength(1);
  });
});

describe('GET /api/search/autocomplete', () => {
  it('returns nothing for a one-character query', async () => {
    const res = await request(app).get('/api/search/autocomplete?q=a');

    expect(res.body).toEqual({ success: true, data: [] });
    expect(Product.calls).toHaveLength(0);
  });

  it('returns at most six product suggestions within the tenant', async () => {
    const res = await request(app).get('/api/search/autocomplete?q=wi').set('x-org-id', '7');

    expect(res.status).toBe(200);
    const [query] = productCalls();
    expect(query.where.org_id).toBe(7);
    expect(query.limit).toBe(6);
    expect(res.body.data.map((s) => s.type)).toEqual(['product', 'product']);
    // org 7 owns "Wireless Keyboard" and "Wired Mouse" — both match `wi`.
    expect(res.body.data.map((s) => s.id)).toEqual([2, 3]);
  });
});

describe('GET /api/search/trending', () => {
  it('returns curated keywords plus up to eight tenant categories', async () => {
    const res = await request(app).get('/api/search/trending').set('x-org-id', '7');

    expect(res.status).toBe(200);
    expect(res.body.data.keywords.length).toBeGreaterThan(3);
    expect(res.body.data.categories).toEqual(['Gear']);
    expect(productCalls()[0].where.org_id).toBe(7);
  });
});
