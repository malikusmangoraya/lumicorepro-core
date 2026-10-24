import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Mollie gateway tests.
 *
 * The service is a singleton built from `getGatewayConfig('mollie')` plus
 * process.env at import time, so every scenario reloads the module with the
 * config mock and env it needs. Network access is always a jest.fn().
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

const SERVICE_PATH = '../../services/payment/mollie.service.js';
const ENV_KEYS = ['MOLLIE_API_KEY', 'MOLLIE_ORGANIZATION_ID'];
const LIVE_ENV = { MOLLIE_API_KEY: 'test_mollie_key_123' };

const originalFetch = global.fetch;

const okResponse = (body) => ({
  ok: true,
  status: 200,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

const errorResponse = (text, status = 422) => ({
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

describe('mollie service - configuration', () => {
  it('builds its identity from the mollie gateway config', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(mockGetGatewayConfig).toHaveBeenCalledWith('mollie');
    expect(svc.enabled).toBe(true);
    expect(svc.apiKey).toBe('test_mollie_key_123');
    expect(svc.name).toBe('Mollie');
    expect(svc.baseURL).toBe('https://api.mollie.com/v2');
    expect(svc.region).toBe('Europe');
    expect(svc.supportedCurrencies).toEqual(
      expect.arrayContaining(['eur', 'usd', 'gbp', 'sek', 'nok', 'dkk', 'chf', 'pln', 'czk', 'huf']),
    );
  });

  it('stays disabled when the gateway config is disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });
    expect(svc.enabled).toBe(false);
  });
});

describe('mollie service - createPayment', () => {
  it('returns a mock checkout without touching the network when disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });

    const result = await svc.createPayment({
      amount: 99.99,
      currency: 'EUR',
      description: 'Order 1',
      redirectUrl: 'https://shop.example.com/cb',
    });

    expect(result.mock).toBe(true);
    expect(result.id).toMatch(/^tr_mock_\d+$/);
    expect(result.checkout_url).toBe('#');
    expect(result._links.checkout.href).toBe('#');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('posts a two-decimal amount under the raw (non-minor-unit) value', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(
      okResponse({ id: 'tr_123', status: 'open', _links: { checkout: { href: 'https://mollie/pay' } } }),
    );

    const result = await svc.createPayment({
      amount: 129.5,
      currency: 'EUR',
      description: 'Order 1',
      redirectUrl: 'https://shop.example.com/cb',
      webhookUrl: 'https://api.example.com/webhooks/mollie',
      metadata: { orderId: 'ord-1' },
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mollie.com/v2/payments');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer test_mollie_key_123',
    });
    expect(JSON.parse(init.body)).toEqual({
      amount: { value: '129.50', currency: 'EUR' },
      description: 'Order 1',
      redirectUrl: 'https://shop.example.com/cb',
      webhookUrl: 'https://api.example.com/webhooks/mollie',
      metadata: { orderId: 'ord-1' },
    });
    expect(result).toEqual({
      id: 'tr_123',
      status: 'open',
      _links: { checkout: { href: 'https://mollie/pay' } },
      mock: false,
    });
  });

  it('formats float artefacts to two decimals and defaults metadata to {}', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ id: 'tr_124' }));

    await svc.createPayment({ amount: 0.1 + 0.2, currency: 'EUR', description: 'Float order' });

    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.amount).toEqual({ value: '0.30', currency: 'EUR' });
    expect(body.metadata).toEqual({});
  });

  it('never marks a live payment as mock, even if Mollie echoes mock:true', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ id: 'tr_125', mock: true }));

    const result = await svc.createPayment({ amount: 5, currency: 'EUR', description: 'x' });

    expect(result.mock).toBe(false);
    expect(result.id).toBe('tr_125');
  });

  it('surfaces the Mollie error body when payment creation fails', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('{"detail":"Invalid API key"}'));

    await expect(
      svc.createPayment({ amount: 10, currency: 'EUR', description: 'Order 2' }),
    ).rejects.toThrow(/Mollie create payment failed: .*Invalid API key/);
  });
});

describe('mollie service - getPaymentStatus', () => {
  it('reports a pending (never paid) status when disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });

    await expect(svc.getPaymentStatus('tr_123')).resolves.toEqual({
      status: 'pending',
      mock: true,
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('fetches /payments/:id with bearer auth and returns the body untouched', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(
      okResponse({ resource: 'payment', id: 'tr_123', status: 'paid', amount: { value: '10.00' } }),
    );

    const result = await svc.getPaymentStatus('tr_123');

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mollie.com/v2/payments/tr_123');
    expect(init.method).toBeUndefined();
    expect(init.headers).toEqual({ Authorization: 'Bearer test_mollie_key_123' });
    expect(result).toEqual({
      resource: 'payment',
      id: 'tr_123',
      status: 'paid',
      amount: { value: '10.00' },
    });
    expect(result).not.toHaveProperty('mock');
  });

  it('surfaces status lookup failures', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('payment not found', 404));

    await expect(svc.getPaymentStatus('tr_missing')).rejects.toThrow(
      /Mollie get payment failed: payment not found/,
    );
  });
});

describe('mollie service - refund', () => {
  it('returns a mock refund reference without a network call when disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });

    const result = await svc.refund({ paymentId: 'tr_123', amount: 10, description: 'return' });

    expect(result.mock).toBe(true);
    expect(result.id).toMatch(/^re_mock_\d+$/);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('reads the refund currency from the payment instead of assuming EUR', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(
        okResponse({ id: 'tr_123', status: 'paid', amount: { value: '50.00', currency: 'GBP' } }),
      )
      .mockResolvedValueOnce(okResponse({ id: 're_1', status: 'pending' }));

    const result = await svc.refund({
      paymentId: 'tr_123',
      amount: 50,
      description: 'Damaged item',
    });

    expect(global.fetch).toHaveBeenCalledTimes(2);
    const [statusUrl, statusInit] = global.fetch.mock.calls[0];
    expect(statusUrl).toBe('https://api.mollie.com/v2/payments/tr_123');
    expect(statusInit.headers.Authorization).toBe('Bearer test_mollie_key_123');

    const [url, init] = global.fetch.mock.calls[1];
    expect(url).toBe('https://api.mollie.com/v2/payments/tr_123/refunds');
    expect(init.method).toBe('POST');
    expect(init.headers.Authorization).toBe('Bearer test_mollie_key_123');
    expect(JSON.parse(init.body)).toEqual({
      description: 'Damaged item',
      amount: { value: '50.00', currency: 'GBP' },
    });
    expect(result).toEqual({ id: 're_1', status: 'pending', mock: false });
  });

  it('uses a caller-supplied currency without re-fetching the payment', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(okResponse({ id: 're_2' }));

    await svc.refund({ paymentId: 'tr_124', amount: 10, currency: 'USD', description: 'x' });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(JSON.parse(global.fetch.mock.calls[0][1].body).amount).toEqual({
      value: '10.00',
      currency: 'USD',
    });
  });

  it('throws when the payment currency cannot be determined', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(okResponse({ id: 'tr_125', status: 'paid' }));

    await expect(
      svc.refund({ paymentId: 'tr_125', amount: 10, description: 'x' }),
    ).rejects.toThrow('Mollie refund: unable to determine payment currency');
    // Only the status lookup ran; no refund was posted.
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch.mock.calls[0][0]).toBe('https://api.mollie.com/v2/payments/tr_125');
  });

  it('omits the amount (and the currency lookup) for a full refund', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(okResponse({ id: 're_3' }));

    await svc.refund({ paymentId: 'tr_126', description: 'Full refund' });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.mollie.com/v2/payments/tr_126/refunds');
    const body = JSON.parse(init.body);
    expect(body).toEqual({ description: 'Full refund' });
    expect(body).not.toHaveProperty('amount');
  });

  it('surfaces status lookup failures during a refund', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(errorResponse('payment not found', 404));

    await expect(
      svc.refund({ paymentId: 'tr_missing', amount: 10, description: 'x' }),
    ).rejects.toThrow(/Mollie get payment failed: payment not found/);
  });

  it('surfaces refund failures', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(okResponse({ amount: { value: '10.00', currency: 'EUR' } }))
      .mockResolvedValueOnce(errorResponse('{"detail":"Insufficient balance"}'));

    await expect(
      svc.refund({ paymentId: 'tr_123', amount: 10, description: 'x' }),
    ).rejects.toThrow(/Mollie refund failed: .*Insufficient balance/);
  });
});

describe('mollie service - webhooks', () => {
  it('re-fetches the authoritative status and returns the payment', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    for (const [id, status] of [
      ['tr_1', 'paid'],
      ['tr_2', 'failed'],
      ['tr_3', 'refunded'],
      ['tr_4', 'expired'],
    ]) {
      global.fetch = jest
        .fn()
        .mockResolvedValueOnce(okResponse({ id, resource: 'payment', status }));

      await expect(svc.handleWebhook({ id, status: 'paid' })).resolves.toEqual({
        valid: true,
        payment: { id, resource: 'payment', status },
      });
      expect(global.fetch.mock.calls[0][0]).toBe(`https://api.mollie.com/v2/payments/${id}`);
    }

    expect(mockLogger.info).toHaveBeenCalledWith(
      'Mollie webhook: tr_3 authoritative status=refunded',
    );
  });

  it('never trusts the body-reported status', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(okResponse({ id: 'tr_forged', status: 'open' }));

    const result = await svc.handleWebhook({ id: 'tr_forged', status: 'paid' });

    expect(result).toEqual({
      valid: true,
      payment: { id: 'tr_forged', status: 'open' },
    });
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('accepts a raw payment id string', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(okResponse({ id: 'tr_str', status: 'paid' }));

    await expect(svc.handleWebhook('tr_str')).resolves.toEqual({
      valid: true,
      payment: { id: 'tr_str', status: 'paid' },
    });
  });

  it('rejects a payload without a payment id and never calls the API', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    await expect(svc.handleWebhook({})).resolves.toEqual({
      valid: false,
      reason: 'missing payment id',
    });
    await expect(svc.handleWebhook(undefined)).resolves.toEqual({
      valid: false,
      reason: 'missing payment id',
    });
    expect(mockLogger.warn).toHaveBeenCalledWith('Mollie webhook rejected: missing payment id');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('propagates lookup failures instead of assuming a status', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch = jest.fn().mockResolvedValueOnce(errorResponse('payment not found', 404));

    await expect(svc.handleWebhook({ id: 'tr_missing' })).rejects.toThrow(
      /Mollie get payment failed: payment not found/,
    );
  });
});
