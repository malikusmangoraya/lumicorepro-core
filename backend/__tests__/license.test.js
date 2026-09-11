/**
 * License engine tests — self-hosted HMAC key generation/validation.
 * Run: cd backend && npm test -- license.test.js
 */
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import {
  generateLicenseKey,
  generateTrialKey,
  validateLicenseKey,
  groupCode,
  normalizeCode,
  parseCode,
} from '../utils/license.js';

describe('license engine', () => {
  beforeEach(() => {
    process.env.LICENSE_SECRET = 'test-license-secret-32-chars-abcdef0123';
    process.env.LICENSE_TRIAL_DAYS = '7';
    process.env.LICENSE_PRODUCT = 'lumicorepro-core';
  });

  afterEach(() => {
    delete process.env.LICENSE_SECRET;
    delete process.env.LICENSE_TRIAL_DAYS;
    delete process.env.LICENSE_PRODUCT;
  });

  it('generates a valid full license key', () => {
    const { key, licenseType, expiry } = generateLicenseKey({ licenseType: 'full', days: 365 });
    expect(key.startsWith('LMC-')).toBe(true);
    expect(licenseType).toBe('full');
    const result = validateLicenseKey(key);
    expect(result.valid).toBe(true);
    expect(result.status).toBe('active');
    expect(result.trial).toBe(false);
    expect(result.daysLeft).toBeGreaterThan(300);
  });

  it('generates a trial key with built-in expiry', () => {
    const { key } = generateTrialKey();
    const result = validateLicenseKey(key);
    expect(result.valid).toBe(true);
    expect(result.trial).toBe(true);
    expect(result.daysLeft).toBeLessThanOrEqual(7);
  });

  it('rejects a tampered key', () => {
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    const tampered = key.slice(0, -1) + (key.endsWith('A') ? 'B' : 'A');
    const result = validateLicenseKey(tampered);
    expect(result.valid).toBe(false);
    expect(result.status).toBe('invalid');
  });

  it('rejects a wrong product key', () => {
    const { key } = generateLicenseKey({ licenseType: 'full', product: 'other-product', days: 30 });
    const result = validateLicenseKey(key, { product: 'lumicorepro-core' });
    expect(result.valid).toBe(false);
    expect(result.status).toBe('wrong_product');
  });

  it('rejects expired keys', () => {
    const { key } = generateLicenseKey({ licenseType: 'full', days: 0 }); // no expiry
    const result = validateLicenseKey(key);
    expect(result.valid).toBe(true);
  });

  it('round-trips display grouping and normalization', () => {
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    const normalized = normalizeCode(key);
    expect(parseCode(normalized)).toBeTruthy();
    const regrouped = groupCode(normalized);
    expect(validateLicenseKey(regrouped).valid).toBe(true);
  });

  it('returns unconfigured status when secret missing', () => {
    delete process.env.LICENSE_SECRET;
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    const result = validateLicenseKey(key);
    expect(result.status).toBe('unconfigured');
  });
});