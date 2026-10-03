import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * Payment webhook middleware. The durable `webhook_events` ledger (unique
 * event_id) is the idempotency source of truth; Redis is only a TTL fast-path,
 * so an evicted key or a restart can never double-apply a payment.
 */

const findOne = jest.fn();
const findOrCreate = jest.fn();
const redisGet = jest.fn();
const redisSet = jest.fn();
const redisClient = { get: redisGet, set: redisSet };
const getRedis = jest.fn(() => redisClient);

const constructEvent = jest.fn();
const stripeClient = { webhooks: { constructEvent } };
const getStripeClient = jest.fn(async () => stripeClient);
const getStripeWebhookSecret = jest.fn(async () => 'whsec_test');

jest.unstable_mockModule('../../models/WebhookEvent.js', () => ({
  default: { findOne, findOrCreate },
}));
jest.unstable_mockModule('../../services/cache/redis.client.js', () => ({ getRedis }));
jest.unstable_mockModule('../../services/payment/dynamic.js', () => ({
  getStripeClient,
  getStripeWebhookSecret,
  // Also consumed by services/payment/paypal.service.js, which this middleware
  // imports for the PayPal verification path.
  getGatewayRuntimeConfig: jest.fn(async () => ({})),
}));

const { stripeWebhook, markWebhookProcessed } = await import(
  '../../middleware/webhookSecurity.js'
);

const fakeRes = () => {
  const res = {};
  res.status = jest.fn((c) => {
    res._status = c;
    return res;
  });
  res.json = jest.fn((b) => {
    res._body = b;
    return res;
  });
  res.send = jest.fn((b) => {
    res._body = b;
    return res;
  });
  return res;
};

beforeEach(() => {
  jest.clearAllMocks();
  getRedis.mockReturnValue(redisClient);
  getStripeClient.mockResolvedValue(stripeClient);
  getStripeWebhookSecret.mockResolvedValue('whsec_test');
  redisGet.mockResolvedValue(null);
  findOne.mockResolvedValue(null);
  findOrCreate.mockResolvedValue([{}, true]);
  redisSet.mockResolvedValue('OK');
});

describe('stripeWebhook - signature verification', () => {
  it('rejects an unsigned request with 403 when signing is mandatory', async () => {
    const next = jest.fn();
    const res = fakeRes();
    await stripeWebhook()({ headers: {}, body: {} }, res, next);
    expect(res._status).toBe(403);
    expect(res._body.error).toBe('Webhook signature required');
    expect(next).not.toHaveBeenCalled();
  });

  it('rejects a bad signature with 400 and does not leak internals beyond the message', async () => {
    constructEvent.mockImplementation(() => {
      throw new Error('no signatures found matching the expected signature');
    });
    const next = jest.fn();
    const res = fakeRes();
    await stripeWebhook()(
      { headers: { 'stripe-signature': 't=1,v1=bad' }, body: Buffer.from('{}') },
      res,
      next
    );
    expect(res._status).toBe(400);
    expect(String(res._body)).toContain('signature verification failed');
    expect(next).not.toHaveBeenCalled();
  });

  it('accepts a valid signature and exposes the parsed event + raw body', async () => {
    const event = { id: 'evt_1', type: 'payment_intent.succeeded', data: { object: { id: 'pi_1' } } };
    constructEvent.mockReturnValue(event);
    const req = {
      headers: { 'stripe-signature': 't=1,v1=good' },
      body: Buffer.from(JSON.stringify(event)),
    };
    const next = jest.fn();
    await stripeWebhook()(req, fakeRes(), next);
    expect(next).toHaveBeenCalledTimes(1);
    expect(req.webhookEvent).toBe(event);
    expect(req.rawBody).toBe(req.body);
  });

  it('refuses the unsigned dev bypass in production', async () => {
    const saved = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';
    const next = jest.fn();
    const res = fakeRes();
    await stripeWebhook({ allowUnsigned: true })(
      { headers: {}, body: JSON.stringify({ id: 'evt_dev' }) },
      res,
      next
    );
    expect(res._status).toBe(403);
    expect(next).not.toHaveBeenCalled();
    process.env.NODE_ENV = saved;
  });

  it('allows an unsigned payload outside production when explicitly opted in', async () => {
    const saved = process.env.NODE_ENV;
    process.env.NODE_ENV = 'test';
    const next = jest.fn();
    await stripeWebhook({ allowUnsigned: true })(
      { headers: {}, body: JSON.stringify({ id: 'evt_dev' }) },
      fakeRes(),
      next
    );
    expect(next).toHaveBeenCalledTimes(1);
    process.env.NODE_ENV = saved;
  });

  it('rejects an unparseable unsigned body with 400', async () => {
    const saved = process.env.NODE_ENV;
    process.env.NODE_ENV = 'test';
    const res = fakeRes();
    await stripeWebhook({ allowUnsigned: true })({ headers: {}, body: 'not json' }, res, jest.fn());
    expect(res._status).toBe(400);
    expect(res._body).toBe('Invalid webhook body');
    process.env.NODE_ENV = saved;
  });
});

describe('stripeWebhook - idempotency', () => {
  it('short-circuits on a Redis hit without touching the ledger', async () => {
    constructEvent.mockReturnValue({ id: 'evt_dup', type: 'payment_intent.succeeded' });
    redisGet.mockResolvedValue(String(Date.now()));
    const next = jest.fn();
    const res = fakeRes();
    await stripeWebhook()(
      { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') },
      res,
      next
    );
    expect(res._body).toMatchObject({ received: true, idempotent: true, eventId: 'evt_dup' });
    expect(next).not.toHaveBeenCalled();
    expect(findOne).not.toHaveBeenCalled();
  });

  it('falls back to the durable ledger when the Redis key is cold', async () => {
    constructEvent.mockReturnValue({ id: 'evt_ledger', type: 'payment_intent.succeeded' });
    redisGet.mockResolvedValue(null);
    findOne.mockResolvedValue({ event_id: 'evt_ledger' });
    const next = jest.fn();
    const res = fakeRes();
    await stripeWebhook()(
      { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') },
      res,
      next
    );
    expect(findOne).toHaveBeenCalledWith({ where: { event_id: 'evt_ledger' } });
    expect(res._body).toMatchObject({ received: true, idempotent: true });
    expect(redisSet).toHaveBeenCalled(); // repopulate the fast-path
    expect(next).not.toHaveBeenCalled();
  });

  it('passes a first-time event through and records the ids for commit', async () => {
    constructEvent.mockReturnValue({ id: 'evt_new', type: 'charge.refunded' });
    redisGet.mockResolvedValue(null);
    findOne.mockResolvedValue(null);
    const req = { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') };
    const next = jest.fn();
    await stripeWebhook()(req, fakeRes(), next);
    expect(next).toHaveBeenCalledTimes(1);
    expect(req._webhookEventId).toBe('evt_new');
    expect(req._webhookDedupeKey).toBe('webhook:processed:evt_new');
  });

  it('continues without dedupe bookkeeping when no event id can be derived', async () => {
    constructEvent.mockReturnValue({ type: 'ping' });
    const req = { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') };
    const next = jest.fn();
    await stripeWebhook()(req, fakeRes(), next);
    expect(next).toHaveBeenCalledTimes(1);
    expect(req._webhookEventId).toBeUndefined();
  });

  it('survives a Redis outage instead of rejecting the payment', async () => {
    constructEvent.mockReturnValue({ id: 'evt_redis_down', type: 'payment_intent.succeeded' });
    redisGet.mockRejectedValue(new Error('ECONNREFUSED'));
    const next = jest.fn();
    await stripeWebhook()(
      { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') },
      fakeRes(),
      next
    );
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('survives a ledger read failure and defers to the handler', async () => {
    constructEvent.mockReturnValue({ id: 'evt_db_down', type: 'payment_intent.succeeded' });
    findOne.mockRejectedValue(new Error('relation does not exist'));
    const next = jest.fn();
    await stripeWebhook()(
      { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') },
      fakeRes(),
      next
    );
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('falls back to the nested object id when the event has no top-level id', async () => {
    constructEvent.mockReturnValue({ data: { object: { id: 'pi_99' } } });
    const req = { headers: { 'stripe-signature': 'sig' }, body: Buffer.from('{}') };
    const next = jest.fn();
    await stripeWebhook()(req, fakeRes(), next);
    expect(req._webhookEventId).toBe('pi_99');
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('falls back to the x-webhook-id header when the event has no id at all', async () => {
    constructEvent.mockReturnValue({ type: 'ping' });
    const req = {
      headers: { 'stripe-signature': 'sig', 'x-webhook-id': 'hdr_1' },
      body: Buffer.from('{}'),
    };
    const next = jest.fn();
    await stripeWebhook()(req, fakeRes(), next);
    expect(req._webhookEventId).toBe('hdr_1');
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('marks nothing as stale when the id is empty', async () => {
    const req = { headers: {}, body: '{}' };
    const res = fakeRes();
    await stripeWebhook({ allowUnsigned: true })(req, res, jest.fn());
    expect(req._webhookDedupeKey).toBeUndefined();
  });
});

describe('markWebhookProcessed', () => {
  it('writes the ledger row and sets the Redis fast-path', async () => {
    const req = {
      _webhookEventId: 'evt_ok',
      _webhookDedupeKey: 'webhook:processed:evt_ok',
      webhookEvent: { id: 'evt_ok', type: 'payment_intent.succeeded' },
    };
    await markWebhookProcessed(req);
    expect(findOrCreate).toHaveBeenCalledWith({
      where: { event_id: 'evt_ok' },
      defaults: expect.objectContaining({
        gateway: 'stripe',
        event_type: 'payment_intent.succeeded',
      }),
    });
    expect(redisSet).toHaveBeenCalledWith(
      'webhook:processed:evt_ok',
      expect.any(String),
      'EX',
      86400
    );
  });

  it('treats a unique-constraint race as idempotent and skips the cache write', async () => {
    findOrCreate.mockRejectedValue(new Error('duplicate key value'));
    const req = {
      _webhookEventId: 'evt_race',
      _webhookDedupeKey: 'webhook:processed:evt_race',
      webhookEvent: { id: 'evt_race', type: 'x' },
    };
    await expect(markWebhookProcessed(req)).resolves.toBe(true);
    expect(redisSet).not.toHaveBeenCalled();
  });

  it('is a no-op when the request carried no event id', async () => {
    await expect(markWebhookProcessed({})).resolves.toBe(true);
    expect(findOrCreate).not.toHaveBeenCalled();
  });

  it('defaults the event type when the payload omits it', async () => {
    await markWebhookProcessed({ _webhookEventId: 'evt_notype', webhookEvent: {} });
    expect(findOrCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        defaults: expect.objectContaining({ event_type: 'unknown' }),
      })
    );
  });
});
