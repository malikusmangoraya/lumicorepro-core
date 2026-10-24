import request from 'supertest';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import jwt from 'jsonwebtoken';
import { Sequelize } from 'sequelize';

/**
 * AI ZIP download route.
 *
 * This route called `agentEndpointUrl()` without importing it, so every
 * download threw a ReferenceError and returned a generic 500 — the product's
 * core deliverable was unreachable while the rest of the API stayed green.
 * Nothing but a real HTTP request through the route catches that, so this
 * suite makes the request.
 */

const offlineSequelize = new Sequelize('postgres://postgres:postgres@localhost:5432/lumicorepro', {
  dialect: 'postgres',
  logging: false,
});

jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: offlineSequelize,
  default: async () => false,
}));

jest.unstable_mockModule('../../services/cache/redis.client.js', () => {
  const memory = {
    get: async () => null,
    set: async () => 'OK',
    del: async () => 1,
    incrby: async () => 1,
    expire: async () => 1,
    ttl: async () => -1,
    keys: async () => [],
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

const mockLog = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn(), http: jest.fn() };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLog,
  logger: mockLog,
  redact: (v) => v,
  withRequestId: () => mockLog,
}));

const { default: app } = await import('../../server.js');

const SECRET = 'ai-download-test-secret';
const AGENT_URL = 'http://127.0.0.1:8123';

const zipBytes = new Uint8Array([80, 75, 3, 4, 1, 2, 3]);

function mockAgent(response) {
  const fetchMock = jest.fn(async () => response);
  global.fetch = fetchMock;
  return fetchMock;
}

beforeEach(() => {
  process.env.JWT_SECRET = SECRET;
  process.env.AI_AGENT_URL = AGENT_URL;
});

const authed = (req) =>
  req.set('Authorization', `Bearer ${jwt.sign({ id: 7, email: 'a@b.c' }, SECRET, { algorithm: 'HS256' })}`);

/** Collect the raw bytes; supertest would otherwise JSON-parse a zip body away. */
const asBuffer = (req) =>
  req.buffer(true).parse((res, cb) => {
    const chunks = [];
    res.on('data', (c) => chunks.push(c));
    res.on('end', () => cb(null, Buffer.concat(chunks)));
  });

describe('GET /api/ai/download/:runId', () => {
  it('streams the agent ZIP instead of a 500', async () => {
    const fetchMock = mockAgent({
      ok: true,
      status: 200,
      headers: { get: () => 'application/zip' },
      arrayBuffer: async () => zipBytes.buffer,
    });

    const res = await asBuffer(authed(request(app).get('/api/ai/download/run_42')));

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toContain('application/zip');
    expect(res.headers['content-disposition']).toContain('run_42.zip');
    expect([...res.body]).toEqual([...zipBytes]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe(`${AGENT_URL}/api/download/run_42`);
  });

  it('propagates a missing archive as the agent status code', async () => {
    mockAgent({
      ok: false,
      status: 404,
      headers: { get: () => 'application/json' },
      arrayBuffer: async () => new Uint8Array(0).buffer,
    });

    const res = await authed(request(app).get('/api/ai/download/nope'));
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Project archive not found' });
  });

  it('rejects an unauthenticated download', async () => {
    mockAgent({ ok: true, status: 200, headers: { get: () => '' }, arrayBuffer: async () => zipBytes.buffer });
    const res = await request(app).get('/api/ai/download/run_42');
    expect(res.status).toBe(401);
  });

  it('returns 500 only when the agent itself is unreachable', async () => {
    global.fetch = jest.fn(async () => {
      throw new Error('ECONNREFUSED');
    });
    const res = await authed(request(app).get('/api/ai/download/run_42'));
    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to stream ZIP archive');
  });
});
