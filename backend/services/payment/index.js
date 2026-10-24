/**
 * Payment Service Manager
 * Centralized gateway management - create, confirm, refund for any gateway
 */

import stripeService from './stripe.service.js';
import paypalService from './paypal.service.js';
import razorpayService from './razorpay.service.js';
import squareService from './square.service.js';
import bkashService from './bkash.service.js';
import mercadopagoService from './mercadopago.service.js';
import flutterwaveService from './flutterwave.service.js';
import paytmService from './paytm.service.js';
import mollieService from './mollie.service.js';
import liqpayService from './liqpay.service.js';
import paddleService from './paddle.service.js';

import {
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled,
} from './config.js';

import logger from '../../utils/logger.js';

const gateways = {
  stripe: stripeService,
  paypal: paypalService,
  razorpay: razorpayService,
  square: squareService,
  bkash: bkashService,
  mercadopago: mercadopagoService,
  flutterwave: flutterwaveService,
  paytm: paytmService,
  mollie: mollieService,
  liqpay: liqpayService,
  paddle: paddleService,
};

/**
 * Provider entry points differ per gateway. Duplicating that knowledge in a
 * route (or duck-typing a method chain) is how gateways silently go unwired:
 * an omitted name used to throw a raw TypeError, and a wrong one would call a
 * logging-only handler. Each map is the single source of truth.
 */
const CREATE_METHOD = {
  stripe: 'createPayment',
  paypal: 'createOrder',
  razorpay: 'createOrder',
  square: 'createPayment',
  bkash: 'createPayment',
  mercadopago: 'createPreference',
  flutterwave: 'initializeTransaction',
  paytm: 'initiateTransaction',
  mollie: 'createPayment',
  liqpay: 'createPaymentForm',
  paddle: 'createCheckout',
};

const CONFIRM_METHOD = {
  stripe: 'confirmPayment',
  paypal: 'captureOrder',
  bkash: 'executePayment',
};

/**
 * Webhook adapters. `ctx` carries what the provider signed:
 *   ctx.rawBody, ctx.signature, ctx.verifHash, ctx.headers,
 *   ctx.notificationUrl, ctx.params
 * Gateways whose handler verifies the signature itself MUST receive ctx —
 * calling them without it correctly yields `{ valid: false }`.
 */
const WEBHOOK_ADAPTER = {
  stripe: (svc, event) => svc.handleWebhook(event),
  paypal: (svc, event) => svc.handleWebhook(event),
  mollie: (svc, event) => svc.handleWebhook(event),
  bkash: (svc, event) => svc.handleWebhook(event),
  paddle: (svc, event) => svc.handleWebhook(event),
  razorpay: (svc, event, ctx) => svc.handleWebhook(event, ctx.signature, ctx.rawBody),
  square: (svc, event, ctx) =>
    svc.handleWebhook(event, {
      signature: ctx.signature,
      rawBody: ctx.rawBody,
      notificationUrl: ctx.notificationUrl,
    }),
  flutterwave: (svc, event, ctx) => svc.handleWebhook(event, ctx.verifHash || ctx.signature || ''),
  mercadopago: (svc, event, ctx) => svc.handleWebhook(event, ctx.headers || {}),
  liqpay: (svc, event) => svc.handleCallback(event),
  paytm: (svc, event, ctx) => svc.handleCallback(ctx.params || event),
};

/**
 * Gateways that authenticate the event inside their handler. A retry from the
 * durable ledger has no live signature header, so these can never be replayed
 * safely — callers must not treat a missing ctx as success.
 */
const VERIFIES_IN_HANDLER = new Set(['razorpay', 'square', 'flutterwave', 'mercadopago', 'liqpay', 'paytm']);

/**
 * Get gateway info list
 */
const getGatewayList = () => {
  return Object.entries(gateways).map(([key, svc]) => ({
    id: key,
    name: svc.name,
    description: svc.description,
    enabled: svc.enabled,
    region: svc.region,
    supportedCurrencies: svc.supportedCurrencies,
    icon: svc.icon,
  }));
};

/**
 * Get list of enabled gateways for client-side rendering
 */
const getEnabledGatewaysList = () => {
  return getGatewayList().filter(g => g.enabled || g.id === 'stripe');
};

const resolve = gateway => {
  const svc = gateways[gateway];
  if (!svc) {
    throw new Error(`Unknown payment gateway: ${gateway}`);
  }
  return svc;
};

/**
 * Create payment through specific gateway
 */
const createPayment = async (gateway, data) => {
  const svc = resolve(gateway);
  const method = CREATE_METHOD[gateway];
  if (!method || typeof svc[method] !== 'function') {
    throw new Error(`Gateway ${gateway} does not support payment creation`);
  }
  logger.info(`Creating ${gateway} payment for amount ${data.amount}`);
  return svc[method]({ ...data });
};

/**
 * Confirm/capture payment through specific gateway
 */
const confirmPayment = async (gateway, data) => {
  const svc = resolve(gateway);
  const method = CONFIRM_METHOD[gateway];
  if (!method || typeof svc[method] !== 'function') {
    throw new Error(`Gateway ${gateway} does not support payment confirmation`);
  }
  return svc[method]({ ...data });
};

/**
 * Refund through specific gateway
 */
const refundPayment = async (gateway, data) => {
  const svc = resolve(gateway);
  if (typeof svc.refund !== 'function') {
    throw new Error(`Gateway ${gateway} does not support refunds`);
  }
  return svc.refund(data);
};

/**
 * Handle webhook from specific gateway.
 * @returns {Promise<object>} the provider handler result, normalised with
 *   `verificationRequired` so callers can tell "rejected" from "not verifiable".
 */
const handleWebhook = async (gateway, event, ctx = {}) => {
  const svc = resolve(gateway);
  const adapter = WEBHOOK_ADAPTER[gateway];
  if (!adapter) {
    throw new Error(`Gateway ${gateway} has no webhook handler`);
  }
  const result = await adapter(svc, event || {}, ctx);
  const normalised = typeof result === 'object' && result !== null ? result : { handled: true };
  return { ...normalised, gateway, verificationRequired: VERIFIES_IN_HANDLER.has(gateway) };
};

/**
 * True when a stored event can be replayed without the provider's live
 * signature — the ingress middleware already verified it before the ledger write.
 */
const isReplayable = gateway => !VERIFIES_IN_HANDLER.has(gateway);

export {
  gateways,
  getGatewayList,
  getEnabledGatewaysList,
  createPayment,
  confirmPayment,
  refundPayment,
  handleWebhook,
  isReplayable,
  CREATE_METHOD,
  CONFIRM_METHOD,
  WEBHOOK_ADAPTER,
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled,
};

export default {
  gateways,
  getGatewayList,
  getEnabledGatewaysList,
  createPayment,
  confirmPayment,
  refundPayment,
  handleWebhook,
  isReplayable,
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled,
};
