/**
 * Feature tests — real rate limiting + production-mode behaviour of
 * backend/routes/auth.routes.js
 * ---------------------------------------------------------------------------
 * authRoutes.test.js stubs middleware/rateLimit.js so the handlers can be driven
 * without a throttle. This file mounts the router behind the REAL express-rate-limit
 * stack (MemoryStore, because the Redis double reports "unavailable") and a
 * production environment, which is the only way to exercise:
 *   - the 5 req/min authLimiter, its 429 body and Retry-After header,
 *   - the per-IP key (so one abusive client cannot lock out another),
 *   - the production branches of routes/auth.routes.js:48-50 (the "demo seeding is
 *     disabled" warning), the `secure:` cookie flags and the `debugOtp` gate at
 *     :545 that must never leak an OTP to a client in production.
 */
import express from 'express';
import request from 'supertest';
import cookieParser from 'cookie-parser';
import bcrypt from 'bcryptjs';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';

// ── Import-time environment: production mode is read once by the router ──────
process.env.NODE_ENV = 'production';
process.env.SEED_DEMO_USERS = 'false';
delete process.env.DEMO_USER_PASSWORD;
delete process.env.WAITLIST_MODE;
process.env.JWT_REFRESH_EXPIRE = '12h';
process.env.JWT_SECRET = 'access-secret-for-rate-limit-tests-000000000';
process.env.JWT_REFRESH_SECRET = 'refresh-secret-for-rate-limit-tests-000';

jest.setTimeout(30000);

// ── Redis double: "no Redis" so rateLimit falls back to MemoryStore ──────────
const kv = new Map();
jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  __esModule: true,
  default: () => ({
    async get(key) { return kv.has(key) ? kv.get(key) : null; },
    async set(key, value) { kv.set(key, value); return 'OK'; },
    async del(key) { return kv.delete(key) ? 1 : 0; },
    async sadd() { return 1; },
    async smembers() { return []; },
    async quit() { return 'OK'; },
  }),
  getRedis: () => ({
    async get(key) { return kv.has(key) ? kv.get(key) : null; },
    async set(key, value) { kv.set(key, value); return 'OK'; },
    async del(key) { return kv.delete(key) ? 1 : 0; },
    async sadd() { return 1; },
    async smembers() { return []; },
  }),
  isRedisAvailable: () => false,
  connectRedis: async () => false,
  disconnectRedis: async () => {},
}));

const logCalls = { info: [], warn: [], error: [] };
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: {
    info: (m) => logCalls.info.push(String(m)),
    warn: (m) => logCalls.warn.push(String(m)),
    error: (m) => logCalls.error.push(String(m)),
    debug: () => {},
    http: () => {},
  },
}));

// ── One real-shaped user: reads answer, writes are not needed here ───────────
const rows = [
  {
    id: 7,
    name: 'Prod User',
    email: 'prod@example.com',
    password: bcrypt.hashSync('Sup3rSecret!', 4),
    role: 'user',
    avatar: '',
    isActive: true,
    isVerified: true,
    twoFactorEnabled: false,
    twoFactorMethod: 'email',
    betaStatus: 'active',
    preferences: { theme: 'dark' },
    createdAt: new Date(),
  },
];

function project(row, excluded) {
  const out = {};
  for (const [key, value] of Object.entries(row)) {
    if (!excluded.includes(key)) out[key] = value;
  }
  Object.defineProperty(out, 'comparePassword', {
    enumerable: false,
    value: (candidate) => bcrypt.compare(candidate, row.password),
  });
  Object.defineProperty(out, 'get', {
    enumerable: false,
    value: () => ({ ...out }),
  });
  Object.defineProperty(out, 'save', { enumerable: false, value: async () => out });
  Object.defineProperty(out, 'update', { enumerable: false, value: async () => out });
  return out;
}

const HIDDEN = ['password', 'verificationToken', 'verificationExpires', 'resetPasswordToken', 'resetPasswordExpires'];

jest.unstable_mockModule('../../models/User.js', () => ({
  __esModule: true,
  default: {
    scope(name) {
      const excluded = name === 'withPassword' ? [] : HIDDEN;
      return {
        findOne: async (options = {}) => {
          const row = rows.find((r) => r.email === String(options.where?.email || '').toLowerCase());
          return row ? project(row, excluded) : null;
        },
      };
    },
    findByPk: async (id) => {
      const row = rows.find((r) => String(r.id) === String(id));
      return row ? project(row, HIDDEN) : null;
    },
    findOne: async () => null,
    create: async () => { throw new Error('this suite never writes'); },
    count: async () => 0,
  },
}));

jest.unstable_mockModule('../../middleware/captchaVerify.js', () => ({
  __esModule: true,
  requireCaptcha: (_req, _res, next) => next(),
  optionalCaptcha: (_req, _res, next) => next(),
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
  auditTrail: () => (_req, _res, next) => next(),
}));
jest.unstable_mockModule('passport', () => ({
  __esModule: true,
  default: { authenticate: () => (_req, _res, next) => next() },
}));

// ── Modules under test ───────────────────────────────────────────────────────
const { default: authRoutes } = await import('../../routes/auth.routes.js');
const { default: errorHandler } = await import('../../middleware/errorHandler.js');
const { generateToken } = await import('../../middleware/auth.js');

/** Logged while auth.routes.js was imported — beforeEach wipes the live arrays. */
const BOOT_LOGS = { info: [...logCalls.info], warn: [...logCalls.warn], error: [...logCalls.error] };

const app = express();
app.disable('x-powered-by');
app.set('trust proxy', 1); // so each X-Forwarded-For below is its own bucket
app.set('env', 'production');
app.use(cookieParser());
app.use(express.json());
app.use('/api/auth', authRoutes);
app.use(errorHandler);

let ipCounter = 0;
const freshIp = () => `203.0.113.${(ipCounter += 1) % 254 || 1}`;

const login = (ip, body = { email: 'ghost@example.com', password: 'whatever' }) =>
  request(app)
    .post('/api/auth/login')
    .set('X-Forwarded-For', ip)
    .send(body);

beforeEach(() => {
  kv.clear();
  logCalls.info.length = 0;
  logCalls.warn.length = 0;
  logCalls.error.length = 0;
});

describe('authLimiter (real express-rate-limit, MemoryStore)', () => {
  it('lets five login attempts through and answers 429 on the sixth', async () => {
    const ip = freshIp();
    const statuses = [];
    for (let i = 0; i < 5; i += 1) {
      const attempt = await login(ip);
      statuses.push(attempt.status);
    }
    expect(statuses).toEqual([401, 401, 401, 401, 401]);

    const sixth = await login(ip);
    expect(sixth.status).toBe(429);
    expect(sixth.body).toEqual({
      success: false,
      error: { code: 'RATE_LIMITED', message: 'Too many auth attempts. Try again in a minute.' },
    });
    expect(Number(sixth.headers['retry-after'])).toBeGreaterThan(0);
    expect(Number(sixth.headers['retry-after'])).toBeLessThanOrEqual(60);
  });

  it('counts per client IP: a second client is not punished for the first', async () => {
    const noisy = freshIp();
    for (let i = 0; i < 6; i += 1) await login(noisy);
    expect((await login(noisy)).status).toBe(429);

    const quiet = freshIp();
    expect((await login(quiet)).status).toBe(401);
  });

  it('shares one bucket across every auth route, not just /login', async () => {
    const ip = freshIp();
    const paths = [
      ['post', '/login', { email: 'ghost@example.com', password: 'x' }],
      ['post', '/forgot-password', { email: 'ghost@example.com' }],
      ['post', '/refresh', { refreshToken: 'garbage' }],
      ['post', '/2fa/login-verify', { email: 'ghost@example.com', otp: '123456' }],
      ['post', '/reset-password', { token: 'a'.repeat(64), password: 'ResetPass9' }],
    ];
    for (const [method, path, body] of paths) {
      const req = method === 'post'
        ? request(app).post(`/api/auth${path}`).set('X-Forwarded-For', ip).send(body)
        : request(app).get(`/api/auth${path}`).set('X-Forwarded-For', ip);
      await req;
    }

    // The sixth request of ANY auth route is refused, so five password mistakes
    // also lock out the recovery email for that minute.
    const blocked = await request(app)
      .post('/api/auth/forgot-password')
      .set('X-Forwarded-For', ip)
      .send({ email: 'ghost@example.com' });
    expect(blocked.status).toBe(429);
    expect(blocked.body.error.code).toBe('RATE_LIMITED');
  });

  it('publishes draft-7 rate-limit headers instead of the legacy X-RateLimit ones', async () => {
    const res = await login(freshIp());

    expect(res.headers['ratelimit-policy']).toBe('5;w=60');
    expect(res.headers.ratelimit).toMatch(/limit=\d+/);
    expect(res.headers.ratelimit).toMatch(/remaining=\d+/);
    expect(res.headers.ratelimit).toMatch(/reset=\d+/);
    expect(res.headers['x-ratelimit-limit']).toBeUndefined();
  });

  it('throttles only the limited routes: /profile stays reachable while /login is blocked', async () => {
    const ip = freshIp();
    for (let i = 0; i < 5; i += 1) await login(ip);

    // /profile has no limiter at all: it stays reachable while /login is throttled.
    const profile = await request(app)
      .get('/api/auth/profile')
      .set('X-Forwarded-For', ip)
      .set('Authorization', `Bearer ${generateToken(7)}`);
    expect(profile.status).toBe(200);
    expect((await login(ip)).status).toBe(429);
  });
});

describe('Production-mode behaviour of the router', () => {
  it('warns that demo seeding is disabled and creates no fixed-credential accounts', async () => {
    expect(BOOT_LOGS.warn.join('\n')).toContain(
      'Production mode: demo account seeding is disabled',
    );
    expect(BOOT_LOGS.warn.join('\n')).not.toContain('Seeded');
    expect(BOOT_LOGS.info.join('\n')).not.toContain('Demo accounts are disabled');

    const res = await login(freshIp(), { email: 'demo@lumicorepro.com', password: 'demo1234' });
    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid credentials' });
  });

  it('marks the refresh cookie Secure and ties Max-Age to JWT_REFRESH_EXPIRE=12h', async () => {
    const ip = freshIp();
    const res = await login(ip, { email: 'prod@example.com', password: 'Sup3rSecret!' });

    expect(res.status).toBe(200);
    const cookie = (res.headers['set-cookie'] || []).find((c) => c.startsWith('refresh_token='));
    expect(cookie).toContain('Secure');
    expect(cookie).toContain('HttpOnly');
    expect(cookie).toContain('SameSite=Lax');
    expect(cookie).toContain('Path=/api/auth');
    expect(cookie).toMatch(/Max-Age=43200/);
  });

  it('never leaks the OTP in the response body', async () => {
    const res = await request(app)
      .post('/api/auth/2fa/send-otp')
      .set('X-Forwarded-For', freshIp())
      .set('Authorization', `Bearer ${generateToken(7)}`)
      .send({});

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: '2FA verification code sent to prod@example.com',
    });
    expect(res.body.debugOtp).toBeUndefined();
    expect(JSON.stringify(res.body)).not.toMatch(/\d{6}/);
  });

  it('keeps the stack out of error responses', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('X-Forwarded-For', freshIp())
      .send({ name: 'Boom', email: 'boom@example.com', password: 'Sup3rSecret!' });

    // User.create throws in this suite; the memory fallback still answers 201, so
    // the contract under test is that no internal detail is ever returned.
    expect([201, 500]).toContain(res.status);
    expect(JSON.stringify(res.body)).not.toMatch(/at \w|bcryptjs|node_modules/);
  });
});
