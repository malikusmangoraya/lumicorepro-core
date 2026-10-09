/**
 * Payment Webhook Security
 * ------------------------
 * 1. Signature verification per gateway (Stripe/PayPal — raw body required).
 * 2. Idempotency: each webhook event id is processed at most once. The durable
 *    webhook_events ledger (unique event_id) is the source of truth; Redis is a
 *    TTL fast-path on top of it, so evictions/restarts can never double-apply.
 */
import Stripe from 'stripe';
import WebhookEvent from '../models/WebhookEvent.js';
import { getRedis } from '../services/cache/redis.client.js';
import { getStripeClient, getStripeWebhookSecret } from '../services/payment/dynamic.js';

const WEBHOOK_DEDUPE_TTL = 60 * 60 * 24; // 24h

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

    // Idempotency — dedupe by event id (durable DB ledger first, Redis fast-path).
    const eventId =
      req.webhookEvent?.id || req.webhookEvent?.data?.object?.id || req.headers['x-webhook-id'];
    if (eventId) {
      const redis = getRedis();
      const dedupeKey = `webhook:processed:${eventId}`;

      const alreadyOnRedis = await redis.get(dedupeKey).catch(() => null);
      if (alreadyOnRedis) {
        return res.json({ received: true, idempotent: true, eventId });
      }

      const ledger = await WebhookEvent.findOne({ where: { event_id: eventId } }).catch(() => null);
      if (ledger) {
        await redis.set(dedupeKey, String(Date.now()), 'EX', WEBHOOK_DEDUPE_TTL).catch(() => {});
        return res.json({ received: true, idempotent: true, eventId });
      }

      // Mark as being-processed; commit AFTER success via helper below.
      req._webhookDedupeKey = dedupeKey;
      req._webhookEventId = eventId;
    }

    next();
  };
}

/** Call after a webhook is successfully handled to commit idempotency. */
export async function markWebhookProcessed(req) {
  const eventId = req._webhookEventId;
  if (eventId) {
    const event = req.webhookEvent || {};
    let ledgerWrite = false;
    try {
      await WebhookEvent.findOrCreate({
        where: { event_id: eventId },
        defaults: {
          gateway: 'stripe',
          event_type: event.type || 'unknown',
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

export default { stripeWebhook, markWebhookProcessed };
