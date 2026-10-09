/**
 * Observability routes — scraped by Prometheus. No user data is exposed.
 *   GET /api/metrics      → Prometheus text exposition (app + SLO series)
 *   GET /api/metrics/slo  → JSON SLO evaluation (dashboards / CI smoke checks)
 */
import express from 'express';
import { renderPrometheus } from '../services/observability/metrics.js';
import { evaluateSlos, renderSloMetrics } from '../services/observability/slo.js';

const router = express.Router();

router.get('/', (req, res) => {
  res.setHeader('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
  res.send(renderPrometheus() + renderSloMetrics());
});

router.get('/slo', (req, res) => {
  res.json({ success: true, data: evaluateSlos() });
});

export default router;
