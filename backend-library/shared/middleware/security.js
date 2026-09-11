/**
 * Enterprise security middleware for Express backends.
 * Industry-standard: Helmet, rate limiting, CORS whitelist, input sanitization.
 */

const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

const DEFAULT_CORS_ORIGINS = [
  'http://localhost:5173',
  'http://localhost:3000',
  process.env.FRONTEND_URL,
].filter(Boolean);

function createRateLimiter(options = {}) {
  return rateLimit({
    windowMs: options.windowMs || 15 * 60 * 1000,
    max: options.max || 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      success: false,
      status: 429,
      message: 'Too many requests. Please try again later.',
    },
  });
}

function createStrictRateLimiter() {
  return rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 20,
    message: { success: false, status: 429, message: 'Auth rate limit exceeded.' },
  });
}

function createCorsMiddleware(origins = DEFAULT_CORS_ORIGINS) {
  return cors({
    origin: (origin, callback) => {
      if (!origin || origins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error(`CORS blocked: ${origin}`));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  });
}

function sanitizeInput(req, res, next) {
  const sanitize = (obj) => {
    if (!obj || typeof obj !== 'object') return obj;
    for (const key of Object.keys(obj)) {
      if (typeof obj[key] === 'string') {
        obj[key] = obj[key]
          .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
          .replace(/javascript:/gi, '')
          .trim();
      } else if (typeof obj[key] === 'object') {
        sanitize(obj[key]);
      }
    }
    return obj;
  };

  if (req.body) sanitize(req.body);
  if (req.query) sanitize(req.query);
  next();
}

function securityHeaders() {
  return helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", 'data:', 'https:'],
        connectSrc: ["'self'", process.env.API_URL || ''].filter(Boolean),
      },
    },
    crossOriginEmbedderPolicy: false,
  });
}

function applySecurityMiddleware(app, options = {}) {
  app.use(securityHeaders());
  app.use(createCorsMiddleware(options.corsOrigins));
  app.use(sanitizeInput);
  app.use('/api/', createRateLimiter(options.rateLimit));
  app.use('/api/auth/', createStrictRateLimiter());
}

module.exports = {
  applySecurityMiddleware,
  createRateLimiter,
  createStrictRateLimiter,
  createCorsMiddleware,
  sanitizeInput,
  securityHeaders,
};
