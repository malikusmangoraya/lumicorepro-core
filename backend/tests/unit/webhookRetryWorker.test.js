import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * Webhook-retry worker tests.
 *
 * The retry handler decides whether a payment event is recorded as applied.
 * Before this suite it marked the ledger row `processed` even when the gateway
 * handler rejected the event or when the gateway can only be verified with a
 * signature header the ledger never stored — a silent failure on the money path.
 */

const mockLog = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
};

jest.unstable_mockModule('bullmq', () => ({ Worker: jest.fn() }));

jest.unstable_mockModule('../../services/queue/queue.service.js', () => ({
  QUEUES: {
    EMAIL: 'lh-email',
    AI_GENERATION: 'lh-ai-generation',
    IMAGE_PROCESSING: 'lh-image-processing',
    REPORT: 'lh-report',
    WEBHOOK_RETRY: 'lh-webhook-retry',
    CART_RECOVERY: 'lh-cart-recovery',
  },
}));

jest.unstable_mockModule('../../services/queue/deadLetter.js', () => ({
  sendToDLQ: jest.fn(),
}));

jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({
  getRedis: () => ({ get: jest.fn(), set: jest.fn(), on: jest.fn() }),
}));

jest.unstable_mockModule('../../utils/logger.js', () => ({
  default: mockLog,
  logger: mockLog,
  withRequestId: () => mockLog,
}));

jest.unstable_mockModule('../../services/email.service.js', () => ({
  sendEmail: jest.fn(async () => ({ sent: true })),
}));

const mockHandleWebhook = jest.fn();
const mockIsReplayable = jest.fn(() => true);

jest.unstable_mockModule('../../services/payment/index.js', () => ({
  handleWebhook: mockHandleWebhook,
  isReplayable: mockIsReplayable,
}));

const mockFindOne = jest.fn();
jest.unstable_mockModule('../../models/WebhookEvent.js', () => ({
  default: { findOne: mockFindOne },
}));

const { handlers } = await import('../../workers/worker.js');

const WEBHOOK_RETRY = handlers['lh-webhook-retry'];
const record = (overrides = {}) => {
  const updates = [];
  return {
    gateway: 'stripe',
    payload: { type: 'payment_intent.succeeded' },
    status: 'failed',
    update: jest.fn(async (fields) => updates.push(fields)),
    updates,
    ...overrides,
  };
};

beforeEach(() => {
  mockFindOne.mockReset();
  mockHandleWebhook.mockReset();
  mockIsReplayable.mockReset();
  mockIsReplayable.mockReturnValue(true);
});

describe('webhook retry handler', () => {
  it('processes a replayable event and marks it processed', async () => {
    const row = record();
    mockFindOne.mockResolvedValue(row);
    mockHandleWebhook.mockResolvedValue({ handled: true, gateway: 'stripe' });

    const result = await WEBHOOK_RETRY({ id: 'j1', data: { eventId: 'evt_1' } });

    expect(result).toBe(true);
    expect(mockHandleWebhook).toHaveBeenCalledWith('stripe', { type: 'payment_intent.succeeded' });
    expect(row.update).toHaveBeenLastCalledWith({ status: 'processed' });
  });

  it('refuses to replay a self-verifying gateway and leaves the row failed', async () => {
    const row = record();
    mockFindOne.mockResolvedValue(row);
    mockHandleWebhook.mockResolvedValue({ valid: false, gateway: 'razorpay' });
    mockIsReplayable.mockReturnValue(false);

    await expect(WEBHOOK_RETRY({ id: 'j2', data: { eventId: 'evt_2', gateway: 'razorpay' } }))
      .resolves.toBe(true);
    expect(mockHandleWebhook).not.toHaveBeenCalled();
    expect(row.update).toHaveBeenCalledWith({ status: 'failed' });
    expect(row.update).not.toHaveBeenCalledWith({ status: 'processed' });
  });

  it('leaves the row failed and retries when a replayable handler rejects', async () => {
    const row = record({ gateway: 'stripe' });
    mockFindOne.mockResolvedValue(row);
    mockHandleWebhook.mockResolvedValue({ valid: false });

    await expect(
      WEBHOOK_RETRY({ id: 'j3', data: { eventId: 'evt_3' } }),
    ).rejects.toThrow('rejected by stripe handler');
    expect(row.updates).toEqual([{ status: 'failed' }]);
  });

  it('skips an event already processed', async () => {
    const row = record({ status: 'processed' });
    mockFindOne.mockResolvedValue(row);

    await expect(WEBHOOK_RETRY({ id: 'j4', data: { eventId: 'evt_4' } })).resolves.toBe(true);
    expect(mockHandleWebhook).not.toHaveBeenCalled();
    expect(row.update).not.toHaveBeenCalled();
  });

  it('does not invent a processed row for an unknown event id', async () => {
    mockFindOne.mockResolvedValue(null);

    await expect(WEBHOOK_RETRY({ id: 'j5', data: { eventId: 'evt_missing' } })).resolves.toBe(true);
    expect(mockHandleWebhook).not.toHaveBeenCalled();
  });

  it('honours the gateway recorded on the ledger row, not the job default', async () => {
    const row = record({ gateway: 'paypal', payload: { event_type: 'PAYMENT.CAPTURE.COMPLETED' } });
    mockFindOne.mockResolvedValue(row);
    mockHandleWebhook.mockResolvedValue({ handled: true });

    await WEBHOOK_RETRY({ id: 'j6', data: { eventId: 'evt_6', gateway: 'stripe' } });

    expect(mockHandleWebhook).toHaveBeenCalledWith('paypal', {
      event_type: 'PAYMENT.CAPTURE.COMPLETED',
    });
    expect(mockIsReplayable).toHaveBeenCalledWith('paypal');
  });

  it('fails a raw payload that the gateway rejects', async () => {
    mockHandleWebhook.mockResolvedValue({ valid: false });

    await expect(
      WEBHOOK_RETRY({ id: 'j7', data: { gateway: 'mollie', payload: { id: 'tr_1' } } }),
    ).rejects.toThrow('rejected by mollie handler');
  });

  it('ignores a job with neither eventId nor payload', async () => {
    await expect(WEBHOOK_RETRY({ id: 'j8', data: {} })).resolves.toBe(true);
    expect(mockHandleWebhook).not.toHaveBeenCalled();
  });
});

describe('worker module safety', () => {
  it('exports handlers without starting BullMQ workers', () => {
    expect(typeof WEBHOOK_RETRY).toBe('function');
    expect(Object.keys(handlers)).toEqual(
      expect.arrayContaining(['lh-email', 'lh-webhook-retry', 'lh-cart-recovery']),
    );
  });
});
