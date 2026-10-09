# The Website Build Playbook

**Audience:** anyone (human or agent) building a **new** website or **updating
an existing** one with LumicorePro.
**Scope:** the single checklist that runs every build end-to-end — frontend,
backend, database, auth/login, payments, sidebar dashboard, logo/animation/motion,
CI/CD, Docker, testing, security, performance and deployment. Design *uniqueness*
(depth on identity, layout, motion taste) lives in the companion
[Unique Project Playbook](./UNIQUE_PROJECT_PLAYBOOK.md); this document owns the
**full-stack build contract**.
**Time:** ~20 minutes to read once; afterwards keep it open and tick it.

---

## 0. How to use this document

1. **New website** → work top to bottom, Phases 0→10. Every phase has
   `DO` (what to build), `FILES` (where it lives in this repo) and
   `- [ ] ACCEPT` (the check that proves it works). Do not skip a phase —
   mark it `N/A — reason` instead.
2. **Updating an existing website** → jump to §16 (the delta path), then re-run
   the gates in §12 before you call it done.
3. **Evidence rule (hard):** a checkbox may only be ticked when the command
   actually ran and its output supports it. "Should pass" is not a pass.
   If a check could not run, write *not measured* — never a ✅.
4. **Cross-links are not duplication.** Where this doc says *see
   [Unique Project Playbook] §5*, that section holds the full detail — read it
   there instead of expecting it here.

Pipeline context (where this doc sits):

```
Brief → Design decisions (Unique Project Playbook + design-manifest.json)
      → THIS PLAYBOOK (build contract, phases 1–10)
      → Gates (§12) → Deploy (§15) → Live verification (evidence!)
```

---

## 1. Phase 0 — Brief, manifest, skeleton

**DO**

- Write the one-paragraph product brief: what the business is, 3 personas, the
  primary conversion (buy / sign up / book / contact), the industry and brand.
- Pick the design direction *before code*: style id, palette, type pairing,
  layout device, motion vocabulary — decisions belong in
  `design-manifest.json` and `.artifacts/` (see Unique Project Playbook §2),
  not in your head.
- Confirm the stack baseline: React 19 + Vite + Tailwind 3 (frontend),
  Express + PostgreSQL/Sequelize + Redis (backend), optional Python FastAPI
  AI agent.

**FILES** — `ai-agent/agent/orchestrator.py` (manifest writer),
`ai-agent/agent/design_style.py` (30 style ids), `tailwind.config.js`,
`src/styles/globals.css`, `.env.example` + `backend/.env.example` (source of
truth for env vars).

- [ ] ACCEPT: brief (business, 3 personas, conversion, industry) written;
      design direction recorded in `design-manifest.json` / `.artifacts/`.
- [ ] ACCEPT: every env var you need exists in `.env.example` — no key is ever
      hardcoded; secrets live in `.env` only.

---

## 2. Phase 1 — Frontend

**DO**

- Routes: `React.lazy()` + `Suspense` at route level only; route table lives in
  `src/routes/` (`index.jsx`, `routeConfig.js`). The standard website set:
  `/`, `/about`, `/services` (or `/products`), `/pricing`, `/contact`,
  `/login`, `/register`, `/checkout`, `/dashboard`, `/admin`,
  `/privacy`, `/terms`, `*` → NotFound.
- Pages use semantic HTML + Tailwind utilities against **tokens only**
  (`--t-*` variables — no raw hex). `dark:` prefix required on color
  utilities; mobile-first; `transition-all duration-200`.
- State rule: `useState` for local UI · React Query for server data
  (`staleTime: 5min`, `gcTime: 30min`, `retry: 2`) · Context for theme/auth/
  currency/i18n · Zustand for cart/filters/chat.
- Every async surface ships **loading / success / error / empty / retry**
  states. Axios interceptor in `src/services/api.js` attaches the JWT and
  maps 401→login, 403→denied, 404→not found, 422→inline errors, 500+→friendly
  generic (no stack traces).
- Images: real `.jpg/.png/.webp/.svg` through `LazyImage` with meaningful
  `alt`; `loading="lazy"` below the fold; 5MB max.
- Components: functional only, ≤300 lines, props `variant/size/disabled/
  className`, `useMemo`/`useCallback` for expensive work, error boundary per
  feature.

**FILES** — `src/pages/`, `src/layouts/` (`MainLayout.jsx` — note
`<main>` carries `min-h-[100svh]`, a CLS fix, do not regress it), `src/routes/`,
`src/context/`, `src/hooks/`, `src/services/api.js`, `src/components/`
(`ui/`, `common/`, `forms/`, `ecommerce/`, `motion/`).

- [ ] ACCEPT: `npm run lint` exits 0.
- [ ] ACCEPT: `npm run build` green **and** `npm run size` PASS
      (budgets in §14).
- [ ] ACCEPT: each route shows loading → content or friendly error; no page
      renders raw JSON or a blank screen on API failure.

---

## 3. Phase 2 — Backend (Express)

**DO**

- Middleware order on every route: `auth → validate → rate-limit → route →
  errorHandler`. Route modules are mounted under `/api/v1/` (or the existing
  `/api/<domain>` prefix of this repo — stay consistent with the router you
  inherit).
- **Response contract (mandatory):** success
  `{ success, status, message, data, timestamp }`; failure
  `{ success:false, status, code, message, timestamp }` with a stable machine
  `code` (e.g. `PAYMENT_UNCONFIGURED`, `PLAN_LIMIT_EXCEEDED`) and a safe user
  message. Never leak stack traces or SQL.
- Validate **every** input (zod/Joi schema per route) — never trust the
  client even when the frontend already validated. Parameterized SQL only.
- Structured logging with `requestId` correlation; errors carry code + context.
- Rate-limit auth and AI endpoints hard; CORS whitelist from
  `ALLOWED_ORIGINS`; helmet/security headers on.

**FILES** — `backend/server.js`, `backend/routes/` (34 route modules incl.
`auth`, `user`, `product`, `order`, `payment`, `cart`, `dashboard`,
`analytics`, `settings`, `notification`, `upload`, `license`),
`backend/middleware/` (`auth.js`, `rbac.js`, `rateLimit.js`,
`validateRequest.js`, `errorHandler.js`, `captchaVerify.js`,
`webhookSecurity.js`, `security.js`, `requestId.js`, `audit.js`,
`planUsageGuard.js`), `backend/config/`.

- [ ] ACCEPT: every new endpoint answers in the response contract above
      (write the test in the same PR).
- [ ] ACCEPT: invalid/missing input → 422 + field messages, not a 500.
- [ ] ACCEPT: unauthenticated hit on a protected route → 401; wrong role → 403.

---

## 4. Phase 3 — Database (PostgreSQL)

**DO**

- Schema first, code second: snake_case tables, foreign keys with
  `ON DELETE` behavior, `NOT NULL` where the domain demands it, CHECK
  constraints for enums-as-strings, **indexes on every column you filter or
  sort by** (plus FKs).
- Soft deletes: `deleted_at` (IS NULL in every query path); `created_at` /
  `updated_at` on all tables.
- Migrations are **versioned, additive and idempotent** (`IF NOT EXISTS` /
  `ADD COLUMN IF NOT EXISTS`), each with a matching `*.down.sql` — CI runs
  every migration **twice** against a throwaway Postgres to prove
  re-application is safe (`.github/workflows/ci.yml` job 6).
- Seed script for demo/production data (niche-aware:
  `backend/scripts/production-seed.js`).

**FILES** — `database/schemas/` (`users.sql`, `ecommerce.sql`, `electronics.sql`,
`saas.sql`, `automotive.sql`, `indexes.sql`), `database/migrations/`,
`backend/models/` (30 Sequelize models: `User`, `Role`, `Permission`,
`Organization`, `Membership`, `Order`, `Payment`, `Subscription`, `Plan`,
`Coupon`, `WebhookEvent`, `AuditLog`, `SystemConfig`, `FeatureFlag` …),
ERD doc: [BACKEND_DATABASE_ERD](./BACKEND_DATABASE_ERD.md).

- [ ] ACCEPT: new columns/tables ship as migration files, not ad-hoc
      `ALTER` on prod; `psql -f` twice → no errors.
- [ ] ACCEPT: every queried column has an index (`EXPLAIN` on the hot query).
- [ ] ACCEPT: seed runs clean on an empty database **and** is re-runnable.

---

## 5. Phase 4 — Authentication & login system

**DO**

- Credentials: **bcrypt cost ≥12**; passwords checked with timing-safe
  compare; min-length + complexity validated server-side.
- Tokens: **JWT access 15 min** + **refresh 7 days** (rotating, stored
  httpOnly/secure cookie or client store per existing convention), separate
  `JWT_SECRET` / `JWT_REFRESH_SECRET`. Refresh endpoint issues a new access
  token and rotates on use; logout blacklists.
- Flows to ship (all exist as reference implementations): register (with
  captcha/Turnstile when configured), login, refresh, logout, profile
  get/update, **email verification**, **password reset (request + finalize)**,
  **2FA** (OTP + authenticator app), **OAuth** (Google/GitHub redirect flow).
- Authorization: RBAC middleware (`rbac.js`) — public / user / vendor / admin
  checked **server-side on every route**; the UI hiding a button is not
  authorization. Org/tenant scoping: filter data by the caller's org id from
  the token, never from a client-supplied body field.
- Brute-force protection: `rateLimit.js` on `/login`, `/register`,
  `/reset-password`, `/2fa/*`; generic "invalid credentials" message (never
  reveal whether the email exists).
- Frontend: `AuthContext` + axios interceptor; protected routes redirect to
  `/login?next=…`; session-expired → silent refresh → fallback to login.

**FILES** — `backend/routes/auth.routes.js`, `backend/middleware/auth.js`,
`backend/middleware/rbac.js`, `src/context/AuthContext.jsx`,
`src/pages/` (`Login.jsx`, `Register.jsx`, `ForgotPassword.jsx`,
`ResetPassword.jsx`, `VerifyEmail.jsx`, `OAuthCallback.jsx`,
`ChangePassword.jsx`), tests in `backend/__tests__/`.

- [ ] ACCEPT: wrong password → 401 generic message; correct → access+refresh;
      refresh works; expired access token recovers without a full logout.
- [ ] ACCEPT: user token cannot read/update another user's row (IDOR probe);
      user token on an admin route → 403.
- [ ] ACCEPT: reset + verification emails produce working single-use tokens
      (or, if SMTP unconfigured, the log-only fallback path is explicit).

---

## 6. Phase 5 — Payment system

**DO**

- Gateways are **runtime-configured from the DB/admin settings**, not
  compile-time: `GET /api/payments/config` returns enabled gateways +
  publishable keys; an unconfigured gateway answers a clean
  `PAYMENT_UNCONFIGURED` error instead of crashing the route.
- Flow: create order (DB) → create payment intent/order on the gateway →
  client confirms → **server-side verify** (never trust the client) →
  mark order paid → issue receipt/invoice. Webhooks are the source of truth
  for async outcomes.
- Webhook security: signature verification per gateway
  (`webhookSecurity.js`), raw-body preserved for signature computation,
  **idempotency** (store `WebhookEvent` id; replaying a webhook changes
  nothing), replay-window check.
- Refunds + customer portal + invoice endpoints exist; wire them if the
  project sells.
- Test mode first: Stripe/PayPal sandbox keys in `.env`, test cards end-to-end
  before any live key.

**FILES** — `backend/routes/payment.routes.js` (Stripe + PayPal + 11 more
gateways code-enabled — see README §5), `backend/routes/lemonsqueezy.routes.js`
(vendor licensing), `backend/middleware/webhookSecurity.js`,
`backend/models/Payment.js`, `Order.js`, `WebhookEvent.js`,
`src/pages/Billing.jsx`, checkout flow in `src/components/ecommerce/`.

- [ ] ACCEPT: sandbox purchase completes: order created → paid → invoice,
      webhook signature rejected when tampered.
- [ ] ACCEPT: same webhook delivered twice → one order state change.
- [ ] ACCEPT: unconfigured gateway shows a friendly "payments not set up"
      state in the UI — no stack trace, no crash.

---

## 7. Phase 6 — Sidebar dashboard & admin

**DO**

- Use `DashboardLayout` (sidebar shell with responsive `sidebarOpen` drawer +
  overlay on mobile, skip link, focus handling) — never hand-roll a second
  sidebar.
- Navigation is **data-driven**: add items to `src/navigation/navItems.js` /
  `navigationConfig.js` with a real Lucide icon **paired with a text label**;
  group into sections (Overview / Commerce / Users / Settings), mark active
  state from the route, and gate items by role (an admin-only item must also
  be blocked by the API — see §5).
- Standard dashboard pages: `Dashboard` (KPIs + charts), `AdminDashboard`,
  `AdminUsers` (CRUD + CSV), `AdminAuditLogs` (filters + pagination),
  `Notifications`, `Billing`, `GlobalSystemSettings`, `OrganizationSettings`,
  `Onboarding`/`SetupWizard` for first run.
- Every widget: loading skeleton, empty state, error state with retry;
  numbers formatted via `Intl` + `CurrencyContext`; charts lazy-loaded.

**FILES** — `src/layouts/DashboardLayout.jsx`, `src/navigation/`
(`navItems.js`, `navigationConfig.js`, `WebsiteLayoutKit.js`),
`src/pages/Dashboard.jsx`, `Admin*.jsx`, `src/components/dashboard/RevenueCard.jsx`,
`src/pages/GlobalSystemSettings.jsx`, `backend/routes/dashboard.routes.js`,
`analytics.routes.js`, `settings.routes.js`, `audit.routes.js`.

- [ ] ACCEPT: sidebar shows the new page, active state correct, mobile drawer
      works, keyboard-navigable, admin items invisible **and** API-blocked
      for non-admins.
- [ ] ACCEPT: every dashboard widget has loading/empty/error states (kill the
      API and reload — nothing renders blank).

---

## 8. Phase 7 — Logo, brand & motion

**DO**

- **Logo:** never plain text. Generate the dynamic vector SVG mark
  (`BrandLogo` / `UniqueLogo`): geometric symbol + dual-color gradient, one
  mark reused everywhere — nav, footer, favicon, OG image, email header.
- **Motion:** choose **one** motion vocabulary per project from the 13
  components in `src/components/motion/` (`Reveal`, `StaggerGroup`,
  `BentoGrid`, `BorderBeam`, `HolographicCard`, `MagneticButton`,
  `SpotlightGrid`, `TextMorph`, `HeroCanvas`, `Scene3D`, `CyberGridCanvas`,
  `ParticleField3D`) — plus the injected `lumi-motion` layer (scroll-reveal,
  hover-lift) for generated projects. Animate `transform`/`opacity` only;
  3D/canvas heroes are optional and lazy-loaded.
- **Mandatory:** respect `prefers-reduced-motion` (kill or simplify every
  animation), no autoplay flashing >3/s, no zero-height canvas, mobile
  fallback for every cinematic hero.
- Full rules, anti-patterns and the scoring of these choices:
  **[Unique Project Playbook](./UNIQUE_PROJECT_PLAYBOOK.md) §3.3 (logos),
  §5 (motion), §7 (DesignLint + visual score).**

**FILES** — `src/components/common/BrandLogo.jsx`, `src/assets/logos/`,
`src/components/motion/`, `ai-agent/agent/pro_design.py` (injected mark),
`ai-agent/agent/extensions/animation_injector.py`.

- [ ] ACCEPT: logo is a real SVG mark (grep for plain-text brand headings —
      none); identical mark in nav, footer, favicon, OG image.
- [ ] ACCEPT: one coherent motion vocabulary (not a sampler platter); with
      OS "reduce motion" enabled the page is fully usable and still.
- [ ] ACCEPT: DesignLint run on the built page — no P1 findings left
      (playbook §7).

---

## 9. Phase 8 — i18n, RTL, accessibility, SEO (every site ships these)

| Concern | Contract | Check |
|---|---|---|
| i18n | every user-facing string via `t('key')`, locales in `src/i18n/locales/*.json`, no hardcoded JSX strings | grep for raw copy in components |
| RTL | `dir="rtl"` on `<html>`, logical properties, `rtl:` prefix, arrows/chevrons flip | switch to an Arabic locale once |
| Currency | numbers in DB, `Intl.NumberFormat` + `CurrencyContext` for display | change currency, totals reformat |
| A11y | WCAG 2.1 AA: landmarks, skip-link first, labels + `aria-describedby`, `aria-live` for async updates, `role="alert"` errors, visible focus, icon-only buttons get `aria-label` + tooltip | keyboard-only pass: Tab/Enter/Escape everywhere |
| Motion a11y | `prefers-reduced-motion` honored | OS setting on |
| SEO | title/description/canonical/OG/JSON-LD per route (`SEOMetaTags`/`PageSEO`), sitemap, robots, honest JSON-LD | view source on 2 routes |
| Cookies/consent | `CookieConsent` when analytics/marketing cookies exist | fresh profile |

- [ ] ACCEPT: keyboard-only walk of the critical path (landing → login →
      main action) with no traps; axe/Lighthouse a11y ≥ 0.95 measured.
- [ ] ACCEPT: both light and dark themes reviewed (`dark:` used, no unreadable
      contrast — 4.5:1 text / 3:1 large & UI).

---

## 10. Phase 9 — CI/CD

**DO** — the repo already has the pipeline; extend it, don't fork it.

- **Single merge gate: `.github/workflows/ci.yml`** (9 jobs → aggregate
  `CI gate` check, which branch protection should require):
  1. Frontend lint · 2. Frontend unit tests (Vitest + coverage)
  3. Frontend build + **bundle budget** (`npm run size`)
  4. Backend syntax check · 5. Backend unit + integration (Jest)
  6. **Migration SQL check** (Postgres 16, every migration applied twice +
     down files) · 7. AI agent pytest · 8. Playwright e2e (chromium)
  9. **gitleaks secret scan** (history, not just worktree) + `npm audit
  --audit-level=high` on frontend and backend.
- Releases: `.github/workflows/deploy.yml` — **tag-triggered** → verify →
  build + push to GHCR → optional SSH deploy. Cron backups:
  `backup.yml`. `ci-cd.yml` is manual-only (fork simulation) — it is *not* a
  merge gate.
- New required check ⇒ add it to `ci.yml`'s `needs:` graph so it joins the
  `CI gate` automatically; never add a second workflow watching a different
  branch set (that is the exact bug this repo already fixed once).

**FILES** — `.github/workflows/` (`ci.yml`, `deploy.yml`, `backup.yml`,
`test.yml`, `autopilot.yml`, `ci-cd.yml`), `.github/gitleaks.toml`.

- [ ] ACCEPT: branch protection requires exactly the `CI gate` check; PRs
      from forks are verified with the manual `ci-cd.yml` workflow.
- [ ] ACCEPT: tagged release ran `deploy.yml` end-to-end (image in GHCR, or
      documented why not).

---

## 11. Phase 10 — Docker

**DO**

- Frontend image: multi-stage `Dockerfile.frontend` (deps → build → static
  serve); backend runs in Node with `NODE_ENV=production` and **fails fast**
  on missing `DATABASE_URL`/`JWT_SECRET`/`JWT_REFRESH_SECRET`.
- `docker-compose.yml` = local/one-command stack (frontend, backend, Postgres,
  Redis, nginx single entry on :80); `docker-compose.prod.yml` for
  production overrides. Secrets come from `.env`, **never** baked into images
  (`.dockerignore` excludes `.env`, `node_modules`, `dist` of other services).
- Healthchecks + `depends_on: condition: service_healthy` so migrations/seed
  order is deterministic; backups covered by `backup.yml`.

**FILES** — `Dockerfile.frontend`, `docker-compose.yml`,
`docker-compose.prod.yml`, `docker-compose.scraper.yml`,
npm script `docker:build`.

- [ ] ACCEPT: `docker compose up --build -d` from a clean machine →
      `GET :5000/api/health` healthy, frontend served, Setup Wizard reachable.
- [ ] ACCEPT: `docker compose down -v && up` + seed → working demo (clean
      bootstrap proven, not just a warm cache).

---

## 12. Quality gates — the commands that decide "done"

| Gate | Command | Target / notes |
|---|---|---|
| Lint | `npm run lint` | exit 0 |
| Frontend unit | `npm run test` | exit 0 (Vitest) |
| Backend unit | `cd backend && npm test` | exit 0 (Jest; CI runs `test:ci` with coverage) |
| AI agent | `venv/Scripts/python.exe -m pytest ai-agent/tests -q` | exit 0 |
| Build | `npm run build` | green |
| Bundle budget | `npm run size` | PASS — see §14 numbers |
| Perf (Lighthouse) | `npm run test:perf` | CLS ≤ 0.1 is a **hard** error; perf 95+ / LCP ≤ 1.5s are warnings |
| E2E | `npm run test:e2e` | Playwright, chromium |
| Docs | `npm run docs:build` | exit 0 |
| Anatomy (generated homes) | `python scripts/audit_international_anatomy.py` | sections present |

Evidence rules: report the numbers you measured (e.g. "Vitest 41 passed,
`size` PASS, CLS 0.0000 ×3"). A target that is not met is reported as
**measured + failing**, not omitted — see §14 for the current honest status
of this repo. Not installed here (say *not measured*, never ✅): visual
regression baselines, k6 load tests, mutation testing.

- [ ] ACCEPT: all applicable rows above ran **in this change** and their real
      output is in your report.

---

## 13. Security checklist (every build, before deploy)

- [ ] No secrets in code or images — `.env` only; gitleaks job green.
- [ ] All inputs validated server-side; parameterized SQL; `dangerouslySetInnerHTML`
      sanitized or not used.
- [ ] CORS whitelist (no `*` with credentials); HTTPS only in production;
      security headers on (helmet).
- [ ] Rate limits on auth, payment, upload and AI endpoints; captcha on
      register/reset when configured.
- [ ] JWT 15min/7day with rotation; bcrypt ≥12; RBAC on every mutating route;
      org/tenant filter server-side.
- [ ] Uploads: MIME + size validated (5MB max), stored outside web root.
- [ ] No stack traces/SQL/error internals in any response or console the user
      can see; webhook signatures verified + idempotent.
- [ ] `npm audit --audit-level=high` clean on frontend **and** backend
      (CI job 9).

---

## 14. Performance budgets (they are design constraints)

Enforced by `npm run size` (`scripts/check-bundle-budget.mjs`):

| Metric | Target | Hard gate | Last measured (this repo) |
|---|---|---|---|
| Initial JS (gzip) | < 150 KB | < 200 KB | 193.2 KB (2026-09-28) — headroom ~7 KB |
| CSS (gzip) | < 30 KB | < 50 KB | 24.6 KB (2026-10-06) PASS |
| Largest chunk (gzip) | — | < 300 KB | 219.4 KB `HeroCanvas` (2026-10-06) PASS |
| CLS | < 0.05 | **< 0.1** | **0.0000 ×3** on `/` and `/login` (2026-10-06) PASS |
| Lighthouse perf | 95+ | — | 0.27–0.41 — **measured, failing (WARN)** |
| LCP | < 1.5 s | — | 4.5–10 s — **measured, failing (WARN)** |

Rules learned the hard way in this repo (do not regress):

- Google Fonts load **once**, async, `display=optional` — a duplicate
  `@import` plus `swap` caused +90px reflows.
- Keep `<main>`'s `min-h-[100svh]` in `MainLayout` — it stops the footer
  from mounting visible above the fold (that single commit caused CLS 0.34).
- **`manualChunks` is a trap**: naming a lazily-reachable lib (`three`,
  `recharts`, `framer-motion`) hoists it to first paint. Chunk only large,
  always-initial runtimes.
- Defer heavy boot-time SDKs (Sentry etc.) to idle — TBT/LCP are the current
  red numbers, and boot-time SDK work is the leading suspect.

- [ ] ACCEPT: `npm run size` PASS and `npm run test:perf` exit 0 after your
      change; perf/LCP numbers quoted as measured (they are WARN today).

---

## 15. Deploy & live verification

**DO**

1. Build/test locally first (`lint`, `test`, `build`, `size`); deploy only
   what was verified.
2. Tag → `deploy.yml` (GHCR image + optional SSH), or `docker compose` on the
   target host behind nginx with TLS.
3. **Live verification (mandatory — a 200 is not a pass):**
   - [ ] Open the site in a browser: renders (HTML/JS/CSS content-types sane),
         no console errors, no failed requests.
   - [ ] Critical path actually works: sign in → main action → sign out;
         payment in sandbox end-to-end if the site sells.
   - [ ] Lighthouse on the **live** URL (perf + a11y + CLS) — numbers, not
         impressions.
   - [ ] Auth probes on the real origin: signed-out API → 401, foreign-origin
         mutation → 403, personal data never cached publicly.
4. Final report lists every gate with its real output; anything not run is
   marked *not measured*.

**FILES** — [DEPLOYMENT](./DEPLOYMENT.md), [RUNBOOK](./RUNBOOK.md),
`.github/workflows/deploy.yml`, `nginx/`.

---

## 16. Updating an existing website (delta path)

Updates are the common case — run this instead of phases 1–10:

1. [ ] State the delta in one sentence (what changes for whom) and check it
       against the design manifest — does it break the brand/identity
       decisions? If yes, revisit Unique Project Playbook first.
2. [ ] Frontend: touch → `lint` + `test` + `build` + `size`
       (bundle headroom is ~7 KB — a chunk crossing 300 KB is a gate failure,
       not noise).
3. [ ] Backend: route/model change → contract test + validation + RBAC
       check; migration → idempotent file + `*.down.sql` (CI applies twice).
4. [ ] Auth/payment touched → re-run §5/§6 acceptance probes (they are the
       most dangerous regressions).
5. [ ] Sidebar/nav changed → `navItems.js` + role gating + mobile drawer
       check (§7).
6. [ ] Motion/logo changed → reduced-motion pass + DesignLint (§8).
7. [ ] Copy changed → i18n keys added in **all** locales, no raw strings.
8. [ ] Re-run the full §12 gate table, then §15 live verification.
9. [ ] CHANGELOG row for the change (`type: desc`, conventional commits).

---

## 17. File map — where every piece of this playbook lives

| Area | Files |
|---|---|
| Frontend shell | `src/layouts/MainLayout.jsx`, `DashboardLayout.jsx` |
| Routes | `src/routes/index.jsx`, `routeConfig.js` |
| API client | `src/services/api.js`, `src/context/AuthContext.jsx` |
| Pages | `src/pages/` (Home, Login, Register, Dashboard, Admin*, Billing, …) |
| Sidebar/nav | `src/navigation/navItems.js`, `navigationConfig.js` |
| Logo/brand | `src/components/common/BrandLogo.jsx`, `src/assets/logos/` |
| Motion | `src/components/motion/` (13 components) |
| Backend entry | `backend/server.js`, `backend/routes/` (34 modules) |
| Backend middleware | `backend/middleware/` (auth, rbac, rateLimit, validateRequest, errorHandler, webhookSecurity, …) |
| Models | `backend/models/` (30 Sequelize models) |
| DB | `database/schemas/`, `database/migrations/` |
| CI/CD | `.github/workflows/ci.yml` (merge gate), `deploy.yml` (tags), `backup.yml` |
| Docker | `Dockerfile.frontend`, `docker-compose.yml`, `docker-compose.prod.yml` |
| Gates | `scripts/check-bundle-budget.mjs`, `scripts/lighthouse.mjs`, `scripts/_cls_probe.cjs`, `.lighthouserc.json` |
| Design/uniqueness | `ai-agent/agent/design_style.py`, `orchestrator.py`, `docs/UNIQUE_PROJECT_PLAYBOOK.md` |

---

## 18. The master checklist (copy this into the PR description)

```markdown
## Website build checklist — <project> (<date>)
Brief/manifest: [ ]  Frontend: [ ]  Backend: [ ]  DB+migration: [ ]
Auth: [ ]  Payments: [ ]  Dashboard/sidebar: [ ]  Logo+motion: [ ]
i18n/RTL/a11y/SEO: [ ]  CI: [ ]  Docker: [ ]  Security: [ ]
### Evidence (real command output)
lint:   test:   backend:   build:   size:   perf(CLS):   e2e:   
### Live verification
URL:   console clean:   critical path:   sandbox purchase:   
Not measured / known red:
```

Anything you cannot fill with real output stays blank or says **not measured**.
That honesty is the difference between a checklist and theater.
