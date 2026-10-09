import { describe, it, expect, beforeEach } from '@jest/globals';
import {
  counter,
  histogram,
  renderPrometheus,
  snapshot,
  resetForTests,
  httpRequestsTotal,
  aiGenerationsTotal,
} from '../../services/observability/metrics.js';
import { evaluateSlos } from '../../services/observability/slo.js';

describe('metrics registry', () => {
  beforeEach(() => resetForTests());

  it('accumulates counters with label dimensions', () => {
    const c = counter('test_total', 'test counter', ['route', 'status']);
    c.inc({ route: '/a', status: '200' });
    c.inc({ route: '/a', status: '200' });
    c.inc({ route: '/a', status: '500' });
    const rows = c.snapshot();
    expect(rows.find((r) => r.labels.status === '200').value).toBe(2);
    expect(rows.find((r) => r.labels.status === '500').value).toBe(1);
  });

  it('renders cumulative histogram buckets in Prometheus format', () => {
    const h = histogram('test_seconds', 'test histogram', [0.1, 1], ['route']);
    h.observe({ route: '/a' }, 0.05);
    h.observe({ route: '/a' }, 0.5);
    const text = renderPrometheus();
    expect(text).toContain('# TYPE test_seconds histogram');
    expect(text).toContain('test_seconds_bucket{route="/a",le="0.1"} 1');
    expect(text).toContain('test_seconds_bucket{route="/a",le="1"} 2');
    expect(text).toContain('test_seconds_bucket{route="/a",le="+Inf"} 2');
    expect(text).toContain('test_seconds_sum{route="/a"} 0.55');
    expect(text).toContain('test_seconds_count{route="/a"} 2');
  });

  it('snapshot exposes both registries', () => {
    httpRequestsTotal().inc({ method: 'GET', route: '/x', status: '200' });
    aiGenerationsTotal().inc({ status: 'success' });
    const snap = snapshot();
    expect(snap.counters.http_requests_total.length).toBe(1);
    expect(snap.counters.ai_generation_total[0].labels.status).toBe('success');
  });
});

describe('SLO evaluation', () => {
  beforeEach(() => resetForTests());

  it('reports no_data when nothing has been measured', () => {
    const slos = evaluateSlos();
    expect(slos.slos.find((s) => s.name === 'api_availability').state).toBe('no_data');
  });

  it('flags page-level burn when 5xx exceed the budget', () => {
    // 99.9% availability target → 0.1% allowed bad. 5% bad ≈ 50x burn.
    for (let i = 0; i < 95; i += 1) httpRequestsTotal().inc({ method: 'GET', route: '/x', status: '200' });
    for (let i = 0; i < 5; i += 1) httpRequestsTotal().inc({ method: 'GET', route: '/x', status: '500' });
    const availability = evaluateSlos().slos.find((s) => s.name === 'api_availability');
    expect(availability.state).toBe('page');
    expect(availability.burn).toBeGreaterThan(14.4);
  });

  it('reports healthy when failures stay inside the budget', () => {
    for (let i = 0; i < 1000; i += 1) httpRequestsTotal().inc({ method: 'GET', route: '/x', status: '200' });
    httpRequestsTotal().inc({ method: 'GET', route: '/x', status: '500' });
    const availability = evaluateSlos().slos.find((s) => s.name === 'api_availability');
    expect(availability.state).toBe('healthy');
  });

  it('evaluates generation success including cache hits', () => {
    aiGenerationsTotal().inc({ status: 'success' }, 94);
    aiGenerationsTotal().inc({ status: 'cache_hit' }, 5);
    aiGenerationsTotal().inc({ status: 'failure' }, 1);
    const gen = evaluateSlos().slos.find((s) => s.name === 'ai_generation_success');
    expect(gen.observed).toBeCloseTo(0.99, 2);
    expect(gen.state).toBe('healthy');
  });
});
