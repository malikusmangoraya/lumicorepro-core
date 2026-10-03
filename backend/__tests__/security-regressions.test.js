/**
 * Security regression tests
 * -------------------------
 * Pure unit tests (no DB, no listening server, no real network) covering the
 * hardening that was just applied to the Express backend:
 *
 *  1. optionalProtect never blocks the request
 *  2. protect pins the JWT algorithm to HS256
 *  3. resolveValidApiKeys() fails secure in production
 *  4. CORS origin policy no longer reflects arbitrary origins
 *  5. pickProductFields() blocks mass-assignment / prototype pollution
 *  6. /uploads static serving carries nosniff + sandbox CSP
 *
 * NOTE on module loading: the backend is native ESM ("type": "module"), so
 * `require()` does not exist inside the Jest module context. `jest.isolateModules`
 * only works with the CJS loader. The ESM equivalent that gives the exact same
 * guarantee (a pristine module registry per test) is
 * `jest.isolateModulesAsync()` + dynamic `import()`.
 */
import { describe, it, expect, beforeAll, beforeEach, afterEach, jest } from '@jest/globals';
import fs from 'fs';
import jwt from 'jsonwebtoken';

// ── Mocks (must be registered before the modules under test are imported) ──

// Keep winston quiet: the middlewares log warnings on every blocked request.
const silentLogger = {
  error: () => {},
  warn: () => {},
  info: () => {},
  http: () => {},
  debug: () => {},
  log: () => {},
};
jest.unstable_mockModule('../utils/logger.js', () => ({
  __esModule: true,
  default: silentLogger,
  withRequestId: () => silentLogger,
  redact: (v) => v,
}));

// Never reach a real database: every lookup rejects, which is exactly the
// offline path the middlewares must survive (and the reason for the
// in-memory-store fallback assertions below).
jest.unstable_mockModule('../models/User.js', () => ({
  __esModule: true,
  default: { findByPk: jest.fn() },
}));

// ── Shared helpers ────────────────────────────────────────────────────────

const ENV_KEYS = ['VALID_API_KEYS', 'NODE_ENV', 'JWT_SECRET', 'ALLOWED_ORIGINS', 'CORS_ORIGIN'];
const TEST_SECRET = 'unit-test-jwt-secret-do-not-use-in-prod';

let envSnapshot = {};

const makeRes = () => {
  const res = {
    statusCode: undefined,
    status: jest.fn(),
    json: jest.fn(),
    send: jest.fn(),
    end: jest.fn(),
  };
  res.status.mockImplementation((code) => {
    res.statusCode = code;
    return res;
  });
  res.json.mockImplementation((payload) => {
    res.body = payload;
    return res;
  });
  res.send.mockImplementation((payload) => {
    res.body = payload;
    return res;
  });
  return res;
};

const makeReq = (headers = {}) => ({ headers });

/** Load a pristine copy of middleware/security.js under the given env values. */
const loadSecurityWith = async (env) => {
  Object.assign(process.env, env);
  let mod;
  await jest.isolateModulesAsync(async () => {
    mod = await import('../middleware/security.js');
  });
  return mod;
};

let auth;
let User;
let pickProductFields;

beforeAll(async () => {
  User = (await import('../models/User.js')).default;
  auth = await import('../middleware/auth.js');
  ({ pickProductFields } = await import('../routes/product.routes.js'));
});

beforeEach(() => {
  envSnapshot = {};
  for (const key of ENV_KEYS) envSnapshot[key] = process.env[key];

  process.env.JWT_SECRET = TEST_SECRET;
  process.env.VALID_API_KEYS = '';
  process.env.NODE_ENV = 'test';
  delete process.env.ALLOWED_ORIGINS;
  delete process.env.CORS_ORIGIN;

  // resetMocks: true wipes implementations between tests, so re-arm the DB stub:
  // every lookup rejects, forcing the documented offline fallback path.
  User.findByPk.mockRejectedValue(new Error('database unavailable in unit tests'));
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (envSnapshot[key] === undefined) delete process.env[key];
    else process.env[key] = envSnapshot[key];
  }
  auth?.registerInMemoryStore(null);
});

// ───────────────────────────────────────────────────────────────────────────

describe('Security regressions: optionalProtect', () => {
  it('calls next() and leaves req.user undefined when no Authorization header is present', async () => {
    const req = makeReq({});
    const res = makeRes();
    const next = jest.fn();

    await auth.optionalProtect(req, res, next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(req.user).toBeUndefined();
  });

  it('calls next() and stays anonymous for a malformed/garbage Bearer token (never 401)', async () => {
    const req = makeReq({ authorization: 'Bearer not-a-real-jwt.at.all' });
    const res = makeRes();
    const next = jest.fn();

    await expect(auth.optionalProtect(req, res, next)).resolves.not.toThrow();

    expect(next).toHaveBeenCalledTimes(1);
    expect(req.user).toBeUndefined();
    expect(res.status).not.toHaveBeenCalled();
    expect(res.json).not.toHaveBeenCalled();
  });

  it('attaches a password-free req.user for a valid token via the in-memory fallback store', async () => {
    auth.registerInMemoryStore(
      new Map([
        [
          42,
          {
            id: 42,
            name: 'Test Vendor',
            email: 'vendor@example.com',
            role: 'vendor',
            isActive: true,
            password: 'super-secret-hash',
            comparePassword: () => Promise.resolve(true),
            save: () => Promise.resolve(),
          },
        ],
      ]),
    );

    const token = jwt.sign({ id: 42 }, TEST_SECRET, { algorithm: 'HS256' });
    const req = makeReq({ authorization: `Bearer ${token}` });
    const res = makeRes();
    const next = jest.fn();

    await auth.optionalProtect(req, res, next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(req.user).toBeDefined();
    expect(req.user.id).toBe(42);
    expect(req.user.email).toBe('vendor@example.com');
    expect(Object.prototype.hasOwnProperty.call(req.user, 'password')).toBe(false);
    expect(req.user.password).toBeUndefined();
    // The DB lookup really was attempted (and failed offline) before the
    // in-memory fallback kicked in — proves the stub is wired to auth.js.
    expect(User.findByPk).toHaveBeenCalledWith(42, { attributes: { exclude: ['password'] } });
  });

  it('never sets res.statusCode nor sends a response on any of the anonymous paths', async () => {
    const cases = [
      {},
      { authorization: 'Bearer garbage' },
      { authorization: 'Bearer eyJhbGciOiJIUzUxMiJ9.e30.badsig' },
      { authorization: 'Basic dXNlcjpwYXNz' },
    ];

    for (const headers of cases) {
      const req = makeReq(headers);
      const res = makeRes();
      const next = jest.fn();

      await auth.optionalProtect(req, res, next);

      expect(next).toHaveBeenCalledTimes(1);
      expect(res.statusCode).toBeUndefined();
      expect(res.status).not.toHaveBeenCalled();
      expect(res.json).not.toHaveBeenCalled();
      expect(res.send).not.toHaveBeenCalled();
      expect(res.end).not.toHaveBeenCalled();
    }
  });
});

describe('Security regressions: protect algorithm pinning', () => {
  it('rejects an HS512 token even though it verifies against the same secret', async () => {
    const token = jwt.sign({ id: 1 }, TEST_SECRET, { algorithm: 'HS512' });
    const req = makeReq({ authorization: `Bearer ${token}` });
    const res = makeRes();
    const next = jest.fn();

    await auth.protect(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
    expect(res.body).toEqual({ success: false, error: 'Not authorized, token failed' });
  });

  it('accepts an HS256 token (fails later on the user lookup, not on the signature)', async () => {
    auth.registerInMemoryStore(new Map()); // signed correctly, but no such user

    const token = jwt.sign({ id: 999 }, TEST_SECRET, { algorithm: 'HS256' });
    const req = makeReq({ authorization: `Bearer ${token}` });
    const res = makeRes();
    const next = jest.fn();

    await auth.protect(req, res, next);

    expect(res.status).toHaveBeenCalledWith(401);
    // The signature passed verification — the failure must be the user lookup.
    expect(res.body.error).not.toBe('Not authorized, token failed');
    expect(res.body.error).toBe('User not found');
  });
});

describe('Security regressions: API key resolution fails secure', () => {
  it('requireApiKey rejects the hardcoded dev key in production when VALID_API_KEYS is empty', async () => {
    const { requireApiKey } = await loadSecurityWith({
      VALID_API_KEYS: '',
      NODE_ENV: 'production',
    });

    const req = makeReq({ 'x-api-key': 'lumicore_dev_key_2026' });
    const res = makeRes();
    const next = jest.fn();

    requireApiKey(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });

  it('gateAI rejects a bare Bearer token (no api key) in production when VALID_API_KEYS is empty', async () => {
    const { gateAI } = await loadSecurityWith({ VALID_API_KEYS: '', NODE_ENV: 'production' });

    const req = makeReq({ authorization: 'Bearer not-a-valid-jwt' });
    const res = makeRes();
    const next = jest.fn();

    gateAI(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
    expect(res.body).toEqual({
      success: false,
      error: 'Authentication or API key required',
    });
  });

  it('gateAI rejects the hardcoded dev key in production when VALID_API_KEYS is empty', async () => {
    const { gateAI } = await loadSecurityWith({ VALID_API_KEYS: '', NODE_ENV: 'production' });

    const req = makeReq({ 'x-api-key': 'lumicore_dev_key_2026' });
    const res = makeRes();
    const next = jest.fn();

    gateAI(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });

  it('requireApiKey accepts a configured key from a comma-separated list', async () => {
    const { requireApiKey } = await loadSecurityWith({ VALID_API_KEYS: 'k1,k2' });

    const req = makeReq({ 'x-api-key': 'k2' });
    const res = makeRes();
    const next = jest.fn();

    requireApiKey(req, res, next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(res.status).not.toHaveBeenCalled();
  });

  it('requireApiKey still rejects the dev key in production when other keys are configured', async () => {
    const { requireApiKey } = await loadSecurityWith({
      VALID_API_KEYS: 'k1',
      NODE_ENV: 'production',
    });

    const req = makeReq({ 'x-api-key': 'lumicore_dev_key_2026' });
    const res = makeRes();
    const next = jest.fn();

    requireApiKey(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(401);
  });
});

describe('Security regressions: CORS origin policy', () => {
  const callOrigin = (corsOptions, origin) => {
    const callback = jest.fn();
    corsOptions.origin(origin, callback);
    return callback;
  };

  it('allows a request with no Origin header', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'test' });

    const cb = callOrigin(corsOptions, undefined);
    expect(cb).toHaveBeenCalledTimes(1);
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('allows the Vite dev origin', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'test' });

    const cb = callOrigin(corsOptions, 'http://localhost:5173');
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('allows the loopback API origin on 127.0.0.1', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'test' });

    const cb = callOrigin(corsOptions, 'http://127.0.0.1:3000');
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('REJECTS an arbitrary internet origin in production (no reflection with credentials)', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'production' });

    const cb = callOrigin(corsOptions, 'https://evil.example.com');
    expect(cb).toHaveBeenCalledTimes(1);
    expect(cb.mock.calls[0][0]).toBeTruthy();
    expect(cb.mock.calls[0][0].message).toMatch(/blocked by cors/i);
    expect(cb.mock.calls[0][1]).toBe(false);
  });

  it('allows an explicitly allowlisted production origin', async () => {
    const { corsOptions } = await loadSecurityWith({
      NODE_ENV: 'production',
      ALLOWED_ORIGINS: 'https://app.yourdomain.com',
    });

    const cb = callOrigin(corsOptions, 'https://app.yourdomain.com');
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('honours legacy CORS_ORIGIN when ALLOWED_ORIGINS is unset', async () => {
    const { corsOptions, resolveAllowedOrigins } = await loadSecurityWith({
      NODE_ENV: 'production',
      CORS_ORIGIN: 'https://legacy.yourdomain.com',
    });

    expect(resolveAllowedOrigins()).toEqual(['https://legacy.yourdomain.com']);
    const cb = callOrigin(corsOptions, 'https://legacy.yourdomain.com');
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('prefers ALLOWED_ORIGINS over legacy CORS_ORIGIN', async () => {
    const { resolveAllowedOrigins } = await loadSecurityWith({
      NODE_ENV: 'production',
      ALLOWED_ORIGINS: 'https://app.yourdomain.com',
      CORS_ORIGIN: 'https://legacy.yourdomain.com',
    });

    expect(resolveAllowedOrigins()).toEqual(['https://app.yourdomain.com']);
  });

  it('allows a private LAN origin outside production', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'test' });

    const cb = callOrigin(corsOptions, 'http://192.168.1.50:5173');
    expect(cb.mock.calls[0][0]).toBeNull();
    expect(cb.mock.calls[0][1]).toBe(true);
  });

  it('rejects an arbitrary internet origin outside production too', async () => {
    const { corsOptions } = await loadSecurityWith({ NODE_ENV: 'test' });

    const cb = callOrigin(corsOptions, 'https://evil.example.com');
    expect(cb).toHaveBeenCalledTimes(1);
    expect(cb.mock.calls[0][0]).toBeTruthy();
    expect(cb.mock.calls[0][1]).toBe(false);
  });

  it('keeps credentials enabled across every branch', async () => {
    const prod = await loadSecurityWith({ NODE_ENV: 'production' });
    const dev = await loadSecurityWith({ NODE_ENV: 'test' });

    expect(prod.corsOptions.credentials).toBe(true);
    expect(dev.corsOptions.credentials).toBe(true);
  });
});

describe('Security regressions: Product mass-assignment guard', () => {
  it('drops admin-only columns for a vendor', () => {
    const body = {
      title: 'Studio Monitor',
      price: 249,
      stock: 12,
      rating: 5,
      reviewCount: 900,
      isActive: true,
      vendor_id: 7,
      org_id: 3,
    };

    const out = pickProductFields(body, 'vendor');

    expect(out.title).toBe('Studio Monitor');
    expect(out.price).toBe(249);
    expect(out.stock).toBe(12);
    for (const key of ['rating', 'reviewCount', 'isActive', 'vendor_id', 'org_id']) {
      expect(Object.prototype.hasOwnProperty.call(out, key)).toBe(false);
    }
  });

  it('allows every catalogue + admin column for an admin', () => {
    const body = {
      title: 'Studio Monitor',
      price: 249,
      stock: 12,
      rating: 5,
      reviewCount: 900,
      isActive: true,
      vendor_id: 7,
      org_id: 3,
    };

    const out = pickProductFields(body, 'admin');

    expect(out).toEqual(body);
  });

  it('drops unknown / injection-shaped keys regardless of role', () => {
    const out = pickProductFields(
      { title: 'X', constructor: 'evil', __proto__evil: true, isAdmin: true, role: 'admin' },
      'admin',
    );

    expect(out.title).toBe('X');
    expect(Object.prototype.hasOwnProperty.call(out, 'constructor')).toBe(false);
    expect(Object.prototype.hasOwnProperty.call(out, '__proto__evil')).toBe(false);
    expect(Object.prototype.hasOwnProperty.call(out, 'isAdmin')).toBe(false);
    expect(Object.prototype.hasOwnProperty.call(out, 'role')).toBe(false);
  });

  it('returns {} and never throws for a non-object body', () => {
    for (const body of [undefined, null, 'a string', 12345, ['a', 'b']]) {
      let out;
      expect(() => {
        out = pickProductFields(body, 'vendor');
      }).not.toThrow();
      expect(out).toEqual({});
    }
  });

  it('is not vulnerable to prototype pollution via a JSON __proto__ payload', () => {
    const body = JSON.parse('{"__proto__":{"admin":true}}');

    const out = pickProductFields(body, 'admin');

    expect(Object.prototype.hasOwnProperty.call(out, 'admin')).toBe(false);
    expect(out.admin).toBeUndefined();
    expect({}.admin).toBeUndefined();
    expect(Object.getPrototypeOf(out)).toBe(Object.prototype);
  });
});

describe('Security regressions: static /uploads hardening (source-level)', () => {
  // server.js has import-time side effects and binds a port, so it is asserted
  // at the source level rather than imported.
  const source = fs.readFileSync(new URL('../server.js', import.meta.url), 'utf8');

  it('serves /uploads through express.static with nosniff and a sandbox CSP', () => {
    const block = source.match(/app\.use\(\s*'\/uploads',[\s\S]*?\n\);/);

    expect(block).not.toBeNull();
    expect(source).toContain('express.static');

    const uploadsBlock = block[0];
    expect(uploadsBlock).toContain("'/uploads'");
    expect(uploadsBlock).toContain('express.static');
    expect(uploadsBlock).toContain('X-Content-Type-Options');
    expect(uploadsBlock).toContain('nosniff');
    expect(uploadsBlock).toContain('Content-Security-Policy');
    expect(uploadsBlock).toContain('sandbox');
  });
});
