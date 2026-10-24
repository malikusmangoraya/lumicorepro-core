/**
 * Feature tests — backend/routes/auth.routes.js
 * ---------------------------------------------
 * The router is mounted on a real Express app (cookie-parser + json + the real
 * error handler) and driven over HTTP with supertest, so every assertion is about
 * the contract a client actually receives.
 *
 * Deliberately REAL (not stubbed): middleware/auth.js protect()/generateToken,
 * services/refreshToken.service.js (rotation, revocation, reuse detection),
 * utils/otp.js, utils/totp.js, middleware/validateRequest.js + the zod schemas,
 * express-validator, bcryptjs, jsonwebtoken and the canonical response helper.
 *
 * Doubled: the User model (an in-memory store that faithfully mirrors
 * models/User.js: a `password`-excluding defaultScope, a `withPassword` scope and
 * the beforeSave hashing hook — see buildUserModel below), the logger, Redis (an
 * in-memory Map behind the real refresh service), email/queue/audit side effects,
 * the rate limiter (covered for real in authRoutesRateLimit.test.js), the captcha
 * middleware and passport.
 */
import express from 'express';
import request from 'supertest';
import cookieParser from 'cookie-parser';
import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { Op } from 'sequelize';
import { describe, it, expect, beforeEach, afterEach, afterAll, jest } from '@jest/globals';
import { matchesWhere } from '../helpers/sequelizeFakes.js';

// The routes hash with bcrypt's production cost (12) and that costs ~0.7 s per
// operation on this machine's CPU-bound fallback, so the offline-register and
// change-password cases need more than jest's 5 s default.
jest.setTimeout(40000);

// ── Import-time environment ─────────────────────────────────────────────────
// auth.routes.js reads JWT_REFRESH_EXPIRE / SEED_DEMO_USERS / NODE_ENV once while
// it is being imported, so they are pinned before the dynamic import below.
const IMPORT_ENV_KEYS = ['JWT_REFRESH_EXPIRE', 'SEED_DEMO_USERS', 'DEMO_USER_PASSWORD', 'WAITLIST_MODE'];
const ENV_AT_IMPORT = Object.fromEntries(IMPORT_ENV_KEYS.map((k) => [k, process.env[k]]));
for (const key of IMPORT_ENV_KEYS) delete process.env[key];
process.env.JWT_SECRET = 'access-secret-for-auth-route-tests-0000000000';
process.env.JWT_REFRESH_SECRET = 'refresh-secret-for-auth-route-tests-00000000';

// ── In-memory Redis double (the real refresh service runs on top of it) ──────
const kv = new Map();
const sets = new Map();
let redisReadDown = false;
let redisWriteDown = false;

/**
 * Splits the revocation store's failure modes: with writes down a revoke is lost
 * while reads still answer, which is exactly the state a half-dead Redis leaves
 * the session in.
 */
function failRedis({ write = false, read = false } = {}) {
  redisWriteDown = write;
  redisReadDown = read;
}

function redisErr(op, key) {
  return new Error(`Redis command failed: ${op} ${key}`);
}

const redisDouble = {
  isMemory: true,
  async get(key) {
    if (redisReadDown) throw redisErr('GET', key);
    return kv.has(key) ? kv.get(key) : null;
  },
  async set(key, value) {
    if (redisWriteDown) throw redisErr('SET', key);
    kv.set(key, value);
    return 'OK';
  },
  async del(key) {
    if (redisWriteDown) throw redisErr('DEL', key);
    const existed = kv.delete(key) || sets.delete(key);
    return existed ? 1 : 0;
  },
  async sadd(key, member) {
    if (redisWriteDown) throw redisErr('SADD', key);
    const set = sets.get(key) || new Set();
    set.add(member);
    sets.set(key, set);
    return 1;
  },
  async smembers(key) {
    if (redisReadDown) throw redisErr('SMEMBERS', key);
    return [...(sets.get(key) || new Set())];
  },
  async keys() {
    return [...kv.keys()];
  },
  async incrby() {
    return 1;
  },
  async expire() {
    return 1;
  },
  async ttl() {
    return -1;
  },
  async quit() {
    return 'OK';
  },
};

jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  __esModule: true,
  default: () => redisDouble,
  getRedis: () => redisDouble,
  isRedisAvailable: () => false,
  connectRedis: async () => false,
  disconnectRedis: async () => {},
}));

// ── Logger double (silent + assertable) ──────────────────────────────────────
// Import-time boot messages (demo-account seeding) fire once, while the module is
// being loaded, and jest's clearMocks wipes the mock's own call log before every
// test — so every entry is mirrored into a plain array we can snapshot.
const logCalls = { info: [], warn: [], error: [], debug: [], http: [] };
const mockLogger = {
  info: jest.fn((...a) => logCalls.info.push(String(a[0] ?? ''))),
  warn: jest.fn((...a) => logCalls.warn.push(String(a[0] ?? ''))),
  error: jest.fn((...a) => logCalls.error.push(String(a[0] ?? ''))),
  debug: jest.fn((...a) => logCalls.debug.push(String(a[0] ?? ''))),
  http: jest.fn((...a) => logCalls.http.push(String(a[0] ?? ''))),
};
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (v) => v,
}));

// ── Rate limiter: pass-through here, exercised for real elsewhere ───────────
jest.unstable_mockModule('../../middleware/rateLimit.js', () => {
  const passthrough = (_req, _res, next) => next();
  const make = () => passthrough;
  return {
    __esModule: true,
    authLimiter: passthrough,
    paymentLimiter: passthrough,
    apiLimiter: passthrough,
    uploadLimiter: passthrough,
    aiLimiter: passthrough,
    aiWriteLimiter: passthrough,
    licenseLimiter: passthrough,
    default: {
      authLimiter: make,
      paymentLimiter: make,
      apiLimiter: make,
      uploadLimiter: make,
      aiLimiter: make,
      aiWriteLimiter: make,
      licenseLimiter: make,
    },
  };
});

// ── Captcha double: blocks only when a test asks it to ───────────────────────
const captcha = { block: false, verified: null };
jest.unstable_mockModule('../../middleware/captchaVerify.js', () => ({
  __esModule: true,
  TURNSTILE_SITE_KEY: '',
  requireCaptcha: (req, res, next) => {
    if (captcha.block) {
      return res.status(403).json({ success: false, error: { code: 'CAPTCHA_FAILED' } });
    }
    return next();
  },
  optionalCaptcha: (req, res, next) => {
    if (captcha.verified === false) {
      return res.status(403).json({ success: false, error: { code: 'CAPTCHA_FAILED' } });
    }
    req.captchaVerified = true;
    return next();
  },
}));

// ── Email / queue / audit side effects ───────────────────────────────────────
const emailMock = {
  sendPasswordResetEmail: jest.fn(),
  sendVerificationEmail: jest.fn(),
  sendOTPEmail: jest.fn(),
  sendEmail: jest.fn(),
  sendWelcomeEmail: jest.fn(),
};
jest.unstable_mockModule('../../services/email.service.js', () => ({
  __esModule: true,
  ...emailMock,
  default: emailMock,
}));

const queueCalls = [];
const enqueueMock = jest.fn();
jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  __esModule: true,
  QUEUES: {
    EMAIL: 'email',
    AI_GENERATION: 'ai_generation',
    IMAGE_PROCESSING: 'image_processing',
    REPORT: 'report',
    WEBHOOK_RETRY: 'webhook_retry',
    CART_RECOVERY: 'cart_recovery',
  },
  enqueue: enqueueMock,
  getQueue: () => null,
  enqueueEmail: () => {},
  closeQueues: async () => {},
  default: { enqueue: enqueueMock },
}));

const auditMock = jest.fn();
jest.unstable_mockModule('../../middleware/audit.js', () => ({
  __esModule: true,
  recordAudit: auditMock,
  auditTrail: () => (_req, _res, next) => next(),
}));

// ── Passport double ─────────────────────────────────────────────────────────
const passportState = { strategy: null, options: null, user: null, error: null };
const passportMock = { authenticate: jest.fn() };
jest.unstable_mockModule('passport', () => ({
  __esModule: true,
  default: passportMock,
}));

// ── User model double ────────────────────────────────────────────────────────
/** Columns the real model hides behind its defaultScope (models/User.js). */
const DEFAULT_EXCLUDED = [
  'password',
  'verificationToken',
  'verificationExpires',
  'resetPasswordToken',
  'resetPasswordExpires',
];

const rows = [];
const modelCalls = [];
let dbDown = false;
let writesDown = false;
let writesAllowedBeforeFailing = 0;

class DbOffline extends Error {}
class WriteOffline extends Error {}

function assertUp() {
  if (dbDown) throw new DbOffline('connect ECONNREFUSED 127.0.0.1:5432');
}

/**
 * Reads keep answering while writes fail — the half-dead database a real Postgres
 * gives you (lock timeouts, read-only replicas). `failWritesAfter(n)` lets the
 * first n writes through, so a route whose INSERT must succeed before its UPDATE
 * can be pushed into exactly that state.
 */
function assertWritesUp() {
  if (!writesDown) return;
  if (writesAllowedBeforeFailing > 0) {
    writesAllowedBeforeFailing -= 1;
    return;
  }
  throw new WriteOffline('could not serialize access due to concurrent update');
}

function failWritesAfter(allowed = 0) {
  writesDown = true;
  writesAllowedBeforeFailing = allowed;
}

/** models/User.js beforeSave hook: a changed password is bcrypt-hashed. */
function hashIfNeeded(row) {
  if (typeof row.password === 'string' && !row.password.startsWith('$2')) {
    // rounds 4 instead of production's 12 — the assertion is "hashed", not speed
    row.password = bcrypt.hashSync(row.password, 4);
  }
}

function makeInstance(row, excluded) {
  const instance = {};
  for (const [key, value] of Object.entries(row)) {
    if (!excluded.includes(key)) instance[key] = value;
  }

  Object.defineProperty(instance, 'comparePassword', {
    enumerable: false,
    value: async function comparePassword(candidate) {
      // mirrors models/User.js: bcrypt.compare(candidate, this.password)
      return bcrypt.compare(candidate, this.password);
    },
  });
  Object.defineProperty(instance, 'toJSON', {
    enumerable: false,
    value: () => ({ ...instance }),
  });
  Object.defineProperty(instance, 'get', {
    enumerable: false,
    value: () => ({ ...instance }),
  });
  Object.defineProperty(instance, 'update', {
    enumerable: false,
    value: async (values) => {
      assertWritesUp();
      assertUp();
      modelCalls.push({ method: 'update', id: row.id, values });
      Object.assign(row, values);
      hashIfNeeded(row);
      for (const [key, value] of Object.entries(row)) {
        if (!excluded.includes(key)) instance[key] = value;
      }
      return instance;
    },
  });
  Object.defineProperty(instance, 'save', {
    enumerable: false,
    value: async (options) => {
      assertWritesUp();
      assertUp();
      modelCalls.push({ method: 'save', id: row.id, options });
      const changed = {};
      for (const key of Object.keys(instance)) {
        if (!excluded.includes(key) && row[key] !== instance[key]) changed[key] = instance[key];
      }
      Object.assign(row, changed);
      hashIfNeeded(row);
      return instance;
    },
  });
  return instance;
}

function viewFor(excluded, scopeName) {
  const view = {
    async findOne(options = {}) {
      assertUp();
      modelCalls.push({ method: 'findOne', scope: scopeName, options });
      const row = rows.find((r) => matchesWhere(r, options.where));
      return row ? makeInstance(row, excluded) : null;
    },
    async findByPk(id, options = {}) {
      assertUp();
      modelCalls.push({ method: 'findByPk', scope: scopeName, id, options });
      const row = rows.find((r) => String(r.id) === String(id));
      if (!row) return null;
      const extraExcluded = (options.attributes && options.attributes.exclude) || [];
      return makeInstance(row, [...excluded, ...extraExcluded]);
    },
    async count(options = {}) {
      assertUp();
      modelCalls.push({ method: 'count', scope: scopeName, options });
      return rows.filter((r) => matchesWhere(r, options.where)).length;
    },
    async create(values = {}, options = {}) {
      assertWritesUp();
      assertUp();
      modelCalls.push({ method: 'create', scope: scopeName, values, options });
      const row = {
        id: rows.reduce((max, r) => Math.max(max, Number(r.id) || 0), 0) + 1,
        isActive: true,
        isVerified: false,
        twoFactorEnabled: false,
        avatar: '',
        preferences: {},
        createdAt: new Date(),
        ...values,
      };
      hashIfNeeded(row);
      rows.push(row);
      return makeInstance(row, excluded);
    },
  };
  return view;
}

const defaultView = viewFor(DEFAULT_EXCLUDED, 'defaultScope');
const passwordView = viewFor([], 'withPassword');

const UserMock = {
  scope: jest.fn(),
  findOne: jest.fn(),
  findByPk: jest.fn(),
  create: jest.fn(),
  count: jest.fn(),
};

jest.unstable_mockModule('../../models/User.js', () => ({
  __esModule: true,
  default: UserMock,
}));

// ── Modules under test (real, except the doubles above) ──────────────────────
const { default: authRoutes } = await import('../../routes/auth.routes.js');
const { default: errorHandler, notFound } = await import('../../middleware/errorHandler.js');
const { generateToken } = await import('../../middleware/auth.js');
const { generateTOTP } = await import('../../utils/totp.js');
const { generateOTP } = await import('../../utils/otp.js');
const { registerSchema, loginSchema } = await import('../../middleware/validations/index.js');

/** Boot-time log lines emitted while auth.routes.js was imported. */
const BOOT_LOGS = { info: [...logCalls.info], warn: [...logCalls.warn], error: [...logCalls.error] };

const FRONTEND_URL = 'https://shop.test';

const app = express();
app.disable('x-powered-by');
app.use(cookieParser());
app.use(express.json());
app.use('/api/auth', authRoutes);
app.use(notFound);
app.use(errorHandler);

const post = (path, body, token) => {
  const req = request(app).post(`/api/auth${path}`);
  if (token) req.set('Authorization', `Bearer ${token}`);
  return req.send(body || {});
};
const get = (path, token) => {
  const req = request(app).get(`/api/auth${path}`);
  if (token) req.set('Authorization', `Bearer ${token}`);
  return req;
};
const put = (path, body, token) => {
  const req = request(app).put(`/api/auth${path}`);
  if (token) req.set('Authorization', `Bearer ${token}`);
  return req.send(body || {});
};

/** Seed a user row exactly the way the model would persist it. */
function seedUser(overrides = {}) {
  const row = {
    id: rows.reduce((max, r) => Math.max(max, Number(r.id) || 0), 0) + 1,
    name: 'Seed User',
    email: `seed${rows.length + 1}@example.com`,
    password: 'SecretPass123',
    role: 'user',
    avatar: '',
    isActive: true,
    isVerified: false,
    twoFactorEnabled: false,
    twoFactorMethod: 'email',
    betaStatus: 'active',
    preferences: { theme: 'dark', language: 'en' },
    createdAt: new Date(),
    ...overrides,
  };
  hashIfNeeded(row);
  rows.push(row);
  return row;
}

const rowByEmail = (email) => rows.find((r) => r.email === String(email).toLowerCase());
const rowById = (id) => rows.find((r) => String(r.id) === String(id));
const cookieValue = (res, name) => {
  const raw = (res.headers['set-cookie'] || []).find((c) => c.startsWith(`${name}=`));
  return raw ? raw.split(';')[0].slice(name.length + 1) : undefined;
};
const cookieHeader = (res, name) =>
  (res.headers['set-cookie'] || []).find((c) => c.startsWith(`${name}=`)) || '';
const isRevoked = (jti) => kv.has(`refresh:revoked:${jti}`);
const jtiOf = (token) => jwt.decode(token).jti;

const TRACKED_ENV = [
  'WAITLIST_MODE',
  'WAITLIST_AUTO_APPROVE_DAILY',
  'FRONTEND_URL',
  'NODE_ENV',
  'JWT_EXPIRE',
  'APP_BRAND',
];

/**
 * Emulates the user row being deleted between protect()'s lookup and the
 * handler's: the first findByPk answers, every later one returns null. This is
 * the only way a route-level "User not found" 404 is reachable behind protect().
 */
function armMidRequestDeletion() {
  const real = UserMock.findByPk.getMockImplementation();
  let seen = 0;
  UserMock.findByPk.mockImplementation((id, options) => {
    seen += 1;
    if (seen === 1) return real(id, options);
    return Promise.resolve(null);
  });
}

let envSnapshot;

beforeEach(() => {
  envSnapshot = Object.fromEntries(TRACKED_ENV.map((k) => [k, process.env[k]]));
  process.env.FRONTEND_URL = FRONTEND_URL;
  delete process.env.WAITLIST_MODE;
  delete process.env.WAITLIST_AUTO_APPROVE_DAILY;
  delete process.env.JWT_EXPIRE;
  delete process.env.APP_BRAND;

  rows.length = 0;
  modelCalls.length = 0;
  queueCalls.length = 0;
  dbDown = false;
  writesDown = false;
  writesAllowedBeforeFailing = 0;
  kv.clear();
  sets.clear();
  redisReadDown = false;
  redisWriteDown = false;
  captcha.block = false;
  captcha.verified = null;
  passportState.strategy = null;
  passportState.options = null;
  passportState.user = null;
  passportState.error = null;

  // jest.config clears implementations between tests, so every double is
  // (re)bound here — a top-level `jest.fn(impl)` would silently return undefined.
  mockLogger.info.mockImplementation((msg) => logCalls.info.push(String(msg)));
  mockLogger.warn.mockImplementation((msg) => logCalls.warn.push(String(msg)));
  mockLogger.error.mockImplementation((msg) => logCalls.error.push(String(msg)));
  mockLogger.debug.mockImplementation((msg) => logCalls.debug.push(String(msg)));
  mockLogger.http.mockImplementation((msg) => logCalls.http.push(String(msg)));

  emailMock.sendVerificationEmail.mockResolvedValue(undefined);
  emailMock.sendPasswordResetEmail.mockResolvedValue(undefined);
  emailMock.sendOTPEmail.mockResolvedValue(undefined);
  emailMock.sendEmail.mockResolvedValue(undefined);
  emailMock.sendWelcomeEmail.mockResolvedValue(undefined);
  enqueueMock.mockImplementation((queue, payload) => {
    queueCalls.push({ queue, payload });
    return Promise.resolve({ id: 'job-1' });
  });
  auditMock.mockResolvedValue(undefined);

  UserMock.scope.mockImplementation((name) =>
    name === 'withPassword' ? passwordView : defaultView,
  );
  UserMock.findOne.mockImplementation((options) => defaultView.findOne(options));
  UserMock.findByPk.mockImplementation((id, options) => defaultView.findByPk(id, options));
  UserMock.create.mockImplementation((values, options) => defaultView.create(values, options));
  UserMock.count.mockImplementation((options) => defaultView.count(options));

  passportMock.authenticate.mockImplementation((strategy, optionsOrCb, maybeCb) => {
    const callback = typeof optionsOrCb === 'function' ? optionsOrCb : maybeCb;
    return (req, res, next) => {
      passportState.strategy = strategy;
      passportState.options = typeof optionsOrCb === 'function' ? undefined : optionsOrCb;
      if (!callback) return res.status(302).json({ strategy, started: true });
      return callback(passportState.error, passportState.user, req, res, next);
    };
  });
});

afterEach(() => {
  for (const key of TRACKED_ENV) {
    if (envSnapshot[key] === undefined) delete process.env[key];
    else process.env[key] = envSnapshot[key];
  }
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /api/auth/register', () => {
  it('creates the user, returns a 15-minute JWT and never the password', async () => {
    const res = await post('/register', {
      name: 'Ada Lovelace',
      email: 'Ada@Example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.user).toEqual({
      id: 1,
      name: 'Ada Lovelace',
      email: 'ada@example.com',
      role: 'user',
      avatar: '',
      preferences: {},
    });
    expect(JSON.stringify(res.body)).not.toMatch(/Sup3rSecret/);
    expect(res.body.user.password).toBeUndefined();

    const decoded = jwt.decode(res.body.token);
    expect(decoded.id).toBe(1);
    expect(decoded.exp - decoded.iat).toBe(15 * 60); // AGENTS.md §3: 15 min access
    expect(() => jwt.verify(res.body.token, process.env.JWT_SECRET, { algorithms: ['HS256'] }))
      .not.toThrow();
  });

  it('hands the raw password to the model so the beforeSave hook hashes it', async () => {
    await post('/register', { name: 'Grace', email: 'grace@example.com', password: 'Sup3rSecret!' });

    const create = modelCalls.find((c) => c.method === 'create');
    expect(create.values).toEqual({
      name: 'Grace',
      email: 'grace@example.com',
      password: 'Sup3rSecret!',
      role: 'user',
      betaStatus: 'active',
    });
    // persisted column is a bcrypt digest, not the plaintext
    expect(rowByEmail('grace@example.com').password).toMatch(/^\$2[aby]\$/);
    expect(rowByEmail('grace@example.com').password).not.toContain('Sup3rSecret');
  });

  it('sends the refresh token as a HttpOnly SameSite=Lax cookie scoped to /api/auth', async () => {
    const res = await post('/register', {
      name: 'Cookie',
      email: 'cookie@example.com',
      password: 'Sup3rSecret!',
    });

    const raw = cookieHeader(res, 'refresh_token');
    expect(raw).toContain('HttpOnly');
    expect(raw).toContain('SameSite=Lax');
    expect(raw).toContain('Path=/api/auth');
    expect(raw).toContain('Max-Age=604800'); // 7 days, the documented refresh TTL
    expect(raw).not.toContain('Secure'); // non-production
    expect(jwt.decode(cookieValue(res, 'refresh_token'))).toEqual(
      expect.objectContaining({ sub: '1', type: 'refresh' }),
    );
  });

  it('rejects an email that is already taken and does not create a second row', async () => {
    seedUser({ email: 'dup@example.com' });
    const res = await post('/register', {
      name: 'Dup',
      email: 'dup@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'User already exists with this email' });
    expect(rows).toHaveLength(1);
    expect(modelCalls.some((c) => c.method === 'create')).toBe(false);
  });

  // FIXED 2026-10-23 (middleware/validateRequest.js): the helper read
  // `{ body, query, params }` off the schema object, but Zod keeps them on
  // `.shape`, so all three destructured to `undefined` and the middleware called
  // next() without parsing anything. Every call site was affected:
  // routes/auth.routes.js:131 & :241, routes/order.routes.js:129 & :182.
  it('applies registerSchema: a malformed body never becomes a row', async () => {
    expect(registerSchema.shape.body.safeParse({ name: '', email: 'not-an-email', password: '123' }).success)
      .toBe(false);

    const res = await post('/register', { name: '', email: 'not-an-email', password: '123' });

    expect(res.status).toBe(422);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details.map((d) => d.path)).toEqual(
      expect.arrayContaining(['name', 'email', 'password'])
    );
    expect(rows).toHaveLength(0);
  });

  it('rejects a client-supplied admin role at the schema, before the route ternary', async () => {
    expect(registerSchema.shape.body.safeParse({
      name: 'Mallory', email: 'mallory@example.com', password: 'Sup3rSecret!', role: 'admin',
    }).success).toBe(false);

    const res = await post('/register', {
      name: 'Mallory',
      email: 'mallory@example.com',
      password: 'Sup3rSecret!',
      role: 'admin',
    });

    // The enum is now the first gate; the ternary at routes/auth.routes.js:165
    // stays as defence in depth for a role that does pass (see the vendor test).
    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('role');
    expect(rows).toHaveLength(0);
  });

  it('accepts the vendor role and ignores unknown mass-assignment fields', async () => {
    const res = await post('/register', {
      name: 'Vendor',
      email: 'vendor@example.com',
      password: 'Sup3rSecret!',
      role: 'vendor',
      isActive: false,
      id: 999,
    });

    expect(res.status).toBe(201);
    const create = modelCalls.find((c) => c.method === 'create');
    expect(Object.keys(create.values).sort()).toEqual(
      ['betaStatus', 'email', 'name', 'password', 'role'].sort(),
    );
    expect(create.values.role).toBe('vendor');
    expect(rowByEmail('vendor@example.com').isActive).toBe(true);
  });

  it('persists an email-verification token and emails exactly that token', async () => {
    const res = await post('/register', {
      name: 'Verify',
      email: 'verify@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(201);
    const row = rowByEmail('verify@example.com');
    expect(row.verificationToken).toMatch(/^[0-9a-f]{64}$/);
    const ttlMs = row.verificationExpires.getTime() - Date.now();
    expect(ttlMs).toBeGreaterThan(23 * 3600 * 1000);
    expect(ttlMs).toBeLessThanOrEqual(24 * 3600 * 1000);
    expect(emailMock.sendVerificationEmail).toHaveBeenCalledWith(
      'verify@example.com',
      'Verify',
      row.verificationToken,
    );
  });

  it('queues a welcome email job', async () => {
    await post('/register', { name: 'Newbie', email: 'newbie@example.com', password: 'Sup3rSecret!' });

    expect(queueCalls).toHaveLength(1);
    expect(queueCalls[0].queue).toBe('email');
    expect(queueCalls[0].payload.to).toBe('newbie@example.com');
    expect(queueCalls[0].payload.subject).toBe('Welcome');
  });

  it('records an auth.register audit entry', async () => {
    await post('/register', { name: 'Audit', email: 'audit@example.com', password: 'Sup3rSecret!' });

    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.register', email: 'audit@example.com' }),
    );
  });

  it('puts signups on the waitlist when WAITLIST_MODE is on and the cap is spent', async () => {
    seedUser({ email: 'approved@example.com', betaStatus: 'active' });
    process.env.WAITLIST_MODE = 'true';
    process.env.WAITLIST_AUTO_APPROVE_DAILY = '0';

    const res = await post('/register', {
      name: 'Waiting',
      email: 'waiting@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(201);
    expect(rowByEmail('waiting@example.com').betaStatus).toBe('waitlist');
    const count = modelCalls.find((c) => c.method === 'count');
    expect(count.options.where.betaStatus).toBe('active');
    expect(count.options.where.createdAt[Op.gte]).toBeInstanceOf(Date);
  });

  it('auto-approves while the daily cap still has room', async () => {
    seedUser({ email: 'approved2@example.com', betaStatus: 'active' });
    process.env.WAITLIST_MODE = 'true';
    process.env.WAITLIST_AUTO_APPROVE_DAILY = '5';

    await post('/register', {
      name: 'Auto',
      email: 'auto@example.com',
      password: 'Sup3rSecret!',
    });

    expect(rowByEmail('auto@example.com').betaStatus).toBe('active');
  });

  it('blocks the handler entirely when captcha verification fails', async () => {
    captcha.block = true;
    const res = await post('/register', {
      name: 'Bot',
      email: 'bot@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(403);
    expect(res.body.error.code).toBe('CAPTCHA_FAILED');
    expect(rows).toHaveLength(0);
    expect(modelCalls).toHaveLength(0);
  });

  it('falls back to the in-memory store and still logs the user in when Postgres is down', async () => {
    dbDown = true;
    const res = await post('/register', {
      name: 'Offline',
      email: 'offline@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(201);
    expect(mockLogger.warn).toHaveBeenCalledWith(expect.stringContaining('memory'));
    expect(res.body.user.email).toBe('offline@example.com');

    // offline users authenticate and pass protect() through the shared store
    const login = await post('/login', { email: 'offline@example.com', password: 'Sup3rSecret!' });
    expect(login.status).toBe(200);
    const profile = await get('/profile', login.body.token);
    expect(profile.status).toBe(200);
    expect(profile.body.user.email).toBe('offline@example.com');
    expect(profile.body.user.password).toBeUndefined();
  });

  it('never writes the plaintext password to the log', async () => {
    await post('/register', { name: 'Quiet', email: 'quiet@example.com', password: 'Sup3rSecret!' });

    const everything = [...logCalls.info, ...logCalls.warn, ...logCalls.error];
    expect(everything.join('\n')).not.toMatch(/Sup3rSecret/);
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /api/auth/login', () => {
  it('issues an access token, a refresh token and stamps lastLogin', async () => {
    const user = seedUser({ email: 'ada@example.com', password: 'Sup3rSecret!' });
    const res = await post('/login', { email: 'ADA@example.com', password: 'Sup3rSecret!' });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.user).toEqual({
      id: user.id,
      name: 'Seed User',
      email: 'ada@example.com',
      role: 'user',
      avatar: '',
      preferences: { theme: 'dark', language: 'en' },
      twoFactorEnabled: false,
      betaStatus: 'active',
    });
    expect(jwt.decode(res.body.token).id).toBe(user.id);
    expect(cookieValue(res, 'refresh_token')).toBe(res.body.refreshToken);
    expect(rowByEmail('ada@example.com').lastLogin).toBeInstanceOf(Date);
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.login.success', userId: user.id }),
    );
  });

  it('looks the account up through the withPassword scope', async () => {
    seedUser({ email: 'scope@example.com' });
    await post('/login', { email: 'scope@example.com', password: 'Sup3rSecret!' });

    expect(UserMock.scope).toHaveBeenCalledWith('withPassword');
    const findOne = modelCalls.find((c) => c.method === 'findOne');
    expect(findOne.options.where).toEqual({ email: 'scope@example.com' });
  });

  it('gives an unknown email and a wrong password the identical 401 body', async () => {
    seedUser({ email: 'target@example.com', password: 'Sup3rSecret!' });

    const unknown = await post('/login', { email: 'nobody@example.com', password: 'whatever1' });
    const wrong = await post('/login', { email: 'target@example.com', password: 'wrong-password' });

    expect(unknown.status).toBe(401);
    expect(wrong.status).toBe(401);
    expect(wrong.body).toEqual(unknown.body);
    expect(wrong.body).toEqual({ success: false, error: 'Invalid credentials' });
    expect(JSON.stringify(wrong.body)).not.toMatch(/password|email/i);
  });

  it('audits a failed login with the attempted email but not the password', async () => {
    seedUser({ email: 'audit2@example.com', password: 'Sup3rSecret!' });
    await post('/login', { email: 'audit2@example.com', password: 'guess-it' });

    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.login.failure', email: 'audit2@example.com' }),
    );
    // Only the metadata argument is stringified: the first argument is the raw
    // req, which is circular by construction.
    const audited = auditMock.mock.calls.map(([, meta]) => JSON.stringify(meta)).join('');
    expect(audited).toContain('auth.login.failure');
    expect(audited).not.toMatch(/guess-it/);
  });

  it('rejects a deactivated account', async () => {
    seedUser({ email: 'banned@example.com', isActive: false });
    const res = await post('/login', { email: 'banned@example.com', password: 'Sup3rSecret!' });

    expect(res.status).toBe(401);
    expect(res.body).toEqual({
      success: false,
      error: 'Account has been deactivated. Please contact support.',
    });
  });

  it('BUG: emails an undefined OTP at login, so 2FA logins cannot be completed', async () => {
    seedUser({ email: 'twofa@example.com', password: 'Sup3rSecret!', twoFactorEnabled: true });
    const res = await post('/login', { email: 'twofa@example.com', password: 'Sup3rSecret!' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      requires2FA: true,
      message: 'Two-factor authentication required. OTP sent to your email.',
      user: { id: 1, name: 'Seed User', email: 'twofa@example.com' },
    });
    expect(res.body.token).toBeUndefined();
    expect(cookieValue(res, 'refresh_token')).toBeUndefined();

    const [otpEmail, otpCode] = emailMock.sendOTPEmail.mock.calls[0];
    expect(otpEmail).toBe('twofa@example.com');
    // BUG (routes/auth.routes.js:274): `const { code } = generateOTP(user.email)`
    // destructures `.code` off a STRING — utils/otp.js:27 returns the code itself,
    // and the two other call sites (:485, :538) use it correctly. The OTP email
    // therefore always carries `undefined`, and the account is locked out at the
    // 2FA wall with nothing to enter.
    expect(otpCode).toBeUndefined();

    // Replace the unknowable login code so the guess below cannot collide with it.
    const mine = generateOTP('twofa@example.com');
    const wrong = mine === '000000' ? '111111' : '000000';
    const attempt = await post('/2fa/login-verify', { email: 'twofa@example.com', otp: wrong });
    expect(attempt.status).toBe(401);
    expect(attempt.body).toEqual({ success: false, error: 'Invalid or expired 2FA code' });
  });

  it('rejects a missing password with 422 instead of probing the credentials store', async () => {
    expect(loginSchema.shape.body.safeParse({ email: 'someone@example.com' }).success).toBe(false);

    const res = await post('/login', { email: 'someone@example.com' });

    // FIXED 2026-10-23: validateRequest used to be a no-op, so this reached the
    // handler and burned a bcrypt comparison on an empty password before answering
    // the generic 401. The schema now rejects the shape first.
    expect(res.status).toBe(422);
    expect(res.body.code).toBe('VALIDATION_ERROR');
    expect(res.body.details.map((d) => d.path)).toContain('password');
  });

  it('rejects a malformed email with 422 rather than a lookup miss', async () => {
    const res = await post('/login', { email: 'not-an-email', password: 'Sup3rSecret!' });

    expect(res.status).toBe(422);
    expect(res.body.details.map((d) => d.path)).toContain('email');
  });

  it('answers 401 (not 500) when the user lookup blows up', async () => {
    dbDown = true;
    const res = await post('/login', { email: 'ghost@example.com', password: 'whatever' });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Invalid credentials');
    expect(mockLogger.warn).toHaveBeenCalledWith(expect.stringContaining('falling back'));
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /api/auth/refresh — rotation & revocation', () => {
  async function loginForTokens(email = 'rot@example.com') {
    seedUser({ email, password: 'Sup3rSecret!' });
    const res = await post('/login', { email, password: 'Sup3rSecret!' });
    expect(res.status).toBe(200);
    return res.body.refreshToken;
  }

  it('rotates the refresh token and revokes the previous one', async () => {
    const oldRefresh = await loginForTokens();
    const oldJti = jtiOf(oldRefresh);

    const res = await post('/refresh', { refreshToken: oldRefresh });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.token).toBeTruthy();
    expect(res.body.refreshToken).not.toBe(oldRefresh);
    expect(isRevoked(oldJti)).toBe(true);
    expect(cookieValue(res, 'refresh_token')).toBe(res.body.refreshToken);
    expect(jwt.verify(res.body.token, process.env.JWT_SECRET, { algorithms: ['HS256'] })).toEqual(
      expect.objectContaining({ id: 1 }),
    );
    // the old access token is a different signature domain: refresh uses its own secret
    expect(jwt.decode(oldRefresh).type).toBe('refresh');
  });

  it('accepts the httpOnly cookie when no body token is sent', async () => {
    const oldRefresh = await loginForTokens('cookie@example.com');
    const res = await request(app)
      .post('/api/auth/refresh')
      .set('Cookie', `refresh_token=${oldRefresh}`)
      .send({});

    expect(res.status).toBe(200);
    expect(isRevoked(jtiOf(oldRefresh))).toBe(true);
  });

  it('rejects a request with no refresh token at all', async () => {
    const res = await post('/refresh', {});

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'No refresh token provided' });
  });

  it('rejects a forged/garbage refresh token', async () => {
    const res = await post('/refresh', { refreshToken: 'not.a.jwt' });

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid or expired refresh token' });
  });

  it('rejects an access token presented as a refresh token', async () => {
    const res = await post('/refresh', { refreshToken: generateToken(1) });

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid or expired refresh token' });
  });

  it('rejects a token signed with the refresh secret but not of type refresh', async () => {
    const forged = jwt.sign(
      { sub: '1', type: 'access', jti: 'jti-access' },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: '1h' },
    );
    const res = await post('/refresh', { refreshToken: forged });

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid token type' });
  });

  it('rejects an expired refresh token', async () => {
    const expired = jwt.sign(
      { sub: '1', type: 'refresh', jti: 'jti-expired' },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: -60 },
    );
    const res = await post('/refresh', { refreshToken: expired });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Invalid or expired refresh token');
  });

  it('revokes the family when a rotated token is replayed (reuse detection)', async () => {
    const oldRefresh = await loginForTokens('reuse@example.com');
    const oldJti = jtiOf(oldRefresh);

    const rotated = await post('/refresh', { refreshToken: oldRefresh });
    expect(rotated.status).toBe(200);
    const newJti = jtiOf(rotated.body.refreshToken);

    const replay = await post('/refresh', { refreshToken: oldRefresh });
    expect(replay.status).toBe(401);
    expect(replay.body.error).toBe('Refresh token has been revoked. Please log in again.');
    expect(mockLogger.warn).toHaveBeenCalledWith(expect.stringContaining('reuse detected'));
    expect(isRevoked(newJti)).toBe(false);

    // SECURITY GAP captured as-is: generateRefreshToken() carries no familyId
    // claim, so every rotation starts a brand-new family and revokeFamily()
    // cannot reach the token the thief just received. It still validates.
    const descendant = await post('/refresh', { refreshToken: rotated.body.refreshToken });
    expect(descendant.status).toBe(200);
  });

  it('refuses to refresh for a deactivated or deleted account', async () => {
    const refreshToken = await loginForTokens('dead@example.com');
    rowByEmail('dead@example.com').isActive = false;

    const res = await post('/refresh', { refreshToken });
    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Account is not active' });
  });

  it('401s when the token subject no longer exists', async () => {
    const orphan = jwt.sign(
      { sub: '4242', type: 'refresh', jti: 'jti-orphan' },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: '1d' },
    );
    const res = await post('/refresh', { refreshToken: orphan });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Account is not active');
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /api/auth/logout', () => {
  it('revokes the presented refresh token and clears the cookie', async () => {
    seedUser({ email: 'bye@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'bye@example.com', password: 'Sup3rSecret!' });
    const refreshToken = login.body.refreshToken;

    const res = await request(app)
      .post('/api/auth/logout')
      .set('Cookie', `refresh_token=${refreshToken}`)
      .send({});

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Logged out successfully' });
    expect(isRevoked(jtiOf(refreshToken))).toBe(true);
    expect(cookieValue(res, 'refresh_token')).toBe('');

    const reused = await post('/refresh', { refreshToken });
    expect(reused.status).toBe(401);
  });

  it('revokes a token supplied in the body', async () => {
    const refreshToken = jwt.sign(
      { sub: '7', type: 'refresh', jti: 'jti-body' },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: '1d' },
    );
    const res = await post('/logout', { refreshToken });

    expect(res.status).toBe(200);
    expect(isRevoked('jti-body')).toBe(true);
  });

  it('is idempotent: nothing to revoke still logs out cleanly', async () => {
    const res = await post('/logout', {});

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(kv.size).toBe(0);
  });

  it('ignores an expired or forged token instead of failing', async () => {
    const res = await post('/logout', { refreshToken: 'garbage.token.value' });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('GET/PUT /api/auth/profile', () => {
  it('returns the profile without any credential material', async () => {
    const user = seedUser({
      email: 'prof@example.com',
      verificationToken: 'a'.repeat(64),
      resetPasswordToken: 'b'.repeat(64),
    });
    const res = await get('/profile', generateToken(user.id));

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.user.email).toBe('prof@example.com');
    expect(res.body.user.password).toBeUndefined();
    // real Sequelize strips these via defaultScope; assert the route strips
    // `password` from the object it got back
    const serialized = JSON.stringify(res.body);
    expect(serialized).not.toMatch(/\$2[aby]\$/);
    expect(serialized).not.toContain('a'.repeat(64));
    expect(serialized).not.toContain('b'.repeat(64));
  });

  it('401s with no Authorization header', async () => {
    const res = await get('/profile');

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Not authorized, no token' });
  });

  it('401s on a tampered signature', async () => {
    const user = seedUser({ email: 'tamper@example.com' });
    const forged = `${generateToken(user.id).split('.').slice(0, 2).join('.')}.Zm9yZ2Vk`;
    const res = await get('/profile', forged);

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Not authorized, token failed' });
  });

  it('401s an alg=none token (algorithm pinned to HS256)', async () => {
    const noneToken = `${Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' }))
      .toString('base64url')}.${Buffer.from(JSON.stringify({ id: 1 }))
      .toString('base64url')}.`;
    const res = await get('/profile', noneToken);

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Not authorized, token failed');
  });

  it('401s an expired access token', async () => {
    const expired = jwt.sign({ id: 1 }, process.env.JWT_SECRET, { expiresIn: -60 });
    const res = await get('/profile', expired);

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Not authorized, token failed');
  });

  it('401s a token whose user has disappeared', async () => {
    const res = await get('/profile', generateToken(9999));

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });

  it('401s a deactivated user even with a valid unexpired token', async () => {
    const user = seedUser({ email: 'off@example.com', isActive: false });
    const res = await get('/profile', generateToken(user.id));

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'User account is deactivated' });
  });

  it('updates only the allow-listed profile fields', async () => {
    const user = seedUser({ email: 'edit@example.com', role: 'user' });
    const res = await put(
      '/profile',
      {
        name: 'New Name',
        phone: '+1 555 0100',
        avatar: 'https://cdn.test/a.png',
        address: { city: 'Lahore' },
        preferences: { theme: 'light' },
        role: 'admin',
        isActive: false,
        password: 'hacked',
      },
      generateToken(user.id),
    );

    expect(res.status).toBe(200);
    expect(res.body.user.name).toBe('New Name');
    expect(res.body.user.preferences).toEqual({ theme: 'light' });
    expect(res.body.user.password).toBeUndefined();
    const row = rowByEmail('edit@example.com');
    expect(row.role).toBe('user');
    expect(row.isActive).toBe(true);
    expect(row.password).not.toBe('hacked');
  });

  it('404s when the authenticated user has been removed mid-session', async () => {
    const user = seedUser({ email: 'vanish@example.com' });
    const token = generateToken(user.id);
    // protect() still resolves the user; the handler's own lookup then misses it.
    armMidRequestDeletion();

    const res = await put('/profile', { name: 'Ghost' }, token);
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
    // The update never happened — the row is untouched.
    expect(rowByEmail('vanish@example.com').name).toBe('Seed User');
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('2FA — email OTP routes', () => {
  it('POST /2fa/setup currently 500s: Buffer.toString has no base32 encoding', async () => {
    const user = seedUser({ email: 'setup2fa@example.com' });
    const res = await post('/2fa/setup', { method: 'email' }, generateToken(user.id));

    // BUG (routes/auth.routes.js:477) — crypto.randomBytes(10).toString('base32')
    // throws ERR_UNKNOWN_ENCODING, so email-2FA enrolment never completes.
    // The row is left untouched, i.e. 2FA is NOT silently half-enabled.
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(rowByEmail('setup2fa@example.com').twoFactorEnabled).toBe(false);
  });

  it('POST /2fa/setup requires authentication', async () => {
    const res = await post('/2fa/setup', {});
    expect(res.status).toBe(401);
  });

  it('POST /2fa/send-otp emails a fresh 6-digit code', async () => {
    const user = seedUser({ email: 'resend2fa@example.com', twoFactorEnabled: true });
    const res = await post('/2fa/send-otp', {}, generateToken(user.id));

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('2FA verification code sent to resend2fa@example.com');
    const [to, code] = emailMock.sendOTPEmail.mock.calls[0];
    expect(to).toBe('resend2fa@example.com');
    expect(code).toMatch(/^\d{6}$/);
    expect(res.body.debugOtp).toBe(code); // dev-only leak, gated on NODE_ENV
  });

  it('POST /2fa/confirm activates 2FA with the emailed OTP', async () => {
    const user = seedUser({ email: 'confirm2fa@example.com', twoFactorEnabled: true });
    const token = generateToken(user.id);
    const sent = await post('/2fa/send-otp', {}, token);
    const res = await post('/2fa/confirm', { otp: sent.body.debugOtp }, token);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Two-factor authentication is now active',
    });
    expect(rowByEmail('confirm2fa@example.com').twoFactorActivatedAt).toBeInstanceOf(Date);
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.2fa.enable' }),
    );
  });

  it('POST /2fa/confirm rejects a wrong OTP', async () => {
    const user = seedUser({ email: 'wrongotp@example.com', twoFactorEnabled: true });
    const sent = await post('/2fa/send-otp', {}, generateToken(user.id));
    const wrongOtp = sent.body.debugOtp === '000000' ? '111111' : '000000';

    const res = await post('/2fa/confirm', { otp: wrongOtp }, generateToken(user.id));
    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Invalid or expired OTP' });
    expect(rowByEmail('wrongotp@example.com').twoFactorActivatedAt).toBeFalsy();
  });

  it('POST /2fa/confirm locks the code after 5 wrong attempts', async () => {
    const user = seedUser({ email: 'brute@example.com', twoFactorEnabled: true });
    const token = generateToken(user.id);
    const sent = await post('/2fa/send-otp', {}, token);
    const wrongOtp = sent.body.debugOtp === '111111' ? '222222' : '111111';

    for (let i = 0; i < 5; i += 1) {
      const bad = await post('/2fa/confirm', { otp: wrongOtp }, token);
      expect(bad.status).toBe(400);
    }
    const after = await post('/2fa/confirm', { otp: sent.body.debugOtp }, token);
    expect(after.status).toBe(400);
    expect(after.body.error).toBe('Invalid or expired OTP');
  });

  it('POST /2fa/confirm validates the OTP shape before checking it', async () => {
    const user = seedUser({ email: 'shape@example.com', twoFactorEnabled: true });
    const res = await post('/2fa/confirm', { otp: '12' }, generateToken(user.id));

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(res.body.errors[0].msg).toBe('6-digit OTP is required');
  });

  it('POST /2fa/login-verify signs a session for the code the OTP store holds', async () => {
    seedUser({ email: 'verify2fa@example.com', password: 'Sup3rSecret!', twoFactorEnabled: true });
    const login = await post('/login', { email: 'verify2fa@example.com', password: 'Sup3rSecret!' });
    expect(login.body.requires2FA).toBe(true);
    // login cannot hand the user a code (see the BUG test), so the mailbox-side
    // call is issued the way /2fa/send-otp does it, proving the defect is in the
    // login route alone and not in the verification route.
    const code = generateOTP('verify2fa@example.com');

    const res = await post('/2fa/login-verify', { email: 'verify2fa@example.com', otp: code });
    expect(res.status).toBe(200);
    expect(res.body.message).toBe('2FA verification successful');
    expect(res.body.user.twoFactorEnabled).toBe(true);
    expect(jwt.decode(res.body.token).email).toBeUndefined();
    expect(cookieValue(res, 'refresh_token')).toBeUndefined();
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.2fa.login_verify' }),
    );
  });

  it('POST /2fa/login-verify rejects a bad OTP with 401 and an unknown email the same way as login', async () => {
    seedUser({ email: 'verify3fa@example.com', twoFactorEnabled: true });

    const bad = await post('/2fa/login-verify', { email: 'verify3fa@example.com', otp: '999999' });
    const unknown = await post('/2fa/login-verify', { email: 'nope@example.com', otp: '999999' });

    expect(bad.status).toBe(401);
    expect(unknown.body).toEqual({ success: false, error: 'Invalid credentials' });
  });

  it('POST /2fa/login-verify tells an account without 2FA to skip the step', async () => {
    seedUser({ email: 'no2fa@example.com', twoFactorEnabled: false });
    const res = await post('/2fa/login-verify', { email: 'no2fa@example.com', otp: '123456' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: '2FA is not enabled for this account' });
  });

  it('POST /2fa/login-verify validates its inputs', async () => {
    const res = await post('/2fa/login-verify', { email: 'not-an-email', otp: '12' });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.path)).toEqual(['email', 'otp']);
  });

  it('POST /2fa/send-otp 404s once the user row is gone', async () => {
    const user = seedUser({ email: 'gone2fa@example.com' });
    const token = generateToken(user.id);
    armMidRequestDeletion();

    const res = await post('/2fa/send-otp', {}, token);
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('2FA — authenticator app (TOTP) routes', () => {
  function setupAuthenticator(email = 'auth-app@example.com') {
    const user = seedUser({ email });
    const token = generateToken(user.id);
    return { user, token };
  }

  it('POST /2fa/authenticator/setup stores a secret and returns an otpauth URI', async () => {
    const { user, token } = setupAuthenticator();
    const res = await post('/2fa/authenticator/setup', {}, token);

    expect(res.status).toBe(200);
    expect(res.body.secret).toMatch(/^[A-Z2-7]{32}$/);
    expect(res.body.otpauthUrl).toContain('otpauth://totp/');
    expect(res.body.otpauthUrl).toContain(`secret=${res.body.secret}`);
    expect(res.body.otpauthUrl).toContain('issuer=Your%20App'); // APP_BRAND unset
    const row = rowByEmail('auth-app@example.com');
    expect(row.twoFactorSecret).toBe(res.body.secret);
    expect(row.twoFactorMethod).toBe('authenticator');
    expect(row.twoFactorEnabled).toBe(false); // enabled only after confirm
  });

  it('POST /2fa/authenticator/confirm activates 2FA with a valid TOTP', async () => {
    const { user, token } = setupAuthenticator('confirm-totp@example.com');
    const setup = await post('/2fa/authenticator/setup', {}, token);
    const code = generateTOTP(setup.body.secret);

    const res = await post('/2fa/authenticator/confirm', { code }, token);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Two-factor authentication is now active',
    });
    const row = rowByEmail('confirm-totp@example.com');
    expect(row.twoFactorEnabled).toBe(true);
    expect(row.twoFactorMethod).toBe('authenticator');
    expect(row.twoFactorActivatedAt).toBeInstanceOf(Date);
  });

  it('POST /2fa/authenticator/confirm rejects a wrong code', async () => {
    const { user, token } = setupAuthenticator('bad-totp@example.com');
    await post('/2fa/authenticator/setup', {}, token);

    const wrong = await post('/2fa/authenticator/confirm', { code: '000000' }, token);
    expect(wrong.status).toBe(400);
    expect(wrong.body).toEqual({ success: false, error: 'Invalid authenticator code' });
    expect(rowByEmail('bad-totp@example.com').twoFactorEnabled).toBe(false);
  });

  it('POST /2fa/authenticator/confirm demands setup first', async () => {
    const { user, token } = setupAuthenticator('no-secret@example.com');
    const res = await post('/2fa/authenticator/confirm', { code: '123456' }, token);

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('No authenticator secret configured. Call setup first.');
  });

  it('POST /2fa/authenticator/confirm validates the code shape', async () => {
    const { user, token } = setupAuthenticator('shape-totp@example.com');
    const res = await post('/2fa/authenticator/confirm', { code: '1234' }, token);

    expect(res.status).toBe(400);
    expect(res.body.errors[0].msg).toBe('6-digit code is required');
  });

  it('POST /2fa/authenticator/verify signs a session for a correct TOTP', async () => {
    const { user } = setupAuthenticator('verify-totp@example.com');
    const row = rowById(user.id);
    row.twoFactorEnabled = true;
    row.twoFactorMethod = 'authenticator';
    row.twoFactorSecret = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

    const res = await post('/2fa/authenticator/verify', {
      email: 'verify-totp@example.com',
      code: generateTOTP(row.twoFactorSecret),
    });

    expect(res.status).toBe(200);
    expect(res.body.user.email).toBe('verify-totp@example.com');
    expect(jwt.verify(res.body.token, process.env.JWT_SECRET, { algorithms: ['HS256'] })).toEqual(
      expect.objectContaining({ id: user.id }),
    );
  });

  it('POST /2fa/authenticator/verify 401s a wrong code', async () => {
    const { user } = setupAuthenticator('verify-bad@example.com');
    const row = rowById(user.id);
    row.twoFactorEnabled = true;
    row.twoFactorMethod = 'authenticator';
    row.twoFactorSecret = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

    const res = await post('/2fa/authenticator/verify', { email: 'verify-bad@example.com', code: '000000' });
    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid or expired authenticator code' });
  });

  it('POST /2fa/authenticator/verify refuses accounts using email 2FA', async () => {
    seedUser({ email: 'email-method@example.com', twoFactorEnabled: true, twoFactorMethod: 'email' });
    const res = await post('/2fa/authenticator/verify', {
      email: 'email-method@example.com',
      code: '123456',
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Authenticator 2FA is not enabled for this account');
  });

  it('POST /2fa/authenticator/verify 401s an unknown account', async () => {
    const res = await post('/2fa/authenticator/verify', { email: 'ghost@example.com', code: '123456' });
    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid credentials' });
  });

  it('POST /2fa/authenticator/setup requires authentication', async () => {
    const res = await post('/2fa/authenticator/setup', {});
    expect(res.status).toBe(401);
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('PUT /api/auth/change-password', () => {
  it('changes the password for an in-memory (Postgres-offline) user', async () => {
    dbDown = true;
    const reg = await post('/register', {
      name: 'Memory',
      email: 'memory-pw@example.com',
      password: 'FirstPass1',
    });
    expect(reg.status).toBe(201);
    const token = reg.body.token;

    const res = await put(
      '/change-password',
      { currentPassword: 'FirstPass1', newPassword: 'SecondPass2' },
      token,
    );

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Password changed successfully' });
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.password.change' }),
    );

    const bad = await post('/login', { email: 'memory-pw@example.com', password: 'FirstPass1' });
    expect(bad.status).toBe(401);
    const good = await post('/login', { email: 'memory-pw@example.com', password: 'SecondPass2' });
    expect(good.status).toBe(200);
  });

  it('rejects a wrong current password', async () => {
    dbDown = true;
    const reg = await post('/register', {
      name: 'Memory2',
      email: 'memory-pw2@example.com',
      password: 'FirstPass1',
    });
    const res = await put(
      '/change-password',
      { currentPassword: 'nope-nope', newPassword: 'SecondPass2' },
      reg.body.token,
    );

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Current password is incorrect' });
  });

  it('refuses to re-use the current password and enforces length', async () => {
    dbDown = true;
    const reg = await post('/register', {
      name: 'Same',
      email: 'same-pw@example.com',
      password: 'FirstPass1',
    });

    const same = await put(
      '/change-password',
      { currentPassword: 'FirstPass1', newPassword: 'FirstPass1' },
      reg.body.token,
    );
    expect(same.status).toBe(400);
    expect(same.body.errors[0].msg).toBe('New password must differ from current password');

    const short = await put(
      '/change-password',
      { currentPassword: 'FirstPass1', newPassword: 'abc' },
      reg.body.token,
    );
    expect(short.status).toBe(400);
    expect(short.body.errors[0].msg).toBe('New password must be at least 6 characters');

    const missing = await put('/change-password', { newPassword: 'abcdef' }, reg.body.token);
    expect(missing.status).toBe(400);
    expect(missing.body.errors[0].msg).toBe('Current password is required');
  });

  it('requires authentication', async () => {
    const res = await put('/change-password', { currentPassword: 'a', newPassword: 'abcdef' });
    expect(res.status).toBe(401);
  });

  it('500s for a database-backed user: the default scope hides the password column', async () => {
    const user = seedUser({ email: 'db-pw@example.com', password: 'Sup3rSecret!' });
    const res = await put(
      '/change-password',
      { currentPassword: 'Sup3rSecret!', newPassword: 'BrandNewPass9' },
      generateToken(user.id),
    );

    // BUG (routes/auth.routes.js:111-122 + :771): findUserById() uses User.findByPk
    // with the defaultScope, which excludes `password`, so comparePassword() is
    // handed `undefined` and bcryptjs throws. Password change is unusable for every
    // Postgres account. The message is not leaked in production.
    expect(res.status).toBe(500);
    expect(res.body.success).toBe(false);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(res.body).not.toHaveProperty('stack');
    expect(rowByEmail('db-pw@example.com').password).not.toBe('BrandNewPass9');
  });

  it('404s when the authenticated row has been deleted', async () => {
    const user = seedUser({ email: 'deleted-pw@example.com', password: 'Sup3rSecret!' });
    armMidRequestDeletion();

    const res = await put(
      '/change-password',
      { currentPassword: 'Sup3rSecret!', newPassword: 'BrandNewPass9' },
      generateToken(user.id),
    );
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('Email verification', () => {
  function userWithVerificationToken(email, expiresInSeconds = 3600) {
    return seedUser({
      email,
      verificationToken: crypto.randomBytes(32).toString('hex'),
      verificationExpires: new Date(Date.now() + expiresInSeconds * 1000),
    });
  }

  it('GET /verify-email/:token flips isVerified and burns the token', async () => {
    const user = userWithVerificationToken('vme@example.com');
    const token = rowByEmail('vme@example.com').verificationToken;

    const res = await get(`/verify-email/${token}`);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Email verified successfully. You can now log in.',
    });
    const row = rowById(user.id);
    expect(row.isVerified).toBe(true);
    expect(row.verificationToken).toBeNull();
    expect(row.verificationExpires).toBeNull();
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.email.verified', userId: user.id }),
    );
  });

  it('rejects a token that has expired, without touching the account', async () => {
    userWithVerificationToken('expired@example.com', -10);
    const token = rowByEmail('expired@example.com').verificationToken;

    const res = await get(`/verify-email/${token}`);

    expect(res.status).toBe(400);
    expect(res.body).toEqual({
      success: false,
      message: 'Verification token is invalid or has expired.',
    });
    expect(rowByEmail('expired@example.com').isVerified).toBe(false);
    // the expiry really is part of the query, not just a JS check
    const where = modelCalls.find((c) => c.method === 'findOne').options.where;
    expect(where.verificationToken).toBe(token);
    expect(where.verificationExpires[Op.gt]).toBeInstanceOf(Date);
  });

  it('rejects a truncated or unknown token', async () => {
    expect((await get('/verify-email/short')).status).toBe(400);
    const unknown = await get(`/verify-email/${'f'.repeat(64)}`);
    expect(unknown.status).toBe(400);
    expect(unknown.body.success).toBe(false);
  });

  it('redirects browser requests to the login page', async () => {
    userWithVerificationToken('browser@example.com');
    const token = rowByEmail('browser@example.com').verificationToken;

    const res = await get(`/verify-email/${token}`).set('Accept', 'text/html');
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe(`${FRONTEND_URL}/login?verified=true`);
  });

  it('does not 500 when the database is unreachable', async () => {
    const user = seedUser({ email: 'offline-verify@example.com' });
    dbDown = true;
    const res = await get(`/verify-email/${'a'.repeat(64)}`, undefined);

    expect(res.status).toBe(400);
    expect(mockLogger.warn).toHaveBeenCalledWith(expect.stringContaining('verify-email error'));
    expect(user.isActive).toBe(true);
  });

  it('POST /resend-verification re-issues a token for an unverified account', async () => {
    seedUser({ email: 'resend@example.com', isVerified: false });
    const res = await post('/resend-verification', { email: 'resend@example.com' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Verification email sent.' });
    const row = rowByEmail('resend@example.com');
    expect(row.verificationToken).toMatch(/^[0-9a-f]{64}$/);
    expect(emailMock.sendVerificationEmail).toHaveBeenCalledWith(
      'resend@example.com',
      'Seed User',
      row.verificationToken,
    );
  });

  it('POST /resend-verification gives the same answer for verified and unknown emails', async () => {
    seedUser({ email: 'verified@example.com', isVerified: true });

    const known = await post('/resend-verification', { email: 'verified@example.com' });
    const unknown = await post('/resend-verification', { email: 'nobody-here@example.com' });
    const expected = {
      success: true,
      message: 'If an unverified account exists, a new verification email has been sent.',
    };

    expect(known.body).toEqual(expected);
    expect(unknown.body).toEqual(expected);
    expect(known.status).toBe(200);
    expect(emailMock.sendVerificationEmail).not.toHaveBeenCalled();
  });

  it('POST /resend-verification validates the email', async () => {
    const res = await post('/resend-verification', { email: 'nope' });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, errors: [expect.any(Object)] });
    expect(res.body.errors[0].msg).toBe('Valid email is required');
  });

  it('POST /resend-verification leaves offline users with the generic answer', async () => {
    dbDown = true;
    const reg = await post('/register', {
      name: 'Offline',
      email: 'offline-resend@example.com',
      password: 'Sup3rSecret!',
    });
    expect(reg.status).toBe(201);

    const res = await post('/resend-verification', { email: 'offline-resend@example.com' });
    expect(res.status).toBe(200);
    expect(res.body.message).toBe(
      'If an unverified account exists, a new verification email has been sent.',
    );
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('Forgot / reset password', () => {
  it('POST /forgot-password stores a 15-minute token and emails it', async () => {
    const user = seedUser({ email: 'forgot@example.com', password: 'Sup3rSecret!' });
    const res = await post('/forgot-password', { email: 'forgot@example.com' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'If an account exists for this email, a password reset link has been sent.',
    });
    const row = rowById(user.id);
    expect(row.resetPasswordToken).toMatch(/^[0-9a-f]{64}$/);
    const ttl = row.resetPasswordExpires.getTime() - Date.now();
    expect(ttl).toBeGreaterThan(14 * 60 * 1000);
    expect(ttl).toBeLessThanOrEqual(15 * 60 * 1000);
    expect(emailMock.sendPasswordResetEmail).toHaveBeenCalledWith(
      'forgot@example.com',
      row.resetPasswordToken,
    );
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.password.forgot' }),
    );
  });

  it('POST /forgot-password answers identically for an unknown address', async () => {
    const knownBody = {
      success: true,
      message: 'If an account exists for this email, a password reset link has been sent.',
    };
    const res = await post('/forgot-password', { email: 'nobody@example.com' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual(knownBody);
    expect(emailMock.sendPasswordResetEmail).not.toHaveBeenCalled();
    expect(modelCalls.some((c) => c.method === 'update')).toBe(false);
  });

  it('POST /forgot-password validates the email shape', async () => {
    const res = await post('/forgot-password', { email: 'bad-email' });

    expect(res.status).toBe(400);
    expect(res.body.errors[0].msg).toBe('Valid email is required');
  });

  it('POST /reset-password/:token applies the new password once', async () => {
    const user = seedUser({ email: 'reset@example.com', password: 'Sup3rSecret!' });
    await post('/forgot-password', { email: 'reset@example.com' });
    const row = rowById(user.id);
    const token = row.resetPasswordToken;

    const res = await post(`/reset-password/${token}`, { password: 'FreshPass99' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Password reset successfully. You can now log in.',
    });
    expect(bcrypt.compareSync('FreshPass99', row.password)).toBe(true);
    expect(row.resetPasswordToken).toBeNull();
    expect(row.resetPasswordExpires).toBeNull();

    const replay = await post(`/reset-password/${token}`, { password: 'AnotherPass7' });
    expect(replay.status).toBe(400);
    expect(replay.body).toEqual({ success: false, error: 'Reset link is invalid or has expired' });

    const login = await post('/login', { email: 'reset@example.com', password: 'FreshPass99' });
    expect(login.status).toBe(200);
  });

  it('POST /reset-password/:token rejects an expired token', async () => {
    const user = seedUser({
      email: 'reset-exp@example.com',
      resetPasswordToken: crypto.randomBytes(32).toString('hex'),
      resetPasswordExpires: new Date(Date.now() - 1000),
    });
    const res = await post(`/reset-password/${rowById(user.id).resetPasswordToken}`, {
      password: 'FreshPass99',
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Reset link is invalid or has expired');
    expect(bcrypt.compareSync('FreshPass99', rowById(user.id).password)).toBe(false);
  });

  it('POST /reset-password/:token validates the new password length', async () => {
    const res = await post(`/reset-password/${'a'.repeat(64)}`, { password: 'short' });

    expect(res.status).toBe(400);
    expect(res.body.errors[0].msg).toBe('Password must be at least 6 characters');
  });

  it('POST /reset-password accepts the token in the body', async () => {
    const user = seedUser({ email: 'reset-body@example.com' });
    await post('/forgot-password', { email: 'reset-body@example.com' });
    const token = rowById(user.id).resetPasswordToken;

    const res = await post('/reset-password', { token, password: 'BodyPass123' });

    expect(res.status).toBe(200);
    expect(bcrypt.compareSync('BodyPass123', rowById(user.id).password)).toBe(true);
    expect(auditMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ action: 'auth.password.reset', userId: user.id }),
    );
  });

  it('POST /reset-password requires a token', async () => {
    const res = await post('/reset-password', { password: 'BodyPass123' });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.path)).toEqual(['token']);
  });

  it('POST /reset-password rejects an unknown token', async () => {
    const res = await post('/reset-password', {
      token: crypto.randomBytes(32).toString('hex'),
      password: 'BodyPass123',
    });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Reset link is invalid or has expired');
  });

  it('forgot-password does not write a token for an offline user', async () => {
    dbDown = true;
    const res = await post('/forgot-password', { email: 'offline-forgot@example.com' });

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(emailMock.sendPasswordResetEmail).not.toHaveBeenCalled();
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('OAuth kick-offs and callbacks', () => {
  it('GET /oauth/google starts the google strategy with profile+email scope', async () => {
    const res = await get('/oauth/google');

    expect(res.status).toBe(302);
    expect(passportState.strategy).toBe('google');
    expect(passportState.options).toEqual({ scope: ['profile', 'email'] });
  });

  it('GET /oauth/github starts the github strategy asking for the email scope', async () => {
    const res = await get('/oauth/github');

    expect(res.status).toBe(302);
    expect(passportState.strategy).toBe('github');
    expect(passportState.options).toEqual({ scope: ['user:email'] });
  });

  it('redirects a successful google callback to the frontend with our JWT', async () => {
    const user = seedUser({ email: 'oauth@example.com', name: 'OAuth Person' });
    passportState.user = { id: user.id, name: 'OAuth Person', email: 'oauth@example.com' };

    const res = await get('/oauth/google/callback');

    expect(res.status).toBe(302);
    const location = new URL(res.headers.location);
    expect(location.origin + location.pathname).toBe(`${FRONTEND_URL}/oauth/callback`);
    expect(location.searchParams.get('name')).toBe('OAuth Person');
    expect(location.searchParams.get('email')).toBe('oauth@example.com');
    const token = location.searchParams.get('token');
    expect(jwt.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] }).id).toBe(user.id);
  });

  it('redirects a failed google callback to the login page', async () => {
    passportState.error = new Error('invalid_state');
    passportState.user = null;

    const res = await get('/oauth/google/callback');

    expect(res.status).toBe(302);
    expect(res.headers.location).toBe(`${FRONTEND_URL}/login?oauth=error`);
  });

  it('redirects a github callback without a user to the login page', async () => {
    passportState.error = null;
    passportState.user = null;

    const res = await get('/oauth/github/callback');

    expect(res.status).toBe(302);
    expect(res.headers.location).toBe(`${FRONTEND_URL}/login?oauth=error`);
  });

  it('encodes OAuth names that would otherwise break the query string', async () => {
    passportState.error = null;
    passportState.user = { id: 3, name: 'Ünï & Nâme', email: 'odd+space@example.com' };

    const res = await get('/oauth/github/callback');
    const location = new URL(res.headers.location);

    expect(location.searchParams.get('name')).toBe('Ünï & Nâme');
    expect(location.searchParams.get('email')).toBe('odd+space@example.com');
    expect(res.headers.location).toContain('name=');
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('Failure paths: half-dead database, dead Redis, dead audit sink', () => {
  it('POST /register 500s when the verification-token UPDATE fails after the INSERT', async () => {
    failWritesAfter(1); // the INSERT goes through, the follow-up UPDATE does not
    const res = await post('/register', {
      name: 'Half',
      email: 'half-reg@example.com',
      password: 'Sup3rSecret!',
    });

    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    // The row is committed before the failing write, so the client that saw a 500
    // can never retry: the second attempt is told the address is taken
    // (routes/auth.routes.js:161-229).
    expect(rowByEmail('half-reg@example.com')).toBeTruthy();

    const retry = await post('/register', {
      name: 'Half',
      email: 'half-reg@example.com',
      password: 'Sup3rSecret!',
    });
    expect(retry.status).toBe(400);
    expect(retry.body.error).toBe('User already exists with this email');
  });

  it('GET /profile 404s when the row disappears between protect() and the handler', async () => {
    const user = seedUser({ email: 'getgone@example.com' });
    armMidRequestDeletion();

    const res = await get('/profile', generateToken(user.id));
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });

  it('PUT /profile 500s when the write fails, leaving the row unchanged', async () => {
    const user = seedUser({ email: 'wprofile@example.com' });
    failWritesAfter(0);

    const res = await put('/profile', { name: 'Never Saved' }, generateToken(user.id));
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(rowByEmail('wprofile@example.com').name).toBe('Seed User');
  });

  it('PUT /profile updates an offline account that has no update() method', async () => {
    dbDown = true;
    const reg = await post('/register', {
      name: 'Offline',
      email: 'offline-profile@example.com',
      password: 'FirstPass1',
    });
    expect(reg.status).toBe(201);

    const res = await put('/profile', { name: 'Renamed' }, reg.body.token);
    expect(res.status).toBe(200);
    expect(res.body.user.name).toBe('Renamed');
    expect(res.body.user.password).toBeUndefined();
  });

  it('POST /2fa/setup refuses to enrol a second time', async () => {
    const user = seedUser({ email: 'already2fa@example.com', twoFactorEnabled: true });
    const res = await post('/2fa/setup', { method: 'email' }, generateToken(user.id));

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: '2FA is already enabled' });
  });

  it('POST /2fa/setup 404s when the row disappears mid-request', async () => {
    const user = seedUser({ email: 'gone-setup@example.com' });
    armMidRequestDeletion();

    const res = await post('/2fa/setup', { method: 'email' }, generateToken(user.id));
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });

  it('POST /2fa/confirm 500s when the activation write fails', async () => {
    const user = seedUser({ email: 'wconfirm@example.com', twoFactorEnabled: true });
    const token = generateToken(user.id);
    const sent = await post('/2fa/send-otp', {}, token);
    failWritesAfter(0);

    const res = await post('/2fa/confirm', { otp: sent.body.debugOtp }, token);
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(rowByEmail('wconfirm@example.com').twoFactorActivatedAt).toBeFalsy();
  });

  it('POST /2fa/authenticator/setup 404s when the row disappears mid-request', async () => {
    const user = seedUser({ email: 'gone-totp@example.com' });
    armMidRequestDeletion();

    const res = await post('/2fa/authenticator/setup', {}, generateToken(user.id));
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });

  it('POST /2fa/authenticator/setup 500s when the secret cannot be persisted', async () => {
    const user = seedUser({ email: 'wtotp@example.com' });
    failWritesAfter(0);

    const res = await post('/2fa/authenticator/setup', {}, generateToken(user.id));
    expect(res.status).toBe(500);
    expect(res.body.secret).toBeUndefined();
    expect(rowByEmail('wtotp@example.com').twoFactorSecret).toBeUndefined();
  });

  it('POST /2fa/authenticator/confirm 404s when the row disappears mid-request', async () => {
    const user = seedUser({ email: 'gone-totp2@example.com', twoFactorSecret: 'JBSWY3DPEHPK3PXP' });
    armMidRequestDeletion();

    const res = await post('/2fa/authenticator/confirm', { code: '123456' }, generateToken(user.id));
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'User not found' });
  });

  it('POST /2fa/authenticator/verify validates the email and the code shape', async () => {
    const res = await post('/2fa/authenticator/verify', { email: 'not-an-email', code: '12' });

    expect(res.status).toBe(400);
    expect(res.body.errors.map((e) => e.path)).toEqual(['email', 'code']);
  });

  it('GET /verify-email/:token reports the token as invalid when the write fails', async () => {
    const token = crypto.randomBytes(32).toString('hex');
    seedUser({
      email: 'wverify@example.com',
      verificationToken: token,
      verificationExpires: new Date(Date.now() + 60000),
    });
    failWritesAfter(0);

    const res = await get(`/verify-email/${token}`);
    // The DB error is swallowed by the inner catch (routes/auth.routes.js:830-832)
    // and indistinguishable from an unknown token — the user is told to request a
    // new link instead of retrying, which is the safe degradation.
    expect(res.status).toBe(400);
    expect(res.body.message).toBe('Verification token is invalid or has expired.');
    expect(logCalls.warn.join(' ')).toContain('DB verify-email error');
    expect(rowByEmail('wverify@example.com').isVerified).toBe(false);
  });

  it('POST /resend-verification 500s when the new token cannot be written', async () => {
    seedUser({ email: 'wresend@example.com' });
    failWritesAfter(0);

    const res = await post('/resend-verification', { email: 'wresend@example.com' });
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(emailMock.sendVerificationEmail).not.toHaveBeenCalled();
  });

  it('POST /forgot-password 500s when the reset token cannot be written', async () => {
    seedUser({ email: 'wforgot@example.com' });
    failWritesAfter(0);

    const res = await post('/forgot-password', { email: 'wforgot@example.com' });
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    // A reset email must never be sent for a token that was not persisted.
    expect(emailMock.sendPasswordResetEmail).not.toHaveBeenCalled();
  });

  it('POST /reset-password/:token 500s when the new password cannot be written', async () => {
    const token = crypto.randomBytes(32).toString('hex');
    seedUser({
      email: 'wreset@example.com',
      password: 'Sup3rSecret!',
      resetPasswordToken: token,
      resetPasswordExpires: new Date(Date.now() + 60000),
    });
    failWritesAfter(0);

    const res = await post(`/reset-password/${token}`, { password: 'ResetPass9' });
    expect(res.status).toBe(500);
    expect(rowByEmail('wreset@example.com').resetPasswordToken).toBe(token);
  });

  it('POST /reset-password (body token) 500s when the new password cannot be written', async () => {
    const token = crypto.randomBytes(32).toString('hex');
    seedUser({
      email: 'wreset2@example.com',
      password: 'Sup3rSecret!',
      resetPasswordToken: token,
      resetPasswordExpires: new Date(Date.now() + 60000),
    });
    failWritesAfter(0);

    const res = await post('/reset-password', { token, password: 'ResetPass9' });
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    const still = await post('/login', { email: 'wreset2@example.com', password: 'Sup3rSecret!' });
    expect(still.status).toBe(200);
  });

  it('POST /refresh fails closed (500, no token) when the revocation store cannot be read', async () => {
    seedUser({ email: 'rredis@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'rredis@example.com', password: 'Sup3rSecret!' });
    failRedis({ read: true });

    const res = await post('/refresh', { refreshToken: login.body.refreshToken });
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
    expect(res.body.token).toBeUndefined();
    expect(cookieValue(res, 'refresh_token')).toBeUndefined();
  });

  it('BUG: POST /logout answers "Logged out" while Redis refuses the revocation, so the token stays live', async () => {
    seedUser({ email: 'rlogout@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'rlogout@example.com', password: 'Sup3rSecret!' });
    const refreshToken = login.body.refreshToken;

    failRedis({ write: true });
    const res = await post('/logout', { refreshToken });
    // routes/auth.routes.js:332-334 swallows "cannot revoke" exactly like "nothing
    // to revoke": the client is told the session ended and clears its cookie, yet
    // the stolen refresh token remains rotatable forever.
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, message: 'Logged out successfully' });
    expect(isRevoked(jtiOf(refreshToken))).toBe(false);

    failRedis({});
    const after = await post('/refresh', { refreshToken });
    expect(after.status).toBe(200);
    expect(after.body.token).toBeDefined();
  });

  it('POST /logout 500s when the audit sink throws', async () => {
    auditMock.mockImplementationOnce(() => {
      throw new Error('audit sink down');
    });

    const res = await post('/logout', {});
    expect(res.status).toBe(500);
    expect(res.body.code).toBe('INTERNAL_ERROR');
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('Route wiring & module bootstrap', () => {
  it('does not seed demo accounts when SEED_DEMO_USERS is unset', () => {
    // Emitted while auth.routes.js was imported, i.e. before clearMocks wiped the
    // mock's call log — read the boot snapshot instead of the spy.
    expect(BOOT_LOGS.info.some((m) => m.includes('Demo accounts are disabled'))).toBe(true);
    expect(BOOT_LOGS.warn.some((m) => m.includes('Seeded'))).toBe(false);
  });

  it('rejects unknown auth paths with the canonical 404 envelope', async () => {
    const res = await get('/does-not-exist');

    expect(res.status).toBe(404);
    expect(res.body.code).toBe('NOT_FOUND');
    expect(res.body.success).toBe(false);
    expect(res.body.data).toBeNull();
    expect(Number.isNaN(Date.parse(res.body.timestamp))).toBe(false);
  });

  it('looks credentials up with withPassword but reset tokens with the default scope', async () => {
    seedUser({ email: 'scope-check@example.com', password: 'Sup3rSecret!' });
    await post('/login', { email: 'scope-check@example.com', password: 'Sup3rSecret!' });
    expect(UserMock.scope).toHaveBeenCalledTimes(1);
    expect(UserMock.scope).toHaveBeenCalledWith('withPassword');

    await post('/forgot-password', { email: 'scope-check@example.com' });
    const resetToken = rowByEmail('scope-check@example.com').resetPasswordToken;
    expect(resetToken).toMatch(/^[0-9a-f]{64}$/);

    UserMock.scope.mockClear();
    modelCalls.length = 0;
    const res = await post(`/reset-password/${resetToken}`, { password: 'ResetPass9' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      message: 'Password reset successfully. You can now log in.',
    });
    // applyPasswordReset() must not attach the password column to its lookup.
    expect(UserMock.scope).not.toHaveBeenCalled();
    const findOne = modelCalls.find((c) => c.method === 'findOne');
    expect(findOne.options.where.resetPasswordToken).toBe(resetToken);
    expect(findOne.scope).toBe('defaultScope');
  });

  it('normalizes the lookup email before hitting the database', async () => {
    seedUser({ email: 'norm@example.com' });
    await post('/login', { email: '  NORM@Example.com  ', password: 'Sup3rSecret!' });

    const findOne = modelCalls.find((c) => c.method === 'findOne');
    expect(findOne.options.where).toEqual({ email: 'norm@example.com' });
  });

  it('keeps a refresh token unusable as an access token', async () => {
    seedUser({ email: 'cross@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'cross@example.com', password: 'Sup3rSecret!' });

    const res = await get('/profile', login.body.refreshToken);
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('Not authorized, token failed');
  });

  it('refuses to rotate a refresh token whose account was deleted after login', async () => {
    const user = seedUser({ email: 'delete-me@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'delete-me@example.com', password: 'Sup3rSecret!' });
    const refreshToken = login.body.refreshToken;
    expect(isRevoked(jtiOf(refreshToken))).toBe(false);

    rows.length = 0;
    const refresh = await post('/refresh', { refreshToken });
    expect(refresh.status).toBe(401);
    expect(refresh.body).toEqual({ success: false, error: 'Account is not active' });
    expect(refresh.body.token).toBeUndefined();
    expect(user.id).toBeDefined();
  });

  it('logs out by revoking the supplied refresh token', async () => {
    const user = seedUser({ email: 'logout-me@example.com', password: 'Sup3rSecret!' });
    const login = await post('/login', { email: 'logout-me@example.com', password: 'Sup3rSecret!' });

    const res = await post('/logout', { refreshToken: login.body.refreshToken });
    expect(res.status).toBe(200);
    expect(isRevoked(jtiOf(login.body.refreshToken))).toBe(true);

    const reuse = await post('/refresh', { refreshToken: login.body.refreshToken });
    expect(reuse.status).toBe(401);
    expect(reuse.body.error).toBe('Refresh token has been revoked. Please log in again.');
    // The account itself is untouched — only the token family died.
    expect(rowById(user.id).isActive).toBe(true);
  });
});
