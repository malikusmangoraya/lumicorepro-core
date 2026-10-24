/**
 * LumicorePro Payment Routes — Enterprise Multi-Gateway
 * Stripe (Visa/Mastercard/Amex) + PayPal + Razorpay
 * All DB operations use Sequelize/PostgreSQL with ACID transactions.
 */
import express from 'express';
import Stripe from 'stripe';
import Order from '../models/Order.js';
import Payment from '../models/Payment.js';
import Notification from '../models/Notification.js';
import { protect, authorize } from '../middleware/auth.js';
import { paymentLimiter } from '../middleware/rateLimit.js';
import { stripeWebhook, paypalWebhook, markWebhookProcessed } from '../middleware/webhookSecurity.js';
import logger from '../utils/logger.js';
import resp from '../utils/response.js';
import { generateInvoiceHTML } from '../utils/invoiceGenerator.js';
import stripeService from '../services/payment/stripe.service.js';
import paypalService from '../services/payment/paypal.service.js';
import paddleService from '../services/payment/paddle.service.js';
import razorpayService from '../services/payment/razorpay.service.js';
import Plan from '../models/Plan.js';
import User from '../models/User.js';
import Subscription from '../models/Subscription.js';
import { sequelize } from '../config/database.js';
import { getEnabledGateways, getGatewayConfig, isGatewayEnabled } from '../services/payment/config.js';
import {
  gatewayReady,
  getStripeClient,
  getStripePublishableKey,
  getGatewayRuntimeConfig,
  UNCONFIGURED_MESSAGE,
} from '../services/payment/dynamic.js';
import systemConfig from '../services/systemConfig.service.js';
import { orderOwnershipError } from '../utils/orderOwnership.js';

const router = express.Router();

const { ok, fail } = resp;

/**
 * Dynamic Stripe client — resolved per request from the runtime SystemConfig
 * (DB-backed, Redis-cached) with process.env as fallback. Null when unconfigured.
 */
async function stripe() {
  return getStripeClient();
}

/* ══════════════════════════════════════════════════════════════════
 * GET /config — unified payment configuration for frontend
 * Shows which gateways are enabled + publishable keys (runtime config)
 * ══════════════════════════════════════════════════════════════════ */
router.get('/config', async (req, res, next) => {
  try {
    const enabledGateways = getEnabledGateways();
    const stripeCfg = await getGatewayRuntimeConfig('stripe');
    const paypalCfg = await getGatewayRuntimeConfig('paypal');
    const publicCfg = await systemConfig.getPublicConfig();

    const currency = publicCfg?.currency || {};
    const defaultCurrency = (currency.code || process.env.DEFAULT_CURRENCY || 'USD').toUpperCase();

    res.json({
      success: true,
      configured: Boolean(stripeCfg.enabled || paypalCfg.enabled),
      unconfiguredMessage: UNCONFIGURED_MESSAGE,
      defaultCurrency,
      supportedCurrencies: ['USD','EUR','GBP','PKR','INR','AED','SAR','BRL','MXN','CAD','AUD','JPY'],
      business: publicCfg?.business || {},
      gateways: {
        stripe: {
          enabled: stripeCfg.enabled,
          publishableKey: stripeCfg.publishableKey || 'pk_test_placeholder',
          methods: ['visa', 'mastercard', 'amex', 'discover', 'apple_pay', 'google_pay'],
        },
        paypal: {
          enabled: paypalCfg.enabled,
          clientId: paypalCfg.clientId || '',
          mode: paypalCfg.mode || 'sandbox',
        },
        razorpay: {
          enabled: isGatewayEnabled('razorpay'),
          keyId: process.env.RAZORPAY_KEY_ID || '',
        },
        paddle: {
          enabled: isGatewayEnabled('paddle'),
          environment: process.env.PADDLE_ENV || 'sandbox',
        },
      },
      supportedMethods: ['visa', 'mastercard', 'amex', 'paypal', 'stripe', 'paddle', 'cod'],
      isLive: Boolean(stripeCfg.enabled),
      enabledGateways,
    });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * STRIPE — Visa / Mastercard / Amex / Apple Pay / Google Pay
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /create-intent — Create a Stripe PaymentIntent (card charge)
 */
router.post('/create-intent', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { orderId, amount, currency } = req.body;

    let targetAmount = amount;
    let order = null;
    let orderCurrency = (currency || process.env.DEFAULT_CURRENCY || 'USD').toUpperCase();

    if (orderId) {
      order = await Order.findByPk(orderId);
      if (!order) {
        return res.status(404).json({ success: false, error: 'Order not found' });
      }
      const ownErr = orderOwnershipError(order, req.user);
      if (ownErr) return res.status(ownErr.status).json({ success: false, error: ownErr.error });
      targetAmount = parseFloat(order.totalPrice);
      orderCurrency = (order.currency || orderCurrency).toUpperCase();
    }

    if (!Number.isFinite(Number(targetAmount)) || Number(targetAmount) <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
    }
    targetAmount = Number(targetAmount);

    // A second intent for the same order is a second charge: a double click or a
    // retried checkout must reuse the pending one, never open another.
    if (order) {
      const pending = await Payment.findOne({
        where: { order_id: order.id, provider: 'stripe', status: 'pending' },
      });
      if (pending) {
        return res.status(409).json({
          success: false,
          error: 'A payment is already pending for this order',
          paymentIntentId: pending.stripePaymentIntentId,
          paymentId: pending.id,
        });
      }
    }

    const amountInCents = Math.round(targetAmount * 100);

    let clientSecret = '';
    let paymentIntentId = '';

    const stripeClient = await stripe();
    if (stripeClient) {
      const paymentIntent = await stripeClient.paymentIntents.create({
        amount: amountInCents,
        currency: orderCurrency.toLowerCase(),
        metadata: {
          userId: String(req.user.id),
          orderId: order ? String(order.id) : '',
          paymentMethod: 'card',
        },
      });
      clientSecret = paymentIntent.client_secret;
      paymentIntentId = paymentIntent.id;
    } else {
      const { ok: ready } = await gatewayReady('stripe');
      if (!ready) {
        // Canonical envelope; HTTP status is unchanged (200) for compatibility.
        return fail(res, 'PAYMENT_UNCONFIGURED', UNCONFIGURED_MESSAGE, 200);
      }
      paymentIntentId = `pi_mock_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
      clientSecret = `${paymentIntentId}_secret_${Math.random().toString(36).substring(2, 8)}`;
    }

    const payment = await Payment.create({
      user_id: req.user.id,
      order_id: order ? order.id : null,
      stripePaymentIntentId: paymentIntentId,
      amount: targetAmount,
      currency: orderCurrency.toLowerCase(),
      status: 'pending',
      provider: 'stripe',
      paymentMethod: 'card',
    });

    res.json({
      success: true,
      clientSecret,
      paymentIntentId,
      paymentId: payment.id,
      amount: targetAmount,
      // The currency actually charged and persisted, not the client's claim.
      currency: orderCurrency.toLowerCase(),
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /confirm — Confirm Stripe payment + update order (ACID transaction)
 */
router.post('/confirm', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { paymentIntentId, orderId, cardDetails } = req.body;

    // A Payment row belongs to the buyer who created it. Without this filter any
    // authenticated user could confirm another user's intent by guessing the id.
    const paymentWhere = { stripePaymentIntentId: paymentIntentId };
    if (req.user?.role !== 'admin') paymentWhere.user_id = req.user?.id;

    const payment = await Payment.findOne({ where: paymentWhere });
    if (!payment) {
      return res.status(404).json({ success: false, error: 'Payment intent not found' });
    }

    const intent = await stripeService.verifyPaymentIntent(paymentIntentId);
    const stripeClient = await stripe();
    if (stripeClient && !intent.succeeded) {
      await payment.update({ status: intent.status === 'failed' ? 'failed' : 'processing' });
      return res.status(400).json({
        success: false,
        error: `Payment not confirmed by gateway (status: ${intent.status})`,
      });
    }

    let result;
    try {
      result = await sequelize.transaction(async (t) => {
        const paymentUpdates = { status: 'succeeded', stripeChargeId: cardDetails?.charge || null };
        if (cardDetails) paymentUpdates.cardDetails = cardDetails;
        await payment.update(paymentUpdates, { transaction: t });

        let order = null;
        const targetOrderId = orderId || (payment && payment.order_id);

        if (targetOrderId) {
          order = await Order.findByPk(targetOrderId, { transaction: t });
          if (order) {
            // The client sends `orderId`, so it is a claim about a row the caller
            // may not own. Aborting here rolls the payment update back too.
            const ownErr = orderOwnershipError(order, req.user);
            if (ownErr) {
              const abort = new Error(ownErr.error);
              abort.statusCode = ownErr.status;
              throw abort;
            }
            await order.update({
              isPaid: true,
              paidAt: new Date(),
              status: 'processing',
              paymentResult: {
                id: paymentIntentId,
                status: 'succeeded',
                updateTime: new Date().toISOString(),
                emailAddress: req.user.email,
              },
            }, { transaction: t });

            await Notification.create({
              recipient: order.user_id == null ? req.user.id : order.user_id,
              type: 'payment',
              title: 'Payment Successful',
              message: `Payment of $${parseFloat(order.totalPrice).toFixed(2)} for order #${order.orderNumber} received.`,
              link: '/templates/ecommerce/OrdersHistory',
              metadata: {},
            }, { transaction: t });
          }
        }

        return { payment, order };
      });
    } catch (txError) {
      if (txError.statusCode) {
        return res.status(txError.statusCode).json({ success: false, error: txError.message });
      }
      throw txError;
    }

    logger.info(`Payment confirmed: ${paymentIntentId} for user ${req.user.email}`);

    res.json({
      success: true,
      message: 'Payment confirmed successfully',
      payment: result.payment,
      order: result.order,
    });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * PAYPAL — Create Order → Approve → Capture
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /paypal/create-order — Create PayPal Checkout Order
 */
router.post('/paypal/create-order', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { orderId, amount, currency = 'usd', description } = req.body;

    let targetAmount = amount;
    let order = null;
    let currencyCode = (currency || process.env.DEFAULT_CURRENCY || 'USD').toUpperCase();

    if (orderId) {
      order = await Order.findByPk(orderId);
      if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
      const ownErr = orderOwnershipError(order, req.user);
      if (ownErr) return res.status(ownErr.status).json({ success: false, error: ownErr.error });
      targetAmount = parseFloat(order.totalPrice);
      // The order is the source of truth for both amount and currency; the
      // client's `currency` only applies to orders-less payments.
      currencyCode = (order.currency || currencyCode).toUpperCase();
    }

    if (!Number.isFinite(Number(targetAmount)) || Number(targetAmount) <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
    }
    targetAmount = Number(targetAmount);

    const paypalOrder = await paypalService.createOrder({
      amount: targetAmount,
      currency: currencyCode,
      orderId: order?.id,
      description: description || `Order ${order?.orderNumber || 'N/A'}`,
    });

    // Record pending payment
    const payment = await Payment.create({
      user_id: req.user.id,
      order_id: order?.id || null,
      stripePaymentIntentId: paypalOrder.id,
      amount: targetAmount,
      currency: currencyCode,
      status: 'pending',
      provider: 'paypal',
      paymentMethod: 'paypal',
    });

    res.json({
      success: true,
      paypalOrderId: paypalOrder.id,
      approvalUrl: paypalOrder.approvalUrl,
      paymentId: payment.id,
      mock: paypalOrder.mock || false,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /paypal/capture — Capture a PayPal order after user approves
 */
router.post('/paypal/capture', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { paypalOrderId, orderId } = req.body;

    if (!paypalOrderId) {
      return res.status(400).json({ success: false, error: 'paypalOrderId is required' });
    }

    // Resolve and authorize the payment BEFORE capturing: captureOrder moves
    // money, and an unknown or foreign PayPal order id must never reach it.
    const paymentWhere = { stripePaymentIntentId: paypalOrderId, provider: 'paypal' };
    if (req.user?.role !== 'admin') paymentWhere.user_id = req.user?.id;

    const payment = await Payment.findOne({ where: paymentWhere });
    if (!payment) {
      return res.status(404).json({ success: false, error: 'PayPal payment not found' });
    }

    const captureResult = await paypalService.captureOrder({ orderId: paypalOrderId });

    const result = await sequelize.transaction(async (t) => {
      await payment.update({
        status: captureResult.success ? 'succeeded' : 'failed',
        stripeChargeId: captureResult.captureId || null,
        providerResponse: { paypalOrderId, captureId: captureResult.captureId, status: captureResult.status },
      }, { transaction: t });

      let order = null;
      const targetOrderId = orderId || payment.order_id;

      if (targetOrderId && captureResult.success) {
        order = await Order.findByPk(targetOrderId, { transaction: t });
        if (order) {
          const ownErr = orderOwnershipError(order, req.user);
          if (ownErr) {
            const abort = new Error(ownErr.error);
            abort.statusCode = ownErr.status;
            throw abort;
          }
          await order.update({
            isPaid: true,
            paidAt: new Date(),
            status: 'processing',
            paymentResult: {
              id: paypalOrderId,
              status: 'succeeded',
              provider: 'paypal',
              updateTime: new Date().toISOString(),
              emailAddress: req.user.email,
            },
          }, { transaction: t });

          await Notification.create({
            recipient: order.user_id == null ? req.user.id : order.user_id,
            type: 'payment',
            title: 'PayPal Payment Successful',
            message: `PayPal payment of $${parseFloat(order.totalPrice).toFixed(2)} for order #${order.orderNumber} received.`,
            link: '/templates/ecommerce/OrdersHistory',
            metadata: {},
          }, { transaction: t });
        }
      }

      return { payment, order };
    });

    logger.info(`PayPal capture: ${paypalOrderId} by ${req.user.email}`);

    res.json({
      success: captureResult.success,
      message: captureResult.success ? 'Payment captured successfully' : 'Payment capture failed',
      payment: result.payment,
      order: result.order,
    });
  } catch (error) {
    if (error.statusCode) {
      return res.status(error.statusCode).json({ success: false, error: error.message });
    }
    next(error);
  }
});

/**
 * POST /paypal/webhook — PayPal webhook handler
 *
 * Every delivery is signature-verified against PayPal's
 * POST /v1/notifications/verify-webhook-signature endpoint (see
 * middleware/webhookSecurity.js → paypalWebhook) and deduplicated by event id
 * via the durable webhook_events ledger. `PAYMENT.CAPTURE.COMPLETED` marks the
 * matching payment + order paid inside one transaction; a delivery whose
 * payment/order cannot be found is logged and still acknowledged with 200 so
 * PayPal stops retrying.
 */
router.post(
  '/paypal/webhook',
  express.raw({ type: 'application/json' }),
  paypalWebhook(),
  async (req, res) => {
    try {
      const event = req.webhookEvent;
      const result = await paypalService.handleWebhook(event);

      await markWebhookProcessed(req);

      return ok(res, {
        received: true,
        eventId: event?.id || null,
        handled: result?.handled === true,
      });
    } catch (error) {
      // Verification + dedupe already passed; only fulfilment failed.
      if (res.headersSent) return res;
      logger.error(`PayPal webhook error: ${error.message}`);
      return fail(res, 'WEBHOOK_PROCESSING_FAILED', 'Webhook processing failed', 400);
    }
  },
);

/* ══════════════════════════════════════════════════════════════════
 * PADDLE — Merchant of Record (cards + PayPal + sales tax handled)
 * ══════════════════════════════════════════════════════════════════ */
router.post('/paddle/checkout', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { orderId, amount, currency = 'usd', description, customerEmail, successUrl } = req.body;

    let targetAmount = amount;
    let order = null;

    if (orderId) {
      order = await Order.findByPk(orderId);
      if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
      const ownErr = orderOwnershipError(order, req.user);
      if (ownErr) return res.status(ownErr.status).json({ success: false, error: ownErr.error });
      targetAmount = parseFloat(order.totalPrice);
    }

    if (!targetAmount || targetAmount <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
    }

    const checkout = await paddleService.createCheckout({
      amount: targetAmount,
      currency,
      orderId: order?.id,
      description: description || `Order ${order?.orderNumber || 'N/A'}`,
      customerEmail,
      successUrl,
    });

    const payment = await Payment.create({
      user_id: req.user.id,
      order_id: order?.id || null,
      gatewayPaymentId: checkout.id,
      amount: targetAmount,
      currency,
      status: 'pending',
      provider: 'paddle',
      paymentMethod: 'card',
    });

    res.json({
      success: true,
      paddleTransactionId: checkout.id,
      checkoutUrl: checkout.checkoutUrl,
      paymentId: payment.id,
      mock: checkout.mock || false,
    });
  } catch (error) {
    next(error);
  }
});

router.post('/paddle/webhook', express.raw({ type: 'application/json' }), async (req, res, next) => {
  try {
    const rawBody = req.body.toString();
    const signature = req.headers['paddle-signature'] || '';
    if (!paddleService.verifyWebhook(rawBody, signature)) {
      return res.status(401).json({ success: false, error: 'Invalid Paddle signature' });
    }

    const event = JSON.parse(rawBody);
    const eventType = event?.event_type || '';

    // Paddle fires `transaction.paid` when the money lands and
    // `transaction.completed` when the transaction closes. Matching on
    // "completed" alone left every paid-but-not-yet-closed payment pending
    // forever, and the else-branch fallback only logs.
    const isPaidEvent = eventType === 'transaction.paid' || eventType === 'transaction.completed';

    if (isPaidEvent) {
      const data = event.data || {};
      const txnId = data.id || data.transaction_id;
      const customOrderId = data?.custom_data?.orderId || data?.metadata?.orderId;
      if (txnId) {
        const payment = await Payment.findOne({ where: { gatewayPaymentId: txnId } })
          || (customOrderId ? await Payment.findOne({ where: { order_id: customOrderId, provider: 'paddle' } }) : null);
        if (payment) {
          await payment.update({ status: 'succeeded', gatewayPaymentId: txnId });
          logger.info(`Paddle payment confirmed: ${txnId} (payment ${payment.id})`);
        }
      }
    } else {
      await paddleService.handleWebhook(event);
    }

    res.json({ received: true });
  } catch (error) {
    logger.error(`Paddle webhook error: ${error.message}`);
    res.status(400).json({ success: false, error: 'Webhook processing failed' });
  }
});

/* ══════════════════════════════════════════════════════════════════
 * RAZORPAY — India (UPI / cards / wallets)
 * ══════════════════════════════════════════════════════════════════ */
router.post('/razorpay/create-order', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { orderId, amount, currency = 'INR', receipt } = req.body;
    let targetAmount = amount;
    let targetOrder = null;

    if (orderId) {
      targetOrder = await Order.findByPk(orderId);
      const ownErr = orderOwnershipError(targetOrder, req.user);
      if (ownErr) return res.status(ownErr.status).json({ success: false, error: ownErr.error });
      targetAmount = parseFloat(targetOrder.totalPrice);
    }

    if (!Number.isFinite(Number(targetAmount)) || Number(targetAmount) <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
    }
    targetAmount = Number(targetAmount);

    const rzpOrder = await razorpayService.createOrder({
      amount: targetAmount,
      currency,
      receipt: receipt || `rcpt_${Date.now()}`,
      notes: { userId: String(req.user.id), orderId: orderId ? String(orderId) : '' },
    });

    // Without this row the gateway order existed only in Razorpay's account:
    // /refund could not find a transaction to return and the ledger had no
    // record of the money owed to the buyer.
    const payment = await Payment.create({
      user_id: req.user.id,
      order_id: targetOrder?.id || null,
      gatewayPaymentId: rzpOrder.id,
      amount: targetAmount,
      currency,
      status: 'pending',
      provider: 'razorpay',
      paymentMethod: 'upi',
    });

    res.json({
      success: true,
      orderId: rzpOrder.id,
      amount: rzpOrder.amount,
      currency: rzpOrder.currency || currency,
      keyId: razorpayService.getKeyId(),
      paymentId: payment.id,
      mock: rzpOrder.mock || false,
    });
  } catch (error) {
    next(error);
  }
});

router.post('/razorpay/verify', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { orderId, paymentId, signature } = req.body;
    if (!orderId || !paymentId || !signature) {
      return res
        .status(400)
        .json({ success: false, error: 'orderId, paymentId and signature are required' });
    }
    const valid = await razorpayService.verifyPayment({ orderId, paymentId, signature });
    if (!valid) {
      return res.status(400).json({ success: false, error: 'Payment signature verification failed' });
    }

    // The gateway order id is what create-order stored; the refund API needs the
    // Razorpay *payment* id, so swap it in now that the signature proves it.
    const payment = await Payment.findOne({
      where: { gatewayPaymentId: orderId, provider: 'razorpay', user_id: req.user.id },
    });
    if (payment) {
      await payment.update({
        status: 'succeeded',
        razorpayPaymentId: paymentId,
        gatewayPaymentId: paymentId,
      });
      if (payment.order_id) {
        const order = await Order.findByPk(payment.order_id);
        if (order) {
          await order.update({ isPaid: true, paidAt: new Date(), status: 'processing' });
        }
      }
    } else {
      logger.warn(`Razorpay verify: signature valid but no Payment row for order ${orderId}`);
    }

    res.json({ success: true });
  } catch (error) {
    next(error);
  }
});

router.post('/razorpay/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    const rawBody = req.body?.toString('utf8') || '';
    let event;
    try {
      event = JSON.parse(rawBody);
    } catch {
      return res.status(400).json({ success: false, error: 'Invalid JSON body' });
    }
    const result = await razorpayService.handleWebhook(
      event,
      req.headers['x-razorpay-signature'],
      rawBody
    );
    if (!result.valid) {
      return res.status(401).json({ success: false, error: 'Invalid signature' });
    }
    res.json({ received: true });
  } catch (error) {
    logger.error(`Razorpay webhook error: ${error.message}`);
    res.status(500).json({ success: false, error: 'Webhook processing failed' });
  }
});

/* ══════════════════════════════════════════════════════════════════
 * REFUND — Admin only, works for Stripe, PayPal, Paddle
 * ══════════════════════════════════════════════════════════════════ */
router.post('/refund', protect, authorize('admin'), paymentLimiter, async (req, res, next) => {
  try {
    const { paymentId, amount, reason } = req.body;

    const payment = await Payment.findByPk(paymentId);
    if (!payment) {
      return res.status(404).json({ success: false, error: 'Payment not found' });
    }

    if (payment.status === 'refunded') {
      return res.status(400).json({ success: false, error: 'Payment has already been refunded' });
    }

    const capturedAmount = parseFloat(payment.amount);
    const alreadyRefunded = parseFloat(payment.refundAmount || 0) || 0;
    // `amount || payment.amount` read an explicit 0 as "refund everything", and
    // accepted negative or non-numeric values straight into the ledger.
    const requested = amount === undefined || amount === null ? capturedAmount : Number(amount);
    if (!Number.isFinite(requested) || requested <= 0) {
      return res.status(400).json({ success: false, error: 'Valid refund amount is required' });
    }
    // Two 60% partial refunds of a 100 order would return 120%: cap the lifetime
    // total at what was actually captured.
    const refundable = capturedAmount - alreadyRefunded;
    if (requested > refundable) {
      return res.status(400).json({
        success: false,
        error: `Refund exceeds the remaining ${refundable.toFixed(2)} on this payment`,
      });
    }

    const refundAmount = requested;
    const isFullRefund = alreadyRefunded + refundAmount >= capturedAmount;
    const refundCurrency = (payment.currency || 'USD').toLowerCase();

    // Gateway-specific refund. If no gateway can actually process this payment
    // we must NOT mark it refunded in the DB — that silently reports money
    // returned while nothing left the provider.
    let gatewayRefunded = false;
    if (payment.provider === 'paypal' && payment.stripePaymentIntentId) {
      await paypalService.refund({ paymentId: payment.stripePaymentIntentId, amount: refundAmount });
      gatewayRefunded = true;
    } else if (payment.provider === 'paddle' && payment.gatewayPaymentId) {
      await paddleService.refund({
        transactionId: payment.gatewayPaymentId,
        amount: isFullRefund ? undefined : refundAmount,
        reason,
      });
      gatewayRefunded = true;
    } else if (payment.provider === 'razorpay' && payment.gatewayPaymentId) {
      await razorpayService.refund({
        paymentId: payment.gatewayPaymentId,
        amount: refundAmount,
      });
      gatewayRefunded = true;
    } else if (payment.stripePaymentIntentId && !payment.stripePaymentIntentId.startsWith('pi_mock')) {
      await stripeService.refund({
        paymentId: payment.stripePaymentIntentId,
        amount: isFullRefund ? undefined : refundAmount,
        currency: refundCurrency,
        reason,
      });
      gatewayRefunded = true;
    }

    if (!gatewayRefunded) {
      return res.status(400).json({
        success: false,
        error: 'No refundable gateway transaction found for this payment',
      });
    }

    const newStatus = isFullRefund ? 'refunded' : 'succeeded';
    await payment.update({
      status: newStatus,
      refundAmount: alreadyRefunded + refundAmount,
      refundReason: reason || 'Customer requested refund',
    });

    // A partial refund leaves the order live: flipping it to `refunded` here told
    // buyers their whole order was returned when only part of it was.
    if (isFullRefund && payment.order_id) {
      const order = await Order.findByPk(payment.order_id);
      if (order) await order.update({ status: 'refunded' });
    }

    logger.info(`Refund processed: $${refundAmount} for payment ${paymentId} (${payment.provider})`);

    res.json({
      success: true,
      message: 'Refund processed successfully',
      payment,
    });
  } catch (error) {
    next(error);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * STRIPE CHECKOUT — Sessions for subscriptions / one-time
 * ══════════════════════════════════════════════════════════════════ */
router.post('/checkout', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { planId, orderId, successUrl, cancelUrl } = req.body;

    let priceId = null;
    let mode = 'payment';
    let credits = 0;
    let metadata = {};

    if (planId) {
      const plan = await Plan.findByPk(planId);
      if (!plan || !plan.isActive) {
        return res.status(404).json({ success: false, error: 'Plan not found' });
      }
      priceId = plan.stripePriceId;
      mode = plan.interval === 'one_time' ? 'payment' : 'subscription';
      credits = parseFloat(plan.creditsGrant || 0);
      metadata = { planId: plan.slug };
      // `agentApiKey` used to be copied from the request body into the Stripe
      // metadata and then replayed as `x-api-key` against the agent's credit
      // top-up endpoint. The body is attacker-controlled and nothing ever
      // proved the key belonged to this buyer, so any stolen agent key could be
      // spent from another account. Credits are granted through the backend
      // usage ledger (services/usage.service.js) instead.
    } else if (orderId) {
      const order = await Order.findByPk(orderId);
      if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
      const ownErr = orderOwnershipError(order, req.user);
      if (ownErr) return res.status(ownErr.status).json({ success: false, error: ownErr.error });
      const orderCurrency = (order.currency || process.env.DEFAULT_CURRENCY || 'USD').toUpperCase();
      const session = await stripeService.createPayment({
        amount: parseFloat(order.totalPrice),
        currency: orderCurrency.toLowerCase(),
        orderId: order.id,
      });
      const payment = await Payment.create({
        user_id: req.user.id,
        order_id: order.id,
        stripePaymentIntentId: session.id,
        amount: parseFloat(order.totalPrice),
        currency: orderCurrency.toLowerCase(),
        status: 'pending',
        provider: 'stripe',
        paymentMethod: 'card',
      });
      return res.json({
        success: true,
        paymentIntentId: session.id,
        clientSecret: session.clientSecret,
        paymentId: payment.id,
      });
    }

    if (!priceId) {
      return res.status(400).json({ success: false, error: 'planId or orderId is required' });
    }

    const baseUrl = (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/+$/, '');
    const session = await stripeService.createCheckoutSession({
      user: req.user,
      priceId,
      mode,
      successUrl: successUrl || `${baseUrl}/billing?success=1`,
      cancelUrl: cancelUrl || `${baseUrl}/pricing?canceled=1`,
      metadata,
      credits,
    });

    if (session.customerId && !req.user.stripeCustomerId) {
      await User.update({ stripeCustomerId: session.customerId }, { where: { id: req.user.id } });
    }

    res.json({ success: true, checkoutUrl: session.url, sessionId: session.id, mode, credits });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /portal — Stripe Billing Portal
 */
router.post('/portal', protect, paymentLimiter, async (req, res, next) => {
  try {
    const baseUrl = (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/+$/, '');
    const session = await stripeService.createPortalSession({
      user: req.user,
      returnUrl: `${baseUrl}/billing`,
    });
    res.json({ success: true, url: session.url });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

/* ══════════════════════════════════════════════════════════════════
 * STRIPE WEBHOOK — signature verified + idempotent
 * ══════════════════════════════════════════════════════════════════ */
router.post('/webhook', express.raw({ type: 'application/json' }), stripeWebhook(), async (req, res) => {
  try {
    await handleStripeEvent(req);
  } catch (error) {
    // An async handler that rejects is invisible to Express 4: the request
    // hangs until the provider times out. Worse, committing the ledger on a
    // half-processed event makes Stripe's retry hit the idempotency guard, so
    // the order would stay unpaid forever. 500 + no ledger write = retry wins.
    logger.error(
      `Stripe webhook ${req.webhookEvent?.type || 'unknown'} (${req.webhookEvent?.id || '-'}) failed: ${error.message}`,
    );
    return res.status(500).json({ received: false, error: 'Webhook processing failed' });
  }

  await markWebhookProcessed(req);
  res.json({ received: true, eventId: req.webhookEvent?.id });
});

async function handleStripeEvent(req) {
  const event = req.webhookEvent;

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      const metadata = session.metadata || {};
      if (session.mode === 'payment' && metadata.credits) {
        await Payment.create({
          user_id: metadata.userId ? parseInt(metadata.userId, 10) : null,
          stripePaymentIntentId: session.payment_intent,
          amount: (session.amount_total || 0) / 100,
          currency: session.currency || 'usd',
          status: 'succeeded',
          provider: 'stripe',
          paymentMethod: 'card',
          providerResponse: { checkoutSessionId: session.id, planId: metadata.planId },
        });
      }
      break;
    }
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object;
      const meta = sub.metadata || {};
      const uId = meta.userId || sub.metadata?.userId;
      const dbSub = uId
        ? await Subscription.findOne({ where: { stripeSubscriptionId: sub.id } })
        : null;
      const payload = {
        status: sub.status,
        cancelAtPeriodEnd: sub.cancel_at_period_end || false,
        currentPeriodStart: sub.current_period_start ? new Date(sub.current_period_start * 1000) : null,
        currentPeriodEnd: sub.current_period_end ? new Date(sub.current_period_end * 1000) : null,
        priceId: sub.items?.data?.[0]?.price?.id || null,
      };
      if (dbSub) {
        await dbSub.update(payload);
      } else if (uId) {
        await Subscription.findOrCreate({
          where: { stripeSubscriptionId: sub.id },
          defaults: {
            user_id: parseInt(uId, 10),
            planName: sub.items?.data?.[0]?.price?.nickname || 'Pro',
            plan_id: null,
            stripeSubscriptionId: sub.id,
            stripeCustomerId: sub.customer,
            priceId: sub.items?.data?.[0]?.price?.id || null,
            status: sub.status,
            cancelAtPeriodEnd: sub.cancel_at_period_end || false,
            currentPeriodStart: sub.current_period_start ? new Date(sub.current_period_start * 1000) : null,
            currentPeriodEnd: sub.current_period_end ? new Date(sub.current_period_end * 1000) : null,
          },
        });
      }
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object;
      await Subscription.update(
        { status: 'canceled' },
        { where: { stripeSubscriptionId: sub.id } }
      );
      break;
    }
    case 'payment_intent.succeeded': {
      const pi = event.data.object;
      await Payment.update({ status: 'succeeded' }, { where: { stripePaymentIntentId: pi.id } });
      const payment = await Payment.findOne({ where: { stripePaymentIntentId: pi.id } });
      if (payment?.order_id) {
        // Deliberately un-caught: the paid flip must either commit or the whole
        // event must be retried. Swallowing it left the money captured and the
        // order permanently unpaid.
        await Order.update(
          { isPaid: true, paidAt: new Date(), status: 'processing' },
          { where: { id: payment.order_id } },
        );
      }
      break;
    }
    case 'payment_intent.payment_failed': {
      const pi = event.data.object;
      await Payment.update(
        { status: 'failed', errorMessage: pi.last_payment_error?.message || 'Payment failed' },
        { where: { stripePaymentIntentId: pi.id } }
      );
      break;
    }
    default:
      break;
  }
}

/* ══════════════════════════════════════════════════════════════════
 * INVOICE
 * ══════════════════════════════════════════════════════════════════ */
router.get('/invoice/:orderId', protect, async (req, res, next) => {
  try {
    const order = await Order.findByPk(req.params.orderId);
    if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
    if (req.user.role !== 'admin' && order.user_id !== req.user.id) {
      return res.status(403).json({ success: false, error: 'Not authorized to view this invoice' });
    }
    const html = generateInvoiceHTML(order.toJSON());
    res.setHeader('Content-Type', 'text/html');
    res.send(html);
  } catch (error) {
    next(error);
  }
});

export default router;
