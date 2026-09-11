/**
 * Dynamic Payment Gateway Resolver
 * ---------------------------------
 * Resolves gateway credentials at request-time from the runtime SystemConfig
 * (DB-backed, Redis-cached) with process.env as a startup fallback. This is
 * the "dynamic environment injection" layer for the payment routes.
 */
import Stripe from 'stripe';
import systemConfig from '../systemConfig.service.js';
import { getGatewayConfig } from './config.js';

const UNCONFIGURED_MESSAGE =
  'Payment system unconfigured. Please insert your keys in the Admin Settings panel.';

export { UNCONFIGURED_MESSAGE };

const pick = (secret, placeholder) => (secret && !String(secret).includes(placeholder)) ? secret : '';

/**
 * Builds a live Stripe client from runtime config (DB first, env fallback).
 * Returns null when no usable secret key exists.
 */
export async function getStripeClient() {
  const db = await systemConfig.get('payments.stripe', {});
  const env = getGatewayConfig('stripe');
  const secret = pick(db?.secretKey, 'your_') || pick(env?.secretKey, 'your_');
  if (!secret) return null;
  try {
    return new Stripe(secret);
  } catch {
    return null;
  }
}

export async function getStripePublishableKey() {
  const db = await systemConfig.get('payments.stripe', {});
  const env = getGatewayConfig('stripe');
  return db?.publishableKey || env?.publishableKey || '';
}

export async function getStripeWebhookSecret() {
  const db = await systemConfig.get('payments.stripe', {});
  const env = getGatewayConfig('stripe');
  return db?.webhookSecret || env?.webhookSecret || '';
}

/**
 * Full runtime config for a gateway (DB merged over env).
 */
export async function getGatewayRuntimeConfig(gateway) {
  const env = getGatewayConfig(gateway) || {};

  if (gateway === 'stripe') {
    const db = await systemConfig.get('payments.stripe', {});
    const secretKey = pick(db?.secretKey, 'your_') || pick(env?.secretKey, 'your_');
    const publishableKey = db?.publishableKey || env?.publishableKey || '';
    return {
      enabled: Boolean(secretKey && publishableKey),
      secretKey,
      publishableKey,
      webhookSecret: db?.webhookSecret || env?.webhookSecret || '',
      mode: db?.mode || 'sandbox',
    };
  }

  if (gateway === 'paypal') {
    const db = await systemConfig.get('payments.paypal', {});
    const clientId = pick(db?.clientId, 'your_') || pick(env?.clientId, 'your_');
    const clientSecret = pick(db?.clientSecret, 'your_') || pick(env?.clientSecret, 'your_');
    return {
      enabled: Boolean(clientId && clientSecret),
      clientId,
      clientSecret,
      mode: db?.mode || env?.mode || 'sandbox',
      webhookId: db?.webhookId || env?.webhookId || '',
    };
  }

  return env;
}

/**
 * Simple unified guard signal for routes that cannot operate without a
 * configured gateway. Returns { ok: true } or { ok: false, message }.
 */
export async function gatewayReady(gateway) {
  const runtime = await getGatewayRuntimeConfig(gateway);
  return runtime?.enabled ? { ok: true } : { ok: false, message: UNCONFIGURED_MESSAGE };
}