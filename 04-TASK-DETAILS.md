# 04 — TASK DETAILS (Har kaam ki poori detail)

Format: **Maqsad -> Steps -> Definition of Done (DoD) -> Pro version -> Premium version**

---

## TASK 1 — Backend `.env.example` mukammal karna  `[P0]`
**Maqsad:** Buyer har feature (OAuth, Redis, SMTP, Stripe) bina code parhe enable kar sake.

**Steps**
1. Code mein `process.env.` search karo, sab variables ki list nikalo:
   ```bash
   grep -rhoE "process\.env\.[A-Z0-9_]+" backend/src | sort -u
   ```
2. Har variable ko groups mein rakho (App, DB, Auth, OAuth, Email, Redis, Payments, AI, Monitoring, License).
3. Har variable ke upar comment: kya hai, zaroori ya optional, kahan se milega.
4. `config/env.js` mein zod schema banao, startup par validate.
5. CI mein script: `.env.example` ke keys == code ke keys (mismatch ho to fail).

**DoD:** Script 0 missing dikhaye. Fresh clone + `.env.example` copy se app boot ho (optional features "not configured" dikhayein, crash na karein).

**Pro:** Env validation startup par saaf message de: `Missing JWT_SECRET (see docs/02-configuration.md#jwt)`.
**Premium:** Interactive `npm run setup` wizard jo `.env` khud generate kare (random secrets ke saath) aur connection test kare.

*Template: file `06-env.example.FULL`*

---

## TASK 2 — Frontend se server secrets hatana  `[P0]`
**Maqsad:** Secrets browser bundle mein leak na hon.

**Steps**
1. `frontend/.env.example` se ye hatao: `JWT_SECRET`, `STRIPE_WEBHOOK_SECRET`, `PAYPAL_CLIENT_SECRET`, `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_WEBHOOK_SECRET`, `BKASH_APP_SECRET`, `RAZORPAY_KEY_SECRET`.
2. Frontend mein sirf `VITE_*` rakho (public keys, API URL).
3. Agar kisi secret ka real `.env` kabhi commit hua ho to **us key ko rotate karo** (sirf delete kaafi nahi, git history mein rehti hai).
4. `gitleaks` ya `trufflehog` se git history scan karo.
5. CI check: frontend env mein `SECRET|KEY|PASSWORD` (VITE_PUBLISHABLE ke ilawa) mile to fail.

**DoD:** Built bundle mein `grep -r "sk_live\|secret"` kuch na mile. gitleaks clean.
**Pro:** Pre-commit hook (husky + gitleaks).
**Premium:** Secrets manager guide (AWS Secrets Manager / Doppler / Vault) + rotation runbook.

---

## TASK 3 — Real migrations  `[P0]`
**Maqsad:** Production mein safe schema upgrade.

**Steps**
1. Umzug ya `sequelize-cli` setup karo, `backend/src/db/migrations/`.
2. Baseline migration: maujooda 3 SQL schemas ko ek initial migration mein badlo.
3. Naming: `20260101120000-create-users.js`, har migration mein `up` aur `down`.
4. Scripts: `db:migrate`, `db:migrate:undo`, `db:seed`, `db:reset` (sirf dev).
5. Production mein `sync()` band; CI mein "migrate up -> down -> up" test.
6. Docker entrypoint: migrate chalao phir server start.

**DoD:** Khaali DB par `db:migrate` poora schema bana de; `undo` kaam kare; CI test pass.
**Pro:** Seeders (demo data, niche-specific realistic), `db:seed:demo`.
**Premium:** Zero-downtime migration guide (expand/contract pattern), automatic pre-migration backup.

---

## TASK 4 — Template ka bacha hua code hatana  `[P0]`
**Maqsad:** Har product apne niche ka lage.

**Steps**
1. Har product ke liye "keep list" banao (kaun se models/routes zaroori).
2. Baqi hatao: e.g. ClaimFlow se `Doctor`, `Cart`, `CartItem`, `Wishlist`, `Product`, `Category`.
3. Unused route modules, pages, translations ke keys, docs ke mentions saaf karo.
4. `depcheck` + `knip` + `ts-prune` chalao, unused deps/exports hatao (`mongoose`).
5. Naming: generic -> niche (`Order` -> `Claim`, `Service` -> `Coverage`).

**DoD:** `depcheck` 0 unused. Route count niche ke hisab se (15-25), 33 nahi. Search karo "Doctor|Cart|Wishlist" -> irrelevant products mein 0.
**Pro:** Har product ka `product.config` jo modules enable karta hai.
**Premium:** Module marketplace (buyer sirf wo modules install kare jo chahiye).

---

## TASK 5 — Automated testing  `[P0]`
**Maqsad:** Release par bharosa, refunds kam.

**Test pyramid**
| Qism | Tool | Kya test | Target |
|---|---|---|---|
| Unit | Vitest/Jest | services, utils, totp, validators | 70%+ |
| Integration | Supertest + test Postgres (Testcontainers) | API routes, DB, auth flow | Har route |
| E2E | Playwright | Register -> login -> core flow -> logout | 10-15 critical flows |
| Contract | OpenAPI + schemathesis | API spec = reality | Pro |
| Visual | Playwright snapshots | UI regression | Premium |

**Steps**
1. Test DB alag, har run mein migrate + seed.
2. Factories (`@faker-js/faker`) test data ke liye.
3. Auth tests: register, duplicate email, wrong password, lockout, refresh rotation, refresh reuse, 2FA, password reset expiry, rate limit.
4. Payment tests: webhook signature valid/invalid, duplicate webhook (idempotency), failed payment.
5. RBAC tests: har role ko har sensitive endpoint par 200/403 matrix.
6. CI mein coverage report + minimum threshold.

**DoD:** `npm test` green, coverage threshold enforce, E2E CI mein chale.
**Pro:** Load test (k6) 100 concurrent users, p95 < 500ms.
**Premium:** Mutation testing (Stryker), accessibility E2E (axe-playwright), chaos/failure tests (Redis down -> app chalti rahe).

---

## TASK 6 — Niche-specific features (Phase 2)  `[P1]`
**Maqsad:** 11 skins ke bajaye 11 asal products.

**Steps (har product)**
1. `02-FEATURES-AND-BENEFITS.md` se us product ki list lo.
2. User stories likho: "Ek [role] ke taur par main [kaam] chahta hoon taake [faida]".
3. Data model design -> migration -> API -> UI -> tests -> docs, is order mein.
4. Realistic seed data (10-30 records, asal naam/terms).
5. Har feature ki Acceptance Criteria likho aur test karo.

**DoD:** Demo mein koi bhi buyer 5 minute mein niche ka core flow end-to-end kar sake.
**Pro:** Niche dashboards (charts, KPIs), import/export, email notifications.
**Premium:** AI assistant niche ke context ke saath, automation rules, integrations (Zapier/Make webhooks).

---

## TASK 7 — Admin dashboard (sab 11 mein)  `[P1]`
**Maqsad:** Buyer ke admin ko control mile (9-page wale products mein bhi).

**Pages:** Overview (KPIs), Users, Roles/Permissions, Niche data tables, Payments, Settings (branding, email, integrations), Audit log, System health.
**Table rules:** server-side pagination, sorting, filters, search, bulk actions, CSV export.

**DoD:** Admin bina code chhue user ban/unban, role badal, data export, audit dekh sake.
**Pro:** Saved views, bulk edit, impersonate user (audit ke saath).
**Premium:** Custom report builder, scheduled reports, feature-flag UI, usage/plan limits.

---

## TASK 8 — GDPR / Privacy features  `[P1]`
**Steps**
1. Cookie consent banner (necessary / analytics / marketing), consent record store karo.
2. "Download my data" (JSON/ZIP) endpoint.
3. "Delete my account" (soft delete -> 30 din baad hard delete job).
4. Privacy Policy / Terms / Cookie Policy pages (editable templates).
5. Data retention config, analytics/AI mein PII masking.
6. Third-party processors ki list docs mein.

**DoD:** User khud data export aur delete kar sake; consent log mein dikhe.
**Pro:** Consent version tracking, re-consent on policy change.
**Premium:** DPA template, data-processing register, regional data residency guide.

---

## TASK 9 — Accessibility (WCAG 2.2 AA)  `[P1]`
**Steps**
1. Semantic HTML, headings order, landmarks.
2. Keyboard: sab kuch Tab se chale, focus ring visible, modals mein focus trap.
3. Color contrast ≥ 4.5:1 (text), 3:1 (UI).
4. Forms: label, error message `aria-describedby`, `aria-live` for toasts.
5. Images alt text, `prefers-reduced-motion` respect (framer-motion animations).
6. RTL (ar, ur) test, screen reader test (NVDA/VoiceOver).
7. CI: `axe-core` + Lighthouse.

**DoD:** Lighthouse a11y ≥ 95, axe mein 0 serious/critical.
**Pro:** Skip links, high-contrast theme.
**Premium:** Accessibility Conformance Report (VPAT) + a11y statement page.
(EU European Accessibility Act: EU mein bechne wale kuch services par lagu hai, apne case mein qanooni mashwara lo.)

---

## TASK 10 — API documentation  `[P2]`
**Steps:** `openapi.yaml` (zod se auto-generate: `zod-to-openapi`), Swagger UI `/api/docs`, har endpoint ka example request/response/error.
**DoD:** Spec validate ho, CI mein spec vs routes check.
**Pro:** Postman collection auto-generate.
**Premium:** Typed SDK (TS) generate + versioning (`/v1`), deprecation policy.

---

## TASK 11 — Monitoring & Logging  `[P2]`
**Steps:** Sentry (FE+BE, source maps), pino/winston JSON + requestId, `/health` + `/ready`, uptime check (UptimeRobot), log redaction (password/token).
**DoD:** Jaan boojh kar error phenko -> Sentry mein aaye.
**Pro:** Alert rules (error spike, 5xx).
**Premium:** Prometheus + Grafana dashboards, OpenTelemetry tracing.

---

## TASK 12 — Security hardening  `[P0/P1]`
Detail file 05 mein. Short list: refresh-token reuse detection, CSP, rate limits, brute-force lockout, upload validation, SSRF protection, dependency audit, webhook idempotency.

---

## TASK 13 — Performance  `[P2]`
**Steps:** Bundle budget CI mein (aap pehle se rakhte hain), image optimization (AVIF/WebP, responsive `srcset`), hero video: poster + lazy + `preload="none"`, DB indexes + slow query log, Redis caching, gzip/brotli, CDN headers.
**DoD:** Lighthouse Performance ≥ 90 mobile, LCP < 2.5s, CLS < 0.1, INP < 200ms.
**Pro:** Edge caching guide (Cloudflare).
**Premium:** Load-test report publish (k6 results) as selling point.

---

## TASK 14 — i18n quality  `[P2]`
**Steps:** Missing-key checker CI mein, pluralization + date/number/currency formats (`Intl`), RTL visual QA (ar, ur), translations ka native review (machine translation akeli kaafi nahi), language switcher + `hreflang`.
**DoD:** 14 locales mein 0 missing keys, RTL pages toot-te nahi.
**Premium:** Translation workflow (Crowdin/Lokalise guide), per-tenant language settings.

---

## TASK 15 — Demo & Marketing assets  `[P2]`
**Steps:** Demo accounts (admin/user), demo data auto-reset har raat, 8-10 screenshots (light+dark), 60-90 sec video, landing page copy (benefit-first), comparison table vs competitors, FAQ.
**Pro:** Interactive product tour (Shepherd.js), public roadmap.
**Premium:** Case studies, testimonials, buyer onboarding email sequence.

---

## TASK 16 — Release & Support process  `[P3]`
**Steps:** SemVer, release checklist, signed ZIP + checksum, upgrade guide, support policy (SLA, channels, kya shamil nahi), refund policy, issue templates.
**Pro:** Private support board / Discord.
**Premium:** Priority support SLA (e.g. 24h), paid installation service, annual maintenance plan.

---

## Rollout ka tareeqa (har product ke liye same)

1. Branch banao -> 2. Task 1-5 -> 3. Task 6 (niche) -> 4. Task 7-9 -> 5. Task 10-14 -> 6. Task 15-16 -> 7. Final QA checklist (file 05) -> 8. Release

**Rule:** Ek waqt mein ek product. Pilot mukammal hone ke baad hi agla.
