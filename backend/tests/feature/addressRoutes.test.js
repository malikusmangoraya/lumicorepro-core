/**
 * Feature tests — routes/address.routes.js
 *
 * The router is mounted on a bare Express app with `protect` stubbed (so the
 * caller's identity is a test input, not a JWT) and the Address model replaced
 * by the in-memory Sequelize double from tests/helpers/sequelizeFakes.js. That
 * double records every query, so these tests assert the ownership filter that
 * ACTUALLY reached the database, not just the status code.
 *
 * Response-envelope note (AGENTS.md §4): this router writes its bodies by hand
 * (`res.json({ success, data })`) and never goes through utils/response.js, so
 * there is no `status`/`timestamp` to assert here. Only the routes that use the
 * shared helpers are checked against the canonical envelope.
 */
import express from 'express';
import request from 'supertest';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const OWNER = { id: 10, role: 'user', email: 'owner@example.com' };
const ADMIN = { id: 99, role: 'admin', email: 'admin@example.com' };

/** Identity the stubbed `protect` middleware attaches to `req.user`. */
let currentUser = { ...OWNER };

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

const addressRows = () => [
  {
    id: 1,
    user_id: 10,
    name: 'Ada Lovelace',
    phone: '+15550001',
    address_line1: '1 Analytical Way',
    address_line2: 'Apt 2',
    city: 'New York',
    state: 'NY',
    postal_code: '10001',
    country: 'US',
    is_default: true,
    label: 'shipping',
    createdAt: new Date('2026-01-01T00:00:00Z'),
  },
  {
    id: 2,
    user_id: 10,
    name: 'Ada Lovelace',
    phone: '',
    address_line1: '2 Billing Rd',
    address_line2: '',
    city: 'Boston',
    state: 'MA',
    postal_code: '02110',
    country: 'US',
    is_default: false,
    label: 'billing',
    createdAt: new Date('2026-01-02T00:00:00Z'),
  },
  {
    id: 3,
    user_id: 20,
    name: 'Other Person',
    phone: '',
    address_line1: '9 Someone Else St',
    address_line2: '',
    city: 'Austin',
    state: 'TX',
    postal_code: '73301',
    country: 'US',
    is_default: false,
    label: 'shipping',
    createdAt: new Date('2026-01-03T00:00:00Z'),
  },
];

const Address = createFakeModel('Address', addressRows());

jest.unstable_mockModule('../../models/Address.js', () => ({
  __esModule: true,
  default: Address,
}));

const { default: addressRoutes } = await import('../../routes/address.routes.js');

const app = express();
app.use(express.json());
app.use('/api/addresses', addressRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const validBody = (overrides = {}) => ({
  name: 'Grace Hopper',
  address_line1: '401 Compiler Ave',
  city: 'Arlington',
  country: 'US',
  label: 'shipping',
  ...overrides,
});

/** Recorded payloads — the double stores every call as `{ method, options }`. */
const methodsCalled = (method) =>
  Address.calls.filter((c) => c.method === method).map((c) => c.options);
const rowById = (id) => Address.rows.find((r) => r.id === id);

beforeEach(() => {
  Address.rows.length = 0;
  Address.rows.push(...addressRows());
  Address.calls.length = 0;
  currentUser = { ...OWNER };
});

describe('GET /api/addresses', () => {
  it('pins the query to the caller and returns only their rows', async () => {
    const res = await request(app).get('/api/addresses');

    expect(res.status).toBe(200);
    expect(Address.whereCalls('findAll')[0].where).toEqual({ user_id: OWNER.id });
    expect(res.body.success).toBe(true);
    expect(res.body.data.map((a) => a.id)).toEqual([1, 2]);
    expect(res.body.data.every((a) => a.user_id === OWNER.id)).toBe(true);
  });

  it('asks for the default address first', async () => {
    await request(app).get('/api/addresses');

    expect(Address.whereCalls('findAll')[0].order).toEqual([
      ['is_default', 'DESC'],
      ['createdAt', 'DESC'],
    ]);
  });

  it('gives an admin the same user-scoped list (no cross-user read)', async () => {
    currentUser = { ...ADMIN };

    const res = await request(app).get('/api/addresses');

    expect(res.status).toBe(200);
    expect(Address.whereCalls('findAll')[0].where).toEqual({ user_id: ADMIN.id });
    expect(res.body.data).toEqual([]);
  });
});

describe('POST /api/addresses', () => {
  it('creates the address for the authenticated user', async () => {
    const res = await request(app).post('/api/addresses').send(validBody());

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    const { values } = methodsCalled('create')[0];
    expect(values.name).toBe('Grace Hopper');
    expect(values.address_line1).toBe('401 Compiler Ave');
    expect(values.city).toBe('Arlington');
    expect(values.label).toBe('shipping');
    expect(values.is_default).toBe(false);
    expect(mockLogger.info).toHaveBeenCalledWith(
      expect.stringContaining('Address created for user 10'),
    );
  });

  it('trims whitespace before persisting', async () => {
    const res = await request(app)
      .post('/api/addresses')
      .send(validBody({ name: '  Grace Hopper  ', city: '  Arlington ' }));

    expect(res.status).toBe(201);
    const { values } = methodsCalled('create')[0];
    expect(values.name).toBe('Grace Hopper');
    expect(values.city).toBe('Arlington');
  });

  it('clears the previous default before creating a new default one', async () => {
    const res = await request(app)
      .post('/api/addresses')
      .send(validBody({ is_default: true }));

    expect(res.status).toBe(201);
    const order = Address.calls.map((c) => c.method);
    expect(order.slice(0, 2)).toEqual(['update', 'create']);
    const [firstUpdate] = methodsCalled('update');
    expect(firstUpdate.values).toEqual({ is_default: false });
    expect(firstUpdate.options.where).toEqual({ user_id: OWNER.id });
    expect(rowById(1).is_default).toBe(false);
    expect(methodsCalled('create')[0].values.is_default).toBe(true);
  });

  it('never demotes another user default when the new address is not the default', async () => {
    const res = await request(app).post('/api/addresses').send(validBody());

    expect(res.status).toBe(201);
    expect(methodsCalled('update')).toHaveLength(0);
    expect(rowById(1).is_default).toBe(true);
  });

  it('rejects a missing required field with 400 and field-level errors', async () => {
    const res = await request(app)
      .post('/api/addresses')
      .send({ address_line1: '401 Compiler Ave', city: 'Arlington' });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(res.body.errors.map((e) => e.path)).toContain('name');
    expect(res.body.errors.find((e) => e.path === 'name').msg).toBe('Name is required');
    expect(methodsCalled('create')).toHaveLength(0);
  });

  it('rejects a blank city and a blank street', async () => {
    const res = await request(app)
      .post('/api/addresses')
      .send({ name: 'Grace', address_line1: '   ', city: '' });

    expect(res.status).toBe(400);
    const paths = res.body.errors.map((e) => e.path);
    expect(paths).toContain('address_line1');
    expect(paths).toContain('city');
  });

  it('rejects an unknown label', async () => {
    const res = await request(app).post('/api/addresses').send(validBody({ label: 'warehouse' }));

    expect(res.status).toBe(400);
    expect(res.body.errors[0]).toMatchObject({ path: 'label', msg: 'Invalid address label' });
    expect(methodsCalled('create')).toHaveLength(0);
  });

  it('rejects an empty optional country instead of storing it', async () => {
    const res = await request(app).post('/api/addresses').send(validBody({ country: '' }));

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.path)).toContain('country');
  });

  it('omitting country and label is valid', async () => {
    const body = validBody();
    delete body.country;
    delete body.label;

    const res = await request(app).post('/api/addresses').send(body);

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
  });

  /**
   * FIXED — routes/address.routes.js used to spread `req.body` after the
   * server-set owner, so a caller-supplied `user_id` won. The body is now
   * whitelisted to the address columns, so the token owner always wins.
   */
  it('ignores a body-supplied user_id and keeps the token owner', async () => {
    const res = await request(app).post('/api/addresses').send(validBody({ user_id: 20 }));

    expect(res.status).toBe(201);
    expect(methodsCalled('create')[0].values.user_id).toBe(OWNER.id);
    expect(rowById(res.body.data.id).user_id).toBe(OWNER.id);
  });
});

describe('PUT /api/addresses/:id', () => {
  it('updates the owner row in place', async () => {
    const res = await request(app)
      .put('/api/addresses/1')
      .send({ name: 'Ada L.', city: 'Albany', is_default: false });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(rowById(1).name).toBe('Ada L.');
    expect(rowById(1).city).toBe('Albany');
  });

  it('scopes the lookup to id + caller (no IDOR write)', async () => {
    const res = await request(app).put('/api/addresses/3').send({ city: 'Hacked' });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Address not found' });
    expect(Address.whereCalls('findOne')[0].where).toEqual({ id: 3, user_id: OWNER.id });
    expect(methodsCalled('update')).toHaveLength(0);
    expect(rowById(3).city).toBe('Austin');
  });

  it('treats a non-numeric id as not found', async () => {
    const res = await request(app).put('/api/addresses/abc').send({ city: 'Hacked' });

    expect(res.status).toBe(404);
    expect(methodsCalled('update')).toHaveLength(0);
  });

  it('demotes the other defaults when promoting this one', async () => {
    const res = await request(app).put('/api/addresses/2').send({ is_default: true });

    expect(res.status).toBe(200);
    expect(rowById(1).is_default).toBe(false);
    expect(rowById(2).is_default).toBe(true);
    const demote = methodsCalled('update').find((c) => c.options && c.options.where);
    expect(demote.values).toEqual({ is_default: false });
  });

  it('sends a falsey is_default without touching the other rows', async () => {
    const res = await request(app).put('/api/addresses/1').send({ is_default: false });

    expect(res.status).toBe(200);
    expect(rowById(1).is_default).toBe(false);
    expect(rowById(2).is_default).toBe(false);
  });

  /**
   * FIXED — `address.update(req.body)` wrote arbitrary columns, including
   * `user_id`, which re-parented the row. PUT is now validated and whitelisted,
   * so the owner column is untouchable.
   */
  it('ignores a user_id in the PUT body and keeps the owner', async () => {
    const res = await request(app).put('/api/addresses/1').send({ user_id: 20, city: 'Albany' });

    expect(res.status).toBe(200);
    expect(rowById(1).user_id).toBe(OWNER.id);
    expect(rowById(1).city).toBe('Albany');
  });

  it('rejects an empty name instead of blanking a required column', async () => {
    const res = await request(app).put('/api/addresses/1').send({ name: '   ' });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.path)).toContain('name');
    expect(rowById(1).name).toBe('Ada Lovelace');
  });

  it('rejects a non-boolean is_default', async () => {
    const res = await request(app).put('/api/addresses/1').send({ is_default: 'yes' });

    expect(res.status).toBe(400);
    expect(methodsCalled('update')).toHaveLength(0);
  });
});

describe('PATCH /api/addresses/:id/default', () => {
  it('clears every other default for the caller and sets this one', async () => {
    const res = await request(app).patch('/api/addresses/2/default');

    expect(res.status).toBe(200);
    const order = Address.calls.map((c) => c.method);
    expect(order).toEqual(['findOne', 'update', 'update']);
    expect(Address.whereCalls('findOne')[0].where).toEqual({ id: 2, user_id: OWNER.id });
    expect(rowById(1).is_default).toBe(false);
    expect(rowById(2).is_default).toBe(true);
  });

  it('404s for another user address and writes nothing', async () => {
    const res = await request(app).patch('/api/addresses/3/default');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Address not found' });
    expect(methodsCalled('update')).toHaveLength(0);
    expect(rowById(3).is_default).toBe(false);
  });

  it('404s for an unknown id', async () => {
    const res = await request(app).patch('/api/addresses/404/default');

    expect(res.status).toBe(404);
  });
});

describe('DELETE /api/addresses/:id', () => {
  it('removes only the caller row', async () => {
    const res = await request(app).delete('/api/addresses/1');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Address deleted' });
    expect(rowById(1)).toBeUndefined();
    expect(rowById(2)).toBeDefined();
    expect(rowById(3)).toBeDefined();
  });

  it('404s when trying to delete another user address', async () => {
    const res = await request(app).delete('/api/addresses/3');

    expect(res.status).toBe(404);
    expect(rowById(3)).toBeDefined();
    expect(methodsCalled('destroy')).toHaveLength(0);
  });

  it('404s for a non-numeric id', async () => {
    const res = await request(app).delete('/api/addresses/not-a-number');

    expect(res.status).toBe(404);
  });

  it('404s when the same address is deleted twice', async () => {
    await request(app).delete('/api/addresses/2');
    const res = await request(app).delete('/api/addresses/2');

    expect(res.status).toBe(404);
  });
});
