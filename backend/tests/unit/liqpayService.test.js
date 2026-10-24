import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * LiqPay service tests.
 *
 * LiqPay API v3 signatures are `base64(sha1(privateKey + data + privateKey))`
 * where `data` is the BASE64 payload string (never the decoded JSON). Both
 * outgoing forms and incoming callbacks sign/verify the base64 string.
 * The singleton is rebuilt per scenario because `enabled` is derived from
 * `getGatewayConfig('liqpay')` at import time.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const originalFetch = global.fetch;
const ENV_KEYS = ['LIQPAY_PUBLIC_KEY', 'LIQPAY_PRIVATE_KEY'];
const originalEnv = Object.fromEntries(ENV_KEYS.map((key) => [key, process.env[key]]));

const PRIVATE_KEY = 'priv_test_key';
const ENABLED_ENV = { LIQPAY_PUBLIC_KEY: 'pub_test_key', LIQPAY_PRIVATE_KEY: PRIVATE_KEY };

const sign = (data, privateKey = PRIVATE_KEY) =>
  crypto.createHash('sha1').update(`${privateKey}${data}${privateKey}`).digest('base64');

const b64 = (text) => Buffer.from(text).toString('base64');
const unb64 = (text) => Buffer.from(text, 'base64').toString('utf8');

async function loadService(env = {}) {
  for (const key of ENV_KEYS) delete process.env[key];
  Object.assign(process.env, env);
  jest.resetModules();
  const mod = await import('../../services/payment/liqpay.service.js');
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

describe('LiqPayService — configuration', () => {
  it('is disabled when LIQPAY_PUBLIC_KEY is missing', async () => {
    const service = await loadService();
    expect(service.enabled).toBe(false);
  });

  it('stays disabled for placeholder credentials containing "your_"', async () => {
    const service = await loadService({ LIQPAY_PUBLIC_KEY: 'your_liqpay_public_key' });
    expect(service.enabled).toBe(false);
  });

  it('is enabled once a real-looking key pair is present', async () => {
    const service = await loadService(ENABLED_ENV);
    expect(service.enabled).toBe(true);
    expect(service.publicKey).toBe('pub_test_key');
  });

  it('exposes the gateway metadata consumed by the checkout UI', async () => {
    const service = await loadService();
    expect(service.name).toBe('LiqPay');
    expect(service.baseURL).toBe('https://www.liqpay.ua/api/3');
    expect(service.supportedCurrencies).toEqual(['uah', 'usd', 'eur']);
  });

  it('returns the public key fallback when the env key is absent', async () => {
    const service = await loadService();
    expect(service.getPublicKey()).toBe('gcb_your_public_key');
  });
});

describe('LiqPayService — mock mode (gateway disabled)', () => {
  it('returns a stub payment form without signing or network access', async () => {
    const service = await loadService();
    global.fetch = jest.fn();

    const form = await service.createPaymentForm({ amount: 100, orderId: 'order-1' });

    expect(form).toEqual({
      publicKey: 'gcb_public_key',
      action: 'https://www.liqpay.ua/api/3/checkout',
      data: '',
      sign: '',
      mock: true,
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('returns a signed refund action without calling the gateway', async () => {
    const service = await loadService({ LIQPAY_PRIVATE_KEY: PRIVATE_KEY });
    global.fetch = jest.fn();

    const result = await service.refund({ orderId: 'order-1', amount: 100, currency: 'USD' });

    expect(result.mock).toBe(true);
    // SHA-1 digest (20 bytes) base64-encodes to 28 characters.
    expect(result.sign).toMatch(/^[A-Za-z0-9+/]{27}=$/);
    expect(result).not.toHaveProperty('data');
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

describe('LiqPayService — createPaymentForm (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('base64-encodes the v3 payload and signs the base64 data string', async () => {
    const form = await service.createPaymentForm({
      amount: 1500,
      currency: 'USD',
      orderId: 'order-42',
      description: 'Pro plan',
      productName: 'LumicorePro',
      serverUrl: 'https://shop.example.com/liqpay/callback',
    });

    const rawJson = unb64(form.data);
    expect(JSON.parse(rawJson)).toEqual({
      version: '3',
      public_key: 'pub_test_key',
      action: 'pay',
      amount: 1500,
      currency_code: 'USD',
      order_id: 'order-42',
      description: 'Pro plan',
      product_name: 'LumicorePro',
      server_url: 'https://shop.example.com/liqpay/callback',
    });
    // LiqPay signs the base64 `data` value, not the decoded JSON.
    expect(form.sign).toBe(sign(form.data));
    expect(form.sign).not.toBe(sign(rawJson));
    expect(form).toMatchObject({
      publicKey: 'pub_test_key',
      action: 'https://www.liqpay.ua/api/3/checkout',
      mock: false,
    });
  });

  it('defaults the currency code to UAH when none is supplied', async () => {
    const form = await service.createPaymentForm({ amount: 250, orderId: 'order-43' });

    expect(JSON.parse(unb64(form.data)).currency_code).toBe('UAH');
  });

  it('produces a different signature for a different private key', async () => {
    const form = await service.createPaymentForm({ amount: 10, orderId: 'order-44' });

    expect(form.sign).toBe(sign(form.data, PRIVATE_KEY));
    expect(form.sign).not.toBe(sign(form.data, 'another_key'));
  });
});

describe('LiqPayService — refund (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('posts a signed refund action as form data and parses the JSON reply', async () => {
    global.fetch = jest.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ status: 'success', action: 'refund', amount: 100 }),
    }));

    const result = await service.refund({ orderId: 'order-42', amount: 100, currency: 'USD' });

    const [url, init] = global.fetch.mock.calls[0];
    // Server API v3 endpoint — refunds must not hit the checkout page URL.
    expect(url).toBe('https://www.liqpay.ua/api/3/request');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/x-www-form-urlencoded');

    const params = new URLSearchParams(init.body);
    const dataB64 = params.get('data');
    expect(JSON.parse(unb64(dataB64))).toEqual({
      version: '3',
      public_key: 'pub_test_key',
      action: 'refund',
      order_id: 'order-42',
      amount: 100,
      currency_code: 'USD',
    });
    // Signature is computed over the URL-encoded base64 `data` value.
    expect(params.get('sign')).toBe(sign(dataB64));
    expect(result).toEqual({ status: 'success', action: 'refund', amount: 100 });
  });

  it('defaults the refund currency to UAH', async () => {
    global.fetch = jest.fn(async () => ({ ok: true, text: async () => '{"status":"success"}' }));

    await service.refund({ orderId: 'order-45', amount: 75 });

    const params = new URLSearchParams(global.fetch.mock.calls[0][1].body);
    expect(JSON.parse(unb64(params.get('data'))).currency_code).toBe('UAH');
  });

  it('throws with the gateway body when the refund request fails', async () => {
    global.fetch = jest.fn(async () => ({ ok: false, status: 500, text: async () => 'gateway down' }));

    await expect(service.refund({ orderId: 'order-42', amount: 100 })).rejects.toThrow(
      'LiqPay refund failed: gateway down'
    );
  });
});

describe('LiqPayService — handleCallback', () => {
  let service;
  const payload = {
    version: '3',
    public_key: 'pub_test_key',
    order_id: 'order-42',
    status: 'success',
    amount: 1500,
  };
  const rawJson = JSON.stringify(payload);
  const dataB64 = b64(rawJson);

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('returns the decoded payload for a signature over the base64 data param', async () => {
    const result = await service.handleCallback({ data: dataB64, sign: sign(dataB64) });

    expect(result).toEqual(payload);
    expect(mockLogger.info).toHaveBeenCalledWith(
      'LiqPay callback: order=order-42, status=success'
    );
  });

  it('rejects a signature made with a different private key', async () => {
    const result = await service.handleCallback({
      data: dataB64,
      sign: sign(dataB64, 'attacker_key'),
    });

    expect(result).toEqual({ error: 'Invalid signature' });
    expect(mockLogger.warn).toHaveBeenCalledWith('LiqPay callback signature mismatch');
  });

  it('rejects a signature taken from a different payload', async () => {
    const tampered = b64(JSON.stringify({ ...payload, amount: 1 }));

    await expect(
      service.handleCallback({ data: tampered, sign: sign(dataB64) })
    ).resolves.toEqual({ error: 'Invalid signature' });
  });

  it('rejects the pre-fix signature computed over the decoded JSON', async () => {
    // Regression guard: signing the decoded JSON (SHA-1 or SHA-256) is wrong —
    // LiqPay signs the base64 string that travels in `data`.
    const result = await service.handleCallback({ data: dataB64, sign: sign(rawJson) });

    expect(result).toEqual({ error: 'Invalid signature' });
  });

  it('rejects a signature of the wrong length without throwing', async () => {
    await expect(
      service.handleCallback({ data: dataB64, sign: 'short' })
    ).resolves.toEqual({ error: 'Invalid signature' });
  });

  it('rejects callbacks without data or sign', async () => {
    await expect(service.handleCallback({})).resolves.toEqual({
      error: 'Missing data or signature',
    });
    await expect(service.handleCallback({ data: dataB64 })).resolves.toEqual({
      error: 'Missing data or signature',
    });
    await expect(service.handleCallback({ sign: sign(dataB64) })).resolves.toEqual({
      error: 'Missing data or signature',
    });
    await expect(service.handleCallback(undefined)).resolves.toEqual({
      error: 'Missing data or signature',
    });
  });

  it('rejects correctly signed data whose JSON payload is malformed', async () => {
    const badData = b64('not-json');

    await expect(
      service.handleCallback({ data: badData, sign: sign(badData) })
    ).resolves.toEqual({ error: 'Invalid payload' });
  });
});
