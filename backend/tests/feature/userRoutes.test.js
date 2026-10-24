/**
 * Feature tests — user administration routes (routes/user.routes.js).
 *
 * Runs the router on a bare Express app with the REAL auth middleware
 * (jsonwebtoken + protect + authorize) and an in-memory User double from
 * tests/helpers/sequelizeFakes.js. The double is wrapped so that
 * `attributes: { exclude: [...] }` behaves like Sequelize (the excluded column
 * is really hidden from the instance and from toJSON), otherwise a test could
 * "pass" while a route leaked the password hash.
 */
import express from 'express';
import request from 'supertest';
import jwt from 'jsonwebtoken';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const SECRET = 'user-routes-test-secret';
const DEFAULT_SCOPE_EXCLUDE = [
  'password',
  'verificationToken',
  'verificationExpires',
  'resetPasswordToken',
  'resetPasswordExpires',
];

const userRows = [];
const User = createFakeModel('User', userRows);

// ── Sequelize attribute-exclusion fidelity ────────────────────────────────
function hideKeys(instance, keys) {
  if (!instance || typeof instance !== 'object') return instance;
  const hidden = new Set(keys);
  if (typeof instance.toJSON !== 'function') {
    const copy = { ...instance };
    for (const key of keys) delete copy[key];
    return copy;
  }
  const plain = () => {
    const out = instance.toJSON();
    for (const key of keys) delete out[key];
    return out;
  };
  return new Proxy(instance, {
    get(target, prop) {
      if (prop === 'toJSON' || prop === 'get') return plain;
      if (hidden.has(prop)) return undefined;
      return Reflect.get(target, prop);
    },
    has(target, prop) {
      return !hidden.has(prop) && Reflect.has(target, prop);
    },
  });
}

function withAttributeFidelity(model, defaultExclude) {
  const keysFor = (options) => {
    const requested = options && options.attributes && options.attributes.exclude;
    return requested || defaultExclude;
  };
  const wrapped = { ...model };

  for (const method of ['findOne', 'findAll', 'findAndCountAll', 'findByPk']) {
    wrapped[method] = async (...args) => {
      const options = method === 'findByPk' ? args[1] : args[0];
      const result = await model[method](...args);
      const keys = keysFor(options);
      if (!keys || !keys.length) return result;
      if (method === 'findAndCountAll') {
        return { count: result.count, rows: result.rows.map((r) => hideKeys(r, keys)) };
      }
      if (Array.isArray(result)) return result.map((r) => hideKeys(r, keys));
      return result ? hideKeys(result, keys) : result;
    };
  }
  return wrapped;
}

const UserDouble = withAttributeFidelity(User, DEFAULT_SCOPE_EXCLUDE);

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

const { default: userRoutes } = await import('../../routes/user.routes.js');

const app = express();
app.use(express.json());
app.use('/api/users', userRoutes);
app.use((err, _req, res, _next) => {
  res.status(500).json({ success: false, error: 'Internal error', message: err.message });
});

// ── fixtures ──────────────────────────────────────────────────────────────
function seedUser(overrides = {}) {
  const row = {
    id: userRows.length + 1,
    name: 'Seed User',
    email: `user${userRows.length + 1}@example.test`,
    password: 'hashed-secret',
    role: 'user',
    isActive: true,
    isVerified: false,
    betaStatus: 'active',
    avatar: '',
    phone: null,
    address: null,
    preferences: {},
    current_org_id: null,
    verificationToken: null,
    resetPasswordToken: null,
    createdAt: new Date('2026-01-01T00:00:00.000Z'),
    updatedAt: new Date('2026-01-02T00:00:00.000Z'),
    ...overrides,
  };
  row.get = () => {
    const { password, ...safe } = row;
    return { ...safe };
  };
  userRows.push(row);
  return row;
}

function token(id) {
  return `Bearer ${jwt.sign({ id }, SECRET, { algorithm: 'HS256', expiresIn: '15m' })}`;
}

const auth = (id) => ({ set: undefined, tokenFor: token(id) });
void auth;

let currentActor = null;

function call(method, path, { id = 1, query, bodyData } = {}) {
  currentActor = id;
  let agent = request(app)[method](path);
  if (query) agent = agent.query(query);
  if (id !== null) agent = agent.set('Authorization', token(id));
  if (bodyData !== undefined) agent = agent.send(bodyData);
  return agent;
}

const optionsFor = (method) => User.calls.filter((c) => c.method === method).map((c) => c.options || c);
const row = (id) => userRows.find((u) => u.id === id);
/** Values actually handed to an instance update (recorded by the fake). */
const instanceUpdates = () =>
  User.calls.filter((c) => c.method === 'update' && c.options && 'values' in c.options).map((c) => c.options);

/**
 * `protect()` always issues the request's very first model call (a `findByPk`
 * for the bearer). Drop that probe so the assertions below describe what the
 * route handler itself did, not what authentication did.
 */
function routeCalls() {
  const [first] = User.calls;
  const isAuthProbe =
    first &&
    first.method === 'findByPk' &&
    String(first.options?.where?.id) === String(currentActor) &&
    first.options?.attributes?.exclude?.join() === 'password';
  return isAuthProbe ? User.calls.slice(1) : User.calls;
}

beforeEach(() => {
  process.env.JWT_SECRET = SECRET;
  userRows.length = 0;
  User.calls.length = 0;
  logLines.length = 0;

  seedUser({ id: 1, name: 'Ada Admin', email: 'ada@example.test', role: 'admin' });
  seedUser({ id: 2, name: 'Vera Vendor', email: 'vera@example.test', role: 'vendor' });
  seedUser({ id: 3, name: 'Sam Searchable', email: 'sam@example.test', betaStatus: 'waitlist' });
  seedUser({ id: 4, name: 'Lea User', email: 'lea@example.test', betaStatus: 'waitlist' });
  seedUser({ id: 5, name: 'Dee Denied', email: 'dee@example.test', betaStatus: 'denied' });
});

afterEach(() => {
  delete process.env.JWT_SECRET;
});

// ── waitlist ──────────────────────────────────────────────────────────────

describe('GET /api/users/waitlist', () => {
  it('returns only waitlisted users with the password excluded from the query', async () => {
    const res = await call('get', '/api/users/waitlist', { id: 1 });

    expect(res.status).toBe(200);
    const options = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(options.where).toEqual({ betaStatus: 'waitlist' });
    expect(options.attributes.exclude).toContain('password');
    expect(res.body.data.total).toBe(2);
    expect(res.body.data.users.map((u) => u.id)).toEqual([3, 4]);
    expect(JSON.stringify(res.body)).not.toContain('hashed-secret');
  });

  it.each([2, 3])('rejects non-admin user id %s with 403', async (id) => {
    const res = await call('get', '/api/users/waitlist', { id });
    expect(res.status).toBe(403);
    expect(res.body.error).toContain('is not authorized');
    expect(routeCalls()).toHaveLength(0);
  });

  it('401s an anonymous caller', async () => {
    const res = await call('get', '/api/users/waitlist', { id: null });
    expect(res.status).toBe(401);
  });
});

describe('POST /api/users/:id/approve-waitlist', () => {
  it('flips the target betaStatus to active', async () => {
    const res = await call('post', '/api/users/3/approve-waitlist', { id: 1 });

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({ id: 3 });
    expect(instanceUpdates()).toEqual([{ where: { id: 3 }, values: { betaStatus: 'active' }, options: undefined }]);
    expect(row(3).betaStatus).toBe('active');
  });

  it('404s for an unknown user and writes nothing', async () => {
    const res = await call('post', '/api/users/999/approve-waitlist', { id: 1 });

    expect(res.status).toBe(404);
    expect(res.body.error).toBe('User not found');
    expect(instanceUpdates()).toHaveLength(0);
  });

  it('approves an already-active user — no waitlist precondition is checked', async () => {
    const res = await call('post', '/api/users/5/approve-waitlist', { id: 1 });

    // Documents current behaviour: a "denied" account can be re-activated by id.
    expect(res.status).toBe(200);
    expect(row(5).betaStatus).toBe('active');
  });

  it('rejects a vendor and the user themselves', async () => {
    const vendor = await call('post', '/api/users/3/approve-waitlist', { id: 2 });
    expect(vendor.status).toBe(403);
    const self = await call('post', '/api/users/3/approve-waitlist', { id: 3 });
    expect(self.status).toBe(403);
    expect(row(3).betaStatus).toBe('waitlist');
  });
});

// ── listing ───────────────────────────────────────────────────────────────

describe('GET /api/users', () => {
  it('paginates with sane defaults', async () => {
    const res = await call('get', '/api/users', { id: 1 });

    expect(res.status).toBe(200);
    const options = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(options).toMatchObject({ where: {}, limit: 10, offset: 0 });
    expect(options.attributes.exclude).toContain('password');
    expect(res.body).toMatchObject({
      success: true,
      count: 5,
      total: 5,
      pagination: { page: 1, limit: 10, pages: 1 },
    });
  });

  it('honours page/limit and computes the page count', async () => {
    const res = await call('get', '/api/users', { id: 1, query: { page: 2, limit: 2 } });

    const options = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(options.limit).toBe(2);
    expect(options.offset).toBe(2);
    expect(res.body.data.map((u) => u.id)).toEqual([3, 4]);
    expect(res.body.pagination).toEqual({ page: 2, limit: 2, pages: 3 });
    expect(res.body.count).toBe(2);
  });

  it('filters by role, passing the raw query value into the where', async () => {
    const res = await call('get', '/api/users', { id: 1, query: { role: 'vendor' } });

    expect(User.calls.find((c) => c.method === 'findAndCountAll').options.where).toEqual({ role: 'vendor' });
    expect(res.body.data.map((u) => u.id)).toEqual([2]);

    const junk = await call('get', '/api/users', { id: 1, query: { role: 'not-a-role' } });
    expect(junk.status).toBe(200);
    expect(junk.body.data).toEqual([]);
  });

  it('searches name and email case-insensitively through Op.or/iLike', async () => {
    const res = await call('get', '/api/users', { id: 1, query: { search: 'SEARCH' } });

    const { where } = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(where[Op.or]).toEqual([
      { name: { [Op.iLike]: '%SEARCH%' } },
      { email: { [Op.iLike]: '%SEARCH%' } },
    ]);
    expect(res.body.data.map((u) => u.id)).toEqual([3]);
  });

  it('combines role and search filters', async () => {
    const res = await call('get', '/api/users', { id: 1, query: { role: 'user', search: 'lea' } });

    const { where } = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(where.role).toBe('user');
    expect(where[Op.or]).toHaveLength(2);
    expect(res.body.data.map((u) => u.id)).toEqual([4]);
  });

  it('lets a VENDOR read the whole account directory with no tenant filter (SECURITY GAP)', async () => {
    const res = await call('get', '/api/users', { id: 2, query: { limit: '1000' } });

    // Documents current behaviour: authorize('admin','vendor') + where {} —
    // every account (email/phone/address of other tenants) is enumerable.
    expect(res.status).toBe(200);
    const options = User.calls.find((c) => c.method === 'findAndCountAll').options;
    expect(options.where).toEqual({});
    expect(options.limit).toBe(1000);
    expect(res.body.data.map((u) => u.email)).toEqual([
      'ada@example.test',
      'vera@example.test',
      'sam@example.test',
      'lea@example.test',
      'dee@example.test',
    ]);
    expect(JSON.stringify(res.body)).not.toContain('hashed-secret');
  });

  it.each([3, 4])('rejects role %s with 403', async (id) => {
    const res = await call('get', '/api/users', { id });
    expect(res.status).toBe(403);
  });

  it('401s without a token', async () => {
    const res = await call('get', '/api/users', { id: null });
    expect(res.status).toBe(401);
  });
});

// ── single user ───────────────────────────────────────────────────────────

describe('GET /api/users/:id', () => {
  it('lets a user read their own profile without the password', async () => {
    const res = await call('get', '/api/users/3', { id: 3 });

    expect(res.status).toBe(200);
    expect(res.body.data).toMatchObject({ id: 3, email: 'sam@example.test', role: 'user' });
    expect(res.body.data.password).toBeUndefined();
    const options = routeCalls().find((c) => c.method === 'findByPk').options;
    expect(options.attributes.exclude).toContain('password');
    expect(options.where).toEqual({ id: 3 });
  });

  it('authenticates with exactly one bearer lookup before the handler reads', async () => {
    await call('get', '/api/users/3', { id: 3 });
    // Guards the routeCalls() assumption: calls[0] is protect()'s probe.
    expect(User.calls.map((c) => c.method)).toEqual(['findByPk', 'findByPk']);
    expect(User.calls[0].options.where).toEqual({ id: 3 });
  });

  it('403s when a non-admin asks for someone else', async () => {
    const res = await call('get', '/api/users/1', { id: 3 });

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Not authorized to access this user');
    // the guard runs before the handler reads anything
    expect(routeCalls()).toHaveLength(0);
  });

  it('lets an admin read anyone', async () => {
    const res = await call('get', '/api/users/4', { id: 1 });
    expect(res.status).toBe(200);
    expect(res.body.data.id).toBe(4);
  });

  it('404s for an unknown id requested by an admin', async () => {
    const res = await call('get', '/api/users/999', { id: 1 });
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('User not found');
  });

  it('treats a non-numeric id as "someone else" (403) for a normal user', async () => {
    const res = await call('get', '/api/users/abc', { id: 3 });

    expect(res.status).toBe(403);
    expect(routeCalls()).toHaveLength(0);
  });

  it('404s a non-numeric id requested by an admin instead of 400', async () => {
    const res = await call('get', '/api/users/abc', { id: 1 });

    // parseInt('abc') is NaN and is handed straight to findByPk.
    expect(res.status).toBe(404);
    expect(routeCalls().find((c) => c.method === 'findByPk').options.where).toEqual({ id: NaN });
  });
});

// ── creation ──────────────────────────────────────────────────────────────

describe('POST /api/users', () => {
  it('creates a user with a normalized email and the default role', async () => {
    const res = await call('post', '/api/users', {
      id: 1,
      bodyData: { name: ' Nina New ', email: 'Nina@Example.test', password: 'hunter22' },
    });

    expect(res.status).toBe(201);
    const created = User.calls.find((c) => c.method === 'create').options.values;
    expect(created).toMatchObject({
      // the `.trim()` sanitizer mutates req.body before the handler reads it
      name: 'Nina New',
      email: 'nina@example.test',
      password: 'hunter22',
      role: 'user',
      phone: null,
    });
    expect(res.body.data.password).toBeUndefined();
    expect(JSON.stringify(res.body)).not.toContain('hashed-secret');
    expect(logLines.join('\n')).toContain('Admin created user: nina@example.test');
  });

  it('rejects a duplicate email (case-insensitively, after normalization)', async () => {
    const res = await call('post', '/api/users', {
      id: 1,
      bodyData: { name: 'Copy', email: 'ADA@example.test', password: 'hunter22' },
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('User with this email already exists');
    expect(User.calls.find((c) => c.method === 'findOne').options.where).toEqual({
      email: 'ada@example.test',
    });
    expect(User.calls.filter((c) => c.method === 'create')).toHaveLength(0);
  });

  it('reports every validation failure at once', async () => {
    const res = await call('post', '/api/users', {
      id: 1,
      bodyData: { name: '', email: 'nope', password: '123' },
    });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.msg)).toEqual(
      expect.arrayContaining(['Name is required', 'Valid email is required', 'Password must be at least 6 characters']),
    );
    expect(routeCalls()).toHaveLength(0);
  });

  it('passes an arbitrary role straight to the model (no HTTP-layer whitelist)', async () => {
    const res = await call('post', '/api/users', {
      id: 1,
      bodyData: { name: 'God', email: 'god@example.test', password: 'hunter22', role: 'superuser' },
    });

    // Documents current behaviour: role is unvalidated at the route; the model
    // isIn validator is what rejects it (a 500 in production, not a 400).
    expect(res.status).toBe(201);
    expect(User.calls.find((c) => c.method === 'create').options.values.role).toBe('superuser');
  });

  it.each([2, 3])('rejects non-admin id %s with 403', async (id) => {
    const res = await call('post', '/api/users', {
      id,
      bodyData: { name: 'X', email: 'x@example.test', password: 'hunter22' },
    });
    expect(res.status).toBe(403);
    expect(routeCalls()).toHaveLength(0);
  });

  it('a plain user cannot self-promote by creating an admin account', async () => {
    const res = await call('post', '/api/users', {
      id: 3,
      bodyData: { name: 'Me', email: 'me2@example.test', password: 'hunter22', role: 'admin' },
    });
    expect(res.status).toBe(403);
    expect(row(3).role).toBe('user');
  });
});

// ── update ────────────────────────────────────────────────────────────────

describe('PUT /api/users/:id', () => {
  it('lets a user update their own profile fields', async () => {
    const res = await call('put', '/api/users/3', {
      id: 3,
      bodyData: { name: 'Sam New', phone: '+1 555', avatar: 'https://cdn/a.png', address: '1 Main St' },
    });

    expect(res.status).toBe(200);
    const [update] = instanceUpdates();
    expect(update.where).toEqual({ id: 3 });
    expect(update.values).toMatchObject({ name: 'Sam New', phone: '+1 555' });
    expect(row(3).name).toBe('Sam New');
    expect(res.body.data.password).toBeUndefined();
  });

  it('ignores role, isActive, isVerified and email when the caller is not an admin', async () => {
    const res = await call('put', '/api/users/3', {
      id: 3,
      bodyData: { name: 'Sam', role: 'admin', isActive: false, isVerified: true, email: 'evil@x.test' },
    });

    expect(res.status).toBe(200);
    expect(instanceUpdates()[0].values).toEqual({ name: 'Sam' });
    expect(row(3)).toMatchObject({ role: 'user', isActive: true, isVerified: false, email: 'sam@example.test' });
  });

  it('applies privileged fields for an admin editing someone else', async () => {
    const res = await call('put', '/api/users/4', {
      id: 1,
      bodyData: { role: 'vendor', isActive: false, isVerified: true, betaStatus: 'denied' },
    });

    expect(res.status).toBe(200);
    expect(instanceUpdates()[0].values).toEqual({
      role: 'vendor',
      isActive: false,
      isVerified: true,
      betaStatus: 'denied',
    });
    expect(row(4)).toMatchObject({ role: 'vendor', isActive: false, betaStatus: 'denied' });
    expect(res.body.data.password).toBeUndefined();
  });

  it('403s a non-admin editing someone else and writes nothing', async () => {
    const res = await call('put', '/api/users/4', { id: 3, bodyData: { name: 'Hacked' } });

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Not authorized to update this user');
    expect(instanceUpdates()).toHaveLength(0);
    expect(row(4).name).toBe('Lea User');
  });

  it('404s for an unknown target', async () => {
    const res = await call('put', '/api/users/999', { id: 1, bodyData: { name: 'Ghost' } });

    expect(res.status).toBe(404);
    expect(res.body.error).toBe('User not found');
    expect(instanceUpdates()).toHaveLength(0);
  });

  it('accepts an empty body as a no-op success', async () => {
    const res = await call('put', '/api/users/3', { id: 3, bodyData: { unknownField: 'x' } });

    expect(res.status).toBe(200);
    expect(instanceUpdates()[0].values).toEqual({});
  });

  it('stores unvalidated values as-is (no type or length checks)', async () => {
    const res = await call('put', '/api/users/3', {
      id: 3,
      bodyData: { name: { nested: 'object' }, preferences: { anything: [1, 2, 3] }, phone: 12345 },
    });

    // Documents current behaviour: PUT has no express-validator chain at all.
    expect(res.status).toBe(200);
    expect(instanceUpdates()[0].values).toEqual({
      name: { nested: 'object' },
      phone: 12345,
      preferences: { anything: [1, 2, 3] },
    });
  });

  it('401s an anonymous caller', async () => {
    const res = await call('put', '/api/users/3', { id: null, bodyData: { name: 'X' } });
    expect(res.status).toBe(401);
  });
});

// ── deletion ──────────────────────────────────────────────────────────────

describe('DELETE /api/users/:id', () => {
  it('removes the user for an admin', async () => {
    const res = await call('delete', '/api/users/4', { id: 1 });

    expect(res.status).toBe(200);
    expect(row(4)).toBeUndefined();
    expect(logLines.join('\n')).toContain('Admin deleted user: lea@example.test (4)');
  });

  it('404s for an unknown id', async () => {
    const res = await call('delete', '/api/users/999', { id: 1 });
    expect(res.status).toBe(404);
    expect(userRows).toHaveLength(5);
  });

  it.each([2, 3, 4])('rejects non-admin id %s with 403', async (id) => {
    const res = await call('delete', `/api/users/${id === 3 ? 4 : id}`, { id });
    expect(res.status).toBe(403);
    expect(userRows.length).toBeGreaterThan(0);
  });

  it('lets an admin delete themselves — no self or last-admin guard (SECURITY GAP)', async () => {
    const res = await call('delete', '/api/users/1', { id: 1 });

    // Documents current behaviour: the only admin account can be removed,
    // leaving nobody who can administer the system.
    expect(res.status).toBe(200);
    expect(row(1)).toBeUndefined();
    expect(userRows.filter((u) => u.role === 'admin')).toHaveLength(0);
  });

  it('refuses a deleted admin token afterwards', async () => {
    await call('delete', '/api/users/1', { id: 1 });
    const res = await call('get', '/api/users/waitlist', { id: 1 });
    expect(res.status).toBe(401);
  });
});

// ── status toggle ─────────────────────────────────────────────────────────

describe('PATCH /api/users/:id/status', () => {
  it('deactivates an account and blocks its token', async () => {
    const res = await call('patch', '/api/users/3/status', { id: 1, bodyData: { isActive: false } });

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('User account deactivated');
    expect(instanceUpdates()[0].values).toEqual({ isActive: false });
    const followUp = await call('get', '/api/users/3', { id: 3 });
    expect(followUp.status).toBe(401);
    expect(followUp.body.error).toBe('User account is deactivated');
  });

  it('activates an account', async () => {
    row(3).isActive = false;
    const res = await call('patch', '/api/users/3/status', { id: 1, bodyData: { isActive: true } });

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('User account activated');
    expect(row(3).isActive).toBe(true);
  });

  it('deactivates when the isActive key is missing or misnamed (SILENT DATA LOSS)', async () => {
    const typo = await call('patch', '/api/users/3/status', { id: 1, bodyData: { active: true } });
    expect(typo.status).toBe(200);
    expect(typo.body.message).toBe('User account deactivated');
    expect(row(3).isActive).toBe(false);

    const empty = await call('patch', '/api/users/4/status', { id: 1, bodyData: {} });
    expect(empty.body.message).toBe('User account deactivated');
    expect(row(4).isActive).toBe(false);
  });

  it('coerces any truthy value, so isActive="false" activates the account', async () => {
    row(3).isActive = false;
    const res = await call('patch', '/api/users/3/status', { id: 1, bodyData: { isActive: 'false' } });

    expect(res.body.message).toBe('User account activated');
    expect(row(3).isActive).toBe(true);
  });

  it('404s for an unknown user and 403s a non-admin', async () => {
    const missing = await call('patch', '/api/users/999/status', { id: 1, bodyData: { isActive: false } });
    expect(missing.status).toBe(404);

    const forbidden = await call('patch', '/api/users/1/status', { id: 3, bodyData: { isActive: false } });
    expect(forbidden.status).toBe(403);
    expect(row(1).isActive).toBe(true);
  });

  it('a vendor cannot disable the admin', async () => {
    const res = await call('patch', '/api/users/1/status', { id: 2, bodyData: { isActive: false } });
    expect(res.status).toBe(403);
    expect(row(1).isActive).toBe(true);
  });
});

// ── preferences ───────────────────────────────────────────────────────────

describe('PUT /api/users/:id/preferences', () => {
  it('merges theme, language and notifications into the existing object', async () => {
    row(3).preferences = { theme: 'light', custom: 'keep', notifications: { email: true } };
    const res = await call('put', '/api/users/3/preferences', {
      id: 3,
      bodyData: { theme: 'dark', notifications: { push: false } },
    });

    expect(res.status).toBe(200);
    expect(res.body.preferences).toEqual({
      theme: 'dark',
      custom: 'keep',
      notifications: { email: true, push: false },
    });
    expect(instanceUpdates()[0].values).toEqual({
      preferences: { theme: 'dark', custom: 'keep', notifications: { email: true, push: false } },
    });
  });

  it('treats falsy values as "not provided" and leaves the stored object alone', async () => {
    row(3).preferences = { theme: 'light' };
    const res = await call('put', '/api/users/3/preferences', {
      id: 3,
      bodyData: { theme: '', language: 0, notifications: null },
    });

    expect(res.status).toBe(200);
    expect(res.body.preferences).toEqual({ theme: 'light' });
  });

  it('starts from an empty preferences object', async () => {
    row(3).preferences = null;
    const res = await call('put', '/api/users/3/preferences', { id: 3, bodyData: { language: 'fr' } });
    expect(res.body.preferences).toEqual({ language: 'fr' });
  });

  it('builds a notifications object when the stored preferences have none', async () => {
    row(3).preferences = null;
    const res = await call('put', '/api/users/3/preferences', {
      id: 3,
      bodyData: { notifications: { push: true } },
    });

    expect(res.body.preferences).toEqual({ notifications: { push: true } });
    expect(instanceUpdates()[0].values).toEqual({ preferences: { notifications: { push: true } } });
    expect(instanceUpdates()[0].where).toEqual({ id: 3 });
  });

  it('403s another user from writing preferences and writes nothing', async () => {
    const res = await call('put', '/api/users/1/preferences', { id: 3, bodyData: { theme: 'dark' } });

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Not authorized');
    expect(instanceUpdates()).toHaveLength(0);
    expect(row(1).preferences).toEqual({});
  });

  it('lets an admin write another user preferences', async () => {
    const res = await call('put', '/api/users/4/preferences', { id: 1, bodyData: { theme: 'light' } });

    expect(res.status).toBe(200);
    expect(instanceUpdates()[0].where).toEqual({ id: 4 });
    expect(row(4).preferences).toEqual({ theme: 'light' });
  });

  it('404s for an unknown target', async () => {
    const res = await call('put', '/api/users/999/preferences', { id: 1, bodyData: { theme: 'dark' } });
    expect(res.status).toBe(404);
  });

  it('401s an anonymous caller', async () => {
    const res = await call('put', '/api/users/3/preferences', { id: null, bodyData: { theme: 'dark' } });
    expect(res.status).toBe(401);
  });
});

// ── error handling ────────────────────────────────────────────────────────

describe('error handling', () => {
  /** Make `UserDouble[method]` reject, after the first `skip` calls succeed. */
  function failOn(method, skip = 0) {
    const original = UserDouble[method];
    let hits = 0;
    UserDouble[method] = async (...args) => {
      hits += 1;
      // the first findByPk is protect()'s bearer lookup — it must keep working,
      // otherwise the request never reaches the route under test.
      if (hits <= skip) return original(...args);
      throw new Error('connection reset');
    };
    return () => {
      UserDouble[method] = original;
    };
  }

  it.each([
    ['get', '/api/users/waitlist', 1, 'findAndCountAll', 0, undefined],
    ['post', '/api/users/3/approve-waitlist', 1, 'findByPk', 1, undefined],
    ['get', '/api/users', 1, 'findAndCountAll', 0, undefined],
    ['post', '/api/users', 1, 'findOne', 0, { name: 'X', email: 'x@example.test', password: 'hunter22' }],
    ['get', '/api/users/3', 3, 'findByPk', 1, undefined],
    ['put', '/api/users/3', 1, 'findByPk', 1, { name: 'Boom' }],
    ['delete', '/api/users/3', 1, 'findByPk', 1, undefined],
    ['patch', '/api/users/3/status', 1, 'findByPk', 1, { isActive: false }],
    ['put', '/api/users/3/preferences', 1, 'findByPk', 1, { theme: 'dark' }],
  ])('%s %s forwards a database failure as 500', async (method, path, id, dbMethod, skip, bodyData) => {
    const restore = failOn(dbMethod, skip);
    try {
      const res = await call(method, path, { id, bodyData });

      expect(res.status).toBe(500);
      expect(res.body.success).toBe(false);
      expect(res.body.error).toBe('Internal error');
      expect(JSON.stringify(res.body)).not.toContain('SELECT');
      expect(res.body.message).toBe('connection reset');
    } finally {
      restore();
    }
  });

  it('writes nothing when the account lookup behind a delete fails', async () => {
    const restore = failOn('findByPk', 1);
    try {
      const res = await call('delete', '/api/users/3', { id: 1 });
      expect(res.status).toBe(500);
      expect(row(3).name).toBe('Sam Searchable');
      expect(instanceUpdates()).toEqual([]);
    } finally {
      restore();
    }
  });

  it('propagates a failing instance update instead of answering 200', async () => {
    const original = UserDouble.findByPk;
    let hits = 0;
    UserDouble.findByPk = async (...args) => {
      hits += 1;
      const instance = await original(...args);
      if (hits === 1 || !instance) return instance;
      return { ...instance, update: () => Promise.reject(new Error('deadlock detected')) };
    };
    try {
      const res = await call('patch', '/api/users/3/status', { id: 1, bodyData: { isActive: false } });

      expect(res.status).toBe(500);
      expect(row(3).isActive).toBe(true);
    } finally {
      UserDouble.findByPk = original;
    }
  });
});
