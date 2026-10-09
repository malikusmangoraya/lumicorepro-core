/**
 * SLOs + error budgets.
 * ----------------------
 * Targets (env-tunable):
 *   - availability:          99.9% of requests return < 500
 *   - latency:               p95 < 0.5s on the /api surface
 *   - generation success:    >= 95% of AI generations succeed (cache hits count as success)
 *
 * Error budget & burn rate follow the Google SRE model: burn rate = observed
 * bad fraction / allowed bad fraction. Two alert windows:
 *   fast burn  14.4x over ~1h   → page
 *   slow burn   6.0x over ~6h   → ticket
 * Metrics are process-local (multi-replica roll-up happens at the scraper);
 * that is the standard Prometheus pattern and keeps this dependency-free.
 */
import { snapshot } from './metrics.js';

const AVAILABILITY_TARGET = Number(process.env.SLO_AVAILABILITY_TARGET || 0.999);
const P95_LATENCY_TARGET_SECONDS = Number(process.env.SLO_P95_LATENCY_SECONDS || 0.5);
const GENERATION_SUCCESS_TARGET = Number(process.env.SLO_GENERATION_SUCCESS_TARGET || 0.95);
const FAST_BURN_THRESHOLD = Number(process.env.SLO_FAST_BURN || 14.4);
const SLOW_BURN_THRESHOLD = Number(process.env.SLO_SLOW_BURN || 6.0);

function counterValue(snap, name, match = {}) {
  const rows = snap.counters[name] || [];
  return rows
    .filter((r) => Object.entries(match).every(([k, v]) => r.labels[k] === v))
    .reduce((acc, r) => acc + r.value, 0);
}

function histogramQuantile(snap, name, labelMatch, q) {
  const row = (snap.histograms[name] || []).find((r) =>
    Object.entries(labelMatch).every(([k, v]) => r.labels[k] === v)
  );
  if (!row || !row.count) return null;
  let cumulative = 0;
  const BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
  const target = row.count * q;
  for (let i = 0; i < BUCKETS.length; i += 1) {
    cumulative += row.counts[i];
    if (cumulative >= target) return BUCKETS[i];
  }
  return null;
}

/**
 * Full SLO evaluation over the current process-lifetime metrics.
 * Returns JSON used by /api/metrics/slo and CI smoke checks.
 */
export function evaluateSlos() {
  const snap = snapshot();

  const total = counterValue(snap, 'http_requests_total');
  const bad5xx = counterValue(snap, 'http_requests_total', { status: '500' })
    + counterValue(snap, 'http_requests_total', { status: '502' })
    + counterValue(snap, 'http_requests_total', { status: '503' })
    + counterValue(snap, 'http_requests_total', { status: '504' });
  const availability = total > 0 ? 1 - bad5xx / total : null;
  const availabilityBudget = AVAILABILITY_TARGET > 0
    ? (availability == null ? null : (availability - AVAILABILITY_TARGET) / (1 - AVAILABILITY_TARGET))
    : null;
  const availabilityBurn = availability == null || total === 0
    ? null
    : (bad5xx / total) / (1 - AVAILABILITY_TARGET);

  const p95 = histogramQuantile(snap, 'http_request_duration_seconds', {}, 0.95);
  const latencyOk = p95 == null ? null : p95 <= P95_LATENCY_TARGET_SECONDS;

  const genOk = counterValue(snap, 'ai_generation_total', { status: 'success' })
    + counterValue(snap, 'ai_generation_total', { status: 'cache_hit' });
  const genBad = counterValue(snap, 'ai_generation_total', { status: 'failure' });
  const genTotal = genOk + genBad;
  const generationSuccess = genTotal > 0 ? genOk / genTotal : null;
  const generationBurn = generationSuccess == null || genTotal === 0
    ? null
    : (1 - generationSuccess) / (1 - GENERATION_SUCCESS_TARGET);

  const evaluateBurn = (burn) => {
    if (burn == null) return { state: 'no_data' };
    if (burn >= FAST_BURN_THRESHOLD) return { state: 'page', burn: Number(burn.toFixed(2)) };
    if (burn >= SLOW_BURN_THRESHOLD) return { state: 'ticket', burn: Number(burn.toFixed(2)) };
    return { state: 'healthy', burn: Number(burn.toFixed(2)) };
  };

  return {
    generatedAt: new Date().toISOString(),
    window: 'process-lifetime (roll up per-replica at the scraper)',
    targets: {
      availability: AVAILABILITY_TARGET,
      p95LatencySeconds: P95_LATENCY_TARGET_SECONDS,
      generationSuccess: GENERATION_SUCCESS_TARGET,
    },
    slos: [
      {
        name: 'api_availability',
        observed: availability,
        budgetRemainingFraction: availabilityBudget,
        ...evaluateBurn(availabilityBurn),
      },
      {
        name: 'api_latency_p95',
        observedP95Seconds: p95,
        ok: latencyOk,
        state: p95 == null ? 'no_data' : (latencyOk ? 'healthy' : 'ticket'),
      },
      {
        name: 'ai_generation_success',
        observed: generationSuccess,
        ...evaluateBurn(generationBurn),
      },
    ],
  };
}

/** Prometheus exposition for the SLO series (scrape-friendly). */
export function renderSloMetrics() {
  const s = evaluateSlos();
  const lines = ['# HELP slo_burn_rate Current error-budget burn rate per SLO', '# TYPE slo_burn_rate gauge'];
  for (const slo of s.slos) {
    if (typeof slo.burn === 'number') lines.push(`slo_burn_rate{slo="${slo.name}"} ${slo.burn}`);
  }
  return `${lines.join('\n')}\n`;
}

export default { evaluateSlos, renderSloMetrics };
