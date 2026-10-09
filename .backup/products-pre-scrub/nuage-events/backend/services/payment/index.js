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

import { getGatewayConfig, getEnabledGateways, isGatewayEnabled } from './config.js';

import Payment from '../../models/Payment.js';
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
};

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
  return getGatewayList().filter((g) => g.enabled || g.id === 'stripe');
};

/**
 * Create payment through specific gateway
 */
const createPayment = async (gateway, data) => {
  const svc = gateways[gateway];
  if (!svc) {
    throw new Error(`Unknown payment gateway: ${gateway}`);
  }
  logger.info(`Creating ${gateway} payment for amount ${data.amount}`);
  return svc.createPayment({ ...data });
};

/**
 * Confirm/capture payment through specific gateway
 */
const confirmPayment = async (gateway, data) => {
  const svc = gateways[gateway];
  if (!svc) {
    throw new Error(`Unknown payment gateway: ${gateway}`);
  }
  return svc.confirmPayment?.(data) || svc.captureOrder?.(data);
};

/**
 * Refund through specific gateway
 */
const refundPayment = async (gateway, data) => {
  const svc = gateways[gateway];
  if (!svc) {
    throw new Error(`Unknown payment gateway: ${gateway}`);
  }
  return svc.refund(data);
};

/**
 * Handle webhook from specific gateway
 */
const handleWebhook = async (gateway, event) => {
  const svc = gateways[gateway];
  if (!svc) {
    throw new Error(`Unknown payment gateway: ${gateway}`);
  }
  return svc.handleWebhook(event);
};

export {
  gateways,
  getGatewayList,
  getEnabledGatewaysList,
  createPayment,
  confirmPayment,
  refundPayment,
  handleWebhook,
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
  getGatewayConfig,
  getEnabledGateways,
  isGatewayEnabled,
};
