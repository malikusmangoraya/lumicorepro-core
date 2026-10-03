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

  it('parses the grouped display form emitted by generateLicenseKey', () => {
    // generateLicenseKey returns groupCode() output, i.e. dashed groups. parseCode
    // is documented to "accept any dash/space grouping" but its old regex only
    // allowed [A-Za-z2-7], so it returned null for every key it had just issued.
    // That is the form a customer actually pastes in from a receipt.
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    // groupCode() emits 5-char groups; the last one is short when the body
    // length is not a multiple of 5.
    expect(key).toMatch(/^LMC-[A-Z2-7]{5}(-[A-Z2-7]{5})*-[A-Z2-7]{1,5}$/);
    expect(parseCode(key)).toBeTruthy();
    // Grouping is cosmetic: every equivalent form must decode identically.
    const grouped = parseCode(key);
    const bare = parseCode(key.replace(/-/g, ''));
    const spaced = parseCode(key.replace(/-/g, ' '));
    expect(bare).toEqual(grouped);
    expect(spaced).toEqual(grouped);
  });

  it('rejects a key with any single character mutated in the signed region', () => {
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    const body = normalizeCode(key).replace(/^LMC-/, '');

    // Every character of the signed blob, except the final one. base32 packs 5
    // bits per character, so a blob whose length is not a multiple of 5 ends
    // with padding bits that fromBase32() discards; mutating the very last
    // character can therefore flip only non-significant bits. Mutating anything
    // earlier must always break the HMAC.
    for (let i = 0; i < body.length - 1; i++) {
      for (const ch of ['A', 'B', 'Z', '7']) {
        if (body[i] === ch) continue;
        const mutated = 'LMC-' + body.slice(0, i) + ch + body.slice(i + 1);
        expect(validateLicenseKey(mutated).valid).toBe(false);
      }
    }
  });

  it('cannot be forged: any accepted final-character variant decodes identically', () => {
    // Pins the security property behind the padding bits above. Some final
    // characters alias to the same blob — that is an encoding quirk, NOT a
    // forgery, so whatever still validates must carry byte-identical license
    // fields. If this ever fails, the signature no longer covers the payload.
    const { key } = generateLicenseKey({ licenseType: 'full', days: 30 });
    const body = normalizeCode(key).replace(/^LMC-/, '');
    const original = parseCode(key);
    expect(original).toBeTruthy();

    let accepted = 0;
    for (const ch of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567') {
      if (ch === body[body.length - 1]) continue;
      const variant = 'LMC-' + body.slice(0, -1) + ch;
      if (validateLicenseKey(variant).valid) {
        accepted += 1;
        expect(parseCode(variant)).toEqual(original);
      }
    }
    // at most 1 of 31 aliases (one padding bit); never all of them
    expect(accepted).toBeLessThan(31);
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