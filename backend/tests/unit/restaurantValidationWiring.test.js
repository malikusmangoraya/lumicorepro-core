/**
 * Unit tests — the validation wiring in routes/restaurant.routes.js
 *
 * `validateRequest` is a FACTORY (`validateRequest(schema) => middleware`).
 * restaurant.routes.js used to place the factory itself in nine express-validator
 * chains; Express called it as `(req, res, next)`, it returned a new middleware,
 * and no route ever called `next()` — those nine endpoints hung until the client
 * timed out. They now use `checkValidation`
 * (middleware/validationResult.js), the express-validator terminal.
 *
 * The first block keeps proving WHY the bare factory is a bug, so the mistake
 * cannot be reintroduced; the second block runs the REAL router (no middleware
 * substituted) and asserts the endpoints answer.
 */
import express from 'express';
import request from 'supertest';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel, createFakeSequelize } from '../helpers/sequelizeFakes.js';
import { validateRequest } from '../../middleware/validateRequest.js';

const fakeDb = {
  ...createFakeSequelize(),
  fn: (fn, ...args) => ({ fn, args }),
  col: (column) => ({ col: column }),
};

const Product = createFakeModel('Product', [
  { id: 1, org_id: 7, title: 'Ribeye Steak', category: 'Mains', isActive: true, isFeatured: true, deleted_at: null },
]);
const Order = createFakeModel('Order', []);
const Review = createFakeModel('Review', []);
const Booking = createFakeModel('Booking', []);
const User = createFakeModel('User', [{ id: 5, name: 'Diner', email: 'diner@example.com' }]);

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { id: 5, role: 'user', email: 'diner@example.com', current_org_id: 7 };
    next();
  },
  authorize: () => (req, _res, next) => next(),
  optionalProtect: (req, _res, next) => next(),
}));

jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: fakeDb,
  default: async () => fakeDb,
}));

jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  enqueue: jest.fn().mockResolvedValue({ jobId: 'job-1' }),
  QUEUES: { EMAIL: 'email' },
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() },
  withRequestId: () => ({}),
  redact: (value) => value,
}));

for (const [path, model] of [
  ['../../models/Product.js', Product],
  ['../../models/Order.js', Order],
  ['../../models/Review.js', Review],
  ['../../models/Booking.js', Booking],
  ['../../models/User.js', User],
]) {
  jest.unstable_mockModule(path, () => ({ __esModule: true, default: model }));
}

const { default: restaurantRoutes } = await import('../../routes/restaurant.routes.js');

const app = express();
app.use(express.json());
app.use('/api/restaurant', restaurantRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

/**
 * Resolve with the error a timed-out request produced (or `null` if it answered).
 * The bug this detects never responds at all, so the budget only has to be long
 * enough to out-run a loaded parallel worker — 400ms flaked on a full-suite run.
 */
const attemptWithTimeout = async (request_, ms = 3000) => {
  try {
    const res = await request_.timeout(ms);
    return null;
  } catch (error) {
    return error;
  }
};

beforeEach(() => {
  for (const model of [Product, Order, Review, Booking, User]) model.calls.length = 0;
});

describe('the factory-as-middleware mistake', () => {
  it('returns a middleware instead of calling next() when Express invokes it', () => {
    let nextCalled = false;
    const returned = validateRequest(
      { body: {}, query: {}, params: {} },
      { json() {} },
      () => {
        nextCalled = true;
      }
    );

    expect(typeof returned).toBe('function');
    expect(nextCalled).toBe(false);
  });

  it('reads the request body as if it were a Zod schema declaration', () => {
    // The destructure target is `{ body, query, params }`; `req.body` is data, so
    // the returned middleware would call `req.body.parse(...)` if it ever ran.
    let nextCalled = false;
    const middleware = validateRequest(
      { body: { items: [1] }, query: {}, params: {} },
      {},
      () => {
        nextCalled = true;
      }
    );

    expect(() => middleware({ body: { items: [1] }, query: {}, params: {} }, {}, () => {})).toThrow();
    expect(nextCalled).toBe(false);
  });
});

describe('GET/POST through the real router', () => {
  it('answers GET /menu: the express-validator chain reaches checkValidation', async () => {
    const error = await attemptWithTimeout(request(app).get('/api/restaurant/menu'));

    expect(error).toBeNull();
    expect(Product.calls.map((c) => c.method)).toContain('findAndCountAll');
  });

  it('rejects an invalid menu query with the canonical 422 instead of hanging', async () => {
    const res = await request(app).get('/api/restaurant/menu').query({ limit: '900' });

    expect(res.status).toBe(422);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details.map((d) => d.path)).toContain('limit');
  });

  it('answers POST /reservations, and 422s an out-of-range party size', async () => {
    const ok = await request(app)
      .post('/api/restaurant/reservations')
      .send({ date: '2027-06-01', time: '19:00', partySize: 4 });
    expect(ok.status).toBe(201);
    expect(Booking.calls.map((c) => c.method)).toContain('create');

    const rejected = await request(app)
      .post('/api/restaurant/reservations')
      .send({ date: '2027-06-01', time: '19:00', partySize: 99 });
    expect(rejected.status).toBe(422);
    expect(rejected.body.details.map((d) => d.path)).toContain('partySize');
  });

  it('does answer GET /featured, which has no validator in its chain', async () => {
    const res = await request(app).get('/api/restaurant/featured').timeout(3000);

    // /featured is anonymous, so tenant scoping restricts it to legacy
    // org_id IS NULL rows — the seeded org-7 product is correctly hidden.
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, data: [] });

    const scoped = await request(app).get('/api/restaurant/featured').set('x-org-id', '7');
    expect(scoped.body).toEqual({ success: true, data: [expect.objectContaining({ id: 1 })] });
  });

  it('does answer GET /orders/:id, which is also wired without it', async () => {
    const res = await request(app).get('/api/restaurant/orders/1').timeout(3000);

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Order not found' });
  });
});
