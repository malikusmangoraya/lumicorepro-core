/**
 * Apex — Plan Usage Guard (Usage Limiter)
 * ---------------------------------------------------------------
 * Middleware-level per-plan caps for AI generations, chat, vision and raw
 * API calls. Sits AFTER `gateAI`/`protect` so `req.user` is populated.
 *
 * - Blocks with HTTP 429 when the monthly plan cap is reached.
 * - Exposes `X-Plan-*` headers so dashboards can render remaining quota.
 * - Fail-open: DB/Redis outage never blocks paid routes.
 */
import { getUsageSummary, resolvePlanLimits, USAGE_METRICS } from '../services/usage.service.js';
import logger from '../utils/logger.js';

const BLOCKED_METRICS = new Set(['ai_generation', 'ai_chat', 'api']);

function _setHeaders(res, summary, metric) {
  if (!summary) return;
  res.setHeader('X-Plan-Name', summary.planName);
  res.setHeader('X-Plan-Limit', String(summary.limits[metric]));
  res.setHeader('X-Plan-Used', String(summary.used[metric]));
  res.setHeader('X-Plan-Remaining', String(summary.remaining[metric]));
  res.setHeader('X-Plan-Resets-At', summary.resetsAt);
}

/**
 * Enforce the monthly cap for a metered metric.
 * `metric` ∈ USAGE_METRICS keys (ai_generation | ai_chat | api).
 *
 * Usage is ONLY incremented on success — call `recordPlanUsage` from the
 * route handler after the work completes.
 */
export function enforcePlanLimit(metric) {
  if (!USAGE_METRICS[metric]) {
    throw new Error(
      `Unknown usage metric: ${metric}. Expected one of ${Object.keys(USAGE_METRICS).join(', ')}`
    );
  }
  return async (req, res, next) => {
    // Service-to-service (x-api-key) calls bypass per-user plan caps.
    if (!req.user?.id) return next();

    try {
      const summary = await getUsageSummary(req.user.id);
      _setHeaders(res, summary, metric);

      const limit = summary.limits[metric];
      const used = summary.used[metric];
      if (limit > 0 && used >= limit) {
        logger.warn(`Plan limit exceeded for user ${req.user.id}: ${metric} ${used}/${limit}`);
        return res.status(429).json({
          success: false,
          error: {
            code: 'PLAN_LIMIT_EXCEEDED',
            message: `Your ${summary.planName} plan's monthly ${USAGE_METRICS[metric].label.toLowerCase()} limit (${limit}) has been reached. Upgrade your plan to continue.`,
            metric,
            limit,
            used,
            resetsAt: summary.resetsAt,
          },
        });
      }
    } catch (err) {
      // Fail-open — quota cannot block revenue paths.
      logger.warn(`enforcePlanLimit skipped for ${metric}: ${err.message}`);
    }
    next();
  };
}

/**
 * Non-blocking request meter for a metric — records usage then proceeds.
 * Used for the raw `api` metric on all /api routes.
 */
export function meterPlanUsage(metric) {
  return (req, res, next) => {
    if (req.user?.id && USAGE_METRICS[metric]) {
      // Defer so it never blocks; lazy import avoids require cycles.
      import('../services/usage.service.js')
        .then((m) => m.recordPlanUsage(req.user.id, metric, 1))
        .catch(() => {});
    }
    next();
  };
}

export default { enforcePlanLimit, meterPlanUsage, BLOCKED_METRICS };
