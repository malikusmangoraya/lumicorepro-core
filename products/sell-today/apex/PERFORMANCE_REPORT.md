# Performance Report

Budgets below follow Apex performance targets. Values that were not measured during the build are reported honestly as *not measured* — run the deployment URL through Lighthouse to backfill them.

| Metric | Target | Measured | Verdict |
|--------|--------|----------|---------|
| Lighthouse Performance | 95+ | ``not measured`` | *not verified* |
| JS bundle (gzip) | <150KB (hard <200KB) | ``not measured`` | *not verified* |
| CSS (gzip) | <30KB (hard <50KB) | ``not measured`` | *not verified* |
| Total bundle (gzip) | <200KB (hard <300KB) | ``not measured`` | *not verified* |
| LCP | <1.5s | ``not measured`` | *not verified* |
| CLS | <0.05 (hard <0.1) | ``not measured`` | *not verified* |

## Measurements taken during the build

- {'performance_targets': {'lcp_ms': 2500, 'cls': 0.05, 'inp_ms': 150, 'ttfb_ms': 600, 'fcp_ms': 1500, 'tbt_ms': 200, 'lighthouse': {'performance': 90, 'accessibility': 92, 'best_practices': 93, 'seo': 90}, 'bundle_kb': {'js': 300, 'css': 70, 'total': 500}, 'note': 'SaaS: dashboard routes can lazy-load; landing must be fast'}, 'analytics_events': 12, 'ab_experiments': 3, 'webhook_events': 10}
