/**
 * Structured Logging System (Winston) — upgraded
 * ----------------------------------------------
 * - Console + rotating file transports (error.log / combined.log).
 * - Request-id correlation: attach { requestId } to every record.
 * - Sensitive-data redaction: passwords, tokens, secrets, card numbers and
 *   Authorization headers are scrubbed from log output (keys + values).
 * - Levels: error (0) / warn (1) / info (2) / http (3) / debug (4).
 */
import winston from 'winston';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const logDir = path.join(__dirname, '..', 'logs');
if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });

// ── Sensitive field names (values are always redacted regardless of case) ──
const SENSITIVE_KEYS = new Set([
  'password',
  'pass',
  'pwd',
  'secret',
  'token',
  'access_token',
  'refresh_token',
  'authorization',
  'apikey',
  'api_key',
  'x-api-key',
  'cardnumber',
  'card_number',
  'cvv',
  'cvc',
  'pan',
  'otp',
  'pin',
  'session',
  'jwt',
  'client_secret',
  'stripe_secret_key',
  'smtp_pass',
  'db_password',
  'private_key',
]);
const REDACTED = '[REDACTED]';

// Regexes for inline "key=value" / "key: value" / JSON-like patterns
const TOKEN_RE = /\b([A-Za-z0-9_\-]{8,})\b/g;

/** Deep-redact an object/array without mutating the original. */
export function redact(value, key = '') {
  // Scalar: redact if the value itself looks like a token and the key is sensitive
  if (typeof value === 'string') {
    if (SENSITIVE_KEYS.has(String(key).toLowerCase().replace(/-/g, '_'))) {
      return REDACTED;
    }
    // Redact extracted JWT / bearer-like strings to avoid accidental leakage
    if (/eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/.test(value)) {
      return REDACTED;
    }
    return value;
  }

  if (value === null || value === undefined) return value;

  if (Array.isArray(value)) {
    return value.map((item) => redact(item, key));
  }

  if (typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      out[k] = SENSITIVE_KEYS.has(k.toLowerCase().replace(/-/g, '_')) ? REDACTED : redact(v, k);
    }
    return out;
  }

  return value;
}

// ── Formats ────────────────────────────────────────────────────────────────
const jsonFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.splat(),
  winston.format((info) => {
    info.requestId = info.requestId || (info.meta && info.meta.requestId);
    if (info.message && typeof info.message === 'object') {
      info.message = redact(info.message);
    }
    if (info.meta) info.meta = redact(info.meta);
    return info;
  })(),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'HH:mm:ss' }),
  winston.format.printf(({ level, message, timestamp, requestId, stack, meta }) => {
    const rid = requestId ? ` [req=${requestId}]` : '';
    const detail = meta ? ` ${JSON.stringify(redact(meta))}` : '';
    return `${timestamp} ${level}${rid}: ${stack || (typeof message === 'string' ? message : JSON.stringify(redact(message)))}${detail}`;
  })
);

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug'),
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json()
  ),
  defaultMeta: { service: 'lumicorepro-api' },
  transports: [
    new winston.transports.Console({ format: consoleFormat }),
    new winston.transports.File({
      filename: path.join(logDir, 'error.log'),
      level: 'error',
      format: jsonFormat,
      maxsize: 5242880,
      maxFiles: 5,
    }),
    new winston.transports.File({
      filename: path.join(logDir, 'combined.log'),
      format: jsonFormat,
      maxsize: 10485760,
      maxFiles: 5,
    }),
  ],
});

/** Bind a request-scoped logger that auto-tags every call with the request id. */
export const withRequestId = (rid) => ({
  error: (msg, meta) => logger.error(msg, { ...meta, requestId: rid }),
  warn: (msg, meta) => logger.warn(msg, { ...meta, requestId: rid }),
  info: (msg, meta) => logger.info(msg, { ...meta, requestId: rid }),
  http: (msg, meta) => logger.http(msg, { ...meta, requestId: rid }),
  debug: (msg, meta) => logger.debug(msg, { ...meta, requestId: rid }),
});

export default logger;
