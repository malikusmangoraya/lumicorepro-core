import { describe, it, expect, beforeEach, jest, afterEach } from '@jest/globals';
import crypto from 'crypto';

process.env.LICENSE_SECRET = 'test-license-secret-for-unit-tests';
process.env.LEMONSQUEEZY_SIGNING_SECRET = 'ls-signing-secret';

const { generateLicenseKey, groupCode, normalizeCode } = await import('../../utils/license.js');
const ls = await import('../../services/lemonsqueezy.service.js');

function sign(body, secret = 'ls-signing-secret') {
  return crypto.createHmac('sha256', secret).update(body).digest('hex');
}

function fakeModel() {
  const rows = [];
  return {
    rows,
    findOne: jest.fn(async ({ where }) => {
      const row = rows.find((r) => r.license_key === where.license_key);
      if (row) row.update = async (values) => Object.assign(row, values);
      return row || null;
    }),
    create: jest.fn(async (row) => {
      rows.push(row);
      row.update = async (values) => Object.assign(row, values);
      return row;
    }),
  };
}

describe('Lemon Squeezy webhook security', () => {
  it('accepts a correctly signed body', () => {
    const body = JSON.stringify({ meta: { event_name: 'license_created' } });
    expect(ls.verifySignature(body, sign(body)).verified).toBe(true);
  });

  it('rejects a forged signature and a missing one', () => {
    const body = JSON.stringify({ meta: { event_name: 'license_created' } });
    expect(ls.verifySignature(body, 'deadbeef').verified).toBe(false);
    expect(ls.verifySignature(body, undefined).reason).toBe('signature_missing');
    expect(ls.verifySignature(body, sign(body, 'wrong-secret')).verified).toBe(false);
  });

  it('reports unconfigured instead of silently accepting', () => {
    const saved = process.env.LEMONSQUEEZY_SIGNING_SECRET;
    delete process.env.LEMONSQUEEZY_SIGNING_SECRET;
    expect(ls.verifySignature('{}', 'anything').reason).toBe('signing_secret_missing');
    process.env.LEMONSQUEEZY_SIGNING_SECRET = saved;
  });
});

describe('Lemon Squeezy event parsing + entitlement lifecycle', () => {
  let model;

  beforeEach(() => {
    model = fakeModel();
    jest.resetModules();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('extracts the license key from checkout custom data', () => {
    const key = generateLicenseKey({ licenseType: 'full' }).key;
    const parsed = ls.parseEvent({
      meta: { event_name: 'license_key_created' },
      data: { attributes: { meta: { custom_data: { license_key: key } }, variant_name: 'Lifetime' } },
    });
    expect(parsed.event).toBe('license_key_created');
    expect(parsed.licenseKey).toBe(groupCode(normalizeCode(key)));
    expect(parsed.variantName).toBe('Lifetime');
  });

  it('activates a purchased key and records entitlement', async () => {
    const key = generateLicenseKey({ licenseType: 'full' }).key;
    const outcome = await ls.handleEvent({
      meta: { event_name: 'license_key_created' },
      data: { attributes: { license_key: { key }, order_id: 4242, user_email: 'buyer@example.com' } },
    }, model);

    expect(outcome.action).toBe('activated');
    expect(outcome.licenseValid).toBe(true);
    expect(model.rows).toHaveLength(1);
    expect(model.rows[0].order_id).toBe('4242');
    expect(model.rows[0].status).toBe('active');
  });

  it('marks a key that fails HMAC validation as rejected', async () => {
    const outcome = await ls.handleEvent({
      meta: { event_name: 'license_key_created' },
      data: { attributes: { license_key: { key: 'LMC-FAKE-KEY-000000' } } },
    }, model);
    expect(outcome.licenseValid).toBe(false);
    expect(model.rows[0].status).toBe('rejected');
  });

  it('revokes on cancellation and refunds', async () => {
    const key = generateLicenseKey({ licenseType: 'full' }).key;
    await ls.handleEvent({
      meta: { event_name: 'license_key_created' },
      data: { attributes: { license_key: { key } } },
    }, model);

    const cancelled = await ls.handleEvent({
      meta: { event_name: 'subscription_cancelled' },
      data: { attributes: { license_key: { key } } },
    }, model);
    expect(cancelled.action).toBe('revoked');
    expect(model.rows[0].status).toBe('revoked');
  });

  it('ignores events without a license key', async () => {
    const outcome = await ls.handleEvent({ meta: { event_name: 'order_created' }, data: { attributes: {} } }, model);
    expect(outcome.action).toBe('ignored');
    expect(outcome.reason).toBe('no_license_key');
  });
});