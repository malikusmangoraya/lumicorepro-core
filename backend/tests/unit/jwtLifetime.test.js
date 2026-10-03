import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import jwt from 'jsonwebtoken';

/**
 * JWT lifetime policy (AGENTS.md §3): 15-minute access tokens + 7-day rotating
 * refresh tokens. `JWT_EXPIRE` stays overridable, but boot validation caps
 * production at 1 hour (see tests/unit/env.test.js).
 */

const silentLogger = {
  error: () => {},
  warn: () => {},
  info: () => {},
  http: () => {},
  debug: () => {},
};

jest.unstable_mockModule('../../models/User.js', () => ({
  __esModule: true,
  default: { findByPk: jest.fn() },
}));
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: silentLogger,
  withRequestId: () => silentLogger,
  redact: (v) => v,
}));

const { generateToken, verifyAccessToken } = await import('../../middleware/auth.js');

const SECRET = 'unit-test-jwt-secret-do-not-use-in-prod';
const ENV_KEYS = ['JWT_SECRET', 'JWT_EXPIRE'];

let snapshot = {};

beforeEach(() => {
  snapshot = {};
  for (const key of ENV_KEYS) snapshot[key] = process.env[key];
  process.env.JWT_SECRET = SECRET;
  delete process.env.JWT_EXPIRE;
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (snapshot[key] === undefined) delete process.env[key];
    else process.env[key] = snapshot[key];
  }
});

describe('generateToken — access token lifetime', () => {
  it('defaults to a 15-minute lifetime (not the old 7 days)', () => {
    const decoded = jwt.verify(generateToken(42), SECRET);

    expect(decoded.id).toBe(42);
    expect(decoded.exp - decoded.iat).toBe(15 * 60);
  });

  it('still honours a JWT_EXPIRE override', () => {
    process.env.JWT_EXPIRE = '5m';
    const decoded = jwt.verify(generateToken(7), SECRET);
    expect(decoded.exp - decoded.iat).toBe(5 * 60);
  });

  it('supports second-based overrides', () => {
    process.env.JWT_EXPIRE = '900s';
    const decoded = jwt.verify(generateToken(7), SECRET);
    expect(decoded.exp - decoded.iat).toBe(900);
  });
});

describe('verifyAccessToken — signature policy', () => {
  it('accepts an HS256 token signed with JWT_SECRET', () => {
    const token = jwt.sign({ id: 3 }, SECRET, { algorithm: 'HS256' });
    expect(verifyAccessToken(token).id).toBe(3);
  });

  it('rejects an HS512 token even though the secret matches (algorithm pinning)', () => {
    const token = jwt.sign({ id: 3 }, SECRET, { algorithm: 'HS512' });
    expect(() => verifyAccessToken(token)).toThrow();
  });

  it('rejects an expired token', () => {
    const token = jwt.sign({ id: 3 }, SECRET, { algorithm: 'HS256', expiresIn: -10 });
    expect(() => verifyAccessToken(token)).toThrow(/expired/i);
  });
});
