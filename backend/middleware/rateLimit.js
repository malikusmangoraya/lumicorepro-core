/**
 * Rate Limiting (Redis-backed, per-route granular)
 * -------------------------------------------------
 * Different limits per route sensitivity:
 *   - auth/login:   strict (5/min)
 *   - public reads: loose
 *   - payments:     strict
 * Returns 429 with Retry-After header. Falls back to MemoryStore when Redis is
 * unavailable so the API still boots/works offline.
 */
import rateLimit from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';
import { getRedis, isRedisAvailable } from '../services/cache/redis.client.js';

const WINDOW = 15 * 60 * 1000;

function buildLimiter({ name, windowMs, max, message }) {
  const opts = {
    windowMs,
    max,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    message: {
      success: false,
      error: { code: 'RATE_LIMITED', message: message || 'Too many requests. Please try again later.' },
    },
    store: isRedisAvailable()
      ? new RedisStore({ client: getRedis(), prefix: `rl:${name}:` })
      : undefined,
    handler: (req, res, next, options) => {
      const retryAfter = Math.ceil((options.windowMs - (Date.now() % options.windowMs)) / 1000) || 1;
      res.setHeader('Retry-After', String(retryAfter));
      res.status(429).json(options.message);
    },
  };
  return rateLimit(opts);
}

export const authLimiter = buildLimiter({
  name: 'auth',
  windowMs: 60 * 1000,
  max: 5,
  message: 'Too many auth attempts. Try again in a minute.',
});

export const paymentLimiter = buildLimiter({
  name: 'payment',
  windowMs: WINDOW,
  max: 30,
  message: 'Too many payment attempts. Please retry shortly.',
});

export const apiLimiter = buildLimiter({
  name: 'api',
  windowMs: WINDOW,
  max: Number(process.env.RATE_LIMIT_MAX_REQUESTS) || 300,
  message: 'Rate limit exceeded. Please try again later.',
});

export const uploadLimiter = buildLimiter({
  name: 'upload',
  windowMs: WINDOW,
  max: 60,
  message: 'Too many uploads. Slow down.',
});

export const aiLimiter = buildLimiter({
  name: 'ai',
  windowMs: 60 * 1000,
  max: 30,
  message: 'Too many AI requests. Please wait a moment.',
});

export const aiWriteLimiter = buildLimiter({
  name: 'ai_write',
  windowMs: 60 * 1000,
  max: 10,
  message: 'Too many generation requests. Please wait a moment.',
});

export const licenseLimiter = buildLimiter({
  name: 'license',
  windowMs: WINDOW,
  max: 60,
  message: 'Too many license checks. Please try again later.',
});

export default { authLimiter, paymentLimiter, apiLimiter, uploadLimiter, aiLimiter, aiWriteLimiter, licenseLimiter };