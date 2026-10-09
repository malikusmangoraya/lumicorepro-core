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
import { stripeWebhook, markWebhookProcessed } from '../middleware/webhookSecurity.js';
import logger from '../utils/logger.js';
import { generateInvoiceHTML } from '../utils/invoiceGenerator.js';
import stripeService from '../services/payment/stripe.service.js';
import paypalService from '../services/payment/paypal.service.js';
import paddleService from '../services/payment/paddle.service.js';
import Plan from '../models/Plan.js';
import User from '../models/User.js';
import Subscription from '../models/Subscription.js';
import { sequelize } from '../config/database.js';
import {
  getEnabledGateways,
  getGatewayConfig,
  isGatewayEnabled,
} from '../services/payment/config.js';
import {
  gatewayReady,
  getStripeClient,
  getStripePublishableKey,
  getGatewayRuntimeConfig,
  UNCONFIGURED_MESSAGE,
} from '../services/payment/dynamic.js';
import systemConfig from '../services/systemConfig.service.js';

const router = express.Router();

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
      supportedCurrencies: [
        'USD',
        'EUR',
        'GBP',
        'PKR',
        'INR',
        'AED',
        'SAR',
        'BRL',
        'MXN',
        'CAD',
        'AUD',
        'JPY',
      ],
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
      targetAmount = parseFloat(order.totalPrice);
      orderCurrency = (order.currency || orderCurrency).toUpperCase();
    }

    if (!targetAmount || targetAmount <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
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
      const { ok } = await gatewayReady('stripe');
      if (!ok) {
        return res.status(200).json({
          success: false,
          code: 'PAYMENT_UNCONFIGURED',
          error: UNCONFIGURED_MESSAGE,
        });
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
      currency,
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

    const payment = await Payment.findOne({ where: { stripePaymentIntentId: paymentIntentId } });
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

    const result = await sequelize.transaction(async (t) => {
      const paymentUpdates = { status: 'succeeded', stripeChargeId: cardDetails?.charge || null };
      if (cardDetails) paymentUpdates.cardDetails = cardDetails;
      await payment.update(paymentUpdates, { transaction: t });

      let order = null;
      const targetOrderId = orderId || (payment && payment.order_id);

      if (targetOrderId) {
        order = await Order.findByPk(targetOrderId, { transaction: t });
        if (order) {
          await order.update(
            {
              isPaid: true,
              paidAt: new Date(),
              status: 'processing',
              paymentResult: {
                id: paymentIntentId,
                status: 'succeeded',
                updateTime: new Date().toISOString(),
                emailAddress: req.user.email,
              },
            },
            { transaction: t }
          );

          await Notification.create(
            {
              recipient: order.user_id == null ? req.user.id : order.user_id,
              type: 'payment',
              title: 'Payment Successful',
              message: `Payment of $${parseFloat(order.totalPrice).toFixed(2)} for order #${order.orderNumber} received.`,
              link: '/templates/ecommerce/OrdersHistory',
              metadata: {},
            },
            { transaction: t }
          );
        }
      }

      return { payment, order };
    });

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

    if (orderId) {
      order = await Order.findByPk(orderId);
      if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
      targetAmount = parseFloat(order.totalPrice);
    }

    if (!targetAmount || targetAmount <= 0) {
      return res.status(400).json({ success: false, error: 'Valid amount is required' });
    }

    const paypalOrder = await paypalService.createOrder({
      amount: targetAmount,
      currency,
      orderId: order?.id,
      description: description || `Order ${order?.orderNumber || 'N/A'}`,
    });

    // Record pending payment
    const payment = await Payment.create({
      user_id: req.user.id,
      order_id: order?.id || null,
      stripePaymentIntentId: paypalOrder.id,
      amount: targetAmount,
      currency,
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

    const captureResult = await paypalService.captureOrder({ orderId: paypalOrderId });

    // Find the pending payment and update in transaction
    const payment = await Payment.findOne({
      where: { stripePaymentIntentId: paypalOrderId, provider: 'paypal' },
    });

    if (!payment) {
      return res.status(404).json({ success: false, error: 'PayPal payment not found' });
    }

    const result = await sequelize.transaction(async (t) => {
      await payment.update(
        {
          status: captureResult.success ? 'succeeded' : 'failed',
          stripeChargeId: captureResult.captureId || null,
          providerResponse: {
            paypalOrderId,
            captureId: captureResult.captureId,
            status: captureResult.status,
          },
        },
        { transaction: t }
      );

      let order = null;
      const targetOrderId = orderId || payment.order_id;

      if (targetOrderId && captureResult.success) {
        order = await Order.findByPk(targetOrderId, { transaction: t });
        if (order) {
          await order.update(
            {
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
            },
            { transaction: t }
          );

          await Notification.create(
            {
              recipient: order.user_id == null ? req.user.id : order.user_id,
              type: 'payment',
              title: 'PayPal Payment Successful',
              message: `PayPal payment of $${parseFloat(order.totalPrice).toFixed(2)} for order #${order.orderNumber} received.`,
              link: '/templates/ecommerce/OrdersHistory',
              metadata: {},
            },
            { transaction: t }
          );
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
    next(error);
  }
});

/**
 * POST /paypal/webhook — PayPal webhook handler
 */
router.post(
  '/paypal/webhook',
  express.raw({ type: 'application/json' }),
  async (req, res, next) => {
    try {
      const event = JSON.parse(req.body.toString());
      await paypalService.handleWebhook(event);
      res.json({ received: true });
    } catch (error) {
      logger.error(`PayPal webhook error: ${error.message}`);
      res.status(400).json({ success: false, error: 'Webhook processing failed' });
    }
  }
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

router.post(
  '/paddle/webhook',
  express.raw({ type: 'application/json' }),
  async (req, res, next) => {
    try {
      const rawBody = req.body.toString();
      const signature = req.headers['paddle-signature'] || '';
      if (!paddleService.verifyWebhook(rawBody, signature)) {
        return res.status(401).json({ success: false, error: 'Invalid Paddle signature' });
      }

      const event = JSON.parse(rawBody);
      const eventType = event?.event_type || '';

      if (eventType.includes('transaction') && eventType.includes('completed')) {
        const data = event.data || {};
        const txnId = data.id || data.transaction_id;
        const customOrderId = data?.custom_data?.orderId || data?.metadata?.orderId;
        if (txnId) {
          const payment =
            (await Payment.findOne({ where: { gatewayPaymentId: txnId } })) ||
            (customOrderId
              ? await Payment.findOne({ where: { order_id: customOrderId, provider: 'paddle' } })
              : null);
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
  }
);

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

    const refundAmount = amount || parseFloat(payment.amount);

    // Gateway-specific refund
    const stripeClient = await stripe();
    if (payment.provider === 'paypal' && payment.stripePaymentIntentId) {
      await paypalService.refund({
        paymentId: payment.stripePaymentIntentId,
        amount: refundAmount,
      });
    } else if (payment.provider === 'paddle' && payment.gatewayPaymentId) {
      await paddleService.refund({
        transactionId: payment.gatewayPaymentId,
        amount: refundAmount,
        reason,
      });
    } else if (
      stripeClient &&
      payment.stripePaymentIntentId &&
      !payment.stripePaymentIntentId.startsWith('pi_mock')
    ) {
      await stripeClient.refunds.create({
        payment_intent: payment.stripePaymentIntentId,
        amount: Math.round(refundAmount * 100),
      });
    }

    const newStatus = refundAmount >= parseFloat(payment.amount) ? 'refunded' : 'succeeded';
    await payment.update({
      status: newStatus,
      refundAmount: parseFloat(payment.refundAmount || 0) + refundAmount,
      refundReason: reason || 'Customer requested refund',
    });

    if (payment.order_id) {
      const order = await Order.findByPk(payment.order_id);
      if (order) await order.update({ status: 'refunded' });
    }

    logger.info(
      `Refund processed: $${refundAmount} for payment ${paymentId} (${payment.provider})`
    );

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
    const { planId, orderId, successUrl, cancelUrl, agentApiKey } = req.body;

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
      if (agentApiKey && typeof agentApiKey === 'string' && agentApiKey.trim()) {
        metadata.agentApiKey = agentApiKey.trim();
      }
    } else if (orderId) {
      const order = await Order.findByPk(orderId);
      if (!order) return res.status(404).json({ success: false, error: 'Order not found' });
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
router.post(
  '/webhook',
  express.raw({ type: 'application/json' }),
  stripeWebhook(),
  async (req, res) => {
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
          if (metadata.agentApiKey) {
            try {
              const aiUrl = (process.env.AI_AGENT_URL || 'http://localhost:8000').replace(
                /\/+$/,
                ''
              );
              await fetch(`${aiUrl}/api/accounts/credits/topup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'x-api-key': metadata.agentApiKey },
                body: JSON.stringify({
                  amount: parseFloat(metadata.credits),
                  reason: 'stripe_purchase',
                }),
              }).catch(() => {});
            } catch {
              /* non-fatal */
            }
          }
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
          currentPeriodStart: sub.current_period_start
            ? new Date(sub.current_period_start * 1000)
            : null,
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
              currentPeriodStart: sub.current_period_start
                ? new Date(sub.current_period_start * 1000)
                : null,
              currentPeriodEnd: sub.current_period_end
                ? new Date(sub.current_period_end * 1000)
                : null,
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
        try {
          const payment = await Payment.findOne({ where: { stripePaymentIntentId: pi.id } });
          if (payment?.order_id) {
            await Order.update(
              { isPaid: true, paidAt: new Date(), status: 'processing' },
              { where: { id: payment.order_id } }
            );
          }
        } catch (orderErr) {
          logger.warn(`Webhook order update skipped: ${orderErr.message}`);
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

    await markWebhookProcessed(req);
    res.json({ received: true, eventId: req.webhookEvent?.id });
  }
);

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
