# Performance Budget — Realestate Website

## Core Web Vitals Targets

| Metric                          | Target   | Google 'Good' Threshold |
| ------------------------------- | -------- | ----------------------- |
| LCP (Largest Contentful Paint)  | < 2500ms | < 2500ms                |
| CLS (Cumulative Layout Shift)   | < 0.1    | < 0.10                  |
| INP (Interaction to Next Paint) | < 200ms  | < 200ms                 |
| TTFB (Time to First Byte)       | < 800ms  | < 800ms                 |
| FCP (First Contentful Paint)    | < 1800ms | < 1800ms                |
| TBT (Total Blocking Time)       | < 300ms  | < 300ms                 |

## Lighthouse Score Targets

- Performance: ≥ 88
- Accessibility: ≥ 88
- Best Practices: ≥ 88
- SEO: ≥ 88

## Bundle Size Budgets

- JavaScript: < 250 KB (gzipped)
- CSS: < 60 KB (gzipped)
- Total page: < 400 KB (gzipped)

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

```html
<link rel="preconnect" href="https://js.stripe.com" />
```

```html
<link rel="preconnect" href="https://api.stripe.com" />
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

> Note: Good baseline — tune per industry after launch
