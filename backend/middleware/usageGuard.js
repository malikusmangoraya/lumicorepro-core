/**
 * AI Usage Guard — Server-side cost protection middleware
 * -------------------------------------------------------
 * 1. Daily generation limit per user/IP (configurable via env)
 * 2. Circuit breaker: auto-block IPs/users with abnormal request rates
 * 3. Request counters for the spend estimator dashboard
 * 4. Per-request token cap enforcement
 *
 * Storage: Redis if available, else in-memory Map with TTL.
 * All enforcement is SERVER-ONLY — client-side checks are cosmetic.
 */
import { getRedis, isRedisAvailable } from '../services/cache/redis.client.js';
import logger from '../utils/logger.js';

// ── Config from env (all overridable) ──────────────────────────────────────
const DAILY_GEN_LIMIT = parseInt(process.env.AI_DAILY_GEN_LIMIT, 10) || 3;
const DAILY_CHAT_LIMIT = parseInt(process.env.AI_DAILY_CHAT_LIMIT, 10) || 20;
const DAILY_VISION_LIMIT = parseInt(process.env.AI_DAILY_VISION_LIMIT, 10) || 10;

// Circuit breaker thresholds
const CB_WINDOW_SECS = 60;
const CB_MAX_REQUESTS = parseInt(process.env.AI_CB_MAX_REQUESTS, 10) || 10;
const CB_BLOCK_SECS = parseInt(process.env.AI_CB_BLOCK_SECS, 10) || 300;

// Token hard caps (per-request)
export const MAX_TOKENS_GENERATION = parseInt(process.env.AI_MAX_TOKENS_GENERATION, 10) || 12000;
export const MAX_TOKENS_CHAT = parseInt(process.env.AI_MAX_TOKENS_CHAT, 10) || 4000;
export const MAX_TOKENS_VISION = parseInt(process.env.AI_MAX_TOKENS_VISION, 10) || 2000;

// ── In-memory fallback stores ──────────────────────────────────────────────
// { key: { count, resetAt } }
const _dailyCounts = new Map();
// { key: [timestamps] }
const _circuitWindow = new Map();
// { key: blockUntil }
const _circuitBlocks = new Map();

// Cleanup stale entries every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of _dailyCounts) {
    if (v.resetAt < now) _dailyCounts.delete(k);
  }
  for (const [k, v] of _circuitBlocks) {
    if (v < now) _circuitBlocks.delete(k);
  }
  for (const [k, arr] of _circuitWindow) {
    const fresh = arr.filter((t) => now - t < CB_WINDOW_SECS * 1000);
    if (fresh.length === 0) _circuitWindow.delete(k);
    else _circuitWindow.set(k, fresh);
  }
}, 5 * 60 * 1000).unref();

// ── Redis helpers ──────────────────────────────────────────────────────────
async function redisGet(key) {
  if (!isRedisAvailable()) return null;
  try {
    const val = await getRedis().get(key);
    return val !== null ? parseInt(val, 10) : null;
  } catch {
    return null;
  }
}

async function redisIncrExpiry(key, windowSecs) {
  if (!isRedisAvailable()) return null;
  try {
    const r = getRedis();
    const val = await r.incr(key);
    if (val === 1) await r.expire(key, windowSecs);
    return val;
  } catch {
    return null;
  }
}

async function redisSetNX(key, value, expirySecs) {
  if (!isRedisAvailable()) return null;
  try {
    const set = await getRedis().set(key, value, 'EX', expirySecs, 'NX');
    return set === 'OK';
  } catch {
    return null;
  }
}

// ── Daily limit counter ────────────────────────────────────────────────────
function _todayKey(prefix, identifier) {
  const d = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  return `usage:${prefix}:${identifier}:${d}`;
}

async function _checkDailyLimit(prefix, identifier, limit) {
  const key = _todayKey(prefix, identifier);

  // Try Redis first
  const redisVal = await redisIncrExpiry(key, 86400);
  if (redisVal !== null) {
    return { allowed: redisVal <= limit, count: redisVal, limit, resetsAt: _endOfDay() };
  }

  // In-memory fallback
  const now = Date.now();
  let entry = _dailyCounts.get(key);
  if (!entry || entry.resetAt < now) {
    entry = { count: 0, resetAt: _endOfDay() };
  }
  entry.count += 1;
  _dailyCounts.set(key, entry);
  return { allowed: entry.count <= limit, count: entry.count, limit, resetsAt: entry.resetAt };
}

function _endOfDay() {
  const now = new Date();
  const end = new Date(now);
  end.setUTCHours(23, 59, 59, 999);
  return end.getTime();
}

// ── Circuit breaker ────────────────────────────────────────────────────────
function _clientKey(req) {
  // Prefer authenticated user ID, fall back to IP
  const userId = req.user?.id || req.userId;
  const ip = req.ip || req.connection?.remoteAddress || 'unknown';
  return userId ? `user:${userId}` : `ip:${ip}`;
}

async function _checkCircuitBreaker(identifier) {
  const now = Date.now();
  const blockKey = `cb_block:${identifier}`;

  // Check if currently blocked (Redis or memory)
  const blockedUntilRedis = await redisGet(blockKey);
  if (blockedUntilRedis !== null) {
    if (blockedUntilRedis > now / 1000) {
      return { blocked: true, retryAfter: Math.ceil(blockedUntilRedis - now / 1000) };
    }
  }

  const blockUntil = _circuitBlocks.get(identifier);
  if (blockUntil && blockUntil > now) {
    return { blocked: true, retryAfter: Math.ceil((blockUntil - now) / 1000) };
  }

  // Track request in sliding window
  const windowKey = `cb_window:${identifier}`;
  const redisWindowCount = await redisIncrExpiry(windowKey, CB_WINDOW_SECS);
  if (redisWindowCount !== null) {
    if (redisWindowCount > CB_MAX_REQUESTS) {
      // Block this identifier
      const blockSecs = CB_BLOCK_SECS;
      await redisSetNX(blockKey, Math.ceil(now / 1000) + blockSecs, blockSecs);
      logger.warn(`Circuit breaker triggered for ${identifier}: ${redisWindowCount} requests in ${CB_WINDOW_SECS}s`);
      return { blocked: true, retryAfter: blockSecs };
    }
    return { blocked: false };
  }

  // In-memory fallback
  const timestamps = _circuitWindow.get(identifier) || [];
  const windowStart = now - CB_WINDOW_SECS * 1000;
  const fresh = timestamps.filter((t) => t > windowStart);
  fresh.push(now);
  _circuitWindow.set(identifier, fresh);

  if (fresh.length > CB_MAX_REQUESTS) {
    const blockUntilMs = now + CB_BLOCK_SECS * 1000;
    _circuitBlocks.set(identifier, blockUntilMs);
    logger.warn(`Circuit breaker triggered for ${identifier}: ${fresh.length} requests in ${CB_WINDOW_SECS}s`);
    return { blocked: true, retryAfter: CB_BLOCK_SECS };
  }

  return { blocked: false };
}

// ── Spend tracking (counters for estimator) ────────────────────────────────
export async function recordUsage({ userId, ip, endpoint, estimatedTokens = 0 }) {
  const today = new Date().toISOString().slice(0, 10);
  const key = `spend:${today}`;
  const field = userId ? `user:${userId}` : `ip:${ip}`;

  if (isRedisAvailable()) {
    try {
      const r = getRedis();
      await r.hincrby(key, `${field}:count`, 1);
      await r.hincrby(key, `${field}:tokens`, estimatedTokens);
      await r.hincrby(key, `global:count`, 1);
      await r.hincrby(key, `global:tokens`, estimatedTokens);
      await r.hincrby(key, `endpoint:${endpoint}:count`, 1);
      await r.expire(key, 86400 * 8); // keep 8 days
      return;
    } catch { /* fall through */ }
  }

  // In-memory (best-effort, resets on restart)
  const countsKey = `${key}:${field}:count`;
  const tokensKey = `${key}:${field}:tokens`;
  _dailyCounts.set(countsKey, {
    count: (_dailyCounts.get(countsKey)?.count || 0) + 1,
    resetAt: Date.now() + 86400000,
  });
  _dailyCounts.set(tokensKey, {
    count: (_dailyCounts.get(tokensKey)?.count || 0) + estimatedTokens,
    resetAt: Date.now() + 86400000,
  });
}

// ── Middleware factories ───────────────────────────────────────────────────

/**
 * Enforce per-user/IP daily generation limit.
 * Must be placed AFTER gateAI (which sets req.user or returns 401).
 */
export function dailyGenLimit(limitOverride) {
  const limit = limitOverride || DAILY_GEN_LIMIT;
  return async (req, res, next) => {
    const clientId = _clientKey(req);
    const result = await _checkDailyLimit('gen', clientId, limit);

    // Set headers so frontend can show remaining count
    res.setHeader('X-Daily-Limit', String(limit));
    res.setHeader('X-Daily-Used', String(result.count));
    res.setHeader('X-Daily-Remaining', String(Math.max(0, limit - result.count)));
    res.setHeader('X-Daily-Resets-At', String(result.resetsAt));

    if (!result.allowed) {
      logger.warn(`Daily generation limit exceeded for ${clientId}: ${result.count}/${limit}`);
      return res.status(429).json({
        success: false,
        error: {
          code: 'DAILY_LIMIT_EXCEEDED',
          message: `Daily generation limit of ${limit} reached. Resets at midnight UTC.`,
          limit,
          used: result.count,
          resetsAt: new Date(result.resetsAt).toISOString(),
        },
      });
    }

    next();
  };
}

/**
 * Enforce daily chat limit.
 */
export function dailyChatLimit(limitOverride) {
  const limit = limitOverride || DAILY_CHAT_LIMIT;
  return async (req, res, next) => {
    const clientId = _clientKey(req);
    const result = await _checkDailyLimit('chat', clientId, limit);

    res.setHeader('X-Daily-Limit', String(limit));
    res.setHeader('X-Daily-Used', String(result.count));
    res.setHeader('X-Daily-Remaining', String(Math.max(0, limit - result.count)));

    if (!result.allowed) {
      return res.status(429).json({
        success: false,
        error: {
          code: 'DAILY_CHAT_LIMIT_EXCEEDED',
          message: `Daily chat limit of ${limit} reached.`,
          limit,
          used: result.count,
        },
      });
    }

    next();
  };
}

/**
 * Circuit breaker middleware — blocks clients sending too many requests.
 */
export function circuitBreaker() {
  return async (req, res, next) => {
    const clientId = _clientKey(req);
    const result = await _checkCircuitBreaker(clientId);

    if (result.blocked) {
      res.setHeader('Retry-After', String(result.retryAfter));
      res.setHeader('X-Circuit-Breaker', 'active');
      logger.warn(`Circuit breaker block for ${clientId}: retry after ${result.retryAfter}s`);
      return res.status(429).json({
        success: false,
        error: {
          code: 'CIRCUIT_BREAKER',
          message: `Too many requests. Temporarily blocked. Try again in ${result.retryAfter} seconds.`,
          retryAfter: result.retryAfter,
        },
      });
    }

    next();
  };
}

/**
 * Enforce per-request max_tokens hard cap.
 * Mutates req.body.max_tokens if present, or adds a default cap.
 */
export function tokenCap(endpointType = 'generation') {
  const caps = {
    generation: MAX_TOKENS_GENERATION,
    chat: MAX_TOKENS_CHAT,
    vision: MAX_TOKENS_VISION,
  };
  const cap = caps[endpointType] || MAX_TOKENS_GENERATION;

  return (req, res, next) => {
    // Clamp any user-supplied max_tokens to the hard cap
    if (req.body && typeof req.body.max_tokens === 'number') {
      req.body.max_tokens = Math.min(req.body.max_tokens, cap);
    }
    // Always inject the cap so downstream code can read it
    if (req.body) {
      req.body._max_tokens_cap = cap;
    }
    next();
  };
}

/**
 * Combined AI cost protection middleware stack.
 * Apply to all expensive AI routes (generate, chat, vision).
 */
export function aiCostGuard(endpointType = 'generation') {
  return [
    circuitBreaker(),
    endpointType === 'generation'
      ? dailyGenLimit()
      : endpointType === 'chat'
        ? dailyChatLimit()
        : dailyGenLimit(DAILY_VISION_LIMIT),
    tokenCap(endpointType),
  ];
}

export default {
  dailyGenLimit,
  dailyChatLimit,
  circuitBreaker,
  tokenCap,
  aiCostGuard,
  recordUsage,
  MAX_TOKENS_GENERATION,
  MAX_TOKENS_CHAT,
  MAX_TOKENS_VISION,
};
