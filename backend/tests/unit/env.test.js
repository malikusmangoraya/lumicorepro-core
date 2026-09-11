import { describe, it, expect } from '@jest/globals';
import { validateConfig } from '../../config/env.js';

describe('Environment validation (fail-fast)', () => {
  const base = {
    JWT_SECRET: 'x'.repeat(32),
    JWT_REFRESH_SECRET: 'y'.repeat(32),
  };

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
    expect(errors.join('\n')).toMatch(/at least 16 chars/);
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