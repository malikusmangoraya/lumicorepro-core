/**
 * Payment Webhook Security
 * ------------------------
 * 1. Signature verification per gateway:
 *      - Stripe: local signature check (`stripe-signature` + signing secret).
 *      - PayPal: remote verification via PayPal's
 *        POST /v1/notifications/verify-webhook-signature endpoint, because
 *        PayPal signs with a rotating certificate that cannot be checked
 *        locally. `PAYPAL_WEBHOOK_ID` is required; the route fails closed
 *        (400) outside an explicit development bypass.
 * 2. Idempotency: each webhook event id is processed at most once. The durable
 *    webhook_events ledger (unique event_id) is the source of truth; Redis is a
 *    TTL fast-path on top of it, so evictions/restarts can never double-apply.
 */
import WebhookEvent from '../models/WebhookEvent.js';
import { getRedis } from '../services/cache/redis.client.js';
import { getStripeClient, getStripeWebhookSecret } from '../services/payment/dynamic.js';
import paypalService from '../services/payment/paypal.service.js';
import logger from '../utils/logger.js';
import { fail } from '../utils/response.js';

const WEBHOOK_DEDUPE_TTL = 60 * 60 * 24; // 24h

/**
 * Idempotency gate shared by every gateway.
 *
 * Checks the Redis fast-path first, then the durable ledger. On a first-time
 * event it stores the dedupe bookkeeping on the request for
 * `markWebhookProcessed()` to commit after successful handling.
 *
 * @param {import('express').Request} req - Request with `webhookEvent` attached
 * @returns {Promise<object|null>} replay response body, or null to continue
 */
async function checkIdempotency(req) {
  const eventId =
    req.webhookEvent?.id || req.webhookEvent?.data?.object?.id || req.headers['x-webhook-id'];
  if (!eventId) return null;

  const redis = getRedis();
  const dedupeKey = `webhook:processed:${eventId}`;

  const alreadyOnRedis = await redis.get(dedupeKey).catch(() => null);
  if (alreadyOnRedis) {
    return { received: true, idempotent: true, eventId };
  }

  const ledger = await WebhookEvent.findOne({ where: { event_id: eventId } }).catch(() => null);
  if (ledger) {
    await redis.set(dedupeKey, String(Date.now()), 'EX', WEBHOOK_DEDUPE_TTL).catch(() => {});
    return { received: true, idempotent: true, eventId };
  }

  // Mark as being-processed; commit AFTER success via helper below.
  req._webhookDedupeKey = dedupeKey;
  req._webhookEventId = eventId;
  return null;
}

/**
 * Stripe signature verification middleware.
 * Call AFTER express.raw({ type: 'application/json' }) on the webhook route.
 */
export function stripeWebhook(middlewareConfig = {}) {
  return async (req, res, next) => {
    const sig = req.headers['stripe-signature'];
    const endpointSecret = (await getStripeWebhookSecret()) || process.env.STRIPE_WEBHOOK_SECRET;

    const stripe = await getStripeClient();

    // Verify signature + validity
    if (stripe && endpointSecret && sig) {
      try {
        req.rawBody = req.body;
        req.webhookEvent = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
      } catch (err) {
        return res.status(400).send(`Webhook signature verification failed: ${err.message}`);
      }
    } else if (middlewareConfig.allowUnsigned === true && process.env.NODE_ENV !== 'production') {
      // Non-production: allow unsigned for local integration tests
      req.rawBody = req.body;
      try {
        req.webhookEvent = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
      } catch {
        return res.status(400).send('Invalid webhook body');
      }
    } else {
      return res.status(403).json({ success: false, error: 'Webhook signature required' });
    }

    req._webhookGateway = 'stripe';

    const duplicate = await checkIdempotency(req);
    if (duplicate) return res.json(duplicate);

    next();
  };
}

/**
 * PayPal webhook verification middleware.
 * Call AFTER express.raw({ type: 'application/json' }) on the webhook route.
 *
 * Verification flow:
 *   1. Parse the raw body (PayPal signs the exact bytes it delivered).
 *   2. Resolve the webhook id (SystemConfig → PAYPAL_WEBHOOK_ID).
 *      Missing id  → 400 (fail closed), except in development where an explicit
 *      warning is logged and verification is skipped.
 *   3. POST the `paypal-transmission-*` headers + event back to PayPal and
 *      require `verification_status === 'SUCCESS'`; anything else → 400.
 *   4. Dedupe by event id so replays never re-apply fulfilment.
 */
export function paypalWebhook() {
  return async (req, res, next) => {
    if (res.headersSent) return next();

    const headers = req.headers || {};

    let event;
    try {
      event = Buffer.isBuffer(req.body) ? JSON.parse(req.body.toString('utf8')) : req.body;
      if (!event || typeof event !== 'object') throw new Error('webhook body is not an object');
    } catch {
      return fail(res, 'INVALID_PAYLOAD', 'Invalid webhook body', 400);
    }

    req.rawBody = req.body;
    req.webhookEvent = event;
    req._webhookGateway = 'paypal';

    const webhookId = await paypalService.getWebhookId().catch(() => '');
    if (!webhookId) {
      if (process.env.NODE_ENV !== 'development') {
        logger.error('PayPal webhook rejected: PAYPAL_WEBHOOK_ID is not configured');
        return fail(res, 'WEBHOOK_NOT_CONFIGURED', 'PayPal webhook is not configured', 400);
      }
      logger.warn(
        'PAYPAL_WEBHOOK_ID is not set — SKIPPING PayPal webhook signature verification (development only)',
      );
    } else {
      let verified = false;
      try {
        verified = await paypalService.verifyWebhookSignature({
          transmissionId: headers['paypal-transmission-id'],
          transmissionTime: headers['paypal-transmission-time'],
          transmissionSig: headers['paypal-transmission-sig'],
          certUrl: headers['paypal-cert-url'],
          authAlgo: headers['paypal-auth-algo'],
          webhookId,
          webhookEvent: event,
        });
      } catch (err) {
        logger.error(`PayPal webhook verification error: ${err.message}`);
        return fail(res, 'WEBHOOK_VERIFICATION_FAILED', 'PayPal webhook verification failed', 400);
      }

      if (!verified) {
        logger.warn('PayPal webhook rejected: signature verification failed');
        return fail(res, 'WEBHOOK_VERIFICATION_FAILED', 'PayPal webhook verification failed', 400);
      }
    }

    const duplicate = await checkIdempotency(req);
    if (duplicate) return res.json(duplicate);

    return next();
  };
}

/**
 * Call after a webhook is successfully handled to commit idempotency.
 *
 * @param {import('express').Request} req - Request carrying the dedupe ids
 * @param {string|null} [gateway=null] - Override; defaults to the middleware tag
 * @returns {Promise<boolean>} always true (best-effort bookkeeping)
 */
export async function markWebhookProcessed(req, gateway = null) {
  const eventId = req._webhookEventId;
  if (eventId) {
    const event = req.webhookEvent || {};
    let ledgerWrite = false;
    try {
      await WebhookEvent.findOrCreate({
        where: { event_id: eventId },
        defaults: {
          gateway: gateway || req._webhookGateway || 'stripe',
          event_type: event.type || event.event_type || 'unknown',
          payload: event,
        },
      });
      ledgerWrite = true;
    } catch {
      // Unique-constraint race: another delivery committed first — idempotent.
    }
    if (req._webhookDedupeKey && ledgerWrite) {
      await getRedis().set(req._webhookDedupeKey, String(Date.now()), 'EX', WEBHOOK_DEDUPE_TTL);
    }
  }
  return true;
}

export default { stripeWebhook, paypalWebhook, markWebhookProcessed };
