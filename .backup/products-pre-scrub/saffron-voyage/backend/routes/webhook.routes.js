/**
 * Webhook Routes — Auto-generated for internal event handling
 * Handles inbound webhooks from Stripe and other providers
 * Emits internal events via EventBus for all downstream processing
 */

import express from 'express';
import crypto from 'crypto';
import Stripe from 'stripe';
import { eventBus } from '../utils/event-bus.js';
import { WebhookDelivery } from '../utils/webhook-delivery.js';
import WebhookLog from '../models/WebhookLog.js';
import logger from '../utils/logger.js';

const router = express.Router();
const stripe = process.env.STRIPE_SECRET_KEY ? new Stripe(process.env.STRIPE_SECRET_KEY) : null;

// ── Registered internal events ──────────────────────────────────────────
export const REGISTERED_EVENTS = [
  'subscription.created',
  'subscription.upgraded',
  'subscription.downgraded',
  'subscription.cancelled',
  'invoice.paid',
  'invoice.failed',
  'user.registered',
  'user.trial_started',
  'user.trial_expiring',
  'feature.limit_reached',
];

// ── HMAC-SHA256 Signature Verification ──────────────────────────────────
function verifySignature(payload, signature, secret) {
  if (!secret || !signature) return false;
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(expected, 'hex'));
}

/**
 * POST /api/webhooks/stripe
 * Stripe webhook endpoint — raw body required for signature verification
 */
router.post('/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  let event;
  try {
    if (stripe && secret && sig) {
      event = stripe.webhooks.constructEvent(req.body, sig, secret);
    } else {
      event = JSON.parse(req.body.toString());
    }
  } catch (err) {
    logger.error(`Stripe webhook signature failed: ${err.message}`);
    return res.status(400).json({ error: `Webhook Error: ${err.message}` });
  }

  // Log the delivery
  await WebhookLog.create({
    source: 'stripe',
    event: event.type,
    payload: JSON.stringify(event),
    status: 'received',
  }).catch(() => {});

  // Emit to internal event bus
  const internalEvent = `stripe.${event.type}`;
  eventBus.emit(internalEvent, event.data.object);
  eventBus.emit('stripe.*', { type: event.type, data: event.data.object });

  logger.info(`Stripe webhook: ${event.type}`);
  res.json({ received: true });
});

/**
 * POST /api/webhooks/custom
 * Generic inbound webhook endpoint with HMAC signature verification
 * Consumers register endpoints via the webhook registry
 */
router.post('/custom/:source', express.json(), async (req, res) => {
  const { source } = req.params;
  const signature = req.headers['x-webhook-signature'] || req.headers['x-hub-signature-256'];
  const secret = process.env[`WEBHOOK_SECRET_${source.toUpperCase()}`];

  if (secret && signature) {
    const rawBody = JSON.stringify(req.body);
    const isValid = verifySignature(rawBody, signature.replace('sha256=', ''), secret);
    if (!isValid) {
      logger.warn(`Invalid webhook signature for source: ${source}`);
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  const eventType = req.headers['x-webhook-event'] || req.body.event || 'unknown';
  await WebhookLog.create({
    source,
    event: eventType,
    payload: JSON.stringify(req.body),
    status: 'received',
  }).catch(() => {});

  eventBus.emit(`${source}.${eventType}`, req.body);
  logger.info(`Custom webhook: ${source}/${eventType}`);
  res.json({ received: true });
});

/**
 * POST /api/webhooks/emit
 * Internal endpoint to trigger events programmatically (authenticated)
 * Used by backend services to fire events for downstream processing
 */
router.post('/emit', async (req, res, next) => {
  try {
    const { event, data, secret } = req.body;
    if (!event) return res.status(400).json({ error: 'event is required' });

    // Optional internal secret check
    const internalSecret = process.env.INTERNAL_WEBHOOK_SECRET;
    if (internalSecret && secret !== internalSecret) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!REGISTERED_EVENTS.includes(event)) {
      return res.status(400).json({ error: `Unknown event: ${event}. See WEBHOOKS.md` });
    }

    eventBus.emit(event, data || {});
    await WebhookLog.create({
      source: 'internal',
      event,
      payload: JSON.stringify(data),
      status: 'emitted',
    }).catch(() => {});

    logger.info(`Internal event emitted: ${event}`);
    res.json({ success: true, event });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/webhooks/logs
 * Return recent webhook delivery logs (admin only in production)
 */
router.get('/logs', async (req, res, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit || '50'), 200);
    const logs = await WebhookLog.find({}).sort({ createdAt: -1 }).limit(limit);
    res.json({ logs });
  } catch (err) {
    next(err);
  }
});

export default router;
