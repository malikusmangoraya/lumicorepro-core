/**
 * Feature tests — secondary payment gateway routes
 * (routes/payment-gateways.routes.js).
 *
 * The router is mounted on a bare Express app with a mocked auth/rate-limit
 * stack, Order model and gateway services, so these tests exercise the HTTP
 * wiring only: status codes, response shapes, raw-body/signature pass-through
 * and the order-ownership guard. Signature algorithms themselves are covered
 * by tests/unit/*Service.test.js.
 */
import express from 'express';
import request from 'supertest';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

const TEST_USER = { id: 7, role: 'user', email: 'buyer@example.com' };
const NOTIFY_URL = 'https://api.test/api/payments/square/webhook';

const ORDERS = new Map([
  [
    'order_owned',
    {
      id: 'order_owned',
      user_id: 7,
      totalPrice: '42.50',
      currency: 'USD',
      orderNumber: 'ORD-1001',
    },
  ],
  [
    'order_foreign',
    {
      id: 'order_foreign',
      user_id: 99,
      totalPrice: '500.00',
      currency: 'USD',
      orderNumber: 'ORD-1002',
    },
  ],
]);

// ── Mocks (registered before the router is imported) ─────────────────────

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  http: jest.fn(),
};

jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: mockLogger,
  withRequestId: () => mockLogger,
  redact: (value) => value,
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { ...TEST_USER };
    next();
  },
  authorize: () => (_req, _res, next) => next(),
  optionalProtect: (_req, _res, next) => next(),
}));

jest.unstable_mockModule('../../middleware/rateLimit.js', () => {
  const passthrough = (_req, _res, next) => next();
  return {
    __esModule: true,
    paymentLimiter: passthrough,
    apiLimiter: passthrough,
    default: { paymentLimiter: passthrough, apiLimiter: passthrough },
  };
});

const findByPk = jest.fn();
jest.unstable_mockModule('../../models/Order.js', () => ({
  __esModule: true,
  default: { findByPk },
}));

const mollieCreatePayment = jest.fn();
const mollieHandleWebhook = jest.fn();
jest.unstable_mockModule('../../services/payment/mollie.service.js', () => ({
  __esModule: true,
  default: { createPayment: mollieCreatePayment, handleWebhook: mollieHandleWebhook },
}));

const flutterwaveInitialize = jest.fn();
const flutterwaveVerify = jest.fn();
const flutterwaveHandleWebhook = jest.fn();
jest.unstable_mockModule('../../services/payment/flutterwave.service.js', () => ({
  __esModule: true,
  default: {
    initializeTransaction: flutterwaveInitialize,
    verifyTransaction: flutterwaveVerify,
    handleWebhook: flutterwaveHandleWebhook,
  },
}));

const squareCreate = jest.fn();
const squareHandleWebhook = jest.fn();
jest.unstable_mockModule('../../services/payment/square.service.js', () => ({
  __esModule: true,
  default: { createPayment: squareCreate, handleWebhook: squareHandleWebhook },
}));

const mpCreatePreference = jest.fn();
const mpHandleWebhook = jest.fn();
jest.unstable_mockModule('../../services/payment/mercadopago.service.js', () => ({
  __esModule: true,
  default: { createPreference: mpCreatePreference, handleWebhook: mpHandleWebhook },
}));

const liqpayCreateForm = jest.fn();
const liqpayHandleCallback = jest.fn();
jest.unstable_mockModule('../../services/payment/liqpay.service.js', () => ({
  __esModule: true,
  default: { createPaymentForm: liqpayCreateForm, handleCallback: liqpayHandleCallback },
}));

const paytmInitiate = jest.fn();
const paytmHandleCallback = jest.fn();
jest.unstable_mockModule('../../services/payment/paytm.service.js', () => ({
  __esModule: true,
  default: { initiateTransaction: paytmInitiate, handleCallback: paytmHandleCallback },
}));

const bkashCreate = jest.fn();
const bkashExecute = jest.fn();
const bkashHandleWebhook = jest.fn();
jest.unstable_mockModule('../../services/payment/bkash.service.js', () => ({
  __esModule: true,
  default: {
    createPayment: bkashCreate,
    executePayment: bkashExecute,
    handleWebhook: bkashHandleWebhook,
  },
}));

const { default: gatewayRoutes } = await import('../../routes/payment-gateways.routes.js');

// Mirror server.js: sign-over-raw-body webhooks are parsed before express.json.
const app = express();
app.use('/api/payments/flutterwave/webhook', express.raw({ type: 'application/json' }));
app.use('/api/payments/square/webhook', express.raw({ type: 'application/json' }));
app.use('/api/payments/mercadopago/webhook', express.raw({ type: 'application/json' }));
app.use(express.json());
app.use('/api/payments', gatewayRoutes);
app.use((err, _req, res, _next) => {
  res.status(500).json({ success: false, error: err.message });
});

// ── Environment + mock defaults ──────────────────────────────────────────

const ENV_KEYS = ['SQUARE_WEBHOOK_NOTIFICATION_URL', 'BACKEND_URL', 'FRONTEND_URL', 'DEFAULT_CURRENCY'];
let envSnapshot = {};

beforeEach(() => {
  envSnapshot = Object.fromEntries(ENV_KEYS.map((key) => [key, process.env[key]]));
  process.env.SQUARE_WEBHOOK_NOTIFICATION_URL = NOTIFY_URL;
  process.env.BACKEND_URL = 'https://api.test';
  process.env.FRONTEND_URL = 'https://shop.test';
  delete process.env.DEFAULT_CURRENCY;

  findByPk.mockImplementation(async (id) => ORDERS.get(String(id)) || null);

  mollieCreatePayment.mockResolvedValue({
    id: 'tr_1',
    _links: { checkout: { href: 'https://mollie.test/checkout' } },
    mock: true,
  });
  mollieHandleWebhook.mockImplementation(async (payload) =>
    payload?.id === 'tr_1'
      ? { valid: true, payment: { id: 'tr_1', status: 'paid' } }
      : { valid: false, reason: 'missing payment id' },
  );

  flutterwaveInitialize.mockResolvedValue({
    id: 'flw_1',
    link: 'https://flutterwave.test/pay',
    status: 'pending',
    mock: true,
  });
  flutterwaveVerify.mockResolvedValue({ id: 12345, status: 'successful', tx_ref: 'flw_ref' });
  flutterwaveHandleWebhook.mockImplementation((_event, hash) => ({
    valid: hash === 'flw-valid-hash',
  }));

  squareCreate.mockResolvedValue({ id: 'sq_1', status: 'APPROVED', mock: true });
  squareHandleWebhook.mockImplementation(async (_event, options = {}) => ({
    valid:
      options.signature === 'square-valid-signature' &&
      options.notificationUrl === NOTIFY_URL &&
      typeof options.rawBody === 'string' &&
      options.rawBody.length > 0,
  }));

  mpCreatePreference.mockResolvedValue({
    id: 'pref_1',
    init_point: 'https://mp.test/checkout',
    mock: true,
  });
  mpHandleWebhook.mockImplementation(async (event, headers = {}) => ({
    valid:
      headers['x-signature'] === 'ts=1700000000,v1=valid' && Boolean(event?.data?.id),
  }));

  liqpayCreateForm.mockResolvedValue({
    publicKey: 'liq_pk',
    action: 'https://liqpay.test/checkout',
    data: 'data-b64',
    sign: 'sign-b64',
    mock: true,
  });
  liqpayHandleCallback.mockImplementation(async ({ sign }) =>
    sign === 'valid-sign'
      ? { status: 'success', order_id: 'ORD-1001' }
      : { error: 'Invalid signature' },
  );

  paytmInitiate.mockResolvedValue({
    txnId: 'paytm_txn_1',
    txnToken: 'paytm-token',
    redirectURL: 'https://paytm.test/pay',
    mock: true,
  });
  paytmHandleCallback.mockImplementation((params = {}) => ({
    valid: params.CHECKSUMHASH === 'valid-checksum',
    params,
  }));

  bkashCreate.mockResolvedValue({
    paymentID: 'bk_1',
    checkoutURL: 'https://bkash.test/checkout',
    mock: true,
  });
  bkashExecute.mockResolvedValue({ success: true, paymentID: 'bk_1' });
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (envSnapshot[key] === undefined) delete process.env[key];
    else process.env[key] = envSnapshot[key];
  }
});

// ── Creation routes ──────────────────────────────────────────────────────

describe('gateway creation routes', () => {
  it('creates a Mollie payment from the stored order total', async () => {
    const res = await request(app)
      .post('/api/payments/mollie/create')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'tr_1',
      checkoutUrl: 'https://mollie.test/checkout',
      mock: true,
    });
    expect(mollieCreatePayment).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 42.5,
        currency: 'USD',
        metadata: { userId: '7', orderId: 'order_owned' },
        webhookUrl: 'https://api.test/api/payments/mollie/webhook',
        redirectUrl: 'https://shop.test/checkout/success',
      }),
    );
  });

  it('returns 404 for an unknown order', async () => {
    const res = await request(app)
      .post('/api/payments/mollie/create')
      .send({ orderId: 'order_missing' });

    expect(res.status).toBe(404);
    expect(res.body.success).toBe(false);
    expect(mollieCreatePayment).not.toHaveBeenCalled();
  });

  it('initializes a Flutterwave transaction', async () => {
    const res = await request(app)
      .post('/api/payments/flutterwave/initialize')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'flw_1',
      checkoutUrl: 'https://flutterwave.test/pay',
      txRef: 'ORD-1001',
      mock: true,
    });
    expect(flutterwaveInitialize).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 42.5,
        currency: 'USD',
        email: 'buyer@example.com',
        txRef: 'ORD-1001',
        meta: { userId: '7', orderId: 'order_owned' },
      }),
    );
  });

  it('verifies a Flutterwave transaction by id', async () => {
    const res = await request(app).get('/api/payments/flutterwave/verify/12345');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, id: 12345, status: 'successful' });
    expect(flutterwaveVerify).toHaveBeenCalledWith({ transactionId: '12345' });
  });

  it('creates a Square payment from the stored order total', async () => {
    const res = await request(app)
      .post('/api/payments/square/create')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, id: 'sq_1', mock: true });
    expect(squareCreate).toHaveBeenCalledWith(
      expect.objectContaining({ amount: 42.5, currency: 'USD' }),
    );
  });

  it('creates a Mercado Pago preference priced at the order total', async () => {
    const res = await request(app)
      .post('/api/payments/mercadopago/create-preference')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'pref_1',
      preferenceId: 'pref_1',
      checkoutUrl: 'https://mp.test/checkout',
      mock: true,
    });
    const args = mpCreatePreference.mock.calls[0][0];
    expect(args.items).toEqual([
      {
        id: 'order_owned',
        title: 'Order ORD-1001',
        quantity: 1,
        unit_price: 42.5,
        currency_id: 'USD',
      },
    ]);
  });

  it('builds a signed LiqPay checkout form', async () => {
    const res = await request(app)
      .post('/api/payments/liqpay/create-form')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'order_owned',
      checkoutUrl: 'https://liqpay.test/checkout',
      action: 'https://liqpay.test/checkout',
      publicKey: 'liq_pk',
      data: 'data-b64',
      sign: 'sign-b64',
      mock: true,
    });
    expect(liqpayCreateForm).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 42.5,
        currency: 'USD',
        orderId: 'ORD-1001',
        serverUrl: 'https://api.test/api/payments/liqpay/callback',
      }),
    );
  });

  it('initiates a Paytm transaction', async () => {
    const res = await request(app)
      .post('/api/payments/paytm/initiate')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'paytm_txn_1',
      txnToken: 'paytm-token',
      redirectURL: 'https://paytm.test/pay',
      checkoutUrl: 'https://paytm.test/pay',
      mock: true,
    });
    expect(paytmInitiate).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 42.5,
        orderId: 'ORD-1001',
        callbackUrl: 'https://api.test/api/payments/paytm/callback',
      }),
    );
  });

  it('creates a bKash payment', async () => {
    const res = await request(app)
      .post('/api/payments/bkash/create')
      .send({ orderId: 'order_owned', amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      success: true,
      id: 'bk_1',
      paymentID: 'bk_1',
      checkoutUrl: 'https://bkash.test/checkout',
      mock: true,
    });
    expect(bkashCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        amount: 42.5,
        orderId: 'order_owned',
        callbackUrl: 'https://shop.test/checkout/bkash/callback',
      }),
    );
  });

  it.each([
    ['Mollie', '/api/payments/mollie/create', mollieCreatePayment],
    ['Flutterwave', '/api/payments/flutterwave/initialize', flutterwaveInitialize],
    ['Square', '/api/payments/square/create', squareCreate],
    ['Mercado Pago', '/api/payments/mercadopago/create-preference', mpCreatePreference],
    ['LiqPay', '/api/payments/liqpay/create-form', liqpayCreateForm],
    ['Paytm', '/api/payments/paytm/initiate', paytmInitiate],
    ['bKash', '/api/payments/bkash/create', bkashCreate],
  ])('%s rejects a foreign order with 403', async (_gateway, path, serviceSpy) => {
    const res = await request(app).post(path).send({ orderId: 'order_foreign' });

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Not authorized for this order' });
    expect(serviceSpy).not.toHaveBeenCalled();
  });

  it('rejects a creation request without a positive amount', async () => {
    const res = await request(app).post('/api/payments/mollie/create').send({ amount: 0 });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(mollieCreatePayment).not.toHaveBeenCalled();
  });
});

// ── Webhooks / callbacks ─────────────────────────────────────────────────

describe('Mollie webhook', () => {
  it('accepts an id whose status is re-fetched successfully', async () => {
    const res = await request(app)
      .post('/api/payments/mollie/webhook')
      .type('form')
      .send({ id: 'tr_1' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(mollieHandleWebhook).toHaveBeenCalledWith({ id: 'tr_1' });
  });

  it('returns 401 when the payment cannot be verified', async () => {
    const res = await request(app)
      .post('/api/payments/mollie/webhook')
      .type('form')
      .send({ id: 'tr_forged' });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when the webhook carries no id', async () => {
    const res = await request(app).post('/api/payments/mollie/webhook').type('form').send({});

    expect(res.status).toBe(401);
    expect(mollieHandleWebhook).toHaveBeenCalledWith({});
  });
});

describe('Flutterwave webhook', () => {
  const payload = JSON.stringify({ event: 'charge.success', data: { id: 12345 } });

  it('accepts a valid verif-hash and passes the parsed event', async () => {
    const res = await request(app)
      .post('/api/payments/flutterwave/webhook')
      .set('Content-Type', 'application/json')
      .set('verif-hash', 'flw-valid-hash')
      .send(payload);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(flutterwaveHandleWebhook).toHaveBeenCalledWith(
      { event: 'charge.success', data: { id: 12345 } },
      'flw-valid-hash',
    );
  });

  it('returns 401 for an invalid verif-hash', async () => {
    const res = await request(app)
      .post('/api/payments/flutterwave/webhook')
      .set('Content-Type', 'application/json')
      .set('verif-hash', 'wrong-hash')
      .send(payload);

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when verif-hash is missing', async () => {
    const res = await request(app)
      .post('/api/payments/flutterwave/webhook')
      .set('Content-Type', 'application/json')
      .send(payload);

    expect(res.status).toBe(401);
    expect(flutterwaveHandleWebhook).not.toHaveBeenCalled();
  });
});

describe('Square webhook', () => {
  const event = {
    type: 'payment.created',
    data: { object: { payment: { id: 'sq_1' } } },
  };
  const payload = JSON.stringify(event);

  it('accepts a valid signature and passes the raw body + notification URL', async () => {
    const res = await request(app)
      .post('/api/payments/square/webhook')
      .set('Content-Type', 'application/json')
      .set('x-square-hmacsha256-signature', 'square-valid-signature')
      .send(payload);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(squareHandleWebhook).toHaveBeenCalledWith(event, {
      signature: 'square-valid-signature',
      rawBody: payload,
      notificationUrl: NOTIFY_URL,
    });
  });

  it('returns 401 for an invalid signature', async () => {
    const res = await request(app)
      .post('/api/payments/square/webhook')
      .set('Content-Type', 'application/json')
      .set('x-square-hmacsha256-signature', 'not-the-signature')
      .send(payload);

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when the signature header is missing', async () => {
    const res = await request(app)
      .post('/api/payments/square/webhook')
      .set('Content-Type', 'application/json')
      .send(payload);

    expect(res.status).toBe(401);
    expect(squareHandleWebhook).not.toHaveBeenCalled();
  });
});

describe('Mercado Pago webhook', () => {
  const event = { action: 'payment.created', type: 'payment', data: { id: 'mp_pay_1' } };
  const payload = JSON.stringify(event);

  it('accepts a valid x-signature', async () => {
    const res = await request(app)
      .post('/api/payments/mercadopago/webhook')
      .set('Content-Type', 'application/json')
      .set('x-signature', 'ts=1700000000,v1=valid')
      .set('x-request-id', 'req-1')
      .send(payload);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(mpHandleWebhook).toHaveBeenCalledWith(
      event,
      expect.objectContaining({
        'x-signature': 'ts=1700000000,v1=valid',
        'x-request-id': 'req-1',
      }),
    );
  });

  it('returns 401 for an invalid x-signature', async () => {
    const res = await request(app)
      .post('/api/payments/mercadopago/webhook')
      .set('Content-Type', 'application/json')
      .set('x-signature', 'ts=1700000000,v1=forged')
      .send(payload);

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when x-signature is missing', async () => {
    const res = await request(app)
      .post('/api/payments/mercadopago/webhook')
      .set('Content-Type', 'application/json')
      .send(payload);

    expect(res.status).toBe(401);
    expect(mpHandleWebhook).not.toHaveBeenCalled();
  });
});

describe('LiqPay callback', () => {
  it('accepts a valid data/sign pair', async () => {
    const res = await request(app)
      .post('/api/payments/liqpay/callback')
      .type('form')
      .send({ data: 'payload-b64', sign: 'valid-sign' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(liqpayHandleCallback).toHaveBeenCalledWith({
      data: 'payload-b64',
      sign: 'valid-sign',
    });
  });

  it('returns 401 for an invalid signature', async () => {
    const res = await request(app)
      .post('/api/payments/liqpay/callback')
      .type('form')
      .send({ data: 'payload-b64', sign: 'bad-sign' });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when sign is missing', async () => {
    const res = await request(app)
      .post('/api/payments/liqpay/callback')
      .type('form')
      .send({ data: 'payload-b64' });

    expect(res.status).toBe(401);
    expect(liqpayHandleCallback).not.toHaveBeenCalled();
  });
});

describe('Paytm callback', () => {
  const params = {
    ORDERID: 'ORD-1001',
    STATUS: 'TXN_SUCCESS',
    CHECKSUMHASH: 'valid-checksum',
  };

  it('accepts a valid CHECKSUMHASH', async () => {
    const res = await request(app)
      .post('/api/payments/paytm/callback')
      .type('form')
      .send(params);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(paytmHandleCallback).toHaveBeenCalledWith(params);
  });

  it('returns 401 for an invalid CHECKSUMHASH', async () => {
    const res = await request(app)
      .post('/api/payments/paytm/callback')
      .type('form')
      .send({ ...params, CHECKSUMHASH: 'forged' });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it('returns 401 when CHECKSUMHASH is missing', async () => {
    const res = await request(app)
      .post('/api/payments/paytm/callback')
      .type('form')
      .send({ ORDERID: 'ORD-1001', STATUS: 'TXN_SUCCESS' });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });
});

describe('bKash callback', () => {
  it('confirms the payment through the execute endpoint', async () => {
    const res = await request(app)
      .post('/api/payments/bkash/callback')
      .type('form')
      .send({ paymentID: 'bk_1', status: 'success' });

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(bkashExecute).toHaveBeenCalledWith({ paymentId: 'bk_1', callbackType: 'payment' });
  });

  it('accepts the GET redirect with query params', async () => {
    const res = await request(app).get(
      '/api/payments/bkash/callback?paymentID=bk_1&status=success',
    );

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(bkashExecute).toHaveBeenCalledWith({ paymentId: 'bk_1', callbackType: 'payment' });
  });

  it('returns 400 when bKash reports the payment did not complete', async () => {
    bkashExecute.mockResolvedValueOnce({ success: false, paymentID: 'bk_1' });

    const res = await request(app)
      .post('/api/payments/bkash/callback')
      .type('form')
      .send({ paymentID: 'bk_1', status: 'success' });

    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
  });

  it('returns 400 when paymentID is missing', async () => {
    const res = await request(app)
      .post('/api/payments/bkash/callback')
      .type('form')
      .send({ status: 'success' });

    expect(res.status).toBe(400);
    expect(bkashExecute).not.toHaveBeenCalled();
  });
});
