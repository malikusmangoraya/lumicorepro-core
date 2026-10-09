/**
 * AI Spend Ledger + Hard Budget Caps.
 * ------------------------------------
 * recordRun()     → one ledger row per billable AI run (per-user/per-run
 *                   accounting the estimator alone cannot provide).
 * checkBudget()   → hard per-user daily spend cap. When the cap would be
 *                   crossed the caller must refuse the run BEFORE it starts.
 *                   Counters live in Redis (multi-worker safe) with an
 *                   in-memory fallback.
 * Alerts: the first time a user crosses their budget a single warn is
 * recorded (logger + audit trail) so ops sees it without alert storms.
 */
import { Op } from 'sequelize';
import { getRedis, isRedisAvailable } from '../cache/redis.client.js';
import logger from '../../utils/logger.js';

const DAILY_BUDGET_USD = parseFloat(process.env.AI_DAILY_BUDGET_USD || '5');
const WEEKLY_BUDGET_USD = parseFloat(process.env.AI_WEEKLY_BUDGET_USD || '0'); // 0 = disabled
const COST_PER_1K_TOKENS = parseFloat(process.env.AI_TOKEN_COST_PER_1K || '0.02');

const _memorySpend = new Map(); // key -> usd (fallback)

function dayKey(userId) {
  return `budget:user:${userId}:${new Date().toISOString().slice(0, 10)}`;
}

export function estimateCostUsd(tokens) {
  return (Number(tokens) || 0) * (COST_PER_1K_TOKENS / 1000);
}

async function addSpend(userId, costUsd) {
  if (!userId) return null;
  if (isRedisAvailable()) {
    try {
      const r = getRedis();
      const key = dayKey(userId);
      const total = await r.incrbyfloat(key, costUsd);
      await r.expire(key, 86400 * 2);
      return Number(total);
    } catch { /* fall through */ }
  }
  const key = dayKey(userId);
  const total = (_memorySpend.get(key) || 0) + costUsd;
  _memorySpend.set(key, total);
  return total;
}

async function getSpend(userId) {
  if (!userId) return 0;
  if (isRedisAvailable()) {
    try {
      const val = await getRedis().get(dayKey(userId));
      if (val !== null) return Number(val);
    } catch { /* fall through */ }
  }
  return _memorySpend.get(dayKey(userId)) || 0;
}

/** Check whether a run costing `projectedCostUsd` is allowed under the caps. */
export async function checkBudget(userId, projectedCostUsd) {
  // Anonymous traffic cannot be attributed to a budget owner; the rate limiter,
  // daily generation caps and token caps still bound that traffic.
  if (!userId) {
    return {
      allowed: true,
      scoped: false,
      spentTodayUsd: 0,
      budgetUsd: DAILY_BUDGET_USD,
      remainingUsd: null,
    };
  }
  const spent = await getSpend(userId);
  const budget = DAILY_BUDGET_USD;
  const allowed = spent + Math.max(0, projectedCostUsd) <= budget;
  return {
    allowed,
    spentTodayUsd: Number(spent.toFixed(6)),
    budgetUsd: budget,
    remainingUsd: Number(Math.max(0, budget - spent).toFixed(6)),
  };
}

/** Record a completed billable run and (once) alert when the budget is crossed. */
export async function recordRun({
  userId, orgId = null, runId = null, ip = null, endpoint = 'generation',
  provider = null, model = null, tokens = 0, costUsd = null, ledgerModel = null,
} = {}) {
  const cost = costUsd != null ? Number(costUsd) : estimateCostUsd(tokens);
  const Ledger = ledgerModel || (await import('../../models/AiSpendLedger.js')).default;

  let persisted = false;
  try {
    await Ledger.create({
      run_id: runId,
      user_id: userId ?? null,
      org_id: orgId ?? null,
      ip,
      endpoint,
      provider,
      model,
      estimated_tokens: Math.round(tokens) || 0,
      estimated_cost_usd: cost,
      kind: 'run',
    });
    persisted = true;
  } catch (err) {
    // Ledger writes must never break a generation response.
    logger.warn(`Spend ledger write skipped: ${err.message}`);
  }

  const totalAfter = await addSpend(userId, cost);
  if (totalAfter != null && totalAfter > DAILY_BUDGET_USD) {
    const alertKey = `budget_alerted:${userId}:${new Date().toISOString().slice(0, 10)}`;
    let shouldAlert = true;
    if (isRedisAvailable()) {
      try {
        shouldAlert = (await getRedis().set(alertKey, '1', 'EX', 86400, 'NX')) === 'OK';
      } catch { /* alert degenerates to warn-per-run */ }
    }
    if (shouldAlert) {
      logger.warn(`AI BUDGET EXCEEDED: user ${userId} spent $${totalAfter.toFixed(4)} today (cap $${DAILY_BUDGET_USD})`);
      try {
        const { recordAudit } = await import('../../middleware/audit.js');
        await recordAudit(
          { headers: {}, socket: {} },
          { action: 'ai.budget.exceeded', userId, meta: { spent: totalAfter, budget: DAILY_BUDGET_USD, runId } },
        );
      } catch { /* audit is best-effort */ }
    }
  }

  return { cost, persisted };
}

/** Aggregated per-day spend for the admin dashboard (last N days). */
export async function getLedgerSummary(days = 7, ledgerModel = null) {
  const Ledger = ledgerModel || (await import('../../models/AiSpendLedger.js')).default;
  const since = new Date(Date.now() - days * 86400_000);
  try {
    const rows = await Ledger.findAll({
      where: { created_at: { [Op.gt]: since } },
      attributes: ['endpoint', 'estimated_tokens', 'estimated_cost_usd'],
      raw: true,
    });
    const byEndpoint = {};
    let tokens = 0;
    let cost = 0;
    for (const row of rows) {
      const ep = row.endpoint || 'generation';
      byEndpoint[ep] = byEndpoint[ep] || { runs: 0, tokens: 0, cost: 0 };
      byEndpoint[ep].runs += 1;
      byEndpoint[ep].tokens += Number(row.estimated_tokens || 0);
      byEndpoint[ep].cost = Number((byEndpoint[ep].cost + Number(row.estimated_cost_usd || 0)).toFixed(6));
      tokens += Number(row.estimated_tokens || 0);
      cost += Number(row.estimated_cost_usd || 0);
    }
    return {
      days,
      totalRuns: rows.length,
      totalTokens: tokens,
      totalCostUsd: Number(cost.toFixed(6)),
      byEndpoint,
      budget: { dailyUsd: DAILY_BUDGET_USD, weeklyUsd: WEEKLY_BUDGET_USD, costPer1kTokens: COST_PER_1K_TOKENS },
    };
  } catch (err) {
    logger.warn(`Ledger summary unavailable: ${err.message}`);
    return { days, totalRuns: 0, totalTokens: 0, totalCostUsd: 0, byEndpoint: {}, error: err.message };
  }
}

export default { checkBudget, recordRun, getLedgerSummary, estimateCostUsd };
