# AGENTS.md — LumicorePro Core

> v7.13 (Marketplace Delivery) | audit remediation in progress (target v8.0)
> Monorepo: React 19 + Vite + Tailwind 3 | Express + PostgreSQL + Redis | Python FastAPI AI Agent

---

## 1. MONOREPO STRUCTURE

```
src/{components/{ui,common,navigation,forms,ecommerce,dashboard,ai,auth,business,motion,editor},pages,layouts,hooks,context,services,routes,styles,utils,icons,templates,i18n,config,data,navigation,pwa,__tests__}
backend/{config,routes,middleware,models,services,utils,__tests__,server.js}
ai-agent/{agent,providers,config,database,utils,tests,main.py,server.py}
backend-library/{shared,ecommerce-base,electronics-backend,fintech-backend,saas-backend,master-express-backend}
{database,schemas,project-rules,docs,k8s,nginx,e2e,scripts,registry,templates}
```

### Read Before (By Area)
| Area | Files |
|------|-------|
| Components | `project-rules/COMPONENT_STANDARDS.md` |
| Architecture | `project-rules/ARCHITECTURE.md`, `PROJECT_RULES.md`, `MASTER_PROMPT.md` |
| Auth | `src/context/AuthContext.jsx`, `backend/middleware/auth.js` |
| API | `src/services/api.js`, `backend/routes/` |
| Routes | `src/routes/index.jsx`, `routeConfig.js` |
| Style | `tailwind.config.js`, `src/styles/globals.css` |
| DB | `database/schemas/`, `backend/models/` |
| AI | `ai-agent/main.py`, `server.py` |

Architecture: `User → React → Hook/Context → Axios → Express → PostgreSQL/Redis`

---

## 2. AGENT BEHAVIOR

- English, brief (1-3 lines), no filler, no emojis. Decisive — ask only for breaking/architecture/security decisions
- `read_file` before edit; batch independent reads. `edit_file` for changes; `execute_command` only for npm/git/docker/python
- 3-5 lines context in `old_string`; preserve style; remove dead code; never leave broken files
- Lint after frontend, test after logic, build after major. 3 failures → stop, report blocker
- Ignore: `node_modules/`, `dist/`, `build/`, `.git/`, `venv/`, `__pycache__/`, `.pytest_cache/`, `coverage/`

---

## 3. SECURITY

- Secrets `.env` only. Validate vs `.env.example`. No hardcoded keys
- Validate all inputs. Parameterized SQL. Sanitize `dangerouslySetInnerHTML`
- HTTPS production, CORS whitelist, rate limit auth/AI, JWT 15min/7day refresh, bcrypt 12+
- Never expose stack traces. Validate MIME/size on uploads
- Checklist: No secrets, no debug logs, input validated, no stack traces, CORS/auth set, rate limits
- **Webhooks: verify the provider's signature header against the RAW body, fail-closed.** Never read a signature from the body, never `if (sig && sig !== hash)` (that accepts unsigned events), and never trust a posted status — Mollie-style providers require re-fetching the payment from their API. Secret missing ⇒ reject, never skip. (2026-10-23: Flutterwave/Razorpay/Square/MercadoPago/Paytm shipped inverted or missing checks; LiqPay signed the wrong payload.)
- **Order-scoped endpoints must call `orderOwnershipError(order, req.user)`** (`backend/utils/orderOwnership.js`) whenever a client sends an `orderId` — a missing check is an IDOR (fixed in 4 payment routes on 2026-10-23).
- `TRUST_PROXY_HOPS` controls `trust proxy` (default 0 = don't trust X-Forwarded-For). Set 1 behind nginx/ingress so IP rate limits are per-client; never `true`.
- **Dependency audit: high/critical must be 0** in `backend/` and root (`npm audit --omit=dev`). 2026-10-23: removed unused `square`, `awilix`, `sharp` (9 highs → 0) and upgraded nodemailer to 10.x. 24 moderate remain in Sentry's transitive OpenTelemetry — accepted risk, revisit when `@sentry/node` permits. Never keep a package that nothing imports.
- **Shared table ⇒ a vertical discriminator is mandatory.** `orders` is written by the store and the restaurant; `orders.source` (`constants/orderSources.js`, migration `008`) is what every listing, admin mutation and aggregate filters on. Creating through `orderService.createOrder(user, { source })` requires it. `bookings` is shared with healthcare via `metadata.type` + nullable healthcare columns — see §4 Database.
- **Never spread `req.body` into a create/update.** Spread after `user_id: req.user.id` lets a caller re-parent a row (address POST/PUT fixed 2026-10-24); `coupon PUT` let `usageCount` be reset. Whitelist writable columns (`pickAddressFields`, `pickCouponFields`) and treat ids/timestamps/owners/ledger counters as server-owned.
- **Tenancy applies to aggregates and caches, not just lists.** Every analytics/report/count/SUM query carries `tenantWhere(req)`; `User` has no org column so it uses `current_org_id`. Search cache keys include `tenantCacheKey(req)` — an org-blind key served one tenant's results to another (fixed 2026-10-24). `x-org-id` is honoured only for anonymous storefront calls.
- **express-validator 7 `.if(condition)` receives `(value, meta)`**, so the request is `meta.req` — `(_v, req) => req.body.x` is always falsy and silently disables the chain (a delivery order shipped with no address, 2026-10-24). Other guards: numeric route params → `parseInt` NaN reaches PostgreSQL as an error, validate/clamp first (`Math.max(1, parseInt(x) || 1)` does NOT clamp negatives).

---

## 4. DEVELOPMENT STANDARDS

### Style
2-space, single quotes, semicolons, 100-char max, trailing commas ES5, arrow callbacks

### Naming
Components `PascalCase`, utils `camelCase`, hooks `use+camelCase`, const `UPPER_SNAKE`, dirs `kebab-case`, env `VITE_`

### React
Functional only. Proper deps/cleanup. Context/Zustand/Query for state. Axios interceptors. Error boundaries. `React.lazy()` route-level. `useMemo`/`useCallback` for expensive ops.

### Tailwind
Utility-first. Config tokens only (no hardcoded hex). `dark:` prefix required. Mobile-first. `transition-all duration-200`. Respect `prefers-reduced-motion`. RTL via `rtl.css`.

### Components & UI/UX
Max 300 lines. Props: `variant`/`size`/`disabled`/`className`. States: default/hover/active/disabled/loading/focus/error. A11y: `aria-*`, keyboard nav, visible focus. Real Lucide icons (`lucide-react`) paired with text labels. Real curated high-res Unsplash images with `LazyImage` & `alt`.
- **Icon props are forwardRef objects, not functions.** `leftIcon`/`rightIcon`/`icon` props receive lucide's forwardRef components — render them as components (`<Icon />`), never as React children. `typeof Icon === 'function'` is false for forwardRef; the fall-through white-screened ProductListing with React error #31 (fixed in `GlassButton`, regression test in `src/__tests__/components/GlassButton.test.jsx`).
- **Branding**: Never plain text. Always generate dynamic vector SVG logos (`UniqueLogo` / `BrandLogo`) with geometric symbols & dual-color gradients.
- **Footers**: Never a single plain line. Always multi-column professional footers (`ModernFooter`) with live status badge (`🟢 99.99% Operational`), newsletter signup, categorized sitemap, and social links.
- **Motion UI**: Bento grids (`BentoGrid`), Spotlight cursor illumination (`SpotlightGrid`), 3D tilt (`HolographicCard`), border beams (`BorderBeam`), and text morphing (`TextMorph`).
- **Variants**: primary/secondary/success/danger/warning/info/outline/ghost/glow. Sizes: xs/sm/md/lg/xl.

### Backend
Response: `{success,status,message,data,timestamp}`. Errors: `success:false` + code + user message. Middleware: auth → validate → route → error. Sequelize models + validation. Structured logging.

### Database
Snake case. Foreign keys + constraints. Index queried columns. Versioned migrations. Soft deletes (`deleted_at`).

- **A route may only write columns the model declares.** The restaurant reservation path once wrote `title`/`startAt`/`org_id` into `bookings`; Sequelize drops unknown attributes, so the insert failed or saved nothing. Migration `008` added the real `bookings.org_id/startAt/metadata` columns and relaxed the healthcare-only NOT NULLs (`doctor_id`, `reason`, `patientInfo`); keep model and migration in step.
- **Reservation slots are instants, not wall clocks.** `utils/reservationSlot.js` converts `date` + `HH:MM` in `RESTAURANT_TIMEZONE` to UTC (`startAt`), validates calendar dates with a round trip, and decides overlap with `[start, start+duration)`. Capacity/party ceilings come from `RESTAURANT_TABLE_CAPACITY` (8) and `RESTAURANT_MAX_PARTY_SIZE` (20), seating length from `RESTAURANT_SEATING_MINUTES` (120).
- **Booking state is a ledger.** Patients may confirm/cancel only; `completed`/`no-show` are clinic-side and terminal states cannot be reopened by a patient. Cancelling a booking with collected money flips `paymentStatus` to `refunded` and returns `refundDue` — a cancellation without that trail hid real money.

---

## 5. COMMANDS

| Command | Action |
|---------|--------|
| `npm run dev` | Frontend (5173) |
| `npm run build` | Production |
| `npm run lint` | ESLint |
| `npm run test` | Vitest |
| `npm run test:e2e` | Playwright |
| `npm run dev:full` | Frontend + Backend |
| `npm run dev:all` | All (Front+Back+AI) |
| `npm run test:backend` | Jest |

---

## 6. TESTING

| Type | Tool | Location | Target | Measured (2026-10-24) |
|------|------|----------|--------|------------------------|
| Frontend | Vitest 5 | `src/**/__tests__/` | 80%+ | **62.74% stmts (honest full-tree) — 1020 tests / 128 files, ratchet gate active** |
| Backend | Jest | `backend/__tests__/`, `backend/tests/` | 80%+ | **74.79% statements (5155/6892) — 82 suites / 1903 tests, ratchet gate active** |
| AI agent | pytest/unittest | `ai-agent/tests/` | 80%+ | **1385 tests + 109 subtests green** (incl. factory / live-verify / demo-video / design suites) |
| E2E | Playwright | `e2e/` | Key paths | **39 tests / 8 files green (2026-10-24, port 5199)** — nav, auth, a11y, products, routes, agent-control-center, generate flow, checkout/billing |
| Mock | MSW | `src/test/` | As needed | In place |

Targets are goals, **not** the current state. Measured on 2026-10-24:
backend coverage is 74.79% statements (5155/6892 statements, 67.11% branches,
69.29% functions, 75.48% lines; 1903 tests / 82 suites) against an 80% target —
up from 71.9% on 2026-10-23. Frontend coverage is 62.74% statements over the full
`src/` tree (1020 tests / 128 files; 59.62% branches, 56.29% functions, 64.93%
lines) — the earlier 51.1% figure predates waves 4/5; an older "~41%" figure only
counted test-loaded files and was retired as dishonest accounting.

**Both suites now have ratchet gates** (`coverageThreshold` in
`backend/jest.config.js`, `coverage.thresholds` in `vite.config.js`, floors set
~1 point under the measured baseline). CI fails below the floor, so coverage
can only go UP — raise the floor whenever tests are added. Never lower or
delete a floor to make a run pass; that is the regression these gates exist to
prevent. Run the backend suite from `backend/` with
`node --experimental-vm-modules ./node_modules/jest/bin/jest.js --coverage`;
the root `npm run test:backend` script is not the instrumented path.

`server.js` only listens when executed directly (`node server.js`) — tests
import `app` via supertest without binding a port. Do not reintroduce an
unconditional top-level `server.listen`; it caused EADDRINUSE flakes whenever
a dev server was already running.

E2E serves the production build via `scripts/e2e-server.mjs` on `E2E_PORT`
(default 5173). On a dev machine 5173 is often already occupied by ANOTHER app,
and `reuseExistingServer` will then test the wrong app — verified in this repo:
a BlogForge instance answered every request while specs "passed" and the real
LumicorePro pages were never loaded. If E2E results look impossible or pages
don't match the codebase, re-run on a fresh port: `E2E_PORT=5199 npx playwright
test`. `reducedMotion: 'reduce'` is set globally for E2E so axe contrast scans
don't measure mid-fade opacity (false 3.58:1 reports on tokens that are 4.6:1
at rest); keep it unless the animation wait is replaced.

Still at 0% or near-0% and worth covering next: `ai.routes.js` (1/47 functions),
`dashboard.routes.js`, `analytics.routes.js`, `playbook.routes.js`,
`upload.routes.js`, `workers/` and `utils/monitoring.js`; the frontend
`src/pages/` + `src/components/` trees are the larger gap. Search, audit and
coupon routes gained suites on 2026-10-24.
Every money-moving gateway now has a suite (Stripe, PayPal, Razorpay, Square,
Flutterwave, Paytm, Mollie, MercadoPago, LiqPay, Paddle, bKash) and HTTP routes
(`backend/routes/payment-gateways.routes.js` for the non-Stripe/PayPal/Paddle/
Razorpay ones) — when touching one, read its "Signing/webhook" header comment
first: several shipped with inverted or missing signature checks (fixed
2026-10-23). Webhook env vars are documented in `backend/.env.example`.

Mock externals (MSW). Test error paths. Isolated tests. Descriptive names. Await async.

---

## 7. PERFORMANCE

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Lighthouse Performance | 95+ | — |
| Bundle (gzip) | <200KB | <300KB |
| Initial JS (gzip) | <200KB | 200KB enforced |
| CSS (gzip) | <30KB | <50KB |
| LCP | <1.5s | — |
| CLS | <0.05 | <0.1 |

- `React.lazy()` + `Suspense` for routes. Vendor chunking. Tree-shake. Lazy-load Three.js/GSAP/Lottie/Recharts
- WebP preferred, `loading="lazy"`, `font-display: swap`
- `useMemo`/`useCallback` for expensive ops. Windowing >100 items. Debounce 300ms. Animate `transform`/`opacity` only
- React Query: `staleTime: 5min`, `gcTime: 30min`. SW: hashed assets indefinite. `localStorage` for prefs only

Measured 2026-10-24 (`npm run size`): initial JS **198.8 KB** gzip across 18 chunks, CSS 26.1 KB, largest chunk `HeroCanvas` 219.4 KB — **passes all enforced budgets** (200 KB initial JS, 50 KB CSS, 300 KB largest chunk) with ~1.2 KB headroom. `CookieConsent`, `ToastRegion`, `Analytics` and the below-the-fold `ModernFooter` were moved behind `React.lazy` (all queue state or render off-screen, nothing is missed on mount). The old 150 KB "JS Bundle" target was retired on 2026-10-23: the mandated stack alone (react+router 92.9 KB, i18next 21.4 KB, lucide 20.2 KB, axios 18.1 KB, react-query 7.9 KB = ~160.5 KB gzip before any app code) made it unreachable without breaking §4 rules, so the target was aligned to the enforced 200 KB gate with the owner's approval. Headroom is tight — treat ANY initial-JS growth as a gate failure, not noise, and lazy-defer UI that is not needed for first paint.

**Manual chunks are a trap on this bundler.** Naming a large lazily-reachable package (`three`, `recharts`, `framer-motion`) in `manualChunks` makes rolldown emit it as a *static* import of the entry chunk, hoisting it onto first paint and negating the lazy boundary. Group only runtimes that are large, always-initial, and slow-moving. Do not name an icon/animation library that lazy routes import.

---

## 8. STATE MANAGEMENT

`UI state → useState` | `Server data → React Query` | `Global UI (theme/auth) → Context` | `Complex frequent (cart/filters) → Zustand` | `URL-driven → searchParams`

### Context
For: Theme, Auth, Currency, i18n, Notifications. Not for: frequent changes/server state/complex logic. Split contexts. Custom hooks to hide API.

### Zustand
For: Cart, filters, chat, dashboard. One store/domain. Immer for mutations. `state => state.property` select pattern.

### React Query
`staleTime: 5min`, `gcTime: 30min`, `retry: 2`. `useMutation` for POST/PUT/DELETE. Optimistic for cart/like/toggle. Prefetch on hover.

---

## 9. ACCESSIBILITY (WCAG 2.1 AA)

- Keyboard: Tab/Enter/Escape. Skip-to-content link first. Landmarks: `<header>`, `<main>`, `<nav>`, `<footer>`
- Contrast: 4.5:1 text, 3:1 large/UI. `alt` on `<img>`, `aria-label` on SVG icons
- Focus: visible indicators. `aria-live` dynamic updates. `role="alert"` for errors
- Forms: labels, `aria-describedby`, fieldsets, `autocomplete`, proper `type=`. Errors: inline, specific, actionable
- Icons: Always with visible text. Icon-only → `aria-label` + tooltip
- Motion: Respect `prefers-reduced-motion`. No auto-play motion, no flash >3/s, manual carousel controls

---

## 10. i18n + RTL + CURRENCY

- Strings: `t('key')` via i18next. No hardcoded JSX strings. Locales: `src/i18n/locales/*.json`
- RTL: `dir="rtl"` on `<html>`. Logical CSS properties (`margin-inline-start`). `rtl:` Tailwind prefix. Flip arrows/chevrons
- Currency: `CurrencyContext.jsx`. Numbers in DB. `Intl.NumberFormat` display. USD/EUR/GBP/PKR/INR/AED/SAR

---

## 11. FORMS

React Hook Form + Yup. Frontend + backend validation (never trust client). Inline field errors. Disabled submit during async. Patterns: strength indicator, debounced search (300ms), drag-drop with type/size validation, multi-step with progress.

---

## 12. REAL-TIME + PWA

### WebSocket (`useSocket.js`)
Reconnect: exponential backoff 1-30s. Heartbeat 25s. Namespaced events (`order:created`). JWT auth. Disconnect on unmount.

### PWA
`public/sw.js` (precache shell, runtime API). `public/manifest.json`. Nav: cache-first, API: network-first, Assets: cache-first stale-revalidate. 50MB image cache.

---

## 13. MONOREPO RULES

- Frontend → Backend: OpenAPI spec. Frontend → AI: REST (FastAPI). Backend → DB: schema-driven
- API versioning: `/api/v1/`. Shared types. Gradual migration for breaking changes
- `.env.example` = source of truth. Validate at startup. `VITE_` prefix frontend

---

## 14. CODE REVIEW CHECKLIST

Rules followed | No dead code | No `any` | No `console.log` | A11y | Responsive | Dark mode | Error handling | Loading states | No secrets | Validated inputs | No re-renders | Tests | Lint + Build pass

---

## 15. ERROR HANDLING + RECOVERY

### Agent
Edit fails 3x → stop, report. Timeout → retry once, alt approach. Corrupted → `git checkout -- file`

### Application
ErrorBoundary per feature. Friendly fallback + retry. 401→login, 403→denied, 404→not found, 422→inline validation, 500+→generic + log. Network: exponential backoff (3 retries max).

### Images
Real `.jpg/.png/.webp/.svg` from `src/assets/`. No placeholders/dummies. 5MB max, 100x100 min. SVG→WebP→PNG→JPG. `loading="lazy"` below fold.

---

## 16. DEVELOPMENT WORKFLOW

1. **Explore:** Read existing code
2. **Plan:** Define approach
3. **Implement:** Follow standards
4. **Test:** Existing + new tests
5. **Validate:** Lint, build, no regressions
6. **Verify:** Read changed files, check dependents

Refactoring: Never change behavior, update tests, small increments, preserve public APIs.

### Git
`type: desc` (feat/fix/docs/style/refactor/test/chore/perf/security). Feature branches. Small commits. Keep main deployable.

### Docs
JSDoc on public components/functions. Inline comments for complex logic only (why, not what). Update on arch/API/feature changes.

---

## 17. SELLABLE PROJECT DELIVERY (mandatory)

Every **new project** this agent creates must be listable on Gumroad, Lemon Squeezy, ThemeForest, Creative Market, GitHub, and Product Hunt.

- **README.md (required):** product pitch, features, stack, prerequisites, copy-paste Getting Started, env table, structure, scripts, deploy, i18n/compliance, troubleshooting, license. Never a one-liner that only points at INSTRUCTIONS.md.
- **International:** English buyer copy, i18n + RTL, multi-currency, GDPR consent, Privacy/Terms, SEO + OG + JSON-LD, robots/sitemap.
- **Pro UI only:** UniqueLogo/BrandLogo, GlassNavbar, ModernFooter, Lucide + labels, real images, dark mode, motion, mobile-first. No placeholders, no text-only logos, no single-line footers.
- **Zero errors:** no TODO/lorem/dummy keys; lint/build clean; `.env.example` only.
- **Ship with:** LICENSE.md, .gitignore, seller kit when generated via the pipeline.

Rule file: `.cursor/rules/marketplace-ready-projects.mdc`

---

## 18. AI WEBSITE FACTORY — MASTER PROMPT WORKFLOW (MANDATORY)

The complete engine lives in `project-rules/MASTER_PROMPT.md` (READ before any new-project work, alongside the Architecture files). It is binding for website/app creation. Core rules:

### Role
Act as a senior Product Engineer + Creative Director + UX/UI + Frontend/Backend/Motion/3D/A11y/SEO/Performance engineer combined. Never code before understanding the product.

### Final Integrated Pipeline (Part 1 + 1b + 2 + 3)
`Business Analysis → Audience/Persona → Brand Strategy → Reference Intelligence → Industry Playbook → UX/IA → Visual Direction → Design System → Design Benchmark → Implementation → Visual/UX/Conversion QA → Automated Design Scoring → Self-Healing → Performance/A11y/SEO → Live Deployment → Live Verification → Final Report`

### Part 1 — Mandatory Pipeline (never skip conceptually)
`Prompt → Business Analysis → Audience Analysis → Brand Positioning → Content Strategy → Information Architecture → User Journey → Visual Direction → Design System → Page Architecture → Interaction Plan → Technical Architecture → Implementation`

### Part 1b — Reference Intelligence (Design Benchmarking)
Cited references (e.g. "Apple-style clarity, Aesop-style restraint, Stripe-style UX") are never copied. Decompose each into attributes — typography, spacing, navigation behavior, image treatment, motion principles, content density, CTA hierarchy, interaction patterns, brand emotion — then synthesize an original design system carrying those qualities, documenting the source→translation mapping in the project brief. Reference = inspiration attributes, NOT template extraction.

### Part 2 — QA + Critic + Self-Healing + Deployment (mandatory after every build)
`Build Verify → Playwright → Visual Regression → Collapse Detection → Accessibility QA → Responsive QA → Performance QA → External Request Audit → SEO QA → Visual Critic → UX Critic → Conversion Critic → Anti-Generic Critic → Multi-Critic Review → Issue Priority → Self-Heal → Failure Protection → Quality Score → Deployment → Live Verification → Final QA Gate`

Never declare success without evidence. Build succeeded ≠ Website completed. Every project must pass the final QA gate (Part 2 Section 24) before COMPLETE.

### Part 2b — Visual Benchmarkability
Design scoring is measurable, not taste: Visual Quality = Typography 15% + Composition 15% + Spacing 15% + Color 10% + Imagery 10% + Hierarchy 10% + Consistency 10% + Brand Fit 10% + Motion 5% + Originality 10% (total 100). Match implementation against pre-written benchmark targets (typography 9/10, spacing 8/10, density 7/10, distinctiveness 9/10, motion restraint 8/10, CTA 9/10, imagery 9/10) using Playwright screenshots + DesignLint output.

### Part 2c — DesignLint (design Linter like ESLint)
Rules: DL001 wide hero heading · DL002 low CTA contrast · DL003 >4 identical cards · DL004 spacing inconsistency · DL005 too many rounded containers · DL006 too many gradients · DL007 repeated decorative effects · DL008 broken heading hierarchy · DL009 mobile hero too tall · DL010 CTA below fold · DL011 visual density too high · DL012 empty section · DL013 generic placeholder copy · DL014 repeated animation pattern · DL015 brand differentiation too low. Output severity (P1-P3) + code + message; findings feed the self-healing loop.

### Part 2d — Redesign Authority + Design Gate
If visual quality < threshold: DO NOT PATCH ONLY — the agent may redesign hero composition, section order, spacing, card structure, typography scale, CTA placement, interaction model, visual treatment (as long as core requirements stay satisfied). Before deployment: Design Gate — Brand clarity, Visual hierarchy, Typography, Spacing, Originality, CTA clarity, Mobile design, Interaction quality each ≥ 85, else `REDESIGN_REQUIRED`. A project is complete only when TECHNICAL QA + UX QA + VISUAL QA + DESIGN SCORE all pass — never just because it compiles.

### Part 3 — Intelligence + Benchmarking + Playbooks (planning layer inside Part 1)
`Industry Playbook (strategy/ux/pages/components/conversion/content/visual/qa) + Brand Playbook (personality/typography/spacing/motion/color/imagery/interaction) + User Requirements + Reference Attributes → Design Decision Engine → single design spec (hero, navigation, grid, typography, motion, 3d, image_ratio, cta_style, surface_style, card_usage) → saved as machine-readable `design-manifest.json`.`

- Supported industries: ecommerce, marketplace, saas, automotive, food, fintech, portfolio, education, healthcare, real-estate, electronics, industrial, hospitality, entertainment, sports, fashion
- Brand playbooks: luxury, minimal, futuristic, editorial, playful, corporate, bold
- UX anti-patterns to avoid: hidden pricing, excessive modals, weak search, unclear checkout, fake reviews, vague CTA, unnecessary carousels
- **Constraint Resolver:** when requirements conflict (e.g. "lots of animation" vs "super-fast mobile"), resolve per context — desktop: rich motion, mobile: simplified, reduced-motion: minimal; record the resolution in the manifest
- **Design Memory:** `.artifacts/01-business.json → 02-audience → 03-brand → 04-reference → 05-playbook → 06-ux → 07-design → 08-architecture → 09-build → 10-designlint → 11-visual-score → 12-critic-review → 13-qa → 14-deployment` makes every decision traceable for later "change the hero" requests

### Implementation Mapping (use existing modules, no duplicates)
Reference Intelligence → `design_intelligence.py`, `competitive_benchmark.py`, `design_style.py` · Playbooks → `theme_matrix.py`, `design_vault.py` · Blueprint → `planner.py`, `project_mode_engine.py` · Manifest/Memory → `memory_retriever.py`, `.artifacts/` · Benchmark/Lint → `vision_pipeline.py`, `quality_gates.py` · Scoring → `quality_gate.py`, `quality_gates.py` · Self-heal/Redesign → `enterprise_repair.py`, `iterate_engine.py`, `restyle_all.py` · **Existing-repo rebuilds → `repo_reverse_engineer.py`** (read-only scan: stack/routes/models/tests/risks + clean-room reconstruction plan; `python ai-agent/agent/repo_reverse_engineer.py <repo> [--json]`) · **Delivery → `factory_pipeline.py`** (one prompt → generate → build → backend tests → QA → deploy; SSE progress) · **Deploy → `deploy_engine.py` + `live_verify.py`** · **Design system → `design_forge.py`** · **Demo video → `demo_video.py`** (`docs/FACTORY.md`) · Orchestration → `orchestrator.py`, `pipeline.py`. Central orchestrator controls task/state; agents must not randomly modify files outside the plan.

**Delivery is evidence-gated.** `status: live`/`delivered` may only be emitted when
`live_verify.verify_site()` passed (200 + real title + app shell + every referenced JS/CSS
asset + every expected SPA route + optional marker/API health) and, for video,
`ffprobe` reported both streams. A CLI exit code, an empty URL, a Vercel login wall or a
"deployment not found" page is not proof. Unverified artifacts are reported as
`deployed-unverified`/`partial`, never as success. A project with `backend/` is not
"delivered" until the hosted API health endpoint is verified and `VITE_API_URL` was baked
into the build (`--factory-api-url`, `--factory-api-health`): static hosts serve the
frontend only. The verifier also rejects a CSS bundle that still contains `@tailwind`
directives — a deploy without `postcss.config.cjs` returns 200 with an unstyled site
(fixed 2026-10-24). Never lower these gates — they exist because every connector
previously reported `live` on exit 0 alone.

**More gates added 2026-10-27:**
- **`built` ≠ `delivered`.** A run with `--factory-deploy none` reports `built`
  (`verified: false`) even when every stage passed — nothing is hosted, so nothing may
  claim hosting. `deployed`+`verified` is the only path to `delivered`.
- **Generation provider preflight.** `factory_pipeline.provider_health()` live-probes
  the active provider's `/models` before a single file is written; a placeholder key or
  a retired model id (Groq dropped `llama-3.3-70b-versatile` and
  `llama-3.2-11b-vision-preview`) stops the run as `generate: blocked` instead of
  failing minutes into generation. Providers rotate model ids — re-verify before
  changing a default.
- **Generated env contract.** `backend/.env.example` must declare every `process.env.X`
  the generated backend reads (`test_backend_env_template_covers_every_var_the_code_reads`
  enforces it). The generated `models/index.js` accepts `DATABASE_URL` and enables TLS
  automatically, because Neon/Supabase/Render/Railway are TLS-only; a `DB_*`-only config
  connects to localhost and fails in production with no local symptom.
- **`postgres:` not `postgresql:`.** Sequelize v6 parses only the short scheme; Neon
  hands out `postgresql://`, which it then treats as a bare database name with no
  credentials — every query dies with `SASL: … client password must be a string` on a
  URL that `pg` connects with happily. The models template normalises it
  (`test_neon_postgresql_url_reaches_sequelize_as_postgres_scheme`).
- **`models/index.js` loads `.env` itself.** `npm run db:migrate`, the serverless
  wrapper and any script require it directly; when only `server.js` loaded dotenv the
  migration runner silently targeted localhost and the real database was never created
  (`test_migration_scripts_get_the_database_from_the_env_file`).
- **TLS verification is on by default.** `rejectUnauthorized: false` for every
  URL-based connection made managed Postgres an optional-encryption transport a
  network attacker could terminate and read credentials from. Neon, Supabase and
  Render all verify against the system CA store, so the default is strict;
  `DB_SSL_CA` covers a private root and `DB_SSL_INSECURE=true` is the explicit
  opt-out (`test_managed_url_keeps_certificate_verification_on`).
- **Health must prove the database.** `/api/v1/health` runs `SELECT 1` and answers
  503 + `db: disconnected` when Postgres is unreachable; the static `{status:
  healthy, uptime}` version certified a broken deployment as live
  (`test_health_endpoint_proves_the_database_is_reachable`).
- **The deployed bundle must carry the API origin.** Vercel rebuilds the frontend
  from source, so `VITE_API_URL` exported only for the local build never ships: the
  site looks perfect while every form posts to the visitor's own localhost.
  `deploy_engine` publishes it on the project before deploying, and `live_verify`
  fails the run as `api-not-baked` unless that host appears in the shipped JS.
- **CRLF corrupts platform secrets.** Piping a Windows-authored env file into
  `vercel env add` appends `\r` to every value (seen on `BRAND_NAME`,
  `DATABASE_URL`, `GROQ_API_KEY`). Strip `\r` when feeding values, and never print
  them — masking with `sed 's/=.*:/=***:/'` leaks everything after the last colon.
- **A rewritten health target must never be probed.** Git Bash/MSYS turns the
  argument `/api/v1/health` into `D:/Git/api/v1/health`, and `urljoin` reads `D:`
  as a scheme, so the value passes through unchanged and the probe hits a file
  path — the run reported `degraded` while the hosted API was perfectly healthy.
  `api_health_target` drops a drive-absolute value and falls back to
  `GENERATED_API_HEALTH_PATH`, `verify_site` reports
  `api-health-target-invalid`, and `_fetch` refuses any non-`http(s)` target
  (`test_a_shell_rewritten_path_falls_back_to_the_generated_contract`,
  `test_a_health_target_that_is_a_local_path_is_named_not_fetched`,
  `test_nothing_but_http_is_ever_fetched`). Prefer `--factory-api-url` alone —
  the health path is derived, so there is nothing for a shell to mangle.

**Reverse-engineering policy:** `repo_reverse_engineer.py` is a clean-room ANALYSER — it never executes, imports, copies or network-calls the target code, and its output is a plan (structure only). Only run it on repositories you own or are licensed to analyse; rebuilding is behaviour-porting, not source copying.

### Quality Gates (Part 2 hard rules)
- **Evidence-based QA only:** pass badges ("WCAG AA ✅", "LCP <1.5s") only when the actual check ran and the measurement supports it; otherwise report "not measured". Never invent metrics.
- **Independent critics:** the builder never grades their own work. Critics judge only actual artifacts (screenshots, DOM, network timings, console logs, audit output) — a pass without artifact evidence is invalid.
- **Regression detection mandatory:** after every fix, re-verify across all breakpoints (375/768/1024/1440/1920 + reduced-motion) and compare before/after evidence. A fix that breaks another viewport is itself a bug.
- **Measurable design review:** Visual Critic passes concrete checks (hierarchy, whitespace, typography, composition, brand distinctiveness, CTA prominence, repeated patterns) with pass/fail + evidence — not taste opinions.

### Quality Score Targets
- **STANDARD** = 80+ (usability, clean design, speed)
- **PREMIUM** = 88+ (stronger identity, custom motion, richer imagery)
- **SIGNATURE** = 92+ (custom storytelling, advanced interaction, editorial layouts)

### Anti-Generic Design
No gratuitous glassmorphism, gradient text, floating cards, glow, particles, blur, parallax, giant headings. Every decorative element must justify hierarchy/storytelling/interaction/emotion/usability or be removed. Never reuse one visual formula on every project.

### 3D Is Optional
Use only when it improves understanding/emotion/storytelling/value. Otherwise choose video / editorial / typographic / UI-preview / minimal hero. Always: mobile fallback, reduced-motion safe, no zero-height canvas.

### Foundations Required
- Semantic color + design tokens (no random hex/colors)
- Typography engine matched to brand (max 2-3 fonts, coherent scale)
- Real product functionality (cart/checkout/auth/filters/builders) with full loading/success/error/empty/retry
- UX journeys: START → ACTION → RESPONSE → NEXT → SUCCESS → ERROR → RECOVERY
- Explicit responsive intent for 320→1920px, WCAG AA, `prefers-reduced-motion`
- Zustand (client) + React Query (server) only; no unnecessary global state
- SEO: honest JSON-LD + OG + sitemap; images sourced/downloaded/optimized/verified locally
- Self-healing loop for all issues; failure protection after 3 attempts
- Delivery package: README, LICENSE, QA report, performance report, a11y report

### Quality Bar
Clearer hierarchy, stronger brand, better UX, deliberate typography, restrained effects, coherent system — over more effects, more pages, more 3D, more code.

---

## 19. CHANGE LOG

The full history lives in [`CHANGELOG.md`](./CHANGELOG.md). It is deliberately not
inlined here: AGENTS.md is loaded into every agent session as instructions, and the old
inline changelog pushed the file past the workspace instruction budget, which silently
truncated its final sections (this one included).

| Date | Ver | Summary |
|------|-----|---------|
| 2026-10-24 | 8.30 | **Factory v2**: one-prompt delivery (`--deliver`), SSE progress, brand-derived design system (4 archetypes/fonts/radius), Groq/xAI providers with custom base URLs, free gTTS narration fallback, CSS-processing deploy gate, in-place regeneration; generated apps get a real contact API, schema, backend tests, PostCSS config |
| 2026-10-24 | 8.29 | **Website Factory**: build → backend tests → browser QA → deploy → live verification → 2-minute demo video, all evidence-gated; Vercel/Netlify/Railway/Pages connectors no longer report live without a verified URL; real marketing pages + working contact API in generated sites; 1351 AI tests |
| 2026-10-24 | 8.28 | Vertical isolation (`orders.source` + migration 008), restaurant order/reservation contract + 175 tests, booking overlap/role/refund ledger fixed, address/wishlist/cart/business/search/audit/coupon security gaps closed, backend 82 suites / 1903 tests / 74.79% stmts (floors raised), AI agent 1317 tests |
| 2026-10-23 | 8.26 | Wave 3: frontend coverage 27.5%→51.1% (783 tests / 114 files), 20+ UI bugs fixed (5 white-screen icon crashes, Chat send crash, Generate 429 crash, Card/Button asChild, honest dashboard scores, error+retry states, template data/i18n), **reverse-engineering module** `repo_reverse_engineer.py` (clean-room, 12 tests) added to the agent |
| 2026-10-23 | 8.25 | Wave 2: 16 gateway HTTP routes wired (fail-closed webhooks), frontend coverage 15.1%→27.5% (491 tests), 20 real UI bugs fixed (SocialLogin/password-page crashes, terms enforcement, SEO alternates, form a11y), bundle 196.1 KB PASS |
| 2026-10-23 | 8.24 | Wave 1: payment gateways fully tested (~205 tests) + 15 real gateway bugs fixed (webhook forgery, refund endpoints, zero-decimal currency), IDOR fixed in 4 payment routes, TRUST_PROXY_HOPS, frontend coverage 15.1% |
| 2026-10-23 | 8.23 | Quality-gate hardening: coverage ratchets enforced (backend 57.7%, frontend 13.1% honest full-tree), CI runs main backend + bundle budget, EADDRINUSE test fix, GlassButton forwardRef-icon crash fixed (React #31 white-screen), 4 GB legacy tree removed, 8 E2E specs |
| 2026-10-03 | 8.0 | Audit remediation: repo hygiene + `.gitignore`, P0 email-logger crash fix, CI gate un-masked, security / tenancy / AI-agent / frontend / ops workstreams |
| 2026-09-24 | 7.13 | 10 vertical AI-agent SaaS products shipped — 69/69 full-stack packaged |
| 2026-09-21 | 7.12 | Full-stack delivery completed — 59/59 packaged with honest manifests |
| 2026-09-18 | 7.11 | Per-brand content pipeline + comparison table + full routes 43/43 |
| 2026-09-17 | 7.10 | System-level anatomy verification + changelog honesty inventory |

Older entries: see `CHANGELOG.md` or `git log`.
