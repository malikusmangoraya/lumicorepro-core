/**
 * Feature tests — the dev-only demo-account seeding in backend/routes/auth.routes.js
 * -----------------------------------------------------------------------------------
 * Lines 52 and 59-98 run once, while the module is being imported, and only when
 * SEED_DEMO_USERS=true, DEMO_USER_PASSWORD is set and NODE_ENV is not production.
 * This file imports the router with exactly that environment so the fixed-password
 * accounts — the riskiest code path in the file — are actually exercised.
 *
 * Everything here is real apart from the doubles: jsonwebtoken, bcryptjs, protect(),
 * the refresh service (on an in-memory Redis) and the error handler. The demo users
 * live in the router's in-memory store, so the User model double is left EMPTY on
 * purpose: it proves the logins are served from memory and not from the database.
 */
import express from 'express';
import request from 'supertest';
import cookieParser from 'cookie-parser';
import jwt from 'jsonwebtoken';
import { describe, it, expect, beforeAll, jest } from '@jest/globals';

// Pinned BEFORE the dynamic import: the seeding branch reads all of these once.
process.env.NODE_ENV = 'test';
process.env.SEED_DEMO_USERS = 'true';
process.env.DEMO_USER_PASSWORD = 'DemoPassw0rd!';
process.env.DEMO_USER_EMAIL = 'qa-person@example.com';
process.env.DEMO_ADMIN_EMAIL = 'QA-Admin@Example.com'; // must be lower-cased by the route
process.env.JWT_SECRET = 'access-secret-for-demo-seed-tests-0000000000';
process.env.JWT_REFRESH_SECRET = 'refresh-secret-for-demo-seed-tests-0000';

jest.setTimeout(40000);

// ── Doubles ──────────────────────────────────────────────────────────────────
const kv = new Map();
const redisDouble = {
  isMemory: true,
  async get(key) { return kv.has(key) ? kv.get(key) : null; },
  async set(key, value) { kv.set(key, value); return 'OK'; },
  async del(key) { return kv.delete(key) ? 1 : 0; },
  async sadd() { return 1; },
  async smembers() { return []; },
  async keys() { return [...kv.keys()]; },
  async incrby() { return 1; },
  async expire() { return 1; },
  async ttl() { return -1; },
  async quit() { return 'OK'; },
};
jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  __esModule: true,
  default: () => redisDouble,
  getRedis: () => redisDouble,
  isRedisAvailable: () => false,
  connectRedis: async () => false,
  disconnectRedis: async () => {},
}));

const logCalls = { info: [], warn: [], error: [], debug: [] };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: {
    info: (m) => logCalls.info.push(String(m)),
    warn: (m) => logCalls.warn.push(String(m)),
    error: (m) => logCalls.error.push(String(m)),
    debug: (m) => logCalls.debug.push(String(m)),
    http: () => {},
  },
}));

const dbLookups = [];
const emptyUserModel = {
  scope() {
    return {
      async findOne(options = {}) {
        dbLookups.push({ method: 'findOne', where: options.where });
        return null;
      },
    };
  },
  async findOne(options = {}) {
    dbLookups.push({ method: 'findOne', where: options.where });
    return null;
  },
  async findByPk(id) {
    dbLookups.push({ method: 'findByPk', id });
    return null;
  },
  async create() { throw new Error('this suite never writes to the database'); },
  async count() { return 0; },
};
jest.unstable_mockModule('../../models/User.js', () => ({
  __esModule: true,
  default: emptyUserModel,
}));

const passthrough = (_req, _res, next) => next();
jest.unstable_mockModule('../../middleware/rateLimit.js', () => ({
  __esModule: true,
  authLimiter: passthrough,
  paymentLimiter: passthrough,
  apiLimiter: passthrough,
  uploadLimiter: passthrough,
  aiLimiter: passthrough,
  aiWriteLimiter: passthrough,
  licenseLimiter: passthrough,
  default: {},
}));
jest.unstable_mockModule('../../middleware/captchaVerify.js', () => ({
  __esModule: true,
  requireCaptcha: passthrough,
  optionalCaptcha: passthrough,
}));
jest.unstable_mockModule('../../services/email.service.js', () => ({
  __esModule: true,
  default: {},
  sendVerificationEmail: () => {},
  sendPasswordResetEmail: () => {},
  sendOTPEmail: () => {},
  sendEmail: () => {},
  sendWelcomeEmail: () => {},
}));
jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  default: {},
  QUEUES: { EMAIL: 'email' },
  enqueue: async () => ({ id: 'job-1' }),
}));
jest.unstable_mockModule('../../middleware/audit.js', () => ({
  __esModule: true,
  recordAudit: async () => {},
  auditTrail: () => passthrough,
}));
jest.unstable_mockModule('passport', () => ({
  __esModule: true,
  default: { authenticate: () => passthrough },
}));

// ── Modules under test ───────────────────────────────────────────────────────
const { default: authRoutes } = await import('../../routes/auth.routes.js');
const { default: errorHandler } = await import('../../middleware/errorHandler.js');

const app = express();
app.disable('x-powered-by');
app.use(cookieParser());
app.use(express.json());
app.use('/api/auth', authRoutes);
app.use(errorHandler);

const post = (path, body) => request(app).post(`/api/auth${path}`).send(body || {});

/** The seeding runs in a fire-and-forget async IIFE, so it has to be awaited. */
async function waitForSeeding() {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (logCalls.warn.some((m) => m.includes('Seeded'))) return;
    if (logCalls.error.some((m) => m.includes('Demo user seed failed'))) {
      throw new Error(logCalls.error.find((m) => m.includes('Demo user seed failed')));
    }
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  throw new Error('demo seeding never completed within 2 s');
}

beforeAll(async () => {
  await waitForSeeding();
});

describe('Demo account seeding (SEED_DEMO_USERS=true, non-production)', () => {
  it('announces exactly the two accounts it created', () => {
    const line = logCalls.warn.find((m) => m.includes('Seeded'));
    expect(line).toContain('Seeded 2 dev-only demo accounts');
    expect(line).toContain('qa-person@example.com');
    expect(line).toContain('qa-admin@example.com');
    expect(line).toContain('must never exist in production');
  });

  it('never writes the demo password to any log level', () => {
    const everything = [...logCalls.info, ...logCalls.warn, ...logCalls.error, ...logCalls.debug];
    expect(everything.join('\n')).not.toContain('DemoPassw0rd!');
  });

  it('logs the demo user in from the in-memory store, with no database row', async () => {
    dbLookups.length = 0;
    const res = await post('/login', {
      email: 'qa-person@example.com',
      password: 'DemoPassw0rd!',
    });

    expect(res.status).toBe(200);
    expect(res.body.user).toEqual({
      id: 1,
      name: 'Demo User',
      email: 'qa-person@example.com',
      role: 'user',
      avatar: expect.any(String),
      preferences: { theme: 'dark', language: 'en' },
      twoFactorEnabled: false,
      betaStatus: 'active',
    });
    expect(res.body.user.password).toBeUndefined();
    expect(jwt.decode(res.body.token).id).toBe(1);
    // The store is consulted only after the (empty) database says nothing.
    expect(dbLookups.map((l) => l.method)).toEqual(['findOne']);
  });

  it('gives the seeded admin the admin role and a refresh cookie', async () => {
    const res = await post('/login', {
      email: 'QA-ADMIN@example.com', // lookup is case-insensitive
      password: 'DemoPassw0rd!',
    });

    expect(res.status).toBe(200);
    expect(res.body.user.role).toBe('admin');
    const cookie = (res.headers['set-cookie'] || []).find((c) => c.startsWith('refresh_token='));
    expect(cookie).toContain('HttpOnly');
    expect(cookie).toContain('SameSite=Lax');
    expect(cookie).toContain('Path=/api/auth');
    expect(cookie).not.toContain('Secure'); // NODE_ENV !== production
  });

  it('rejects the demo accounts with any other password', async () => {
    const res = await post('/login', {
      email: 'qa-admin@example.com',
      password: 'wrong-password',
    });

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid credentials' });
  });

  it('serves protect() from the in-memory store for a demo bearer token', async () => {
    const login = await post('/login', { email: 'qa-person@example.com', password: 'DemoPassw0rd!' });
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', `Bearer ${login.body.token}`);

    expect(res.status).toBe(200);
    expect(res.body.user.email).toBe('qa-person@example.com');
    expect(res.body.user.password).toBeUndefined();
  });

  it('refuses to register an email that a demo account already owns', async () => {
    const res = await post('/register', {
      name: 'Squatter',
      email: 'qa-person@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('User already exists with this email');
  });

  it('refuses an empty password for a demo account before any credential check', async () => {
    const res = await post('/login', { email: 'qa-person@example.com', password: '' });

    // loginSchema.password is min(1); validateRequest now actually runs it, so the
    // request stops at the shape gate instead of spending a bcrypt comparison to
    // arrive at the same answer.
    expect(res.status).toBe(422);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details.map((d) => d.path)).toContain('password');
  });
});
