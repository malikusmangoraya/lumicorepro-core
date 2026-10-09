/**
 * Lemon Squeezy integration — selling the product.
 * -----------------------------------------------
 * The marketplace already has Stripe/PayPal/Razorpay for *buying templates*,
 * but there was no way to sell THIS product itself through Lemon Squeezy.
 *
 * Flow:
 *   1. Lemon Squeezy sends a signed webhook (`X-Signature` = HMAC-SHA256 of the
 *      RAW body with the store signing secret). We verify it — an unsigned or
 *      forged event is rejected with 401 and never touches the database.
 *   2. `license_created` / `license_key_created` activate the buyer's key.
 *      The customer supplies our HMAC key through the Lemon Squeezy checkout
 *      custom field, so we record the entitlement against a key we already
 *      know is genuine (validateLicenseKey still decides the verdict).
 *   3. `subscription_cancelled` / `subscription_expired` / refund events
 *      revoke or suspend the entitlement — a cancelled buyer stops activating.
 *
 * Entitlements are persisted (the license engine itself is stateless/HMAC),
 * which is what makes revocation possible.
 */
import crypto from 'crypto';
import { validateLicenseKey, groupCode, normalizeCode } from '../utils/license.js';
import LicenseEntitlement from '../models/LicenseEntitlement.js';
import logger from '../utils/logger.js';

export function signingSecret() {
  return process.env.LEMONSQUEEZY_SIGNING_SECRET || '';
}

export function isConfigured() {
  return Boolean(signingSecret());
}

/** Constant-time HMAC-SHA256 verification of the raw webhook body. */
export function verifySignature(rawBody, signature) {
  const secret = signingSecret();
  if (!secret) return { verified: false, reason: 'signing_secret_missing' };
  if (typeof signature !== 'string' || !signature.length) {
    return { verified: false, reason: 'signature_missing' };
  }
  const expected = crypto.createHmac('sha256', secret).update(rawBody ?? '').digest('hex');
  const a = Buffer.from(expected, 'utf8');
  const b = Buffer.from(signature.toLowerCase(), 'utf8');
  if (a.length !== b.length) return { verified: false, reason: 'signature_mismatch' };
  return crypto.timingSafeEqual(a, b) ? { verified: true } : { verified: false, reason: 'signature_mismatch' };
}

/** Pull the fields we care about out of a Lemon Squeezy event envelope. */
export function parseEvent(payload) {
  const data = payload?.data || {};
  const attributes = data.attributes || {};
  const meta = attributes.meta?.custom_data || attributes.meta || {};
  const licenseKey = attributes.license_key?.key || attributes.key || meta.license_key || null;
  const variantName = attributes.variant_name || attributes.variant?.name || meta.variant || null;
  const orderId = attributes.order_id ?? null;
  const storeId = attributes.store_id ?? null;
  const customerEmail = attributes.user_email || attributes.customer_email || meta.email || null;
  const customerName = attributes.user_name || attributes.customer_name || null;
  const expiresAt = attributes.renews_at || attributes.ends_at || attributes.expiry || null;
  return {
    event: payload?.meta?.event_name || null,
    licenseKey: licenseKey ? groupCode(normalizeCode(licenseKey)) : null,
    variantName,
    orderId: orderId ? String(orderId) : null,
    storeId: storeId ? String(storeId) : null,
    customerEmail,
    customerName,
    expiresAt: expiresAt ? new Date(expiresAt) : null,
  };
}

const REVOKE_EVENTS = new Set([
  'subscription_cancelled',
  'subscription_expired',
  'subscription_paused',
  'order_refunded',
]);

/** Persist an entitlement for a Lemon Squeezy purchase. */
export async function recordEntitlement({
  licenseKey, variantName = null, orderId = null, storeId = null,
  email = null, name = null, status = 'active', expiresAt = null,
} = {}, model = LicenseEntitlement) {
  const validation = validateLicenseKey(licenseKey);
  // A key that fails HMAC validation is recorded as 'rejected' (never as an
  // active entitlement) so an operator can see a bad checkout instead of it
  // silently activating. Explicit revocation states pass through untouched.
  const effectiveStatus = !validation.valid && status === 'active' ? 'rejected' : status;
  const row = {
    license_key: groupCode(normalizeCode(licenseKey)),
    variant_name: variantName,
    order_id: orderId,
    store_id: storeId,
    customer_email: email,
    customer_name: name,
    status: effectiveStatus,
    license_valid: Boolean(validation.valid),
    license_status: validation.status || 'invalid',
    activated_at: effectiveStatus === 'active' ? new Date() : null,
    expires_at: expiresAt,
  };
  const existing = await model.findOne({ where: { license_key: row.license_key } });
  if (existing) {
    await existing.update({ ...row, activated_at: row.activated_at || existing.activated_at });
    return existing;
  }
  return model.create(row);
}

/** Handle a verified webhook payload. Returns the action taken. */
export async function handleEvent(payload, model = LicenseEntitlement) {
  const parsed = parseEvent(payload);
  if (!parsed.event) return { action: 'ignored', reason: 'no_event_name' };
  if (!parsed.licenseKey) return { action: 'ignored', reason: 'no_license_key', event: parsed.event };
  if (REVOKE_EVENTS.has(parsed.event)) {
    const existing = await model.findOne({ where: { license_key: parsed.licenseKey } });
    if (!existing) {
      logger.warn(`LemonSqueezy ${parsed.event}: no entitlement for ${parsed.licenseKey}`);
      return { action: 'ignored', reason: 'entitlement_not_found', event: parsed.event };
    }
    await existing.update({ status: parsed.event === 'subscription_paused' ? 'paused' : 'revoked' });
    return { action: 'revoked', event: parsed.event, licenseKey: parsed.licenseKey };
  }
  const row = await recordEntitlement({ ...parsed, status: 'active' }, model);
  return {
    action: 'activated',
    event: parsed.event,
    licenseKey: parsed.licenseKey,
    licenseValid: Boolean(row.license_valid),
  };
}

/** Public entitlement lookup used by the app's activation screen. */
export async function getEntitlement(licenseKey, model = LicenseEntitlement) {
  if (!licenseKey) return null;
  const row = await model.findOne({
    where: { license_key: groupCode(normalizeCode(licenseKey)) },
    raw: true,
  });
  if (!row) return { known: false, status: 'not_purchased' };
  const validation = validateLicenseKey(licenseKey);
  return {
    known: true,
    status: row.status,
    licenseValid: Boolean(validation.valid),
    licenseStatus: validation.status,
    variant: row.variant_name,
    activatedAt: row.activated_at,
    expiresAt: row.expires_at,
    active: row.status === 'active' && Boolean(validation.valid),
  };
}

export default {
  verifySignature,
  parseEvent,
  handleEvent,
  recordEntitlement,
  getEntitlement,
  isConfigured,
};