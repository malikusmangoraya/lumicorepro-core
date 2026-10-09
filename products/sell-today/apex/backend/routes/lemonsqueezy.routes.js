/**
 * Lemon Squeezy routes
 * --------------------
 * Mounted automatically at /api/lemonsqueezy by the server bootstrap:
 *
 *   GET  /config    public storefront configuration (safe to expose)
 *   POST /checkout  returns a hosted checkout URL for the selected plan
 *   POST /webhook   delivery endpoint, HMAC-SHA256 verified and idempotent
 *
 * Signature verification needs the untouched request bytes; server.js reads
 * them into a Buffer before the JSON parsers run, so req.body is a Buffer here.
 */
import express from 'express';
import crypto from 'crypto';

import { optionalProtect } from '../middleware/auth.js';
import { paymentLimiter } from '../middleware/rateLimit.js';
import WebhookEvent from '../models/WebhookEvent.js';
import Payment from '../models/Payment.js';
import Order from '../models/Order.js';
import logger from '../utils/logger.js';
import {
  UNCONFIGURED_MESSAGE,
  applyEvent,
  createCheckout,
  getRuntimeConfig,
  verifyWebhookSignature,
} from '../services/payment/lemonsqueezy.service.js';

const router = express.Router();

/**
 * GET /config — what the storefront needs before it opens checkout.
 */
router.get('/config', async (req, res, next) => {
  try {
    const config = await getRuntimeConfig();
    res.json({
      success: true,
      configured: config.configured,
      checkoutMode: config.checkoutMode,
      storeId: config.storeId || null,
      webhooks: {
        url: `${req.baseUrl}/webhook`,
        signatureVerified: Boolean(config.webhookSecret),
      },
      unconfiguredMessage: UNCONFIGURED_MESSAGE,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /checkout — hosted checkout for the selected plan.
 * Sign-in is optional: visitors can pay, and signed-in buyers are attributed
 * to their account and their open order.
 */
router.post('/checkout', optionalProtect, paymentLimiter, async (req, res, next) => {
  try {
    const { variantId, planName, amount, currency, orderId, email, redirectUrl, customData } =
      req.body || {};
    const user = req.user || null;

    let order = null;
    const localOrderId = Number.parseInt(orderId, 10);
    if (Number.isFinite(localOrderId)) {
      order = await Order.findByPk(localOrderId).catch(() => null);
      if (order && user && order.user_id !== user.id && user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          error: 'Not authorized to check out this order',
        });
      }
    }

    const orderAmount = order ? Number(order.totalPrice) : 0;
    const checkout = await createCheckout({
      planName,
      variantId,
      amount: amount ?? (orderAmount || undefined),
      currency: currency || undefined,
      userId: user?.id,
      orderId: order?.id,
      email: email || user?.email,
      customData: customData || {},
      redirectUrl,
    });

    if (!checkout.configured) {
      return res.status(503).json({
        success: false,
        configured: false,
        error: checkout.message || UNCONFIGURED_MESSAGE,
      });
    }

    const amountValue = Number(amount ?? orderAmount) || 0;
    let paymentId = null;
    if (amountValue > 0) {
      try {
        const payment = await Payment.create({
          user_id: user?.id || null,
          order_id: order?.id || null,
          gatewayPaymentId: checkout.variant || null,
          amount: amountValue,
          currency: String(currency || 'USD').toLowerCase(),
          status: 'pending',
          provider: 'lemonsqueezy',
          paymentMethod: 'card',
        });
        paymentId = payment.id;
      } catch (error) {
        logger.warn(`Pending Lemon Squeezy payment row skipped: ${error.message}`);
      }
    }

    res.json({
      success: true,
      url: checkout.url,
      mode: checkout.mode,
      paymentId,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /webhook — Lemon Squeezy delivery endpoint.
 * Rejected deliveries get a non-2xx so the sender retries; accepted ones are
 * written to the webhook_events ledger so a retry cannot apply them twice.
 */
router.post('/webhook', async (req, res) => {
  const rawBody = Buffer.isBuffer(req.body)
    ? req.body
    : Buffer.from(typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {}));

  const config = await getRuntimeConfig();
  const signature = req.headers['x-signature'] || '';

  if (config.webhookSecret) {
    if (!verifyWebhookSignature(rawBody, signature, config.webhookSecret)) {
      return res.status(401).json({ success: false, error: 'Invalid Lemon Squeezy signature' });
    }
  } else if (process.env.NODE_ENV === 'production') {
    return res.status(503).json({
      success: false,
      error: 'LEMONSQUEEZY_WEBHOOK_SECRET is not configured',
    });
  } else {
    logger.warn(
      'Lemon Squeezy webhook accepted without signature verification — set LEMONSQUEEZY_WEBHOOK_SECRET'
    );
  }

  let event;
  try {
    event = JSON.parse(rawBody.toString('utf8'));
  } catch {
    return res.status(400).json({ success: false, error: 'Invalid payload' });
  }

  const eventName = event?.meta?.event_name || req.headers['x-event-name'] || 'unknown';
  const eventId =
    event?.meta?.event_id || crypto.createHash('sha256').update(rawBody).digest('hex');

  const seen = await WebhookEvent.findOne({ where: { event_id: eventId } }).catch(() => null);
  if (seen) {
    return res.json({ received: true, idempotent: true, event: eventName });
  }

  try {
    const actions = await applyEvent(eventName, event);
    await WebhookEvent.findOrCreate({
      where: { event_id: eventId },
      defaults: { gateway: 'lemonsqueezy', event_type: eventName, payload: event },
    }).catch((error) => {
      logger.warn(`Lemon Squeezy webhook ledger write failed: ${error.message}`);
    });
    logger.info(`Lemon Squeezy webhook: ${eventName}`);
    return res.json({ received: true, event: eventName, actions });
  } catch (error) {
    logger.error(`Lemon Squeezy webhook failed (${eventName}): ${error.message}`);
    return res.status(500).json({ success: false, error: 'Webhook processing failed' });
  }
});

export default router;
