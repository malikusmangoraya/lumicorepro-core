import cors from 'cors';
import helmet from 'helmet';
import jwt from 'jsonwebtoken';
import logger from '../utils/logger.js';

// Production CORS Configuration
const allowedOrigins = (
  process.env.ALLOWED_ORIGINS || 'http://localhost:5173,http://localhost:3000'
)
  .split(',')
  .map((origin) => origin.trim());

// Origins that are safe to trust without an explicit allowlist entry:
// localhost, and (outside production only) RFC1918 private LAN ranges so a
// developer can test from a phone/other device on the same network.
const LOCAL_ORIGIN_RE = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;
const LAN_ORIGIN_RE =
  /^https?:\/\/(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$/;
const isProduction = process.env.NODE_ENV === 'production';

export const corsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (e.g. mobile apps, curl, server-to-server)
    if (!origin) return callback(null, true);

    // Security: never reflect an arbitrary internet Origin together with
    // `credentials: true` — that lets any website read authenticated
    // responses. Outside production we only trust loopback + private LAN.
    const trusted =
      allowedOrigins.includes(origin) ||
      LOCAL_ORIGIN_RE.test(origin) ||
      (!isProduction && LAN_ORIGIN_RE.test(origin));

    if (trusted) {
      return callback(null, true);
    }
    logger.warn(`Blocked by CORS: ${origin}`);
    return callback(new Error('Origin blocked by CORS policy'), false);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'X-API-Key',
    'X-Org-Id',
    'X-Tenant',
    'Accept',
  ],
  exposedHeaders: ['Content-Range', 'X-Content-Range'],
  maxAge: 86400, // 24 hours preflight cache
};

export const corsMiddleware = cors(corsOptions);

// Helmet Strict Security Policy
export const helmetMiddleware = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://js.stripe.com'],
      styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
      fontSrc: ["'self'", 'https://fonts.gstatic.com', 'data:'],
      imgSrc: ["'self'", 'data:', 'blob:', 'https:', 'http:'],
      connectSrc: [
        "'self'",
        'https://api.stripe.com',
        'https://*.sentry.io',
        'ws:',
        'wss:',
        'http://localhost:*',
      ],
      frameSrc: ["'self'", 'https://js.stripe.com', 'https://hooks.stripe.com'],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: process.env.NODE_ENV === 'production' ? [] : null,
    },
  },
  crossOriginEmbedderPolicy: false,
  crossOriginResourcePolicy: { policy: 'cross-origin' },
  dnsPrefetchControl: { allow: true },
  frameguard: { action: 'sameorigin' },
  hidePoweredBy: true,
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
  ieNoOpen: true,
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  xssFilter: true,
});

// API Key Validation Middleware

/**
 * Resolve the set of accepted service-to-service API keys.
 *
 * Security: a hardcoded fallback key shipped in source is a real credential
 * leak. In production we FAIL SECURE — if VALID_API_KEYS is unset/empty the
 * caller gets an empty allowlist and every key check returns 401, which
 * surfaces the misconfiguration immediately instead of silently accepting a
 * publicly-known key. The dev-only fallback exists purely for local DX.
 */
const DEV_API_KEY = '';
function resolveValidApiKeys() {
  const configured = (process.env.VALID_API_KEYS || '')
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean);
  if (configured.length > 0) return configured;
  if (process.env.NODE_ENV === 'production') {
    logger.error('VALID_API_KEYS is not set — refusing all API-key auth in production');
    return [];
  }
  return [DEV_API_KEY];
}

export const requireApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const validKeys = resolveValidApiKeys();

  if (!apiKey || !validKeys.includes(apiKey)) {
    return res.status(401).json({
      success: false,
      error: 'Invalid or missing API key',
    });
  }

  next();
};

/**
 * Gate for cost-heavy AI endpoints. Accepts either:
 *  - a valid `x-api-key` (service-to-service), or
 *  - a valid Bearer JWT (signed-in frontend users)
 * and returns 401 otherwise. Keeps the public demo UX working while
 * preventing unauthenticated abuse of expensive generation endpoints.
 */
export const gateAI = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const validKeys = resolveValidApiKeys();
  if (apiKey && validKeys.includes(apiKey)) return next();

  const authHeader = req.headers.authorization;
  if (authHeader?.startsWith('Bearer ')) {
    try {
      const decoded = jwt.verify(authHeader.slice(7), process.env.JWT_SECRET, {
        algorithms: ['HS256'],
      });
      if (decoded?.id) {
        req.user = req.user || { id: decoded.id };
        return next();
      }
    } catch {
      /* fall through to 401 */
    }
  }

  return res.status(401).json({
    success: false,
    error: 'Authentication or API key required',
  });
};
