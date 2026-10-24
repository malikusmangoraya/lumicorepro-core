import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Paddle service tests.
 *
 * Covers the mock (unconfigured) branch, the live Billing API payloads
 * (including minor-unit amount conversion), webhook HMAC verification and
 * refunds. `fetch` is always mocked and the webhook signatures are produced
 * with the real `node:crypto` implementation.
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

const originalFetch = global.fetch;
const ENV_KEYS = ['PADDLE_API_KEY', 'PADDLE_WEBHOOK_SECRET', 'PADDLE_ENV'];
const originalEnv = Object.fromEntries(ENV_KEYS.map((key) => [key, process.env[key]]));

const WEBHOOK_SECRET = 'pdl_ntfset_test_secret';
const ENABLED_ENV = {
  PADDLE_API_KEY: 'pdl_sandbox_apikey',
  PADDLE_WEBHOOK_SECRET: WEBHOOK_SECRET,
  PADDLE_ENV: 'sandbox',
};

const ok = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const fail = (message) => ({
  ok: false,
  status: 422,
  json: async () => ({ error: message }),
  text: async () => message,
});

const hmac = (ts, body, secret = WEBHOOK_SECRET) =>
  crypto.createHmac('sha256', secret).update(`${ts}:${body}`).digest('base64');

async function loadService(env = {}) {
  for (const key of ENV_KEYS) delete process.env[key];
  Object.assign(process.env, env);
  jest.resetModules();
  const mod = await import('../../services/payment/paddle.service.js');
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

describe('PaddleService — configuration', () => {
  it('is disabled when PADDLE_API_KEY is missing', async () => {
    const service = await loadService();
    expect(service.enabled).toBe(false);
  });

  it('stays disabled for placeholder credentials containing "your_"', async () => {
    const service = await loadService({ PADDLE_API_KEY: 'your_paddle_api_key' });
    expect(service.enabled).toBe(false);
  });

  it('is enabled once a real-looking key is present', async () => {
    const service = await loadService(ENABLED_ENV);
    expect(service.enabled).toBe(true);
    expect(service.apiKey).toBe('pdl_sandbox_apikey');
  });

  it('points at the sandbox API only when PADDLE_ENV=sandbox', async () => {
    const sandbox = await loadService({ ...ENABLED_ENV, PADDLE_ENV: 'sandbox' });
    expect(sandbox.baseURL).toBe('https://sandbox-api.paddle.com');

    const live = await loadService({ ...ENABLED_ENV, PADDLE_ENV: 'production' });
    expect(live.baseURL).toBe('https://api.paddle.com');
  });

  it('exposes the gateway metadata consumed by the checkout UI', async () => {
    const service = await loadService();
    expect(service.name).toBe('Paddle');
    expect(service.region).toBe('Global');
    expect(service.supportedCurrencies).toEqual(
      expect.arrayContaining(['usd', 'eur', 'gbp', 'jpy'])
    );
  });
});

describe('PaddleService — mock mode (gateway disabled)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService();
    global.fetch = jest.fn();
  });

  it('returns a demo checkout URL keyed by the order id', async () => {
    const result = await service.createCheckout({
      amount: 49.99,
      currency: 'eur',
      orderId: 'order-77',
    });

    expect(result).toEqual({
      id: expect.stringMatching(/^paddle_mock_\d+$/),
      checkoutUrl: 'https://demo.paddle.com/checkout/mock/order-77',
      amount: 49.99,
      currency: 'eur',
      mock: true,
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('falls back to the generated id when no order id is supplied and defaults to usd', async () => {
    const result = await service.createCheckout({ amount: 10 });

    expect(result.currency).toBe('usd');
    expect(result.checkoutUrl).toBe(`https://demo.paddle.com/checkout/mock/${result.id}`);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('short-circuits refunds', async () => {
    await expect(
      service.refund({ transactionId: 'txn_1', amount: 10 })
    ).resolves.toEqual({ success: true, mock: true, transactionId: 'txn_1' });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

describe('PaddleService — createCheckout (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('posts a Billing transaction with amounts in minor units', async () => {
    global.fetch = jest.fn(async () =>
      ok({ data: { id: 'txn_1', checkout: { url: 'https://pay.paddle.io/txn_1' } } })
    );

    const result = await service.createCheckout({
      amount: 49.99,
      currency: 'usd',
      orderId: 'order-77',
      description: 'LumicorePro Pro plan',
      customerEmail: 'buyer@example.com',
      successUrl: 'https://shop.example.com/thank-you',
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://sandbox-api.paddle.com/transactions');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer pdl_sandbox_apikey');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(init.headers['Paddle-Idempotency-Key']).toBe('LU-order-77');
    expect(init.headers).not.toHaveProperty('X-Transaction-Id');
    expect(JSON.parse(init.body)).toEqual({
      items: [
        {
          quantity: 1,
          price: { unit_price: { amount: '4999', currency_code: 'USD' } },
          custom_data: { orderId: 'order-77' },
        },
      ],
      custom_data: { orderId: 'order-77' },
      description: 'LumicorePro Pro plan',
      customer_email: 'buyer@example.com',
      success_url: 'https://shop.example.com/thank-you',
    });
    expect(result).toEqual({
      id: 'txn_1',
      checkoutUrl: 'https://pay.paddle.io/txn_1',
      amount: 49.99,
      currency: 'usd',
      mock: false,
    });
  });

  it('reads the hosted checkout URL from data.checkout.url', async () => {
    global.fetch = jest.fn(async () =>
      ok({
        data: {
          id: 'txn_checkout',
          checkout: { url: 'https://pay.paddle.io/checkout/txn_checkout' },
          // Legacy/nonexistent shape must not be used as a fallback.
          urls: { checkout: 'https://wrong.example.com' },
        },
      })
    );

    const result = await service.createCheckout({ amount: 5, orderId: 'order-81' });

    expect(result.checkoutUrl).toBe('https://pay.paddle.io/checkout/txn_checkout');
  });

  it('does not multiply zero-decimal currencies by 100', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_jpy', checkout: { url: 'u' } } }));

    await service.createCheckout({ amount: 1500, currency: 'jpy', orderId: 'order-jpy' });

    const unitPrice = JSON.parse(global.fetch.mock.calls[0][1].body).items[0].price.unit_price;
    expect(unitPrice).toEqual({ amount: '1500', currency_code: 'JPY' });
  });

  it('rounds fractional cents instead of truncating them', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_2', checkout: { url: 'u' } } }));

    await service.createCheckout({ amount: 19.999, currency: 'eur', orderId: 'order-78' });

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.items[0].price.unit_price.amount).toBe('2000');
    expect(body.items[0].price.unit_price.currency_code).toBe('EUR');
  });

  it('handles floating point noise in the amount (0.1 + 0.2)', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_3', checkout: { url: 'u' } } }));

    await service.createCheckout({ amount: 0.1 + 0.2, orderId: 'order-79' });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body).items[0].price.unit_price.amount).toBe(
      '30'
    );
  });

  it('coerces numeric order ids to strings and applies defaults', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_4', checkout: { url: 'u' } } }));

    await service.createCheckout({ amount: 5, orderId: 1001 });

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.custom_data.orderId).toBe('1001');
    expect(body.items[0].custom_data.orderId).toBe('1001');
    expect(body.description).toBe('LumicorePro order');
    expect(body).not.toHaveProperty('customer_email');
    expect(body).not.toHaveProperty('success_url');
    expect(global.fetch.mock.calls[0][1].headers['Paddle-Idempotency-Key']).toBe('LU-1001');
  });

  it('works without an order id (timestamp-based idempotency header)', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_5', checkout: { url: 'u' } } }));

    await service.createCheckout({ amount: 5 });

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.custom_data.orderId).toBe('');
    expect(global.fetch.mock.calls[0][1].headers['Paddle-Idempotency-Key']).toMatch(
      /^LU-\d{13,}$/
    );
  });

  it('returns an empty checkout URL when Paddle omits it', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'txn_6' } }));

    const result = await service.createCheckout({ amount: 5, orderId: 'order-80' });

    expect(result).toMatchObject({ id: 'txn_6', checkoutUrl: '', mock: false });
  });

  it('returns an empty checkout URL when the payload has no data object', async () => {
    global.fetch = jest.fn(async () => ok({}));

    await expect(service.createCheckout({ amount: 5 })).resolves.toMatchObject({
      id: undefined,
      checkoutUrl: '',
      mock: false,
    });
  });

  it('treats an unspecified currency as USD and handles zero-decimal case-insensitively', () => {
    // Paddle amounts are serialised as strings of minor units.
    expect(service._toMinorUnits(10)).toBe('1000');
    expect(service._toMinorUnits(10, 'JPY')).toBe('10');
    expect(service._toMinorUnits(10, 'Krw')).toBe('10');
    expect(service._toMinorUnits(10, 'EUR')).toBe('1000');
  });

  it('throws with the gateway body when transaction creation fails', async () => {
    global.fetch = jest.fn(async () => fail('currency_code not supported'));

    await expect(service.createCheckout({ amount: 5, currency: 'xyz' })).rejects.toThrow(
      'Paddle create checkout failed: currency_code not supported'
    );
  });
});

describe('PaddleService — refund (live)', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('posts a full-refund adjustment and returns the adjustment id', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 'adj_1', status: 'approved' } }));

    const result = await service.refund({
      transactionId: 'txn_1',
      reason: 'requested_by_customer',
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://sandbox-api.paddle.com/adjustments');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer pdl_sandbox_apikey');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual({
      action: 'refund',
      transaction_id: 'txn_1',
      reason: 'requested_by_customer',
      items: [{ type: 'full' }],
    });
    expect(result).toEqual({ success: true, refundId: 'adj_1', transactionId: 'txn_1' });
  });

  it('applies a default reason for a full refund', async () => {
    global.fetch = jest.fn(async () => ok({ data: { id: 're_2' } }));

    const result = await service.refund({ transactionId: 'txn_2' });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({
      action: 'refund',
      transaction_id: 'txn_2',
      reason: 'Refund requested by customer',
      items: [{ type: 'full' }],
    });
    expect(result).toEqual({ success: true, refundId: 're_2', transactionId: 'txn_2' });
  });

  it('rejects partial refunds with an explicit full-refund-only error', async () => {
    global.fetch = jest.fn();

    await expect(
      service.refund({ transactionId: 'txn_3', amount: 5 })
    ).rejects.toThrow(/Paddle integration supports full refunds only/);
    await expect(service.refund({ transactionId: 'txn_3', amount: 0 })).rejects.toThrow(
      /full refunds only/
    );
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('throws with the gateway body when the refund fails', async () => {
    global.fetch = jest.fn(async () => fail('transaction not refundable'));

    await expect(service.refund({ transactionId: 'txn_3' })).rejects.toThrow(
      'Paddle refund failed: transaction not refundable'
    );
  });
});

describe('PaddleService — verifyWebhook', () => {
  const rawBody = JSON.stringify({ event_type: 'transaction.completed', data: { id: 'txn_1' } });
  const ts = '1700000000';
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('accepts a valid ts/h1 signature', () => {
    expect(service.verifyWebhook(rawBody, `ts=${ts};h1=${hmac(ts, rawBody)}`)).toBe(true);
  });

  it('accepts headers that carry extra signature parts', () => {
    const header = `ts=${ts};h1=${hmac(ts, rawBody)};v1=legacy`;
    expect(service.verifyWebhook(rawBody, header)).toBe(true);
  });

  it('rejects a tampered body', () => {
    const signature = hmac(ts, rawBody);
    const tampered = JSON.stringify({ event_type: 'transaction.completed', data: { id: 'txn_2' } });

    expect(service.verifyWebhook(tampered, `ts=${ts};h1=${signature}`)).toBe(false);
  });

  it('rejects a signature made with the wrong secret', () => {
    const header = `ts=${ts};h1=${hmac(ts, rawBody, 'attacker_secret')}`;
    expect(service.verifyWebhook(rawBody, header)).toBe(false);
  });

  it('rejects a signature computed over the wrong timestamp (replay guard)', () => {
    const header = `ts=${ts};h1=${hmac('1700000001', rawBody)}`;
    expect(service.verifyWebhook(rawBody, header)).toBe(false);
  });

  it('rejects short/garbage signatures without throwing on length mismatch', () => {
    expect(() => service.verifyWebhook(rawBody, `ts=${ts};h1=deadbeef`)).not.toThrow();
    expect(service.verifyWebhook(rawBody, `ts=${ts};h1=deadbeef`)).toBe(false);
  });

  it('rejects a header missing ts or h1', () => {
    expect(service.verifyWebhook(rawBody, `h1=${hmac(ts, rawBody)}`)).toBe(false);
    expect(service.verifyWebhook(rawBody, `ts=${ts}`)).toBe(false);
    expect(service.verifyWebhook(rawBody, undefined)).toBe(false);
    expect(service.verifyWebhook(rawBody, '')).toBe(false);
  });

  it('refuses every signature when no webhook secret is configured', async () => {
    const unconfigured = await loadService();
    expect(unconfigured.verifyWebhook(rawBody, `ts=${ts};h1=${hmac(ts, rawBody)}`)).toBe(false);
  });
});

describe('PaddleService — handleWebhook', () => {
  let service;

  beforeEach(async () => {
    service = await loadService(ENABLED_ENV);
  });

  it('returns and logs the event type', async () => {
    const type = await service.handleWebhook({
      event_type: 'transaction.completed',
      data: { id: 'txn_1' },
    });

    expect(type).toBe('transaction.completed');
    expect(mockLogger.info).toHaveBeenCalledWith('Paddle webhook: transaction.completed (txn_1)');
  });

  it('falls back to the legacy `type` field', async () => {
    await expect(
      service.handleWebhook({ type: 'subscription.created', data: { id: 'sub_1' } })
    ).resolves.toBe('subscription.created');
  });

  it('returns an empty string for an unknown payload instead of throwing', async () => {
    await expect(service.handleWebhook({})).resolves.toBe('');
    await expect(service.handleWebhook(undefined)).resolves.toBe('');
    expect(mockLogger.info).toHaveBeenCalledWith('Paddle webhook:  ()');
  });
});
