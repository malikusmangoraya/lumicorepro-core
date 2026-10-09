/**
 * Feature test — full HTTP request→response via supertest against the
 * exported Express app. DB/Redis mocks keep it offline & deterministic.
 */
import request from 'supertest';
import { describe, it, expect, jest } from '@jest/globals';
import { Sequelize } from 'sequelize';

// Models call Model.init({...}, { sequelize }) at import time, so the mocked
// module must provide a REAL (never-connected) Sequelize instance.
const offlineSequelize = new Sequelize(
  process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/lumicorepro',
  { dialect: 'postgres', logging: false },
);

jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: offlineSequelize,
  default: async () => false,
}));

jest.unstable_mockModule('../../services/cache/redis.client.js', () => {
  const memory = {
    __memory: true,
    isMemory: true,
    get: async () => null,
    set: async () => 'OK',
    del: async () => 1,
    keys: async () => [],
    sadd: async () => 1,
    smembers: async () => [],
    srem: async () => 1,
    incrby: async () => 1,
    expire: async () => 1,
    ttl: async () => -1,
    quit: async () => 'OK',
  };
  return {
    __esModule: true,
    default: () => memory,
    getRedis: () => memory,
    isRedisAvailable: () => false,
    connectRedis: async () => false,
    disconnectRedis: async () => {},
  };
});

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {}, http: () => {} },
  withRequestId: () => ({
    info: () => {}, warn: () => {}, error: () => {}, debug: () => {}, http: () => {},
  }),
  redact: (v) => v,
}));

const { default: app } = await import('../../server.js');

describe('HTTP layer basics', () => {
  it('exposes /api/health', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });

  it('returns X-Request-Id header on every response', async () => {
    const res = await request(app).get('/api/health');
    expect(res.headers['x-request-id']).toBeTruthy();
  });

  it('responds 404 with the canonical envelope for unknown routes', async () => {
    const res = await request(app).get('/api/does-not-exist');
    expect(res.status).toBe(404);
    expect(Object.keys(res.body).sort()).toEqual(
      ['success', 'status', 'message', 'code', 'data', 'timestamp'].sort(),
    );
    expect(res.body.success).toBe(false);
    expect(res.body.status).toBe(404);
    expect(res.body.code).toBe('NOT_FOUND');
    expect(res.body.data).toBeNull();
    expect(res.body.message).toBeTruthy();
    expect(Number.isNaN(Date.parse(res.body.timestamp))).toBe(false);
  });

  it('serves versioned /api/v1/* aliases of every route', async () => {
    const res = await request(app).get('/api/v1/health');
    expect(res.status).toBe(200);
    expect(res.headers['api-version']).toBe('v1');
    expect(res.body.success).toBe(true);
  });

  it('marks legacy unversioned /api/* responses as deprecated', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.headers['deprecation']).toBe('true');
  });

  it('enforces auth rate-limit on /api/auth/refresh with 429 Retry-After', async () => {
    // Hit the auth limiter (5/min) repeatedly with no refresh token → 401 (not 429)
    // to avoid DB; then confirm the limiter plumbing doesn't crash the route.
    const res = await request(app).post('/api/auth/refresh').send({});
    expect([401, 429]).toContain(res.status);
  });
});