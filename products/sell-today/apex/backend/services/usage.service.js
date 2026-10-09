/**
 * Apex — Plan Usage Service
 * ---------------------------------------------------------------
 * Per-plan monthly usage limits (Usage Limiter middleware backing).
 *
 * Limits are derived from the user's active subscription → Plan. Because
 * Plan.features is a prieced-card string array, numeric caps come from the
 * seeded `creditsGrant` column (credits/month). Free accounts get a default
 * allowance. All enforcement is SERVER-ONLY.
 *
 * Storage: Redis counters (month-keyed, auto-expire) with in-memory fallback.
 * Never throws — API callers fail open when the store is unavailable.
 */
import { getRedis, isRedisAvailable } from './cache/redis.client.js';
import logger from '../utils/logger.js';

// Metrics the plan system can meter.
export const USAGE_METRICS = {
  ai_generation: { label: 'AI Generations', multiplier: 1 },
  ai_chat: { label: 'AI Chat Messages', multiplier: 5 },
  api: { label: 'API Calls', multiplier: 1000 },
};

// Free-tier defaults — generous enough to demo, capped to push paid upgrades.
const DEFAULT_MONTHLY_LIMITS = {
  ai_generation: 10,
  ai_chat: 50,
  api: 1000,
};

const COUNTER_TTL_SECS = 45 * 24 * 60 * 60; // 45 days — covers a month + grace
const MEMORY_TTL_MS = COUNTER_TTL_SECS * 1000;

// In-memory fallback: key → { count, resetAt }
const _memCounts = new Map();

// Clean up stale in-memory counters every 5 minutes.
setInterval(
  () => {
    const now = Date.now();
    for (const [key, entry] of _memCounts) {
      if (entry.resetAt < now) _memCounts.delete(key);
    }
  },
  5 * 60 * 1000
).unref();

/** Current billing month key — `YYYY-M` (1-12, no zero padding). */
export function currentMonthKey(date = new Date()) {
  return `${date.getUTCFullYear()}-${date.getUTCMonth() + 1}`;
}

/** Next month boundary (ms) — used for counter TTL + resetsAt header. */
export function nextMonthReset(date = new Date()) {
  const reset = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 1));
  return reset.getTime();
}

function _counterKey(metric, userId, monthKey) {
  return `planusage:${metric}:${userId}:${monthKey}`;
}

async function _getCounter(metric, userId, monthKey) {
  const key = _counterKey(metric, userId, monthKey);
  if (isRedisAvailable()) {
    try {
      const val = await getRedis().get(key);
      return val !== null ? parseInt(val, 10) : 0;
    } catch {
      /* fall through to memory */
    }
  }
  const entry = _memCounts.get(key);
  return entry && entry.resetAt > Date.now() ? entry.count : 0;
}

async function _incrementCounter(metric, userId, monthKey, delta = 1) {
  const key = _counterKey(metric, userId, monthKey);
  if (isRedisAvailable()) {
    try {
      const r = getRedis();
      const val = await r.incrby(key, delta);
      if (val === delta) await r.expire(key, COUNTER_TTL_SECS);
      return val;
    } catch {
      /* fall through to memory */
    }
  }
  let entry = _memCounts.get(key);
  if (!entry || entry.resetAt < Date.now()) {
    entry = { count: 0, resetAt: Date.now() + MEMORY_TTL_MS };
  }
  entry.count += delta;
  _memCounts.set(key, entry);
  return entry.count;
}

/**
 * Resolve the active subscription + plan for a user. Returns
 * `{ sub, plan, planName }` or defaults when no active subscription exists
 * (or the DB is offline). Fail-open by design.
 */
export async function resolvePlanForUser(userId) {
  try {
    // Import the model registry (models/index.js) so the Subscription→Plan
    // association registered there is available for the eager-load below.
    const { Subscription, Plan } = await import('../models/index.js');
    const sub = await Subscription.findOne({
      where: { user_id: userId, status: ['active', 'trialing', 'past_due'] },
      order: [['createdAt', 'DESC']],
      include: [{ model: Plan, as: 'plan', required: false }],
    });
    if (sub) {
      return { sub, plan: sub.plan || null, planName: sub.planName || 'Pro' };
    }
  } catch (err) {
    logger.warn(`resolvePlanForUser failed (offline DB?): ${err.message}`);
  }
  return { sub: null, plan: null, planName: 'Free' };
}

/**
 * Resolve numeric monthly limits for a user's plan.
 * Paid plans scale from creditsGrant (credits = AI generations / mo).
 */
export function resolvePlanLimits(plan, fallback = DEFAULT_MONTHLY_LIMITS) {
  if (!plan) return { ...fallback };
  const credits = parseFloat(plan.creditsGrant);
  if (!credits || credits <= 0) return { ...fallback };
  return {
    ai_generation: Math.max(1, Math.round(credits)),
    ai_chat: Math.max(1, Math.round(credits * USAGE_METRICS.ai_chat.multiplier)),
    api: Math.max(1, Math.round(credits * USAGE_METRICS.api.multiplier)),
  };
}

/**
 * Snapshot of the current user's usage vs their plan for the month.
 * Returns `{ planName, resetsAt, limits, used, remaining }`.
 */
export async function getUsageSummary(userId) {
  const { plan, planName } = await resolvePlanForUser(userId);
  const limits = resolvePlanLimits(plan);
  const monthKey = currentMonthKey();
  const used = {};
  const remaining = {};
  for (const metric of Object.keys(USAGE_METRICS)) {
    const count = await _getCounter(metric, userId, monthKey);
    used[metric] = count;
    remaining[metric] = Math.max(0, limits[metric] - count);
  }
  return {
    planName,
    monthKey,
    resetsAt: new Date(nextMonthReset()).toISOString(),
    limits,
    used,
    remaining,
  };
}

/**
 * Record usage against a user's plan (best-effort, never blocks a response).
 * Also writes an AnalyticsEvent row so dashboards can chart history.
 */
export async function recordPlanUsage(userId, metric, delta = 1) {
  if (!userId) return;
  if (!USAGE_METRICS[metric]) return;
  const monthKey = currentMonthKey();
  try {
    await _incrementCounter(metric, userId, monthKey, delta);
    const { AnalyticsEvent } = await import('../models/index.js');
    await AnalyticsEvent.create({
      user_id: userId,
      eventName: `plan_usage.${metric}`,
      payload: { metric, delta, monthKey, at: new Date().toISOString() },
    }).catch(() => {});
  } catch (err) {
    logger.warn(`recordPlanUsage failed: ${err.message}`);
  }
}

/**
 * Monthly usage history for the last N billing months (for charts).
 * Returns ascending array of `{ month, ai_generation, ai_chat, api }`.
 */
export async function getUsageHistory(userId, months = 6) {
  const out = [];
  const now = new Date();
  for (let i = months - 1; i >= 0; i -= 1) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - i, 1));
    const monthKey = currentMonthKey(d);
    const row = { month: monthKey };
    for (const metric of Object.keys(USAGE_METRICS)) {
      row[metric] = await _getCounter(metric, userId, monthKey);
    }
    out.push(row);
  }
  return out;
}

export default {
  USAGE_METRICS,
  DEFAULT_MONTHLY_LIMITS,
  currentMonthKey,
  nextMonthReset,
  resolvePlanForUser,
  resolvePlanLimits,
  getUsageSummary,
  recordPlanUsage,
  getUsageHistory,
};
