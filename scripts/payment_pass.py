#!/usr/bin/env python3
"""Payment + international checkout pass for every project in products/.

One pass, applied identically to all products, that:

  1. deletes the dead CommonJS payment stub (backend/routes/paymentRoutes.js)
  2. adds a real Lemon Squeezy service + routes (checkout, config, signed webhook)
  3. registers the gateway in the payment registry (config.js / index.js)
  4. fixes webhook raw-body ordering in server.js (signature verification is
     currently impossible because express.json() parses the body first)
  5. expands the .env templates with the full gateway key matrix
  6. passes payment environment variables through docker-compose
  7. upgrades the frontend Lemon Squeezy helper (env config + backend checkout
     + a visible demo fallback)
  8. registers Lemon Squeezy events in the webhook registry
  9. rewrites the buyer documentation and appends the seller-key guide

The script is idempotent: every edit is skipped when it is already applied.

    python scripts/payment_pass.py            # apply to every product
    python scripts/payment_pass.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"


# --------------------------------------------------------------------------- #
# File helpers
# --------------------------------------------------------------------------- #
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def sub_once(text: str, pattern: str, replacement: str, what: str,
             count: int = 1, flags: int = re.S) -> str:
    """Replace `count` matches or raise — a silent no-op would hide a broken edit."""
    new, n = re.subn(pattern, replacement, text, count=count, flags=flags)
    if n != count:
        raise RuntimeError(f"{what}: expected {count} match(es), found {n}")
    return new


def insert_before(text: str, anchor: str, insertion: str, what: str) -> str:
    """Insert `insertion` in front of the first `anchor` match.

    A function replacement is used so backslashes in the inserted JavaScript
    (regex literals) are never treated as group references.
    """
    pattern = re.compile(anchor, re.S)
    if not pattern.search(text):
        raise RuntimeError(f"{what}: anchor not found")
    return pattern.sub(lambda m: insertion + m.group(0), text, count=1)


# --------------------------------------------------------------------------- #
# New backend sources
# --------------------------------------------------------------------------- #
LS_SERVICE = r'''/**
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
  let db = {};
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
'''

LS_ROUTES = r'''/**
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

  let event = null;
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
'''

FRONTEND_LS = r'''/**
 * Lemon Squeezy storefront helper
 * ------------------------------
 * Resolution order for a checkout:
 *   1. an explicit checkout URL passed by the caller
 *   2. the store overlay link (VITE_LEMONSQUEEZY_STORE_URL + variant id)
 *   3. the backend checkout endpoint (authoritative, records the order)
 *   4. the built-in demo dialog, so the pricing page still works before keys
 *      are inserted
 */
const LEMON_SCRIPT = 'https://assets.lemonsqueezy.com/lemon.js';

const env = (key, fallback = '') =>
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) || fallback;

export const lemonSqueezyConfig = {
  storeId: env('VITE_LEMONSQUEEZY_STORE_ID'),
  storeUrl: env('VITE_LEMONSQUEEZY_STORE_URL').replace(/\/+$/, ''),
  variantId: env('VITE_LEMONSQUEEZY_VARIANT_ID'),
  apiBase: env('VITE_API_URL').replace(/\/+$/, ''),
};

let lemonLoaded = false;

/** Loads the Lemon Squeezy overlay script once per session. */
export function loadLemonSqueezy() {
  if (lemonLoaded || typeof window === 'undefined') return Promise.resolve();

  return new Promise((resolve) => {
    if (document.querySelector('script[src*="lemonsqueezy.com/lemon.js"]')) {
      lemonLoaded = true;
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = LEMON_SCRIPT;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      lemonLoaded = true;
      if (window.createLemonSqueezy) {
        window.createLemonSqueezy();
      }
      resolve();
    };
    script.onerror = () => {
      resolve();
    };
    document.head.appendChild(script);
  });
}

const openUrl = (url) => {
  if (!url || typeof window === 'undefined') return false;
  if (window.LemonSqueezy?.Url?.Open) {
    window.LemonSqueezy.Url.Open(url);
    return true;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
  return true;
};

/** Store configuration served by the API — probed once, never cached on failure. */
export async function getStoreConfig() {
  if (!lemonSqueezyConfig.apiBase) return null;
  try {
    const response = await fetch(`${lemonSqueezyConfig.apiBase}/api/lemonsqueezy/config`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

/** Ask the backend for a hosted checkout URL. */
async function requestCheckout(payload) {
  if (!lemonSqueezyConfig.apiBase) return null;
  try {
    const response = await fetch(`${lemonSqueezyConfig.apiBase}/api/lemonsqueezy/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) return null;
    const body = await response.json();
    return body?.url ? body : null;
  } catch {
    return null;
  }
}

const overlayUrl = (variantId) => {
  if (!lemonSqueezyConfig.storeUrl || !variantId) return '';
  return `${lemonSqueezyConfig.storeUrl}/buy/variant:${variantId}`;
};

/**
 * Demo fallback: a small self-contained dialog. It never charges anyone and it
 * makes the difference between "not configured yet" and a broken page obvious.
 */
function openDemoCheckout({ planName, price, onSuccess }) {
  if (typeof document === 'undefined') return;

  const existing = document.getElementById('lemon-squeezy-demo');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.id = 'lemon-squeezy-demo';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Checkout preview');
  overlay.style.cssText =
    'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,6,23,.82);backdrop-filter:blur(6px);';
  overlay.innerHTML = `
    <div style="max-width:420px;width:100%;border-radius:20px;border:1px solid rgba(148,163,184,.25);background:#0b1220;padding:28px;font-family:inherit;color:#e2e8f0;box-shadow:0 30px 60px rgba(0,0,0,.45)">
      <h3 style="margin:0 0 6px;font-size:18px;font-weight:700;color:#fff">Checkout preview</h3>
      <p style="margin:0 0 16px;font-size:13px;line-height:1.6;color:#94a3b8">
        ${planName ? `<strong style="color:#e2e8f0">${planName}</strong>${price ? ` — $${price}` : ''}.<br/>` : ''}
        This storefront has no Lemon Squeezy keys yet, so no payment is taken. Add the store
        details from <code>frontend/.env</code> to switch this button to real checkout.
      </p>
      <button type="button" id="lemon-squeezy-demo-close"
        style="width:100%;padding:11px 16px;border-radius:12px;border:0;background:linear-gradient(90deg,#22d3ee,#2563eb);color:#fff;font-size:13px;font-weight:700;cursor:pointer">
        Got it
      </button>
    </div>`;

  const close = () => {
    overlay.remove();
    if (typeof onSuccess === 'function') onSuccess({ demo: true });
  };
  overlay.querySelector('#lemon-squeezy-demo-close').addEventListener('click', close);
  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) close();
  });
  document.body.appendChild(overlay);

  // Kept for integrations that listen for the event instead of the dialog.
  window.dispatchEvent(
    new CustomEvent('open-mock-checkout', {
      detail: { customData: { planName, price } },
    })
  );
}

/**
 * Open checkout for a plan.
 * Pass `checkoutUrl` to bypass resolution, `variantId` to pin a variant, or
 * `customData` (the pricing table passes planName/amount/billingCycle).
 */
export async function openLemonSqueezyCheckout({
  checkoutUrl,
  variantId,
  customData = {},
  onSuccess,
  onClose,
} = {}) {
  if (typeof window === 'undefined') return;

  const planName = customData.planName || customData.plan || '';

  if (checkoutUrl && openUrl(checkoutUrl)) return;

  await loadLemonSqueezy();

  const variant = variantId || lemonSqueezyConfig.variantId || '';
  const overlay = overlayUrl(variant);
  if (overlay && openUrl(overlay)) return;

  const remote = await requestCheckout({ ...customData, planName, variantId: variant || undefined });
  if (remote && openUrl(remote.url)) return;

  openDemoCheckout({ planName, price: customData.amount, onSuccess, onClose });
}

export default { loadLemonSqueezy, openLemonSqueezyCheckout, getStoreConfig, lemonSqueezyConfig };
'''

# --------------------------------------------------------------------------- #
# Environment templates
# --------------------------------------------------------------------------- #
SERVER_PAYMENT_ENV = """
# ── Payments ─────────────────────────────────────────────────────────────────
# Every gateway is optional. Without keys the app still boots and the checkout
# endpoints answer with a clear "not configured" message instead of failing.
# Insert only the keys you want to sell with, then list them here:
#   PAYMENT_GATEWAYS_ENABLED=stripe,paypal,lemonsqueezy     (or =all for testing)
PAYMENT_GATEWAYS_ENABLED=stripe,paypal,lemonsqueezy
DEFAULT_CURRENCY=USD
FRONTEND_URL=http://localhost:5173

# Stripe — dashboard.stripe.com/apikeys  (webhook: /api/payment/webhook)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# PayPal — developer.paypal.com/dashboard/applications  (webhook: /api/payment/paypal/webhook)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=

# Lemon Squeezy (merchant of record) — app.lemonsqueezy.com/settings/api
# Overlay checkout only needs the store id; an API key additionally enables
# server-side checkout creation. Webhook: /api/lemonsqueezy/webhook
LEMONSQUEEZY_STORE_ID=
LEMONSQUEEZY_STORE_URL=
LEMONSQUEEZY_API_KEY=
LEMONSQUEEZY_WEBHOOK_SECRET=
LEMONSQUEEZY_VARIANT_ID=
# One variant per pricing tier — LEMONSQUEEZY_VARIANT_STARTER / _PRO / _ENTERPRISE
LEMONSQUEEZY_VARIANT_STARTER=
LEMONSQUEEZY_VARIANT_PRO=
LEMONSQUEEZY_VARIANT_ENTERPRISE=

# Paddle (merchant of record) — webhooks: /api/payment/paddle/webhook
PADDLE_API_KEY=
PADDLE_WEBHOOK_SECRET=
PADDLE_ENV=sandbox

# Additional gateways — enable them with PAYMENT_GATEWAYS_ENABLED=all
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
SQUARE_ACCESS_TOKEN=
SQUARE_LOCATION_ID=
SQUARE_ENVIRONMENT=sandbox
MOLLIE_API_KEY=
MOLLIE_ORGANIZATION_ID=
FLUTTERWAVE_PUBLIC_KEY=
FLUTTERWAVE_SECRET_KEY=
FLUTTERWAVE_ENCRYPTION_KEY=
FLUTTERWAVE_WEBHOOK_SECRET=
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_PUBLIC_KEY=
MERCADOPAGO_WEBHOOK_PASSWORD=
LIQPAY_PUBLIC_KEY=
LIQPAY_PRIVATE_KEY=
PAYTM_MERCHANT_ID=
PAYTM_MERCHANT_KEY=
PAYTM_WEBSITE=WEBSTAGING
PAYTM_INDUSTRY_TYPE=Retail
PAYTM_CHANNEL_ID=WEB
PAYTM_MODE=sandbox
BKASH_APP_KEY=
BKASH_APP_SECRET=
BKASH_USERNAME=
BKASH_PASSWORD=
BKASH_MERCHANT_ID=
"""

FRONTEND_PAYMENT_ENV = """
# ── Storefront checkout ──────────────────────────────────────────────────────
# Built at build time by Vite, so restart the dev server after editing.
VITE_LEMONSQUEEZY_STORE_ID=
VITE_LEMONSQUEEZY_STORE_URL=
VITE_LEMONSQUEEZY_VARIANT_ID=
VITE_STRIPE_PUBLISHABLE_KEY=
"""

COMPOSE_PAYMENT_ENV = """      # Payment gateways — values are read from the host .env; blank disables one.
      PAYMENT_GATEWAYS_ENABLED: ${PAYMENT_GATEWAYS_ENABLED:-}
      DEFAULT_CURRENCY: ${DEFAULT_CURRENCY:-USD}
      FRONTEND_URL: ${FRONTEND_URL:-http://localhost}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY:-}
      STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY:-}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET:-}
      PAYPAL_CLIENT_ID: ${PAYPAL_CLIENT_ID:-}
      PAYPAL_CLIENT_SECRET: ${PAYPAL_CLIENT_SECRET:-}
      PAYPAL_MODE: ${PAYPAL_MODE:-sandbox}
      PAYPAL_WEBHOOK_ID: ${PAYPAL_WEBHOOK_ID:-}
      LEMONSQUEEZY_STORE_ID: ${LEMONSQUEEZY_STORE_ID:-}
      LEMONSQUEEZY_STORE_URL: ${LEMONSQUEEZY_STORE_URL:-}
      LEMONSQUEEZY_API_KEY: ${LEMONSQUEEZY_API_KEY:-}
      LEMONSQUEEZY_WEBHOOK_SECRET: ${LEMONSQUEEZY_WEBHOOK_SECRET:-}
      LEMONSQUEEZY_VARIANT_ID: ${LEMONSQUEEZY_VARIANT_ID:-}
      PADDLE_API_KEY: ${PADDLE_API_KEY:-}
      PADDLE_WEBHOOK_SECRET: ${PADDLE_WEBHOOK_SECRET:-}
      PADDLE_ENV: ${PADDLE_ENV:-sandbox}
      RAZORPAY_KEY_ID: ${RAZORPAY_KEY_ID:-}
      RAZORPAY_KEY_SECRET: ${RAZORPAY_KEY_SECRET:-}
      SQUARE_ACCESS_TOKEN: ${SQUARE_ACCESS_TOKEN:-}
      MOLLIE_API_KEY: ${MOLLIE_API_KEY:-}
      FLUTTERWAVE_SECRET_KEY: ${FLUTTERWAVE_SECRET_KEY:-}
      MERCADOPAGO_ACCESS_TOKEN: ${MERCADOPAGO_ACCESS_TOKEN:-}
      LIQPAY_PUBLIC_KEY: ${LIQPAY_PUBLIC_KEY:-}
      PAYTM_MERCHANT_ID: ${PAYTM_MERCHANT_ID:-}
      BKASH_APP_KEY: ${BKASH_APP_KEY:-}
"""

RAW_BODY_MIDDLEWARE = r'''// ── Raw body capture for signed payment webhooks ────────────────────────────
// Stripe, PayPal, Paddle and Lemon Squeezy verify an HMAC over the exact bytes
// they sent. The JSON parser below would replace those bytes with a parsed
// object, so these endpoints are read into a Buffer first and the body parsers
// are then told the body has already been read. Every other route keeps the
// normal JSON path.
const SIGNED_WEBHOOK_PATHS = [
  /\/payment\/webhook$/,
  /\/payment\/paypal\/webhook$/,
  /\/payment\/paddle\/webhook$/,
  /\/webhook\/stripe$/,
  /\/lemonsqueezy\/webhook$/,
];
app.use((req, res, next) => {
  if (req.method !== 'POST' || !SIGNED_WEBHOOK_PATHS.some((pattern) => pattern.test(req.path))) {
    return next();
  }
  const limit = parseInt(process.env.WEBHOOK_BODY_LIMIT, 10) || 1024 * 1024;
  const chunks = [];
  let size = 0;
  let overflow = false;
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size > limit) overflow = true;
    else chunks.push(chunk);
  });
  req.on('end', () => {
    if (overflow) return res.status(413).json({ error: 'Webhook payload too large' });
    req.rawBody = Buffer.concat(chunks);
    req.body = req.rawBody;
    req._body = true; // body-parser: already read, do not parse again
    next();
  });
  req.on('error', next);
});

'''

LS_REGISTRY_EVENTS = [
    ("order.created", "lemonsqueezy", "Order paid — fulfillment unlocks"),
    ("order.refunded", "lemonsqueezy", "Order refunded by the merchant of record"),
    ("subscription.created", "lemonsqueezy", "New subscription (recurring plan)"),
    ("subscription.updated", "lemonsqueezy", "Subscription plan or status changed"),
    ("subscription.cancelled", "lemonsqueezy", "Subscription cancelled"),
    ("license.created", "lemonsqueezy", "License key issued to the buyer"),
]


def buyer_payment_section(brand: str) -> str:
    return f"""## 2. Connecting Lemon Squeezy Payments

Lemon Squeezy is the **merchant of record**, so sales tax, VAT, invoices and payouts are handled for you. Connect it once and both the demo and the live site use it.

### 2.1 Create the product

1. Create an account at [app.lemonsqueezy.com](https://app.lemonsqueezy.com) and activate the store (identity verification).
2. Create one product with a variant per tier (Starter / Pro / Enterprise). Copy each **Variant ID**.
3. Copy the **Store ID** from *Settings → Stores* and, for server-created checkouts, an **API key** from *Settings → API*.

### 2.2 Add the keys

`backend/.env` (the API process):

```bash
LEMONSQUEEZY_STORE_ID=123456
LEMONSQUEEZY_STORE_URL=https://acme.my.lemonsqueezy.com
LEMONSQUEEZY_WEBHOOK_SECRET=            # Settings -> Webhooks -> Signing secret
LEMONSQUEEZY_VARIANT_STARTER=111111     # one variant id per pricing tier
LEMONSQUEEZY_VARIANT_PRO=222222
LEMONSQUEEZY_VARIANT_ENTERPRISE=333333
LEMONSQUEEZY_API_KEY=                   # optional, only for API-created checkouts
```

`frontend/.env` (the storefront — Vite reads this at build time):

```bash
VITE_LEMONSQUEEZY_STORE_ID=123456
VITE_LEMONSQUEEZY_STORE_URL=https://acme.my.lemonsqueezy.com
VITE_LEMONSQUEEZY_VARIANT_ID=111111
```

Set `PAYMENT_GATEWAYS_ENABLED=stripe,paypal,lemonsqueezy` (or `all` while testing every gateway).

### 2.3 Point the pricing table at the variants

Each plan in `frontend/src/components/ecommerce/PricingTable.jsx` may carry a `variantId`; without it the app falls back to `LEMONSQUEEZY_VARIANT_<PLAN>` from the backend, and finally to `VITE_LEMONSQUEEZY_VARIANT_ID`.

### 2.4 Register the webhook

In *Settings → Webhooks* add:

| Field | Value |
| --- | --- |
| URL | `https://your-domain.com/api/lemonsqueezy/webhook` |
| Events | `order_created`, `order_refunded`, `subscription_created`, `subscription_updated`, `subscription_cancelled`, `license_key_created`, `license_key_updated` |
| Signing secret | copy into `LEMONSQUEEZY_WEBHOOK_SECRET` |

Deliveries are verified with HMAC-SHA256 (`X-Signature`), replayed deliveries are ignored through the webhook ledger, and a failed step returns a non-2xx so the sender retries.

### 2.5 What the endpoints do

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/lemonsqueezy/config` | GET | Store id, checkout mode, webhook URL (public) |
| `/api/lemonsqueezy/checkout` | POST | Hosted checkout URL for a plan or an open order |
| `/api/lemonsqueezy/webhook` | POST | Signed purchase, refund and subscription events |

### 2.6 Other gateways in the box

Stripe, PayPal, Paddle, Razorpay, Square, Mollie, Flutterwave, Mercado Pago, LiqPay, Paytm and bKash are already implemented (`backend/services/payment/`). Add their keys to `backend/.env` and list them in `PAYMENT_GATEWAYS_ENABLED`.

Without any keys the pricing buttons open a clearly labelled preview dialog, so the demo on GitHub Pages keeps working before the store is connected.
"""


def seller_key_guide(brand: str) -> str:
    return f"""
---

## 5. What The Buyer Sets Up After Purchase

Hand this list to the customer with the download. It is the complete key-insertion path — no code changes are required.

1. **Store identity** — `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_STORE_URL` (both in `backend/.env`, plus `VITE_LEMONSQUEEZY_STORE_ID` / `VITE_LEMONSQUEEZY_STORE_URL` in `frontend/.env`).
2. **Plans** — one `LEMONSQUEEZY_VARIANT_<PLAN>` per pricing tier, or `variantId` on each plan in `PricingTable.jsx`.
3. **Webhooks** — `LEMONSQUEEZY_WEBHOOK_SECRET` plus an endpoint at `https://their-domain/api/lemonsqueezy/webhook` for `order_created`, `order_refunded`, `subscription_created`, `subscription_updated`, `subscription_cancelled`, `license_key_created`, `license_key_updated`.
4. **Optional** — `LEMONSQUEEZY_API_KEY` to create checkouts server-side instead of using the store overlay link.
5. **Other cards** — `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET`, `PADDLE_API_KEY`, then set `PAYMENT_GATEWAYS_ENABLED` to the list you want live (`all` enables every implemented gateway while testing).
6. **Environment on the host** — with Docker, the same variables are read straight from the host `.env` (see `docker-compose.yml`), so no rebuild is needed.

Smoke test: `GET /api/lemonsqueezy/config` must report `configured: true`, and a paid order must appear as `succeeded` in the payments table.
"""


# --------------------------------------------------------------------------- #
# Per-product work
# --------------------------------------------------------------------------- #
def product_brand(doc_text: str, fallback: str) -> str:
    m = re.search(r"^#\s+\S+\s+—\s+(.+?)\s+—\s+", doc_text, re.M)
    if m:
        return m.group(1)
    m = re.search(r"^#\s+(.+?)\s+—", doc_text, re.M)
    return m.group(1) if m else fallback


def process(product: Path, dry_run: bool) -> dict:
    log: list[str] = []
    slug = product.name
    be = product / "backend"
    fe = product / "frontend"

    def emit(msg: str) -> None:
        log.append(msg)

    # -- 1. dead CommonJS payment stub -------------------------------------
    stub = be / "routes" / "paymentRoutes.js"
    if stub.exists():
        refs = []
        for js in be.rglob("*.js"):
            if js == stub or "node_modules" in js.parts:
                continue
            if "paymentRoutes" in js.read_text(encoding="utf-8", errors="replace"):
                refs.append(str(js.relative_to(product)))
        if refs:
            emit(f"skip dead stub paymentRoutes.js (referenced by {', '.join(refs)})")
        elif not dry_run:
            stub.unlink()
            emit("deleted dead CommonJS stub backend/routes/paymentRoutes.js")
        else:
            emit("would delete backend/routes/paymentRoutes.js")

    # -- 2. Lemon Squeezy service + routes ---------------------------------
    svc = be / "services" / "payment" / "lemonsqueezy.service.js"
    if not svc.exists():
        if not dry_run:
            write(svc, LS_SERVICE)
        emit("added backend/services/payment/lemonsqueezy.service.js")

    routes = be / "routes" / "lemonsqueezy.routes.js"
    if not routes.exists():
        if not dry_run:
            write(routes, LS_ROUTES)
        emit("added backend/routes/lemonsqueezy.routes.js (mounted at /api/lemonsqueezy)")

    # -- 3. gateway registry ------------------------------------------------
    cfg = be / "services" / "payment" / "config.js"
    text = read(cfg)
    if "lemonsqueezy:" not in text:
        block = (
            r"(      environment: process\.env\.PADDLE_ENV \|\| 'sandbox',\r?\n)"
            r"(    \},)"
        )
        addition = (
            r"\1\2\n"
            "    lemonsqueezy: {\n"
            "      enabled: Boolean(\n"
            "        (process.env.LEMONSQUEEZY_API_KEY &&\n"
            "          !process.env.LEMONSQUEEZY_API_KEY.includes('your_')) ||\n"
            "        (process.env.LEMONSQUEEZY_STORE_URL &&\n"
            "          !process.env.LEMONSQUEEZY_STORE_URL.includes('your_'))\n"
            "      ),\n"
            "      apiKey: process.env.LEMONSQUEEZY_API_KEY,\n"
            "      storeId: process.env.LEMONSQUEEZY_STORE_ID,\n"
            "      storeUrl: process.env.LEMONSQUEEZY_STORE_URL,\n"
            "      webhookSecret: process.env.LEMONSQUEEZY_WEBHOOK_SECRET,\n"
            "      variantId: process.env.LEMONSQUEEZY_VARIANT_ID,\n"
            "    },"
        )
        text = sub_once(text, block, addition, "config.js lemonsqueezy entry")
        emit("config.js: lemonsqueezy gateway entry added")
    if "'lemonsqueezy'," not in text:
        text = sub_once(
            text,
            r"(\n(\s+)'paddle',)(\r?\n)(\s*\];)",
            r"\1\2'lemonsqueezy',\3\4",
            "config.js gateway list",
        )
        emit("config.js: lemonsqueezy added to the gateway list")
    old_whitelist = "const launchWhitelist = ['stripe', 'paypal'];"
    if old_whitelist in text:
        n = text.count(old_whitelist)
        text = text.replace(
            old_whitelist, "const launchWhitelist = ['stripe', 'paypal', 'lemonsqueezy'];"
        )
        emit(f"config.js: lemonsqueezy added to the launch whitelist ({n} site(s))")
    if not dry_run and text != read(cfg):
        write(cfg, text)

    idx = be / "services" / "payment" / "index.js"
    text = read(idx)
    if "lemonsqueezy.service.js" not in text:
        text = sub_once(
            text,
            r"(import liqpayService from './liqpay\.service\.js';)",
            r"\1\nimport lemonsqueezyService from './lemonsqueezy.service.js';",
            "index.js import",
        )
        text = sub_once(
            text,
            r"(\n(\s+)liqpay: liqpayService,)",
            r"\1\n\2lemonsqueezy: lemonsqueezyService,",
            "index.js registry",
        )
        emit("index.js: lemonsqueezy service registered")
        if not dry_run:
            write(idx, text)

    # -- 4. webhook raw body ordering --------------------------------------
    server = be / "server.js"
    text = read(server)
    if "SIGNED_WEBHOOK_PATHS" not in text:
        text = insert_before(
            text,
            r"app\.use\(express\.json\(\{ limit:",
            RAW_BODY_MIDDLEWARE,
            "server.js raw body middleware",
        )
        emit("server.js: raw-body capture added before the JSON parser")
        if not dry_run:
            write(server, text)

    # -- 5. environment templates ------------------------------------------
    for rel in (".env.example", "backend/.env.example", "frontend/.env.example"):
        env_file = product / rel
        if not env_file.exists():
            emit(f"skip {rel} (missing)")
            continue
        text = read(env_file)
        # the shipped template keys become part of the grouped matrix below
        text = re.sub(r"(?m)^STRIPE_SECRET_KEY=.*\n", "", text)
        text = re.sub(r"(?m)^VITE_STRIPE_PUBLISHABLE_KEY=.*\n", "", text)
        additions = SERVER_PAYMENT_ENV
        if rel.startswith("frontend"):
            additions = FRONTEND_PAYMENT_ENV + SERVER_PAYMENT_ENV
        if "LEMONSQUEEZY_STORE_ID" not in text:
            text = text.rstrip("\n") + "\n" + additions
            emit(f"{rel}: payment key matrix added")
        else:
            emit(f"{rel}: payment matrix already present")
        if not dry_run:
            write(env_file, text)

    # -- 6. docker-compose passthrough --------------------------------------
    compose = product / "docker-compose.yml"
    text = read(compose)
    if "LEMONSQUEEZY_STORE_ID" not in text:
        text = sub_once(
            text,
            r"(      CORS_ORIGIN: \$\{CORS_ORIGIN:-[^}]*\})",
            r"\1\n" + COMPOSE_PAYMENT_ENV.rstrip("\n"),
            "docker-compose payment passthrough",
        )
        emit("docker-compose.yml: payment variables passed through to the API")
        if not dry_run:
            write(compose, text)

    # -- 7. frontend helper --------------------------------------------------
    fe_ls = fe / "src" / "services" / "lemonSqueezy.js"
    if "VITE_LEMONSQUEEZY_STORE_URL" not in read(fe_ls):
        if not dry_run:
            write(fe_ls, FRONTEND_LS)
        emit("frontend/src/services/lemonSqueezy.js: env config + backend checkout + demo dialog")
    else:
        emit("frontend lemonSqueezy.js: already upgraded")

    # -- 8. webhook registry ------------------------------------------------
    registry = be / "webhook-registry.json"
    if registry.exists():
        data = json.loads(read(registry))
        events = data.setdefault("events", [])
        known = {(e.get("event"), e.get("source")) for e in events}
        added = 0
        for event, source, description in LS_REGISTRY_EVENTS:
            if (event, source) not in known:
                events.append({"event": event, "source": source, "description": description})
                added += 1
        integrations = data.setdefault("integrations", [])
        if "lemonsqueezy" not in integrations:
            integrations.append("lemonsqueezy")
            added += 1
        if added and not dry_run:
            write(registry, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        emit(f"webhook-registry.json: {added} Lemon Squeezy entries added")

    # -- 9. documentation ---------------------------------------------------
    buyer_doc = product / "BUYER_DOCUMENTATION.md"
    brand = product_brand(read(buyer_doc), slug) if buyer_doc.exists() else slug
    if buyer_doc.exists():
        text = read(buyer_doc)
        new_section = buyer_payment_section(brand)
        pattern = r"## 2\. Connecting Lemon Squeezy Payments\n.*?(?=\n---\n\n## 3\.)"
        if "## 2. Connecting Lemon Squeezy Payments" in text:
            text = sub_once(text, pattern, new_section.rstrip("\n") + "\n", "buyer docs §2")
            emit("BUYER_DOCUMENTATION.md: payment section rewritten with the real endpoints")
            if not dry_run:
                write(buyer_doc, text)
        else:
            emit("BUYER_DOCUMENTATION.md: §2 heading not found — left untouched")

    seller_doc = product / "LEMON_SQUEEZY_SELLER_KIT.md"
    if seller_doc.exists():
        text = read(seller_doc)
        if "What The Buyer Sets Up After Purchase" not in text:
            text = text.rstrip("\n") + "\n" + seller_key_guide(brand)
            emit("LEMON_SQUEEZY_SELLER_KIT.md: buyer key-insertion guide appended")
            if not dry_run:
                write(seller_doc, text)

    return {"product": slug, "actions": log}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    products = sorted(
        p for p in PRODUCTS.iterdir()
        if p.is_dir() and (p / "backend").is_dir() and not p.name.startswith(".")
    )
    total = 0
    for product in products:
        result = process(product, args.dry_run)
        total += len(result["actions"])
        print(f"\n== {result['product']}")
        for line in result["actions"]:
            print(f"   {line}")
    print(f"\n{'would apply' if args.dry_run else 'applied'} {total} change(s) "
          f"across {len(products)} product(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())