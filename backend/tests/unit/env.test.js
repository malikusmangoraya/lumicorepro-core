import { describe, it, expect } from '@jest/globals';
import { validateConfig, parseDurationMs, isValidOrigin } from '../../config/env.js';

const base = {
  JWT_SECRET: 'x'.repeat(32),
  JWT_REFRESH_SECRET: 'y'.repeat(32),
  DATABASE_URL: 'postgres://postgres:postgres@localhost:5432/lumicorepro',
  ALLOWED_ORIGINS: 'https://app.example.com',
};

describe('Environment validation (fail-fast)', () => {

  it('accepts a valid environment', () => {
    const { ok, errors } = validateConfig(base);
    expect(ok).toBe(true);
    expect(errors).toEqual([]);
  });

  it('reports missing required vars', () => {
    const { ok, errors } = validateConfig({});
    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/JWT_SECRET/);
    expect(errors.join('\n')).toMatch(/JWT_REFRESH_SECRET/);
  });

  it('rejects a too-short JWT_SECRET', () => {
    const { ok, errors } = validateConfig({ ...base, JWT_SECRET: 'short' });
    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/at least 32 chars/);
  });

  it('rejects JWT secrets of 16-31 chars that the old 16-char policy allowed', () => {
    for (const length of [16, 24, 31]) {
      const { ok, errors } = validateConfig({
        ...base,
        JWT_SECRET: 'x'.repeat(length),
        JWT_REFRESH_SECRET: 'y'.repeat(length),
      });
      expect(ok).toBe(false);
      expect(errors.join('\n')).toMatch(/at least 32 chars/);
    }
  });

  it('accepts a 32-char JWT secret', () => {
    const { ok, errors } = validateConfig(base);
    expect(ok).toBe(true);
    expect(errors).toEqual([]);
  });

  it('rejects out-of-range PORT', () => {
    const { ok, errors } = validateConfig({ ...base, PORT: '99999' });
    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/PORT/);
  });

  it('accepts a valid numeric PORT', () => {
    const { ok } = validateConfig({ ...base, PORT: '5000' });
    expect(ok).toBe(true);
  });
});

describe('parseDurationMs (JWT duration helper)', () => {
  it('parses jwt-style durations', () => {
    expect(parseDurationMs('15m')).toBe(900_000);
    expect(parseDurationMs('900s')).toBe(900_000);
    expect(parseDurationMs('1h')).toBe(3_600_000);
    expect(parseDurationMs('7d')).toBe(604_800_000);
    expect(parseDurationMs('500ms')).toBe(500);
    expect(parseDurationMs('900')).toBe(900_000); // bare number = seconds
    expect(parseDurationMs('15M')).toBe(900_000);
  });

  it('returns null for empty, malformed, or non-positive values', () => {
    for (const value of [undefined, null, '', 'soon', '15 minutes', '-5m', 'm', '0m', '0']) {
      expect(parseDurationMs(value)).toBeNull();
    }
  });

  it('validates browser origins without accepting paths or credentials', () => {
    expect(isValidOrigin('https://app.example.com')).toBe(true);
    expect(isValidOrigin('http://localhost:5173')).toBe(true);
    for (const value of ['foo', 'https://app.example.com/api', 'https://user@app.example.com', 'ftp://app.example.com']) {
      expect(isValidOrigin(value)).toBe(false);
    }
  });
});

describe('JWT_EXPIRE policy (15m access tokens, 1h production ceiling)', () => {
  it('accepts the documented 15m default in production', () => {
    const { ok, errors } = validateConfig({
      ...base,
      NODE_ENV: 'production',
      JWT_EXPIRE: '15m',
    });
    expect(errors).toEqual([]);
    expect(ok).toBe(true);
  });

  it('accepts exactly 1h in production (boundary)', () => {
    const { ok } = validateConfig({ ...base, NODE_ENV: 'production', JWT_EXPIRE: '1h' });
    expect(ok).toBe(true);
  });

  it('REJECTS a 7d access token in production with a policy message', () => {
    const { ok, errors } = validateConfig({
      ...base,
      NODE_ENV: 'production',
      JWT_EXPIRE: '7d',
    });

    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/JWT_EXPIRE/);
    expect(errors.join('\n')).toMatch(/1-hour maximum/);
    expect(errors.join('\n')).toMatch(/JWT_EXPIRE=15m/);
  });

  it('REJECTS anything just over the 1h ceiling in production', () => {
    const { ok, errors } = validateConfig({
      ...base,
      NODE_ENV: 'production',
      JWT_EXPIRE: '3601s',
    });
    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/exceeds the 1-hour maximum/);
  });

  it('allows a longer access token outside production (dev override)', () => {
    const { ok, errors } = validateConfig({
      ...base,
      NODE_ENV: 'development',
      JWT_EXPIRE: '7d',
    });
    expect(errors).toEqual([]);
    expect(ok).toBe(true);
  });

  it('rejects a malformed JWT_EXPIRE in every environment', () => {
    for (const NODE_ENV of ['production', 'development', 'test']) {
      const { ok, errors } = validateConfig({ ...base, NODE_ENV, JWT_EXPIRE: 'whenever' });
      expect(ok).toBe(false);
      expect(errors.join('\n')).toMatch(/not a duration/);
    }
  });

  it('does not complain when JWT_EXPIRE is unset (code default applies)', () => {
    const { ok, errors } = validateConfig({ ...base, NODE_ENV: 'production' });
    expect(errors).toEqual([]);
    expect(ok).toBe(true);
  });
});

describe('Production infrastructure config', () => {
  it('accepts documented production database and origin settings', () => {
    const { ok, errors } = validateConfig({ ...base, NODE_ENV: 'production' });

    expect(errors).toEqual([]);
    expect(ok).toBe(true);
  });

  it('rejects a missing production DATABASE_URL', () => {
    const { DATABASE_URL, ...withoutDatabase } = base;
    const { ok, errors } = validateConfig({ ...withoutDatabase, NODE_ENV: 'production' });

    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/DATABASE_URL/);
  });

  it('rejects missing or blank production ALLOWED_ORIGINS', () => {
    for (const ALLOWED_ORIGINS of [undefined, '', ' , ', 'https://app.example.com/api']) {
      const { ok, errors } = validateConfig({ ...base, NODE_ENV: 'production', ALLOWED_ORIGINS });

      expect(ok).toBe(false);
      expect(errors.join('\n')).toMatch(/ALLOWED_ORIGINS/);
    }
  });

  it('does not require production infrastructure settings outside production', () => {
    const { DATABASE_URL, ALLOWED_ORIGINS, ...withoutInfrastructure } = base;
    const { ok, errors } = validateConfig({ ...withoutInfrastructure, NODE_ENV: 'development' });

    expect(errors).toEqual([]);
    expect(ok).toBe(true);
  });
});

describe('Production secret placeholders', () => {
  it('rejects copied .env.example JWT values', () => {
    const { ok, errors } = validateConfig({
      ...base,
      NODE_ENV: 'production',
      JWT_SECRET: 'change-this-to-a-secure-random-string-at-least-32-chars',
      JWT_REFRESH_SECRET: 'your-super-secret-jwt-key-change-in-production-min-32-chars',
    });

    expect(ok).toBe(false);
    expect(errors.join('\n')).toMatch(/JWT_SECRET.*example\/placeholder secret/);
    expect(errors.join('\n')).toMatch(/JWT_REFRESH_SECRET.*example\/placeholder secret/);
  });
});