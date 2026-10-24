import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Mercado Pago service tests.
 *
 * The service exports a singleton whose `enabled` flag is computed from
 * `getGatewayConfig('mercadopago')` at import time, so each scenario loads a
 * fresh module instance with the env it needs (same pattern as
 * tests/unit/bkashService.test.js). `fetch` is always replaced with a mock —
 * no real network call is made and no API key is required.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const originalFetch = global.fetch;
const ENV_KEYS = [
  'MERCADOPAGO_ACCESS_TOKEN',
  'MERCADOPAGO_PUBLIC_KEY',
  'MERCADOPAGO_WEBHOOK_SECRET',
];
const originalEnv = Object.fromEntries(ENV_KEYS.map((key) => [key, process.env[key]]));

const WEBHOOK_SECRET = 'mp_webhook_secret';

const ENABLED_ENV = {
  MERCADOPAGO_ACCESS_TOKEN: 'APP_USR-access-token',
  MERCADOPAGO_PUBLIC_KEY: 'APP_USR-public-key',
  MERCADOPAGO_WEBHOOK_SECRET: WEBHOOK_SECRET,
};

/** Mercado Pago x-signature: hmacSha256(`id:<id>;request-id:<rid>;ts:<ts>;`). */
const signMp = (dataId, { ts = '1700000000', requestId = 'req-1', secret = WEBHOOK_SECRET } = {}) =>
  crypto
    .createHmac('sha256', secret)
    .update(`id:${dataId};request-id:${requestId};ts:${ts};`)
    .digest('hex');

const mpHeaders = (dataId, opts = {}) => ({
  'x-signature': `ts=${opts.ts || '1700000000'},v1=${signMp(dataId, opts)}`,
  'x-request-id': opts.requestId || 'req-1',
});

const ok = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const fail = (message) => ({
  ok: false,
  status: 400,
  json: async () => ({ message }),
  text: async () => message,
});

async function loadService(env = {}) {
  for (const key of ENV_KEYS) delete process.env[key];
  Object.assign(process.env, env);
  jest.resetModules();
  const mod = await import('../../services/payment/mercadopago.service.js');
  return mod.default;
}

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  global.fetch = originalFetch;
  for (const key of ENV_KEYS) {
    if (originalEnv[key] === undefined) delete process.env[key];
    else process.env[key] = originalEnv[key];
  }
});

describe('MercadoPagoService — configuration', () => {
  it('is disabled when MERCADOPAGO_ACCESS_TOKEN is missing', async () => {
    const service = await loadService();
    expect(service.enabled).toBe(false);
  });

  it('stays disabled for placeholder credentials containing "your_"', async () => {
    const service = await loadService({ MERCADOPAGO_ACCESS_TOKEN: 'your_mercadopago_token' });
    expect(service.enabled).toBe(false);
  });

  it('is enabled once a real-looking access token is present', async () => {
    const service = await loadService(ENABLED_ENV);
    expect(service.enabled).toBe(true);
    expect(service.accessToken).toBe('APP_USR-access-token');
  });

  it('exposes the gateway metadata consumed by the checkout UI', async () => {
    const service = await loadService();
    expect(service.name).toBe('Mercado Pago');
    expect(service.baseURL).toBe('https://api.mercadopago.com');
    expect(service.region).toBe('Latin America');
    expect(service.supportedCurrencies).toEqual(
      expect.arrayContaining(['ars', 'brl', 'mxn', 'usd', 'pyg'])
    );
    // Paraguay's ISO code is PYG — the old 'pym' entry was invalid.
    expect(service.supportedCurrencies).not.toContain('pym');
  });

  it('returns the public key fallback when the env key is absent', async () => {
    const service = await loadService();
    expect(service.getPublicKey()).toBe('TEST_PUBLIC_KEY');
  });

  it('returns the configured public key when present', async () => {
    const service = await loadService(ENABLED_ENV);
    expect(service.getPublicKey()).toBe('APP_USR-public-key');
  });
});

describe('MercadoPagoService — mock mode (gateway disabled)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService();
    global.fetch = jest.fn();
  });

  it('returns a mock preference without touching the network', async () => {
    const result = await service.createPreference({
      items: [{ title: 'Pro plan', quantity: 1, unit_price: 49.99 }],
      backUrl: 'https://shop.example.com/back',
    });

    expect(result.mock).toBe(true);
    expect(result.id).toMatch(/^mp_mock_\d+$/);
    expect(result.init_point).toBe('#');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('returns an auto-approved mock payment', async () => {
    const result = await service.processPayment({
      amount: 49.99,
      description: 'Pro plan',
      payerEmail: 'buyer@example.com',
    });

    expect(result).toMatchObject({ status: 'approved', mock: true });
    expect(result.id).toMatch(/^mpayment_mock_\d+$/);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('short-circuits refunds', async () => {
    await expect(service.refund({ paymentId: 'pay_1', amount: 10 })).resolves.toEqual({
      success: true,
      mock: true,
      paymentId: 'pay_1',
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

describe('MercadoPagoService — createPreference (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('posts the preference to /v1/preferences with the bearer token', async () => {
    global.fetch = jest.fn(async () => ok({ id: 'pref_1', init_point: 'https://mp/checkout' }));

    const result = await service.createPreference({
      items: [{ id: 'sku-1', title: 'Pro plan', quantity: 2, unit_price: 49.99 }],
      paymentMethods: { excluded_payment_types: [{ id: 'ticket' }] },
      backUrl: 'https://shop.example.com/checkout/back',
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mercadopago.com/v1/preferences');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(init.headers.Authorization).toBe('Bearer APP_USR-access-token');
    expect(JSON.parse(init.body)).toEqual({
      items: [{ id: 'sku-1', title: 'Pro plan', quantity: 2, unit_price: 49.99 }],
      back_url: 'https://shop.example.com/checkout/back',
      auto_return: 'approved',
      payment_methods: { excluded_payment_types: [{ id: 'ticket' }] },
    });
    expect(result).toMatchObject({ id: 'pref_1', init_point: 'https://mp/checkout', mock: false });
  });

  it('defaults items to an empty array and omits absent optional fields', async () => {
    global.fetch = jest.fn(async () => ok({ id: 'pref_2' }));

    await service.createPreference({});

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.items).toEqual([]);
    expect(body).not.toHaveProperty('payment_methods');
    expect(body).not.toHaveProperty('back_url');
  });

  it('throws a descriptive error and surfaces the gateway body on failure', async () => {
    global.fetch = jest.fn(async () => fail('invalid_access_token'));

    await expect(service.createPreference({ items: [] })).rejects.toThrow(
      'Mercado Pago preference failed: invalid_access_token'
    );
  });
});

describe('MercadoPagoService — processPayment (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('charges the card with the expected payload and defaults installments to 1', async () => {
    global.fetch = jest.fn(async () => ok({ id: 12345, status: 'approved' }));

    const result = await service.processPayment({
      amount: 199.9,
      description: 'Order #1001',
      payerEmail: 'buyer@example.com',
      token: 'card-token-abc',
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mercadopago.com/v1/payments');
    expect(init.headers.Authorization).toBe('Bearer APP_USR-access-token');
    expect(JSON.parse(init.body)).toEqual({
      transaction_amount: 199.9,
      description: 'Order #1001',
      payment_method_id: 'visa',
      payer: { email: 'buyer@example.com' },
      token: 'card-token-abc',
      installments: 1,
    });
    expect(result).toMatchObject({ id: 12345, status: 'approved', mock: false });
  });

  it('passes the requested installment count through unchanged', async () => {
    global.fetch = jest.fn(async () => ok({ id: 1, status: 'in_process' }));

    await service.processPayment({ amount: 300, payerEmail: 'b@e.com', token: 't', installments: 6 });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body).installments).toBe(6);
  });

  it('throws with the gateway reason when the charge is rejected', async () => {
    global.fetch = jest.fn(async () => fail('cc_rejected_insufficient_amount'));

    await expect(
      service.processPayment({ amount: 10, payerEmail: 'b@e.com', token: 't' })
    ).rejects.toThrow('Mercado Pago payment failed: cc_rejected_insufficient_amount');
  });
});

describe('MercadoPagoService — refund (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('posts a partial refund with the requested amount', async () => {
    global.fetch = jest.fn(async () => ok({ id: 'refund_1', status: 'approved' }));

    const result = await service.refund({ paymentId: 'pay_99', amount: 25.5 });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mercadopago.com/v1/payments/pay_99/refunds');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer APP_USR-access-token');
    expect(JSON.parse(init.body)).toEqual({ amount: 25.5 });
    expect(result).toEqual({ success: true, refunds: { id: 'refund_1', status: 'approved' } });
  });

  it('sends no body for a full refund (amount omitted or zero)', async () => {
    global.fetch = jest.fn(async () => ok({ id: 'refund_2' }));

    await service.refund({ paymentId: 'pay_99' });
    expect(global.fetch.mock.calls[0][1].body).toBeUndefined();

    await service.refund({ paymentId: 'pay_99', amount: 0 });
    expect(global.fetch.mock.calls[1][1].body).toBeUndefined();
  });

  it('throws when the gateway refuses the refund', async () => {
    global.fetch = jest.fn(async () => fail('not_refundable'));

    await expect(service.refund({ paymentId: 'pay_99', amount: 5 })).rejects.toThrow(
      'Mercado Pago refund failed: not_refundable'
    );
  });
});

describe('MercadoPagoService — verifyWebhook', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('accepts an x-signature over the documented manifest', () => {
    expect(service.verifyWebhook('pay_123', mpHeaders('pay_123'))).toBe(true);
  });

  it('accepts the capitalization Mercado Pago actually sends', () => {
    const headers = {
      'X-Signature': `ts=1700000000,v1=${signMp('pay_123')}`,
      'X-Request-Id': 'req-1',
    };

    expect(service.verifyWebhook('pay_123', headers)).toBe(true);
  });

  it('binds the signature to data id, request id and timestamp', () => {
    const headers = mpHeaders('pay_123');

    expect(service.verifyWebhook('pay_999', headers)).toBe(false);
    expect(service.verifyWebhook('pay_123', { ...headers, 'x-request-id': 'req-2' })).toBe(false);
    // Signature over ts=1700000000 presented under a different ts.
    expect(
      service.verifyWebhook('pay_123', {
        'x-signature': `ts=1700000001,v1=${signMp('pay_123', { ts: '1700000000' })}`,
        'x-request-id': 'req-1',
      }),
    ).toBe(false);
  });

  it('rejects a signature made with the wrong secret', () => {
    expect(
      service.verifyWebhook('pay_123', mpHeaders('pay_123', { secret: 'attacker_secret' })),
    ).toBe(false);
  });

  it('fails closed when no webhook secret is configured', async () => {
    const unconfigured = await loadService({
      MERCADOPAGO_ACCESS_TOKEN: 'APP_USR-access-token',
    });

    expect(unconfigured.verifyWebhook('pay_123', mpHeaders('pay_123'))).toBe(false);
    expect(mockLogger.warn).toHaveBeenCalledWith(
      'Mercado Pago webhook rejected: webhook secret is not configured',
    );
  });

  it('rejects missing ids, missing signatures and malformed headers without throwing', () => {
    expect(service.verifyWebhook('pay_123')).toBe(false);
    expect(service.verifyWebhook('', mpHeaders('pay_123'))).toBe(false);
    expect(service.verifyWebhook('pay_123', {})).toBe(false);
    expect(service.verifyWebhook('pay_123', { 'x-signature': 'garbage' })).toBe(false);
    expect(service.verifyWebhook('pay_123', { 'x-signature': 'ts=1' })).toBe(false);
    expect(service.verifyWebhook('pay_123', { 'x-signature': 'v1=abc' })).toBe(false);
    expect(() => service.verifyWebhook('pay_123', { 'x-signature': 'ts=1,v1=deadbeef' })).not.toThrow();
  });
});

describe('MercadoPagoService — handleWebhook', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('dispatches payment events only after verifying the signature', async () => {
    const event = { action: 'payment', data: { id: 'pay_123' } };

    await expect(service.handleWebhook(event, mpHeaders('pay_123'))).resolves.toEqual({
      valid: true,
    });
    expect(mockLogger.info).toHaveBeenCalledWith('Mercado Pago payment event: pay_123');
  });

  it('logs refund events with the resource id', async () => {
    const event = { action: 'refund', data: { id: 'refund_123' } };

    await expect(service.handleWebhook(event, mpHeaders('refund_123'))).resolves.toEqual({
      valid: true,
    });
    expect(mockLogger.info).toHaveBeenCalledWith('Mercado Pago refund event: refund_123');
  });

  it('accepts events that only carry a top-level id', async () => {
    const event = { action: 'payment', id: 'pay_top' };

    await expect(service.handleWebhook(event, mpHeaders('pay_top'))).resolves.toEqual({
      valid: true,
    });
    expect(mockLogger.info).toHaveBeenCalledWith('Mercado Pago payment event: pay_top');
  });

  it('falls back to the legacy type field when action is absent', async () => {
    const event = { type: 'payment', data: { id: 'pay_typed' } };

    await expect(service.handleWebhook(event, mpHeaders('pay_typed'))).resolves.toEqual({
      valid: true,
    });
    expect(mockLogger.info).toHaveBeenCalledWith('Mercado Pago payment event: pay_typed');
  });

  it('logs unhandled actions instead of throwing', async () => {
    const event = { action: 'subscription', data: { id: 'sub_1' } };

    await expect(service.handleWebhook(event, mpHeaders('sub_1'))).resolves.toEqual({
      valid: true,
    });
    expect(mockLogger.info).toHaveBeenCalledWith('Unhandled Mercado Pago webhook: subscription');
  });

  it('rejects an event without a valid signature and does not dispatch it', async () => {
    const event = { action: 'payment', data: { id: 'pay_123' } };

    await expect(service.handleWebhook(event)).resolves.toEqual({
      valid: false,
      reason: 'invalid or missing signature',
    });
    await expect(
      service.handleWebhook(event, { 'x-signature': 'ts=1,v1=deadbeef', 'x-request-id': 'req-1' }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });

    expect(mockLogger.info).not.toHaveBeenCalled();
  });
});
