import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

/**
 * PayPal webhook verification + fulfilment.
 *
 * `verifyWebhookSignature` must call PayPal's
 * POST /v1/notifications/verify-webhook-signature with the transmission headers
 * and only accept an explicit SUCCESS. `handleWebhook` must flip the matching
 * payment + order to paid inside ONE transaction for PAYMENT.CAPTURE.COMPLETED,
 * and must acknowledge (never throw) when nothing matches.
 */

const findPaymentOne = jest.fn();
const findOrderByPk = jest.fn();
const notificationCreate = jest.fn();
const transaction = jest.fn();
const getGatewayRuntimeConfig = jest.fn();

const fetchMock = jest.fn();

const silentLogger = {
  error: () => {},
  warn: () => {},
  info: () => {},
  http: () => {},
  debug: () => {},
};

jest.unstable_mockModule('../../models/Payment.js', () => ({ default: { findOne: findPaymentOne } }));
jest.unstable_mockModule('../../models/Order.js', () => ({ default: { findByPk: findOrderByPk } }));
jest.unstable_mockModule('../../models/Notification.js', () => ({
  default: { create: notificationCreate },
}));
jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: { transaction },
  default: async () => false,
}));
jest.unstable_mockModule('../../services/payment/dynamic.js', () => ({ getGatewayRuntimeConfig }));
jest.unstable_mockModule('../../utils/logger.js', () => ({
  __esModule: true,
  default: silentLogger,
  withRequestId: () => silentLogger,
  redact: (v) => v,
}));

const { default: paypalService } = await import('../../services/payment/paypal.service.js');

const TOKEN_RESPONSE = { ok: true, json: async () => ({ access_token: 'tok-123' }) };
const verifyResponse = (status) => ({ ok: true, json: async () => ({ verification_status: status }) });

const VERIFY_ARGS = {
  transmissionId: 'txn-1',
  transmissionTime: '2026-10-03T10:00:00Z',
  transmissionSig: 'sig-abc',
  certUrl: 'https://api.paypal.com/v1/notifications/certs/CERT-1',
  authAlgo: 'SHA256withRSA',
  webhookId: 'WH-TEST',
  webhookEvent: { id: 'WH-EVT-1', event_type: 'PAYMENT.CAPTURE.COMPLETED' },
};

const captureEvent = (resource = {}) => ({
  id: 'WH-EVT-1',
  event_type: 'PAYMENT.CAPTURE.COMPLETED',
  resource: {
    id: 'CAP-1',
    status: 'COMPLETED',
    supplementary_data: { related_ids: { order_id: 'PPO-1' } },
    ...resource,
  },
});

const originalFetch = globalThis.fetch;
let savedWebhookId;

beforeEach(() => {
  jest.clearAllMocks();
  savedWebhookId = process.env.PAYPAL_WEBHOOK_ID;
  process.env.PAYPAL_WEBHOOK_ID = 'WH-TEST';
  process.env.PAYPAL_MODE = 'sandbox';

  paypalService.clientId = 'client-id';
  paypalService.clientSecret = 'client-secret';
  paypalService.baseURL = 'https://api-m.sandbox.paypal.com';
  paypalService.enabled = true;

  transaction.mockImplementation(async (fn) => fn('tx'));
  getGatewayRuntimeConfig.mockResolvedValue({ webhookId: 'WH-TEST', mode: 'sandbox' });
  notificationCreate.mockResolvedValue({ id: 1 });

  // The service talks to PayPal through the global fetch.
  globalThis.fetch = fetchMock;
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  if (savedWebhookId === undefined) delete process.env.PAYPAL_WEBHOOK_ID;
  else process.env.PAYPAL_WEBHOOK_ID = savedWebhookId;
});

describe('verifyWebhookSignature', () => {
  it('POSTs the transmission headers to verify-webhook-signature and accepts SUCCESS', async () => {
    fetchMock.mockResolvedValueOnce(TOKEN_RESPONSE).mockResolvedValueOnce(verifyResponse('SUCCESS'));

    const verified = await paypalService.verifyWebhookSignature(VERIFY_ARGS);

    expect(verified).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    const [url, options] = fetchMock.mock.calls[1];
    expect(url).toBe('https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature');
    expect(options.method).toBe('POST');
    expect(options.headers.Authorization).toBe('Bearer tok-123');
    expect(JSON.parse(options.body)).toEqual({
      transmission_id: 'txn-1',
      transmission_time: '2026-10-03T10:00:00Z',
      transmission_sig: 'sig-abc',
      cert_url: 'https://api.paypal.com/v1/notifications/certs/CERT-1',
      auth_algo: 'SHA256withRSA',
      webhook_id: 'WH-TEST',
      webhook_event: VERIFY_ARGS.webhookEvent,
    });
  });

  it('returns false for a FAILURE verification_status', async () => {
    fetchMock.mockResolvedValueOnce(TOKEN_RESPONSE).mockResolvedValueOnce(verifyResponse('FAILURE'));
    await expect(paypalService.verifyWebhookSignature(VERIFY_ARGS)).resolves.toBe(false);
  });

  it('returns false for a non-JSON / unexpected verification body', async () => {
    fetchMock
      .mockResolvedValueOnce(TOKEN_RESPONSE)
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    await expect(paypalService.verifyWebhookSignature(VERIFY_ARGS)).resolves.toBe(false);
  });

  it('returns false without calling PayPal when a transmission header is missing', async () => {
    const verified = await paypalService.verifyWebhookSignature({
      ...VERIFY_ARGS,
      transmissionSig: undefined,
    });

    expect(verified).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('returns false when no webhook id is configured', async () => {
    const verified = await paypalService.verifyWebhookSignature({ ...VERIFY_ARGS, webhookId: '' });
    expect(verified).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('throws when PayPal rejects the verification request itself', async () => {
    fetchMock
      .mockResolvedValueOnce(TOKEN_RESPONSE)
      .mockResolvedValueOnce({ ok: false, text: async () => 'invalid_token' });

    await expect(paypalService.verifyWebhookSignature(VERIFY_ARGS)).rejects.toThrow(
      /verification request failed/,
    );
  });
});

describe('handleWebhook — PAYMENT.CAPTURE.COMPLETED fulfilment', () => {
  const makePayment = (overrides = {}) => ({
    id: 11,
    order_id: 55,
    status: 'pending',
    stripeChargeId: null,
    update: jest.fn(async () => {}),
    ...overrides,
  });

  const makeOrder = (overrides = {}) => ({
    id: 55,
    isPaid: false,
    user_id: 3,
    orderNumber: 'ORD-1',
    totalPrice: '25.00',
    update: jest.fn(async () => {}),
    ...overrides,
  });

  it('marks the matching payment + order paid inside one transaction', async () => {
    const payment = makePayment();
    const order = makeOrder();
    findPaymentOne.mockResolvedValueOnce(payment);
    findOrderByPk.mockResolvedValueOnce(order);

    const result = await paypalService.handleWebhook(captureEvent());

    expect(transaction).toHaveBeenCalledTimes(1);
    expect(findPaymentOne).toHaveBeenCalledWith({
      where: { provider: 'paypal', stripeChargeId: 'CAP-1' },
      transaction: 'tx',
    });

    expect(payment.update).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'succeeded', stripeChargeId: 'CAP-1' }),
      { transaction: 'tx' },
    );

    expect(findOrderByPk).toHaveBeenCalledWith(55, { transaction: 'tx' });
    expect(order.update).toHaveBeenCalledTimes(1);
    const orderUpdate = order.update.mock.calls[0][0];
    expect(orderUpdate).toMatchObject({ isPaid: true, status: 'processing' });
    expect(orderUpdate.paidAt).toBeInstanceOf(Date);
    expect(orderUpdate.paymentResult).toMatchObject({ captureId: 'CAP-1', provider: 'paypal' });
    expect(order.update.mock.calls[0][1]).toEqual({ transaction: 'tx' });

    expect(notificationCreate).toHaveBeenCalledWith(
      expect.objectContaining({ recipient: 3, type: 'payment' }),
      { transaction: 'tx' },
    );
    expect(result).toEqual({ handled: true, orderId: 55 });
  });

  it('falls back to the PayPal order id when the capture id is unknown', async () => {
    const payment = makePayment({ stripeChargeId: null });
    findPaymentOne.mockResolvedValueOnce(null).mockResolvedValueOnce(payment);
    findOrderByPk.mockResolvedValueOnce(makeOrder());

    await paypalService.handleWebhook(captureEvent());

    expect(findPaymentOne).toHaveBeenNthCalledWith(2, {
      where: { provider: 'paypal', stripePaymentIntentId: 'PPO-1' },
      transaction: 'tx',
    });
  });

  it('is a no-op for a duplicate delivery of an already-paid order', async () => {
    const payment = makePayment();
    const order = makeOrder({ isPaid: true });
    findPaymentOne.mockResolvedValueOnce(payment);
    findOrderByPk.mockResolvedValueOnce(order);

    const result = await paypalService.handleWebhook(captureEvent());

    expect(order.update).not.toHaveBeenCalled();
    expect(notificationCreate).not.toHaveBeenCalled();
    expect(result).toEqual({ handled: true, orderId: 55, duplicate: true });
  });

  it('acknowledges (200-friendly) without throwing when the order is missing', async () => {
    findPaymentOne.mockResolvedValueOnce(makePayment());
    findOrderByPk.mockResolvedValueOnce(null);

    const result = await paypalService.handleWebhook(captureEvent());

    expect(result).toEqual({ handled: true, orderId: null });
    expect(notificationCreate).not.toHaveBeenCalled();
  });

  it('acknowledges without a transaction when no payment matches the capture', async () => {
    findPaymentOne.mockResolvedValue(null);

    const result = await paypalService.handleWebhook(captureEvent());

    expect(result).toEqual({ handled: false, orderId: null });
    expect(findOrderByPk).not.toHaveBeenCalled();
    expect(notificationCreate).not.toHaveBeenCalled();
  });

  it('skips the notification for an order with no user (recipient is NOT NULL)', async () => {
    findPaymentOne.mockResolvedValueOnce(makePayment());
    findOrderByPk.mockResolvedValueOnce(makeOrder({ user_id: null }));

    const result = await paypalService.handleWebhook(captureEvent());

    expect(result).toEqual({ handled: true, orderId: 55 });
    expect(notificationCreate).not.toHaveBeenCalled();
  });

  it('does not open a transaction when the event carries no capture/order id', async () => {
    const result = await paypalService.handleWebhook({
      id: 'WH-EVT-EMPTY',
      event_type: 'PAYMENT.CAPTURE.COMPLETED',
      resource: {},
    });

    expect(transaction).not.toHaveBeenCalled();
    expect(result).toEqual({ handled: false, orderId: null });
  });

  it('logs and ignores other event types (e.g. PAYMENT.CAPTURE.DENIED)', async () => {
    const result = await paypalService.handleWebhook({
      id: 'WH-EVT-2',
      event_type: 'PAYMENT.CAPTURE.DENIED',
      resource: { id: 'CAP-2' },
    });

    expect(transaction).not.toHaveBeenCalled();
    expect(result).toEqual({ handled: false, orderId: null });
  });
});

describe('getWebhookId', () => {
  it('prefers the runtime SystemConfig value', async () => {
    getGatewayRuntimeConfig.mockResolvedValue({ webhookId: 'WH-RUNTIME' });
    await expect(paypalService.getWebhookId()).resolves.toBe('WH-RUNTIME');
  });

  it('falls back to PAYPAL_WEBHOOK_ID', async () => {
    getGatewayRuntimeConfig.mockResolvedValue({ webhookId: '' });
    await expect(paypalService.getWebhookId()).resolves.toBe('WH-TEST');
  });

  it('returns an empty string (fail closed) when SystemConfig throws', async () => {
    delete process.env.PAYPAL_WEBHOOK_ID;
    getGatewayRuntimeConfig.mockRejectedValue(new Error('db down'));
    await expect(paypalService.getWebhookId()).resolves.toBe('');
  });
});
