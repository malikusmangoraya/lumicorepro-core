/**
 * Feature tests — multi-tenant organisation routes (routes/org.routes.js).
 *
 * The router is mounted on a bare Express app with the REAL auth + RBAC
 * middleware and the REAL rbac service running on in-memory Sequelize doubles
 * (tests/helpers/sequelizeFakes.js). Nothing in the tenancy path is mocked
 * away: `protect` verifies a genuine HS256 token, `requireOrg` resolves the
 * org from `x-org-id`, `getMembership` loads the membership with its role, and
 * every query records the exact `where` it carried — so these tests assert the
 * tenant filter, not just the status code.
 */
import express from 'express';
import request from 'supertest';
import jwt from 'jsonwebtoken';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { createFakeModel, matchesWhere } from '../helpers/sequelizeFakes.js';

const SECRET = 'org-routes-test-secret';
const ALL_CODES = [
  'org.view',
  'org.manage',
  'org.members.manage',
  'products.manage',
  'orders.view',
  'analytics.view',
];
const MEMBER_CODES = ['org.view', 'orders.view', 'analytics.view'];

// ── backing stores (contents replaced by seed() before every test) ─────────
const orgRows = [];
const userRows = [];
const membershipRows = [];
const roleRows = [];
const permissionRows = [];
const auditRows = [];
const queueJobs = [];

const Organization = createFakeModel('Organization', orgRows, { paranoidField: 'deleted_at' });
const User = createFakeModel('User', userRows);
const Membership = createFakeModel('Membership', membershipRows);
const Role = createFakeModel('Role', roleRows);
const Permission = createFakeModel('Permission', permissionRows);
const AuditLog = createFakeModel('AuditLog', auditRows);

// ── instance/behaviour extensions the shared helper does not provide ───────
/** `row.get({plain:true})` — what protect() reads. Password-free like the model scope. */
function decorateUser(row) {
  if (!row.get) {
    row.get = () => {
      const { password, ...safe } = row;
      return { ...safe };
    };
  }
  return row;
}

/** Role rows behave like Sequelize instances with a belongsToMany accessor. */
function decorateRole(row) {
  if (row.__decorated) return row;
  row.__decorated = true;
  if (!Array.isArray(row.permissions)) row.permissions = [];
  row.setPermissions = async (perms) => {
    row.permissions = (perms || []).map((p) => (p && typeof p.toJSON === 'function' ? p.toJSON() : { ...p }));
    return row;
  };
  return row;
}

/** Membership rows resolve `role`/`organization` live (stands in for the include). */
function decorateMembership(row) {
  if (row.__decorated) return row;
  row.__decorated = true;
  Object.defineProperty(row, 'role', {
    configurable: true,
    enumerable: false,
    get() {
      return roleRows.find((r) => String(r.id) === String(row.role_id)) || null;
    },
  });
  Object.defineProperty(row, 'organization', {
    configurable: true,
    enumerable: false,
    get() {
      return orgRows.find((o) => String(o.id) === String(row.org_id)) || null;
    },
  });
  return row;
}

function instanceOf(model, row, { paranoidField = null } = {}) {
  const inst = {
    _row: row,
    toJSON: () => ({ ...row }),
    update: async (values) => {
      model.calls.push({ method: 'update', options: { where: { id: row.id }, values } });
      Object.assign(row, values);
      return inst;
    },
    destroy: async () => {
      if (paranoidField) row[paranoidField] = new Date();
      return inst;
    },
  };
  return new Proxy(inst, {
    get: (target, prop) => (prop in target ? target[prop] : row[prop]),
    has: (target, prop) => prop in target || prop in row,
  });
}

/** Sequelize `findOrCreate` for the fake models the routes rely on. */
function addFindOrCreate(model, rows, { decorate = null, paranoidField = null } = {}) {
  const originalCreate = model.create;
  model.create = async (values = {}, options = {}) => {
    const created = await originalCreate(values, options);
    if (decorate) decorate(created._row);
    return created;
  };
  model.findOrCreate = async (options = {}) => {
    model.calls.push({ method: 'findOrCreate', options });
    const { where = {}, defaults = {} } = options;
    const visible = rows.filter(
      (r) => !paranoidField || r[paranoidField] === null || r[paranoidField] === undefined,
    );
    const hit = visible.find((r) => matchesWhere(r, where));
    if (hit) {
      if (decorate) decorate(hit);
      return [instanceOf(model, hit, { paranoidField }), false];
    }
    const created = await model.create({ ...defaults, ...where });
    return [created, true];
  };
  return model;
}

addFindOrCreate(Membership, membershipRows, { decorate: decorateMembership });
addFindOrCreate(Role, roleRows, { decorate: decorateRole });
addFindOrCreate(Permission, permissionRows);
addFindOrCreate(Organization, orgRows, { paranoidField: 'deleted_at' });

/** User.scope('withPassword').findOne(...) — used by findUserByEmail(). */
User.scope = (name) => ({
  findOne: (options = {}) => {
    User.calls.push({ method: `scope:${name}.findOne`, options });
    return User.findOne(options);
  },
});

// ── mocks (registered before the router is imported) ───────────────────────
const noop = () => {};
const fakeLogger = {
  info: noop,
  warn: noop,
  error: noop,
  debug: noop,
  http: noop,
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: fakeLogger,
  withRequestId: () => fakeLogger,
  redact: (value) => value,
}));

jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  QUEUES: { EMAIL: 'lh-email', REPORT: 'lh-report' },
  enqueue: async (name, payload) => {
    queueJobs.push({ name, payload });
    return { jobId: 'job-1', fallback: false };
  },
}));

jest.unstable_mockModule('../../models/Organization.js', () => ({
  __esModule: true,
  default: Organization,
}));
jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: User }));
jest.unstable_mockModule('../../models/Membership.js', () => ({
  __esModule: true,
  default: Membership,
}));
jest.unstable_mockModule('../../models/Role.js', () => ({ __esModule: true, default: Role }));
jest.unstable_mockModule('../../models/Permission.js', () => ({
  __esModule: true,
  default: Permission,
}));
jest.unstable_mockModule('../../models/AuditLog.js', () => ({ __esModule: true, default: AuditLog }));

const { default: orgRoutes } = await import('../../routes/org.routes.js');

const app = express();
app.use(express.json());
app.use('/api/orgs', orgRoutes);
app.use((err, _req, res, _next) => {
  res.status(500).json({ success: false, error: 'Internal error', message: err.message });
});

// ── fixtures ──────────────────────────────────────────────────────────────
function permission(code) {
  return { id: permissionRows.length + 1, code, name: code, description: code };
}

function seedRole(orgId, name, id, codes) {
  const row = decorateRole({
    id,
    org_id: orgId,
    name,
    description: `System ${name} role`,
    is_system: true,
    permissions: codes.map((code) => permissionRows.find((p) => p.code === code)).filter(Boolean),
  });
  roleRows.push(row);
  return row;
}

function seedMembership(orgId, userId, roleId, status = 'active') {
  const row = decorateMembership({
    id: membershipRows.length + 1,
    org_id: orgId,
    user_id: userId,
    role_id: roleId,
    status,
    invited_by: null,
    joined_at: status === 'active' ? new Date('2026-01-01T00:00:00.000Z') : null,
  });
  membershipRows.push(row);
  return row;
}

function seedUser(id, name, email, extra = {}) {
  const row = decorateUser({
    id,
    name,
    email,
    password: 'hashed-secret',
    role: 'user',
    isActive: true,
    current_org_id: null,
    ...extra,
  });
  userRows.push(row);
  return row;
}

function inviteToken(payload, options = {}) {
  return jwt.sign({ purpose: 'org_invite', ...payload }, SECRET, {
    algorithm: 'HS256',
    expiresIn: '7d',
    ...options,
  });
}

/** Bearer token for a seeded user, as protect() expects. */
function as(id) {
  return `Bearer ${jwt.sign({ id }, SECRET, { algorithm: 'HS256', expiresIn: '15m' })}`;
}

function optionsFor(model, method) {
  return model.calls.filter((c) => c.method === method).map((c) => c.options);
}

/** Every recorded membership write (create/update/destroy/findOrCreate). */
function membershipWrites() {
  return Membership.calls.filter((c) => ['create', 'update', 'destroy', 'findOrCreate'].includes(c.method));
}

function callsMatching(model, method, subset) {
  return optionsFor(model, method).filter((o) =>
    Object.entries(subset).every(([key, value]) => String(o.where?.[key]) === String(value)),
  );
}

function seed() {
  for (const store of [orgRows, userRows, membershipRows, roleRows, permissionRows, auditRows, queueJobs]) {
    store.length = 0;
  }
  for (const model of [Organization, User, Membership, Role, Permission, AuditLog]) model.calls.length = 0;

  ALL_CODES.forEach((code) => permissionRows.push(permission(code)));

  // org 1 = Acme (caller's org), org 2 = Globex (foreign tenant), org 3 = deleted
  orgRows.push(
    { id: 1, name: 'Acme', slug: 'acme-1', owner_id: 1, settings: {}, deleted_at: null },
    { id: 2, name: 'Globex', slug: 'globex-2', owner_id: 50, settings: {}, deleted_at: null },
    {
      id: 3,
      name: 'Dead Co',
      slug: 'dead-3',
      owner_id: 1,
      settings: {},
      deleted_at: new Date('2026-01-01T00:00:00.000Z'),
    },
  );

  seedRole(1, 'owner', 10, ALL_CODES);
  seedRole(1, 'admin', 11, ALL_CODES);
  seedRole(1, 'member', 12, MEMBER_CODES);
  seedRole(2, 'owner', 20, ALL_CODES);
  seedRole(2, 'admin', 21, ALL_CODES);
  seedRole(2, 'member', 22, MEMBER_CODES);

  // user 1 owner of Acme · user 2 plain member · user 3 members-manager (admin role)
  // user 4 outsider · user 5 global admin holding only a member role · user 6 revoked
  seedUser(1, 'Priya Nair', 'priya@acme.test', { current_org_id: 1 });
  seedUser(2, 'Sam Bell', 'sam@acme.test', { current_org_id: 1 });
  seedUser(3, 'Ana Ruiz', 'ana@acme.test', { current_org_id: 1 });
  seedUser(4, 'Lee Vox', 'lee@globex.test', { current_org_id: 2 });
  seedUser(5, 'Root Admin', 'root@lumicore.test', { role: 'admin', current_org_id: 1 });
  seedUser(6, 'Ex Member', 'ex@acme.test', { current_org_id: null });
  seedUser(7, 'Newbie', 'newbie@outside.test', { current_org_id: null });
  seedUser(8, 'No Org', 'noorg@acme.test');

  seedMembership(1, 1, 10);
  seedMembership(1, 2, 12);
  seedMembership(1, 3, 11);
  seedMembership(2, 4, 20);
  seedMembership(1, 5, 12);
  seedMembership(1, 6, 12, 'revoked');
}

beforeEach(() => {
  process.env.JWT_SECRET = SECRET;
  process.env.FRONTEND_URL = 'https://app.test/';
  seed();
});

afterEach(() => {
  delete process.env.JWT_SECRET;
  delete process.env.FRONTEND_URL;
});

// ── public invite resolution ──────────────────────────────────────────────

describe('GET /api/orgs/invite/:token (public)', () => {
  it('resolves a valid invite without any auth header', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'Newbie@Outside.test' });
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      data: {
        orgId: 1,
        orgName: 'Acme',
        email: 'Newbie@Outside.test',
        role: 'member',
        expiresAt: expect.any(String),
      },
    });
    // tenant lookup is a plain primary-key read of the token's org only
    expect(callsMatching(Organization, 'findByPk', { id: 1 })).toHaveLength(1);
  });

  it('rejects a garbage token and issues no database query', async () => {
    const res = await request(app).get('/api/orgs/invite/not-a-jwt');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Invite is invalid or has expired' });
    expect(Organization.calls).toHaveLength(0);
  });

  it('rejects a token signed with the wrong secret', async () => {
    const token = jwt.sign(
      { purpose: 'org_invite', orgId: 1, roleId: 12, email: 'a@b.test' },
      'attacker-secret',
      { algorithm: 'HS256', expiresIn: '7d' },
    );
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(400);
    expect(Organization.calls).toHaveLength(0);
  });

  it('rejects a token whose purpose is not org_invite', async () => {
    const token = jwt.sign({ orgId: 1, roleId: 12, email: 'a@b.test' }, SECRET, {
      algorithm: 'HS256',
      expiresIn: '7d',
    });
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(400);
    expect(Organization.calls).toHaveLength(0);
  });

  it('rejects an org_invite token that points at a soft-deleted organization', async () => {
    const token = inviteToken({ orgId: 3, roleId: 12, email: 'a@b.test' });
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Invite is invalid or has expired');
  });

  it('rejects an expired invite token', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'a@b.test' }, { expiresIn: '-1s' });
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(400);
  });

  it('falls back to the member role name when the role id no longer exists', async () => {
    const token = inviteToken({ orgId: 1, roleId: 999, email: 'a@b.test' });
    const res = await request(app).get(`/api/orgs/invite/${token}`);

    expect(res.status).toBe(200);
    expect(res.body.data.role).toBe('member');
  });
});

// ── public invite acceptance ──────────────────────────────────────────────

describe('POST /api/orgs/invite/:token/accept (public)', () => {
  it('joins an existing account to the invited org and scopes every write to it', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'Newbie@Outside.test' });
    // user 7 exists with that email
    const res = await request(app)
      .post(`/api/orgs/invite/${token}/accept`)
      .send({});

    expect(res.status).toBe(201);
    expect(res.body.data.user).toEqual({ id: 7, name: 'Newbie', email: 'newbie@outside.test' });
    expect(res.body.data.org).toMatchObject({ id: 1, name: 'Acme' });

    const findOrCreate = optionsFor(Membership, 'findOrCreate');
    expect(findOrCreate).toHaveLength(1);
    expect(findOrCreate[0].where).toEqual({ org_id: 1, user_id: 7 });
    expect(findOrCreate[0].defaults).toMatchObject({
      org_id: 1,
      user_id: 7,
      role_id: 12,
      status: 'active',
      invited_by: null,
    });

    // the "active org" pointer is written to the invitee's own row only
    const userUpdates = optionsFor(User, 'update');
    expect(userUpdates).toHaveLength(1);
    expect(userUpdates[0].values).toEqual({ current_org_id: 1 });
    expect(userUpdates[0].options.where).toEqual({ id: 7 });

    const joined = membershipRows.find((m) => m.user_id === 7);
    expect(joined).toMatchObject({ org_id: 1, status: 'active', role_id: 12 });
  });

  it('registers a brand-new account when the invited email has no user', async () => {
    const token = inviteToken({ orgId: 1, roleId: 11, email: 'brand-new@outside.test' });
    const res = await request(app)
      .post(`/api/orgs/invite/${token}/accept`)
      .send({ name: '  Brand New  ', password: 'hunter22' });

    expect(res.status).toBe(201);
    const creates = optionsFor(User, 'create');
    expect(creates).toHaveLength(1);
    expect(creates[0].values).toMatchObject({
      name: 'Brand New',
      email: 'brand-new@outside.test',
      password: 'hunter22',
      isActive: true,
    });
    expect(res.body.data.user.email).toBe('brand-new@outside.test');
    expect(membershipRows.find((m) => m.org_id === 1 && m.role_id === 11)).toBeTruthy();
  });

  it('derives the display name from the email local part when name is omitted', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'derived@outside.test' });
    await request(app).post(`/api/orgs/invite/${token}/accept`).send({ password: 'hunter22' });

    expect(optionsFor(User, 'create')[0].values.name).toBe('derived');
  });

  it('refuses to create an account without a password', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'ghost@outside.test' });
    const res = await request(app).post(`/api/orgs/invite/${token}/accept`).send({ name: 'Ghost' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({
      success: false,
      error: 'Password is required to create your account',
    });
    expect(optionsFor(User, 'create')).toHaveLength(0);
    expect(membershipWrites()).toHaveLength(0);
  });

  it('rejects a weak password through the validator, before touching the db', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'weak@outside.test' });
    const res = await request(app)
      .post(`/api/orgs/invite/${token}/accept`)
      .send({ password: '123' });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(Array.isArray(res.body.errors)).toBe(true);
    expect(membershipWrites()).toHaveLength(0);
  });

  it('rejects an over-long name', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'long@outside.test' });
    const res = await request(app)
      .post(`/api/orgs/invite/${token}/accept`)
      .send({ name: 'x'.repeat(121), password: 'hunter22' });

    expect(res.status).toBe(400);
    expect(optionsFor(User, 'create')).toHaveLength(0);
  });

  it('rejects an invalid token without creating anything', async () => {
    const res = await request(app).post('/api/orgs/invite/junk/accept').send({ password: 'hunter22' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Invite is invalid or has expired' });
    expect(membershipWrites()).toHaveLength(0);
  });

  it('does not leak the invite password hash into the response', async () => {
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'leak@outside.test' });
    const res = await request(app)
      .post(`/api/orgs/invite/${token}/accept`)
      .send({ password: 'hunter22' });

    expect(res.body.data.user).not.toHaveProperty('password');
    expect(JSON.stringify(res.body)).not.toContain('hashed-secret');
  });

  it('re-activates a membership that an admin already revoked (SECURITY GAP)', async () => {
    // user 6 was revoked from org 1 but still holds the original 7-day invite token
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'ex@acme.test' });
    const res = await request(app).post(`/api/orgs/invite/${token}/accept`).send({});

    // Documents current behaviour: revocation is not honoured by the accept flow.
    expect(res.status).toBe(201);
    expect(membershipRows.find((m) => m.user_id === 6).status).toBe('active');
  });

  it('accepts an invite to a soft-deleted organization (SECURITY GAP)', async () => {
    // GET /invite/:token refuses, but POST accept never re-checks the org exists.
    const token = inviteToken({ orgId: 3, roleId: 12, email: 'newbie@outside.test' });
    const res = await request(app).post(`/api/orgs/invite/${token}/accept`).send({});

    // Documents current behaviour: membership is created against a dead tenant.
    expect(res.status).toBe(201);
    expect(res.body.data.org).toBeNull();
    expect(membershipRows.some((m) => m.org_id === 3 && m.user_id === 7)).toBe(true);
    expect(userRows.find((u) => u.id === 7).current_org_id).toBe(3);
  });
});

// ── auth boundary ─────────────────────────────────────────────────────────

describe('authentication boundary', () => {
  it.each([
    ['GET', '/api/orgs'],
    ['POST', '/api/orgs'],
    ['GET', '/api/orgs/current'],
    ['GET', '/api/orgs/permissions'],
    ['GET', '/api/orgs/roles'],
    ['GET', '/api/orgs/1/members'],
    ['PUT', '/api/orgs/1'],
    ['DELETE', '/api/orgs/1'],
    ['POST', '/api/orgs/1/select'],
    ['POST', '/api/orgs/1/members'],
    ['POST', '/api/orgs/1/members/invite'],
    ['PUT', '/api/orgs/1/members/2'],
    ['DELETE', '/api/orgs/1/members/2'],
  ])('%s %s returns 401 without a token', async (method, path) => {
    const res = await request(app)[method.toLowerCase()](path);
    expect(res.status).toBe(401);
  });

  it('returns 401 for a token signed with the wrong secret', async () => {
    const token = jwt.sign({ id: 1 }, 'nope', { algorithm: 'HS256', expiresIn: '15m' });
    const res = await request(app).get('/api/orgs').set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(401);
  });

  it('returns 401 for a token whose user no longer exists', async () => {
    const res = await request(app).get('/api/orgs').set('Authorization', as(404));
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('User not found');
  });

  it('returns 401 for a deactivated account', async () => {
    userRows.find((u) => u.id === 1).isActive = false;
    const res = await request(app).get('/api/orgs').set('Authorization', as(1));
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('User account is deactivated');
  });
});

// ── organization creation ─────────────────────────────────────────────────

describe('POST /api/orgs', () => {
  it('creates the org, binds the creator as owner and activates it', async () => {
    const res = await request(app)
      .post('/api/orgs')
      .set('Authorization', as(2))
      .send({ name: '  Nova Labs  ' });

    expect(res.status).toBe(201);
    expect(res.body.role).toBe('owner');
    expect(res.body.org.name).toBe('Nova Labs');
    expect(res.body.org.owner_id).toBe(2);
    expect(res.body.org.slug).toMatch(/^nova-labs-/);

    const created = optionsFor(Membership, 'create')[0].values;
    expect(created).toMatchObject({ org_id: res.body.org.id, user_id: 2, status: 'active' });
    const ownerRole = roleRows.find((r) => r.org_id === res.body.org.id && r.name === 'owner');
    expect(created.role_id).toBe(ownerRole.id);

    const userUpdate = optionsFor(User, 'update').slice(-1)[0];
    expect(userUpdate.values).toEqual({ current_org_id: res.body.org.id });
    expect(userUpdate.options.where).toEqual({ id: 2 });

    expect(auditRows.map((a) => a.action)).toContain('org.create');
  });

  it('seeds the three system roles for the new organization', async () => {
    const res = await request(app).post('/api/orgs').set('Authorization', as(2)).send({ name: 'Roles Co' });
    const names = roleRows.filter((r) => r.org_id === res.body.org.id).map((r) => r.name);
    expect(names).toEqual(expect.arrayContaining(['owner', 'admin', 'member']));
  });

  it('rejects a missing or blank name', async () => {
    const blank = await request(app).post('/api/orgs').set('Authorization', as(2)).send({ name: '   ' });
    expect(blank.status).toBe(400);
    expect(blank.body.error).toBe('Organization name is required');
    expect(optionsFor(Organization, 'create')).toHaveLength(0);

    const missing = await request(app).post('/api/orgs').set('Authorization', as(2)).send({});
    expect(missing.status).toBe(400);
  });

  it('truncates an over-long name to the column limit', async () => {
    const res = await request(app)
      .post('/api/orgs')
      .set('Authorization', as(2))
      .send({ name: 'n'.repeat(300) });
    expect(res.body.org.name).toHaveLength(255);
  });

  it('answers 400 on a unique-slug collision', async () => {
    const original = Organization.create;
    Organization.create = async () => {
      const err = new Error('slug must be unique');
      err.name = 'SequelizeUniqueConstraintError';
      throw err;
    };
    try {
      const res = await request(app).post('/api/orgs').set('Authorization', as(2)).send({ name: 'Dupe' });
      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Organization name already in use');
    } finally {
      Organization.create = original;
    }
  });
});

// ── listing & current org ─────────────────────────────────────────────────

describe('GET /api/orgs', () => {
  it('lists only the orgs the caller belongs to, filtered by their own user id', async () => {
    const res = await request(app).get('/api/orgs').set('Authorization', as(1));

    expect(res.status).toBe(200);
    expect(optionsFor(Membership, 'findAll')[0].where).toEqual({ user_id: 1 });
    expect(res.body.orgs).toHaveLength(1);
    expect(res.body.orgs[0]).toMatchObject({ org: { id: 1, name: 'Acme' }, role: 'owner' });
  });

  it('reports a null role when the membership has no role row', async () => {
    membershipRows.push(decorateMembership({ id: 99, org_id: 2, user_id: 1, role_id: 999, status: 'invited' }));
    const res = await request(app).get('/api/orgs').set('Authorization', as(1));

    expect(res.body.orgs.find((o) => o.org.id === 2).role).toBeNull();
  });

  it('returns an empty list for a user with no memberships', async () => {
    const res = await request(app).get('/api/orgs').set('Authorization', as(8));
    expect(res.body).toEqual({ success: true, orgs: [] });
  });
});

describe('GET /api/orgs/current', () => {
  it('resolves the org named by x-org-id with the caller role and permissions', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(3)).set('x-org-id', '1');

    expect(res.status).toBe(200);
    expect(res.body.org.id).toBe(1);
    expect(res.body.role).toBe('admin');
    expect(res.body.permissions).toEqual(expect.arrayContaining(['org.members.manage']));

    const membershipWhere = optionsFor(Membership, 'findOne')[0].where;
    expect(membershipWhere).toMatchObject({ org_id: 1, user_id: 3, status: 'active' });
  });

  it('falls back to the user current_org_id when no header is sent', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(2));

    expect(res.status).toBe(200);
    expect(res.body.org.id).toBe(1);
    expect(res.body.role).toBe('member');
    expect(callsMatching(Organization, 'findByPk', { id: 1 })).toHaveLength(1);
  });

  it('403s when the header names a tenant the caller is not an active member of', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(1)).set('x-org-id', '2');

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('You are not a member of this organization');
    // the membership probe is tenant-scoped: both ids present, no org-only query
    expect(optionsFor(Membership, 'findOne')).toHaveLength(1);
    expect(optionsFor(Membership, 'findOne')[0].where).toMatchObject({ org_id: 2, user_id: 1 });
    expect(optionsFor(Membership, 'findAll')).toHaveLength(0);
  });

  it('treats a revoked membership as no membership at all', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(6)).set('x-org-id', '1');
    expect(res.status).toBe(403);
  });

  it('404s for a soft-deleted organization', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(1)).set('x-org-id', '3');
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Organization not found');
    expect(Membership.calls).toHaveLength(0);
  });

  it('provisions a personal workspace when nothing is selected', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(8));

    expect(res.status).toBe(200);
    expect(res.body.provisioned).toBe(true);
    expect(res.body.role).toBe('owner');
    expect(res.body.org.slug).toMatch(/^no-org-[a-z0-9]+-8$/);
    expect(res.body.org.name).toBe("No Org's Workspace");
    expect(res.body.org.owner_id).toBe(8);
    expect(res.body.permissions).toEqual(ALL_CODES);

    const created = optionsFor(Organization, 'create')[0].values;
    expect(created.owner_id).toBe(8);
    const membership = optionsFor(Membership, 'findOrCreate')[0];
    expect(membership.where).toEqual({ org_id: res.body.org.id, user_id: 8 });
    expect(optionsFor(User, 'update').slice(-1)[0].values).toEqual({ current_org_id: res.body.org.id });
  });

  it('reuses an existing personal workspace when the generated slug already matches', async () => {
    const nowSpy = jest.spyOn(Date, 'now').mockReturnValue(1_700_000_000_000);
    const first = await request(app).get('/api/orgs/current').set('Authorization', as(8));
    expect(first.body.provisioned).toBe(true);

    // pointer cleared (as it is after an org delete) but the clock is the same
    userRows.find((u) => u.id === 8).current_org_id = null;
    const second = await request(app).get('/api/orgs/current').set('Authorization', as(8));

    expect(second.body.provisioned).toBe(false);
    expect(second.body.org.id).toBe(first.body.org.id);
    expect(optionsFor(Organization, 'findOne').slice(-1)[0].where).toEqual({
      slug: first.body.org.slug,
    });
    expect(optionsFor(Organization, 'create')).toHaveLength(1);
    nowSpy.mockRestore();
  });

  it('creates a second workspace org once the clock moves on (KNOWN GAP)', async () => {
    // The slug embeds Date.now(), so the findOne({slug}) existence check can
    // never match the org created a millisecond earlier: provisioning is not
    // idempotent. Documents current behaviour — each unselected GET /current
    // leaves another org + 3 roles behind.
    const first = await request(app).get('/api/orgs/current').set('Authorization', as(8));
    userRows.find((u) => u.id === 8).current_org_id = null;
    const second = await request(app).get('/api/orgs/current').set('Authorization', as(8));

    expect(first.body.provisioned).toBe(true);
    expect(second.body.provisioned).toBe(true);
    expect(second.body.org.id).not.toBe(first.body.org.id);
    expect(optionsFor(Organization, 'create')).toHaveLength(2);
  });

  it('never provisions when the header selects a foreign tenant', async () => {
    const res = await request(app).get('/api/orgs/current').set('Authorization', as(4)).set('x-org-id', '1');
    expect(res.status).toBe(403);
    expect(optionsFor(Organization, 'create')).toHaveLength(0);
  });
});

describe('GET /api/orgs/permissions and /api/orgs/roles', () => {
  it('returns the global permission catalog', async () => {
    const res = await request(app).get('/api/orgs/permissions').set('Authorization', as(2));
    expect(res.status).toBe(200);
    expect(res.body.permissions.map((p) => p.code)).toEqual(expect.arrayContaining(ALL_CODES));
  });

  it('lists only the active tenant roles with their permission codes', async () => {
    const res = await request(app).get('/api/orgs/roles').set('Authorization', as(2)).set('x-org-id', '1');

    expect(res.status).toBe(200);
    expect(optionsFor(Role, 'findAll')[0].where).toEqual({ org_id: 1 });
    expect(res.body.roles).toHaveLength(3);
    const member = res.body.roles.find((r) => r.name === 'member');
    expect(member.permissions).toEqual(MEMBER_CODES);
  });

  it('does not list another tenant roles when the header points elsewhere', async () => {
    const res = await request(app).get('/api/orgs/roles').set('Authorization', as(4)).set('x-org-id', '2');

    expect(res.body.roles.map((r) => r.id)).toEqual([20, 21, 22]);
    expect(optionsFor(Role, 'findAll')[0].where).toEqual({ org_id: 2 });
  });

  it('rejects a member of another org with 403 before querying roles', async () => {
    const res = await request(app).get('/api/orgs/roles').set('Authorization', as(1)).set('x-org-id', '2');
    expect(res.status).toBe(403);
    expect(Role.calls).toHaveLength(0);
  });
});

// ── org switching ─────────────────────────────────────────────────────────

describe('POST /api/orgs/:id/select', () => {
  it('switches the active org when an active membership exists', async () => {
    const res = await request(app).post('/api/orgs/2/select').set('Authorization', as(4));

    expect(res.status).toBe(200);
    expect(res.body.orgId).toBe(2);
    expect(optionsFor(Membership, 'findOne')[0].where).toEqual({ org_id: '2', user_id: 4, status: 'active' });
    expect(optionsFor(User, 'update')[0].values).toEqual({ current_org_id: '2' });
    expect(optionsFor(User, 'update')[0].options.where).toEqual({ id: 4 });
  });

  it('403s and writes nothing when the caller is not a member', async () => {
    const res = await request(app).post('/api/orgs/2/select').set('Authorization', as(1));

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('You are not a member of this organization');
    expect(optionsFor(User, 'update')).toHaveLength(0);
    expect(userRows.find((u) => u.id === 1).current_org_id).toBe(1);
  });

  it('refuses to select an org through a revoked membership', async () => {
    const res = await request(app).post('/api/orgs/1/select').set('Authorization', as(6));
    expect(res.status).toBe(403);
    expect(optionsFor(Membership, 'findOne')[0].where).toMatchObject({ status: 'active' });
  });
});

// ── org update / delete ───────────────────────────────────────────────────

describe('PUT /api/orgs/:id', () => {
  it('renames the tenant-scoped organization resolved by requireOrg', async () => {
    const res = await request(app)
      .put('/api/orgs/1')
      .set('Authorization', as(1))
      .set('x-org-id', '1')
      .send({ name: ' Acme Industries ' });

    expect(res.status).toBe(200);
    expect(res.body.org.name).toBe('Acme Industries');
    expect(orgRows.find((o) => o.id === 1).name).toBe('Acme Industries');
    expect(auditRows.map((a) => a.action)).toContain('org.update');
  });

  it('answers 404, never 403, when the path id is a different tenant', async () => {
    const res = await request(app)
      .put('/api/orgs/2')
      .set('Authorization', as(1))
      .set('x-org-id', '1')
      .send({ name: 'Hijacked' });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Organization not found' });
    expect(orgRows.find((o) => o.id === 2).name).toBe('Globex');
  });

  it('403s a plain member who tries to rename the org', async () => {
    const res = await request(app)
      .put('/api/orgs/1')
      .set('Authorization', as(2))
      .set('x-org-id', '1')
      .send({ name: 'Sneaky' });

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Organization management permission required');
    expect(orgRows.find((o) => o.id === 1).name).toBe('Acme');
  });

  it('rejects a blank name', async () => {
    const res = await request(app)
      .put('/api/orgs/1')
      .set('Authorization', as(1))
      .set('x-org-id', '1')
      .send({ name: '  ' });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Organization name is required');
  });

  it('403s before resolving the org when no x-org-id is selected', async () => {
    const res = await request(app).put('/api/orgs/1').set('Authorization', as(8)).send({ name: 'X' });
    expect(res.status).toBe(403);
    expect(res.body.error).toBe('No active organization selected');
  });
});

describe('DELETE /api/orgs/:id', () => {
  it('soft-deletes the caller tenant and clears their active org', async () => {
    const res = await request(app).delete('/api/orgs/1').set('Authorization', as(1)).set('x-org-id', '1');

    expect(res.status).toBe(200);
    expect(orgRows.find((o) => o.id === 1).deleted_at).toBeInstanceOf(Date);
    expect(userRows.find((u) => u.id === 1).current_org_id).toBeNull();
    expect(auditRows.map((a) => a.action)).toContain('org.delete');
    // the org is now invisible to the paranoid default scope
    expect(await Organization.findByPk(1)).toBeNull();
  });

  it('answers 404 when the path id is another tenant', async () => {
    const res = await request(app).delete('/api/orgs/2').set('Authorization', as(1)).set('x-org-id', '1');

    expect(res.status).toBe(404);
    expect(orgRows.find((o) => o.id === 2).deleted_at).toBeNull();
  });

  it('lets a members-manager destroy the whole organization (SECURITY GAP)', async () => {
    // user 2 is a plain member; user 3 holds org.members.manage but is not the owner.
    const res = await request(app).delete('/api/orgs/1').set('Authorization', as(3)).set('x-org-id', '1');

    // Documents current behaviour: isOrgManager() accepts org.members.manage.
    expect(res.status).toBe(200);
    expect(orgRows.find((o) => o.id === 1).deleted_at).toBeInstanceOf(Date);
  });

  it('403s a plain member', async () => {
    const res = await request(app).delete('/api/orgs/1').set('Authorization', as(2)).set('x-org-id', '1');
    expect(res.status).toBe(403);
    expect(orgRows.find((o) => o.id === 1).deleted_at).toBeNull();
  });
});

// ── members ───────────────────────────────────────────────────────────────

describe('GET /api/orgs/:id/members', () => {
  it('lists only the tenant memberships with the org filter in the query', async () => {
    const res = await request(app).get('/api/orgs/1/members').set('Authorization', as(1)).set('x-org-id', '1');

    expect(res.status).toBe(200);
    const findAll = optionsFor(Membership, 'findAll');
    expect(findAll).toHaveLength(1);
    expect(findAll[0].where).toEqual({ org_id: 1 });
    expect(res.body.members.map((m) => m.userId).sort((a, b) => a - b)).toEqual([1, 2, 3, 5, 6]);
    expect(res.body.members.map((m) => m.userId)).not.toContain(4);
    expect(res.body.members.find((m) => m.userId === 2)).toMatchObject({ role: 'member', email: 'sam@acme.test' });
  });

  it('404s a cross-tenant probe without issuing an unscoped membership query', async () => {
    const res = await request(app).get('/api/orgs/2/members').set('Authorization', as(1)).set('x-org-id', '1');

    expect(res.status).toBe(404);
    expect(optionsFor(Membership, 'findAll')).toHaveLength(0);
  });

  it('403s a non-member reaching for a foreign tenant', async () => {
    const res = await request(app).get('/api/orgs/2/members').set('Authorization', as(1)).set('x-org-id', '2');
    expect(res.status).toBe(403);
    expect(res.body.error).toBe('You are not a member of this organization');
    expect(optionsFor(Membership, 'findAll')).toHaveLength(0);
  });

  it('reports null profile fields when the member account is gone', async () => {
    userRows.splice(
      userRows.findIndex((u) => u.id === 2),
      1,
    );
    const res = await request(app).get('/api/orgs/1/members').set('Authorization', as(1)).set('x-org-id', '1');

    expect(res.body.members.find((m) => m.userId === 2)).toMatchObject({ name: null, email: null });
  });
});

describe('POST /api/orgs/:id/members', () => {
  it('rejects a padded email — the validator runs before the route trim', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: '  newbie@outside.test  ', role: 'admin' });

    expect(res.status).toBe(400);
    expect(res.body.errors[0].msg).toBe('Valid email is required');
    expect(membershipWrites()).toHaveLength(0);
  });

  it('creates an active membership bound to the resolved tenant and role', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'Newbie@Outside.test', role: 'admin' });

    expect(res.status).toBe(201);
    // role lookup is tenant-scoped, so a foreign org role id can never be adopted
    expect(optionsFor(Role, 'findOne')[0].where).toEqual({ org_id: 1, name: 'admin' });
    const findOrCreate = optionsFor(Membership, 'findOrCreate')[0];
    expect(findOrCreate.where).toEqual({ org_id: 1, user_id: 7 });
    expect(findOrCreate.defaults).toMatchObject({ org_id: 1, role_id: 11, status: 'active', invited_by: 3 });
    expect(queueJobs).toHaveLength(1);
    expect(queueJobs[0].payload.to).toBe('newbie@outside.test');
    expect(auditRows.map((a) => a.action)).toContain('org.member.invite');
  });

  it('treats role names case-sensitively (an Admin invite is a 400, not a silent grant)', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'newbie@outside.test', role: 'Admin' });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Unknown role: Admin');
    expect(optionsFor(Role, 'findOne')[0].where).toEqual({ org_id: 1, name: 'Admin' });
    expect(membershipWrites()).toHaveLength(0);
  });

  it('defaults to the member role', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'lee@globex.test' });

    expect(res.status).toBe(201);
    expect(optionsFor(Role, 'findOne')[0].where).toEqual({ org_id: 1, name: 'member' });
    expect(optionsFor(Membership, 'findOrCreate')[0].defaults.role_id).toBe(12);
  });

  it('is idempotent for an existing membership', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test', role: 'owner' });

    expect(res.status).toBe(201);
    expect(membershipRows.filter((m) => m.org_id === 1 && m.user_id === 2)).toHaveLength(1);
  });

  it('rejects an invalid email', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'not-an-email' });

    expect(res.status).toBe(400);
    expect(res.body.errors[0].msg).toBe('Valid email is required');
    expect(membershipWrites()).toHaveLength(0);
  });

  it('rejects an unknown role name', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test', role: 'superuser' });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Unknown role: superuser');
    expect(membershipWrites()).toHaveLength(0);
  });

  it('404s when no account matches the email', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'nobody@nowhere.test' });

    expect(res.status).toBe(404);
    expect(res.body.error).toBe('No account found for this email');
    expect(membershipWrites()).toHaveLength(0);
    expect(queueJobs).toHaveLength(0);
  });

  it('403s a plain member and 404s a cross-tenant path id', async () => {
    const forbidden = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(2))
      .set('x-org-id', '1')
      .send({ email: 'newbie@outside.test' });
    expect(forbidden.status).toBe(403);
    expect(forbidden.body.error).toBe('Missing permission: org.members.manage');

    const crossTenant = await request(app)
      .post('/api/orgs/2/members')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'newbie@outside.test' });
    expect(crossTenant.status).toBe(404);
    expect(membershipWrites()).toHaveLength(0);
  });

  it('lets a global admin manage members without the org permission', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(5))
      .set('x-org-id', '1')
      .send({ email: 'newbie@outside.test' });

    expect(res.status).toBe(201);
  });

  it('still requires membership for a global admin', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members')
      .set('Authorization', as(4))
      .set('x-org-id', '1')
      .send({ email: 'newbie@outside.test' });

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('You are not a member of this organization');
  });
});

describe('POST /api/orgs/:id/members/invite', () => {
  it('issues a signed invite link bound to the resolved tenant', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'Ghost@Outside.test', role: 'admin' });

    expect(res.status).toBe(201);
    expect(res.body.expiresIn).toBe('7d');
    expect(res.body.inviteUrl.startsWith('https://app.test/invite/')).toBe(true);

    const token = res.body.inviteUrl.split('/invite/')[1];
    expect(jwt.verify(token, SECRET, { algorithms: ['HS256'] })).toMatchObject({
      purpose: 'org_invite',
      orgId: 1,
      roleId: 11,
      email: 'ghost@outside.test',
    });
    // no account yet → nothing is persisted to memberships
    expect(optionsFor(Membership, 'findOrCreate')).toHaveLength(0);
    expect(queueJobs).toHaveLength(1);
    expect(queueJobs[0].payload.html).toContain('Accept invitation');
  });

  it('creates a pending (invited) membership when the account already exists', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test' });

    expect(res.status).toBe(201);
    const findOrCreate = optionsFor(Membership, 'findOrCreate')[0];
    expect(findOrCreate.where).toEqual({ org_id: 1, user_id: 2 });
    expect(findOrCreate.defaults).toMatchObject({ status: 'invited', invited_by: 3, joined_at: null });
  });

  it('never mints a token for a foreign tenant id in the path', async () => {
    const res = await request(app)
      .post('/api/orgs/2/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test' });

    expect(res.status).toBe(404);
    expect(optionsFor(Membership, 'findOrCreate')).toHaveLength(0);
    expect(queueJobs).toHaveLength(0);
  });

  it('rejects an invalid email and an unknown role', async () => {
    const badEmail = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'nope' });
    expect(badEmail.status).toBe(400);

    const badRole = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test', role: 'owner2' });
    expect(badRole.status).toBe(400);
    expect(badRole.body.error).toBe('Unknown role: owner2');
  });

  it('403s a member without the manage permission', async () => {
    const res = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(2))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test' });
    expect(res.status).toBe(403);
  });

  it('uses the default frontend origin when FRONTEND_URL is unset', async () => {
    delete process.env.FRONTEND_URL;
    const res = await request(app)
      .post('/api/orgs/1/members/invite')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ email: 'sam@acme.test' });
    expect(res.body.inviteUrl).toMatch(/^http:\/\/localhost:5173\/invite\//);
  });
});

describe('PUT /api/orgs/:id/members/:userId', () => {
  it('changes a role through a tenant-scoped membership lookup', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ role: 'admin' });

    expect(res.status).toBe(200);
    expect(optionsFor(Membership, 'findOne').slice(-1)[0].where).toEqual({ org_id: 1, user_id: '2' });
    expect(optionsFor(Role, 'findOne')[0].where).toEqual({ org_id: 1, name: 'admin' });
    expect(membershipRows.find((m) => m.user_id === 2).role_id).toBe(11);
    expect(auditRows.map((a) => a.meta.targetUserId)).toContain('2');
  });

  it('404s a membership that lives in another tenant instead of mutating it', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/4')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ role: 'owner' });

    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Membership not found');
    expect(membershipRows.find((m) => m.user_id === 4).role_id).toBe(20);
  });

  it('404s the cross-tenant path id before any membership read', async () => {
    const res = await request(app)
      .put('/api/orgs/2/members/4')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ role: 'member' });

    expect(res.status).toBe(404);
    // requireOrg's own probe is the only membership read; the target row is never fetched
    expect(optionsFor(Membership, 'findOne')).toHaveLength(1);
    expect(optionsFor(Membership, 'findOne')[0].where).toMatchObject({ org_id: 1, user_id: 3 });
    expect(membershipWrites()).toHaveLength(0);
  });

  it('reactivates a revoked membership and stamps joined_at', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/6')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ status: 'active' });

    expect(res.status).toBe(200);
    const member = membershipRows.find((m) => m.user_id === 6);
    expect(member.status).toBe('active');
    expect(member.joined_at).toBeInstanceOf(Date);
  });

  it('sets an explicit status without touching joined_at', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ status: 'revoked' });

    expect(res.status).toBe(200);
    expect(membershipRows.find((m) => m.user_id === 2).status).toBe('revoked');
  });

  it('silently ignores an unrecognised status value', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ status: 'banana' });

    expect(res.status).toBe(200);
    expect(membershipRows.find((m) => m.user_id === 2).status).toBe('active');
  });

  it('rejects an unknown role without touching the membership', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ role: 'ghost' });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Unknown role: ghost');
    expect(optionsFor(Membership, 'update')).toHaveLength(0);
  });

  it('lets a members-manager promote themselves to owner (SECURITY GAP)', async () => {
    // user 3 holds org.members.manage but is not the org owner (role_id 11 = admin).
    const res = await request(app)
      .put('/api/orgs/1/members/3')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({ role: 'owner' });

    // Documents current behaviour: no self-promotion / highest-role guard.
    expect(res.status).toBe(200);
    expect(membershipRows.find((m) => m.user_id === 3).role_id).toBe(10);
  });

  it('403s a plain member and 401s an anonymous caller', async () => {
    const forbidden = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(2))
      .set('x-org-id', '1')
      .send({ role: 'owner' });
    expect(forbidden.status).toBe(403);

    const anon = await request(app).put('/api/orgs/1/members/2').set('x-org-id', '1').send({ role: 'owner' });
    expect(anon.status).toBe(401);
  });

  it('accepts a status-only change with no role body', async () => {
    const res = await request(app)
      .put('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send({});

    expect(res.status).toBe(200);
    expect(optionsFor(Role, 'findOne')).toHaveLength(0);
  });
});

describe('DELETE /api/orgs/:id/members/:userId', () => {
  it('revokes a tenant-scoped membership', async () => {
    const res = await request(app)
      .delete('/api/orgs/1/members/2')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send();

    expect(res.status).toBe(200);
    expect(optionsFor(Membership, 'findOne').slice(-1)[0].where).toEqual({ org_id: 1, user_id: '2' });
    expect(membershipRows.find((m) => m.user_id === 2).status).toBe('revoked');
    expect(auditRows.map((a) => a.action)).toContain('org.member.remove');
  });

  it('refuses to revoke your own membership', async () => {
    const res = await request(app)
      .delete('/api/orgs/1/members/3')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send();

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Cannot revoke your own membership');
    expect(membershipRows.find((m) => m.user_id === 3).status).toBe('active');
  });

  it('404s a member of another tenant', async () => {
    const res = await request(app)
      .delete('/api/orgs/1/members/4')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send();

    expect(res.status).toBe(404);
    expect(membershipRows.find((m) => m.user_id === 4).status).toBe('active');
  });

  it('revokes the organization owner, leaving no owner (SECURITY GAP)', async () => {
    const res = await request(app)
      .delete('/api/orgs/1/members/1')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send();

    // Documents current behaviour: no last-owner protection.
    expect(res.status).toBe(200);
    expect(membershipRows.find((m) => m.user_id === 1).status).toBe('revoked');
    expect(membershipRows.some((m) => m.org_id === 1 && m.role_id === 10 && m.status === 'active')).toBe(false);
  });

  it('404s a cross-tenant path id and 403s a plain member', async () => {
    const crossTenant = await request(app)
      .delete('/api/orgs/2/members/4')
      .set('Authorization', as(3))
      .set('x-org-id', '1')
      .send();
    expect(crossTenant.status).toBe(404);
    expect(membershipWrites()).toHaveLength(0);
    expect(optionsFor(Membership, 'findOne')).toHaveLength(1); // requireOrg probe only

    const forbidden = await request(app)
      .delete('/api/orgs/1/members/2')
      .set('Authorization', as(2))
      .set('x-org-id', '1')
      .send();
    expect(forbidden.status).toBe(403);
  });
});

// ── error forwarding ──────────────────────────────────────────────────────

describe('error handling', () => {
  const patches = [];

  function restorePatches() {
    while (patches.length) {
      const { model, method, original } = patches.pop();
      model[method] = original;
    }
  }
  afterEach(restorePatches);

  /** Make a model method reject, so the handler catch/next() path runs. */
  function throwOn(model, method) {
    patches.push({ model, method, original: model[method] });
    model[method] = async () => {
      throw new Error('connection reset');
    };
  }

  /** Keep the read working but make the returned instance fail on write. */
  function breakInstanceWrite(model, method, verb) {
    patches.push({ model, method, original: model[method] });
    const original = model[method];
    model[method] = async (...args) => {
      const inst = await original(...args);
      if (inst && typeof inst[verb] === 'function') {
        inst[verb] = async () => {
          throw new Error('connection reset');
        };
      }
      return inst;
    };
  }

  /** Authenticated request as `userId`, with the tenant header unless orgId is null. */
  function call(method, path, { userId = 1, orgId = 1 } = {}) {
    const agent = request(app)[method](path).set('Authorization', as(userId));
    return orgId === null ? agent : agent.set('x-org-id', String(orgId));
  }

  it.each([
    [
      'GET /invite/:token',
      () => throwOn(Organization, 'findByPk'),
      () => request(app).get(`/api/orgs/invite/${inviteToken({ orgId: 1, roleId: 12, email: 'a@b.test' })}`),
    ],
    [
      'POST /invite/:token/accept',
      () => throwOn(Membership, 'findOrCreate'),
      () =>
        request(app).post(
          `/api/orgs/invite/${inviteToken({ orgId: 1, roleId: 12, email: 'priya@acme.test' })}/accept`,
        ),
    ],
    [
      'POST /api/orgs',
      () => throwOn(Membership, 'create'),
      () => call('post', '/api/orgs', { userId: 2 }).send({ name: 'Boom' }),
    ],
    ['GET /api/orgs', () => throwOn(Membership, 'findAll'), () => call('get', '/api/orgs', { orgId: null })],
    [
      'GET /api/orgs/current (provisioning)',
      () => throwOn(Permission, 'findOrCreate'),
      () => call('get', '/api/orgs/current', { userId: 8, orgId: null }),
    ],
    [
      'GET /api/orgs/current (resolved)',
      () => throwOn(Organization, 'findByPk'),
      () => call('get', '/api/orgs/current'),
    ],
    [
      'GET /api/orgs/permissions',
      () => throwOn(Permission, 'findAll'),
      () => call('get', '/api/orgs/permissions', { orgId: null }),
    ],
    ['GET /api/orgs/roles', () => throwOn(Role, 'findAll'), () => call('get', '/api/orgs/roles')],
    ['POST /api/orgs/:id/select', () => throwOn(Membership, 'findOne'), () => call('post', '/api/orgs/1/select', { orgId: null })],
    [
      'PUT /api/orgs/:id',
      () => breakInstanceWrite(Organization, 'findByPk', 'update'),
      () => call('put', '/api/orgs/1').send({ name: 'Boom' }),
    ],
    [
      'DELETE /api/orgs/:id',
      () => breakInstanceWrite(Organization, 'findByPk', 'destroy'),
      () => call('delete', '/api/orgs/1'),
    ],
    ['GET /api/orgs/:id/members', () => throwOn(Membership, 'findAll'), () => call('get', '/api/orgs/1/members')],
    [
      'POST /api/orgs/:id/members',
      () => throwOn(Role, 'findOne'),
      () => call('post', '/api/orgs/1/members', { userId: 3 }).send({ email: 'sam@acme.test' }),
    ],
    [
      'POST /api/orgs/:id/members/invite',
      () => throwOn(Role, 'findOne'),
      () => call('post', '/api/orgs/1/members/invite', { userId: 3 }).send({ email: 'sam@acme.test' }),
    ],
    [
      'PUT /api/orgs/:id/members/:userId',
      () => breakInstanceWrite(Membership, 'findOne', 'update'),
      () => call('put', '/api/orgs/1/members/2', { userId: 3 }).send({ role: 'admin' }),
    ],
    [
      'DELETE /api/orgs/:id/members/:userId',
      () => breakInstanceWrite(Membership, 'findOne', 'update'),
      () => call('delete', '/api/orgs/1/members/2', { userId: 3 }),
    ],
  ])('%s forwards the database failure as 500', async (_label, breakIt, run) => {
    breakIt();
    const res = await run();

    expect(res.status).toBe(500);
    expect(res.body.success).toBe(false);
    expect(res.body.error).toBe('Internal error');
    expect(res.body.message).toBe('connection reset');
    expect(JSON.stringify(res.body)).not.toMatch(/at \w+|Sequelize|SELECT .* FROM/);
    restorePatches();
  });

  it('answers 500 when the invitee account cannot be resolved after creation', async () => {
    // findUserByEmail() swallows the failure (returns null), so the route falls
    // through to its explicit "cannot resolve account" guard.
    throwOn(User, 'findOne');
    const token = inviteToken({ orgId: 1, roleId: 12, email: 'who@outside.test' });
    const res = await request(app).post(`/api/orgs/invite/${token}/accept`).send({ password: 'hunter22' });

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ success: false, error: 'Failed to resolve account' });
    expect(membershipWrites()).toHaveLength(0);
    restorePatches();
  });

  it('does not leak a stack trace or SQL in a validation error', async () => {
    const res = await request(app).post('/api/orgs').set('Authorization', as(2)).send({ name: 123 });

    expect([201, 400, 500]).toContain(res.status);
    expect(JSON.stringify(res.body)).not.toMatch(/at Object\.<anonymous>|SELECT .* FROM/i);
  });
});
