import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() },
}));

const originalFetch = global.fetch;

/**
 * bkash.service.js exports a singleton built at import time from
 * process.env, so "enabled" scenarios need the env set before a dynamic import.
 */
async function loadBkash(appKey) {
  const saved = {
    BKASH_APP_KEY: process.env.BKASH_APP_KEY,
    BKASH_APP_SECRET: process.env.BKASH_APP_SECRET,
  };
  if (appKey) process.env.BKASH_APP_KEY = appKey;
  else delete process.env.BKASH_APP_KEY;
  process.env.BKASH_APP_SECRET = 'app-secret';
  jest.resetModules();
  const mod = await import('../../services/payment/bkash.service.js');
  return {
    svc: mod.default,
    restore: () => {
      for (const [k, v] of Object.entries(saved)) {
        if (v === undefined) delete process.env[k];
        else process.env[k] = v;
      }
    },
  };
}

const jsonResponse = (body, ok = true) => ({
  ok,
  status: ok ? 200 : 400,
  json: async () => body,
  text: async () => JSON.stringify(body),
});

beforeEach(() => {
  jest.clearAllMocks();
});
afterEach(() => {
  global.fetch = originalFetch;
  delete process.env.BKASH_APP_KEY;
  delete process.env.BKASH_APP_SECRET;
});

describe('bkash service - disabled / mock mode', () => {
  it('is disabled when BKASH_APP_KEY is unset', async () => {
    const { svc, restore } = await loadBkash(null);
    expect(svc.enabled).toBe(false);
    restore();
  });

  it('returns a mock checkout without touching the network', async () => {
    const { svc, restore } = await loadBkash(null);
    global.fetch = jest.fn();
    const r = await svc.createPayment({ amount: 500, orderId: 'o1' });
    expect(r.mock).toBe(true);
    expect(r.checkoutURL).toBe('#');
    expect(r.paymentID).toMatch(/^bkash_mock_/);
    expect(global.fetch).not.toHaveBeenCalled();
    restore();
  });

  it('short-circuits execute and refund in mock mode', async () => {
    const { svc, restore } = await loadBkash(null);
    await expect(svc.executePayment({ paymentId: 'p1' })).resolves.toMatchObject({
      success: true,
      mock: true,
    });
    await expect(svc.refund({ paymentId: 'p1' })).resolves.toMatchObject({
      success: true,
      mock: true,
    });
    restore();
  });
});

describe('bkash service - live mode', () => {
  it('requests a token with basic auth built from app key + secret', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    expect(svc.enabled).toBe(true);

    global.fetch = jest.fn(async () => jsonResponse({ access_token: 'tok_123' }));
    const token = await svc.getAccessToken();

    expect(token).toBe('tok_123');
    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toContain('/tokenization');
    expect(init.headers['X-App-Key']).toBe('app-key-1');
    const expected = Buffer.from('app-key-1:app-secret').toString('base64');
    expect(init.headers.Authorization).toBe(`Basic ${expected}`);
    restore();
  });

  it('throws a descriptive error when the token request fails', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest.fn(async () => jsonResponse({ message: 'bad creds' }, false));
    await expect(svc.getAccessToken()).rejects.toThrow(/bKash token failed/);
    restore();
  });

  it('creates a checkout with the bearer token and BDT currency', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentID: 'pay_1', bkashURL: 'https://pay' }));

    const r = await svc.createPayment({ amount: 1200, orderId: 'o1', callbackUrl: 'https://cb' });

    const [, init] = global.fetch.mock.calls[1];
    expect(init.headers.authorization).toBe('Bearer tok_123');
    const body = JSON.parse(init.body);
    expect(body.amount).toBe(1200);
    expect(body.currency).toBe('BDT');
    expect(body.callbackURL).toBe('https://cb');
    expect(r).toMatchObject({ paymentID: 'pay_1', mock: false });
    restore();
  });

  it('derives success from paymentStatusCode 0000 on execute', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentStatusCode: '0000', trxID: 'T1' }));

    const r = await svc.executePayment({ paymentId: 'pay_1', callbackType: 'callback' });
    expect(r.success).toBe(true);
    expect(r.trxID).toBe('T1');
    restore();
  });

  it('reports success=false for a non-0000 paymentStatusCode', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentStatusCode: '9999' }));

    const r = await svc.executePayment({ paymentId: 'pay_1' });
    expect(r.success).toBe(false);
    restore();
  });

  it('does not let the gateway payload overwrite the computed success flag', async () => {
    // Regression guard: `{ success: computed, ...data }` let an echoed
    // success:true from a FAILED response win, marking a declined payment paid.
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentStatusCode: '9999', success: true }));

    const r = await svc.executePayment({ paymentId: 'pay_1' });
    expect(r.paymentStatusCode).toBe('9999');
    expect(r.success).toBe(false);
    restore();
  });

  it('applies the same guard on refund', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentStatusCode: '9999', success: true }));
    const r = await svc.refund({ paymentId: 'pay_1', amount: 100 });
    expect(r.success).toBe(false);
    restore();
  });

  it('surfaces a refund failure from the gateway', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ message: 'cannot refund' }, false));
    await expect(svc.refund({ paymentId: 'pay_1' })).rejects.toThrow(/bKash refund failed/);
    restore();
  });

  it('marks a live createPayment as not a mock', async () => {
    const { svc, restore } = await loadBkash('app-key-1');
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'tok_123' }))
      .mockResolvedValueOnce(jsonResponse({ paymentID: 'pay_1', mock: true }));
    const r = await svc.createPayment({ amount: 100 });
    expect(r.mock).toBe(false);
    restore();
  });
});

describe('bkash service - webhook handling', () => {
  it('does not throw for payment, refund or unknown event types', async () => {
    const { svc, restore } = await loadBkash(null);
    await expect(svc.handleWebhook({ eventType: 'PAYMENT', paymentID: 'p' })).resolves.toBeUndefined();
    await expect(svc.handleWebhook({ eventType: 'REFUND', paymentID: 'p' })).resolves.toBeUndefined();
    await expect(svc.handleWebhook({ eventType: 'NOPE' })).resolves.toBeUndefined();
    restore();
  });
});
