/**
 * Feature tests — routes/restaurant.routes.js
 *
 * IMPORTANT — the wiring this file had to substitute:
 * restaurant.routes.js puts the *bare* `validateRequest` function into its
 * middleware chains (lines 45, 131, 169, 269, 299, 351, 419, 440, 464). That
 * export is a factory: `validateRequest({body,query,params}) => middleware`, so
 * calling it as middleware returns a function and never calls `next()`. Every one
 * of those nine routes therefore hangs until the socket times out in production.
 * This is proven (not assumed) in
 * tests/unit/restaurantValidationWiring.test.js — run it against the real
 * router before reading the substitutions below.
 *
 * To get the handler bodies under test anyway, this file mocks ONLY that one
 * middleware with the terminal the express-validator chains above it were always
 * meant to reach: `validationResult(req)` → the canonical
 * `utils/response.js` 422 envelope (the real helper, imported, not reimplemented)
 * → otherwise `next()`. Everything else — the validator chains themselves,
 * tenantScope, the Sequelize doubles — is exercised for real.
 *
 * Fake-model limitations this file works around (never by editing the shared
 * helper, which other suites share):
 *   - `Op.contains` is not evaluated by the double, so tag/metadata filters are
 *     asserted from the recorded query shape.
 *   - `sequelize.fn('DISTINCT', …)` is answered by a local adapter (categories).
 *   - `Review.findOrCreate` and `Order.sum` do not exist on the double, so local
 *     adapters implement the documented Sequelize contract.
 *
 * Bug ledger (fixed items keep their line as a regression note; assertions prove
 * the CURRENT behaviour, never the old bug):
 *   FIXED 2026-10-23 — restaurant.routes.js used bare `validateRequest` (a
 *            factory) in 9 of 14 chains, so those endpoints hung until the client
 *            timed out. They now use `checkValidation`
 *            (middleware/validationResult.js); the 422 and happy-path tests below
 *            run against the real middleware.
 *   FIXED 2026-10-23 — the food order was built as `{productId, qty}` while
 *            services/orderService.js reads `item.product` / `item.quantity`, so
 *            every restaurant line resolved to `where: { id: undefined }` with an
 *            undefined quantity and a NaN total. The route now translates the cart
 *            vocabulary into `{product, quantity}` (numbers), sends a payment
 *            method and, for a delivery, a validated address.
 *   FIXED 2026-10-23 — the review POST product lookup and the public review list
 *            carried no tenant filter, so a caller could rate another org's menu
 *            item and read its reviews. Both are scoped now.
 *   FIXED 2026-10-23 — GET /admin/stats filtered on `orgId`, which is not a
 *            column (PostgreSQL aborts; the double matched nothing), so every
 *            dashboard figure read 0. It uses tenantWhere() now.
 *   FIXED 2026-10-23 — stacked dietary filters overwrote one shared `where.tags`
 *            key and raw price strings reached SQL. Tags combine into one
 *            `Op.contains` and prices are cast.
 *   FIXED 2026-10-23 — a reservation was inserted with no availability, capacity,
 *            past-date or clock check, and it wrote `title`/`description`, which
 *            are not columns on models/Booking.js (Sequelize dropped them) into a
 *            table whose `doctor_id`/`reason`/`patientInfo` were NOT NULL: no food
 *            booking could be stored at all. The route now seats parties on a
 *            timezone-anchored `startAt` inside a transaction that counts the
 *            overlapping seatings against RESTAURANT_TABLE_CAPACITY, and
 *            migration 008 gave `bookings` the `org_id`/`startAt`/`metadata`
 *            columns the route already assumed.
 *   FIXED 2026-10-23 — the status docstring advertised preparing/ready, which the
 *            shared order enum does not have. The restaurant kitchen runs on the
 *            pipeline's own words (`processing` = in the kitchen, `shipped` = out
 *            for delivery), the same labels src/pages/restaurant/AdminDashboard.jsx
 *            renders, and the route now rejects anything else plus the two ledger
 *            statuses that must go through the cancel/refund endpoints.
 *   FIXED 2026-10-23 — nothing stamped an order as restaurant business, so
 *            GET /restaurant/orders listed the caller's store orders and a
 *            restaurant admin could rewrite them. `orders.source` (migration 008)
 *            is written by createOrder and filtered by every food route.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { validationResult } from 'express-validator';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel, createFakeSequelize, matchesWhere } from '../helpers/sequelizeFakes.js';
import responseHelpers from '../../utils/response.js';

const BUYER = { id: 5, role: 'user', email: 'diner@example.com', current_org_id: 7 };
const ADMIN = { id: 1, role: 'admin', email: 'chef@example.com', current_org_id: 7 };

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

/** The terminal the production chains were written to reach. */
const validateTerminal = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return responseHelpers.sendValidationError(
      res,
      errors.array().map((e) => ({ path: e.path, message: e.msg }))
    );
  }
  return next();
};

jest.unstable_mockModule('../../middleware/validateRequest.js', () => ({
  __esModule: true,
  validateRequest: validateTerminal,
  default: validateTerminal,
}));

const fakeDb = {
  ...createFakeSequelize(),
  fn: (fn, ...args) => ({ fn, args }),
  col: (column) => ({ col: column }),
};
jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: fakeDb,
  default: async () => fakeDb,
}));

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

const enqueue = jest.fn();
const QUEUES = { EMAIL: 'email', WHATSAPP: 'whatsapp', SMS: 'sms' };
jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  enqueue: (...args) => enqueue(...args),
  QUEUES,
}));

const createOrder = jest.fn();
jest.unstable_mockModule('../../services/orderService.js', () => ({
  __esModule: true,
  createOrder: (...args) => createOrder(...args),
  default: {},
}));

const productRows = () => [
  {
    id: 1,
    org_id: 7,
    title: 'Truffle Fries',
    description: 'Sea salt & rosemary',
    price: '12.50',
    category: 'Sides',
    tags: ['vegetarian'],
    isFeatured: true,
    isActive: true,
    stock: 50,
    rating: 4.2,
    reviewCount: 5,
    thumbnail: 'fries.jpg',
    deleted_at: null,
    createdAt: new Date('2026-01-01T09:00:00Z'),
  },
  {
    id: 2,
    org_id: 7,
    title: 'Ribeye Steak',
    description: '300g, pepper crust',
    price: '34.00',
    category: 'Mains',
    tags: [],
    isFeatured: false,
    isActive: true,
    stock: 12,
    rating: 4.8,
    reviewCount: 2,
    thumbnail: 'steak.jpg',
    deleted_at: null,
    createdAt: new Date('2026-01-02T09:00:00Z'),
  },
  {
    id: 3,
    org_id: 7,
    title: 'Kale Salad',
    description: 'No dressing',
    price: '9.00',
    category: 'Sides',
    tags: ['vegan', 'gluten-free'],
    isFeatured: false,
    isActive: false,
    stock: 30,
    rating: 0,
    reviewCount: 0,
    thumbnail: null,
    deleted_at: null,
    createdAt: new Date('2026-01-03T09:00:00Z'),
  },
  {
    id: 4,
    org_id: 7,
    title: 'House Lemonade',
    description: 'Sweet',
    price: '5.00',
    category: 'Drinks',
    tags: [],
    isFeatured: false,
    isActive: true,
    stock: 9,
    rating: 3,
    reviewCount: 1,
    thumbnail: 'lemonade.jpg',
    deleted_at: new Date('2026-02-01T09:00:00Z'),
    createdAt: new Date('2026-01-04T09:00:00Z'),
  },
  {
    id: 5,
    org_id: 3,
    title: 'Other Org Pizza',
    description: 'Foreign tenant',
    price: '20.00',
    category: 'Mains',
    tags: ['vegetarian'],
    isFeatured: true,
    isActive: true,
    stock: 8,
    rating: 5,
    reviewCount: 4,
    thumbnail: 'pizza.jpg',
    deleted_at: null,
    createdAt: new Date('2026-01-05T09:00:00Z'),
  },
];

const Product = createFakeModel('Product', productRows(), { paranoidField: 'deleted_at' });

const reviewRows = () => [
  { id: 10, product_id: 2, user_id: 8, org_id: 7, rating: 4, comment: 'Solid cook', createdAt: new Date('2026-01-05T09:00:00Z') },
  { id: 11, product_id: 2, user_id: 9, org_id: 7, rating: 5, comment: 'Best on the menu', createdAt: new Date('2026-01-06T09:00:00Z') },
  { id: 12, product_id: 5, user_id: 8, org_id: 3, rating: 3, comment: 'Foreign review', createdAt: new Date('2026-01-07T09:00:00Z') },
];

const Review = createFakeModel('Review', reviewRows());
const Booking = createFakeModel('Booking', []);
const User = createFakeModel('User', [
  { id: 5, name: 'Diner', email: 'diner@example.com' },
  { id: 8, name: 'Regular', email: 'r@example.com' },
]);

const orderRows = () => [
  {
    id: 1,
    user_id: 5,
    org_id: 7,
    orderNumber: 'ORD-20260201-AAA',
    status: 'pending',
    source: 'restaurant',
    items: [{ product_id: 2, quantity: 1, price: 34 }],
    totalPrice: 46.5,
    paymentMethod: 'cod',
    deleted_at: null,
    createdAt: new Date('2026-02-01T09:00:00Z'),
  },
  {
    id: 2,
    user_id: 5,
    org_id: 7,
    orderNumber: 'ORD-20260202-BBB',
    status: 'delivered',
    source: 'restaurant',
    items: [{ product_id: 1, quantity: 2, price: 12.5 }],
    totalPrice: 34.1,
    paymentMethod: 'stripe',
    deleted_at: null,
    createdAt: new Date('2026-02-02T09:00:00Z'),
  },
  {
    id: 3,
    user_id: 6,
    org_id: 7,
    orderNumber: 'ORD-20260203-CCC',
    status: 'processing',
    // The same tenant sells hardware through the store vertical: this row is the
    // control that every restaurant query must filter out.
    source: 'ecommerce',
    items: [{ product_id: 1, quantity: 1, price: 12.5 }],
    totalPrice: 22.49,
    paymentMethod: 'paypal',
    deleted_at: null,
    createdAt: new Date('2026-02-03T09:00:00Z'),
  },
  {
    id: 4,
    user_id: 5,
    org_id: 3,
    orderNumber: 'ORD-20260204-DDD',
    status: 'pending',
    source: 'restaurant',
    items: [{ product_id: 5, quantity: 1, price: 20 }],
    totalPrice: 29.99,
    paymentMethod: 'cod',
    deleted_at: null,
    createdAt: new Date('2026-02-04T09:00:00Z'),
  },
];

const Order = createFakeModel('Order', orderRows(), { paranoidField: 'deleted_at' });

jest.unstable_mockModule('../../models/Product.js', () => ({ __esModule: true, default: Product }));
jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: Order }));
jest.unstable_mockModule('../../models/Review.js', () => ({ __esModule: true, default: Review }));
jest.unstable_mockModule('../../models/Booking.js', () => ({ __esModule: true, default: Booking }));
jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: User }));

/* ── Local adapters for contract points the shared double omits ───────────── */

/** `sequelize.fn('DISTINCT', col)` → one projected row per distinct value. */
const baseProductFindAll = Product.findAll;
Product.findAll = async (options = {}) => {
  const pair = Array.isArray(options.attributes) ? options.attributes.find((a) => Array.isArray(a)) : null;
  if (!pair || pair[0]?.fn !== 'DISTINCT') return baseProductFindAll(options);

  Product.calls.push({ method: 'findAll', options });
  const column = pair[0].args[0].col;
  const alias = pair[1];
  const visible = Product.rows.filter((r) => r.deleted_at === null || r.deleted_at === undefined);
  const matched = visible.filter((r) => matchesWhere(r, options.where));
  const unique = [...new Set(matched.map((r) => r[column]))];
  return unique.map((value) => ({ [alias]: value }));
};

/** `Model.sum(column, options)` → numeric sum or null for an empty set. */
Order.sum = async (column, options = {}) => {
  Order.calls.push({ method: 'sum', options });
  const matched = Order.rows.filter(
    (r) => (r.deleted_at === null || r.deleted_at === undefined) && matchesWhere(r, options.where)
  );
  if (matched.length === 0) return null;
  return matched.reduce((total, row) => total + Number(row[column] || 0), 0);
};

/** `Model.findOrCreate({where, defaults})` → `[instance, created]`. */
let nextReviewId = 100;
Review.findOrCreate = async ({ where = {}, defaults = {} } = {}) => {
  if (forcedFailure && forcedFailure.target === 'Review.findOrCreate') throw new Error(forcedFailure.message);
  Review.calls.push({ method: 'findOrCreate', options: { where, defaults } });
  const existing = Review.rows.find((r) => matchesWhere(r, where));
  if (existing) return [await Review.findByPk(existing.id), false];

  const row = { id: nextReviewId, ...where, ...defaults, createdAt: new Date('2026-03-01T09:00:00Z') };
  nextReviewId += 1;
  Review.rows.push(row);
  return [await Review.findByPk(row.id), true];
};

const { default: restaurantRoutes } = await import('../../routes/restaurant.routes.js');

const app = express();
app.use(express.json());
app.use('/api/restaurant', restaurantRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const callsOf = (model, method) => model.calls.filter((c) => c.method === method).map((c) => c.options);
const lastWhere = (model, method) => callsOf(model, method).at(-1)?.where;

let forcedFailure = null;
const poisable = (model, method) => {
  const original = model[method];
  model[method] = async (...args) => {
    if (forcedFailure && forcedFailure.target === `${model.name}.${method}`) throw new Error(forcedFailure.message);
    return original(...args);
  };
};
poisable(Product, 'findAndCountAll');
poisable(Product, 'findAll');
poisable(Product, 'findOne');
poisable(Product, 'findByPk');
poisable(Product, 'count');
poisable(Product, 'create');
poisable(Order, 'findAndCountAll');
poisable(Order, 'findOne');
poisable(Order, 'count');
poisable(Booking, 'create');
poisable(Booking, 'findAll');
poisable(Booking, 'count');
poisable(Review, 'findAll');

const menuIds = (body) => body.data.map((row) => row.id);

/**
 * Menu/category/featured/item/review reads are PUBLIC (no `protect`), so their
 * tenant comes from the storefront `x-org-id` header — the documented third
 * precedence in services/tenantScope.service.js. `currentUser` only affects
 * routes that actually run `protect`.
 */
const shop = (url) => request(app).get(url).set('x-org-id', '7');

beforeEach(() => {
  Product.rows.length = 0;
  Product.rows.push(...productRows());
  Order.rows.length = 0;
  Order.rows.push(...orderRows());
  Review.rows.length = 0;
  Review.rows.push(...reviewRows());
  Booking.rows.length = 0;
  nextReviewId = 100;
  for (const model of [Product, Order, Review, Booking, User]) model.calls.length = 0;

  forcedFailure = null;
  currentUser = { ...BUYER };
  enqueue.mockResolvedValue({ jobId: 'job-1' });
  createOrder.mockResolvedValue({
    order: { id: 77, orderNumber: 'ORD-20260303-NEW', status: 'pending' },
    totalPrice: 46.5,
  });
});

// ── GET /api/restaurant/menu ─────────────────────────────────────────────────
describe('GET /api/restaurant/menu', () => {
  it('lists active, not-soft-deleted items of the caller tenant only', async () => {
    const res = await shop('/api/restaurant/menu');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, count: 2, total: 2, pagination: { page: 1, limit: 12, pages: 1 } });
    expect(menuIds(res.body)).toEqual([1, 2]);
    expect(lastWhere(Product, 'findAndCountAll')).toEqual({
      isActive: true,
      deleted_at: null,
      org_id: 7,
    });
    expect(Product.calls.at(-1).options.order).toEqual([['isFeatured', 'DESC'], ['createdAt', 'DESC']]);
  });

  it('restricts an org-less storefront caller to legacy rows', async () => {
    currentUser = { ...BUYER, current_org_id: null };
    await request(app).get('/api/restaurant/menu');

    expect(lastWhere(Product, 'findAndCountAll').org_id).toEqual({ [Op.is]: null });
  });

  it('filters by category with a case-insensitive match', async () => {
    const res = await shop('/api/restaurant/menu?category=mains');

    expect(menuIds(res.body)).toEqual([2]);
    expect(lastWhere(Product, 'findAndCountAll').category).toEqual({ [Op.iLike]: 'mains' });
  });

  it('treats category=all as no category filter', async () => {
    await request(app).get('/api/restaurant/menu?category=all');
    expect('category' in lastWhere(Product, 'findAndCountAll')).toBe(false);
  });

  it('searches title and description with an OR of LIKE patterns', async () => {
    const res = await shop('/api/restaurant/menu?search=steak');

    expect(menuIds(res.body)).toEqual([2]);
    expect(lastWhere(Product, 'findAndCountAll')[Op.or]).toEqual([
      { title: { [Op.iLike]: '%steak%' } },
      { description: { [Op.iLike]: '%steak%' } },
    ]);
  });

  it('combines stacked dietary tags into one filter and casts prices for SQL', async () => {
    // `Op.contains` with every selected tag: an item must carry all of them.
    await shop('/api/restaurant/menu?vegetarian=true&vegan=true');
    expect(lastWhere(Product, 'findAndCountAll').tags).toEqual({
      [Op.contains]: ['vegetarian', 'vegan'],
    });

    // The comparison values are numbers, not query strings.
    await shop('/api/restaurant/menu?minPrice=10&maxPrice=20');
    expect(lastWhere(Product, 'findAndCountAll').price).toEqual({ [Op.gte]: 10, [Op.lte]: 20 });
  });

  it('pages and clamps to the documented defaults', async () => {
    const res = await shop('/api/restaurant/menu?page=2&limit=1');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ total: 2, pagination: { page: 2, limit: 1, pages: 2 } });
    expect(Product.calls.at(-1).options).toMatchObject({ limit: 1, offset: 1 });
  });

  it.each([
    ['limit above the 50 cap', '/api/restaurant/menu?limit=51', 'limit'],
    ['page below 1', '/api/restaurant/menu?page=0', 'page'],
    ['non-boolean vegetarian', '/api/restaurant/menu?vegetarian=yes', 'vegetarian'],
    ['negative minPrice', '/api/restaurant/menu?minPrice=-1', 'minPrice'],
  ])('rejects %s with the canonical 422 envelope', async (_label, url, path) => {
    const res = await request(app).get(url);

    expect(res.status).toBe(422);
    expect(res.body).toMatchObject({
      success: false,
      status: 422,
      message: 'Validation failed',
      code: 'VALIDATION_ERROR',
      data: null,
    });
    expect(typeof res.body.timestamp).toBe('string');
    expect(res.body.details.map((d) => d.path)).toContain(path);
    expect(callsOf(Product, 'findAndCountAll')).toHaveLength(0);
  });

  it('hands a database failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Product.findAndCountAll', message: 'menu read failed' };
    const res = await request(app).get('/api/restaurant/menu');

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'menu read failed' });
  });
});

// ── GET /api/restaurant/categories ───────────────────────────────────────────
describe('GET /api/restaurant/categories', () => {
  it('returns the distinct active categories of the caller tenant, sorted', async () => {
    const res = await shop('/api/restaurant/categories');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: ['Mains', 'Sides'] });
    const options = Product.calls.at(-1).options;
    expect(options.where).toEqual({
      isActive: true,
      org_id: 7,
      category: { [Op.ne]: null },
    });
    expect(options.raw).toBe(true);
  });

  it('drops null categories and never leaks another org', async () => {
    Product.rows[1].category = null;
    const res = await shop('/api/restaurant/categories');

    expect(res.body.data).toEqual(['Sides']);
  });

  it('hands a failing aggregate to the error handler (500)', async () => {
    forcedFailure = { target: 'Product.findAll', message: 'distinct read failed' };
    const res = await request(app).get('/api/restaurant/categories');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('distinct read failed');
  });
});

// ── GET /api/restaurant/featured ─────────────────────────────────────────────
describe('GET /api/restaurant/featured', () => {
  it('shows only the caller tenant featured items, newest first, capped at 8', async () => {
    const res = await shop('/api/restaurant/featured');

    expect(res.status).toBe(200);
    expect(menuIds(res.body)).toEqual([1]);
    expect(lastWhere(Product, 'findAll')).toEqual({ isActive: true, isFeatured: true, org_id: 7 });
    expect(Product.calls.at(-1).options).toMatchObject({ limit: 8, order: [['createdAt', 'DESC']] });
  });

  it('answers an empty list for a tenant with nothing featured', async () => {
    Product.rows[0].isFeatured = false;
    const res = await request(app).get('/api/restaurant/featured');

    expect(res.body).toEqual({ success: true, data: [] });
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Product.findAll', message: 'featured read failed' };
    const res = await request(app).get('/api/restaurant/featured');
    expect(res.status).toBe(500);
  });
});

// ── GET /api/restaurant/menu/:id ─────────────────────────────────────────────
describe('GET /api/restaurant/menu/:id', () => {
  it('returns the item with its reviews attached', async () => {
    const res = await shop('/api/restaurant/menu/2');

    expect(res.status).toBe(200);
    expect(res.body.data.title).toBe('Ribeye Steak');
    expect(lastWhere(Product, 'findOne')).toEqual({ id: '2', isActive: true, org_id: 7 });
    expect(Product.calls.at(-1).options.include).toEqual([
      { model: Review, as: 'reviews', order: [['createdAt', 'DESC']], limit: 10, required: false },
    ]);
  });

  it('answers 404 for a retired item', async () => {
    const res = await shop('/api/restaurant/menu/3');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Menu item not found' });
  });

  it('answers 404 for another organization item and a soft-deleted one', async () => {
    expect((await shop('/api/restaurant/menu/5')).status).toBe(404);
    expect((await shop('/api/restaurant/menu/4')).status).toBe(404);
    expect(lastWhere(Product, 'findOne')).toEqual({ id: '4', isActive: true, org_id: 7 });
  });

  it('rejects a non-numeric id with 422 before querying', async () => {
    const res = await request(app).get('/api/restaurant/menu/abc');

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('id');
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Product.findOne', message: 'item read failed' };
    const res = await request(app).get('/api/restaurant/menu/2');
    expect(res.status).toBe(500);
  });
});

// ── POST /api/restaurant/orders ──────────────────────────────────────────────
describe('POST /api/restaurant/orders', () => {
  it('creates the food order for the caller org and returns a receipt payload', async () => {
    const res = await request(app)
      .post('/api/restaurant/orders')
      .send({ items: [{ productId: 2, qty: 1, price: 0.01 }], notes: 'Medium rare' });

    expect(res.status).toBe(201);
    expect(res.body).toEqual({
      success: true,
      data: { orderNumber: 'ORD-20260303-NEW', id: 77, status: 'pending', totalPrice: 46.5 },
    });

    const [user, payload] = createOrder.mock.calls[0];
    expect(user).toEqual({ ...BUYER });
    expect(payload.orgId).toBe(7);
    expect(payload.notes).toBe('Medium rare');
  });

  it('translates the cart vocabulary into the shape createOrder reads', async () => {
    // src/pages/restaurant/Cart.jsx:47 posts `{productId, qty}`; services
    // /orderService.js:69,76 requires `{product, quantity}` as integers, and a
    // client price must never reach the order snapshot.
    await request(app)
      .post('/api/restaurant/orders')
      .send({ items: [{ productId: '2', qty: '3', price: 0.01, title: 'Free Ribeye' }] });

    const payload = createOrder.mock.calls[0][1];
    expect(payload.items).toEqual([{ product: 2, quantity: 3 }]);
    expect(payload.source).toBe('restaurant');
    expect(payload.items[0]).not.toHaveProperty('price');
    expect(payload.items[0]).not.toHaveProperty('productId');
  });

  it('defaults a food order to pay-at-collection with nothing to ship', async () => {
    const res = await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 1 }] });

    expect(res.status).toBe(201);
    const payload = createOrder.mock.calls[0][1];
    expect(payload.paymentMethod).toBe('cod');
    // Pickup and dine-in ship nothing, so `orders.shippingAddress` stays null
    // instead of carrying a fake street (migration 008 made the column nullable).
    expect(payload.shippingAddress).toBeNull();
    expect(payload.orgId).toBe(7);
    expect(payload.source).toBe('restaurant');
  });

  it('records the delivery address and projects out everything else', async () => {
    const res = await request(app).post('/api/restaurant/orders').send({
      items: [{ productId: 2, qty: 1 }],
      fulfillment: 'delivery',
      paymentMethod: 'stripe',
      address: {
        fullName: '  Ana Diner  ',
        phone: '+15550001234',
        line1: '12 Grid Street',
        city: 'Karachi',
        postcode: '75300',
        courier: 'free-limo',
        totalPrice: 0.01,
      },
    });

    expect(res.status).toBe(201);
    const payload = createOrder.mock.calls[0][1];
    expect(payload.paymentMethod).toBe('stripe');
    // Only the address fields are stored: the invoice renders this JSONB, so a
    // client cannot smuggle a discount or a delivery promise into it.
    expect(payload.shippingAddress).toEqual({
      fullName: 'Ana Diner',
      phone: '+15550001234',
      line1: '12 Grid Street',
      city: 'Karachi',
      postcode: '75300',
    });
  });

  it.each([
    ['a delivery with no address', { fulfillment: 'delivery' }],
    [
      'a delivery missing the street',
      { fulfillment: 'delivery', address: { fullName: 'A', phone: '1', city: 'X', postcode: '1' } },
    ],
  ])('rejects %s with 422 before the service runs', async (_label, extra) => {
    const res = await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 1 }], ...extra });

    expect(res.status).toBe(422);
    // express-validator reports the failing leaf, so a missing street surfaces
    // as `address.line1` rather than `address`.
    expect(res.body.details.some((d) => d.path.startsWith('address'))).toBe(true);
    expect(createOrder).not.toHaveBeenCalled();
  });

  it.each([
    ['an unknown payment method', { paymentMethod: 'crypto' }],
    ['an unknown fulfillment', { fulfillment: 'helipad' }],
    ['a 100-steak line', { items: [{ productId: 2, qty: 100 }] }],
    ['more lines than the kitchen can cook', { items: Array.from({ length: 51 }, (_, i) => ({ productId: i + 1, qty: 1 })) }],
    ['notes longer than the ticket', { items: [{ productId: 2, qty: 1 }], notes: 'x'.repeat(501) }],
  ])('rejects %s with 422', async (_label, extra) => {
    const res = await request(app).post('/api/restaurant/orders').send(extra);

    expect(res.status).toBe(422);
    expect(createOrder).not.toHaveBeenCalled();
  });

  it('queues the confirmation email with the recalculated total', async () => {
    await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 1 }] });

    expect(enqueue).toHaveBeenCalledWith(
      QUEUES.EMAIL,
      expect.objectContaining({
        to: 'diner@example.com',
        subject: 'Order Confirmed — #ORD-20260303-NEW',
        html: expect.stringContaining('Total: $46.50.'),
      })
    );
  });

  it.each([
    ['a missing cart', {}],
    ['an empty cart', { items: [] }],
    ['items that is not an array', { items: 'steak' }],
    ['an item without a productId', { items: [{ qty: 1 }] }],
    ['a zero-quantity line', { items: [{ productId: 2, qty: 0 }] }],
    ['a non-integer product id', { items: [{ productId: 'two', qty: 1 }] }],
  ])('rejects %s with 422 before the service is called', async (_label, payload) => {
    const res = await request(app).post('/api/restaurant/orders').send(payload);

    expect(res.status).toBe(422);
    expect(res.body).toMatchObject({ success: false, status: 422, code: 'VALIDATION_ERROR', data: null });
    expect(createOrder).not.toHaveBeenCalled();
  });

  it('surfaces the stock rejection with the service status code', async () => {
    createOrder.mockRejectedValue(
      Object.assign(new Error("Insufficient stock for product 'Ribeye Steak' (Available: 12)"), { statusCode: 400 })
    );
    // qty 13 is legal as far as the request validator is concerned (the per-line
    // ceiling is 99) and is rejected by the stock check inside the service.
    const res = await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 13 }] });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: "Insufficient stock for product 'Ribeye Steak' (Available: 12)" });
    expect(enqueue).not.toHaveBeenCalled();
  });

  it('maps a missing product to 404 and an unexpected failure to 500', async () => {
    createOrder.mockRejectedValue(Object.assign(new Error('Product not found'), { statusCode: 404 }));
    expect((await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 9, qty: 1 }] })).status).toBe(404);

    createOrder.mockRejectedValue(new Error('deadlock detected'));
    const failed = await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 1 }] });
    expect(failed.status).toBe(500);
    expect(failed.body.error).toBe('deadlock detected');
  });

  it('turns a queue rejection into a 500 (the order exists, the email did not send)', async () => {
    enqueue.mockRejectedValue(new Error('broker unreachable'));
    const res = await request(app).post('/api/restaurant/orders').send({ items: [{ productId: 2, qty: 1 }] });

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('broker unreachable');
  });
});

// ── GET /api/restaurant/orders ───────────────────────────────────────────────
describe('GET /api/restaurant/orders', () => {
  it('lists the caller restaurant orders inside the tenant', async () => {
    const res = await request(app).get('/api/restaurant/orders');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, count: 2, total: 2, pagination: { page: 1, limit: 10, pages: 1 } });
    expect(res.body.data.map((o) => o.id)).toEqual([1, 2]);
    expect(lastWhere(Order, 'findAndCountAll')).toEqual({ org_id: 7, user_id: 5, source: 'restaurant' });
  });

  it('pages with limit/offset', async () => {
    const res = await request(app).get('/api/restaurant/orders?page=2&limit=1');

    expect(res.body.data.map((o) => o.id)).toEqual([2]);
    expect(Order.calls.at(-1).options).toMatchObject({ limit: 1, offset: 1, order: [['createdAt', 'DESC']] });
  });

  it.each([
    ['page 0', 'page=0', { page: 1, limit: 10, offset: 0 }],
    ['a negative page', 'page=-4', { page: 1, limit: 10, offset: 0 }],
    ['limit 0', 'limit=0', { page: 1, limit: 10, offset: 0 }],
    ['a negative limit', 'limit=-1', { page: 1, limit: 10, offset: 0 }],
    ['a limit of 100000', 'limit=100000', { page: 1, limit: 100, offset: 0 }],
    ['a non-numeric page and limit', 'page=two&limit=lots', { page: 1, limit: 10, offset: 0 }],
  ])('clamps %s instead of handing it to SQL', async (_label, query, expected) => {
    const res = await request(app).get(`/api/restaurant/orders?${query}`);

    expect(res.status).toBe(200);
    expect(res.body.pagination.page).toBe(expected.page);
    expect(res.body.pagination.limit).toBe(expected.limit);
    expect(Order.calls.at(-1).options).toMatchObject({ limit: expected.limit, offset: expected.offset });
  });

  it('keeps store orders out of the food history', async () => {
    // Same user, same tenant, different vertical: the row exists and must not
    // appear, because `orders.source` is what the listing filters on.
    Order.rows.push({
      id: 9,
      user_id: 5,
      org_id: 7,
      orderNumber: 'ORD-ECOMM-1',
      status: 'pending',
      source: 'ecommerce',
      items: [{ product_id: 900, quantity: 1, price: 5 }],
      totalPrice: 5,
      deleted_at: null,
      createdAt: new Date('2026-02-05T09:00:00Z'),
    });

    const res = await request(app).get('/api/restaurant/orders');

    expect(lastWhere(Order, 'findAndCountAll').source).toBe('restaurant');
    expect(res.body.data.map((o) => o.orderNumber)).not.toContain('ORD-ECOMM-1');
    expect(res.body.data.map((o) => o.id)).toEqual([1, 2]);
  });

  it('scopes an unauthenticated-org caller to legacy rows', async () => {
    currentUser = { ...BUYER, current_org_id: null };
    await request(app).get('/api/restaurant/orders');

    expect(lastWhere(Order, 'findAndCountAll')).toEqual({
      org_id: { [Op.is]: null },
      user_id: 5,
      source: 'restaurant',
    });
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findAndCountAll', message: 'orders read failed' };
    const res = await request(app).get('/api/restaurant/orders');
    expect(res.status).toBe(500);
  });
});

// ── GET /api/restaurant/orders/:id ───────────────────────────────────────────
describe('GET /api/restaurant/orders/:id', () => {
  it('scopes the lookup to the owner inside the tenant filter', async () => {
    const res = await request(app).get('/api/restaurant/orders/1');

    expect(res.status).toBe(200);
    expect(res.body.data.orderNumber).toBe('ORD-20260201-AAA');
    expect(lastWhere(Order, 'findOne')).toEqual({ id: 1, user_id: 5, org_id: 7, source: 'restaurant' });
  });

  it.each([
    ['another user order in the same org', '3'],
    ['an order in another org', '4'],
    ['an unknown id', '9999'],
  ])('answers 404 for %s so nothing is leaked', async (_label, id) => {
    const res = await request(app).get(`/api/restaurant/orders/${id}`);

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
  });

  it('does not let an admin bypass the owner filter on this route', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).get('/api/restaurant/orders/3');

    expect(res.status).toBe(404);
  });

  it('rejects a non-numeric id with 422 instead of an operator 500', async () => {
    const res = await request(app).get('/api/restaurant/orders/abc');

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('id');
    expect(callsOf(Order, 'findOne')).toHaveLength(0);
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Order.findOne', message: 'order read failed' };
    const res = await request(app).get('/api/restaurant/orders/1');
    expect(res.status).toBe(500);
  });
});

// ── PATCH /api/restaurant/admin/orders/:id/status ────────────────────────────
describe('PATCH /api/restaurant/admin/orders/:id/status', () => {
  it('refuses a non-admin before reading the order', async () => {
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status: 'delivered' });

    expect(res.status).toBe(403);
    expect(Order.calls).toHaveLength(0);
  });

  it('marks the order status for an admin inside their tenant', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status: 'shipped' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: expect.objectContaining({ id: 1, status: 'shipped' }) });
    expect(callsOf(Order, 'update').at(-1).values).toEqual({ status: 'shipped' });
    expect(lastWhere(Order, 'findOne')).toEqual({ id: 1, org_id: 7, source: 'restaurant' });
  });

  it('answers 404 for another tenant order and deletes nothing', async () => {
    currentUser = { ...ADMIN, current_org_id: 9 };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status: 'delivered' });

    expect(res.status).toBe(404);
    expect(Order.rows[0].status).toBe('pending');
  });

  it('will not rewrite a store order from the kitchen queue', async () => {
    // Order 3 is the same tenant's hardware sale: a restaurant admin has no
    // business moving it, and the vertical filter is what says so.
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/3/status').send({ status: 'delivered' });

    expect(res.status).toBe(404);
    expect(Order.rows[2].status).toBe('processing');
    expect(callsOf(Order, 'update')).toHaveLength(0);
  });

  it('rejects a status outside the enum with 422', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status: 'teleported' });

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('status');
    expect(callsOf(Order, 'update')).toHaveLength(0);
  });

  it.each([
    ['processing', 'the kitchen queue'],
    ['shipped', 'out for delivery'],
    ['delivered', 'completed'],
  ])('moves a food order to %s (%s)', async (status) => {
    // The restaurant runs on the shared order pipeline: `processing` is the
    // kitchen and `shipped` is ready/out, which is what
    // src/pages/restaurant/AdminDashboard.jsx labels them. There is no separate
    // preparing/ready vocabulary to invent.
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status });

    expect(res.status).toBe(200);
    expect(callsOf(Order, 'update').at(-1).values).toEqual({ status });
  });

  it.each([
    ['cancelled', 'PATCH /api/orders/:id/cancel', 'restores stock'],
    ['refunded', 'POST /api/payments/refund', 'records the refund'],
  ])('refuses to write %s straight to the column', async (status, endpoint, why) => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain(endpoint);
    expect(res.body.error).toContain(why);
    expect(callsOf(Order, 'update')).toHaveLength(0);
    expect(Order.rows[0].status).toBe('pending');
  });

  it('rejects a non-numeric id with 422 before querying', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/orders/abc/status').send({ status: 'shipped' });

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('id');
    expect(callsOf(Order, 'findOne')).toHaveLength(0);
  });

  it('hands a failure to the error handler (500)', async () => {
    currentUser = { ...ADMIN };
    forcedFailure = { target: 'Order.findOne', message: 'status write failed' };
    const res = await request(app).patch('/api/restaurant/admin/orders/1/status').send({ status: 'shipped' });
    expect(res.status).toBe(500);
  });
});

// ── POST /api/restaurant/reservations ────────────────────────────────────────
describe('POST /api/restaurant/reservations', () => {
  const reservation = (overrides = {}) => ({
    date: '2027-06-01',
    time: '19:00',
    partySize: 4,
    name: 'Table for Ana',
    phone: '+15550001234',
    ...overrides,
  });

  /** A seating already held in this tenant (the route counts these). */
  const seated = (count, overrides = {}) => {
    const start = new Date('2027-06-01T19:30:00Z');
    for (let i = 0; i < count; i += 1) {
      Booking.rows.push({
        id: 500 + i,
        user_id: 8,
        org_id: 7,
        bookingNumber: `BK-SEAT-${i}`,
        date: '2027-06-01',
        time: '19:30',
        startAt: start,
        duration: 120,
        status: 'confirmed',
        metadata: { type: 'restaurant-reservation', partySize: 2 },
        ...overrides,
      });
    }
  };

  it('creates a table booking stamped with the caller tenant and identity', async () => {
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(201);
    const values = callsOf(Booking, 'create').at(-1).values;
    expect(values).toMatchObject({
      user_id: 5,
      org_id: 7,
      service_id: null,
      doctor_id: null,
      date: '2027-06-01',
      time: '19:00',
      status: 'pending',
      reason: 'Table reservation for 4',
      notes: '',
    });
    expect(values.metadata).toEqual({
      partySize: 4,
      phone: '+15550001234',
      name: 'Table for Ana',
      type: 'restaurant-reservation',
    });
    expect(values.startAt).toBeInstanceOf(Date);
    expect(res.body.data.id).toBe(Booking.rows.at(-1).id);
  });

  it('writes only columns models/Booking.js actually has', async () => {
    // `title` and `description` are not Sequelize attributes, so create() dropped
    // them and the party details vanished with them.
    await request(app).post('/api/restaurant/reservations').send(reservation());

    const values = callsOf(Booking, 'create').at(-1).values;
    expect(values).not.toHaveProperty('title');
    expect(values).not.toHaveProperty('description');
    expect(Object.keys(values).sort()).toEqual([
      'date',
      'doctor_id',
      'duration',
      'metadata',
      'notes',
      'org_id',
      'reason',
      'service_id',
      'startAt',
      'status',
      'time',
      'user_id',
    ]);
  });

  it('anchors the slot on an instant, not on the server local time', async () => {
    // The venue zone comes from RESTAURANT_TIMEZONE (UTC in tests), so the stored
    // value is the same instant on every deployment. A bare
    // `new Date('2027-06-01T19:00')` instead shifted by the host offset.
    await request(app).post('/api/restaurant/reservations').send(reservation());

    const stored = callsOf(Booking, 'create').at(-1).values.startAt;
    expect(stored).toBeInstanceOf(Date);
    expect(stored.toISOString()).toBe('2027-06-01T19:00:00.000Z');
  });

  it('holds the table for the seating duration', async () => {
    await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(callsOf(Booking, 'create').at(-1).values.duration).toBe(120);
  });

  it('keeps the notes in the notes column', async () => {
    await request(app).post('/api/restaurant/reservations').send(reservation({ notes: 'Window seat, high chair' }));

    const values = callsOf(Booking, 'create').at(-1).values;
    expect(values.notes).toBe('Window seat, high chair');
    expect(values.reason).toBe('Table reservation for 4');
  });

  it.each([
    ['partySize of 0', reservation({ partySize: 0 })],
    ['a party over the venue ceiling', reservation({ partySize: 21 })],
    ['a non-numeric partySize', reservation({ partySize: 'large' })],
    ['a missing date', { time: '19:00', partySize: 2 }],
    ['a non-ISO date', reservation({ date: '01/06/2026' })],
    ['a date that does not exist', reservation({ date: '2027-02-30' })],
    ['an empty time', reservation({ time: '' })],
    ['an impossible clock', reservation({ time: '25:70' })],
    ['a 12-hour clock', reservation({ time: '7pm' })],
    ['a name longer than a reservation', reservation({ name: 'x'.repeat(101) })],
  ])('rejects %s with 422 and writes nothing', async (_label, payload) => {
    const res = await request(app).post('/api/restaurant/reservations').send(payload);

    expect(res.status).toBe(422);
    expect(res.body).toMatchObject({ success: false, status: 422, code: 'VALIDATION_ERROR', data: null });
    expect(callsOf(Booking, 'create')).toHaveLength(0);
    expect(Booking.rows).toHaveLength(0);
  });

  it('refuses a slot that has already passed', async () => {
    const res = await request(app).post('/api/restaurant/reservations').send(reservation({ date: '2020-01-06' }));

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Reservations must be for a future date and time' });
    expect(Booking.rows).toHaveLength(0);
  });

  it('checks availability before inserting, so a table cannot be double-booked', async () => {
    seated(1);
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(201);
    expect(Booking.rows).toHaveLength(2);
    const availability = callsOf(Booking, 'findAll').at(-1);
    expect(availability.where).toEqual({
      org_id: 7,
      date: '2027-06-01',
      status: { [Op.notIn]: ['cancelled', 'no-show'] },
    });
    expect(availability.transaction).toBeDefined();
  });

  it('refuses the caller a second table in the same slot', async () => {
    seated(1, { user_id: 5 });
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(409);
    expect(res.body).toEqual({ success: false, error: 'You already have a reservation at this time' });
    expect(Booking.rows).toHaveLength(1);
  });

  it('refuses the slot once every table is seated', async () => {
    seated(8);
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(409);
    expect(res.body).toEqual({ success: false, error: 'No table is free at this time' });
    expect(Booking.rows).toHaveLength(8);
  });

  it('counts only the tables that actually overlap the seating', async () => {
    // Eight seatings from 21:00Z: the 19:00Z party leaves as they arrive.
    seated(8, { startAt: new Date('2027-06-01T21:00:00Z'), time: '21:00' });
    const res = await request(app).post('/api/restaurant/reservations').send(reservation({ time: '19:00' }));

    expect(res.status).toBe(201);
  });

  it('frees a cancelled or no-show seating', async () => {
    seated(4, { status: 'cancelled' });
    seated(4, { status: 'no-show' });
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    // The where clause excludes them, so nothing is counted against capacity.
    expect(Booking.rows).toHaveLength(9);
    expect(res.status).toBe(201);
  });

  it('never counts another tenant seatings or an appointment', async () => {
    seated(8, { org_id: 3 });
    Booking.rows.push({
      id: 900,
      user_id: 5,
      org_id: 7,
      date: '2027-06-01',
      time: '19:30',
      startAt: new Date('2027-06-01T19:30:00Z'),
      duration: 30,
      status: 'confirmed',
      doctor_id: 1,
      // A healthcare appointment: no reservation metadata at all.
    });

    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(201);
  });

  it('stamps the legacy NULL org for a caller with no organization', async () => {
    currentUser = { ...BUYER, current_org_id: null };
    await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(callsOf(Booking, 'create').at(-1).values.org_id).toBeNull();
    expect(callsOf(Booking, 'findAll').at(-1).where.org_id).toEqual({ [Op.is]: null });
  });

  it('hands a write failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Booking.create', message: 'reservations table locked' };
    const res = await request(app).post('/api/restaurant/reservations').send(reservation());

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('reservations table locked');
  });
});

// ── GET /api/restaurant/reservations ─────────────────────────────────────────
describe('GET /api/restaurant/reservations', () => {
  it('queries the caller own reservations by tenant and metadata type', async () => {
    const res = await request(app).get('/api/restaurant/reservations');

    expect(res.status).toBe(200);
    // The double cannot evaluate Op.contains, so the query shape is the evidence.
    expect(lastWhere(Booking, 'findAll')).toEqual({
      org_id: 7,
      user_id: 5,
      metadata: { [Op.contains]: { type: 'restaurant-reservation' } },
    });
    expect(Booking.calls.at(-1).options.order).toEqual([['startAt', 'DESC']]);
    expect(res.body).toEqual({ success: true, data: [] });
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Booking.findAll', message: 'read failed' };
    const res = await request(app).get('/api/restaurant/reservations');
    expect(res.status).toBe(500);
  });
});

// ── POST /api/restaurant/reviews ─────────────────────────────────────────────
describe('POST /api/restaurant/reviews', () => {
  it('stores a new review and recomputes the aggregate rating honestly', async () => {
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 2, rating: 1, comment: 'Overcooked' });

    expect(res.status).toBe(201);
    expect(callsOf(Review, 'findOrCreate').at(-1)).toEqual({
      where: { user_id: 5, product_id: 2 },
      defaults: { rating: 1, comment: 'Overcooked', org_id: 7 },
    });

    const aggregate = callsOf(Review, 'findAll').at(-1);
    expect(aggregate.where).toEqual({ product_id: 2 });
    expect(aggregate.attributes[0][0]).toEqual({ fn: 'AVG', args: [{ col: 'rating' }] });

    // 4, 5 and the new 1 → mean 3.333…, three reviews.
    expect(Product.rows[1].rating).toBe(3.33);
    expect(Product.rows[1].reviewCount).toBe(3);
    expect(res.body.data.comment).toBe('Overcooked');
  });

  it('replaces an existing review instead of duplicating it', async () => {
    currentUser = { ...BUYER, id: 8, current_org_id: 7 };
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 2, rating: 5 });

    expect(res.status).toBe(201);
    expect(Review.rows).toHaveLength(3);
    expect(Review.rows[0].rating).toBe(5);
    expect(Review.rows[0].comment).toBe('');
    expect(res.body.data.id).toBe(10);
    // 5 and 5 → mean 5, two reviews.
    expect(Product.rows[1].rating).toBe(5);
    expect(Product.rows[1].reviewCount).toBe(2);
  });

  it('defaults an omitted comment to an empty string', async () => {
    await request(app).post('/api/restaurant/reviews').send({ productId: 1, rating: 4 });

    expect(callsOf(Review, 'findOrCreate').at(-1).defaults.comment).toBe('');
  });

  it.each([
    ['a rating of 0', { productId: 2, rating: 0 }],
    ['a rating of 6', { productId: 2, rating: 6 }],
    ['a non-integer rating', { productId: 2, rating: 'four' }],
    ['a missing product id', { rating: 4 }],
    ['a non-numeric product id', { productId: 'steak', rating: 4 }],
  ])('rejects %s with 422', async (_label, payload) => {
    const res = await request(app).post('/api/restaurant/reviews').send(payload);

    expect(res.status).toBe(422);
    expect(callsOf(Review, 'findOrCreate')).toHaveLength(0);
    expect(Product.rows[1].reviewCount).toBe(2);
  });

  it('answers 404 for an unknown menu item', async () => {
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 999, rating: 5 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Menu item not found' });
    expect(callsOf(Review, 'findOrCreate')).toHaveLength(0);
  });

  it('refuses to rate another organization menu item', async () => {
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 5, rating: 5, comment: 'Sabotage' });

    // The lookup is tenant-scoped, so org-3 item 5 is invisible to this caller:
    // no review row is written and the other tenant's aggregate is untouched.
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Menu item not found' });
    expect(lastWhere(Product, 'findOne')).toEqual({ id: 5, org_id: 7 });
    expect(callsOf(Review, 'findOrCreate')).toHaveLength(0);
    expect(Product.rows[4].rating).not.toBe(4);
  });

  it('hands a rating write failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Review.findOrCreate', message: 'review write failed' };
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 2, rating: 5 });

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('review write failed');
  });

  it('hands an aggregate recompute failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Review.findAll', message: 'aggregate read failed' };
    const res = await request(app).post('/api/restaurant/reviews').send({ productId: 2, rating: 5 });

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('aggregate read failed');
  });
});

// ── GET /api/restaurant/reviews/:productId ───────────────────────────────────
describe('GET /api/restaurant/reviews/:productId', () => {
  it('lists the reviews for a menu item, newest first, capped at 20', async () => {
    const res = await shop('/api/restaurant/reviews/2');

    expect(res.status).toBe(200);
    // The double ignores `order`, so only the set is asserted here; the sort the
    // route asked for is asserted from the recorded options below.
    expect(res.body.data.map((r) => r.id).sort((a, b) => a - b)).toEqual([10, 11]);
    expect(lastWhere(Review, 'findAll')).toEqual({ product_id: '2', org_id: 7 });
    expect(Review.calls.at(-1).options).toMatchObject({ limit: 20, order: [['createdAt', 'DESC']] });
  });

  it('never lists another organization item reviews', async () => {
    const res = await shop('/api/restaurant/reviews/5');

    expect(res.body.data).toEqual([]);
    expect(lastWhere(Review, 'findAll').org_id).toBe(7);
  });

  it('answers an empty list for an item nobody reviewed', async () => {
    const res = await shop('/api/restaurant/reviews/1');
    expect(res.body).toEqual({ success: true, data: [] });
  });

  it('hands a failure to the error handler (500)', async () => {
    forcedFailure = { target: 'Review.findAll', message: 'reviews read failed' };
    const res = await request(app).get('/api/restaurant/reviews/2');
    expect(res.status).toBe(500);
  });
});

// ── Admin menu CRUD ──────────────────────────────────────────────────────────
describe('POST /api/restaurant/admin/menu', () => {
  const newDish = (overrides = {}) => ({
    title: 'Lamb Kofta',
    price: '18.50',
    category: 'Mains',
    description: 'With mint yoghurt',
    tags: ['gluten-free'],
    ...overrides,
  });

  it('refuses a non-admin before writing', async () => {
    const res = await request(app).post('/api/restaurant/admin/menu').send(newDish());

    expect(res.status).toBe(403);
    expect(callsOf(Product, 'create')).toHaveLength(0);
  });

  it('creates the dish stamped with the caller tenant', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).post('/api/restaurant/admin/menu').send(newDish());

    expect(res.status).toBe(201);
    expect(callsOf(Product, 'create').at(-1).values).toEqual({
      title: 'Lamb Kofta',
      description: 'With mint yoghurt',
      price: '18.50',
      category: 'Mains',
      tags: ['gluten-free'],
      org_id: 7,
    });
    expect(res.body.data.id).toBe(Product.rows.at(-1).id);
  });

  it('blocks mass assignment through keys outside the whitelist', async () => {
    currentUser = { ...ADMIN, current_org_id: 3 };
    const res = await request(app)
      .post('/api/restaurant/admin/menu')
      .send(newDish({ id: 999, org_id: 7, user_id: 5, rating: 5, reviewCount: 400, deleted_at: null, isActive: false, isFeatured: true }));

    expect(res.status).toBe(201);
    const values = callsOf(Product, 'create').at(-1).values;
    expect(values).not.toHaveProperty('id');
    expect(values).not.toHaveProperty('rating');
    expect(values).not.toHaveProperty('reviewCount');
    expect(values).not.toHaveProperty('deleted_at');
    expect(values.org_id).toBe(3);
    expect(values.isActive).toBe(false);
    expect(values.isFeatured).toBe(true);
  });

  it.each([
    ['a missing title', newDish({ title: '' })],
    ['a missing category', { title: 'X', price: 1 }],
    ['a negative price', newDish({ price: -1 })],
    ['a non-numeric price', newDish({ price: 'free' })],
  ])('rejects %s with 422', async (_label, payload) => {
    currentUser = { ...ADMIN };
    const res = await request(app).post('/api/restaurant/admin/menu').send(payload);

    expect(res.status).toBe(422);
    expect(callsOf(Product, 'create')).toHaveLength(0);
  });

  it('hands a write failure to the error handler (500)', async () => {
    currentUser = { ...ADMIN };
    forcedFailure = { target: 'Product.create', message: 'menu write failed' };
    const res = await request(app).post('/api/restaurant/admin/menu').send(newDish());
    expect(res.status).toBe(500);
  });
});

describe('PATCH /api/restaurant/admin/menu/:id', () => {
  it('refuses a non-admin', async () => {
    const res = await request(app).patch('/api/restaurant/admin/menu/1').send({ price: '1.00' });
    expect(res.status).toBe(403);
  });

  it('updates only whitelisted fields on the caller tenant item', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app)
      .patch('/api/restaurant/admin/menu/1')
      .send({ price: '11.00', isFeatured: false, org_id: 3, rating: 5, user_id: 9 });

    expect(res.status).toBe(200);
    expect(lastWhere(Product, 'findOne')).toEqual({ id: '1', org_id: 7 });
    expect(callsOf(Product, 'update').at(-1).values).toEqual({ price: '11.00', isFeatured: false });
    expect(Product.rows[0].org_id).toBe(7);
    expect(Product.rows[0].rating).toBe(4.2);
  });

  it('answers 404 for another tenant item and writes nothing', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/menu/5').send({ price: '0.01' });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Menu item not found' });
    expect(callsOf(Product, 'update')).toHaveLength(0);
    expect(Product.rows[4].price).toBe('20.00');
  });

  it('rejects a non-numeric id with 422 before querying', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/menu/abc').send({ price: '1' });

    expect(res.status).toBe(422);
    expect(callsOf(Product, 'findOne')).toHaveLength(0);
  });

  it('leaves the row untouched when nothing in the body is whitelisted', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).patch('/api/restaurant/admin/menu/1').send({ bogus: 'x' });

    expect(res.status).toBe(200);
    expect(callsOf(Product, 'update').at(-1).values).toEqual({});
  });
});

describe('DELETE /api/restaurant/admin/menu/:id', () => {
  it('refuses a non-admin', async () => {
    const res = await request(app).delete('/api/restaurant/admin/menu/1');
    expect(res.status).toBe(403);
    expect(Product.calls).toHaveLength(0);
  });

  it('soft-deletes the item and hides it from the public menu', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).delete('/api/restaurant/admin/menu/1');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Menu item removed' });
    expect(Product.rows).toHaveLength(5);
    expect(Product.rows[0].deleted_at).toBeInstanceOf(Date);

    const menu = await request(app).get('/api/restaurant/menu');
    expect(menuIds(menu.body)).not.toContain(1);
  });

  it('answers 404 for another tenant item and keeps it alive', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).delete('/api/restaurant/admin/menu/5');

    expect(res.status).toBe(404);
    expect(Product.rows[4].deleted_at).toBeNull();
  });

  it('rejects a non-numeric id with 422', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).delete('/api/restaurant/admin/menu/NaN');

    expect(res.status).toBe(422);
    expect(callsOf(Product, 'destroy')).toHaveLength(0);
  });

  it('returns 404 when the item is already deleted', async () => {
    currentUser = { ...ADMIN };
    await request(app).delete('/api/restaurant/admin/menu/2');
    const res = await request(app).delete('/api/restaurant/admin/menu/2');

    expect(res.status).toBe(404);
  });
});

// ── GET /api/restaurant/admin/stats ──────────────────────────────────────────
describe('GET /api/restaurant/admin/stats', () => {
  it('refuses a non-admin', async () => {
    const res = await request(app).get('/api/restaurant/admin/stats');
    expect(res.status).toBe(403);
  });

  it('scopes every aggregate to the caller tenant on the real org_id column', async () => {
    currentUser = { ...ADMIN };
    const res = await request(app).get('/api/restaurant/admin/stats');

    expect(res.status).toBe(200);
    // `orgId` is not a column: it matched nothing, and on PostgreSQL the unknown
    // attribute aborts each count. The route now uses tenantWhere().
    expect(lastWhere(Product, 'count')).toEqual({ org_id: 7, isActive: true });
    expect(lastWhere(Order, 'count')).toEqual({
      org_id: 7,
      source: 'restaurant',
      status: ['pending', 'processing', 'shipped'],
    });
    expect(callsOf(Order, 'sum').at(-1).where).toEqual({ org_id: 7, source: 'restaurant', status: 'delivered' });
    expect(lastWhere(Booking, 'count')).toMatchObject({ org_id: 7 });

    expect(res.body.data).toEqual({
      totalMenuItems: 2,
      totalOrders: 2,
      totalRevenue: 34.1,
      pendingOrders: 1,
      totalReservations: 0,
    });
  });

  it('keeps store revenue off the restaurant dashboard', async () => {
    currentUser = { ...ADMIN };
    Order.rows.push({
      id: 10,
      user_id: 6,
      org_id: 7,
      orderNumber: 'ORD-ECOMM-2',
      status: 'delivered',
      source: 'ecommerce',
      items: [{ product_id: 900, quantity: 1, price: 900 }],
      totalPrice: 900,
      deleted_at: null,
      createdAt: new Date('2026-02-06T09:00:00Z'),
    });

    const res = await request(app).get('/api/restaurant/admin/stats');

    expect(res.body.data.totalRevenue).toBe(34.1);
    expect(res.body.data.totalOrders).toBe(2);
  });

  it('sums delivered revenue when the filter matches its own column', async () => {
    currentUser = { ...ADMIN };
    const total = await Order.sum('totalPrice', { where: { org_id: 7, status: 'delivered' } });

    expect(total).toBeCloseTo(34.1, 2);
    expect(callsOf(Order, 'sum')).toHaveLength(1);
  });

  it('treats a null revenue aggregate as zero', async () => {
    // An empty delivered set makes Order.sum() resolve to null; the route
    // coerces with `|| 0` so the dashboard never reports NaN.
    expect(await Order.sum('totalPrice', { where: { org_id: 7, status: 'refunded' } })).toBeNull();
    currentUser = { ...ADMIN };
    Order.rows.forEach((row) => {
      if (row.status === 'delivered') row.status = 'refunded';
    });

    const res = await request(app).get('/api/restaurant/admin/stats');
    expect(res.body.data.totalRevenue).toBe(0);
  });

  it('hands a broken aggregate to the error handler (500)', async () => {
    currentUser = { ...ADMIN };
    forcedFailure = { target: 'Product.count', message: 'stats read failed' };
    const res = await request(app).get('/api/restaurant/admin/stats');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('stats read failed');
  });
});
