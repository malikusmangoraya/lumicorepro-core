# LumicorePro Improvements Roadmap

**Version:** 1.0  
**Priority:** ROI-ranked feature and bugfix backlog

---

## Critical (Week 2 — Blocking Launch)

| ID | Item | ROI | Effort | Category |
|----|------|-----|--------|----------|
| C1 | Social proof live notifications | 95 | 4h | Conversion |
| C2 | AI chat shopping assistant (wire ChatBox to API) | 93 | 6h | Support |
| C3 | Stripe checkout integration in generated projects | 92 | 6h | Commerce |
| C4 | OWASP security audit pass | 92 | 4h | Security |
| C5 | Lighthouse 95+ optimization pass | 95 | 4h | Performance |

---

## High Priority (Week 2-3)

| ID | Item | ROI | Effort | Category |
|----|------|-----|--------|----------|
| H1 | Loyalty points & rewards engine | 88 | 8h | Retention |
| H2 | Smart search with autocomplete | 85 | 6h | Discovery |
| H3 | Personalized product recommendations | 90 | 6h | Conversion |
| H4 | Route-based code splitting | 88 | 3h | Performance |
| H5 | WebP image conversion + lazy loading | 95 | 2h | Performance |
| H6 | SaaS analytics dashboard wiring | 87 | 6h | SaaS |
| H7 | Error monitoring (Sentry integration) | 82 | 2h | Ops |

---

## Medium Priority (Week 3-4)

| ID | Item | ROI | Effort | Category |
|----|------|-----|--------|----------|
| M1 | Wishlist + product compare side-by-side | 78 | 5h | Engagement |
| M2 | Two-factor authentication | 75 | 6h | Security |
| M3 | WCAG 2.1 AA accessibility audit | 78 | 4h | Accessibility |
| M4 | SEO structured data + meta tags | 80 | 2h | SEO |
| M5 | Redis caching layer for high traffic | 70 | 4h | Performance |
| M6 | Multi-currency support in CartSummary | 72 | 4h | Commerce |
| M7 | Admin panel for generated projects | 68 | 10h | Admin |

---

## Bugfixes (Ongoing)

| ID | Issue | Severity | Fix |
|----|-------|----------|-----|
| B1 | master-express-backend missing route files | High | Copy shared routes or stub |
| B2 | Component prop mismatch warnings | Medium | Align prop signatures |
| B3 | Frontend env vars missing from .env.example | Low | Auto-generate in project_builder |
| B4 | PostgreSQL vs MySQL schema inconsistency | Medium | Standardize on PostgreSQL |
| B5 | React 18 vs 19 version in generated projects | Low | Sync PACKAGE_VERSION_MAP |

---

## Infrastructure (Week 4+)

| ID | Item | Effort | Impact |
|----|------|--------|--------|
| I1 | CI/CD pipeline (GitHub Actions) | 4h | Automated testing |
| I2 | Docker compose for generated projects | 3h | Easy local dev |
| I3 | Template preview gallery in frontend | 8h | Sales/marketing |
| I4 | API documentation (OpenAPI/Swagger) | 4h | Developer experience |
| I5 | Multi-provider AI fallback UI | 3h | Reliability |

---

## ROI Calculation

```
ROI/Effort Ratio = ROI Score / Effort Hours

Example: Social proof (95 ROI / 4h) = 23.75 → Top priority
Example: Admin panel (68 ROI / 10h) = 6.8 → Lower priority
```

The `ImprovementRecommender` agent module uses this same formula automatically after each generation.

---

## How to Prioritize

1. Run generation → read `improvement_recommendations` in report
2. Fix all Critical items before launch
3. Implement High items for market differentiation
4. Schedule Medium items post-launch based on user feedback
5. Bugfixes: address B1-B2 before any public demo

---

## Success Criteria per Phase

| Week | Done When |
|------|-----------|
| Week 1 | 9-phase pipeline generates valid projects with quality report |
| Week 2 | Social proof + AI chat + Stripe working in generated ecommerce |
| Week 3 | Loyalty + search + recommendations live |
| Week 4 | Lighthouse 95+, security audit passed, launch_ready consistently true |
