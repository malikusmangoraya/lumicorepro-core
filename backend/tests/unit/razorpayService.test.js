import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Razorpay gateway service tests.
 *
 * razorpay.service.js exports a singleton built at import time from process.env
 * and talks to the REST API through global fetch, so each scenario stubs fetch
 * and re-imports the service with the desired credentials. No real network.
 */

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  http: jest.fn(),
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
}));

const originalFetch = global.fetch;
const ENV_KEYS = ['RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'RAZORPAY_WEBHOOK_SECRET'];
let savedEnv;
let mockFetch;

const jsonResponse = (body, ok = true) => ({
  ok,
  status: ok ? 200 : 400,
  json: async () => body,
  text: async () => (typeof body === 'string' ? body : JSON.stringify(body)),
});

async function loadRazorpay({ keyId, keySecret = 'rzp_test_secret' } = {}) {
  if (keyId) process.env.RAZORPAY_KEY_ID = keyId;
  else delete process.env.RAZORPAY_KEY_ID;
  if (keySecret) process.env.RAZORPAY_KEY_SECRET = keySecret;
  else delete process.env.RAZORPAY_KEY_SECRET;
  jest.resetModules();
  const mod = await import('../../services/payment/razorpay.service.js');
  return mod.default;
}

function sign(orderId, paymentId, secret) {
  return crypto
    .createHmac('sha256', secret)
    .update(`${orderId}|${paymentId}`)
    .digest('hex');
}

const WEBHOOK_SECRET = 'whsec_razorpay_test';
const signWebhook = (rawBody, secret = WEBHOOK_SECRET) =>
  crypto.createHmac('sha256', secret).update(rawBody).digest('hex');

async function loadWithWebhookSecret(secret = WEBHOOK_SECRET, keyId = 'rzp_test_key') {
  if (secret) process.env.RAZORPAY_WEBHOOK_SECRET = secret;
  else delete process.env.RAZORPAY_WEBHOOK_SECRET;
  return loadRazorpay({ keyId });
}

beforeEach(() => {
  savedEnv = {};
  for (const key of ENV_KEYS) {
    savedEnv[key] = process.env[key];
    delete process.env[key];
  }
  jest.clearAllMocks();
  mockFetch = jest.fn();
  global.fetch = mockFetch;
});

afterEach(() => {
  global.fetch = originalFetch;
  for (const key of ENV_KEYS) {
    if (savedEnv[key] === undefined) delete process.env[key];
    else process.env[key] = savedEnv[key];
  }
});

describe('configuration', () => {
  it('is disabled without a key id', async () => {
    const svc = await loadRazorpay();

    expect(svc.enabled).toBe(false);
    expect(svc.keyId).toBeUndefined();
  });

  it('treats the .env.example "your_" placeholder as unconfigured', async () => {
    const svc = await loadRazorpay({ keyId: 'your_razorpay_key_id' });

    expect(svc.enabled).toBe(false);
  });

  it('enables the gateway when a real key id is present', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });

    expect(svc.enabled).toBe(true);
    expect(svc.keySecret).toBe('rzp_test_secret');
  });

  it('exposes India-only gateway metadata', async () => {
    const svc = await loadRazorpay();

    expect(svc.name).toBe('Razorpay');
    expect(svc.region).toBe('India');
    expect(svc.supportedCurrencies).toEqual(['inr']);
    expect(svc.baseURL).toBe('https://api.razorpay.com');
  });
});

describe('createOrder', () => {
  it('returns a mock order in paise without touching the network', async () => {
    const svc = await loadRazorpay();

    const result = await svc.createOrder({ amount: 49.99, receipt: 'rcpt_1' });

    expect(result.id).toMatch(/^rzp_mock_\d+$/);
    expect(result.amount).toBe(4999);
    expect(result.currency).toBe('INR');
    expect(result.mock).toBe(true);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('posts the order in the smallest unit with basic auth when enabled', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse({ id: 'order_1', status: 'created' }));

    const result = await svc.createOrder({
      amount: 49.99,
      receipt: 'rcpt_1',
      notes: { orderId: 'o1' },
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.razorpay.com/v1/orders');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    const expectedAuth = Buffer.from('rzp_test_key:rzp_test_secret').toString('base64');
    expect(init.headers.Authorization).toBe(`Basic ${expectedAuth}`);
    expect(JSON.parse(init.body)).toEqual({
      amount: 4999,
      currency: 'INR',
      receipt: 'rcpt_1',
      notes: { orderId: 'o1' },
    });
    expect(result).toEqual({ id: 'order_1', status: 'created', mock: false });
  });

  it('defaults notes to an empty object', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse({ id: 'order_1' }));

    await svc.createOrder({ amount: 1 });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.notes).toEqual({});
  });

  it('throws with the gateway body when the order request fails', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse('{"error":"bad credentials"}', false));

    await expect(svc.createOrder({ amount: 10 })).rejects.toThrow(
      'Razorpay create order failed: {"error":"bad credentials"}',
    );
  });

  it('propagates transport failures', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockRejectedValue(new Error('ECONNRESET'));

    await expect(svc.createOrder({ amount: 10 })).rejects.toThrow('ECONNRESET');
  });
});

describe('verifyPayment', () => {
  it('accepts a signature produced with the key secret', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });

    const signature = sign('order_1', 'pay_1', 'rzp_test_secret');

    await expect(
      svc.verifyPayment({ orderId: 'order_1', paymentId: 'pay_1', signature }),
    ).resolves.toBe(true);
  });

  it('rejects a tampered signature', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    const signature = sign('order_1', 'pay_1', 'rzp_test_secret');

    await expect(
      svc.verifyPayment({ orderId: 'order_1', paymentId: 'pay_1', signature: `${signature}0` }),
    ).resolves.toBe(false);
  });

  it('binds the signature to order and payment id order', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    const swapped = sign('pay_1', 'order_1', 'rzp_test_secret');

    await expect(
      svc.verifyPayment({ orderId: 'order_1', paymentId: 'pay_1', signature: swapped }),
    ).resolves.toBe(false);
  });

  it('rejects a missing signature', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });

    await expect(
      svc.verifyPayment({ orderId: 'order_1', paymentId: 'pay_1' }),
    ).resolves.toBe(false);
  });
});

describe('refund', () => {
  it('returns a mock refundId (not an orderId) when disabled', async () => {
    const svc = await loadRazorpay();

    const result = await svc.refund({ paymentId: 'pay_1', amount: 10 });

    expect(result.success).toBe(true);
    expect(result.mock).toBe(true);
    expect(result.refundId).toMatch(/^ref_mock_\d+$/);
    expect(result).not.toHaveProperty('orderId');
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('posts the refund in paise and returns the refund id', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse({ id: 'rfnd_1', status: 'processed' }));

    const result = await svc.refund({ paymentId: 'pay_1', amount: 12.34 });

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.razorpay.com/v1/payments/pay_1/refund');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ payment_id: 'pay_1', amount: 1234 });
    expect(result).toEqual({ success: true, refundId: 'rfnd_1' });
  });

  it('omits the amount for a full refund', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse({ id: 'rfnd_1' }));

    await svc.refund({ paymentId: 'pay_1' });

    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual({ payment_id: 'pay_1' });
  });

  it('throws with the gateway body when the refund fails', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });
    mockFetch.mockResolvedValue(jsonResponse('{"error":"payment not captured"}', false));

    await expect(svc.refund({ paymentId: 'pay_1' })).rejects.toThrow(
      'Razorpay refund failed: {"error":"payment not captured"}',
    );
  });
});

describe('verifyWebhook', () => {
  it('accepts an HMAC-SHA256 of the raw body computed with the webhook secret', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = '{"event":"payment.captured"}';

    expect(svc.verifyWebhook(rawBody, signWebhook(rawBody))).toBe(true);
  });

  it('rejects a signature for a different body (raw body must be signed verbatim)', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = '{"event":"payment.captured"}';

    expect(svc.verifyWebhook(`${rawBody} `, signWebhook(rawBody))).toBe(false);
    expect(svc.verifyWebhook(rawBody, signWebhook('{"event":"payment.failed"}'))).toBe(false);
  });

  it('rejects a signature made with the wrong secret', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = '{"event":"payment.captured"}';

    expect(svc.verifyWebhook(rawBody, signWebhook(rawBody, 'attacker_secret'))).toBe(false);
  });

  it('rejects missing body or signature', async () => {
    const svc = await loadWithWebhookSecret();

    expect(svc.verifyWebhook('', signWebhook(''))).toBe(false);
    expect(svc.verifyWebhook('{"a":1}', '')).toBe(false);
    expect(svc.verifyWebhook('{"a":1}', undefined)).toBe(false);
  });

  it('fails closed when RAZORPAY_WEBHOOK_SECRET is not configured', async () => {
    const svc = await loadWithWebhookSecret(null);
    const rawBody = '{"event":"payment.captured"}';

    expect(svc.verifyWebhook(rawBody, signWebhook(rawBody, ''))).toBe(false);
    expect(mockLogger.warn).toHaveBeenCalledWith(
      'Razorpay webhook rejected: RAZORPAY_WEBHOOK_SECRET is not configured',
    );
  });

  it('rejects a short/garbage signature without throwing on the length mismatch', async () => {
    const svc = await loadWithWebhookSecret();

    expect(() => svc.verifyWebhook('{"a":1}', 'deadbeef')).not.toThrow();
    expect(svc.verifyWebhook('{"a":1}', 'deadbeef')).toBe(false);
  });
});

describe('handleWebhook', () => {
  const paymentEntity = (id) => ({ payload: { payment: { entity: { id } } } });
  const event = (name, id) => ({ event: name, ...paymentEntity(id) });

  it('verifies the signature and logs a captured payment', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = JSON.stringify(event('payment.captured', 'pay_1'));

    await expect(
      svc.handleWebhook(JSON.parse(rawBody), signWebhook(rawBody), rawBody),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith('Razorpay payment captured: pay_1');
  });

  it('logs a failed payment', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = JSON.stringify(event('payment.failed', 'pay_2'));

    await expect(
      svc.handleWebhook(JSON.parse(rawBody), signWebhook(rawBody), rawBody),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith('Razorpay payment failed: pay_2');
  });

  it('logs unhandled event types without throwing', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = JSON.stringify({ event: 'subscription.activated', payload: {} });

    await expect(
      svc.handleWebhook(JSON.parse(rawBody), signWebhook(rawBody), rawBody),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith(
      'Unhandled Razorpay webhook: subscription.activated',
    );
  });

  it('rejects forged events without dispatching them', async () => {
    const svc = await loadWithWebhookSecret();
    const rawBody = JSON.stringify(event('payment.captured', 'pay_forged'));

    await expect(
      svc.handleWebhook(JSON.parse(rawBody), 'forged-signature', rawBody),
    ).resolves.toEqual({ valid: false });

    expect(mockLogger.warn).toHaveBeenCalledWith('Razorpay webhook signature mismatch');
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('rejects events when no signature or raw body is supplied', async () => {
    const svc = await loadWithWebhookSecret();

    await expect(svc.handleWebhook(event('payment.captured', 'pay_3'))).resolves.toEqual({
      valid: false,
    });
    await expect(
      svc.handleWebhook(event('payment.captured', 'pay_4'), signWebhook('x')),
    ).resolves.toEqual({ valid: false });
  });

  it('fails closed when the webhook secret is missing', async () => {
    const svc = await loadWithWebhookSecret(null);
    const rawBody = JSON.stringify(event('payment.captured', 'pay_5'));

    await expect(
      svc.handleWebhook(JSON.parse(rawBody), signWebhook(rawBody, ''), rawBody),
    ).resolves.toEqual({ valid: false });
    expect(mockLogger.info).not.toHaveBeenCalled();
  });
});

describe('getKeyId', () => {
  it('returns the configured key id', async () => {
    const svc = await loadRazorpay({ keyId: 'rzp_test_key' });

    expect(svc.getKeyId()).toBe('rzp_test_key');
  });

  it('falls back to a test placeholder when unset', async () => {
    const svc = await loadRazorpay();

    expect(svc.getKeyId()).toBe('rzp_test_placeholder');
  });
});
