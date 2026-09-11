/**
 * Self-Hosted License Key Engine (free, no licensing SaaS)
 * ---------------------------------------------------------
 * HMAC-SHA256 signed license keys validated entirely offline on our own
 * server. Keys are base32 (parse-safe, uppercase) grouped as
 * LMC-XXXXX-XXXXX-XXXXX-... and wrap a signed payload:
 *
 *   { licenseType: 'trial'|'full', product, issuedAt, expiry, features? }
 *
 * Signature is HMAC(secret) so keys can never be forged without
 * LICENSE_SECRET (kept in .env, never committed).
 *
 * Trial keys carry built-in expiry (LICENSE_TRIAL_DAYS, default 14) and are
 * meant to be paired with the frontend LicenseWatermark component.
 */
import crypto from 'crypto';

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

function secret() {
  return process.env.LICENSE_SECRET || '';
}

function trialDays() {
  return parseInt(process.env.LICENSE_TRIAL_DAYS || '14', 10);
}

function productName() {
  return process.env.LICENSE_PRODUCT || 'lumicorepro-core';
}

/* ── tiny base32 (RFC 4648, no padding) ────────────────────────────────── */
function toBase32(buf) {
  const bytes = Buffer.from(buf);
  let out = '';
  let bits = 0;
  let value = 0;
  for (const byte of bytes) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      out += ALPHABET[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) out += ALPHABET[(value << (5 - bits)) & 31];
  return out;
}

function fromBase32(str) {
  const clean = String(str).replace(/[^A-Za-z2-7]/g, '').toUpperCase();
  const bytes = [];
  let bits = 0;
  let value = 0;
  for (const ch of clean) {
    const idx = ALPHABET.indexOf(ch);
    if (idx === -1) return null;
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return Buffer.from(bytes);
}

/* ── key assembly ────────────────────────────────────────────────────────── */
function hmac(payload) {
  return crypto.createHmac('sha256', secret()).update(payload).digest();
}

/** Encode { parts[] } into a compact binary blob + HMAC tag. */
function encodePayload(parts) {
  const payload = Buffer.from(parts.join('\u0001'), 'utf8');
  // 1-byte length prefix keeps { payload, tag } unambiguous after decode.
  const blob = Buffer.concat([Buffer.from([payload.length]), payload, hmac(payload)]);
  return toBase32(blob);
}

function decodePayload(code) {
  const blob = fromBase32(code);
  if (!blob || blob.length < 33) return null;
  const len = blob[0];
  const payload = blob.subarray(1, 1 + len).toString('utf8');
  const tag = blob.subarray(1 + len);
  const expect = hmac(payload);
  if (tag.length !== expect.length) return null;
  if (!crypto.timingSafeEqual(tag, expect)) return null;
  return payload.split('\u0001');
}

/** Build a raw (ungrouped) license code from payload parts. */
export function buildCode(parts) {
  return `LMC-${encodePayload(parts)}`;
}

/** Parse a license code (accepts any dash/space grouping) into payload parts or null. */
export function parseCode(code) {
  const raw = String(code || '').trim();
  const m = raw.match(/^LMC-?([A-Za-z2-7]+)$/i);
  if (!m) return null;
  return decodePayload(m[1]);
}

/** Group a code into LMC-XXXXX-XXXXX-… display form. */
export function groupCode(code) {
  const body = String(code || '').replace(/^LMC-?/i, '');
  const groups = [];
  for (let i = 0; i < body.length; i += 5) groups.push(body.slice(i, i + 5));
  return `LMC-${groups.join('-')}`;
}

/** Normalize any user-entered display form back to a parseable code. */
export function normalizeCode(raw) {
  const body = String(raw || '').replace(/^LMC-?/i, '').replace(/[\s-]/g, '').toUpperCase();
  return body ? `LMC-${body}` : '';
}

/* ── lifecycle ────────────────────────────────────────────────────────────── */
export function generateLicenseKey({ licenseType = 'full', product = productName(), days = 0, features = [] } = {}) {
  const issuedAt = Date.now();
  const expiry = days > 0 ? issuedAt + days * 86400000 : 0;
  const token = buildCode([licenseType, product, String(issuedAt), String(expiry), features.join(',')]);
  return { key: groupCode(token), licenseType, issuedAt, expiry };
}

export function generateTrialKey(product = productName()) {
  return generateLicenseKey({ licenseType: 'trial', product, days: trialDays() });
}

const EMPTY = {
  valid: false,
  status: 'invalid',
  licenseType: null,
  product: null,
  issuedAt: null,
  expiry: null,
  daysLeft: 0,
  trial: false,
};

export function validateLicenseKey(rawKey, { product = productName() } = {}) {
  if (!secret()) return { ...EMPTY, status: 'unconfigured', message: 'LICENSE_SECRET is not set in .env' };
  const parts = parseCode(normalizeCode(rawKey));
  if (!parts || parts.length < 5) return EMPTY;

  const [licenseType, prod, issuedAtS, expiryS, featuresS] = parts;
  const issuedAt = Number(issuedAtS);
  const expiry = Number(expiryS);
  const now = Date.now();

  if (!Number.isFinite(issuedAt) || !Number.isFinite(expiry)) return EMPTY;
  if (product && prod && prod !== product) {
    return { ...EMPTY, status: 'wrong_product', product: prod };
  }

  const trial = licenseType === 'trial';
  if (expiry > 0 && now > expiry) {
    return {
      valid: false,
      status: 'expired',
      licenseType,
      product: prod,
      issuedAt,
      expiry,
      daysLeft: 0,
      trial,
    };
  }

  return {
    valid: true,
    status: 'active',
    licenseType,
    product: prod,
    issuedAt,
    expiry,
    features: featuresS ? featuresS.split(',').filter(Boolean) : [],
    trial,
    daysLeft: expiry > 0 ? Math.max(0, Math.ceil((expiry - now) / 86400000)) : Infinity,
  };
}

export default {
  generateLicenseKey,
  generateTrialKey,
  validateLicenseKey,
  parseCode,
  groupCode,
  normalizeCode,
};