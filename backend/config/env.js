/**
 * Environment Configuration & Validation (fail-fast)
 * ------------------------------------------------
 * Validates .env on app start with a light, dependency-free schema so a
 * missing/invalid production variable surfaces immediately instead of as a
 * silent runtime bug. Wrap each call in try/catch at bootstrap to toggle
 * strictness (always strict in production).
 */
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env explicitly so validation sees values regardless of server.js order.
const envFile = path.join(__dirname, '..', '.env');
if (fs.existsSync(envFile)) dotenv.config({ path: envFile });

const required = {
  JWT_SECRET: { min: 32, msg: 'JWT_SECRET must be at least 32 chars (use a strong random secret)' },
  JWT_REFRESH_SECRET: { min: 32, msg: 'JWT_REFRESH_SECRET must be at least 32 chars' },
};

const numbers = {
  PORT: { min: 1, max: 65535 },
};

const optional = {
  DEFAULT_CURRENCY: { pattern: /^[A-Z]{3}$/, msg: 'DEFAULT_CURRENCY must be an ISO 4217 3-letter code (e.g. USD)' },
  DEFAULT_LOCALE: { pattern: /^[a-z]{2}([_-][A-Za-z]{2,4})?$/, msg: 'DEFAULT_LOCALE must be a BCP 47 tag (e.g. en, en-US)' },
  TZ: { pattern: /^[A-Za-z_]+(\/[A-Za-z_+\/-]+)?$/, msg: 'TZ must be a valid IANA timezone (e.g. UTC, Asia/Karachi)' },
};

// ── Access-token lifetime policy (AGENTS.md §3) ─────────────────────────────
// 15-minute access tokens are the documented default; a production deployment
// may raise JWT_EXPIRE but never beyond one hour.
const ACCESS_TOKEN_MAX_MS = 60 * 60 * 1000; // 1h
const DURATION_RE = /^(\d+)\s*(ms|s|m|h|d)?$/i;
const DURATION_UNIT_MS = { ms: 1, s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000 };

/**
 * Parse a jwt/ms-style duration ('15m', '900s', '1h', '2d', bare seconds).
 *
 * @param {string|number} value - Duration string from env
 * @returns {number|null} Milliseconds, or null when unparseable
 */
export function parseDurationMs(value) {
  if (value === undefined || value === null || value === '') return null;
  const match = String(value).trim().match(DURATION_RE);
  if (!match) return null;
  const amount = Number(match[1]);
  const unit = (match[2] || 's').toLowerCase();
  if (!Number.isSafeInteger(amount) || amount <= 0) return null;
  return amount * DURATION_UNIT_MS[unit];
}

export function isValidOrigin(value) {
  if (typeof value !== 'string' || !/^https?:\/\/[^/\s?#]+$/.test(value.trim())) return false;
  try {
    const url = new URL(value.trim());
    if (!['http:', 'https:'].includes(url.protocol)) return false;
    if (url.username || url.password) return false;
    if (url.port) {
      const port = Number(url.port);
      if (!Number.isInteger(port) || port < 1 || port > 65535) return false;
    }
    return true;
  } catch {
    return false;
  }
}

// A 32-character example secret is still an example secret. Copy-pasted
// .env.example values must not boot production.
const SECRET_PLACEHOLDER_MARKERS = [
  'your_',
  'your-',
  'change-this',
  'changeme',
  'example',
  'placeholder',
];

function looksLikePlaceholderSecret(value) {
  const normalized = String(value || '').trim().toLowerCase();
  return SECRET_PLACEHOLDER_MARKERS.some((marker) => normalized.includes(marker));
}

/** Validate and return normalized errors, or null when valid. */
export function validateConfig(env = process.env, { strict = false } = {}) {
  const errors = [];

  for (const [key, rule] of Object.entries(required)) {
    const val = env[key];
    if (!val) {
      errors.push(`Missing required env var: ${key}`);
      continue;
    }
    if (rule.min && val.length < rule.min) errors.push(rule.msg);
    if (env.NODE_ENV === 'production' && looksLikePlaceholderSecret(val)) {
      errors.push(
        `Invalid env var ${key} in production: value looks like an example/placeholder secret. ` +
          'Generate a random secret instead of copying .env.example.',
      );
    }
  }

  for (const [key, rule] of Object.entries(numbers)) {
    if (env[key] === undefined) continue;
    const num = Number(env[key]);
    if (!Number.isFinite(num) || num < rule.min || num > rule.max) {
      errors.push(`Invalid env var ${key}: expected number in [${rule.min}, ${rule.max}]`);
    }
  }

  for (const [key, rule] of Object.entries(optional)) {
    if (env[key] === undefined || env[key] === '') continue;
    if (rule.pattern && !rule.pattern.test(String(env[key]).trim())) {
      errors.push(`Invalid env var ${key}: ${rule.msg}`);
    }
  }

  // JWT_EXPIRE: access tokens must stay short-lived. In production anything
  // above 1 hour is rejected outright (policy: 15m access + 7d refresh).
  if (env.JWT_EXPIRE !== undefined && env.JWT_EXPIRE !== '') {
    const expiresMs = parseDurationMs(env.JWT_EXPIRE);
    if (expiresMs === null) {
      errors.push(
        `Invalid env var JWT_EXPIRE: "${env.JWT_EXPIRE}" is not a duration. ` +
          'Use a jwt duration such as 15m, 900s or 1h.',
      );
    } else if (env.NODE_ENV === 'production' && expiresMs > ACCESS_TOKEN_MAX_MS) {
      errors.push(
        `Invalid env var JWT_EXPIRE in production: "${env.JWT_EXPIRE}" exceeds the 1-hour maximum ` +
          'for access tokens (policy: 15m access + 7d rotating refresh). Set JWT_EXPIRE=15m.',
      );
    }
  }

  // Production needs an explicit database connection and browser origin allow-list.
  // Localhost fallbacks are a deployment misconfiguration, not a secure default.
  if (env.NODE_ENV === 'production') {
    if (!env.DATABASE_URL) {
      errors.push('Missing required env var: DATABASE_URL');
    }
    const origins = String(env.ALLOWED_ORIGINS || '')
      .split(',')
      .map((origin) => origin.trim())
      .filter(Boolean);
    if (!origins.length || !origins.every(isValidOrigin)) {
      errors.push('Invalid env var ALLOWED_ORIGINS: use comma-separated origins such as https://app.example.com,http://localhost:5173');
    }
  }

  return { ok: errors.length === 0, errors, strict };
}

/** Fail-fast: throws describing missing/invalid vars. */
export function assertValidConfig(env = process.env) {
  const { ok, errors } = validateConfig(env);
  if (!ok) {
    throw new Error(
      `Environment validation failed:\n - ${errors.join('\n - ')}\n` +
        'Fix these in backend/.env before starting.',
    );
  }
}

/** No-op that returns ok so tests/offline dev can short-circuit cleanly. */
export function envReady() {
  const { ok, errors } = validateConfig();
  return { ok, errors };
}

export default {
  validate: validateConfig,
  assertValid: assertValidConfig,
  ready: envReady,
};
