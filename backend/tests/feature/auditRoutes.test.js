/**
 * Feature tests — routes/audit.routes.js
 *
 * The router is admin-only. The real auth middleware shape is reproduced by a
 * stub that attaches `req.user` from `x-test-role`/`x-test-id`; the AuditLog
 * model (and its two named helpers) are replaced so the tests assert the where
 * clause and the CSV the route actually produced.
 */
import express from 'express';
import request from 'supertest';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { createFakeModel } from '../helpers/sequelizeFakes.js';

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = {
      id: Number(req.headers['x-test-id'] || 1),
      role: req.headers['x-test-role'] || 'user',
      email: 'actor@example.test',
    };
    next();
  },
  authorize:
    (...roles) =>
    (req, res, next) => {
      if (!req.user || !roles.includes(req.user.role)) {
        return res.status(403).json({ success: false, error: 'Not authorized' });
      }
      return next();
    },
  optionalProtect: (_req, _res, next) => next(),
}));

const auditRows = () => [
  {
    id: 1,
    created_at: new Date('2026-06-01T10:00:00.000Z'),
    user_id: 10,
    email: 'ada@example.test',
    action: 'user.login',
    ip: '10.0.0.1',
    user_agent: 'Mozilla/5.0',
    meta: { ok: true },
    prev_hash: '',
    hash: 'aaa',
  },
  {
    id: 2,
    created_at: new Date('2026-06-02T10:00:00.000Z'),
    user_id: 11,
    email: 'quote"comma,@example.test',
    action: 'order.refunded',
    ip: '10.0.0.2',
    user_agent: 'curl/8',
    meta: { amount: 10 },
    prev_hash: 'aaa',
    hash: 'bbb',
  },
];

const AuditLog = createFakeModel('AuditLog', auditRows());
const purgeAuditLogs = jest.fn(async () => 2);
const verifyAuditChain = jest.fn(async () => ({ valid: true, checked: 2 }));

jest.unstable_mockModule('../../models/AuditLog.js', () => ({
  __esModule: true,
  default: AuditLog,
  purgeAuditLogs,
  verifyAuditChain,
}));

const { default: auditRoutes } = await import('../../routes/audit.routes.js');

const app = express();
app.use(express.json());
app.use('/api/audit-logs', auditRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

const call = (method, path, { role = 'admin', query, bodyData } = {}) => {
  let agent = request(app)[method](path).set('x-test-role', role);
  if (query) agent = agent.query(query);
  if (bodyData !== undefined) agent = agent.send(bodyData);
  return agent;
};

const lastQuery = (method) => {
  const calls = AuditLog.calls.filter((c) => c.method === method);
  return calls.at(-1).options;
};

beforeEach(() => {
  AuditLog.rows.length = 0;
  AuditLog.rows.push(...auditRows());
  AuditLog.calls.length = 0;
  // jest.config.js sets resetMocks, so implementations must be bound per test.
  purgeAuditLogs.mockResolvedValue(2);
  verifyAuditChain.mockResolvedValue({ valid: true, checked: 2 });
  mockLogger.error.mockClear();
});

describe('authorization', () => {
  it.each([
    ['get', '/api/audit-logs'],
    ['get', '/api/audit-logs/export'],
    ['get', '/api/audit-logs/verify'],
    ['delete', '/api/audit-logs/retention'],
  ])('%s %s refuses a non-admin', async (method, path) => {
    const res = await call(method, path, { role: 'vendor' });

    expect(res.status).toBe(403);
    expect(AuditLog.calls).toHaveLength(0);
  });
});

describe('GET /api/audit-logs', () => {
  it('lists newest-first with pagination metadata', async () => {
    const res = await call('get', '/api/audit-logs');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: true,
      total: 2,
      pagination: { page: 1, limit: 20, pages: 1 },
    });
    expect(res.body.data.map((r) => r.id)).toEqual([1, 2]);
    expect(lastQuery('findAndCountAll')).toMatchObject({
      order: [['created_at', 'DESC']],
      limit: 20,
      offset: 0,
    });
  });

  it.each([
    ['page=0&limit=-1', { page: 1, limit: 20 }],
    ['page=-3', { page: 1, limit: 20 }],
    ['limit=500', { page: 1, limit: 100 }],
  ])('clamps %s instead of passing it to SQL', async (queryString, expected) => {
    const res = await call('get', `/api/audit-logs?${queryString}`);

    expect(res.status).toBe(200);
    expect(res.body.pagination.page).toBe(expected.page);
    expect(res.body.pagination.limit).toBe(expected.limit);
  });

  it('builds every filter into the where clause', async () => {
    await call('get', '/api/audit-logs', {
      query: {
        action: 'login',
        email: '@example',
        userId: '10',
        ip: '10.0.0.1',
        from: '2026-06-01',
        to: '2026-06-30',
      },
    });

    const { where } = lastQuery('findAndCountAll');
    expect(where.action).toEqual({ [Op.iLike]: '%login%' });
    expect(where.email).toEqual({ [Op.iLike]: '%@example%' });
    expect(where.user_id).toBe(10);
    expect(where.ip).toBe('10.0.0.1');
    expect(where.created_at[Op.gte]).toEqual(new Date('2026-06-01'));
    expect(where.created_at[Op.lte]).toEqual(new Date('2026-06-30'));
  });

  it.each([
    ['a non-numeric userId', { userId: 'abc' }],
    ['an invalid from date', { from: 'not-a-date' }],
  ])('rejects %s with 400 before querying', async (_label, query) => {
    const res = await call('get', '/api/audit-logs', { query });

    expect(res.status).toBe(400);
    expect(AuditLog.calls).toHaveLength(0);
  });
});

describe('GET /api/audit-logs/export', () => {
  it('streams a BOM-prefixed CSV with escaped cells', async () => {
    const res = await call('get', '/api/audit-logs/export');

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toContain('text/csv');
    expect(res.headers['content-disposition']).toBe('attachment; filename="audit-logs.csv"');
    expect(res.text.startsWith('\uFEFF')).toBe(true);

    const [, first, second] = res.text.split('\n');
    expect(first).toBe('"1","2026-06-01T10:00:00.000Z","10","ada@example.test","user.login","10.0.0.1","Mozilla/5.0","{""ok"":true}"');
    // A quote inside a cell is doubled, and the comma stays inside the quotes.
    expect(second).toContain('"quote""comma,@example.test"');
  });

  it('applies the same filters as the listing', async () => {
    await call('get', '/api/audit-logs/export', { query: { action: 'refund', userId: '11' } });

    const { where } = lastQuery('findAll');
    expect(where.action).toEqual({ [Op.iLike]: '%refund%' });
    expect(where.user_id).toBe(11);
  });
});

describe('GET /api/audit-logs/verify', () => {
  it('reports a valid chain', async () => {
    const res = await call('get', '/api/audit-logs/verify');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, valid: true, checked: 2 });
    expect(verifyAuditChain).toHaveBeenCalledWith(AuditLog, 5000);
    expect(mockLogger.error).not.toHaveBeenCalled();
  });

  it('logs a broken chain as a security incident', async () => {
    verifyAuditChain.mockResolvedValueOnce({
      valid: false,
      brokenAtId: 2,
      reason: 'prev_hash does not match the previous row',
    });

    const res = await call('get', '/api/audit-logs/verify?limit=10');

    expect(res.body.success).toBe(false);
    expect(res.body.brokenAtId).toBe(2);
    expect(verifyAuditChain).toHaveBeenCalledWith(AuditLog, 10);
    expect(mockLogger.error).toHaveBeenCalledWith(
      expect.stringContaining('AUDIT CHAIN BROKEN at id=2'),
    );
  });
});

describe('DELETE /api/audit-logs/retention', () => {
  it('requires a real cutoff date', async () => {
    const res = await call('delete', '/api/audit-logs/retention', {
      bodyData: { before: 'nope', confirm: 'PURGE-AUDIT-LOGS' },
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('before (ISO date) is required');
    expect(purgeAuditLogs).not.toHaveBeenCalled();
  });

  it('requires the explicit confirmation phrase', async () => {
    const res = await call('delete', '/api/audit-logs/retention', {
      bodyData: { before: '2026-01-01', confirm: 'yes' },
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toContain('explicit confirmation');
    expect(purgeAuditLogs).not.toHaveBeenCalled();
  });

  it('purges rows older than the cutoff when confirmed', async () => {
    const res = await call('delete', '/api/audit-logs/retention', {
      bodyData: { before: '2026-01-01T00:00:00.000Z', confirm: 'PURGE-AUDIT-LOGS' },
    });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      data: { deleted: 2, before: '2026-01-01T00:00:00.000Z' },
    });
    expect(purgeAuditLogs).toHaveBeenCalledWith(new Date('2026-01-01T00:00:00.000Z'));
  });
});
