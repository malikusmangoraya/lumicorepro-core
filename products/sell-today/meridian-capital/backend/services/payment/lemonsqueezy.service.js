/**
 * Lemon Squeezy — Merchant of Record payments
 * -------------------------------------------
 * Lemon Squeezy is the merchant of record: sales tax, VAT, invoicing, payouts and
 * license delivery happen on their side. This module covers what runs in this
 * app:
 *
 *   1. credential resolution — Admin Settings first, .env as the fallback
 *   2. hosted checkout — API checkout when a key is present, the store overlay
 *      link otherwise (no key required)
 *   3. webhook signature verification — HMAC-SHA256 over the raw payload
 *   4. mapping confirmed events onto the local payment records
 *
 * Credentials (backend/.env, or Admin Settings -> Payments):
 *   LEMONSQUEEZY_API_KEY          optional; enables server-side checkout
 *   LEMONSQUEEZY_STORE_ID         Settings -> Stores
 *   LEMONSQUEEZY_STORE_URL        overlay base, e.g. https://acme.my.lemonsqueezy.com
 *   LEMONSQUEEZY_WEBHOOK_SECRET   Settings -> Webhooks (signing secret)
 *   LEMONSQUEEZY_VARIANT_ID       default plan / variant
 *   LEMONSQUEEZY_VARIANT_PRO      per-plan override, e.g. LEMONSQUEEZY_VARIANT_PRO
 */
import crypto from 'crypto';

import systemConfig from '../systemConfig.service.js';
import { getGatewayConfig } from './config.js';
import { UNCONFIGURED_MESSAGE } from './dynamic.js';
import Payment from '../../models/Payment.js';
import Order from '../../models/Order.js';
import logger from '../../utils/logger.js';

const API_BASE = 'https://api.lemonsqueezy.com/v1';

/**
 * Values still carrying the shipped template wording are treated as "not set",
 * so an unedited .env.example never looks like a working configuration.
 */
const clean = (value) => {
  const v = String(value ?? '').trim();
  return v && !v.toLowerCase().includes('your_') ? v : '';
};

/** Runtime credentials — Admin Settings (DB) win, process.env is the fallback. */
export async function getRuntimeConfig() {
  const env = getGatewayConfig('lemonsqueezy') || {};
  let db;
  try {
    db = (await systemConfig.get('payments.lemonsqueezy', {})) || {};
  } catch {
    db = {};
  }

  const apiKey = clean(db.apiKey) || clean(env.apiKey);
  const storeId = clean(db.storeId) || clean(env.storeId);
  const storeUrl = (clean(db.storeUrl) || clean(env.storeUrl)).replace(/\/+$/, '');
  const webhookSecret = clean(db.webhookSecret) || clean(env.webhookSecret);
  const variantId = clean(db.variantId) || clean(env.variantId);

  return {
    apiKey,
    storeId,
    storeUrl,
    webhookSecret,
    variantId,
    configured: Boolean(storeId || storeUrl || apiKey),
    checkoutMode: apiKey && storeId ? 'api' : storeUrl ? 'overlay' : 'unconfigured',
  };
}

/** Variant for a plan: LEMONSQUEEZY_VARIANT_PRO first, then the default variant. */
export function resolveVariantId(config, planName) {
  if (planName) {
    const key = `LEMONSQUEEZY_VARIANT_${String(planName).toUpperCase().replace(/[^A-Z0-9]+/g, '_')}`;
    const override = clean(process.env[key]);
    if (override) return override;
  }
  return config.variantId || '';
}

/** Lemon Squeezy signs the raw payload with HMAC-SHA256 and sends hex in X-Signature. */
export function verifyWebhookSignature(rawBody, signature, secret) {
  if (!secret || !signature) return false;
  const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  const received = Buffer.from(String(signature), 'utf8');
  const expectedBuf = Buffer.from(expected, 'utf8');
  return received.length === expectedBuf.length && crypto.timingSafeEqual(received, expectedBuf);
}

/**
 * Build a hosted checkout URL.
 * Preference: server-created API checkout (records the order) -> store overlay
 * link (works with a store URL alone) -> unconfigured.
 */
export async function createCheckout({
  planName,
  variantId,
  amount,
  currency = 'USD',
  userId,
  orderId,
  email,
  customData = {},
  redirectUrl,
} = {}) {
  const config = await getRuntimeConfig();
  const variant = String(variantId || resolveVariantId(config, planName)).trim();

  const custom = {
    ...customData,
    plan: planName || customData.plan || 'standard',
    ...(userId ? { userId: String(userId) } : {}),
    ...(orderId ? { orderId: String(orderId) } : {}),
    ...(amount ? { amount: String(amount) } : {}),
    ...(currency ? { currency: String(currency).toUpperCase() } : {}),
  };

  if (config.apiKey && config.storeId && variant) {
    try {
      const response = await fetch(`${API_BASE}/checkouts`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${config.apiKey}`,
          Accept: 'application/vnd.api+json',
          'Content-Type': 'application/vnd.api+json',
        },
        body: JSON.stringify({
          data: {
            type: 'checkouts',
            attributes: {
              checkout_options: { embed: 'overlay', theme: 'dark' },
              checkout_data: {
                ...(email ? { email } : {}),
                custom,
              },
              ...(redirectUrl ? { redirect_url: redirectUrl } : {}),
            },
            relationships: {
              store: { data: { type: 'stores', id: String(config.storeId) } },
              variant: { data: { type: 'variants', id: String(variant) } },
            },
          },
        }),
      });

      if (response.ok) {
        const body = await response.json().catch(() => null);
        const url = body?.data?.attributes?.url;
        if (url) return { url, mode: 'api', variant, configured: true };
      } else {
        const detail = await response.text().catch(() => '');
        logger.warn(`Lemon Squeezy checkout API ${response.status}: ${detail.slice(0, 200)}`);
      }
    } catch (error) {
      logger.warn(`Lemon Squeezy checkout API unreachable: ${error.message}`);
    }
  }

  if (config.storeUrl && variant) {
    return {
      url: `${config.storeUrl}/buy/variant:${variant}`,
      mode: 'overlay',
      variant,
      configured: true,
    };
  }

  return {
    url: '',
    mode: 'unconfigured',
    variant,
    configured: false,
    message: UNCONFIGURED_MESSAGE,
  };
}

/** Refund a Lemon Squeezy order (Settings -> Orders -> Refund, or this endpoint). */
export async function refund({ orderId, amount, reason } = {}) {
  const config = await getRuntimeConfig();
  if (!config.apiKey) throw new Error(UNCONFIGURED_MESSAGE);
  if (!orderId) throw new Error('A Lemon Squeezy order id is required to issue a refund');

  const response = await fetch(`${API_BASE}/refunds`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      Accept: 'application/vnd.api+json',
      'Content-Type': 'application/vnd.api+json',
    },
    body: JSON.stringify({
      data: {
        type: 'refunds',
        attributes: {
          ...(amount ? { amount } : {}),
          reason: reason || 'Requested by customer',
        },
        relationships: {
          order: { data: { type: 'orders', id: String(orderId) } },
        },
      },
    }),
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(`Lemon Squeezy refund failed (${response.status})`);
  }
  return body?.data || null;
}

/**
 * Apply one verified event to the local records.
 *
 * Every step is best-effort: the durable copy of the event lives in the
 * webhook_events ledger, and a rejected row must never turn into a delivery
 * Lemon Squeezy retries forever.
 */
export async function applyEvent(eventName, event) {
  const data = event?.data || {};
  const attrs = data.attributes || {};
  const custom = attrs.checkout_data?.custom || attrs.custom_data || event?.meta?.custom_data || {};
  const gatewayId = data.id ? String(data.id) : null;
  const localOrderId = Number.parseInt(custom.orderId, 10);
  const userId = Number.parseInt(custom.userId, 10);
  const actions = [];

  if (eventName === 'order_created') {
    // Lemon Squeezy reports totals in the currency's smallest unit.
    const amount = (Number(attrs.total ?? attrs.total_usd ?? 0) || 0) / 100;
    let order = null;
    if (Number.isFinite(localOrderId)) {
      order = await Order.findByPk(localOrderId).catch(() => null);
    }

    try {
      const pendingWhere = { provider: 'lemonsqueezy', status: 'pending' };
      if (order) pendingWhere.order_id = order.id;
      else if (Number.isFinite(userId)) pendingWhere.user_id = userId;

      const pending = order || Number.isFinite(userId)
        ? await Payment.findOne({ where: pendingWhere })
        : null;

      if (pending) {
        await pending.update({
          status: 'succeeded',
          gatewayPaymentId: gatewayId,
          amount,
          currency: String(attrs.currency || 'usd').toLowerCase(),
        });
        actions.push('payment_confirmed');
      } else {
        await Payment.create({
          user_id: Number.isFinite(userId) ? userId : null,
          order_id: order ? order.id : null,
          gatewayPaymentId: gatewayId,
          amount,
          currency: String(attrs.currency || 'usd').toLowerCase(),
          status: 'succeeded',
          provider: 'lemonsqueezy',
          paymentMethod: 'card',
          providerResponse: { orderId: gatewayId, email: attrs.user_email || null },
        });
        actions.push('payment_recorded');
      }
    } catch (error) {
      logger.warn(`Lemon Squeezy payment row skipped: ${error.message}`);
    }

    if (order) {
      await order.update({ isPaid: true, paidAt: new Date(), status: 'processing' }).catch(() => {});
      actions.push('order_marked_paid');
    }
    return actions;
  }

  if (eventName === 'order_refunded') {
    const [, affected] = await Payment.update(
      { status: 'refunded' },
      { where: { gatewayPaymentId: gatewayId } }
    ).catch(() => [0, 0]);
    actions.push(`refunds_recorded:${affected || 0}`);
    return actions;
  }

  if (eventName.startsWith('subscription_')) {
    logger.info(`Lemon Squeezy subscription event ${eventName} (${gatewayId || 'n/a'})`);
    actions.push('subscription_tracked');
    return actions;
  }

  if (eventName === 'license_key_created' || eventName === 'license_key_updated') {
    logger.info(
      `Lemon Squeezy license event ${eventName}${attrs.license_key ? ` (${attrs.license_key})` : ''}`
    );
    actions.push('license_recorded');
    return actions;
  }

  actions.push('recorded');
  return actions;
}

const lemonsqueezyService = {
  name: 'Lemon Squeezy',
  description: 'Merchant of Record checkout — global tax, invoicing and payouts handled',
  region: 'Global',
  supportedCurrencies: ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'PKR'],
  icon: 'lemonsqueezy',
  enabled: Boolean(getGatewayConfig('lemonsqueezy')?.enabled),
  createPayment: createCheckout,
  confirmPayment: async ({ checkoutUrl } = {}) => ({ checkoutUrl, status: 'hosted' }),
  refund,
  handleWebhook: applyEvent,
  getRuntimeConfig,
  verifyWebhookSignature,
  createCheckout,
  resolveVariantId,
  applyEvent,
};

export default lemonsqueezyService;
export { UNCONFIGURED_MESSAGE };
