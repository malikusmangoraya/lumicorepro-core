/**
 * AI Spend Estimator — daily/weekly estimated token use + projected cost
 * ----------------------------------------------------------------------
 * Reads usage counters recorded by usageGuard.recordUsage() and aggregates:
 *   - daily count & tokens per endpoint
 *   - weekly total
 *   - estimated cost at configurable per-1K-token price (default worst-case)
 * Pure local counters — NO paid analytics required. Configurable entirely via env.
 */
import os from 'os';
import { getRedis, isRedisAvailable } from '../cache/redis.client.js';

// ── Cost model (free-tier friendly default = worst-case premium price) ─────
// Price per 1K tokens (input+output blended). Defaults assume premium models;
// lower it with TOKEN_COST_PER_1K to match your provider's real rate.
const COST_PER_1K_TOKENS = parseFloat(process.env.AI_TOKEN_COST_PER_1K || '0.02');
// Average tokens consumed per generation (input prompt + output code)
const AVG_TOKENS_PER_GENERATION = parseInt(process.env.AI_AVG_TOKENS_GENERATION || '18000', 10);
const AVG_TOKENS_PER_CHAT = parseInt(process.env.AI_AVG_TOKENS_CHAT || '2500', 10);
const AVG_TOKENS_PER_VISION = parseInt(process.env.AI_AVG_TOKENS_VISION || '1200', 10);

const DAILY_LIMIT = parseInt(process.env.AI_DAILY_GEN_LIMIT, 10) || 3;

// Expose config to the widget so it can render the same numbers
export function getEstimatorConfig() {
  return {
    dailyGenLimit: DAILY_LIMIT,
    costPer1kTokens: COST_PER_1K_TOKENS,
    avgTokensPerGeneration: AVG_TOKENS_PER_GENERATION,
    avgTokensPerChat: AVG_TOKENS_PER_CHAT,
    avgTokensPerVision: AVG_TOKENS_PER_VISION,
  };
}

function _daysAgo(n) {
  const d = new Date();
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}

const ENDPOINT_TOKENS = {
  generation: AVG_TOKENS_PER_GENERATION,
  chat: AVG_TOKENS_PER_CHAT,
  vision: AVG_TOKENS_PER_VISION,
};

/**
 * Estimate token usage for a single request without a real counter.
 * Used when recording happens out-of-band or Redis is down.
 */
export function estimateTokensForRequest(endpoint) {
  return ENDPOINT_TOKENS[endpoint] || AVG_TOKENS_PER_GENERATION;
}

/**
 * Aggregate spend for the last N days.
 * Returns per-day + totals.
 */
export async function getSpendSummary(days = 8) {
  const today = new Date().toISOString().slice(0, 10);
  const dayKeys = [];
  for (let i = days - 1; i >= 0; i -= 1) {
    dayKeys.push({ key: `spend:${_daysAgo(i)}`, date: _daysAgo(i), isToday: i === 0 });
  }

  const daily = [];
  let totalCount = 0;
  let totalTokens = 0;
  const byEndpoint = {};
  const byUser = {};

  if (isRedisAvailable()) {
    try {
      const r = getRedis();
      const pipe = r.pipeline();
      for (const { key } of dayKeys) pipe.hgetall(key);
      const results = await pipe.exec();
      for (let i = 0; i < dayKeys.length; i += 1) {
        const fields = results[i]?.[1] || {};
        const entry = {
          date: dayKeys[i].date,
          isToday: dayKeys[i].isToday,
          count: parseInt(fields['global:count'] || 0, 10),
          tokens: parseInt(fields['global:tokens'] || 0, 10),
        };
        for (const [field, val] of Object.entries(fields)) {
          if (field.startsWith('endpoint:')) {
            const ep = field.replace('endpoint:', '').replace(':count', '');
            byEndpoint[ep] = (byEndpoint[ep] || 0) + parseInt(val, 10);
          }
          if (field.startsWith('user:') && field.endsWith(':tokens')) {
            const uid = field.replace('user:', '').replace(':tokens', '');
            byUser[uid] = (byUser[uid] || 0) + parseInt(val, 10);
          }
        }
        totalCount += entry.count;
        totalTokens += entry.tokens;
        daily.push(entry);
      }
    } catch {
      /* fall through to in-memory */
    }
  }

  const estimatedCost = totalTokens * (COST_PER_1K_TOKENS / 1000);

  return {
    generatedAt: new Date().toISOString(),
    source: isRedisAvailable() ? 'redis' : 'in-memory',
    daily,
    totals: {
      requests: totalCount,
      estimatedTokens: totalTokens,
      estimatedCost,
    },
    byEndpoint,
    topUsers: Object.entries(byUser)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([userId, tokens]) => ({ userId, tokens })),
    config: getEstimatorConfig(),
  };
}

/**
 * Simple weekly flag so the dashboard can flag "projected over budget".
 */
export function getWeeklyProjection() {
  const { totals } = weeklySummaryCache;
  const daysCovered = weeklySummaryCache.daysCovered || 1;
  const projectedTokens = totals.estimatedTokens + Math.round(
    (totals.estimatedTokens / Math.max(daysCovered, 1)) * (7 - Math.min(daysCovered, 7))
  );
  const projectedCost = projectedTokens * (COST_PER_1K_TOKENS / 1000);
  return {
    projectedTokens,
    projectedCost,
    daysCovered: Math.min(daysCovered, 7),
    warning: projectedCost > (parseFloat(process.env.AI_WEEKLY_BUDGET || '0') || Infinity)
      ? 'Projected spend exceeds AI_WEEKLY_BUDGET'
      : null,
  };
}

const weeklySummaryCache = { totals: { estimatedTokens: 0, requests: 0 }, daysCovered: 1 };

export default {
  getSpendSummary,
  getWeeklyProjection,
  getEstimatorConfig,
  estimateTokensForRequest,
};