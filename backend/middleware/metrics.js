/**
 * HTTP metrics middleware — records request count + latency per matched route.
 *
 * Uses the route pattern (req.route.path) rather than the raw URL so series
 * stay bounded (see metrics.js cardinality policy). Unmatched requests are
 * bucketed as `unmatched` to keep the aggregate count honest without naming
 * arbitrary attacker-supplied paths.
 */
import { httpRequestsTotal, httpRequestDuration } from '../services/observability/metrics.js';

function routeLabel(req) {
  if (req.route?.path) return `${req.baseUrl || ''}${req.route.path}`;
  return 'unmatched';
}

export function metricsMiddleware(req, res, next) {
  const startedAt = process.hrtime.bigint();
  res.on('finish', () => {
    const durationSeconds = Number(process.hrtime.bigint() - startedAt) / 1e9;
    const route = routeLabel(req);
    httpRequestsTotal().inc({ method: req.method, route, status: String(res.statusCode) });
    httpRequestDuration().observe({ method: req.method, route }, durationSeconds);
  });
  next();
}

export default metricsMiddleware;
