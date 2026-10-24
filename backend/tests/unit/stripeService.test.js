import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * Stripe gateway service tests.
 *
 * stripe.service.js exports a singleton built at import time from process.env,
 * so each scenario re-imports a fresh instance after setting the env. The Stripe
 * SDK and the runtime-config resolver (`./dynamic.js`) are mocked: no network
 * calls, no real keys, no DB.
 */

const mockLogger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  http: jest.fn(),
};
const mockPaymentUpdate = jest.fn();
const mockGetStripeClient = jest.fn();
const mockGetStripePublishableKey = jest.fn();
const MockStripe = jest.fn();

let mockClient;

jest.unstable_mockModule('stripe', () => ({ default: MockStripe }));

jest.unstable_mockModule('../../services/payment/dynamic.js', () => ({
  getStripeClient: mockGetStripeClient,
  getStripePublishableKey: mockGetStripePublishableKey,
}));

jest.unstable_mockModule('../../models/Payment.js', () => ({
  default: { update: mockPaymentUpdate },
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
}));

const ENV_KEYS = [
  'STRIPE_SECRET_KEY',
  'STRIPE_PUBLISHABLE_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'FRONTEND_URL',
];
let savedEnv;

function buildClient() {
  return {
    paymentIntents: {
      create: jest.fn(async () => ({
        id: 'pi_live_1',
        client_secret: 'pi_live_1_secret',
        status: 'requires_payment_method',
      })),
      retrieve: jest.fn(async () => ({ id: 'pi_live_1', status: 'succeeded' })),
    },
    refunds: { create: jest.fn(async () => ({ id: 're_live_1' })) },
    customers: { create: jest.fn(async () => ({ id: 'cus_live_1' })) },
    checkout: {
      sessions: {
        create: jest.fn(async () => ({
          id: 'cs_live_1',
          url: 'https://checkout.stripe.com/c/pay/cs_live_1',
        })),
      },
    },
    billingPortal: {
      sessions: {
        create: jest.fn(async () => ({ url: 'https://billing.stripe.com/p/session_1' })),
      },
    },
    subscriptions: { cancel: jest.fn(async () => ({ id: 'sub_1', status: 'canceled' })) },
  };
}

/**
 * Imports a fresh singleton with the given secret key (or none).
 * resetModules is required because the constructor snapshot is import-time.
 */
async function loadStripe(secretKey) {
  if (secretKey) process.env.STRIPE_SECRET_KEY = secretKey;
  else delete process.env.STRIPE_SECRET_KEY;
  jest.resetModules();
  const mod = await import('../../services/payment/stripe.service.js');
  return mod.default;
}

beforeEach(() => {
  savedEnv = {};
  for (const key of ENV_KEYS) {
    savedEnv[key] = process.env[key];
    delete process.env[key];
  }
  jest.clearAllMocks();
  mockClient = buildClient();
  MockStripe.mockImplementation(function stripeConstructor() {
    return mockClient;
  });
  mockGetStripeClient.mockResolvedValue(mockClient);
  mockGetStripePublishableKey.mockResolvedValue('pk_test_db');
  mockPaymentUpdate.mockResolvedValue([1]);
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (savedEnv[key] === undefined) delete process.env[key];
    else process.env[key] = savedEnv[key];
  }
});

describe('configuration', () => {
  it('is disabled with no client when STRIPE_SECRET_KEY is missing', async () => {
    const svc = await loadStripe();

    expect(svc.enabled).toBe(false);
    expect(svc.client).toBeNull();
    expect(MockStripe).not.toHaveBeenCalled();
  });

  it('treats the .env.example "your_" placeholder as unconfigured', async () => {
    const svc = await loadStripe('your_stripe_secret_key_here');

    expect(svc.enabled).toBe(false);
    expect(svc.client).toBeNull();
    expect(MockStripe).not.toHaveBeenCalled();
  });

  it('builds the SDK client from a real key and enables the gateway', async () => {
    const svc = await loadStripe('sk_test_abc123');

    expect(svc.enabled).toBe(true);
    expect(svc.client).toBe(mockClient);
    expect(MockStripe).toHaveBeenCalledWith('sk_test_abc123');
  });

  it('exposes checkout metadata for the global card/wallet region', async () => {
    const svc = await loadStripe();

    expect(svc.name).toBe('Stripe');
    expect(svc.region).toBe('Global');
    expect(svc.supportedCurrencies).toContain('usd');
    expect(svc.supportedCurrencies).toContain('jpy');
  });
});

describe('refresh + getPublicKey', () => {
  it('re-enables the singleton from runtime config without a restart', async () => {
    const svc = await loadStripe();
    expect(svc.enabled).toBe(false);

    const result = await svc.refresh();

    expect(result).toEqual({ enabled: true });
    expect(svc.enabled).toBe(true);
    expect(svc.client).toBe(mockClient);
    expect(svc.getPublicKey()).toBe('pk_test_db');
  });

  it('disables the singleton when the runtime resolver has no usable key', async () => {
    mockGetStripeClient.mockResolvedValue(null);
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.refresh()).resolves.toEqual({ enabled: false });
    expect(svc.enabled).toBe(false);
    expect(svc.client).toBeNull();
  });

  it('falls back to STRIPE_PUBLISHABLE_KEY from the environment', async () => {
    process.env.STRIPE_PUBLISHABLE_KEY = 'pk_test_env';
    const svc = await loadStripe();

    expect(svc.getPublicKey()).toBe('pk_test_env');
  });

  it('falls back to a test placeholder when nothing is configured', async () => {
    const svc = await loadStripe();

    expect(svc.getPublicKey()).toBe('pk_test_placeholder');
  });
});

describe('createPayment', () => {
  it('returns a mock PaymentIntent when disabled without touching the SDK', async () => {
    const svc = await loadStripe();

    const result = await svc.createPayment({
      amount: 49.5,
      currency: 'usd',
      orderId: 'order_1',
    });

    expect(result.id).toMatch(/^pi_mock_\d+_[a-z0-9]+$/);
    expect(result.clientSecret).toBe(`${result.id}_secret_mock`);
    expect(result).toEqual({
      id: result.id,
      clientSecret: `${result.id}_secret_mock`,
      amount: 49.5,
      currency: 'usd',
      mock: true,
    });
    expect(mockClient.paymentIntents.create).not.toHaveBeenCalled();
  });

  it('converts to the minor unit and merges metadata when enabled', async () => {
    const svc = await loadStripe('sk_test_abc123');

    const result = await svc.createPayment({
      amount: 19.99,
      currency: 'eur',
      orderId: 77,
      description: 'Order 77',
      metadata: { cartId: 'c1' },
    });

    expect(mockClient.paymentIntents.create).toHaveBeenCalledWith({
      amount: 1999,
      currency: 'eur',
      description: 'Order 77',
      metadata: { orderId: '77', cartId: 'c1' },
    });
    expect(result).toEqual({
      id: 'pi_live_1',
      clientSecret: 'pi_live_1_secret',
      amount: 19.99,
      currency: 'eur',
      mock: false,
    });
  });

  it('sends an empty orderId metadata entry when no order is supplied', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.createPayment({ amount: 5, currency: 'usd' });

    const params = mockClient.paymentIntents.create.mock.calls[0][0];
    expect(params.metadata).toEqual({ orderId: '' });
  });

  it('does not multiply zero-decimal currencies by 100', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.createPayment({ amount: 1500, currency: 'jpy' });
    await svc.createPayment({ amount: 1500, currency: 'usd' });

    expect(mockClient.paymentIntents.create.mock.calls[0][0].amount).toBe(1500);
    expect(mockClient.paymentIntents.create.mock.calls[1][0].amount).toBe(150000);
  });

  it('applies default currency, description, order id and metadata', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.createPayment({ amount: 5 });

    expect(mockClient.paymentIntents.create).toHaveBeenCalledWith({
      amount: 500,
      currency: 'usd',
      description: undefined,
      metadata: { orderId: '' },
    });
  });

  it('treats every Stripe zero-decimal currency as whole units', async () => {
    const svc = await loadStripe('sk_test_abc123');

    for (const currency of ['jpy', 'krw', 'vnd', 'clp', 'xof', 'pyg']) {
      expect(svc._toMinorUnits(1000, currency)).toBe(1000);
    }
    expect(svc._toMinorUnits(10.5, 'usd')).toBe(1050);
    expect(svc._toMinorUnits(10.5, 'eur')).toBe(1050);
  });

  it('propagates SDK failures to the caller', async () => {
    const svc = await loadStripe('sk_test_abc123');
    mockClient.paymentIntents.create.mockRejectedValue(new Error('stripe api down'));

    await expect(svc.createPayment({ amount: 10, currency: 'usd' })).rejects.toThrow(
      'stripe api down',
    );
  });
});

describe('confirmPayment + verifyPaymentIntent', () => {
  it('short-circuits with a mock success when disabled', async () => {
    const svc = await loadStripe();

    await expect(svc.confirmPayment({ paymentIntentId: 'pi_x' })).resolves.toEqual({
      success: true,
      mock: true,
      paymentIntentId: 'pi_x',
    });
    await expect(svc.verifyPaymentIntent('pi_x')).resolves.toEqual({
      status: 'succeeded',
      succeeded: true,
      mock: true,
    });
    expect(mockClient.paymentIntents.retrieve).not.toHaveBeenCalled();
  });

  it('reports success only for a succeeded intent', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.confirmPayment({ paymentIntentId: 'pi_live_1' })).resolves.toEqual({
      success: true,
      paymentIntentId: 'pi_live_1',
      status: 'succeeded',
    });
  });

  it('reports failure for an intent that has not succeeded yet', async () => {
    const svc = await loadStripe('sk_test_abc123');
    mockClient.paymentIntents.retrieve.mockResolvedValue({
      id: 'pi_live_1',
      status: 'requires_action',
    });

    await expect(svc.confirmPayment({ paymentIntentId: 'pi_live_1' })).resolves.toEqual({
      success: false,
      paymentIntentId: 'pi_live_1',
      status: 'requires_action',
    });
  });

  it('derives succeeded from the live intent status', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.verifyPaymentIntent('pi_live_1')).resolves.toEqual({
      status: 'succeeded',
      succeeded: true,
      mock: false,
    });

    mockClient.paymentIntents.retrieve.mockResolvedValue({
      id: 'pi_live_1',
      status: 'processing',
    });
    await expect(svc.verifyPaymentIntent('pi_live_1')).resolves.toEqual({
      status: 'processing',
      succeeded: false,
      mock: false,
    });
  });
});

describe('refund', () => {
  it('returns a mock refund when disabled', async () => {
    const svc = await loadStripe();

    await expect(svc.refund({ paymentId: 'pi_x', amount: 10 })).resolves.toEqual({
      success: true,
      mock: true,
      paymentId: 'pi_x',
    });
    expect(mockClient.refunds.create).not.toHaveBeenCalled();
  });

  it('sends the refund amount in cents with the default reason', async () => {
    const svc = await loadStripe('sk_test_abc123');

    const result = await svc.refund({ paymentId: 'pi_live_1', amount: 12.34 });

    expect(mockClient.refunds.create).toHaveBeenCalledWith({
      payment_intent: 'pi_live_1',
      amount: 1234,
      reason: 'requested_by_customer',
    });
    expect(result).toEqual({ success: true, refundId: 're_live_1', paymentId: 'pi_live_1' });
  });

  it('honours an explicit reason and omits amount for a full refund', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.refund({ paymentId: 'pi_live_1', reason: 'fraudulent' });

    expect(mockClient.refunds.create).toHaveBeenCalledWith({
      payment_intent: 'pi_live_1',
      amount: undefined,
      reason: 'fraudulent',
    });
  });

  it('throws for amount 0 instead of silently issuing a full refund', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.refund({ paymentId: 'pi_live_1', amount: 0 })).rejects.toThrow(
      'Stripe refund: amount must be greater than zero (omit it for a full refund)',
    );
    expect(mockClient.refunds.create).not.toHaveBeenCalled();
  });

  it('converts refund amounts with the zero-decimal rule', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.refund({ paymentId: 'pi_live_1', amount: 500, currency: 'jpy' });

    expect(mockClient.refunds.create).toHaveBeenCalledWith({
      payment_intent: 'pi_live_1',
      amount: 500,
      reason: 'requested_by_customer',
    });
  });

  it('propagates SDK refund failures', async () => {
    const svc = await loadStripe('sk_test_abc123');
    mockClient.refunds.create.mockRejectedValue(new Error('charge already refunded'));

    await expect(svc.refund({ paymentId: 'pi_live_1' })).rejects.toThrow(
      'charge already refunded',
    );
  });
});

describe('ensureCustomer', () => {
  it('returns a mock customer when disabled', async () => {
    const svc = await loadStripe();

    await expect(svc.ensureCustomer({ id: 42 })).resolves.toEqual({ id: 'cus_mock_42' });
    await expect(svc.ensureCustomer(undefined)).resolves.toEqual({ id: 'cus_mock_anon' });
    expect(mockClient.customers.create).not.toHaveBeenCalled();
  });

  it('reuses an existing stripeCustomerId without a network call', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.ensureCustomer({ id: 42, stripeCustomerId: 'cus_existing' })).resolves.toEqual(
      { id: 'cus_existing', exists: true },
    );
    expect(mockClient.customers.create).not.toHaveBeenCalled();
  });

  it('creates a customer with stringified user metadata', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(
      svc.ensureCustomer({ id: 42, email: 'buyer@example.com', name: 'Ayesha' }),
    ).resolves.toEqual({ id: 'cus_live_1' });

    expect(mockClient.customers.create).toHaveBeenCalledWith({
      email: 'buyer@example.com',
      name: 'Ayesha',
      metadata: { userId: '42' },
    });
  });
});

describe('createCheckoutSession', () => {
  it('returns a mock checkout URL when disabled', async () => {
    process.env.FRONTEND_URL = 'https://shop.example';
    const svc = await loadStripe();

    const session = await svc.createCheckoutSession({
      user: { id: 42 },
      priceId: 'price_123',
      successUrl: 'https://shop.example/ok',
      cancelUrl: 'https://shop.example/cancel',
    });

    expect(session.id).toMatch(/^cs_mock_\d+$/);
    expect(session.url).toMatch(/^https:\/\/shop\.example\/mock-checkout\?session=cs_mock_\d+$/);
    expect(session.customerId).toBe('cus_mock_42');
    expect(session.mock).toBe(true);
    expect(mockClient.checkout.sessions.create).not.toHaveBeenCalled();
  });

  it('creates a subscription session carrying user + credit metadata', async () => {
    const svc = await loadStripe('sk_test_abc123');

    const session = await svc.createCheckoutSession({
      user: { id: 42 },
      priceId: 'price_123',
      successUrl: 'https://shop.example/ok',
      cancelUrl: 'https://shop.example/cancel',
      credits: 5,
      metadata: { plan: 'pro' },
    });

    expect(mockClient.checkout.sessions.create).toHaveBeenCalledWith({
      mode: 'subscription',
      customer: 'cus_live_1',
      line_items: [{ price: 'price_123', quantity: 1 }],
      success_url: 'https://shop.example/ok',
      cancel_url: 'https://shop.example/cancel',
      metadata: { userId: '42', credits: '5', plan: 'pro' },
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      subscription_data: { metadata: { userId: '42' } },
    });
    expect(session).toEqual({
      id: 'cs_live_1',
      url: 'https://checkout.stripe.com/c/pay/cs_live_1',
      customerId: 'cus_live_1',
    });
    expect(session.mock).toBeUndefined();
  });

  it('omits subscription_data for one-off payment mode', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await svc.createCheckoutSession({
      user: { id: 42 },
      priceId: 'price_123',
      mode: 'payment',
      successUrl: 'https://shop.example/ok',
      cancelUrl: 'https://shop.example/cancel',
    });

    const params = mockClient.checkout.sessions.create.mock.calls[0][0];
    expect(params.mode).toBe('payment');
    expect(params.subscription_data).toBeUndefined();
  });
});

describe('createPortalSession', () => {
  it('returns the frontend billing URL when disabled', async () => {
    process.env.FRONTEND_URL = 'https://shop.example';
    const svc = await loadStripe();

    await expect(svc.createPortalSession({ user: { id: 42 } })).resolves.toEqual({
      url: 'https://shop.example/billing',
    });
    expect(mockClient.billingPortal.sessions.create).not.toHaveBeenCalled();
  });

  it('falls back to localhost when FRONTEND_URL is unset', async () => {
    const svc = await loadStripe();

    await expect(
      svc.createPortalSession({ user: { id: 42 }, returnUrl: '' }),
    ).resolves.toEqual({ url: 'http://localhost:5173/billing' });
  });

  it('refuses to open a portal for a user without a Stripe customer', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.createPortalSession({ user: { id: 42 } })).rejects.toThrow(
      'Customer not created yet',
    );
  });

  it('creates a billing portal session for an existing customer', async () => {
    const svc = await loadStripe('sk_test_abc123');

    const result = await svc.createPortalSession({
      user: { id: 42, stripeCustomerId: 'cus_existing' },
      returnUrl: 'https://shop.example/account',
    });

    expect(mockClient.billingPortal.sessions.create).toHaveBeenCalledWith({
      customer: 'cus_existing',
      return_url: 'https://shop.example/account',
    });
    expect(result).toEqual({ url: 'https://billing.stripe.com/p/session_1' });
  });
});

describe('cancelSubscription', () => {
  it('short-circuits with a mock success when disabled', async () => {
    const svc = await loadStripe();

    await expect(svc.cancelSubscription('sub_1')).resolves.toEqual({
      success: true,
      mock: true,
    });
    expect(mockClient.subscriptions.cancel).not.toHaveBeenCalled();
  });

  it('reports the status returned by Stripe', async () => {
    const svc = await loadStripe('sk_test_abc123');

    await expect(svc.cancelSubscription('sub_1')).resolves.toEqual({
      success: true,
      status: 'canceled',
    });
    expect(mockClient.subscriptions.cancel).toHaveBeenCalledWith('sub_1');
  });
});

describe('handleWebhook', () => {
  it('marks the matching Payment succeeded on payment_intent.succeeded', async () => {
    const svc = await loadStripe();

    await svc.handleWebhook({
      type: 'payment_intent.succeeded',
      data: { object: { id: 'pi_webhook_1' } },
    });

    expect(mockPaymentUpdate).toHaveBeenCalledWith(
      { status: 'succeeded', gatewayPaymentId: 'pi_webhook_1' },
      { where: { stripePaymentIntentId: 'pi_webhook_1' } },
    );
  });

  it('marks the matching Payment failed on payment_intent.payment_failed', async () => {
    const svc = await loadStripe();

    await svc.handleWebhook({
      type: 'payment_intent.payment_failed',
      data: { object: { id: 'pi_webhook_2' } },
    });

    expect(mockPaymentUpdate).toHaveBeenCalledWith(
      { status: 'failed' },
      { where: { stripePaymentIntentId: 'pi_webhook_2' } },
    );
  });

  it('logs and ignores unhandled event types', async () => {
    const svc = await loadStripe();

    await expect(
      svc.handleWebhook({ type: 'charge.refunded', data: { object: { id: 'ch_1' } } }),
    ).resolves.toBeUndefined();

    expect(mockPaymentUpdate).not.toHaveBeenCalled();
    expect(mockLogger.info).toHaveBeenCalledWith('Unhandled Stripe webhook: charge.refunded');
  });
});
