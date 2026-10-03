import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * PayPal webhook verification middleware.
 *
 * PayPal signs deliveries with a rotating certificate, so verification is a
 * remote call to POST /v1/notifications/verify-webhook-signature. The route must
 * fail closed (400) whenever that check cannot be completed, and must never
 * reach the database or the fulfilment handler for an unverified payload.
 */

const findOne = jest.fn();
const findOrCreate = jest.fn();
const redisGet = jest.fn();
const redisSet = jest.fn();
const redisClient = { get: redisGet, set: redisSet };
const getRedis = jest.fn(() => redisClient);

const getWebhookId = jest.fn();
const verifyWebhookSignature = jest.fn();
const handleWebhook = jest.fn();
const paypalService = { getWebhookId, verifyWebhookSignature, handleWebhook };

const getStripeClient = jest.fn(async () => null);
const getStripeWebhookSecret = jest.fn(async () => '');

const loggerWarn = jest.fn();
const loggerError = jest.fn();
const silentLogger = {
  error: loggerError,
  warn: loggerWarn,
  info: () => {},
  http: () => {},
  debug: () => {},
};

jest.unstable_mockModule('../../models/WebhookEvent.js', () => ({
  default: { findOne, findOrCreate },
}));
jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({ getRedis }));
jest.unstable_mockModule('../../services/payment/dynamic.js', () => ({
  getStripeClient,
  getStripeWebhookSecret,
}));
jest.unstable_mockModule('../../services/payment/paypal.service.js', () => ({
  __esModule: true,
  default: paypalService,
}));
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: silentLogger,
  withRequestId: () => silentLogger,
  redact: (v) => v,
}));

const { paypalWebhook, markWebhookProcessed } = await import(
  '../../middleware/webhookSecurity.js'
);

const TRANSMISSION_HEADERS = {
  'paypal-transmission-id': 'txn-1',
  'paypal-transmission-time': '2026-10-03T10:00:00Z',
  'paypal-transmission-sig': 'sig-abc',
  'paypal-cert-url': 'https://api.paypal.com/v1/notifications/certs/CERT-1',
  'paypal-auth-algo': 'SHA256withRSA',
};

const CAPTURE_EVENT = {
  id: 'WH-EVT-1',
  event_type: 'PAYMENT.CAPTURE.COMPLETED',
  resource: { id: 'CAP-1', status: 'COMPLETED' },
};

const fakeRes = () => {
  const res = { headersSent: false };
  res.status = jest.fn((c) => {
    res._status = c;
    return res;
  });
  res.json = jest.fn((b) => {
    res._body = b;
    res.headersSent = true;
    return res;
  });
  res.send = jest.fn((b) => {
    res._body = b;
    res.headersSent = true;
    return res;
  });
  return res;
};

const makeReq = (event = CAPTURE_EVENT, headers = TRANSMISSION_HEADERS) => ({
  headers,
  body: Buffer.from(JSON.stringify(event)),
});

let savedNodeEnv;

beforeEach(() => {
  savedNodeEnv = process.env.NODE_ENV;
  process.env.NODE_ENV = 'test';

  jest.clearAllMocks();
  getRedis.mockReturnValue(redisClient);
  redisGet.mockResolvedValue(null);
  redisSet.mockResolvedValue('OK');
  findOne.mockResolvedValue(null);
  findOrCreate.mockResolvedValue([{}, true]);
  getWebhookId.mockResolvedValue('WH-TEST');
  verifyWebhookSignature.mockResolvedValue(true);
  handleWebhook.mockResolvedValue({ handled: true, orderId: 9 });
});

afterEach(() => {
  if (savedNodeEnv === undefined) delete process.env.NODE_ENV;
  else process.env.NODE_ENV = savedNodeEnv;
});

describe('paypalWebhook — signature verification', () => {
  it('rejects a forged payload with 400 and never touches the DB or fulfilment', async () => {
    verifyWebhookSignature.mockResolvedValue(false);
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()(makeReq(), res, next);

    expect(res._status).toBe(400);
    expect(res._body.code).toBe('WEBHOOK_VERIFICATION_FAILED');
    expect(res._body).toMatchObject({ success: false, status: 400, data: null });
    expect(next).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
    expect(findOrCreate).not.toHaveBeenCalled();
    expect(handleWebhook).not.toHaveBeenCalled();
  });

  it('sends the PayPal transmission headers + webhook id to the verification API', async () => {
    await paypalWebhook()(makeReq(), fakeRes(), jest.fn());

    expect(verifyWebhookSignature).toHaveBeenCalledTimes(1);
    expect(verifyWebhookSignature).toHaveBeenCalledWith({
      transmissionId: 'txn-1',
      transmissionTime: '2026-10-03T10:00:00Z',
      transmissionSig: 'sig-abc',
      certUrl: 'https://api.paypal.com/v1/notifications/certs/CERT-1',
      authAlgo: 'SHA256withRSA',
      webhookId: 'WH-TEST',
      webhookEvent: CAPTURE_EVENT,
    });
  });

  it('rejects with 400 when verification cannot be completed (API error)', async () => {
    verifyWebhookSignature.mockRejectedValue(new Error('PayPal auth failed: 401'));
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()(makeReq(), res, next);

    expect(res._status).toBe(400);
    expect(res._body.code).toBe('WEBHOOK_VERIFICATION_FAILED');
    expect(next).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
    expect(handleWebhook).not.toHaveBeenCalled();
  });

  it('fails closed with 400 when PAYPAL_WEBHOOK_ID is missing in production', async () => {
    process.env.NODE_ENV = 'production';
    getWebhookId.mockResolvedValue('');
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()(makeReq(), res, next);

    expect(res._status).toBe(400);
    expect(res._body.code).toBe('WEBHOOK_NOT_CONFIGURED');
    expect(verifyWebhookSignature).not.toHaveBeenCalled();
    expect(next).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
  });

  it('also fails closed outside production (test/staging) when the id is missing', async () => {
    process.env.NODE_ENV = 'test';
    getWebhookId.mockResolvedValue('');
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()(makeReq(), res, next);

    expect(res._status).toBe(400);
    expect(res._body.code).toBe('WEBHOOK_NOT_CONFIGURED');
    expect(next).not.toHaveBeenCalled();
  });

  it('development only: explicitly skips verification with a warning when the id is missing', async () => {
    process.env.NODE_ENV = 'development';
    getWebhookId.mockResolvedValue('');
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()(makeReq(), res, next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(verifyWebhookSignature).not.toHaveBeenCalled();
    expect(loggerWarn).toHaveBeenCalled();
    expect(String(loggerWarn.mock.calls[0][0])).toMatch(/SKIPPING/);
  });

  it('rejects an unparseable body with 400 before any verification or DB access', async () => {
    const res = fakeRes();
    const next = jest.fn();

    await paypalWebhook()({ headers: TRANSMISSION_HEADERS, body: Buffer.from('not json') }, res, next);

    expect(res._status).toBe(400);
    expect(res._body.code).toBe('INVALID_PAYLOAD');
    expect(verifyWebhookSignature).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
    expect(next).not.toHaveBeenCalled();
  });
});

describe('paypalWebhook — idempotency', () => {
  it('passes a verified first-time event through and tags the gateway', async () => {
    const req = makeReq();
    const next = jest.fn();

    await paypalWebhook()(req, fakeRes(), next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(req._webhookGateway).toBe('paypal');
    expect(req._webhookEventId).toBe('WH-EVT-1');
    expect(req._webhookDedupeKey).toBe('webhook:processed:WH-EVT-1');
  });

  it('short-circuits a replay found on the Redis fast-path', async () => {
    redisGet.mockResolvedValue(String(Date.now()));
    const next = jest.fn();
    const res = fakeRes();

    await paypalWebhook()(makeReq(), res, next);

    expect(res._body).toMatchObject({ received: true, idempotent: true, eventId: 'WH-EVT-1' });
    expect(next).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
    expect(handleWebhook).not.toHaveBeenCalled();
  });

  it('short-circuits a replay found in the durable ledger and re-warms Redis', async () => {
    findOne.mockResolvedValue({ event_id: 'WH-EVT-1' });
    const next = jest.fn();
    const res = fakeRes();

    await paypalWebhook()(makeReq(), res, next);

    expect(findOne).toHaveBeenCalledWith({ where: { event_id: 'WH-EVT-1' } });
    expect(redisSet).toHaveBeenCalled();
    expect(res._body).toMatchObject({ received: true, idempotent: true });
    expect(next).not.toHaveBeenCalled();
  });

  it('records the delivery in the ledger with gateway "paypal"', async () => {
    const req = makeReq();
    await paypalWebhook()(req, fakeRes(), jest.fn());

    await markWebhookProcessed(req);

    expect(findOrCreate).toHaveBeenCalledWith({
      where: { event_id: 'WH-EVT-1' },
      defaults: expect.objectContaining({
        gateway: 'paypal',
        event_type: 'PAYMENT.CAPTURE.COMPLETED',
      }),
    });
    expect(redisSet).toHaveBeenCalledWith(
      'webhook:processed:WH-EVT-1',
      expect.any(String),
      'EX',
      86400,
    );
  });
});
