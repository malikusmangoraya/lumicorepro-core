# Performance Budget — Saas Website

## Core Web Vitals Targets

| Metric                          | Target   | Google 'Good' Threshold |
| ------------------------------- | -------- | ----------------------- |
| LCP (Largest Contentful Paint)  | < 2500ms | < 2500ms                |
| CLS (Cumulative Layout Shift)   | < 0.05   | < 0.10                  |
| INP (Interaction to Next Paint) | < 150ms  | < 200ms                 |
| TTFB (Time to First Byte)       | < 600ms  | < 800ms                 |
| FCP (First Contentful Paint)    | < 1500ms | < 1800ms                |
| TBT (Total Blocking Time)       | < 200ms  | < 300ms                 |

## Lighthouse Score Targets

- Performance: ≥ 90
- Accessibility: ≥ 92
- Best Practices: ≥ 93
- SEO: ≥ 90

## Bundle Size Budgets

- JavaScript: < 300 KB (gzipped)
- CSS: < 70 KB (gzipped)
- Total page: < 500 KB (gzipped)

## Critical Resource Preconnects

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
```

```html
<link rel="preconnect" href="https://fonts.gstatic.com" />
```

```html
<link rel="preconnect" href="https://www.googletagmanager.com" />
```

## Optimization Checklist

- [ ] Convert all images to WebP/AVIF format
- [ ] Enable Brotli compression on server
- [ ] Set long cache headers for hashed assets (1 year)
- [ ] Defer non-critical JavaScript
- [ ] Use font-display: swap for web fonts
- [ ] Add width/height to all `<img>` elements
- [ ] Eliminate render-blocking resources
- [ ] Preload LCP image with `<link rel=preload>`
- [ ] Run Lighthouse CI on every PR

> Note: SaaS: dashboard routes can lazy-load; landing must be fast
