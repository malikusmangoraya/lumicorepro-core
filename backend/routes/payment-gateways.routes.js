/**
 * LumicorePro Payment Routes — Secondary Gateways
 * Mollie · Flutterwave · Square · Mercado Pago · LiqPay · Paytm · bKash
 *
 * Mounted alongside routes/payment.routes.js at `/api/payments`. Every route
 * path below is prefixed by the gateway name so it cannot collide with the
 * Stripe / PayPal / Paddle / Razorpay routes.
 *
 * Signature schemes (all verified inside the gateway service, never here):
 *   - Mollie:        unsigned webhook, only `id`; status re-fetched from the API
 *   - Flutterwave:   shared secret in the `verif-hash` header
 *   - Square:        base64 HMAC-SHA256 over `<notification URL><raw body>`
 *   - Mercado Pago:  `x-signature: ts=…,v1=…` HMAC over `id:…;request-id:…;ts:…;`
 *   - LiqPay:        base64(sha1(privateKey + data + privateKey)) over `data`
 *   - Paytm:         CHECKSUMHASH AES/SHA-256 checksum over the callback params
 *   - bKash:         no callback signature — the payment is confirmed with
 *                    bKash's execute endpoint (authoritative, server-to-server)
 */
import express from 'express';
import Order from '../models/Order.js';
import { protect } from '../middleware/auth.js';
import { paymentLimiter } from '../middleware/rateLimit.js';
import logger from '../utils/logger.js';
import { orderOwnershipError } from '../utils/orderOwnership.js';
import mollieService from '../services/payment/mollie.service.js';
import flutterwaveService from '../services/payment/flutterwave.service.js';
import squareService from '../services/payment/square.service.js';
import mercadoPagoService from '../services/payment/mercadopago.service.js';
import liqpayService from '../services/payment/liqpay.service.js';
import paytmService from '../services/payment/paytm.service.js';
import bkashService from '../services/payment/bkash.service.js';

const router = express.Router();

// A POST without a body leaves req.body undefined; every handler below reads
// body fields directly. Route-level raw/urlencoded parsers still overwrite it.
router.use((req, _res, next) => {
  if (!req.body) req.body = {};
  next();
});

const defaultCurrency = () => (process.env.DEFAULT_CURRENCY || 'USD').toUpperCase();
const frontendUrl = () => (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/+$/, '');
const backendUrl = () =>
  (process.env.BACKEND_URL || `http://localhost:${process.env.PORT || 5000}`).replace(/\/+$/, '');

/** Canonical error response used by this router (same shape as payment.routes.js). */
const fail = (res, status, error) => res.status(status).json({ success: false, error });

/**
 * Resolve the amount/currency for a creation request.
 *
 * When `orderId` is present the order is loaded, ownership is enforced and the
 * stored `totalPrice` / `currency` are used — a client-sent amount is ignored
 * so nobody can pay $1 for a $500 order. Without an order the client amount is
 * accepted (matching the existing Stripe/PayPal routes), but it must be valid.
 *
 * @returns {Promise<{order: object|null, amount: number, currency: string,
 *   error?: {status: number, error: string}}>}
 */
async function resolveContext(req) {
  const body = req.body || {};
  let order = null;
  let amount = Number(body.amount);
  let currency = String(body.currency || defaultCurrency()).toUpperCase();

  if (body.orderId) {
    order = await Order.findByPk(body.orderId);
    const ownErr = orderOwnershipError(order, req.user);
    if (ownErr) return { error: ownErr };
    amount = Number.parseFloat(order.totalPrice);
    if (order.currency) currency = String(order.currency).toUpperCase();
  }

  if (!Number.isFinite(amount) || amount <= 0) {
    return { error: { status: 400, error: 'Valid amount is required' } };
  }
  return { order, amount, currency };
}

/** Read a raw JSON webhook body as UTF-8 (fail-closed on pre-parsed bodies). */
const rawBodyOf = (req) =>
  Buffer.isBuffer(req.body) ? req.body.toString('utf8') : typeof req.body === 'string' ? req.body : '';

/** Parse a raw JSON webhook body; returns null when it is not valid JSON. */
function parseRawJson(req) {
  const raw = rawBodyOf(req);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

const orderRef = (order, fallbackPrefix) =>
  order ? String(order.orderNumber || order.id) : `${fallbackPrefix}_${Date.now()}`;

/* ══════════════════════════════════════════════════════════════════
 * MOLLIE — Europe (iDEAL, Bancontact, cards, …)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /mollie/create — Create a Mollie payment and return its checkout URL.
 */
router.post('/mollie/create', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, currency, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const description = req.body.description || `Order ${order?.orderNumber || 'N/A'}`;
    const payment = await mollieService.createPayment({
      amount,
      currency,
      description,
      redirectUrl: req.body.redirectUrl || `${frontendUrl()}/checkout/success`,
      // Server-controlled: a client-supplied webhook URL would silently move
      // payment confirmation away from this backend.
      webhookUrl: `${backendUrl()}/api/payments/mollie/webhook`,
      metadata: { userId: String(req.user.id), orderId: order ? String(order.id) : '' },
    });

    const checkoutUrl = payment?._links?.checkout?.href || payment?.checkout_url || null;
    logger.info(`Mollie payment created: ${payment?.id} for user ${req.user.id}`);

    res.json({
      success: true,
      id: payment?.id || null,
      checkoutUrl,
      mock: payment?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /mollie/webhook — Mollie posts only `{ id }` (form-urlencoded).
 * The service re-fetches the authoritative status from the Mollie API; a
 * posted status would be forgeable and must never be trusted.
 */
router.post('/mollie/webhook', express.urlencoded({ extended: false }), async (req, res, next) => {
  try {
    const result = await mollieService.handleWebhook(req.body || {});
    if (!result?.valid) return fail(res, 401, 'Invalid Mollie webhook');

    logger.info(
      `Mollie webhook accepted: ${req.body?.id} status=${result.payment?.status || 'unknown'}`,
    );
    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * FLUTTERWAVE — Africa (cards, bank transfer, USSD)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /flutterwave/initialize — Initialize a Flutterwave payment link.
 */
router.post('/flutterwave/initialize', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, currency, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const txRef = req.body.txRef || orderRef(order, 'flw');
    const transaction = await flutterwaveService.initializeTransaction({
      amount,
      currency,
      email: req.body.email || req.user.email,
      firstName: req.body.firstName || '',
      lastName: req.body.lastName || '',
      txRef,
      redirectUrl: req.body.redirectUrl || `${frontendUrl()}/checkout/success`,
      meta: { userId: String(req.user.id), orderId: order ? String(order.id) : '' },
    });

    logger.info(`Flutterwave transaction initialized: ${transaction?.id} (${txRef})`);

    res.json({
      success: true,
      id: transaction?.id || null,
      checkoutUrl: transaction?.link || null,
      txRef,
      mock: transaction?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /flutterwave/verify/:transactionId — Server-side transaction verification.
 */
router.get('/flutterwave/verify/:transactionId', protect, paymentLimiter, async (req, res, next) => {
  try {
    const transaction = await flutterwaveService.verifyTransaction({
      transactionId: req.params.transactionId,
    });

    res.json({
      success: true,
      id: transaction?.id || req.params.transactionId,
      status: transaction?.status || 'unknown',
      transaction,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /flutterwave/webhook — Shared secret in the `verif-hash` header.
 */
router.post('/flutterwave/webhook', express.raw({ type: 'application/json' }), async (req, res, next) => {
  try {
    const signature = req.headers['verif-hash'];
    if (!signature) return fail(res, 401, 'Missing Flutterwave signature');

    const event = parseRawJson(req);
    if (!event) return fail(res, 400, 'Invalid JSON body');

    const result = flutterwaveService.handleWebhook(event, signature);
    if (!result?.valid) return fail(res, 401, 'Invalid Flutterwave signature');

    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * SQUARE — US / Japan / Australia (cards, contactless)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /square/create — Create a Square payment.
 */
router.post('/square/create', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, currency, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const payment = await squareService.createPayment({
      amount,
      currency,
      sourceId: req.body.sourceId,
      idempotencyKey: req.body.idempotencyKey || `sq_${order ? order.id : req.user.id}_${Date.now()}`,
    });

    logger.info(`Square payment created: ${payment?.id} for user ${req.user.id}`);

    res.json({
      success: true,
      id: payment?.id || null,
      payment,
      mock: payment?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /square/webhook — HMAC-SHA256 over `<notification URL><raw body>`,
 * sent in `x-square-hmacsha256-signature`. The notification URL must match the
 * one configured in Square exactly, so it comes from the environment.
 */
router.post('/square/webhook', express.raw({ type: 'application/json' }), async (req, res, next) => {
  try {
    const signature = req.headers['x-square-hmacsha256-signature'];
    if (!signature) return fail(res, 401, 'Missing Square signature');

    const event = parseRawJson(req);
    if (!event) return fail(res, 400, 'Invalid JSON body');

    const result = await squareService.handleWebhook(event, {
      signature,
      rawBody: rawBodyOf(req),
      notificationUrl: process.env.SQUARE_WEBHOOK_NOTIFICATION_URL || '',
    });
    if (!result?.valid) return fail(res, 401, 'Invalid Square signature');

    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * MERCADO PAGO — Latin America (checkout preference)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /mercadopago/create-preference — Create a Checkout Pro preference.
 * With an orderId the preference carries one item priced at the stored order
 * total, so the charged amount can never be influenced by the client.
 */
router.post('/mercadopago/create-preference', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, currency, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const description = req.body.description || `Order ${order?.orderNumber || 'N/A'}`;
    let items;
    if (order) {
      items = [
        {
          id: String(order.id),
          title: description,
          quantity: 1,
          unit_price: amount,
          currency_id: currency,
        },
      ];
    } else if (Array.isArray(req.body.items) && req.body.items.length > 0) {
      items = req.body.items;
    } else {
      items = [
        { id: `item_${Date.now()}`, title: description, quantity: 1, unit_price: amount, currency_id: currency },
      ];
    }

    const preference = await mercadoPagoService.createPreference({
      items,
      paymentMethods: req.body.paymentMethods,
      backUrl: req.body.backUrl || `${frontendUrl()}/checkout/success`,
    });

    logger.info(`Mercado Pago preference created: ${preference?.id} for user ${req.user.id}`);

    res.json({
      success: true,
      id: preference?.id || null,
      preferenceId: preference?.id || null,
      checkoutUrl: preference?.init_point || preference?.sandbox_init_point || null,
      mock: preference?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /mercadopago/webhook — `x-signature`/`x-request-id` headers; the
 * manifest is `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`.
 */
router.post('/mercadopago/webhook', express.raw({ type: 'application/json' }), async (req, res, next) => {
  try {
    if (!req.headers['x-signature']) return fail(res, 401, 'Missing Mercado Pago signature');

    let event = parseRawJson(req) || {};
    const dataId = event?.data?.id || event?.id || req.query['data.id'] || req.query.id;
    if (dataId && !event?.data?.id) {
      event = { ...event, data: { ...(event.data || {}), id: String(dataId) } };
    }

    const result = await mercadoPagoService.handleWebhook(event, req.headers);
    if (!result?.valid) return fail(res, 401, 'Invalid Mercado Pago signature');

    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * LIQPAY — Ukraine / CIS (form POST to the LiqPay checkout)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /liqpay/create-form — Build the signed `data`/`sign` checkout form.
 */
router.post('/liqpay/create-form', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, currency, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const description = req.body.description || `Order ${order?.orderNumber || 'N/A'}`;
    const form = await liqpayService.createPaymentForm({
      amount,
      currency,
      orderId: req.body.orderRef || orderRef(order, 'liqpay'),
      description,
      productName: req.body.productName || description,
      // Server-controlled callback: LiqPay signs the payload posted back here.
      serverUrl: `${backendUrl()}/api/payments/liqpay/callback`,
    });

    logger.info(`LiqPay checkout form created for order ${form?.mock ? 'mock' : 'live'}`);

    res.json({
      success: true,
      id: order?.id || null,
      checkoutUrl: form?.action || null,
      action: form?.action || null,
      publicKey: form?.publicKey || null,
      data: form?.data || null,
      sign: form?.sign || null,
      mock: form?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /liqpay/callback — `data` + `sign` form fields; signature is verified
 * over the base64 `data` string exactly as received.
 */
router.post('/liqpay/callback', express.urlencoded({ extended: false }), async (req, res, next) => {
  try {
    const { data, sign } = req.body || {};
    if (!data || !sign) return fail(res, 401, 'Missing LiqPay signature');

    const result = await liqpayService.handleCallback({ data, sign });
    if (result?.error) {
      const status = result.error === 'Invalid signature' ? 401 : 400;
      return fail(res, status, result.error);
    }

    logger.info(`LiqPay callback accepted: order=${result?.order_id} status=${result?.status}`);
    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * PAYTM — India (wallet, UPI, cards)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /paytm/initiate — Obtain a transaction token / payment page URL.
 */
router.post('/paytm/initiate', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const result = await paytmService.initiateTransaction({
      amount,
      orderId: req.body.orderRef || orderRef(order, 'paytm'),
      email: req.body.email || req.user.email,
      phone: req.body.phone || '',
      // Server-controlled callback: the CHECKSUMHASH verification happens here.
      callbackUrl: `${backendUrl()}/api/payments/paytm/callback`,
    });

    logger.info(`Paytm transaction initiated for order ${req.body.orderRef || order?.id || 'guest'}`);

    res.json({
      success: true,
      id: result?.txnId || order?.id || null,
      txnToken: result?.txnToken || null,
      redirectURL: result?.redirectURL || null,
      checkoutUrl: result?.redirectURL || null,
      mock: result?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /paytm/callback — Paytm posts the result back with CHECKSUMHASH.
 */
router.post('/paytm/callback', express.urlencoded({ extended: false }), async (req, res, next) => {
  try {
    const result = paytmService.handleCallback(req.body || {});
    if (!result?.valid) return fail(res, 401, 'Invalid Paytm checksum');

    logger.info(`Paytm callback accepted: order=${result.params?.ORDERID} status=${result.params?.STATUS}`);
    res.json({ received: true });
  } catch (err) {
    next(err);
  }
});

/* ══════════════════════════════════════════════════════════════════
 * BKASH — Bangladesh (tokenized checkout)
 * ══════════════════════════════════════════════════════════════════ */

/**
 * POST /bkash/create — Create a bKash tokenized checkout payment.
 */
router.post('/bkash/create', protect, paymentLimiter, async (req, res, next) => {
  try {
    const { order, amount, error } = await resolveContext(req);
    if (error) return fail(res, error.status, error.error);

    const payment = await bkashService.createPayment({
      amount,
      orderId: order ? String(order.id) : req.body.orderRef || `bkash_${Date.now()}`,
      callbackUrl: req.body.callbackUrl || `${frontendUrl()}/checkout/bkash/callback`,
      notifyUrl: req.body.notifyUrl || `${backendUrl()}/api/payments/bkash/callback`,
    });

    logger.info(`bKash payment created: ${payment?.paymentID} for user ${req.user.id}`);

    res.json({
      success: true,
      id: payment?.paymentID || null,
      paymentID: payment?.paymentID || null,
      checkoutUrl: payment?.checkoutURL || null,
      mock: payment?.mock === true,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * bKash callback handler.
 *
 * bKash has no callback signature. The callback only supplies a paymentID;
 * confirmation is the `executePayment` call, which asks bKash server-to-server
 * (with our credentials) whether the payment succeeded. A forged callback
 * therefore cannot mark an unpaid order as paid.
 *
 * bKash redirects the browser back with GET query params (`paymentID`,
 * `status`); a server-side notify integration posts the same fields.
 */
async function handleBkashCallback(req, res, next) {
  try {
    const source = req.method === 'GET' ? req.query : req.body || {};
    const paymentId = source.paymentID || source.paymentId;
    if (!paymentId) return fail(res, 400, 'paymentID is required');
    if (source.status && source.status !== 'success') {
      return fail(res, 400, 'bKash payment was not completed');
    }

    const result = await bkashService.executePayment({
      paymentId,
      callbackType: source.callbackType || 'payment',
    });
    if (!result?.success) return fail(res, 400, 'bKash payment was not completed');

    logger.info(`bKash callback confirmed: ${paymentId}`);
    res.json({ received: true });
  } catch (err) {
    next(err);
  }
}

router.get('/bkash/callback', handleBkashCallback);
router.post('/bkash/callback', express.urlencoded({ extended: false }), handleBkashCallback);

export default router;
