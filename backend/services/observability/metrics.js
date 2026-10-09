/**
 * Observability — dependency-free Prometheus metrics registry.
 * -------------------------------------------------------------
 * No prom-client dependency: the exposition format is plain text and the
 * primitives (counters, histograms with buckets) are small. Exposed at
 * GET /api/metrics for Prometheus/VictoriaMetrics/Alertmanager scraping.
 *
 * Cardinality policy: label values for `route` are the matched route
 * pattern (e.g. `/api/ai/generate`), NEVER the raw URL, so request params
 * cannot explode the series count.
 */

const HELP_RE = /[\\n]/g;

/** Prometheus label values MUST be quoted and escaped. */
function formatLabelValue(value) {
  return String(value)
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n');
}

/** "a=1,b=2" -> ['a="1"', 'b="2"'] (as a label-value string) */
function renderLabels(key) {
  if (!key) return '';
  return key
    .split(',')
    .map((pair) => {
      const idx = pair.indexOf('=');
      const name = pair.slice(0, idx);
      const value = pair.slice(idx + 1);
      return `${name}="${formatLabelValue(value)}"`;
    })
    .join(',');
}

class Counter {
  constructor(name, help, labelNames = []) {
    this.name = name;
    this.help = help;
    this.labelNames = labelNames;
    this.values = new Map(); // "a=1,b=2" -> number
  }

  key(labels = {}) {
    if (!this.labelNames.length) return '';
    return this.labelNames.map((l) => `${l}=${String(labels[l] ?? '')}`).join(',');
  }

  inc(labels = {}, value = 1) {
    const k = this.key(labels);
    this.values.set(k, (this.values.get(k) || 0) + value);
  }

  snapshot() {
    return [...this.values.entries()].map(([k, v]) => {
      const out = {};
      if (k) for (const pair of k.split(',')) {
        const [l, val] = pair.split('=');
        out[l] = val;
      }
      return { labels: out, value: v };
    });
  }
}

class Histogram {
  constructor(name, help, buckets, labelNames = []) {
    this.name = name;
    this.help = help;
    this.buckets = [...buckets].sort((a, b) => a - b);
    this.labelNames = labelNames;
    // "a=1,b=2" -> { counts: number[], sum, count }
    this.series = new Map();
  }

  key(labels = {}) {
    if (!this.labelNames.length) return '';
    return this.labelNames.map((l) => `${l}=${String(labels[l] ?? '')}`).join(',');
  }

  observe(labels = {}, value) {
    const k = this.key(labels);
    let s = this.series.get(k);
    if (!s) {
      s = { counts: new Array(this.buckets.length).fill(0), sum: 0, count: 0 };
      this.series.set(k, s);
    }
    for (let i = 0; i < this.buckets.length; i += 1) {
      if (value <= this.buckets[i]) {
        s.counts[i] += 1;
        break;
      }
    }
    s.sum += value;
    s.count += 1;
  }

  /** Quantile estimate from the bucket Cumulative Distribution Function (prometheus_quantile-style). */
  quantile(labels = {}, q) {
    const s = this.series.get(this.key(labels));
    if (!s || s.count === 0) return null;
    // cumulative counts at each bucket
    let cumulative = 0;
    const cumulativeCounts = this.buckets.map((_, i) => (cumulative += s.counts[i]));
    const target = s.count * q;
    for (let i = 0; i < this.buckets.length; i += 1) {
      if (cumulativeCounts[i] >= target) {
        const lower = i === 0 ? 0 : this.buckets[i - 1];
        const span = this.buckets[i] - lower || 1;
        const frac = (target - (i === 0 ? 0 : cumulativeCounts[i - 1])) / (s.counts[i] || 1);
        return lower + Math.min(Math.max(frac, 0), 1) * span;
      }
    }
    return this.buckets[this.buckets.length - 1];
  }

  snapshot() {
    return [...this.series.entries()].map(([k, s]) => {
      const labels = {};
      if (k) for (const pair of k.split(',')) {
        const [l, val] = pair.split('=');
        labels[l] = val;
      }
      return { labels, count: s.count, sum: s.sum, counts: [...s.counts] };
    });
  }
}

const registry = {
  counters: new Map(),
  histograms: new Map(),
};

export function counter(name, help, labelNames = []) {
  if (!registry.counters.has(name)) registry.counters.set(name, new Counter(name, help, labelNames));
  return registry.counters.get(name);
}

export function histogram(name, help, buckets, labelNames = []) {
  if (!registry.histograms.has(name)) registry.histograms.set(name, new Histogram(name, help, buckets, labelNames));
  return registry.histograms.get(name);
}

// ── Default application metrics ────────────────────────────────────────────
// Accessors (not constants): the registry can be reset in tests, and a
// captured instance would then write into a detached object that never shows
// up in the exposition.
const DEFAULTS = {
  http_requests_total: () => counter('http_requests_total', 'Total HTTP requests processed by the API', ['method', 'route', 'status']),
  http_request_duration_seconds: () => histogram('http_request_duration_seconds', 'HTTP request latency in seconds', [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10], ['method', 'route']),
  ai_generation_total: () => counter('ai_generation_total', 'AI generation attempts by outcome', ['status']),
  ai_generation_duration_seconds: () => histogram('ai_generation_duration_seconds', 'End-to-end AI generation latency in seconds', [1, 5, 15, 30, 60, 120, 240, 480]),
  ai_spend_estimated_usd_total: () => counter('ai_spend_estimated_usd_total', 'Estimated AI provider spend in USD (from the per-run ledger)'),
  ai_semantic_cache_total: () => counter('ai_semantic_cache_total', 'Semantic cache lookups by result', ['result']),
};

export const httpRequestsTotal = DEFAULTS.http_requests_total;
export const httpRequestDuration = DEFAULTS.http_request_duration_seconds;
export const aiGenerationsTotal = DEFAULTS.ai_generation_total;
export const aiGenerationDuration = DEFAULTS.ai_generation_duration_seconds;
export const aiSpendUsd = DEFAULTS.ai_spend_estimated_usd_total;
export const aiCacheHitsTotal = DEFAULTS.ai_semantic_cache_total;

// Register defaults at import time so a fresh process exposes them.
for (const register of Object.values(DEFAULTS)) register();

/** Render all metrics in the Prometheus text exposition format (v0.0.4). */
export function renderPrometheus() {
  const lines = [];
  for (const c of registry.counters.values()) {
    lines.push(`# HELP ${c.name} ${c.help.replace(HELP_RE, ' ')}`);
    lines.push(`# TYPE ${c.name} counter`);
    if (c.values.size === 0) lines.push(`${c.name} 0`);
    for (const [k, v] of c.values) {
      const lbl = renderLabels(k);
      lines.push(`${c.name}${lbl ? `{${lbl}}` : ''} ${v}`);
    }
  }
  for (const h of registry.histograms.values()) {
    lines.push(`# HELP ${h.name} ${h.help.replace(HELP_RE, ' ')}`);
    lines.push(`# TYPE ${h.name} histogram`);
    for (const [k, s] of h.series) {
      const base = renderLabels(k);
      const withLe = (le) => (base ? `${base},le="${le}"` : `le="${le}"`);
      let cumulative = 0;
      h.buckets.forEach((b, i) => {
        cumulative += s.counts[i];
        lines.push(`${h.name}_bucket{${withLe(b)}} ${cumulative}`);
      });
      lines.push(`${h.name}_bucket{${withLe('+Inf')}} ${s.count}`);
      lines.push(`${h.name}_sum${base ? `{${base}}` : ''} ${s.sum}`);
      lines.push(`${h.name}_count${base ? `{${base}}` : ''} ${s.count}`);
    }
  }
  return `${lines.join('\n')}\n`;
}

/** JSON snapshot (used by SLO math and tests). */
export function snapshot() {
  return {
    counters: Object.fromEntries([...registry.counters.entries()].map(([n, c]) => [n, c.snapshot()])),
    histograms: Object.fromEntries([...registry.histograms.entries()].map(([n, h]) => [n, h.snapshot()])),
  };
}

export function resetForTests() {
  registry.counters.clear();
  registry.histograms.clear();
  // Re-register defaults so the exported accessors keep pointing at live
  // objects after a reset (an empty exposition would hide real bugs).
  for (const register of Object.values(DEFAULTS)) register();
}

export default { counter, histogram, renderPrometheus, snapshot, resetForTests };
