import crypto from 'crypto';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import PaytmChecksum from 'paytmchecksum';

/**
 * Paytm gateway tests.
 *
 * Checksums follow Paytm's official scheme:
 *   paramsString = values sorted by key, joined with "|"
 *   hash         = sha256(paramsString + "|" + salt).hex + salt
 *   checksum     = base64(AES-128-CBC(hash, merchantKey, "@@@@&&&&####$$$$"))
 * Interoperability is asserted in BOTH directions against the official
 * `paytmchecksum` package (installed in backend/node_modules).
 *
 * The service is a singleton created from `getGatewayConfig('paytm')` +
 * process.env at import time, so each scenario reloads the module.
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

const SERVICE_PATH = '../../services/payment/paytm.service.js';
const ENV_KEYS = [
  'PAYTM_MERCHANT_ID',
  'PAYTM_MERCHANT_KEY',
  'PAYTM_WEBSITE',
  'PAYTM_INDUSTRY_TYPE',
  'PAYTM_CHANNEL_ID',
  'PAYTM_MODE',
];

// AES-128 needs exactly 16 bytes; any other length cannot produce a checksum.
const MERCHANT_KEY = 'merchantkey12345';
const OTHER_MERCHANT_KEY = 'other-merchant-k';
const PAYTM_IV = '@@@@&&&&####$$$$';

const LIVE_ENV = {
  PAYTM_MERCHANT_ID: 'mid_test_123',
  PAYTM_MERCHANT_KEY: MERCHANT_KEY,
};

const FLAT_PARAMS = {
  ORDER_ID: 'order-9',
  MID: 'mid_test_123',
  TXN_AMOUNT: '10.00',
  CURRENCY: 'INR',
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

describe('paytm service - configuration', () => {
  it('builds its identity and staging defaults from the paytm gateway config', async () => {
    const svc = await loadService({ env: LIVE_ENV });

    expect(mockGetGatewayConfig).toHaveBeenCalledWith('paytm');
    expect(svc.enabled).toBe(true);
    expect(svc.merchantId).toBe('mid_test_123');
    expect(svc.merchantKey).toBe(MERCHANT_KEY);
    expect(svc.website).toBe('WEBSTAGING');
    expect(svc.industryType).toBe('Retail');
    expect(svc.channelId).toBe('WEB');
    expect(svc.mode).toBe('sandbox');
    expect(svc.baseURL).toBe('https://securegw-stage.paytm.in');
    expect(svc.supportedCurrencies).toEqual(['inr']);
    expect(svc.region).toBe('India');
    // A 16-byte key is the only valid AES-128 length: no warning expected.
    expect(mockLogger.warn).not.toHaveBeenCalled();
  });

  it('warns when an enabled merchant key is not 16 bytes', async () => {
    await loadService({ env: { PAYTM_MERCHANT_ID: 'mid_test_123', PAYTM_MERCHANT_KEY: 'short' } });

    expect(mockLogger.warn).toHaveBeenCalledWith(
      'Paytm merchant key should be 16 bytes — checksum will fail with this key',
    );
  });

  it('stays disabled when the gateway config is disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });
    expect(svc.enabled).toBe(false);
  });

  it('uses the production host for any mode other than sandbox', async () => {
    const production = await loadService({ env: { ...LIVE_ENV, PAYTM_MODE: 'production' } });
    expect(production.baseURL).toBe('https://securegw.paytm.in');

    const live = await loadService({ env: { ...LIVE_ENV, PAYTM_MODE: 'live' } });
    expect(live.baseURL).toBe('https://securegw.paytm.in');
  });

  it('honours explicit website / industry / channel overrides', async () => {
    const svc = await loadService({
      env: {
        ...LIVE_ENV,
        PAYTM_WEBSITE: 'DEFAULT',
        PAYTM_INDUSTRY_TYPE: 'Education',
        PAYTM_CHANNEL_ID: 'WAP',
      },
    });

    expect(svc.website).toBe('DEFAULT');
    expect(svc.industryType).toBe('Education');
    expect(svc.channelId).toBe('WAP');
  });
});

describe('paytm service - checksum scheme', () => {
  let svc;

  beforeEach(async () => {
    svc = await loadService({ env: LIVE_ENV });
  });

  it('signs the sorted parameter VALUES joined by "|"', () => {
    // Same values, different insertion order => same checksum payload.
    const reversed = Object.fromEntries(Object.entries(FLAT_PARAMS).reverse());
    expect(svc._paramsString(FLAT_PARAMS)).toBe(svc._paramsString(reversed));
    expect(svc._paramsString(FLAT_PARAMS)).toBe('INR|mid_test_123|order-9|10.00');
  });

  it('produces an AES-128-CBC checksum of sha256(params|salt).hex + salt', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);
    const decrypted = svc._decrypt(checksum);

    // sha256 hex (64 chars) + 4-char salt.
    expect(decrypted).toMatch(/^[a-f0-9]{64}.{4}$/);

    const salt = decrypted.slice(-4);
    const expectedHash = crypto
      .createHash('sha256')
      .update(`${svc._paramsString(FLAT_PARAMS)}|${salt}`)
      .digest('hex') + salt;
    expect(decrypted).toBe(expectedHash);

    // The blob is exactly what Paytm's AES-128-CBC helper produces.
    const decipher = crypto.createDecipheriv('AES-128-CBC', MERCHANT_KEY, PAYTM_IV);
    const manual = decipher.update(checksum, 'base64', 'binary') + decipher.final('binary');
    expect(manual).toBe(decrypted);
    expect(Buffer.from(checksum, 'base64')).toHaveLength(80);
  });

  it('round-trips generateChecksum -> verifyChecksum in any key order', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    expect(svc.verifyChecksum(FLAT_PARAMS, checksum)).toBe(true);
    const reversed = Object.fromEntries(Object.entries(FLAT_PARAMS).reverse());
    expect(svc.verifyChecksum(reversed, checksum)).toBe(true);
  });

  it('accepts a checksum produced by the official paytmchecksum package', async () => {
    const official = await PaytmChecksum.generateSignature(FLAT_PARAMS, MERCHANT_KEY);

    expect(svc.verifyChecksum(FLAT_PARAMS, official)).toBe(true);
    expect(PaytmChecksum.verifySignature({ ...FLAT_PARAMS }, MERCHANT_KEY, official)).toBe(true);
  });

  it('produces checksums the official package verifies', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    expect(PaytmChecksum.verifySignature({ ...FLAT_PARAMS }, MERCHANT_KEY, checksum)).toBe(true);
  });

  it('rejects a checksum after the amount is tampered with', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    expect(svc.verifyChecksum({ ...FLAT_PARAMS, TXN_AMOUNT: '1.00' }, checksum)).toBe(false);
    expect(
      PaytmChecksum.verifySignature(
        { ...FLAT_PARAMS, TXN_AMOUNT: '1.00' },
        MERCHANT_KEY,
        checksum,
      ),
    ).toBe(false);
  });

  it('binds the checksum to the merchant key, not just the params', async () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);
    const other = await loadService({
      env: { PAYTM_MERCHANT_ID: 'mid_test_123', PAYTM_MERCHANT_KEY: OTHER_MERCHANT_KEY },
    });

    expect(other.verifyChecksum(FLAT_PARAMS, checksum)).toBe(false);

    const officialOther = await PaytmChecksum.generateSignature(FLAT_PARAMS, OTHER_MERCHANT_KEY);
    expect(svc.verifyChecksum(FLAT_PARAMS, officialOther)).toBe(false);
  });

  it('accepts pre-serialised string params (official package parity)', async () => {
    const paramsString = 'mid_test_123|INR|order-9|10.00';
    const ours = svc.generateChecksum(paramsString);
    expect(PaytmChecksum.verifySignature(paramsString, MERCHANT_KEY, ours)).toBe(true);

    const official = await PaytmChecksum.generateSignature(paramsString, MERCHANT_KEY);
    expect(svc.verifyChecksum(paramsString, official)).toBe(true);
  });

  it('treats null/undefined values as empty strings', () => {
    expect(svc._paramsString({ A: null, B: undefined, C: 'x' })).toBe('||x');
  });

  it('exposes verifyChecksumResponse as a promise-friendly delegate', async () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    await expect(svc.verifyChecksumResponse(FLAT_PARAMS, checksum)).resolves.toBe(true);
    await expect(
      svc.verifyChecksumResponse({ ...FLAT_PARAMS, CURRENCY: 'USD' }, checksum),
    ).resolves.toBe(false);
  });

  it('returns false (never throws) for empty or malformed checksums', () => {
    for (const bad of ['', undefined, null, 'not-base64!!!', 'deadbeef', 'AAAA']) {
      expect(() => svc.verifyChecksum(FLAT_PARAMS, bad)).not.toThrow();
      expect(svc.verifyChecksum(FLAT_PARAMS, bad)).toBe(false);
    }
  });

  it('returns false when no merchant key is configured', async () => {
    const keyless = await loadService({ env: { PAYTM_MERCHANT_ID: 'mid_test_123' } });

    expect(keyless.verifyChecksum(FLAT_PARAMS, svc.generateChecksum(FLAT_PARAMS))).toBe(false);
  });

  it('does not mutate the caller params when verifying', () => {
    const params = { ...FLAT_PARAMS };
    const checksum = svc.generateChecksum(params);
    svc.verifyChecksum(params, checksum);

    expect(params).toEqual(FLAT_PARAMS);
  });
});

describe('paytm service - initiateTransaction', () => {
  it('returns a mock transaction without touching the network when disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });

    const result = await svc.initiateTransaction({
      amount: 500,
      orderId: 'order-1',
      email: 'buyer@example.com',
      phone: '9999999999',
      callbackUrl: 'https://shop.example.com/cb',
    });

    expect(result.mock).toBe(true);
    expect(result.txnId).toMatch(/^paytm_mock_\d+$/);
    expect(result.redirectURL).toBe('#paytm_mock');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('posts the signed body to initiateTransaction and returns the txn token', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(
      okResponse({
        body: { txnToken: 'TXN_9000', resultInfo: { resultStatus: 'S', resultCode: '0000' } },
      }),
    );

    const result = await svc.initiateTransaction({
      amount: 129.5,
      orderId: 'order-1',
      email: 'buyer@example.com',
      phone: '9999999999',
      callbackUrl: 'https://shop.example.com/cb',
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe(
      'https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction?mid=mid_test_123&orderId=order-1',
    );
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' });

    const payload = JSON.parse(init.body);
    expect(payload.body).toEqual({
      requestType: 'Payment',
      mid: 'mid_test_123',
      websiteName: 'WEBSTAGING',
      orderId: 'order-1',
      txnAmount: { value: '129.50', currency: 'INR' },
      userInfo: { custId: 'buyer@example.com' },
      callbackUrl: 'https://shop.example.com/cb',
    });
    expect(payload.head.signature).toMatch(/^[A-Za-z0-9+/]+=*$/);
    // Signature is computed over the JSON body string, binding nested amounts.
    expect(svc.verifyChecksum(JSON.stringify(payload.body), payload.head.signature)).toBe(true);
    expect(
      svc.verifyChecksum(JSON.stringify({ ...payload.body, orderId: 'order-tampered' }), payload.head.signature),
    ).toBe(false);
    expect(
      svc.verifyChecksum(JSON.stringify({ ...payload.body, mid: 'attacker_mid' }), payload.head.signature),
    ).toBe(false);
    // The amount is part of the signed payload — tampering must break the signature.
    expect(
      svc.verifyChecksum(
        JSON.stringify({ ...payload.body, txnAmount: { value: '1.00', currency: 'INR' } }),
        payload.head.signature,
      ),
    ).toBe(false);

    expect(result).toEqual({
      txnToken: 'TXN_9000',
      redirectURL:
        'https://securegw-stage.paytm.in/theia/api/v1/showPaymentPage?mid=mid_test_123&orderId=order-1',
      mock: false,
    });
  });

  it('formats the amount to two decimals without float artefacts', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ body: { txnToken: 'T', resultInfo: { resultStatus: 'S' } } }));

    await svc.initiateTransaction({ amount: 0.1 + 0.2, orderId: 'order-2' });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body).body.txnAmount.value).toBe('0.30');
  });

  it('falls back to phone, then order id, for the customer id', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ body: { txnToken: 'T', resultInfo: { resultStatus: 'S' } } }));

    await svc.initiateTransaction({ amount: 10, orderId: 'order-3', phone: '9999999999' });
    expect(JSON.parse(global.fetch.mock.calls[0][1].body).body.userInfo.custId).toBe('9999999999');

    await svc.initiateTransaction({ amount: 10, orderId: 'order-4' });
    expect(JSON.parse(global.fetch.mock.calls[1][1].body).body.userInfo.custId).toBe('order-4');
  });

  it('throws when Paytm does not answer resultStatus "S"', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(
      okResponse({
        body: { resultInfo: { resultStatus: 'F', resultCode: '501', resultMsg: 'Invalid request' } },
      }),
    );

    await expect(
      svc.initiateTransaction({ amount: 10, orderId: 'order-5' }),
    ).rejects.toThrow('Paytm initiate transaction rejected: 501 Invalid request');
  });

  it('throws with UNKNOWN when the result info is missing', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({}));

    await expect(
      svc.initiateTransaction({ amount: 10, orderId: 'order-6' }),
    ).rejects.toThrow('Paytm initiate transaction rejected: UNKNOWN');
  });

  it('surfaces HTTP failures with the gateway text', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('{"message":"Invalid MID"}'));

    await expect(
      svc.initiateTransaction({ amount: 10, orderId: 'order-7' }),
    ).rejects.toThrow(/Paytm initiate transaction failed: .*Invalid MID/);
  });
});

describe('paytm service - refund', () => {
  it('returns a mock success without touching the network when disabled', async () => {
    const svc = await loadService({ env: LIVE_ENV, config: { enabled: false } });

    const result = await svc.refund({ orderId: 'order-1', txnAmount: 50, refundId: 'refund-1' });

    expect(result).toEqual({ success: true, mock: true, orderId: 'order-1', refundId: 'refund-1' });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('posts a signed REFUND request to /theia/api/v1/refund', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ body: { resultInfo: { resultStatus: 'S' } } }));

    const result = await svc.refund({
      orderId: 'order-1',
      txnAmount: 250,
      refundId: 'refund-1',
    });

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://securegw-stage.paytm.in/theia/api/v1/refund');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' });

    const payload = JSON.parse(init.body);
    expect(payload.body).toEqual({
      mid: 'mid_test_123',
      txnType: 'REFUND',
      orderId: 'order-1',
      txnAmount: { value: '250.00', currency: 'INR' },
      refId: 'refund-1',
    });
    expect(svc.verifyChecksum(JSON.stringify(payload.body), payload.head.signature)).toBe(true);
    expect(result).toEqual({ success: true, orderId: 'order-1', refundId: 'refund-1' });
  });

  it('normalises the refund amount to two decimals', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ body: { resultInfo: { resultStatus: 'S' } } }));

    await svc.refund({ orderId: 'order-2', txnAmount: 250.5, refundId: 'refund-2' });

    expect(JSON.parse(global.fetch.mock.calls[0][1].body).body.txnAmount.value).toBe('250.50');
  });

  it('reports success=false for any status other than "S"', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({ body: { resultInfo: { resultStatus: 'P' } } }));

    const result = await svc.refund({ orderId: 'order-3', txnAmount: 10, refundId: 'refund-3' });

    expect(result.success).toBe(false);
    expect(result).toMatchObject({ orderId: 'order-3', refundId: 'refund-3' });
  });

  it('reports success=false (without throwing) for an empty gateway body', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(okResponse({}));

    await expect(
      svc.refund({ orderId: 'order-4', txnAmount: 10, refundId: 'refund-4' }),
    ).resolves.toMatchObject({ success: false });
  });

  it('surfaces refund HTTP failures with the gateway text', async () => {
    const svc = await loadService({ env: LIVE_ENV });
    global.fetch.mockResolvedValue(errorResponse('{"message":"Refund window expired"}'));

    await expect(
      svc.refund({ orderId: 'order-5', txnAmount: 10, refundId: 'refund-5' }),
    ).rejects.toThrow(/Paytm refund failed: .*Refund window expired/);
  });
});

describe('paytm service - handleCallback', () => {
  let svc;

  beforeEach(async () => {
    svc = await loadService({ env: LIVE_ENV });
  });

  it('accepts a callback with a valid CHECKSUMHASH and strips the checksum', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    const result = svc.handleCallback({ ...FLAT_PARAMS, CHECKSUMHASH: checksum });

    expect(result.valid).toBe(true);
    expect(result.params).toEqual(FLAT_PARAMS);
    expect(result.params).not.toHaveProperty('CHECKSUMHASH');
  });

  it('accepts a CHECKSUMHASH generated by the official package', async () => {
    const official = await PaytmChecksum.generateSignature(FLAT_PARAMS, MERCHANT_KEY);

    expect(svc.handleCallback({ ...FLAT_PARAMS, CHECKSUMHASH: official }).valid).toBe(true);
  });

  it('rejects a callback whose status/amount was tampered with', () => {
    const checksum = svc.generateChecksum(FLAT_PARAMS);

    const result = svc.handleCallback({
      ...FLAT_PARAMS,
      TXN_AMOUNT: '1.00',
      CHECKSUMHASH: checksum,
    });

    expect(result.valid).toBe(false);
    expect(result.params.TXN_AMOUNT).toBe('1.00');
  });

  it('rejects a callback with no CHECKSUMHASH or an empty payload', () => {
    expect(svc.handleCallback(FLAT_PARAMS).valid).toBe(false);
    expect(svc.handleCallback({}).valid).toBe(false);
    expect(svc.handleCallback(undefined)).toEqual({ valid: false, params: {} });
  });
});
