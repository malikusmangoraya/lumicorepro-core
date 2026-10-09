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
  JWT_SECRET: { min: 16, msg: 'JWT_SECRET must be at least 16 chars (use a strong random secret)' },
  JWT_REFRESH_SECRET: { min: 16, msg: 'JWT_REFRESH_SECRET must be at least 16 chars' },
};

const numbers = {
  PORT: { min: 1, max: 65535 },
};

const optional = {
  DEFAULT_CURRENCY: {
    pattern: /^[A-Z]{3}$/,
    msg: 'DEFAULT_CURRENCY must be an ISO 4217 3-letter code (e.g. USD)',
  },
  DEFAULT_LOCALE: {
    pattern: /^[a-z]{2}([_-][A-Za-z]{2,4})?$/,
    msg: 'DEFAULT_LOCALE must be a BCP 47 tag (e.g. en, en-US)',
  },
  TZ: {
    pattern: /^[A-Za-z_]+(\/[A-Za-z_+\/-]+)?$/,
    msg: 'TZ must be a valid IANA timezone (e.g. UTC, Asia/Karachi)',
  },
};

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

  return { ok: errors.length === 0, errors, strict };
}

/** Fail-fast: throws describing missing/invalid vars. */
export function assertValidConfig(env = process.env) {
  const { ok, errors } = validateConfig(env);
  if (!ok) {
    throw new Error(
      `Environment validation failed:\n - ${errors.join('\n - ')}\n` +
        'Fix these in backend/.env before starting.'
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
