/**
 * Usage Limiter — per-plan monthly metering and enforcement (fail-open).
 * Attach per route: router.get('/', enforceLimit('api', { limit: 1000 }), handler);
 * Individual metrics are configurable via the USAGE_LIMITS env (JSON).
 */
let limitConfig = {};
try {
  limitConfig = process.env.USAGE_LIMITS ? JSON.parse(process.env.USAGE_LIMITS) : {};
} catch (_) {
  /* invalid env, use defaults */
}

const defaultLimits = Object.assign(
  {
    api: 1000,
    ai_generation: 50,
    ai_chat: 200,
    uploads: 100,
    exports: 50,
  },
  limitConfig && typeof limitConfig === 'object' ? limitConfig : {}
);

const monthKey = () => {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
};

const counters = new Map();

const usageOf = (metric) => counters.get(`${monthKey()}:${metric}`) || 0;

const bump = (metric, n = 1) => {
  const key = `${monthKey()}:${metric}`;
  const next = usageOf(metric) + n;
  counters.set(key, next);
  return next;
};

const planMultiplier = (user) => {
  const map = { free: 1, starter: 1, pro: 5, growth: 20, scale: 100, enterprise: 1000 };
  return map[(user && (user.plan || user.role)) || 'free'] || 1;
};

const enforceLimit =
  (metric, options = {}) =>
  (req, res, next) => {
    try {
      const limit = (options.limit || defaultLimits[metric] || 1000) * planMultiplier(req.user);
      if (usageOf(metric) >= limit) {
        return res.status(429).json({
          success: false,
          code: 'PLAN_LIMIT_EXCEEDED',
          message: `Monthly ${metric} limit of ${limit} reached. Upgrade your plan to continue.`,
        });
      }
      res.setHeader('X-Plan-Limit', limit);
      res.setHeader('X-Plan-Usage', usageOf(metric));
      res.once('finish', () => {
        if (res.statusCode < 500) bump(metric, 1);
      });
      next();
    } catch (err) {
      next();
    }
  };

const meter = (metric) => (req, res, next) => {
  res.once('finish', () => {
    if (res.statusCode < 500) {
      try {
        bump(metric, 1);
      } catch (_) {
        /* noop */
      }
    }
  });
  next();
};

module.exports = { enforceLimit, meter, defaultLimits, counters };
