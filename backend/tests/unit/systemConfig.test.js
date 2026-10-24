import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * systemConfig.service tests.
 *
 * The service holds payment/SMTP credentials at runtime and backs the admin
 * settings panel. Key behaviours under test: defaults merging, dotted-path
 * gets, secret masking (public + admin views must never leak private keys),
 * fail-open when the DB is offline, and the Redis cache layer.
 */

const mockFindAll = jest.fn();
const mockUpsert = jest.fn();
const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

let redisAvailable = false;
const fakeRedis = {
  isReady: true,
  get: jest.fn(),
  set: jest.fn(),
};

jest.unstable_mockModule('../../models/SystemConfig.js', () => ({
  default: {
    findAll: mockFindAll,
    upsert: mockUpsert,
    // No sequelize pool -> _dbAvailable() is false in tests unless overridden
    sequelize: null,
  },
}));

jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  getRedis: () => fakeRedis,
  isRedisAvailable: () => redisAvailable,
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const { default: systemConfig } = await import('../../services/systemConfig.service.js');

beforeEach(() => {
  redisAvailable = false;
  systemConfig.memory = {};
  systemConfig.memoryLoaded = false;
  jest.clearAllMocks();
  mockFindAll.mockResolvedValue([]);
  mockUpsert.mockResolvedValue([{}, true]);
  fakeRedis.get.mockResolvedValue(null);
  fakeRedis.set.mockResolvedValue('OK');
});

describe('defaults and merging', () => {
  it('returns built-in defaults when DB is empty', async () => {
    const cfg = await systemConfig.getAll();
    expect(cfg.currency.code).toBe('USD');
    expect(cfg.payments.stripe.enabled).toBe(false);
    expect(cfg.setup.completed).toBe(false);
  });

  it('merges DB rows over defaults without losing default keys', async () => {
    mockFindAll.mockResolvedValueOnce([
      { key: 'business', value: { name: 'Acme Co' } },
    ]);
    const cfg = await systemConfig.getAll();
    expect(cfg.business.name).toBe('Acme Co');
    // default keys survive the merge
    expect(cfg.business.tagline).toBe('');
    expect(cfg.currency.code).toBe('USD');
  });
});

describe('get() with paths', () => {
  it('returns a whole group and dotted sub-paths', async () => {
    mockFindAll.mockResolvedValueOnce([
      { key: 'payments', value: { stripe: { enabled: true, publishableKey: 'pk_test_1' } } },
    ]);
    expect(await systemConfig.get('payments.stripe.publishableKey')).toBe('pk_test_1');
    expect((await systemConfig.get('payments')).stripe.enabled).toBe(true);
  });

  it('returns the fallback for unknown paths', async () => {
    await systemConfig.getAll();
    expect(await systemConfig.get('does.not.exist', 'FB')).toBe('FB');
    expect(await systemConfig.get('payments.stripe.secretKey', null)).toBe('');
  });

  it('returns the full snapshot for an empty path', async () => {
    const full = await systemConfig.get('');
    expect(full).toHaveProperty('business');
    expect(full).toHaveProperty('payments');
  });
});

describe('set() and bulkSet()', () => {
  it('upserts to the DB and updates the in-memory snapshot', async () => {
    await systemConfig.set('business', { name: 'New Name', supportEmail: 'a@b.c' });
    expect(mockUpsert).toHaveBeenCalledWith({
      key: 'business',
      value: { name: 'New Name', supportEmail: 'a@b.c' },
    });
    const cfg = await systemConfig.getAll();
    expect(cfg.business.name).toBe('New Name');
  });

  it('merges repeated sets on the same key', async () => {
    await systemConfig.set('business', { name: 'First' });
    await systemConfig.set('business', { tagline: 'Second' });
    const cfg = await systemConfig.getAll();
    expect(cfg.business.name).toBe('First');
    expect(cfg.business.tagline).toBe('Second');
  });

  it('bulkSet saves every entry and skips invalid keys', async () => {
    await systemConfig.bulkSet({
      business: { name: 'Bulk' },
      '': { ignored: true },
      currency: { code: 'PKR' },
    });
    const keys = mockUpsert.mock.calls.map((c) => c[0].key);
    expect(keys).toContain('business');
    expect(keys).toContain('currency');
    expect(keys).not.toContain('');
  });

  it('writes through to Redis when available', async () => {
    redisAvailable = true;
    await systemConfig.set('business', { name: 'Cached' });
    expect(fakeRedis.set).toHaveBeenCalled();
    const [cacheKey] = fakeRedis.set.mock.calls[0];
    expect(cacheKey).toBe('system_config:full');
  });
});

describe('isConfigured()', () => {
  it('fails open (true) when the DB is offline', async () => {
    // sequelize is null in the mock -> offline
    expect(await systemConfig.isConfigured()).toBe(true);
  });
});

describe('secret masking', () => {
  it('getPublicConfig never exposes private keys', async () => {
    mockFindAll.mockResolvedValueOnce([
      {
        key: 'payments',
        value: {
          stripe: { enabled: true, secretKey: 'sk_live_SECRET', publishableKey: 'pk_live_1', webhookSecret: 'whsec_SECRET' },
          paypal: { enabled: true, clientId: 'cid', clientSecret: 'cs_SECRET' },
        },
      },
    ]);
    const pub = await systemConfig.getPublicConfig();
    const serialized = JSON.stringify(pub);
    expect(serialized).not.toContain('sk_live_SECRET');
    expect(serialized).not.toContain('whsec_SECRET');
    expect(serialized).not.toContain('cs_SECRET');
    expect(pub.payments.stripeEnabled).toBe(true);
    expect(pub.payments.stripePublishableKey).toBe('pk_live_1');
  });

  it('maskAdminConfig redacts every private credential', async () => {
    mockFindAll.mockResolvedValueOnce([
      {
        key: 'payments',
        value: {
          stripe: { secretKey: 'sk_SECRET', webhookSecret: 'whsec_SECRET', publishableKey: 'pk_ok' },
          paypal: { clientSecret: 'cs_SECRET', webhookId: 'wid_SECRET', clientId: 'cid_ok' },
        },
      },
      { key: 'smtp', value: { pass: 'smtp_SECRET', host: 'smtp.ok.com' } },
    ]);
    const cfg = await systemConfig.getAll();
    const masked = systemConfig.maskAdminConfig(cfg);
    const serialized = JSON.stringify(masked);
    expect(serialized).not.toContain('sk_SECRET');
    expect(serialized).not.toContain('whsec_SECRET');
    expect(serialized).not.toContain('cs_SECRET');
    expect(serialized).not.toContain('wid_SECRET');
    expect(serialized).not.toContain('smtp_SECRET');
    // Public values stay visible
    expect(masked.payments.stripe.publishableKey).toBe('pk_ok');
    expect(masked.smtp.host).toBe('smtp.ok.com');
  });
});

describe('redis read path', () => {
  it('loads from Redis before touching the DB', async () => {
    redisAvailable = true;
    fakeRedis.get.mockResolvedValueOnce(JSON.stringify({ business: { name: 'FromRedis' } }));
    const cfg = await systemConfig.getAll();
    expect(cfg.business.name).toBe('FromRedis');
    expect(mockFindAll).not.toHaveBeenCalled();
  });

  it('falls back to the DB when Redis is empty', async () => {
    redisAvailable = true;
    fakeRedis.get.mockResolvedValueOnce(null);
    mockFindAll.mockResolvedValueOnce([{ key: 'business', value: { name: 'FromDB' } }]);
    const cfg = await systemConfig.getAll();
    expect(cfg.business.name).toBe('FromDB');
    expect(mockFindAll).toHaveBeenCalled();
  });
});

describe('DB failure handling', () => {
  it('warns and serves defaults when findAll throws', async () => {
    mockFindAll.mockRejectedValueOnce(new Error('connection lost'));
    const cfg = await systemConfig.getAll();
    expect(mockLogger.warn).toHaveBeenCalled();
    expect(cfg.currency.code).toBe('USD');
  });
});
