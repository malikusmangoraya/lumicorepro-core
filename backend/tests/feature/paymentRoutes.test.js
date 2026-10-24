/**
 * Feature tests — routes/payment.routes.js (Stripe / PayPal / Paddle / Razorpay).
 *
 * The router is mounted exactly like server.js (raw body parsers BEFORE
 * express.json for every webhook path) with the DB layer replaced by the
 * in-memory Sequelize doubles, so these tests assert what actually reached the
 * query and what actually changed in the stored rows — not just the status code.
 *
 * The Stripe/PayPal ingress middleware is the REAL
 * middleware/webhookSecurity.js (only its Redis/ledger/model deps are doubled),
 * so signature rejection and event idempotency are genuinely exercised here.
 *
 * Every defect this suite once pinned with `it.failing(...)` is fixed in
 * routes/payment.routes.js (2026-10-23) and enforced by a normal test — there
 * is no expected-failure marker left here. Do not add one back: a documented
 * gap must end as a fix plus an enforced assertion, not a placeholder that
 * reports green while the bug ships.
 */
import express from 'express';
import request from 'supertest';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { createFakeModel, createFakeSequelize, matchesWhere } from '../helpers/sequelizeFakes.js';

const USER = { id: 7, role: 'user', email: 'buyer@example.com' };
const ADMIN = { id: 3, role: 'admin', email: 'ops@example.com' };
const VALID_STRIPE_SIG = 't=1700000000,v1=good-sig';
const UNCONFIGURED_MESSAGE =
  'Payment system unconfigured. Please insert your keys in the Admin Settings panel.';

/** Mutated by each test; `protect` copies it onto req.user. */
let currentUser = { ...USER };
/** Live Stripe client returned by services/payment/dynamic.js (null = unconfigured). */
let currentStripeClient = null;
let stripeReady = true;

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

const models = {};
const delegate = (key) =>
  new Proxy(
    {},
    {
      get: (_target, prop) => {
        const model = models[key];
        return model ? model[prop] : undefined;
      },
    },
  );

for (const name of ['Order', 'Payment', 'Notification', 'Plan', 'User', 'Subscription']) {
  jest.unstable_mockModule(`../../models/${name}.js`, () => ({
    __esModule: true,
    default: delegate(name),
  }));
}

jest.unstable_mockModule('../../models/WebhookEvent.js', () => ({
  __esModule: true,
  default: delegate('WebhookEvent'),
}));

jest.unstable_mockModule('../../middleware/auth.js', () => ({
  __esModule: true,
  protect: (req, _res, next) => {
    req.user = { ...currentUser };
    next();
  },
  // Mirrors middleware/auth.js:148-158 so role gates are really enforced.
  authorize: (...roles) => (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: `User role '${req.user?.role}' is not authorized to access this route`,
      });
    }
    return next();
  },
  optionalProtect: (req, _res, next) => {
    req.user = { ...currentUser };
    next();
  },
}));

jest.unstable_mockModule('../../middleware/rateLimit.js', () => {
  const passthrough = (_req, _res, next) => next();
  return { __esModule: true, paymentLimiter: passthrough, apiLimiter: passthrough };
});

const fakeSequelize = createFakeSequelize();
jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: fakeSequelize,
  default: { sequelize: fakeSequelize },
}));

const dynamic = {
  getStripeClient: jest.fn(),
  getStripeWebhookSecret: jest.fn(),
  getStripePublishableKey: jest.fn(),
  getGatewayRuntimeConfig: jest.fn(),
  gatewayReady: jest.fn(),
  UNCONFIGURED_MESSAGE,
};
jest.unstable_mockModule('../../services/payment/dynamic.js', () => ({ __esModule: true, ...dynamic }));

const stripeService = {
  verifyPaymentIntent: jest.fn(),
  refund: jest.fn(),
  createPayment: jest.fn(),
  createCheckoutSession: jest.fn(),
  createPortalSession: jest.fn(),
  handleWebhook: jest.fn(),
};
const paypalService = {
  createOrder: jest.fn(),
  captureOrder: jest.fn(),
  handleWebhook: jest.fn(),
  refund: jest.fn(),
  getWebhookId: jest.fn(),
  verifyWebhookSignature: jest.fn(),
};
const paddleService = {
  createCheckout: jest.fn(),
  verifyWebhook: jest.fn(),
  handleWebhook: jest.fn(),
  refund: jest.fn(),
};
const razorpayService = {
  createOrder: jest.fn(),
  verifyPayment: jest.fn(),
  handleWebhook: jest.fn(),
  refund: jest.fn(),
  getKeyId: jest.fn(),
};

for (const [file, svc] of [
  ['stripe', stripeService],
  ['paypal', paypalService],
  ['paddle', paddleService],
  ['razorpay', razorpayService],
]) {
  jest.unstable_mockModule(`../../services/payment/${file}.service.js`, () => ({
    __esModule: true,
    default: svc,
  }));
}

const systemConfig = { get: jest.fn(), getPublicConfig: jest.fn() };
jest.unstable_mockModule('../../services/systemConfig.service.js', () => ({
  __esModule: true,
  default: systemConfig,
}));

const aiAgent = {
  AI_AGENT_TIMEOUTS: { status: 5000, quick: 2000 },
  agentEndpointUrl: (path) => `https://agent.test${path}`,
  fetchWithTimeout: jest.fn(),
};
jest.unstable_mockModule('../../utils/aiAgent.js', () => ({ __esModule: true, ...aiAgent }));

// Redis fast-path + durable ledger doubles for the real webhookSecurity middleware.
const redisStore = new Map();
const fakeRedis = {
  get: async (key) => (redisStore.has(key) ? redisStore.get(key) : null),
  set: async (key, value) => {
    redisStore.set(key, value);
    return 'OK';
  },
  incrby: async () => 0,
  expire: async () => 1,
};
jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  __esModule: true,
  getRedis: () => fakeRedis,
  isRedisAvailable: () => true,
}));

const { default: paymentRoutes } = await import('../../routes/payment.routes.js');

// ── App: same body-parser order as server.js:154-211 ─────────────────────
const app = express();
for (const path of [
  '/api/payments/webhook',
  '/api/payments/paypal/webhook',
  '/api/payments/paddle/webhook',
  '/api/payments/razorpay/webhook',
]) {
  app.use(path, express.raw({ type: 'application/json' }));
}
app.use(express.json({ limit: '10mb' }));
app.use('/api/payments', paymentRoutes);
app.use((err, _req, res, _next) => {
  res.status(err.statusCode || 500).json({ success: false, error: err.message });
});

// ── Fixtures ─────────────────────────────────────────────────────────────

// Numbers keep the shared fixture readable; utils/invoiceGenerator.js coerces
// with money() either way, and the "DECIMAL strings" test at the bottom of this
// file pins what real PostgreSQL rows (models/Order.js:50-72) actually return.
const orderRow = (overrides = {}) => ({
  id: 1,
  user_id: 7,
  org_id: null,
  orderNumber: 'ORD-1001',
  totalPrice: 42.5,
  currency: 'USD',
  status: 'pending',
  isPaid: false,
  paidAt: null,
  paymentResult: null,
  paymentMethod: 'stripe',
  items: [{ title: 'Keyboard', price: 20, quantity: 2, selectedColor: null, selectedSize: null }],
  itemsPrice: 40,
  taxPrice: 2.5,
  shippingPrice: 0,
  createdAt: new Date('2026-01-05T10:00:00Z'),
  shippingAddress: { fullName: 'Ada L', street: '1 Main', city: 'Karachi', state: 'SD', zipCode: '75000', country: 'PK' },
  ...overrides,
});

const paymentRow = (overrides = {}) => ({
  id: 5,
  user_id: 7,
  order_id: 1,
  provider: 'stripe',
  stripePaymentIntentId: 'pi_live_9',
  stripeChargeId: null,
  gatewayPaymentId: null,
  amount: '100.00',
  currency: 'usd',
  status: 'succeeded',
  paymentMethod: 'card',
  cardDetails: null,
  refundAmount: '0.00',
  refundReason: '',
  errorMessage: '',
  ...overrides,
});

/** Sequelize's findOrCreate is not part of the shared fake; add it locally. */
function attachFindOrCreate(model) {
  model.findOrCreate = async ({ where = {}, defaults = {} } = {}) => {
    model.calls.push({ method: 'findOrCreate', options: { where, defaults } });
    const existing = model.rows.find((row) => matchesWhere(row, where));
    if (existing) return [existing, false];
    const created = await model.create({ ...where, ...defaults });
    return [created, true];
  };
  return model;
}

function seed(overrides = {}) {
  models.Order = createFakeModel('Order', overrides.orders || [orderRow(), orderRow({ id: 2, user_id: 99, orderNumber: 'ORD-1002', totalPrice: 500, itemsPrice: 500, taxPrice: 0, shippingPrice: 0 })]);
  models.Payment = createFakeModel('Payment', overrides.payments || []);
  models.Notification = createFakeModel('Notification', []);
  models.Plan = createFakeModel('Plan', overrides.plans || []);
  models.User = createFakeModel('User', overrides.users || [{ id: 7, stripeCustomerId: null }]);
  models.Subscription = attachFindOrCreate(createFakeModel('Subscription', overrides.subscriptions || []));

  models.WebhookEvent = attachFindOrCreate(createFakeModel('WebhookEvent', []));
}

/**
 * `index` is an explicit position in the matched list; omitted means "the last
 * one", i.e. the write that actually stuck.
 */
const findCall = (model, method, index) => {
  const matched = model.calls.filter((c) => c.method === method);
  return (index === undefined ? matched[matched.length - 1] : matched[index]) || null;
};

/** Where clause of a model-level `update(values, options)` call. */
const updateWhereOf = (model, method = 'update') => {
  const call = findCall(model, method);
  return call ? call.options.options?.where ?? call.options.where : null;
};

function makeStripeClient(intentId = 'pi_live_1') {
  return {
    paymentIntents: {
      create: jest.fn(async (params) => ({
        id: params.id ?? intentId,
        client_secret: `${intentId}_secret_abc`,
        ...params,
      })),
    },
    webhooks: {
      constructEvent: (raw, signature) => {
        if (signature !== VALID_STRIPE_SIG) {
          throw new Error('No signatures found matching the expected signature for payload');
        }
        return JSON.parse(Buffer.isBuffer(raw) ? raw.toString('utf8') : String(raw));
      },
    },
  };
}

const stripeEvent = (id, type, object) => ({
  id,
  type,
  data: { object },
});

/**
 * The Stripe webhook handler used to be `async (req, res)` with no try/catch and
 * no `next`. Express 4 discards the returned promise, so any fulfilment error
 * (DB down, gateway throw) produced BOTH a request that is never answered —
 * verified: supertest hung past the 5 s test timeout — and a process-level
 * unhandled rejection that jest-circus attributed to whichever test was running.
 * Since 2026-10-23 the handler wraps its work and answers 500 without writing the
 * idempotency ledger, so a failing delivery is retried by the provider instead of
 * silently committed. `postWebhook` below exercises that guarded path.
 */

const postWebhook = (event, signature = VALID_STRIPE_SIG) =>
  request(app)
    .post('/api/payments/webhook')
    .set('Content-Type', 'application/json')
    .set('stripe-signature', signature)
    .send(JSON.stringify(event));

const ENV_KEYS = [
  'FRONTEND_URL',
  'BACKEND_URL',
  'DEFAULT_CURRENCY',
  'PAYMENT_GATEWAYS_ENABLED',
  'RAZORPAY_KEY_ID',
  'PADDLE_ENV',
  'STRIPE_WEBHOOK_SECRET',
];
let envSnapshot = {};

beforeEach(() => {
  envSnapshot = Object.fromEntries(ENV_KEYS.map((k) => [k, process.env[k]]));
  process.env.FRONTEND_URL = 'https://shop.test';
  process.env.BACKEND_URL = 'https://api.test';
  delete process.env.DEFAULT_CURRENCY;
  delete process.env.PAYMENT_GATEWAYS_ENABLED;
  delete process.env.RAZORPAY_KEY_ID;
  delete process.env.STRIPE_WEBHOOK_SECRET;

  currentUser = { ...USER };
  currentStripeClient = null;
  stripeReady = true;
  redisStore.clear();
  seed();

  // `resetMocks: true` strips module-scope implementations, so they bind here.
  dynamic.getStripeClient.mockImplementation(async () => currentStripeClient);
  dynamic.getStripeWebhookSecret.mockResolvedValue('whsec_test');
  dynamic.getStripePublishableKey.mockResolvedValue('pk_test_1');
  dynamic.gatewayReady.mockImplementation(async () =>
    stripeReady ? { ok: true } : { ok: false, message: UNCONFIGURED_MESSAGE },
  );
  dynamic.getGatewayRuntimeConfig.mockImplementation(async (gateway) =>
    gateway === 'stripe'
      ? { enabled: true, publishableKey: 'pk_live_runtime', mode: 'live' }
      : { enabled: false, clientId: '', mode: 'sandbox', webhookId: '' },
  );

  systemConfig.getPublicConfig.mockResolvedValue({ business: { name: 'Acme' }, currency: {} });

  stripeService.verifyPaymentIntent.mockResolvedValue({ status: 'succeeded', succeeded: true, mock: true });
  stripeService.refund.mockResolvedValue({ success: true, refundId: 're_1' });
  stripeService.createPayment.mockResolvedValue({ id: 'pi_svc_1', clientSecret: 'pi_svc_1_secret' });
  stripeService.createCheckoutSession.mockResolvedValue({ id: 'cs_1', url: 'https://stripe.test/pay', customerId: 'cus_9' });
  stripeService.createPortalSession.mockResolvedValue({ url: 'https://stripe.test/portal' });
  stripeService.handleWebhook.mockResolvedValue({ handled: true });

  paypalService.createOrder.mockResolvedValue({ id: 'PO-1', approvalUrl: 'https://paypal.test/approve', mock: true });
  paypalService.captureOrder.mockResolvedValue({ success: true, captureId: 'CAP-1', status: 'COMPLETED' });
  paypalService.handleWebhook.mockResolvedValue({ handled: true });
  paypalService.refund.mockResolvedValue({ success: true, refundId: 'PAYRE-1' });
  paypalService.getWebhookId.mockResolvedValue('whk_1');
  paypalService.verifyWebhookSignature.mockResolvedValue(true);

  paddleService.createCheckout.mockResolvedValue({ id: 'txn_1', checkoutUrl: 'https://paddle.test/pay', mock: true });
  paddleService.verifyWebhook.mockImplementation((rawBody, signature) => signature === 'paddle-valid' && rawBody.length > 0);
  paddleService.handleWebhook.mockResolvedValue({ handled: true });
  // Mirrors services/payment/paddle.service.js:130-134 — full refunds only.
  paddleService.refund.mockImplementation(async ({ amount }) => {
    if (amount !== undefined && amount !== null) {
      throw new Error('Paddle integration supports full refunds only');
    }
    return { success: true, adjustmentId: 'adj_1' };
  });

  razorpayService.createOrder.mockResolvedValue({ id: 'order_rzp', amount: 4250, currency: 'INR', mock: true });
  razorpayService.verifyPayment.mockResolvedValue(true);
  razorpayService.handleWebhook.mockImplementation((event, signature) =>
    Promise.resolve(signature === 'rzp-valid' ? { valid: true } : { valid: false }),
  );
  razorpayService.refund.mockResolvedValue({ success: true, refundId: 'rfp_1' });
  razorpayService.getKeyId.mockReturnValue('rzp_test_key');

  aiAgent.fetchWithTimeout.mockResolvedValue({ ok: true, json: async () => ({ credited: true }) });
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (envSnapshot[key] === undefined) delete process.env[key];
    else process.env[key] = envSnapshot[key];
  }
});

// ══════════════════════════════════════════════════════════════════════════
describe('GET /config', () => {
  it('exposes runtime currency, publishable key and gateway flags', async () => {
    systemConfig.getPublicConfig.mockResolvedValue({
      business: { name: 'Acme Store' },
      currency: { code: 'pkr' },
    });

    const res = await request(app).get('/api/payments/config');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: true,
      configured: true,
      unconfiguredMessage: UNCONFIGURED_MESSAGE,
      defaultCurrency: 'PKR',
      business: { name: 'Acme Store' },
      isLive: true,
    });
    expect(res.body.gateways.stripe).toMatchObject({ enabled: true, publishableKey: 'pk_live_runtime' });
    expect(res.body.gateways.paypal).toMatchObject({ enabled: false, clientId: '' });
    expect(res.body.supportedCurrencies).toContain('PKR');
  });

  it('falls back to DEFAULT_CURRENCY then USD, and keeps non-whitelisted gateways off', async () => {
    process.env.RAZORPAY_KEY_ID = 'rzp_live_key';
    process.env.DEFAULT_CURRENCY = 'aed';

    const res = await request(app).get('/api/payments/config');

    expect(res.body.defaultCurrency).toBe('AED');
    // services/payment/config.js:134 launch-whitelists the UI to stripe+paypal.
    expect(res.body.gateways.razorpay.enabled).toBe(false);

    process.env.PAYMENT_GATEWAYS_ENABLED = 'all';
    const open = await request(app).get('/api/payments/config');
    expect(open.body.gateways.razorpay.enabled).toBe(true);
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /create-intent', () => {
  it('charges the stored order total, not the amount the client claims', async () => {
    currentStripeClient = makeStripeClient();
    const res = await request(app)
      .post('/api/payments/create-intent')
      .send({ orderId: 1, amount: 0.01, currency: 'EUR' });

    expect(res.status).toBe(200);
    expect(currentStripeClient.paymentIntents.create).toHaveBeenCalledWith({
      amount: 4250,
      currency: 'usd',
      metadata: { userId: '7', orderId: '1', paymentMethod: 'card' },
    });
    const created = models.Payment.calls.find((c) => c.method === 'create');
    expect(created.options.values).toMatchObject({
      user_id: 7,
      order_id: 1,
      amount: 42.5,
      currency: 'usd',
      status: 'pending',
      provider: 'stripe',
    });
    expect(res.body).toMatchObject({ success: true, paymentIntentId: 'pi_live_1', amount: 42.5 });
  });

  it('reports the currency it actually charged — echoes the order currency, not the client claim (fixed 2026-10-23, routes/payment.routes.js create-intent)',
    async () => {
      currentStripeClient = makeStripeClient();

      const res = await request(app)
        .post('/api/payments/create-intent')
        .send({ orderId: 1, amount: 1, currency: 'EUR' });

      expect(res.body.currency).toBe('usd');
    },
  );

  it('derives the currency from the order, falling back to DEFAULT_CURRENCY', async () => {
    process.env.DEFAULT_CURRENCY = 'aed';
    currentStripeClient = makeStripeClient();
    models.Order.rows[0].currency = null;

    await request(app).post('/api/payments/create-intent').send({ orderId: 1 });

    expect(currentStripeClient.paymentIntents.create).toHaveBeenCalledWith(
      expect.objectContaining({ currency: 'aed' }),
    );
  });

  it('refuses user B orders presented by user A (IDOR)', async () => {
    currentStripeClient = makeStripeClient();

    const res = await request(app)
      .post('/api/payments/create-intent')
      .send({ orderId: 2, amount: 1 });

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Not authorized for this order' });
    expect(currentStripeClient.paymentIntents.create).not.toHaveBeenCalled();
    expect(models.Payment.calls).toEqual([]);
  });

  it('lets an admin create an intent against another user order', async () => {
    currentUser = { ...ADMIN };
    currentStripeClient = makeStripeClient();

    const res = await request(app).post('/api/payments/create-intent').send({ orderId: 2 });

    expect(res.status).toBe(200);
    const created = models.Payment.calls.find((c) => c.method === 'create');
    expect(created.options.values.order_id).toBe(2);
    expect(created.options.values.amount).toBe(500);
  });

  it('404s an unknown order before touching the gateway', async () => {
    currentStripeClient = makeStripeClient();

    const res = await request(app).post('/api/payments/create-intent').send({ orderId: 404, amount: 10 });

    expect(res.status).toBe(404);
    expect(currentStripeClient.paymentIntents.create).not.toHaveBeenCalled();
    expect(models.Payment.calls).toEqual([]);
  });

  it.each([0, -1, -0.01])('rejects a non-positive amount (%s)', async (amount) => {
    const res = await request(app).post('/api/payments/create-intent').send({ amount });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Valid amount is required' });
    expect(models.Payment.calls).toEqual([]);
  });

  it('rejects a NaN amount derived from an unreadable order total', async () => {
    models.Order.rows[0].totalPrice = 'not-a-price';

    const res = await request(app).post('/api/payments/create-intent').send({ orderId: 1 });

    expect(res.status).toBe(400);
    expect(models.Payment.calls).toEqual([]);
  });

  it('rejects a non-numeric amount string instead of charging Math.round(NaN*100) (fixed 2026-10-23)',
    async () => {
      currentStripeClient = makeStripeClient();

      const res = await request(app).post('/api/payments/create-intent').send({ amount: 'ten' });

      expect(res.status).toBe(400);
      expect(models.Payment.calls).toEqual([]);
    },
  );

  it('creates a mock intent when Stripe is unconfigured and records nothing', async () => {
    stripeReady = false;

    const res = await request(app).post('/api/payments/create-intent').send({ orderId: 1 });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: false,
      code: 'PAYMENT_UNCONFIGURED',
      message: UNCONFIGURED_MESSAGE,
      data: null,
    });
    // The duplicate-payment guard reads the ledger, so a findOne is expected —
    // what must never happen on an unconfigured gateway is a stored payment.
    expect(models.Payment.calls.filter((c) => c.method !== 'findOne')).toEqual([]);
  });

  it('mints a pi_mock intent in developer mode and persists it as pending', async () => {
    const res = await request(app).post('/api/payments/create-intent').send({ orderId: 1 });

    expect(res.status).toBe(200);
    expect(res.body.paymentIntentId).toMatch(/^pi_mock_/);
    const created = models.Payment.calls.find((c) => c.method === 'create');
    expect(created.options.values.stripePaymentIntentId).toBe(res.body.paymentIntentId);
  });

  it('refuses a second live intent for an order that already has a pending payment (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5, order_id: 1, stripePaymentIntentId: 'pi_live_first', status: 'pending' })] });
      currentStripeClient = makeStripeClient('pi_live_second');

      const res = await request(app).post('/api/payments/create-intent').send({ orderId: 1 });

      expect(res.status).toBe(409);
      expect(currentStripeClient.paymentIntents.create).not.toHaveBeenCalled();
      expect(models.Payment.rows).toHaveLength(1);
    },
  );
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /confirm', () => {
  const confirmable = () =>
    seed({
      payments: [paymentRow({ id: 5, order_id: 1, stripePaymentIntentId: 'pi_live_9', status: 'pending' })],
    });

  it('marks payment and order paid in one transaction and notifies the owner', async () => {
    confirmable();

    const res = await request(app)
      .post('/api/payments/confirm')
      .send({ paymentIntentId: 'pi_live_9', orderId: 1, cardDetails: { charge: 'ch_1', last4: '4242' } });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, message: 'Payment confirmed successfully' });

    const payment = models.Payment.rows[0];
    expect(payment.status).toBe('succeeded');
    expect(payment.stripeChargeId).toBe('ch_1');
    expect(payment.cardDetails).toEqual({ charge: 'ch_1', last4: '4242' });

    const order = models.Order.rows[0];
    expect(order.isPaid).toBe(true);
    expect(order.status).toBe('processing');
    expect(order.paymentResult).toMatchObject({ id: 'pi_live_9', status: 'succeeded', emailAddress: 'buyer@example.com' });

    const note = models.Notification.calls.find((c) => c.method === 'create');
    expect(note.options.values).toMatchObject({
      recipient: 7,
      type: 'payment',
      message: 'Payment of $42.50 for order #ORD-1001 received.',
    });
  });

  it('refuses an order that carries no owner — confirm is the buyer\'s endpoint, not a free-for-all', async () => {
    confirmable();
    models.Order.rows[0].user_id = null;

    const res = await request(app)
      .post('/api/payments/confirm')
      .send({ paymentIntentId: 'pi_live_9', orderId: 1 });

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Not authorized for this order' });
    expect(models.Order.rows[0].isPaid).toBe(false);
    expect(models.Notification.calls).toEqual([]);
  });

  it('404s an unknown payment intent without touching any order', async () => {
    confirmable();

    const res = await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_never' });

    expect(res.status).toBe(404);
    expect(models.Order.rows[0].isPaid).toBe(false);
    expect(models.Notification.calls).toEqual([]);
  });

  it('refuses to mark an order paid when the gateway has not succeeded', async () => {
    confirmable();
    currentStripeClient = makeStripeClient();
    stripeService.verifyPaymentIntent.mockResolvedValue({ status: 'requires_payment_method', succeeded: false });

    const res = await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_live_9', orderId: 1 });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Payment not confirmed by gateway (status: requires_payment_method)');
    expect(models.Payment.rows[0].status).toBe('processing');
    expect(models.Order.rows[0].isPaid).toBe(false);
    expect(fakeSequelize._transaction).toBeDefined();
    expect(models.Notification.calls).toEqual([]);
  });

  it('records a gateway failure as failed, not as pending', async () => {
    confirmable();
    currentStripeClient = makeStripeClient();
    stripeService.verifyPaymentIntent.mockResolvedValue({ status: 'failed', succeeded: false });

    const res = await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_live_9' });

    expect(res.status).toBe(400);
    expect(models.Payment.rows[0].status).toBe('failed');
  });

  it('looks the payment up by its gateway id, scoped to the caller', async () => {
    confirmable();

    await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_live_9' });

    const call = models.Payment.whereCalls('findOne')[0];
    expect(call.where).toEqual({ stripePaymentIntentId: 'pi_live_9', user_id: 7 });
  });

  it('falls back to the payment order id when the client omits orderId', async () => {
    confirmable();

    const res = await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_live_9' });

    expect(res.status).toBe(200);
    expect(models.Order.rows[0].isPaid).toBe(true);
  });

  it('refuses to flip an order the caller does not own (fixed 2026-10-23 — confirm calls orderOwnershipError)',
    async () => {
      confirmable();
      models.Order.rows[1].user_id = 99;

      const res = await request(app)
        .post('/api/payments/confirm')
        .send({ paymentIntentId: 'pi_live_9', orderId: 2 });

      expect(res.status).toBe(403);
      expect(models.Order.rows[1].isPaid).toBe(false);
    },
  );

  it(
    'only confirms a payment belonging to the caller — the lookup is scoped by user_id (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5, user_id: 99, order_id: 2, stripePaymentIntentId: 'pi_victim', status: 'pending' })] });

      const res = await request(app).post('/api/payments/confirm').send({ paymentIntentId: 'pi_victim' });

      expect([401, 403, 404]).toContain(res.status);
      expect(models.Payment.rows[0].status).toBe('pending');
    },
  );
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /paypal/create-order', () => {
  it('prices the PayPal order from the stored total', async () => {
    const res = await request(app)
      .post('/api/payments/paypal/create-order')
      .send({ orderId: 1, amount: 0.01, currency: 'eur', description: 'Custom' });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      success: true,
      paypalOrderId: 'PO-1',
      approvalUrl: 'https://paypal.test/approve',
      mock: true,
    });
    expect(paypalService.createOrder).toHaveBeenCalledWith({
      amount: 42.5,
      currency: 'USD',
      orderId: 1,
      description: 'Custom',
    });
    const created = models.Payment.calls.find((c) => c.method === 'create');
    expect(created.options.values).toMatchObject({
      provider: 'paypal',
      stripePaymentIntentId: 'PO-1',
      amount: 42.5,
      status: 'pending',
    });
  });

  it(
    'charges and reports the order currency instead of the client claim (fixed 2026-10-23)',
    async () => {
      await request(app)
        .post('/api/payments/paypal/create-order')
        .send({ orderId: 1, amount: 1, currency: 'eur' });

      expect(paypalService.createOrder).toHaveBeenCalledWith(
        expect.objectContaining({ currency: 'USD' }),
      );
    },
  );

  it('rejects a foreign order with 403 and creates nothing', async () => {
    const res = await request(app).post('/api/payments/paypal/create-order').send({ orderId: 2 });

    expect(res.status).toBe(403);
    expect(paypalService.createOrder).not.toHaveBeenCalled();
    expect(models.Payment.calls).toEqual([]);
  });

  it('404s an unknown order and rejects a zero total', async () => {
    const missing = await request(app).post('/api/payments/paypal/create-order').send({ orderId: 77 });
    expect(missing.status).toBe(404);

    models.Order.rows[0].totalPrice = '0.00';
    const zero = await request(app).post('/api/payments/paypal/create-order').send({ orderId: 1 });
    expect(zero.status).toBe(400);
    expect(zero.body).toEqual({ success: false, error: 'Valid amount is required' });
  });
});

describe('POST /paypal/capture', () => {
  const pendingPaypal = () =>
    seed({ payments: [paymentRow({ id: 5, provider: 'paypal', stripePaymentIntentId: 'PO-1', order_id: 1, status: 'pending' })] });

  it('captures, records the capture id and marks the order paid', async () => {
    pendingPaypal();

    const res = await request(app).post('/api/payments/paypal/capture').send({ paypalOrderId: 'PO-1', orderId: 1 });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, message: 'Payment captured successfully' });
    expect(models.Payment.rows[0]).toMatchObject({
      status: 'succeeded',
      stripeChargeId: 'CAP-1',
      providerResponse: { paypalOrderId: 'PO-1', captureId: 'CAP-1', status: 'COMPLETED' },
    });
    expect(models.Order.rows[0].isPaid).toBe(true);
    expect(models.Notification.calls.find((c) => c.method === 'create').options.values.title).toBe(
      'PayPal Payment Successful',
    );
  });

  it('looks the payment up scoped to the paypal provider and the caller', async () => {
    pendingPaypal();

    await request(app).post('/api/payments/paypal/capture').send({ paypalOrderId: 'PO-1' });

    expect(models.Payment.whereCalls('findOne')[0].where).toEqual({
      stripePaymentIntentId: 'PO-1',
      provider: 'paypal',
      user_id: 7,
    });
  });

  it('records a declined capture as failed and leaves the order unpaid', async () => {
    pendingPaypal();
    paypalService.captureOrder.mockResolvedValue({ success: false, captureId: null, status: 'DENIED' });

    const res = await request(app).post('/api/payments/paypal/capture').send({ paypalOrderId: 'PO-1', orderId: 1 });

    expect(res.body.success).toBe(false);
    expect(models.Payment.rows[0].status).toBe('failed');
    expect(models.Order.rows[0].isPaid).toBe(false);
    expect(models.Notification.calls).toEqual([]);
  });

  it('requires the paypalOrderId and 404s an unknown payment', async () => {
    pendingPaypal();

    const missing = await request(app).post('/api/payments/paypal/capture').send({});
    expect(missing.status).toBe(400);

    const unknown = await request(app).post('/api/payments/paypal/capture').send({ paypalOrderId: 'PO-nope' });
    expect(unknown.status).toBe(404);
  });

  it(
    'never captures funds it cannot record — the Payment row is looked up before captureOrder (fixed 2026-10-23)',
    async () => {
      pendingPaypal();

      const res = await request(app).post('/api/payments/paypal/capture').send({ paypalOrderId: 'PO-orphan' });

      expect(res.status).toBe(404);
      expect(paypalService.captureOrder).not.toHaveBeenCalled();
    },
  );

  it(
    'refuses to flip a foreign order on capture (fixed 2026-10-23 — orderOwnershipError inside the transaction)',
    async () => {
      pendingPaypal();

      const res = await request(app)
        .post('/api/payments/paypal/capture')
        .send({ paypalOrderId: 'PO-1', orderId: 2 });

      expect(res.status).toBe(403);
      expect(models.Order.rows[1].isPaid).toBe(false);
    },
  );
});

describe('POST /paypal/webhook (real verification middleware)', () => {
  const event = { id: 'evt_pp_1', event_type: 'PAYMENT.CAPTURE.COMPLETED', resource: { id: 'CAP-1' } };

  const send = (body = JSON.stringify(event), signature = 'sig-1') =>
    request(app)
      .post('/api/payments/paypal/webhook')
      .set('Content-Type', 'application/json')
      .set('paypal-transmission-id', 'tx-1')
      .set('paypal-transmission-time', '2026-01-01T00:00:00Z')
      .set('paypal-transmission-sig', signature)
      .set('paypal-cert-url', 'https://paypal.test/cert')
      .set('paypal-auth-algo', 'SHA256withRSA')
      .send(body);

  it('acknowledges a verified event and commits it to the ledger', async () => {
    const res = await send();

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual({ received: true, eventId: 'evt_pp_1', handled: true });
    expect(paypalService.handleWebhook).toHaveBeenCalledWith(event);
    expect(paypalService.verifyWebhookSignature).toHaveBeenCalledWith(
      expect.objectContaining({ transmissionSig: 'sig-1', webhookId: 'whk_1', webhookEvent: event }),
    );
    expect(models.WebhookEvent.rows[0]).toMatchObject({ event_id: 'evt_pp_1', gateway: 'paypal' });
  });

  it('rejects an event whose signature PayPal does not confirm', async () => {
    paypalService.verifyWebhookSignature.mockResolvedValue(false);

    const res = await send();

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({ success: false, code: 'WEBHOOK_VERIFICATION_FAILED' });
    expect(paypalService.handleWebhook).not.toHaveBeenCalled();
    expect(models.WebhookEvent.calls).toEqual([]);
  });

  it('fails closed when PAYPAL_WEBHOOK_ID is not configured', async () => {
    paypalService.getWebhookId.mockResolvedValue('');

    const res = await send();

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({ success: false, code: 'WEBHOOK_NOT_CONFIGURED' });
    expect(paypalService.handleWebhook).not.toHaveBeenCalled();
  });

  it('delivers the same event twice but handles it once', async () => {
    const first = await send();
    const second = await send();

    expect(first.body.data.handled).toBe(true);
    expect(second.status).toBe(200);
    expect(second.body).toEqual({ received: true, idempotent: true, eventId: 'evt_pp_1' });
    expect(paypalService.handleWebhook).toHaveBeenCalledTimes(1);
    expect(models.WebhookEvent.rows).toHaveLength(1);
  });

  it('rejects a body that is not JSON', async () => {
    const res = await send('not-json');

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({ success: false, code: 'INVALID_PAYLOAD' });
  });

  it('answers the canonical envelope when fulfilment itself throws', async () => {
    paypalService.handleWebhook.mockRejectedValue(new Error('db down'));

    const res = await send();

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({ success: false, code: 'WEBHOOK_PROCESSING_FAILED' });
    // The dedupe key is only written after successful fulfilment
    // (middleware/webhookSecurity.js:176-199), so PayPal must be free to retry.
    expect(findCall(models.WebhookEvent, 'findOrCreate')).toBeNull();
    expect(models.WebhookEvent.rows).toHaveLength(0);
    expect(redisStore.size).toBe(0);
  });

  it('trusts an unsigned event in development but never in test/production', async () => {
    paypalService.getWebhookId.mockResolvedValue('');
    const previous = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    const dev = await send();

    process.env.NODE_ENV = previous;

    expect(dev.status).toBe(200);
    expect(mockLogger.warn).toHaveBeenCalledWith(expect.stringContaining('SKIPPING PayPal webhook signature verification'));
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /paddle/checkout', () => {
  it('prices the transaction from the order and stores the gateway id', async () => {
    const res = await request(app)
      .post('/api/payments/paddle/checkout')
      .send({ orderId: 1, amount: 0.01, currency: 'eur', customerEmail: 'a@b.c', successUrl: 'https://shop.test/done' });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, paddleTransactionId: 'txn_1', checkoutUrl: 'https://paddle.test/pay', mock: true });
    expect(paddleService.createCheckout).toHaveBeenCalledWith({
      amount: 42.5,
      currency: 'eur',
      orderId: 1,
      description: 'Order ORD-1001',
      customerEmail: 'a@b.c',
      successUrl: 'https://shop.test/done',
    });
    expect(models.Payment.calls.find((c) => c.method === 'create').options.values).toMatchObject({
      provider: 'paddle',
      gatewayPaymentId: 'txn_1',
      amount: 42.5,
    });
  });

  it('blocks a foreign order and rejects a zero amount', async () => {
    const foreign = await request(app).post('/api/payments/paddle/checkout').send({ orderId: 2 });
    expect(foreign.status).toBe(403);
    expect(models.Payment.calls).toEqual([]);

    models.Order.rows[0].totalPrice = '0';
    const zero = await request(app).post('/api/payments/paddle/checkout').send({ orderId: 1 });
    expect(zero.status).toBe(400);
  });
});

describe('POST /paddle/webhook', () => {
  const completed = { event_type: 'transaction.completed', data: { id: 'txn_1', custom_data: { orderId: 1 } } };

  const send = (body, signature) =>
    request(app)
      .post('/api/payments/paddle/webhook')
      .set('Content-Type', 'application/json')
      .set('paddle-signature', signature)
      .send(typeof body === 'string' ? body : JSON.stringify(body));

  it('confirms the matching payment by gateway transaction id', async () => {
    seed({ payments: [paymentRow({ id: 5, provider: 'paddle', stripePaymentIntentId: null, gatewayPaymentId: 'txn_1', status: 'pending' })] });

    const res = await send(completed, 'paddle-valid');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(models.Payment.rows[0].status).toBe('succeeded');
    // The signature is verified against the RAW body, not the parsed object.
    const [rawBody, signature] = paddleService.verifyWebhook.mock.calls[0];
    expect(typeof rawBody).toBe('string');
    expect(JSON.parse(rawBody)).toEqual(completed);
    expect(signature).toBe('paddle-valid');
  });

  it('falls back to the order id when the transaction id is unknown', async () => {
    seed({ payments: [paymentRow({ id: 5, provider: 'paddle', gatewayPaymentId: 'txn_old', stripePaymentIntentId: null, status: 'pending' })] });

    await send({ event_type: 'transaction.completed', data: { id: 'txn_new', custom_data: { orderId: 1 } } }, 'paddle-valid');

    expect(models.Payment.rows[0].status).toBe('succeeded');
  });

  it(
    'confirms a `transaction.paid` event too, not only transaction.completed (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5, provider: 'paddle', stripePaymentIntentId: null, gatewayPaymentId: 'txn_1', status: 'pending' })] });

      await send({ event_type: 'transaction.paid', data: { id: 'txn_1', custom_data: { orderId: 1 } } }, 'paddle-valid');

      expect(models.Payment.rows[0].status).toBe('succeeded');
    },
  );

  it('rejects a forged signature and never touches the ledger', async () => {
    seed({ payments: [paymentRow({ id: 5, provider: 'paddle', gatewayPaymentId: 'txn_1', status: 'pending' })] });

    const res = await send(completed, 'paddle-forged');

    expect(res.status).toBe(401);
    expect(res.body).toEqual({ success: false, error: 'Invalid Paddle signature' });
    expect(models.Payment.rows[0].status).toBe('pending');
  });

  it('rejects an unsigned event', async () => {
    const res = await send(completed, '');

    expect(res.status).toBe(401);
    expect(paddleService.handleWebhook).not.toHaveBeenCalled();
  });

  it('delegates non-completed events to the service', async () => {
    const res = await send({ event_type: 'subscription.updated', data: { id: 'sub_1' } }, 'paddle-valid');

    expect(res.status).toBe(200);
    expect(paddleService.handleWebhook).toHaveBeenCalledWith({ event_type: 'subscription.updated', data: { id: 'sub_1' } });
    expect(models.Payment.calls).toEqual([]);
  });

  it('acknowledges an unknown transaction without inventing a payment row', async () => {
    const res = await send({ event_type: 'transaction.completed', data: { id: 'txn_ghost' } }, 'paddle-valid');

    expect(res.status).toBe(200);
    expect(models.Payment.rows).toHaveLength(0);
    expect(models.Payment.calls.filter((c) => c.method === 'update' || c.method === 'create')).toEqual([]);
  });

  it('answers 400 when the signed body is not JSON', async () => {
    const res = await send('garbage-not-json', 'paddle-valid');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Webhook processing failed' });
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('Razorpay routes', () => {
  it('creates a Razorpay order priced from the stored total', async () => {
    const res = await request(app)
      .post('/api/payments/razorpay/create-order')
      .send({ orderId: 1, amount: 0.01, currency: 'INR' });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, orderId: 'order_rzp', amount: 4250, keyId: 'rzp_test_key' });
    expect(razorpayService.createOrder).toHaveBeenCalledWith(
      expect.objectContaining({ amount: 42.5, currency: 'INR', notes: { userId: '7', orderId: '1' } }),
    );
  });

  it(
    'persists a Payment row for the gateway order so /refund can find it (fixed 2026-10-23)',
    async () => {
      await request(app).post('/api/payments/razorpay/create-order').send({ orderId: 1 });

      expect(models.Payment.rows).toHaveLength(1);
      expect(models.Payment.rows[0]).toMatchObject({ provider: 'razorpay', order_id: 1 });
    },
  );

  it('404s and 403s like every other order-scoped creator', async () => {
    const missing = await request(app).post('/api/payments/razorpay/create-order').send({ orderId: 99 });
    expect(missing.status).toBe(404);
    expect(razorpayService.createOrder).not.toHaveBeenCalled();

    const foreign = await request(app).post('/api/payments/razorpay/create-order').send({ orderId: 2 });
    expect(foreign.status).toBe(403);
  });

  it('rejects a zero-total order', async () => {
    models.Order.rows[0].totalPrice = '0.00';

    const res = await request(app).post('/api/payments/razorpay/create-order').send({ orderId: 1, amount: 500 });

    expect(res.status).toBe(400);
  });

  it('verifies a payment signature and refuses an unsigned one', async () => {
    const missing = await request(app).post('/api/payments/razorpay/verify').send({ orderId: 'o1' });
    expect(missing.status).toBe(400);
    expect(missing.body.error).toBe('orderId, paymentId and signature are required');

    razorpayService.verifyPayment.mockResolvedValue(false);
    const bad = await request(app)
      .post('/api/payments/razorpay/verify')
      .send({ orderId: 'o1', paymentId: 'pay_1', signature: 'forged' });
    expect(bad.status).toBe(400);
    expect(bad.body.error).toBe('Payment signature verification failed');

    razorpayService.verifyPayment.mockResolvedValue(true);
    const good = await request(app)
      .post('/api/payments/razorpay/verify')
      .send({ orderId: 'o1', paymentId: 'pay_1', signature: 'ok' });
    expect(good.body).toEqual({ success: true });
  });

  it('records the gateway payment id on verify so /refund has something to return', async () => {
    seed({
      payments: [
        paymentRow({
          id: 5,
          provider: 'razorpay',
          stripePaymentIntentId: null,
          gatewayPaymentId: 'order_rzp',
          order_id: 1,
          status: 'pending',
        }),
      ],
    });
    razorpayService.verifyPayment.mockResolvedValue(true);

    const res = await request(app)
      .post('/api/payments/razorpay/verify')
      .send({ orderId: 'order_rzp', paymentId: 'pay_real_1', signature: 'ok' });

    expect(res.body).toEqual({ success: true });
    expect(models.Payment.rows[0]).toMatchObject({
      status: 'succeeded',
      gatewayPaymentId: 'pay_real_1',
      razorpayPaymentId: 'pay_real_1',
    });
    expect(models.Order.rows[0]).toMatchObject({ isPaid: true, status: 'processing' });
  });

  it('logs instead of silently succeeding when verify has no ledger row', async () => {
    razorpayService.verifyPayment.mockResolvedValue(true);

    const res = await request(app)
      .post('/api/payments/razorpay/verify')
      .send({ orderId: 'order_orphan', paymentId: 'pay_x', signature: 'ok' });

    expect(res.status).toBe(200);
    expect(models.Payment.rows).toHaveLength(0);
    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining('no Payment row for order order_orphan'),
    );
  });

  it('rejects a razorpay webhook whose signature does not validate', async () => {
    const event = { event: 'payment.captured', payload: { payment: { entity: { id: 'pay_1' } } } };
    const body = JSON.stringify(event);

    const bad = await request(app)
      .post('/api/payments/razorpay/webhook')
      .set('Content-Type', 'application/json')
      .set('x-razorpay-signature', 'forged')
      .send(body);
    expect(bad.status).toBe(401);
    expect(bad.body).toEqual({ success: false, error: 'Invalid signature' });

    const unsigned = await request(app)
      .post('/api/payments/razorpay/webhook')
      .set('Content-Type', 'application/json')
      .send(body);
    expect(unsigned.status).toBe(401);
  });

  it('accepts a valid razorpay webhook signed over the raw body', async () => {
    const event = { event: 'payment.captured', payload: { payment: { entity: { id: 'pay_1' } } } };
    const body = JSON.stringify(event);

    const res = await request(app)
      .post('/api/payments/razorpay/webhook')
      .set('Content-Type', 'application/json')
      .set('x-razorpay-signature', 'rzp-valid')
      .send(body);

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true });
    expect(razorpayService.handleWebhook).toHaveBeenCalledWith(event, 'rzp-valid', body);
  });

  it('refuses to parse a malformed razorpay body', async () => {
    const res = await request(app)
      .post('/api/payments/razorpay/webhook')
      .set('Content-Type', 'application/json')
      .set('x-razorpay-signature', 'rzp-valid')
      .send('}{');

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Invalid JSON body' });
    expect(razorpayService.handleWebhook).not.toHaveBeenCalled();
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /refund (admin only)', () => {
  // routes/payment.routes.js:591 gates this on authorize('admin'); the outer
  // beforeEach restores the plain user.
  beforeEach(() => {
    currentUser = { ...ADMIN };
  });

  it('refuses a non-admin caller', async () => {
    seed({ payments: [paymentRow()] });
    currentUser = { ...USER };

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5 });

    expect(res.status).toBe(403);
    expect(stripeService.refund).not.toHaveBeenCalled();
    expect(models.Payment.rows[0].status).toBe('succeeded');
  });

  it('404s an unknown payment instead of reporting a refund', async () => {
    seed({ payments: [paymentRow()] });

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 999 });

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ success: false, error: 'Payment not found' });
    expect(stripeService.refund).not.toHaveBeenCalled();
  });

  it('refunds a Stripe payment in full and flips payment + order to refunded', async () => {
    seed({ payments: [paymentRow({ id: 5, order_id: 1 })] });

    const res = await request(app)
      .post('/api/payments/refund')
      .send({ paymentId: 5, reason: 'Duplicate charge' });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, message: 'Refund processed successfully' });
    expect(stripeService.refund).toHaveBeenCalledWith({
      paymentId: 'pi_live_9',
      amount: undefined,
      currency: 'usd',
      reason: 'Duplicate charge',
    });
    expect(models.Payment.rows[0]).toMatchObject({ status: 'refunded', refundAmount: 100, refundReason: 'Duplicate charge' });
    expect(models.Order.rows[0].status).toBe('refunded');
  });

  it('keeps a partial refund as succeeded and forwards the exact amount', async () => {
    seed({ payments: [paymentRow({ id: 5, order_id: null })] });

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: 40 });

    expect(res.status).toBe(200);
    expect(stripeService.refund).toHaveBeenCalledWith(expect.objectContaining({ amount: 40 }));
    expect(models.Payment.rows[0]).toMatchObject({ status: 'succeeded', refundAmount: 40 });
    expect(models.Order.rows[0].status).toBe('pending');
  });

  it('rejects a second refund of an already refunded payment', async () => {
    seed({ payments: [paymentRow({ id: 5, status: 'refunded', refundAmount: '100.00' })] });

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'Payment has already been refunded' });
    expect(stripeService.refund).not.toHaveBeenCalled();
  });

  it('refuses a mock Stripe intent instead of reporting money returned', async () => {
    seed({ payments: [paymentRow({ id: 5, stripePaymentIntentId: 'pi_mock_1_abc', status: 'pending' })] });

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5 });

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'No refundable gateway transaction found for this payment' });
    expect(stripeService.refund).not.toHaveBeenCalled();
    expect(models.Payment.rows[0].status).toBe('pending');
  });

  it('dispatches to the provider recorded on the payment', async () => {
    seed({
      payments: [
        paymentRow({ id: 11, provider: 'paypal', stripePaymentIntentId: 'PO-1' }),
        paymentRow({ id: 12, provider: 'paddle', stripePaymentIntentId: null, gatewayPaymentId: 'txn_1' }),
        paymentRow({ id: 13, provider: 'razorpay', stripePaymentIntentId: null, gatewayPaymentId: 'pay_rzp' }),
      ],
    });
    currentUser = { ...ADMIN };

    await request(app).post('/api/payments/refund').send({ paymentId: 11 });
    await request(app).post('/api/payments/refund').send({ paymentId: 12 });
    await request(app).post('/api/payments/refund').send({ paymentId: 13 });

    expect(paypalService.refund).toHaveBeenCalledWith({ paymentId: 'PO-1', amount: 100 });
    expect(paddleService.refund).toHaveBeenCalledWith({ transactionId: 'txn_1', amount: undefined, reason: undefined });
    expect(razorpayService.refund).toHaveBeenCalledWith({ paymentId: 'pay_rzp', amount: 100 });
  });

  it('leaves the ledger untouched when the gateway rejects the refund', async () => {
    seed({ payments: [paymentRow({ id: 5 })] });
    stripeService.refund.mockRejectedValue(new Error('Stripe: no such payment_intent'));

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5 });

    expect(res.status).toBe(500);
    expect(models.Payment.rows[0].status).toBe('succeeded');
    expect(models.Payment.rows[0].refundAmount).toBe('0.00');
  });

  it('surfaces a Paddle partial refund as an error rather than a silent full refund', async () => {
    seed({ payments: [paymentRow({ id: 5, provider: 'paddle', stripePaymentIntentId: null, gatewayPaymentId: 'txn_1' })] });
    currentUser = { ...ADMIN };

    const res = await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: 25 });

    expect(res.status).toBe(500);
    expect(models.Payment.rows[0].status).toBe('succeeded');
  });

  it(
    'caps cumulative refunds at the captured amount (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5, order_id: null, refundAmount: '60.00' })] });

      const res = await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: 60 });

      expect(res.status).toBe(400);
      expect(stripeService.refund).not.toHaveBeenCalled();
      expect(models.Payment.rows[0].refundAmount).toBe('60.00');
    },
  );

  it(
    'rejects amount 0 instead of refunding everything (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5 })] });

      const res = await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: 0 });

      expect(res.status).toBe(400);
      expect(stripeService.refund).not.toHaveBeenCalled();
    },
  );

  it(
    'rejects a negative refund amount (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5 })] });

      const res = await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: -500 });

      expect(res.status).toBe(400);
      expect(models.Payment.rows[0].refundAmount).toBe('0.00');
    },
  );

  it(
    'does not mark the order refunded for a partial refund (fixed 2026-10-23)',
    async () => {
      seed({ payments: [paymentRow({ id: 5, order_id: 1 })] });

      await request(app).post('/api/payments/refund').send({ paymentId: 5, amount: 10 });

      expect(models.Order.rows[0].status).toBe('pending');
    },
  );
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /checkout (Stripe Checkout)', () => {
  it('starts a subscription session scaled by the plan credits', async () => {
    models.Plan = createFakeModel('Plan', [
      { id: 3, slug: 'pro', stripePriceId: 'price_pro', interval: 'month', creditsGrant: '250', isActive: true },
    ]);

    const res = await request(app).post('/api/payments/checkout').send({ planId: 3 });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, checkoutUrl: 'https://stripe.test/pay', sessionId: 'cs_1', mode: 'subscription', credits: 250 });
    expect(stripeService.createCheckoutSession).toHaveBeenCalledWith(
      expect.objectContaining({
        priceId: 'price_pro',
        mode: 'subscription',
        credits: 250,
        metadata: { planId: 'pro' },
        successUrl: 'https://shop.test/billing?success=1',
        cancelUrl: 'https://shop.test/pricing?canceled=1',
      }),
    );
  });

  it('stores the Stripe customer against the requesting user only', async () => {
    models.Plan = createFakeModel('Plan', [
      { id: 3, slug: 'basic', stripePriceId: 'price_basic', interval: 'one_time', creditsGrant: '10', isActive: true },
    ]);

    await request(app).post('/api/payments/checkout').send({ planId: 3 });

    const call = findCall(models.User, 'update');
    expect(updateWhereOf(models.User)).toEqual({ id: 7 });
    expect(call.options.values).toEqual({ stripeCustomerId: 'cus_9' });
  });

  it('skips the customer write when the user already has one', async () => {
    models.Plan = createFakeModel('Plan', [
      { id: 3, slug: 'basic', stripePriceId: 'price_basic', interval: 'one_time', creditsGrant: '10', isActive: true },
    ]);
    currentUser = { ...USER, stripeCustomerId: 'cus_existing' };

    await request(app).post('/api/payments/checkout').send({ planId: 3 });

    expect(models.User.calls).toEqual([]);
  });

  it('takes the one-time path for an order and prices it from the DB', async () => {
    const res = await request(app).post('/api/payments/checkout').send({ orderId: 1 });

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ success: true, paymentIntentId: 'pi_svc_1', clientSecret: 'pi_svc_1_secret' });
    expect(stripeService.createPayment).toHaveBeenCalledWith({ amount: 42.5, currency: 'usd', orderId: 1 });
    expect(models.Payment.calls.find((c) => c.method === 'create').options.values).toMatchObject({
      amount: 42.5,
      currency: 'usd',
      order_id: 1,
      status: 'pending',
    });
  });

  it('403s a foreign order and 404s a missing one on the order path', async () => {
    const foreign = await request(app).post('/api/payments/checkout').send({ orderId: 2 });
    expect(foreign.status).toBe(403);
    expect(stripeService.createPayment).not.toHaveBeenCalled();

    const missing = await request(app).post('/api/payments/checkout').send({ orderId: 88 });
    expect(missing.status).toBe(404);
  });

  it('404s an unknown or deactivated plan and 400s when neither id is given', async () => {
    models.Plan = createFakeModel('Plan', [
      { id: 4, slug: 'old', stripePriceId: 'price_old', interval: 'month', creditsGrant: '5', isActive: false },
    ]);

    expect((await request(app).post('/api/payments/checkout').send({ planId: 4 })).body).toEqual({
      success: false,
      error: 'Plan not found',
    });
    expect((await request(app).post('/api/payments/checkout').send({ planId: 99 })).status).toBe(404);

    const none = await request(app).post('/api/payments/checkout').send({});
    expect(none.status).toBe(400);
    expect(none.body).toEqual({ success: false, error: 'planId or orderId is required' });
  });

  it(
    'never forwards an agent API key taken from the request body (fixed 2026-10-23)',
    async () => {
      models.Plan = createFakeModel('Plan', [
        { id: 3, slug: 'pro', stripePriceId: 'price_pro', interval: 'month', creditsGrant: '250', isActive: true },
      ]);

      await request(app).post('/api/payments/checkout').send({ planId: 3, agentApiKey: 'sk-agent-of-another-tenant' });

      expect(stripeService.createCheckoutSession).toHaveBeenCalledWith(
        expect.objectContaining({ metadata: { planId: 'pro' } }),
      );
    },
  );
});

describe('POST /portal', () => {
  it('returns the billing portal URL', async () => {
    const res = await request(app).post('/api/payments/portal').send({});

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ success: true, url: 'https://stripe.test/portal' });
    expect(stripeService.createPortalSession).toHaveBeenCalledWith({
      user: expect.objectContaining({ id: 7 }),
      returnUrl: 'https://shop.test/billing',
    });
  });

  it('answers 400 when the portal cannot be created', async () => {
    stripeService.createPortalSession.mockRejectedValue(new Error('No billing account'));

    const res = await request(app).post('/api/payments/portal').send({});

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ success: false, error: 'No billing account' });
  });
});

// ══════════════════════════════════════════════════════════════════════════
describe('POST /webhook (Stripe)', () => {
  it('refuses an unsigned event', async () => {
    const res = await request(app)
      .post('/api/payments/webhook')
      .set('Content-Type', 'application/json')
      .send(JSON.stringify(stripeEvent('evt_1', 'payment_intent.succeeded', { id: 'pi_live_9' })));

    expect(res.status).toBe(403);
    expect(res.body).toEqual({ success: false, error: 'Webhook signature required' });
    expect(models.Payment.calls).toEqual([]);
  });

  it('refuses an event with a bad signature', async () => {
    currentStripeClient = makeStripeClient();

    const res = await postWebhook(
      stripeEvent('evt_1', 'payment_intent.succeeded', { id: 'pi_live_9' }),
      't=1,v1=forged',
    );

    expect(res.status).toBe(400);
    expect(res.text).toContain('Webhook signature verification failed');
    expect(models.Payment.calls).toEqual([]);
    expect(models.WebhookEvent.calls).toEqual([]);
  });

  it('marks the payment and its order paid, with the gateway id in the WHERE clause', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5, order_id: 1, status: 'pending' })] });

    const res = await postWebhook(stripeEvent('evt_pi', 'payment_intent.succeeded', { id: 'pi_live_9' }));

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ received: true, eventId: 'evt_pi' });
    expect(models.Payment.rows[0].status).toBe('succeeded');
    expect(updateWhereOf(models.Payment)).toEqual({ stripePaymentIntentId: 'pi_live_9' });
    expect(models.Order.rows[0]).toMatchObject({ isPaid: true, status: 'processing' });
    expect(updateWhereOf(models.Order)).toEqual({ id: 1 });
    expect(models.WebhookEvent.rows[0]).toMatchObject({ event_id: 'evt_pi', gateway: 'stripe' });
  });

  it('applies the same event once across two deliveries', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5, order_id: 1, status: 'pending' })] });
    const event = stripeEvent('evt_dup', 'payment_intent.succeeded', { id: 'pi_live_9' });

    const first = await postWebhook(event);
    const second = await postWebhook(event);

    expect(first.body.received).toBe(true);
    expect(second.body).toEqual({ received: true, idempotent: true, eventId: 'evt_dup' });
    expect(models.Payment.calls.filter((c) => c.method === 'update')).toHaveLength(1);
    expect(models.WebhookEvent.rows).toHaveLength(1);
  });

  it('records the failure reason on payment_intent.payment_failed', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5, status: 'processing' })] });

    await postWebhook(
      stripeEvent('evt_fail', 'payment_intent.payment_failed', {
        id: 'pi_live_9',
        last_payment_error: { message: 'card declined' },
      }),
    );

    expect(models.Payment.rows[0]).toMatchObject({ status: 'failed', errorMessage: 'card declined' });
    expect(models.Order.rows[0].isPaid).toBe(false);
  });

  it('defaults the failure message when Stripe sends none', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5 })] });

    await postWebhook(stripeEvent('evt_fail2', 'payment_intent.payment_failed', { id: 'pi_live_9' }));

    expect(models.Payment.rows[0].errorMessage).toBe('Payment failed');
  });

  it('credits a one-time checkout purchase without replaying a client-supplied agent key', async () => {
    currentStripeClient = makeStripeClient();

    const res = await postWebhook(
      stripeEvent('evt_cs', 'checkout.session.completed', {
        id: 'cs_2',
        mode: 'payment',
        payment_intent: 'pi_cs_1',
        amount_total: 2500,
        currency: 'usd',
        metadata: { userId: '7', credits: '250', planId: 'pro', agentApiKey: 'agent-key-1' },
      }),
    );

    expect(res.status).toBe(200);
    expect(models.Payment.rows[0]).toMatchObject({
      user_id: 7,
      stripePaymentIntentId: 'pi_cs_1',
      amount: 25,
      status: 'succeeded',
      provider: 'stripe',
    });
    // A key that arrived in a request body is not a credential this server may
    // spend: the top-up call is gone, and nothing forwards it upstream.
    expect(aiAgent.fetchWithTimeout).not.toHaveBeenCalled();
  });

  it('ignores a subscription-mode checkout session', async () => {
    currentStripeClient = makeStripeClient();

    await postWebhook(
      stripeEvent('evt_cs2', 'checkout.session.completed', {
        id: 'cs_3',
        mode: 'subscription',
        metadata: { credits: '10' },
      }),
    );

    expect(models.Payment.rows).toHaveLength(0);
  });

  it('updates an existing subscription row', async () => {
    currentStripeClient = makeStripeClient();
    models.Subscription = attachFindOrCreate(createFakeModel('Subscription', [
      { id: 8, user_id: 7, stripeSubscriptionId: 'sub_1', status: 'trialing', cancelAtPeriodEnd: false },
    ]));

    await postWebhook(
      stripeEvent('evt_sub', 'customer.subscription.updated', {
        id: 'sub_1',
        status: 'active',
        cancel_at_period_end: true,
        current_period_end: 1800000000,
        items: { data: [{ price: { id: 'price_pro' } }] },
        metadata: { userId: '7' },
      }),
    );

    expect(models.Subscription.rows[0]).toMatchObject({ status: 'active', cancelAtPeriodEnd: true });
    expect(models.Subscription.whereCalls('findOne')[0].where).toEqual({ stripeSubscriptionId: 'sub_1' });
  });

  it('creates a subscription row when the ledger has none', async () => {
    currentStripeClient = makeStripeClient();

    await postWebhook(
      stripeEvent('evt_sub2', 'customer.subscription.created', {
        id: 'sub_new',
        customer: 'cus_1',
        status: 'active',
        current_period_start: 1700000000,
        items: { data: [{ price: { id: 'price_pro', nickname: 'Pro' } }] },
        metadata: { userId: '7' },
      }),
    );

    expect(models.Subscription.rows[0]).toMatchObject({
      user_id: 7,
      stripeSubscriptionId: 'sub_new',
      planName: 'Pro',
      status: 'active',
    });
  });

  it('skips subscription writes when the event carries no user id', async () => {
    currentStripeClient = makeStripeClient();

    await postWebhook(
      stripeEvent('evt_sub3', 'customer.subscription.created', { id: 'sub_x', status: 'active', metadata: {} }),
    );

    expect(models.Subscription.calls).toEqual([]);
  });

  it('cancels the stored subscription on customer.subscription.deleted', async () => {
    currentStripeClient = makeStripeClient();
    models.Subscription = attachFindOrCreate(createFakeModel('Subscription', [
      { id: 8, stripeSubscriptionId: 'sub_1', status: 'active' },
    ]));

    await postWebhook(stripeEvent('evt_del', 'customer.subscription.deleted', { id: 'sub_1' }));

    expect(models.Subscription.rows[0].status).toBe('canceled');
    expect(updateWhereOf(models.Subscription)).toEqual({ stripeSubscriptionId: 'sub_1' });
  });

  it('acknowledges an unhandled event type without writing anything', async () => {
    currentStripeClient = makeStripeClient();

    const res = await postWebhook(stripeEvent('evt_x', 'invoice.created', { id: 'in_1' }));

    expect(res.body).toEqual({ received: true, eventId: 'evt_x' });
    expect(models.Payment.calls).toEqual([]);
    expect(models.Subscription.calls).toEqual([]);
  });

  it('flips only the payment when the intent has no order attached', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5, order_id: null, status: 'pending' })] });

    const res = await postWebhook(
      stripeEvent('evt_noorder', 'payment_intent.succeeded', { id: 'pi_live_9' }),
    );

    expect(res.status).toBe(200);
    expect(models.Payment.rows[0].status).toBe('succeeded');
    expect(models.Order.calls.filter((c) => c.method === 'update')).toEqual([]);
    expect(models.WebhookEvent.rows).toHaveLength(1);
  });

  it('answers 500 when the order update rejects so the provider retries', async () => {
    currentStripeClient = makeStripeClient();
    seed({ payments: [paymentRow({ id: 5, order_id: 1, status: 'pending' })] });
    models.Order.update = async () => {
      throw new Error('orders table locked');
    };

    const res = await postWebhook(
      stripeEvent('evt_orderr', 'payment_intent.succeeded', { id: 'pi_live_9' }),
    );

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ received: false, error: 'Webhook processing failed' });
    expect(models.Payment.rows[0].status).toBe('succeeded');
    expect(models.Order.rows[0].isPaid).toBe(false);
    expect(mockLogger.error).toHaveBeenCalledWith(expect.stringContaining('orders table locked'));
  });

  it(
    'does not commit a half-processed event to the ledger so Stripe can retry (fixed 2026-10-23)',
    async () => {
      currentStripeClient = makeStripeClient();
      seed({ payments: [paymentRow({ id: 5, order_id: 1, status: 'pending' })] });
      models.Order.update = async () => {
        throw new Error('orders table locked');
      };

      await postWebhook(stripeEvent('evt_retry', 'payment_intent.succeeded', { id: 'pi_live_9' }));

      expect(models.WebhookEvent.rows).toHaveLength(0);
      expect(redisStore.has('webhook:processed:evt_retry')).toBe(false);
    },
  );
});

// ══════════════════════════════════════════════════════════════════════════
describe('GET /invoice/:orderId', () => {
  it('renders the invoice for the order owner', async () => {
    const res = await request(app).get('/api/payments/invoice/1');

    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toMatch(/text\/html/);
    expect(res.text).toContain('#ORD-1001');
    expect(res.text).toContain('PENDING');
    expect(res.text).toContain('$42.50 USD');
  });

  it('renders a paid badge for an admin', async () => {
    currentUser = { ...ADMIN };
    models.Order.rows[1].isPaid = true;

    const res = await request(app).get('/api/payments/invoice/2');

    expect(res.status).toBe(200);
    expect(res.text).toContain('PAID');
  });

  it('403s another user invoice and 404s an unknown order', async () => {
    const foreign = await request(app).get('/api/payments/invoice/2');
    expect(foreign.status).toBe(403);
    expect(foreign.body).toEqual({ success: false, error: 'Not authorized to view this invoice' });

    const missing = await request(app).get('/api/payments/invoice/999');
    expect(missing.status).toBe(404);
  });

  it(
    'renders an invoice whose totals come back from PostgreSQL as DECIMAL strings (fixed 2026-10-23, utils/invoiceGenerator.js money())',
    async () => {
      models.Order.rows[0].totalPrice = '42.50';
      models.Order.rows[0].itemsPrice = '40.00';
      models.Order.rows[0].taxPrice = '2.50';
      models.Order.rows[0].shippingPrice = '0.00';

      const res = await request(app).get('/api/payments/invoice/1');

      expect(res.status).toBe(200);
      expect(res.text).toContain('$42.50 USD');
      expect(res.text).toContain('$40.00');
    },
  );

  it('escapes order content instead of injecting it into the invoice page', async () => {
    models.Order.rows[0].items = [
      { title: '<script>alert(1)</script>', quantity: '2', price: '10.00' },
    ];
    models.Order.rows[0].shippingAddress = {
      fullName: '<img src=x onerror=alert(1)>',
      street: '1 Main St',
      city: 'Karachi',
      state: 'Sindh',
      zipCode: '75500',
      country: 'PK',
    };

    const res = await request(app).get('/api/payments/invoice/1');

    expect(res.status).toBe(200);
    expect(res.text).not.toContain('<script>alert(1)</script>');
    expect(res.text).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(res.text).toContain('&lt;img src=x onerror=alert(1)&gt;');
    // The quantity and unit price arrive as strings on real rows.
    expect(res.text).toContain('$20.00');
  });
});
