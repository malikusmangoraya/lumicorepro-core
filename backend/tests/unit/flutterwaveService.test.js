import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Flutterwave gateway tests.
 *
 * The service is a singleton built from `getGatewayConfig('flutterwave')` plus
 * process.env at import time, so every scenario reloads the module with the
 * config mock and env it needs. Network access is always a jest.fn().
 *
 * Webhooks are authenticated with the plain shared secret from the dashboard,
 * compared against the `verif-hash` header — not an HMAC of the body.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };
const mockGetGatewayConfig = jest.fn();

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

jest.unstable_mockModule('../../services/payment/config.js', () => ({
  getGatewayConfig: mockGetGatewayConfig,
  default: { getGatewayConfig: mockGetGatewayConfig },
}));

const SERVICE_PATH = '../../services/payment/flutterwave.service.js';
const ENV_KEYS = [
  'FLUTTERWAVE_SECRET_KEY',
  'FLUTTERWAVE_PUBLIC_KEY',
  'FLUTTERWAVE_ENCRYPTION_KEY',
  'FLUTTERWAVE_WEBHOOK_HASH',
];

const WEBHOOK_HASH = 'flw-webhook-hash-secret';

const LIVE_ENV = {
  FLUTTERWAVE_SECRET_KEY: 'flw-secret-test',
  FLUTTERWAVE_PUBLIC_KEY: 'FLWPUBK_TEST_env123',
  FLUTTERWAVE_ENCRYPTION_KEY: 'flw-encryption-test',
  FLUTTERWAVE_WEBHOOK_HASH: WEBHOOK_HASH,
};

const originalFetch = global.fetch;

const okResponse = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const errorResponse = (text, status = 400) => ({
  ok: false,
  status,
  json: async () => ({}),
  text: async () => text,
});

let savedEnv;

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
  savedEnv = {};
  for (const key of ENV_KEYS) {
    savedEnv[key] = process.env[key];
    delete process.env[key];
  }
});

afterEach(() => {
  global.fetch = originalFetch;
  for (const key of ENV_KEYS) {
    if (savedEnv[key] === undefined) delete process.env[key];
    else process.env[key] = savedEnv[key];
  }
});

async function loadService({ env = {}, config = { enabled: true } } = {}) {
  for (const key of ENV_KEYS) delete process.env[key];
  Object.assign(process.env, env);
  mockGetGatewayConfig.mockReturnValue(config);
  jest.resetModules();
  const mod = await import(SERVICE_PATH);
  return mod.default;
}

describe('flutterwave service - configuration', () => {
  it('builds its identity from the flutterwave gateway config', async () => {
    const svc = await loadService();

    expect(mockGetGatewayConfig).toHaveBeenCalledWith('flutterwave');
    expect(svc.enabled).toBe(true);
    expect(svc.name).toBe('Flutterwave');
    expect(svc.baseURL).toBe('https://api.flutterwave.com/v3');
    expect(svc.region).toBe('Africa');
    expect(svc.supportedCurrencies).toEqual(
      expect.arrayContaining(['ngn', 'ghs', 'ksh', 'egp', 'usd', 'gbp', 'eur', 'zar', 'tzs']),
    );
  });

  it('stays disabled when the gateway config is disabled', async () => {
    const svc = await loadService({ config: { enabled: false } });
    expect(svc.enabled).toBe(false);
  });

  it('reads secret, public and encryption keys from the environment', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(svc.secretKey).toBe('flw-secret-test');
    expect(svc.publicKey).toBe('FLWPUBK_TEST_env123');
    expect(svc.encryptionKey).toBe('flw-encryption-test');
  });

  it('exposes the env public key and falls back to the documented test key', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    expect(svc.getPublicKey()).toBe('FLWPUBK_TEST_env123');

    delete process.env.FLUTTERWAVE_PUBLIC_KEY;
    expect(svc.getPublicKey()).toBe('FLWPUBK_TEST');
  });
});

describe('flutterwave service - initializeTransaction', () => {
  it('returns a mock checkout link without touching the network when disabled', async () => {
    const svc = await loadService({ config: { enabled: false } });

    const result = await svc.initializeTransaction({
      amount: 5000,
      currency: 'NGN',
      email: 'buyer@example.com',
      txRef: 'ref-1',
      redirectUrl: 'https://shop.example.com/callback',
    });

    expect(result).toMatchObject({
      link: 'https://shop.example.com/callback',
      status: 'pending',
      mock: true,
    });
    expect(result.id).toMatch(/^flw_mock_\d+$/);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('uses "#" as the mock link when no redirect URL is supplied', async () => {
    const svc = await loadService({ config: { enabled: false } });
    const result = await svc.initializeTransaction({ amount: 10, currency: 'USD' });
    expect(result.link).toBe('#');
  });

  it('posts the charge to /payments with bearer auth and a snake_case payload', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(
      okResponse({ status: 'success', data: { id: 42, link: 'https://checkout.flw', status: 'success' } }),
    );

    const result = await svc.initializeTransaction({
      amount: 5000,
      currency: 'NGN',
      email: 'buyer@example.com',
      firstName: 'Ada',
      lastName: 'Obi',
      txRef: 'ref-1',
      redirectUrl: 'https://shop.example.com/callback',
      meta: { orderId: 'ord-1' },
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.flutterwave.com/v3/payments');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer flw-secret-test',
    });
    expect(JSON.parse(init.body)).toEqual({
      amount: 5000,
      currency: 'NGN',
      email: 'buyer@example.com',
      first_name: 'Ada',
      last_name: 'Obi',
      tx_ref: 'ref-1',
      redirect_url: 'https://shop.example.com/callback',
      meta: { orderId: 'ord-1' },
      payment_options: 'card,banktransfer,ussd',
    });
    expect(result).toEqual({ id: 42, link: 'https://checkout.flw', status: 'success', mock: false });
  });

  it('defaults meta to an empty object and never marks a live call as mock', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { id: 7, mock: true } }));

    const result = await svc.initializeTransaction({
      amount: 1,
      currency: 'USD',
      email: 'a@b.co',
      txRef: 'r',
    });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body).meta).toEqual({});
    // The gateway echoing mock:true must not turn a real call into a mock one.
    expect(result.mock).toBe(false);
  });

  it('surfaces the gateway error body when initialization fails', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('{"message":"Invalid currency"}'));

    await expect(
      svc.initializeTransaction({ amount: 10, currency: 'NGN', email: 'a@b.co', txRef: 'r' }),
    ).rejects.toThrow(/Flutterwave initialize failed: .*Invalid currency/);
  });
});

describe('flutterwave service - verifyTransaction', () => {
  it('reports a pending (never successful) status when the gateway is disabled', async () => {
    const svc = await loadService({ config: { enabled: false } });

    await expect(svc.verifyTransaction({ txRef: 'ref-1' })).resolves.toEqual({
      status: 'pending',
      chargecode: '',
      mock: true,
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('verifies by transaction id when one is supplied', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { status: 'successful', amount: 5000 } }));

    const result = await svc.verifyTransaction({ txRef: 'ref-1', transactionId: '9911' });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.flutterwave.com/v3/transactions/9911/verify');
    expect(init.method).toBe('GET');
    expect(init.headers).toEqual({ Authorization: 'Bearer flw-secret-test' });
    expect(result).toEqual({ status: 'successful', amount: 5000, mock: false });
  });

  it('falls back to the tx_ref query string when no transaction id is given', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { status: 'successful' } }));

    await svc.verifyTransaction({ txRef: 'ref-42' });

    expect(global.fetch.mock.calls[0][0]).toBe(
      'https://api.flutterwave.com/v3/transactions/verify?reference=ref-42',
    );
  });

  it('leaves the gateway verdict untouched instead of coercing it to success', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { status: 'failed', chargecode: '99' } }));

    const result = await svc.verifyTransaction({ txRef: 'ref-1' });

    expect(result.status).toBe('failed');
    expect(result.mock).toBe(false);
  });

  it('propagates verification failures with the gateway text', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('transaction not found', 404));

    await expect(svc.verifyTransaction({ txRef: 'missing' })).rejects.toThrow(
      /Flutterwave verify failed: transaction not found/,
    );
  });
});

describe('flutterwave service - refund', () => {
  it('returns a mock refund reference without a network call when disabled', async () => {
    const svc = await loadService({ config: { enabled: false } });

    const result = await svc.refund({ transactionId: '9911', amount: 2500 });

    expect(result.mock).toBe(true);
    expect(result.id).toMatch(/^flw_ref_mock_\d+$/);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('posts the narration, transaction id and amount to /refunds', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { id: 7, status: 'success' } }));

    const result = await svc.refund({ transactionId: '9911', amount: 2500 });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.flutterwave.com/v3/refunds');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer flw-secret-test');
    expect(JSON.parse(init.body)).toEqual({
      narration: 'Customer requested refund',
      id: '9911',
      amount: 2500,
    });
    expect(result).toEqual({ id: 7, status: 'success', mock: false });
  });

  it('omits the amount from the payload when it is undefined (full refund)', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ data: { id: 8 } }));

    await svc.refund({ transactionId: '9911' });

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body).not.toHaveProperty('amount');
    expect(body.id).toBe('9911');
  });

  it('surfaces refund failures', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('{"message":"Refund not allowed"}'));

    await expect(svc.refund({ transactionId: '1', amount: 10 })).rejects.toThrow(
      /Flutterwave refund failed: .*Refund not allowed/,
    );
  });
});

describe('flutterwave service - webhooks', () => {
  it('accepts a matching verif-hash and dispatches known event types', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    // handleWebhook is synchronous and returns its verdict directly.
    expect(
      svc.handleWebhook({ event: 'charge.success', data: { id: 'tx-1' } }, WEBHOOK_HASH),
    ).toEqual({ valid: true });
    expect(
      svc.handleWebhook({ event: 'charge.failed', data: { id: 'tx-2' } }, WEBHOOK_HASH),
    ).toEqual({ valid: true });
    expect(svc.handleWebhook({ event: 'transfer.completed' }, WEBHOOK_HASH)).toEqual({
      valid: true,
    });

    expect(mockLogger.info).toHaveBeenCalledWith('Flutterwave charge success: tx-1');
    expect(mockLogger.info).toHaveBeenCalledWith('Flutterwave charge failed: tx-2');
    expect(mockLogger.info).toHaveBeenCalledWith('Unhandled Flutterwave webhook: transfer.completed');
    expect(mockLogger.warn).not.toHaveBeenCalled();
  });

  it('rejects and does not dispatch on a mismatched verif-hash', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    const result = await svc.handleWebhook(
      { event: 'charge.success', data: { id: 'tx-1' } },
      'forged-signature',
    );

    expect(result).toEqual({ valid: false });
    expect(mockLogger.warn).toHaveBeenCalledWith('Flutterwave webhook signature mismatch');
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('rejects an event with no verif-hash header at all', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(svc.handleWebhook({ event: 'charge.success', data: { id: 'tx-9' } })).toEqual({
      valid: false,
    });
    expect(mockLogger.warn).toHaveBeenCalledWith('Flutterwave webhook signature mismatch');
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('does not accept a body property that merely resembles the header', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(
      svc.handleWebhook({
        event: 'charge.success',
        data: { id: 'tx-10' },
        'verif-hash': WEBHOOK_HASH,
        signature: WEBHOOK_HASH,
      }),
    ).toEqual({ valid: false });
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('rejects a body-keyed HMAC even when it hashes only the event body', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    const body = { event: 'charge.success', data: { id: 'tx-11' } };
    const hmac = crypto.createHmac('sha256', WEBHOOK_HASH)
      .update(JSON.stringify(body))
      .digest('hex');

    expect(svc.handleWebhook(body, hmac)).toEqual({ valid: false });
    expect(mockLogger.warn).toHaveBeenCalledWith('Flutterwave webhook signature mismatch');
  });

  it('fails closed when FLUTTERWAVE_WEBHOOK_HASH is not configured', async () => {
    const svc = await loadService({ env: { FLUTTERWAVE_SECRET_KEY: 'flw-secret-test' } });

    expect(
      svc.handleWebhook({ event: 'charge.success', data: { id: 'tx-12' } }, WEBHOOK_HASH),
    ).toEqual({ valid: false });
    expect(mockLogger.warn).toHaveBeenCalledWith(
      'Flutterwave webhook rejected: FLUTTERWAVE_WEBHOOK_HASH is not configured',
    );
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('rejects a shorter/longer hash without throwing on the length mismatch', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(
      svc.handleWebhook({ event: 'charge.success', data: { id: 'tx-13' } }, `${WEBHOOK_HASH}x`),
    ).toEqual({ valid: false });
    expect(
      svc.handleWebhook({ event: 'charge.success', data: { id: 'tx-14' } }, WEBHOOK_HASH.slice(0, 4)),
    ).toEqual({ valid: false });
  });
});
