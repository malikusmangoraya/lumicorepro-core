/**
 * Feature tests — multi-tenant RBAC middleware (middleware/rbac.js).
 *
 * The middleware is mounted on a real Express app so the assertions cover the
 * HTTP contract end-to-end: which status/body a denied request gets, whether the
 * handler actually ran, and — via the recorded Sequelize calls — whether the
 * org/user/status filters really reached the membership query.
 *
 * `services/rbac.service.js` is NOT mocked: `getMembership()` and
 * `permissionCodes()` run for real against in-memory model doubles
 * (tests/helpers/sequelizeFakes.js), so a permission regression in the service
 * would surface here instead of being hidden by a stub.
 */
import express from 'express';
import request from 'supertest';
import { Sequelize } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel, matchesWhere } from '../helpers/sequelizeFakes.js';

// Models call Model.init(..., { sequelize }) at import time, so the mocked DB
// module must hand out a real — but never connected — Sequelize instance.
const offlineSequelize = new Sequelize(
  'postgres://postgres:postgres@localhost:5432/lumicorepro_test',
  { dialect: 'postgres', logging: false },
);

jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: offlineSequelize,
  default: async () => false,
}));

jest.unstable_mockModule('../../utils/logger.js', () => {
  const silent = { info() {}, warn() {}, error() {}, debug() {}, http() {} };
  return {
    __esModule: true,
    default: silent,
    withRequestId: () => silent,
    redact: (v) => v,
  };
});

// ── Organization rows (paranoid: deleted_at hides a row, like the real model) ─
const orgStore = createFakeModel(
  'Organization',
  [
    { id: 1, slug: 'acme', name: 'Acme', deleted_at: null },
    { id: 2, slug: 'gone', name: 'Gone Co', deleted_at: new Date('2026-01-01') },
    { id: 3, slug: 'delta', name: 'Delta', deleted_at: null },
    { id: 4, slug: 'revoked', name: 'Revoked Co', deleted_at: null },
  ],
  { paranoidField: 'deleted_at' },
);

// ── Membership rows, shaped the way getMembership()'s include expects ────────
const membershipStore = createFakeModel('Membership', [
  {
    id: 10,
    org_id: 1,
    user_id: 5,
    status: 'active',
    role: { permissions: [{ code: 'org.view' }, { code: 'products.manage' }] },
  },
  {
    id: 11,
    org_id: 1,
    user_id: 6,
    status: 'active',
    role: { permissions: [{ code: 'org.view' }] },
  },
  { id: 12, org_id: 1, user_id: 7, status: 'active', role: { permissions: [] } },
  {
    id: 13,
    org_id: 3,
    user_id: 5,
    status: 'active',
    role: { permissions: [{ code: 'org.manage' }] },
  },
  {
    id: 14,
    org_id: 4,
    user_id: 5,
    status: 'revoked',
    role: { permissions: [{ code: 'org.manage' }] },
  },
  {
    id: 15,
    org_id: 1,
    user_id: 8,
    status: 'active',
    role: { permissions: [{ code: 'org.members.manage' }] },
  },
]);

const orgModel = { findByPk: jest.fn() };
jest.unstable_mockModule('../../models/Organization.js', () => ({
  __esModule: true,
  default: orgModel,
}));

jest.unstable_mockModule('../../models/Membership.js', () => ({
  __esModule: true,
  default: membershipStore,
}));

const { requireOrg, requirePermission, isOrgManager, default: rbacDefault } = await import(
  '../../middleware/rbac.js'
);
const { default: errorHandler } = await import('../../middleware/errorHandler.js');

/** Stands in for protect()/auth middleware (covered by its own tests). */
const asUser = (user) => (req, _res, next) => {
  req.user = user;
  next();
};

function buildApp(middleware) {
  const app = express();
  app.use(express.json());
  app.get('/guarded', ...middleware, (req, res) => {
    res.json({
      success: true,
      data: {
        reached: true,
        orgId: req.orgCtx ? req.orgCtx.org.id : null,
        permissions: req.orgCtx ? req.orgCtx.permissions : null,
      },
    });
  });
  app.use(errorHandler);
  return app;
}

const MEMBER = { id: 5, role: 'user', current_org_id: 1 };
const VIEWER = { id: 6, role: 'user', current_org_id: 1 };
const NO_PERMS = { id: 7, role: 'user', current_org_id: 1 };
const ADMIN = { id: 5, role: 'admin', current_org_id: 1 };

/** The `where` of the most recent Membership.findOne call. */
const lastMembershipWhere = () => membershipStore.whereCalls('findOne').at(-1).where;

beforeEach(() => {
  // Fresh call log per test: the row stores are shared across the file, but the
  // "no query was issued" assertions need per-test isolation.
  orgStore.calls.length = 0;
  membershipStore.calls.length = 0;
  orgModel.findByPk.mockImplementation((id, options) => orgStore.findByPk(id, options));
});

describe('requireOrg — organization resolution', () => {
  it('loads the org from the x-org-id header and attaches orgCtx with permission codes', async () => {
    const app = buildApp([asUser(MEMBER), requireOrg]);
    const res = await request(app).get('/guarded').set('x-org-id', '1');

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data).toEqual({
      reached: true,
      orgId: 1,
      permissions: ['org.view', 'products.manage'],
    });
  });

  it('falls back to the user current_org_id when no header is sent', async () => {
    const app = buildApp([asUser(VIEWER), requireOrg]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(200);
    expect(res.body.data.permissions).toEqual(['org.view']);
    expect(lastMembershipWhere()).toEqual({ org_id: 1, user_id: 6, status: 'active' });
  });

  it('lets the header override the stored current org (tenant switch)', async () => {
    const app = buildApp([asUser(MEMBER), requireOrg]);
    const res = await request(app).get('/guarded').set('x-org-id', '3');

    expect(res.status).toBe(200);
    expect(res.body.data.orgId).toBe(3);
    // user 5 also has a row in org 3 — the query must be scoped to the switched org
    expect(lastMembershipWhere()).toEqual({ org_id: 3, user_id: 5, status: 'active' });
  });

  it('denies with 403 when the user has no active organization at all', async () => {
    const app = buildApp([asUser({ id: 5, role: 'user' }), requireOrg]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'No active organization selected' });
    // fails closed before touching the database
    expect(orgModel.findByPk).not.toHaveBeenCalled();
    expect(membershipStore.calls).toHaveLength(0);
  });

  it('404s for an unknown organization', async () => {
    const app = buildApp([asUser(MEMBER), requireOrg]);
    const res = await request(app).get('/guarded').set('x-org-id', '999');

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Organization not found' });
    expect(membershipStore.calls).toHaveLength(0);
  });

  it('404s for a soft-deleted organization (paranoid scope hides the row)', async () => {
    const app = buildApp([asUser(MEMBER), requireOrg]);
    const res = await request(app).get('/guarded').set('x-org-id', '2');

    expect(res.status).toBe(404);
    expect(res.body.error).toBe('Organization not found');
  });

  it('403s a stranger and scopes the membership query to org + user + active status', async () => {
    const app = buildApp([asUser({ id: 99, role: 'user', current_org_id: 1 }), requireOrg]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({
      success: false,
      error: 'You are not a member of this organization',
    });

    const options = membershipStore.whereCalls('findOne')[0];
    expect(options.where).toEqual({ org_id: 1, user_id: 99, status: 'active' });
    expect(options.include[0].as).toBe('role');
    // the fake matcher proves no row satisfies that filter
    expect(membershipStore.rows.some((r) => matchesWhere(r, options.where))).toBe(false);
  });

  it('treats a revoked membership as no membership at all', async () => {
    const app = buildApp([asUser({ id: 5, role: 'user', current_org_id: 4 }), requireOrg]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(lastMembershipWhere()).toEqual({ org_id: 4, user_id: 5, status: 'active' });
    // row 14 exists for that org/user but is revoked → must not match
    const revoked = membershipStore.rows.find((r) => r.id === 14);
    expect(matchesWhere(revoked, lastMembershipWhere())).toBe(false);
  });

  it('forwards a database failure to the error handler instead of crashing', async () => {
    orgModel.findByPk.mockImplementation(() => {
      throw new Error('connection reset');
    });
    const app = buildApp([asUser(MEMBER), requireOrg]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(500);
    expect(res.body.success).toBe(false);
    expect(res.body.code).toBe('INTERNAL_ERROR');
  });

  it('exports every guard on the default export too', () => {
    expect(rbacDefault.requireOrg).toBe(requireOrg);
    expect(rbacDefault.requirePermission).toBe(requirePermission);
    expect(rbacDefault.isOrgManager).toBe(isOrgManager);
  });
});

describe('requirePermission — allow and deny per role', () => {
  const guard = (code) => buildApp([asUser(MEMBER), requireOrg, requirePermission(code)]);

  it('allows a member holding the permission code', async () => {
    const res = await request(guard('products.manage')).get('/guarded').set('x-org-id', '1');
    expect(res.status).toBe(200);
    expect(res.body.data.reached).toBe(true);
  });

  it('denies a member missing the permission code, naming it in the error', async () => {
    const res = await request(guard('orders.view')).get('/guarded').set('x-org-id', '1');
    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Missing permission: orders.view' });
  });

  it('denies by default when the membership carries an empty permission set', async () => {
    const app = buildApp([asUser(NO_PERMS), requireOrg, requirePermission('org.view')]);
    const res = await request(app).get('/guarded').set('x-org-id', '1');

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Missing permission: org.view');
  });

  it('denies when requireOrg never ran (missing orgCtx fails closed)', async () => {
    const app = buildApp([asUser(MEMBER), requirePermission('org.view')]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Missing permission: org.view' });
  });

  it('global admin bypasses the permission check without an orgCtx', async () => {
    const app = buildApp([asUser(ADMIN), requirePermission('anything.at.all')]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(200);
    expect(res.body.data.orgId).toBeNull();
    // bypass must not even read the tenant tables
    expect(orgModel.findByPk).not.toHaveBeenCalled();
  });

  it('anonymous request (no req.user) is denied, not crashed', async () => {
    const app = buildApp([requirePermission('org.view')]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Missing permission: org.view');
  });
});

describe('isOrgManager — management gate', () => {
  it('allows a member with org.manage', async () => {
    const app = buildApp([asUser(MEMBER), requireOrg, isOrgManager]);
    const res = await request(app).get('/guarded').set('x-org-id', '3');

    expect(res.status).toBe(200);
    expect(res.body.data.permissions).toEqual(['org.manage']);
  });

  it('allows a member with org.members.manage', async () => {
    const app = buildApp([
      asUser({ id: 8, role: 'user', current_org_id: 1 }),
      requireOrg,
      isOrgManager,
    ]);
    const res = await request(app).get('/guarded').set('x-org-id', '1');

    expect(res.status).toBe(200);
    expect(res.body.data.permissions).toEqual(['org.members.manage']);
  });

  it('denies a read-only member', async () => {
    const app = buildApp([asUser(VIEWER), requireOrg, isOrgManager]);
    const res = await request(app).get('/guarded').set('x-org-id', '1');

    expect(res.status).toBe(403);
    expect(res.body).toEqual({
      success: false,
      error: 'Organization management permission required',
    });
  });

  it('denies when no organization context exists', async () => {
    const app = buildApp([asUser(MEMBER), isOrgManager]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(403);
    expect(res.body.error).toBe('Organization management permission required');
  });

  it('global admin passes without any membership lookup', async () => {
    const app = buildApp([asUser(ADMIN), isOrgManager]);
    const res = await request(app).get('/guarded');

    expect(res.status).toBe(200);
    expect(membershipStore.calls).toHaveLength(0);
  });
});
