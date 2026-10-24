import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * Payment dispatcher registry tests.
 *
 * The dispatcher is the only place that knows which method each gateway
 * exposes. These tests are the anti-drift gate: a new gateway added to the map
 * without a create/confirm/webhook adapter, or an adapter that calls the wrong
 * provider method, fails here rather than throwing a raw TypeError in
 * production (or silently running a logging-only webhook handler).
 */

const mockLogger = { info: jest.fn(), warn: jest.fn(), error: jest.fn(), debug: jest.fn() };

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLogger,
  logger: mockLogger,
  withRequestId: () => mockLogger,
}));

jest.unstable_mockModule('../../models/Payment.js', () => ({
  default: { update: jest.fn(), findOne: jest.fn() },
}));

const GATEWAY_IDS = [
  'stripe',
  'paypal',
  'razorpay',
  'square',
  'bkash',
  'mercadopago',
  'flutterwave',
  'paytm',
  'mollie',
  'liqpay',
  'paddle',
];

const SPY_METHODS = [
  'createPayment',
  'createOrder',
  'createPreference',
  'initializeTransaction',
  'initiateTransaction',
  'createPaymentForm',
  'createCheckout',
  'confirmPayment',
  'captureOrder',
  'executePayment',
  'refund',
  'handleWebhook',
  'handleCallback',
];

const stubServices = {};
for (const id of GATEWAY_IDS) {
  const stub = { name: id, enabled: false, region: 'Test', supportedCurrencies: ['usd'], icon: '' };
  for (const method of SPY_METHODS) {
    stub[method] = jest.fn();
  }
  stubServices[id] = stub;
  jest.unstable_mockModule(`../../services/payment/${id}.service.js`, () => ({
    default: stubServices[id],
  }));
}

jest.unstable_mockModule('../../services/payment/config.js', () => ({
  getGatewayConfig: jest.fn(() => null),
  getEnabledGateways: jest.fn(() => []),
  isGatewayEnabled: jest.fn(() => false),
}));

const dispatcher = await import('../../services/payment/index.js');
const {
  gateways,
  CREATE_METHOD,
  CONFIRM_METHOD,
  WEBHOOK_ADAPTER,
  createPayment,
  confirmPayment,
  refundPayment,
  handleWebhook,
  isReplayable,
} = dispatcher;

beforeEach(() => {
  // `resetMocks: true` (backend/jest.config.js) strips implementations from
  // module-scope mocks before every test, so they must be (re)bound here.
  for (const id of GATEWAY_IDS) {
    for (const method of SPY_METHODS) {
      stubServices[id][method].mockImplementation(async () => ({
        ok: true,
        via: `${id}.${method}`,
      }));
    }
  }
});

describe('gateway registry', () => {
  it('registers every provider service including paddle', () => {
    expect(Object.keys(gateways).sort()).toEqual([...GATEWAY_IDS].sort());
  });

  it('keeps the adapter maps exactly aligned with the registered gateways', () => {
    expect(Object.keys(CREATE_METHOD).sort()).toEqual([...GATEWAY_IDS].sort());
    expect(Object.keys(WEBHOOK_ADAPTER).sort()).toEqual([...GATEWAY_IDS].sort());
    expect(Object.keys(CONFIRM_METHOD).sort()).toEqual(['stripe', 'paypal', 'bkash'].sort());
  });

  it('names only methods that exist on the real service objects', () => {
    for (const [id, method] of Object.entries(CREATE_METHOD)) {
      expect(typeof gateways[id][method]).toBe('function');
    }
    for (const [id, method] of Object.entries(CONFIRM_METHOD)) {
      expect(typeof gateways[id][method]).toBe('function');
    }
    for (const id of GATEWAY_IDS) {
      expect(typeof gateways[id].refund).toBe('function');
    }
  });
});

describe('createPayment dispatch', () => {
  it.each(Object.entries(CREATE_METHOD || {}))(
    '%s routes to %s',
    async (id, method) => {
      const result = await createPayment(id, { amount: 10, currency: 'usd' });
      expect(stubServices[id][method]).toHaveBeenCalledWith({ amount: 10, currency: 'usd' });
      expect(result.via).toBe(`${id}.${method}`);
    },
  );

  it('rejects an unknown gateway instead of throwing a TypeError', async () => {
    await expect(createPayment('bitcoin', { amount: 1 })).rejects.toThrow(
      'Unknown payment gateway: bitcoin',
    );
  });
});

describe('confirm and refund dispatch', () => {
  it('captures a PayPal order through captureOrder', async () => {
    await confirmPayment('paypal', { orderId: 'PO-1' });
    expect(stubServices.paypal.captureOrder).toHaveBeenCalledWith({ orderId: 'PO-1' });
  });

  it('finalises a bKash payment through executePayment', async () => {
    await confirmPayment('bkash', { paymentId: 'PK-1' });
    expect(stubServices.bkash.executePayment).toHaveBeenCalledWith({ paymentId: 'PK-1' });
  });

  it('refuses confirmation for a gateway that cannot capture', async () => {
    await expect(confirmPayment('liqpay', {})).rejects.toThrow(
      'Gateway liqpay does not support payment confirmation',
    );
  });

  it('routes refunds to each provider refund', async () => {
    await refundPayment('paddle', { transactionId: 'txn_1' });
    expect(stubServices.paddle.refund).toHaveBeenCalledWith({ transactionId: 'txn_1' });
  });
});

describe('webhook dispatch', () => {
  it('passes the signature context to self-verifying gateways', async () => {
    const ctx = {
      rawBody: '{}',
      signature: 'sig',
      verifHash: 'hash',
      headers: { h: '1' },
      notificationUrl: 'https://x/cb',
      params: { a: '1' },
    };

    await handleWebhook('razorpay', { event: 'payment.captured' }, ctx);
    expect(stubServices.razorpay.handleWebhook).toHaveBeenCalledWith(
      { event: 'payment.captured' },
      'sig',
      '{}',
    );

    await handleWebhook('square', { type: 'payment.created' }, ctx);
    expect(stubServices.square.handleWebhook).toHaveBeenCalledWith(
      { type: 'payment.created' },
      { signature: 'sig', rawBody: '{}', notificationUrl: 'https://x/cb' },
    );

    await handleWebhook('flutterwave', { event: 'charge.succeeded' }, ctx);
    expect(stubServices.flutterwave.handleWebhook).toHaveBeenCalledWith(
      { event: 'charge.succeeded' },
      'hash',
    );

    await handleWebhook('mercadopago', { action: 'payment.updated' }, ctx);
    expect(stubServices.mercadopago.handleWebhook).toHaveBeenCalledWith(
      { action: 'payment.updated' },
      { h: '1' },
    );

    await handleWebhook('liqpay', { data: 'd', sign: 's' }, ctx);
    expect(stubServices.liqpay.handleCallback).toHaveBeenCalledWith({ data: 'd', sign: 's' });

    await handleWebhook('paytm', { BODY: {} }, ctx);
    expect(stubServices.paytm.handleCallback).toHaveBeenCalledWith({ a: '1' });
  });

  it('marks the result with the gateway and whether it self-verifies', async () => {
    const stripe = await handleWebhook('stripe', { type: 'payment_intent.succeeded' });
    expect(stripe).toMatchObject({ gateway: 'stripe', verificationRequired: false });

    const razorpay = await handleWebhook('razorpay', { event: 'x' });
    expect(razorpay).toMatchObject({ gateway: 'razorpay', verificationRequired: true });
  });

  it('normalises a bare-string handler result', async () => {
    stubServices.paddle.handleWebhook.mockResolvedValueOnce('transaction.paid');
    const result = await handleWebhook('paddle', { event_type: 'transaction.paid' });
    expect(result).toMatchObject({ handled: true, gateway: 'paddle' });
  });

  it('treats an explicit valid:false from the provider as a rejection', async () => {
    stubServices.razorpay.handleWebhook.mockResolvedValueOnce({ valid: false });
    const result = await handleWebhook('razorpay', { event: 'x' }, {});
    expect(result.valid).toBe(false);
  });

  it('flags gateways whose events cannot be replayed from the ledger', () => {
    expect(isReplayable('stripe')).toBe(true);
    expect(isReplayable('paypal')).toBe(true);
    for (const id of ['razorpay', 'square', 'flutterwave', 'mercadopago', 'liqpay', 'paytm']) {
      expect(isReplayable(id)).toBe(false);
    }
  });

  it('rejects an unknown gateway webhook instead of silently dropping it', async () => {
    await expect(handleWebhook('bitcoin', { type: 'x' })).rejects.toThrow(
      'Unknown payment gateway: bitcoin',
    );
  });
});
