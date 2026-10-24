import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Square gateway service tests.
 *
 * square.service.js exports a singleton built at import time from process.env
 * and talks to Square's REST API through global fetch, so each scenario stubs
 * fetch and re-imports the service with the desired credentials. No real calls.
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
const ENV_KEYS = [
  'SQUARE_ACCESS_TOKEN',
  'SQUARE_LOCATION_ID',
  'SQUARE_ENVIRONMENT',
  'SQUARE_WEBHOOK_SIGNATURE_KEY',
];
let savedEnv;
let mockFetch;

const WEBHOOK_KEY = 'sq_webhook_signature_key';
const NOTIFICATION_URL = 'https://api.example.com/webhooks/square';

const jsonResponse = (body, ok = true) => ({
  ok,
  status: ok ? 200 : 400,
  json: async () => body,
  text: async () => (typeof body === 'string' ? body : JSON.stringify(body)),
});

async function loadSquare({
  accessToken,
  locationId = 'LOC_1',
  environment,
  signatureKey,
} = {}) {
  if (accessToken) process.env.SQUARE_ACCESS_TOKEN = accessToken;
  else delete process.env.SQUARE_ACCESS_TOKEN;
  if (locationId) process.env.SQUARE_LOCATION_ID = locationId;
  else delete process.env.SQUARE_LOCATION_ID;
  if (environment) process.env.SQUARE_ENVIRONMENT = environment;
  else delete process.env.SQUARE_ENVIRONMENT;
  if (signatureKey) process.env.SQUARE_WEBHOOK_SIGNATURE_KEY = signatureKey;
  else delete process.env.SQUARE_WEBHOOK_SIGNATURE_KEY;
  jest.resetModules();
  const mod = await import('../../services/payment/square.service.js');
  return mod.default;
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
  it('is disabled without an access token', async () => {
    const svc = await loadSquare();

    expect(svc.enabled).toBe(false);
    expect(svc.accessToken).toBeUndefined();
  });

  it('treats the .env.example "your_" placeholder as unconfigured', async () => {
    const svc = await loadSquare({ accessToken: 'your_square_access_token' });

    expect(svc.enabled).toBe(false);
  });

  it('enables the gateway and keeps the location id', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });

    expect(svc.enabled).toBe(true);
    expect(svc.locationId).toBe('LOC_1');
    expect(svc.name).toBe('Square');
    expect(svc.supportedCurrencies).toEqual(['usd', 'jpy', 'aud', 'gbp', 'cad']);
  });

  it('defaults to the sandbox base URL', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });

    expect(svc.environment).toBe('sandbox');
    expect(svc.baseURL).toBe('https://connect.squareupsandbox.com');
  });

  it('switches to the production base URL when SQUARE_ENVIRONMENT=production', async () => {
    const svc = await loadSquare({
      accessToken: 'sq_test_token',
      environment: 'production',
    });

    expect(svc.baseURL).toBe('https://connect.squareup.com');
  });
});

describe('createPayment', () => {
  it('returns a mock payment without touching the network when disabled', async () => {
    const svc = await loadSquare();

    const result = await svc.createPayment({ amount: 19.5, sourceId: 'cnon:card-nonce-ok' });

    expect(result.id).toMatch(/^sq_mock_\d+$/);
    expect(result).toEqual({ id: result.id, amount: 19.5, mock: true });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('charges the amount in minor units with a bearer token', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(
      jsonResponse({ payment: { id: 'pay_1', status: 'COMPLETED' } }),
    );

    const result = await svc.createPayment({ amount: 19.99, idempotencyKey: 'idem_1', sourceId: 'cnon:card-nonce-ok' });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toBe('https://connect.squareupsandbox.com/v2/payments');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(init.headers.Authorization).toBe('Bearer sq_test_token');
    expect(init.headers['Idempotency-Key']).toBe('idem_1');
    expect(JSON.parse(init.body)).toEqual({
      idempotency_key: 'idem_1',
      source_id: 'cnon:card-nonce-ok',
      amount_money: { amount: 1999, currency: 'USD' },
      location_id: 'LOC_1',
    });
    expect(result).toEqual({ id: 'pay_1', status: 'COMPLETED', mock: false });
  });

  it('generates an idempotency key when the caller omits one', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({ payment: { id: 'pay_1' } }));

    await svc.createPayment({ amount: 5, sourceId: 'cnon:card-nonce-ok' });

    const [, init] = mockFetch.mock.calls[0];
    const body = JSON.parse(init.body);
    expect(init.headers['Idempotency-Key']).toMatch(/^sq_\d+$/);
    expect(body.idempotency_key).toMatch(/^sq_\d+$/);
  });

  it('never lets a gateway payload mark the payment as a mock', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(
      jsonResponse({ payment: { id: 'pay_1', status: 'APPROVED', mock: true } }),
    );

    const result = await svc.createPayment({ amount: 5, idempotencyKey: 'idem_1', sourceId: 'cnon:card-nonce-ok' });

    expect(result).toEqual({ id: 'pay_1', status: 'APPROVED', mock: false });
  });

  it('settles in the caller currency, defaulting to usd', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token', environment: 'production' });
    mockFetch.mockResolvedValue(jsonResponse({ payment: { id: 'pay_1' } }));

    await svc.createPayment({ amount: 12.5, idempotencyKey: 'idem_1', sourceId: 'cnon:card-nonce-ok' });
    await svc.createPayment({
      amount: 12.5,
      idempotencyKey: 'idem_2',
      currency: 'GBP',
      sourceId: 'cnon:card-nonce-ok',
    });

    expect(JSON.parse(mockFetch.mock.calls[0][1].body).amount_money).toEqual({
      amount: 1250,
      currency: 'USD',
    });
    expect(JSON.parse(mockFetch.mock.calls[1][1].body).amount_money).toEqual({
      amount: 1250,
      currency: 'GBP',
    });
  });

  it('does not multiply zero-decimal JPY by 100', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({ payment: { id: 'pay_jpy' } }));

    await svc.createPayment({ amount: 1000, idempotencyKey: 'idem_jpy', currency: 'JPY', sourceId: 'cnon:card-nonce-ok' });

    expect(JSON.parse(mockFetch.mock.calls[0][1].body).amount_money).toEqual({
      amount: 1000,
      currency: 'JPY',
    });
  });

  it('refuses a live payment without a Web Payments SDK sourceId', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    await expect(svc.createPayment({ amount: 5 })).rejects.toThrow(/sourceId/);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('throws with the gateway body when the payment request fails', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse('{"errors":[{"code":"CARD_DECLINED"}]}', false));

    await expect(svc.createPayment({ amount: 5, sourceId: 'cnon:card-nonce-ok' })).rejects.toThrow(
      'Square create payment failed: {"errors":[{"code":"CARD_DECLINED"}]}',
    );
  });

  it('defaults the minor-unit conversion to usd when no currency is given', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });

    expect(svc._toMinorUnits(12.5)).toBe(1250);
    expect(svc._toMinorUnits(1000, 'jpy')).toBe(1000);
    expect(svc._toMinorUnits(12.5, 'gbp')).toBe(1250);
  });
});

describe('refund', () => {
  it('returns a mock refund when disabled', async () => {
    const svc = await loadSquare();

    await expect(svc.refund({ paymentId: 'pay_1', amount: 5 })).resolves.toEqual({
      success: true,
      mock: true,
      paymentId: 'pay_1',
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('creates the refund via /v2/refunds with payment_id and amount_money', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({ refund: { id: 'rfnd_1', status: 'COMPLETED' } }));

    const result = await svc.refund({ paymentId: 'pay_1', amount: 12.34 });

    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toBe('https://connect.squareupsandbox.com/v2/refunds');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer sq_test_token');
    expect(init.headers['Idempotency-Key']).toMatch(/^refund_pay_1_\d+$/);
    expect(JSON.parse(init.body)).toEqual({
      idempotency_key: expect.stringMatching(/^refund_pay_1_\d+$/),
      payment_id: 'pay_1',
      amount_money: { amount: 1234, currency: 'USD' },
    });
    expect(JSON.parse(init.body)).not.toHaveProperty('refund_money');
    expect(result).toEqual({ success: true, refundId: 'rfnd_1' });
  });

  it('sends amount 0 for a full refund', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({ refund: { id: 'rfnd_1' } }));

    await svc.refund({ paymentId: 'pay_1' });

    expect(JSON.parse(mockFetch.mock.calls[0][1].body).amount_money).toEqual({
      amount: 0,
      currency: 'USD',
    });
  });

  it('honours the currency and JPY zero-decimal rule on refunds', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({ refund: { id: 'rfnd_jpy' } }));

    await svc.refund({ paymentId: 'pay_jpy', amount: 500, currency: 'JPY' });

    expect(JSON.parse(mockFetch.mock.calls[0][1].body).amount_money).toEqual({
      amount: 500,
      currency: 'JPY',
    });
  });

  it('returns an undefined refund id when the payload has no refund object', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse({}));

    await expect(svc.refund({ paymentId: 'pay_1' })).resolves.toEqual({
      success: true,
      refundId: undefined,
    });
  });

  it('throws with the gateway body when the refund fails', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    mockFetch.mockResolvedValue(jsonResponse('{"errors":[{"code":"REFUND_FAILED"}]}', false));

    await expect(svc.refund({ paymentId: 'pay_1' })).rejects.toThrow(
      'Square refund failed: {"errors":[{"code":"REFUND_FAILED"}]}',
    );
  });
});

describe('handleWebhook', () => {
  const event = (type, id) => ({ type, data: { object: { payment: { id } } } });
  const rawBodyFor = (type, id) => JSON.stringify(event(type, id));
  const sign = (rawBody, notificationUrl = NOTIFICATION_URL, key = WEBHOOK_KEY) =>
    crypto.createHmac('sha256', key).update(`${notificationUrl}${rawBody}`).digest('base64');

  it('verifies the signature and logs payment.created', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const rawBody = rawBodyFor('payment.created', 'pay_1');

    await expect(
      svc.handleWebhook(event('payment.created', 'pay_1'), {
        signature: sign(rawBody),
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith('Square payment created: pay_1');
  });

  it('logs payment.updated with the id from data.object.payment', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const rawBody = rawBodyFor('payment.updated', 'pay_2');

    await expect(
      svc.handleWebhook(event('payment.updated', 'pay_2'), {
        signature: sign(rawBody),
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith('Square payment updated: pay_2');
  });

  it('logs unhandled event types without throwing', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const rawBody = rawBodyFor('refund.created', 'rfnd_1');

    await expect(
      svc.handleWebhook(event('refund.created', 'rfnd_1'), {
        signature: sign(rawBody),
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: true });

    expect(mockLogger.info).toHaveBeenCalledWith('Unhandled Square webhook: refund.created');
  });

  it('rejects a tampered body before dispatching', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const signedBody = rawBodyFor('payment.created', 'pay_1');
    const tamperedBody = rawBodyFor('payment.created', 'pay_attacker');

    await expect(
      svc.handleWebhook(event('payment.created', 'pay_attacker'), {
        signature: sign(signedBody),
        rawBody: tamperedBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });

    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('binds the signature to the notification URL', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const rawBody = rawBodyFor('payment.created', 'pay_1');

    await expect(
      svc.handleWebhook(event('payment.created', 'pay_1'), {
        signature: sign(rawBody, 'https://attacker.example.com/webhooks/square'),
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });
  });

  it('fails closed when SQUARE_WEBHOOK_SIGNATURE_KEY is not configured', async () => {
    const svc = await loadSquare({ accessToken: 'sq_test_token' });
    const rawBody = rawBodyFor('payment.created', 'pay_1');

    await expect(
      svc.handleWebhook(event('payment.created', 'pay_1'), {
        signature: sign(rawBody),
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });

    expect(mockLogger.warn).toHaveBeenCalledWith(
      'Square webhook rejected: SQUARE_WEBHOOK_SIGNATURE_KEY is not configured',
    );
    expect(mockLogger.info).not.toHaveBeenCalled();
  });

  it('rejects a webhook when no options object is supplied', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });

    await expect(svc.handleWebhook({ type: 'payment.created' })).resolves.toEqual({
      valid: false,
      reason: 'invalid or missing signature',
    });
  });

  it('rejects missing signature, body or notification URL without throwing', async () => {
    const svc = await loadSquare({ signatureKey: WEBHOOK_KEY });
    const rawBody = rawBodyFor('payment.created', 'pay_1');

    await expect(svc.handleWebhook(event('payment.created', 'pay_1'), {})).resolves.toEqual({
      valid: false,
      reason: 'invalid or missing signature',
    });
    await expect(
      svc.handleWebhook(event('payment.created', 'pay_1'), {
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });
    await expect(
      svc.handleWebhook(event('payment.created', 'pay_1'), {
        signature: 'short',
        rawBody,
        notificationUrl: NOTIFICATION_URL,
      }),
    ).resolves.toEqual({ valid: false, reason: 'invalid or missing signature' });
  });
});
