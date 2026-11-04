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
- **Footers**: Use a composed multi-column footer with brand identity and real route links. Only show newsletter, social, language/currency or status controls when backed by working behavior and owner-supplied evidence. Never fabricate uptime, certification, testimonials, prices or payment availability.
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
| Backend | Jest | `backend/__tests__/`, `backend/tests/` | 80%+ | **74.8% statements (5158/6895) — 82 suites / 1903 tests, ratchet gate active** |
| AI agent | pytest/unittest | `ai-agent/tests/` | 80%+ | **1616 tests + 123 subtests green** (2026-10-27; incl. factory / live-verify / deploy / schema / demo-video / design suites) |
| E2E | Playwright | `e2e/` | Key paths | **39 tests / 8 files green (2026-10-24, port 5199)** — nav, auth, a11y, products, routes, agent-control-center, generate flow, checkout/billing |
| Mock | MSW | `src/test/` | As needed | In place |

**The AI agent suite runs under pytest, and only pytest.** `unittest discover`
collects only `TestCase` subclasses — measured 2026-10-29 it found 774 tests
while pytest collected 2110, so 1336 tests (including every engine added after
2026-10-28) silently never ran. `ai-agent/tests/test_ci_workflow.py` reads
`.github/workflows/ci.yml` and fails if the runner regresses. Do not add a
`unittest` collection command to any workflow, and do not disable that test.

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
- **A CI step must exercise the behaviour it certifies.** A workflow leg that
  runs `npm ci` against a gitignored path, or calls `npm run x` on a package
  that does not define `x`, cannot pass on a clean checkout and proves nothing
  until someone notices. `ai-agent/tests/test_ci_workflow.py` parses the
  workflow and asserts every invoked script exists in the target package.
- **A gate that always exits 0 is not a gate.** `verify_delivery_builds.py`
  returned 0 unconditionally until 2026-10-29, so no product could ever fail
  it. Verification scripts exit non-zero on FAIL, and report
  `not measured` (never a silent pass) when the tool or environment needed to
  measure is absent.
- **Ratchet floors only fall.** `scripts/lint_ratchet.py` and
  `ai-agent/lint-baseline.json` record the measured ruff and bandit backlog
  (ruff 300, bandit_high 11, bandit_medium 38 at 2026-10-29). Raise a floor
  only when the backlog genuinely grows for a reason recorded in the commit;
  never raise one to make a run pass.
- **`delivery/` is build output, `products/sell-today/` is source.** Delivery
  verification runs on `products/sell-today/` with `--layout frontend`; a gate
  that reads `delivery/` is measuring an artifact, not a product.
- **A verification script must not mutate what it measures.** Cleanup removes
  only files the run created (`node_modules/`, a lockfile that did not exist
  before); a tracked `package-lock.json` is product source.

### Prompt-controlled app generation

| Request | Generated surfaces |
|---------|--------------------|
| Website | `frontend/`; no mobile project |
| Web app | Authenticated records app in `frontend/` |
| App/mobile | Expo project in `mobile/`; no `frontend/` |
| Website and app | Website plus Expo project |
| PWA | Adds PWA files to a requested web surface; it does not create a web surface |

- `app-contract.json` is the authoritative `{version, web, pwa, mobile}` contract. Keep its values consistent with generated files and factory stages. A contract must request at least one client surface: `web: "none"` with `mobile: null` fails closed, and `pwa: true` requires a web surface.
- Stage verdicts in `.factory/report.md` are literal: `PASS` is measured evidence, `SKIPPED` means the surface was not requested or could not run, and `NOT MEASURED` means the platform is outside this pipeline (iOS). An app-only run never films the API host — `video` is `SKIPPED`.
- A deliberate skip is a disclosure, never a gate. A stage recorded as skipped/blocked/not_measured must appear in the handoff's "Not proven" block, and the status gates must not re-read that skip as a failure — an unavoidable skip caps every delivery on `partial`.
- New record IDs are client-generated UUIDs. Backend create operations are idempotent for a repeated ID; do not create duplicate rows on retry.
- Every generated surface ignores its own build output. `mobile/.gitignore` covers `node_modules/`, `.expo/`, `dist/`, `/android/`, `/ios/`, `.maestro/test-results/` (written by `maestro test` inside the tracked flows directory), signing material and `.env*`; `frontend/.gitignore` and `backend/.gitignore` do the same for their trees. A delivered project that tracks `expo prebuild` output commits a customer's toolchain into their repository.
- `--android-toolchain check` only checks installed tools. Installation requires the explicit `--android-toolchain install`; accepting SDK licenses additionally requires `--accept-licenses`. Generation and verification never install the toolchain automatically.
- Android verification fails closed: Expo export and TypeScript, debug APK build/metadata, emulator boot/install/launch, clean logcat, and Maestro flows must pass. Missing tools or failed steps cannot be reported as verified.
- A debug APK is a deliverable only when it carries its own JavaScript. `@react-native/gradle-plugin`'s `TaskConfiguration.kt` registers `createBundle<Variant>JsAndAssets` for non-debuggable variants only, and `react.debuggableVariants` defaults to `['debug','debugOptimized']`, so a stock `assembleDebug` produces an APK that installs, launches, and renders the redbox "Unable to load script. Make sure you're running Metro or that your bundle 'index.android.bundle' is packaged correctly for release." Measured on proof8: the 74,101,673-byte APK contained `assets/app.config` and `assets/app.fingerprint` and no bundle at all, yet `steps.gradle.ok=True`. Enforced: `mobile_verify._bundle_js_in_debug_build` writes `react { debuggableVariants = [] }` into the prebuilt `mobile/android/app/build.gradle` after `expo prebuild --clean` (a *commented* `// debuggableVariants = [...]` in Expo's own template is not a setting), and `_apk_js_bundle` refuses any APK whose archive has no `assets/*.bundle`, so `build_apk` fails with the Metro explanation instead of reporting success; the accepted bundle name is recorded as `js_bundle` in the report and `apk.json`. An APK that needs Metro is not a product, and a passing Gradle exit code plus a large file certifies nothing about startup.
- The proof APK builds the target AVD's own image ABI (`mobile_verify._avd_abi` reads `abi.type` from `config.ini`, passed as `-PreactNativeArchitectures=`); the chosen ABI is recorded in `apk.json`. Building all four ABIs quadruples native compile time and disk and dies inside `mergeDebugNativeLibs` with "not enough space on the disk" long before any app defect is reached. Build all ABIs only when the AVD ABI is unknown.
- The mobile stages consume `android_toolchain.toolchain()` (filesystem paths). `check_environment()` is readiness booleans for the CLI only; passing it into `build_apk`/`verify_emulator` makes Gradle receive `ANDROID_HOME=...\mobile\android\True`. `mobile_verify._toolchain_paths` rejects non-path or missing values as `blocked`, and test fixtures must use the path shape.
- Windows native builds need an SDK CMake package whose `ninja` is long-path aware (1.11+). React Native codegen object paths embed the absolute source path twice (~321 characters), which a 1.10.2 ninja cannot even `stat`; `LongPathsEnabled=1` does not help a binary that is not `longPathAware`, and installing `cmake;3.31.6` does not change what AGP picks because its built-in default is 3.22.1. `android_toolchain._resolve_cmake` returns `(package, gap)` and reports no usable CMake when any installed package is unusable, so the readiness gate blocks before a 13-minute Gradle build instead of failing inside it. The returned path is readiness evidence only — Gradle still selects its own CMake.
- A readiness probe never runs without a bound: `android_toolchain._run` takes a `timeout` and every read-only probe (`java -version`, `emulator -list-avds`, `ninja --version`) passes `_PROBE_TIMEOUT`, while installs pass none because sdkmanager downloads for minutes. `check_environment()` blocks a delivery, so an unbounded probe turns one wedged binary into a hung factory with nothing on screen.
- An emulator boot is bounded by the AVD's own disk demand before it starts. `mobile_verify._emulator_disk_gap` reads `disk.dataPartition.size` from `<avd_home>/<avd>.avd/config.ini` and requires 120% of it plus a 1 GB reserve, because that is the emulator's own rule (measured: a 6,144 MB partition asks for 7,372.80 MB free) and a boot that does start keeps writing qcow2 clusters onto the volume that must also take the APK install and the evidence. proof8 and proof9 both burned a completed APK build to reach that wall; the gate now reports `blocked` with the free/needed figures. A proof AVD may declare a smaller partition, but whatever it declares is what the gate measures — and the size belongs in the evidence, not in a footnote.
- A boot budget is a measurement, not a round number. `mobile_verify.verify_emulator` polls `sys.boot_completed` against `_BOOT_TIMEOUT_SECONDS = 900` and records `boot_seconds`; the earlier 240-second deadline was copied from nothing — measured on an 8 GB host with 42 MB of free RAM, the cold boot completed about six minutes after launch, two minutes after that deadline had already reported failure. A budget shorter than a cold boot on the machine that runs the stage turns a healthy emulator into a failed verdict and makes the operator re-run a 17-minute build for the same false answer. The same rule covers the reason text: `_boot_reason` only names a `FATAL`/`ERROR` line whose message contains a word, because proof10's failure read `did not boot within 240 seconds: }` — the closing brace of the emulator's own `Args {…}` dump.
- A launch verdict belongs to the app under test, not to the device. Measured on a real boot of `com.lumicore.northstar`: host memory pressure produced `ANR in com.google.android.gms`, `ANR in com.android.phone` and `ANR in com.google.android.googlequicksearchbox:search`, while the app's own failure — `E/unknown:ReactNative: java.lang.RuntimeException: Unable to load script` — sat at line 2797 of a 4,052-line logcat, outside the 4,000-character evidence window `_capture` keeps. A whole-device pattern scan (`_clean_logcat`, now deleted) was therefore simultaneously a false positive and a false clean. Enforced: `_app_pid` resolves the process with `adb shell pidof <package>` and a launch that leaves no process fails as `… is not running after launch; the app process exited` before any log or Maestro call; `_app_logs` reads the app's own `logcat -d -v brief --pid=<pid>` plus `-b crash` and `-b events`; `_app_crash_reason` attributes `am_crash`/`am_anr` and crash-buffer entries to the package instead of pattern-matching anywhere, and reports `Unable to load script` as the APK defect it is; `_app_logs_readable` fails closed if a buffer cannot be read, because silence is not evidence of a clean start.
- `process.terminate()` on the emulator launcher does not stop the virtual machine. Measured after proof10's timeout: `qemu-system-x86_64-headless.exe` was still running and went on to boot (`sys.boot_completed=1`, `bootcompleted.ini` written at 04:53 for a 04:47 launch), holding 3,933 MB of committed memory on an 8 GB host and growing `userdata-qemu.img.qcow2` to 825 MB on a volume already at 98% full. Enforced: `mobile_verify._avd_serial` + `_stop_emulator` issue `adb emu kill` only after `adb -s <serial> emu avd name` confirms the device is the AVD this run launched, and a device that survives is reported as `Android emulator did not stop: …` in the failures — otherwise the next run inherits a wedged emulator and a disk it cannot write to, and reports the previous run's failure as its own.
- A blocked stage must state the remedy, not only the condition. `_resolve_cmake` names the offending package, its ninja version, and the `sdkmanager --uninstall "cmake;<version>"` command; `factory_pipeline` appends that `cmake_gap` to the "Android toolchain is not ready" message. "Not ready: CMake" leaves the operator with a blocked delivery and no way to fix it. Test stubs for these probes return the producer's shape (`SimpleNamespace(returncode, stdout, stderr)` from a fake `_run`) so the version parse, the minimum comparison and the newest-wins choice stay covered.
- A bounded command capture keeps the head as well as the tail (`mobile_verify._capture`, `_CAPTURE_LIMIT`). `aapt dump badging` prints the `package:` line first and a real dump measured 5,971 characters, so tail-only parsing reported a successfully built APK as having no package name. Test stubs for `run` must return the producer's shape (full `stdout`, never a pre-tailed `stdout_tail`) or they certify the bug.
- The capture window is never the only copy of a failure diagnosis. `maestro test` spends its console on ANSI banners, so proof12 recorded `Maestro smoke flow failed` with nothing but promotion boxes inside the window while the cause — `Assertion is false: "Sign in" is visible` — sat in `<mobile>/.maestro/test-results/<flow>/**/logs/maestro.log`, and the screen it gave up on sat in `screen-hierarchy/`. Enforced: `_maestro_artifacts` reads both after a flow fails, `_maestro_reason` lifts the last verdict line, and `_maestro_dialog` names a device-owned dialog from that hierarchy — proof12's screen held only `System UI isn't responding`, `Close app` and `Wait` with the app under test alive at pid 2563 and a clean logcat, so the verdict says whose hang it was and still fails closed. The reason is appended to the failure line and stored in `maestro/<flow>.json`; when Maestro dies before writing a log (measured on proof12's `records` run, which left an empty timestamp directory) the verdict falls back to `exit code N with no Maestro log on disk`. Both files are copied into the evidence directory and the lifted reason is passed through `_evidence_safe`, because `maestro.log` holds the run's email and password in clear inside the customer's tree — measured: each of the three logs proof12 and proof14 left carries one `using … password …` DEBUG line of 541–543 characters. None of the three carried a verdict marker, so on the producer observed today the credential sits *below* the line `_maestro_reason` lifts; that is a proximity, not a guarantee, and a flow that fails on the sign-in step quotes the account in the verdict itself, which is why the reason is redacted before it reaches the report, `failures` and `maestro/<flow>.json` (test: `test_a_maestro_verdict_that_echoes_the_test_account_is_redacted_where_it_prints`). The whole-device logcat beside it is deliberately not copied (measured 511,583 bytes over 4,052 lines in `D:\mb\live-logcat.txt`, the dump that launch verdict read).
- A stage's measurements are written by the teardown, not by its happy path. proof13 cold-booted the AVD in 125 s (a 1,536 MB guest, where proof12's 2 GB guest took 275 s) and then lost the device during `adb install`, and its evidence directory held only `emulator-boot.log`: the `emulator.json` writer sat *after* the install `return`, so the boot time, the AVD's declared RAM and the volume figures survived only in a scratch driver's stdout. Enforced: `verify_emulator` writes `emulator.json` in the same `finally` as the boot log, from `report` plus the hoisted `device_logs`, so a run that dies mid-way still leaves `booted`/`boot_seconds`/`installed`/`app_pid` and the AVD volume, partition and `avd_ram_size` — and the log windows it actually managed to read, no more. Test: `test_a_run_that_dies_after_the_boot_still_leaves_its_measurements_behind`.
- A Maestro run may only report what the Maestro run itself wrote. `maestro test` appends a timestamped run directory under the *stable* path it was given, and that is measured, not inferred: `D:\mb\app\mobile\.maestro\test-results\smoke\` still holds both `2026-10-29_054800` (proof12) and `2026-10-29_062956` (proof14), and proof14's evidence folder carried proof12's screenshot at `maestro/screenshots/.maestro/test-results/smoke/2026-10-29_054800/…` beside its own. A stage that reads those roots diagnoses and illustrates a run it never performed. Enforced, three ways: `verify_emulator` removes `<mobile>/.maestro/test-results/<flow>` before invoking that flow and, if the removal raises (a wedged earlier Maestro JVM holding the directory), records `Could not clear Maestro <flow> results from an earlier run`, marks that flow `ok=False` with the reason in `error`, and **does not invoke the flow at all** — running it anyway would print the stale verdict and copy the stale PNG; `_maestro_artifacts` takes the newest log and pairs it with the screen hierarchy written in the *same* attempt directory (with no log at all it still reads the newest screen, because a flow can die before opening one); and `_copy_maestro_screenshots` copies PNGs only from the flow directories this run cleared and owns, never by walking `.maestro/`, whose flow YAMLs keep their own anchor images. Tests: `test_an_earlier_runs_maestro_log_cannot_be_read_as_this_runs` (asserted per flow — clearing only `smoke` fails it), `test_a_flow_that_cannot_clear_an_earlier_run_fails_instead_of_misreporting` (asserts the flow was never started, no `reason` was lifted, no stale `.log` entered evidence and `screenshots == []`), `test_a_run_that_never_reached_maestro_claims_no_screenshots`, `test_the_newest_maestro_attempt_supplies_the_verdict_and_its_own_screen`, `test_the_screen_the_run_ended_on_is_read_even_when_maestro_wrote_no_log`, `test_emulator_runs_both_maestro_flows_without_recording_credentials`. Each of the three behaviours was mutated and died (`continue` removed → 1 failure; the redaction wrapper removed → 6; the owned-directory scope reverted to a `.maestro` walk → 3; `_newest` flipped to `min` → 2). The **live leg is outstanding**: proof14 predates these gates, so the next emulator proof must show the clearing and the scoped copy against the real tool before the bullet may be called measured end to end.
- A QA run leaves behind only the captures it measured. `browser_qa` names its report `qa/qa-report.json` and each screenshot `qa/route-<sha256(route)[:16]>-<WxH>.png`, so a narrower run over the same project replaces the report and keeps the earlier run's PNGs: measured in `prompt-controlled-app-system-2026-10-28/website-only/qa/`, 34 captures written 22:45–22:49 by the 35-sample matrix sat beside one capture written 22:51 by the isolated `/pricing@1920` re-run, under a report whose `evidence.viewport_captures` was `1` — a buyer counting files reads 35 proven samples where one was measured, and the 35-sample verdict itself had been overwritten. Enforced: `BrowserQA._finish` derives ownership from the report (`_captures_named_by` walks it for `.png` strings, so scene and PWA captures need no name list) and unlinks what this run did not cite; a capture that refuses to go makes the run fail with `QA capture from an earlier run is still beside this report: <name> (<Type>)`. The prune runs in `_finish`, which the setup path reaches even when the run died before opening a browser, so a failed run leaves no half-mixed evidence either. Tests: `test_a_qa_run_leaves_only_the_captures_it_measured`, `test_a_capture_that_cannot_be_removed_keeps_its_run_from_being_believed` (the blocker is a real `OSError` from a directory named `stale.png`, not a patched `unlink`).
- Guest RAM is disclosed, never gated, and the host's free memory is the real mobile rig limit. `avd_ram_size` is copied verbatim from the AVD's own `config.ini` into `emulator.json` and is never a reason to block: host free memory swings from 0.07 GB to 1.48 GB within minutes on this 7.89 GB machine, and refusing a boot on a figure the emulator never asked for would fail deliveries it could finish. The measurement that settled the cause: proof12 hung the device's System UI with a 2 GB guest and proof14 hung it identically with a 1,536 MB guest, so shrinking the guest is not the lever — a Qoder session plus the emulator plus the Maestro JVM does not fit, and Maestro passes only with more free host RAM (CI) or a physical device. While a `mobile_emulator` run's Maestro flows fail, no claim may read "mobile verified"; the report states boot, install, launch and logcat as measured and Maestro as failed with its own named cause.
- Dependency pins must satisfy `npx expo install --check` and `npx expo-doctor` on the installed Expo SDK — those two tools are the judge, and they read Expo's published SDK version data, not just the local `expo/bundledNativeModules.json`. Expo 58 declares `react-native` 0.88.0 (api.expo.dev/v2/versions `facebookReactNativeVersion`) while the shipped matrix file lists 0.88.1; pinning the matrix value passes `npm install` but fails both tools on the customer's machine. A pinned version that only `npm install` accepts also breaks `expo install --check`, `expo-doctor`, and Expo Go.
- `app_runs` proves the app against a temporary fixture API only. It is not backend or database evidence; `delivered` requires verified hosted API + database and `full_stack` mobile evidence.
- iOS export may be checked, but signing, store submission, and iOS device verification are not supported delivery claims.

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

**Premium generation and browser gates:**
- Mandatory file writes, AI kit, production spec, schema mirror, repair and final artifacts fail closed. Consume concurrent write results and propagate internal repair I/O errors; report stage and exception class without secrets. Valid idempotent kits may write zero files, but existing corrupt routers/services and missing imported dependencies must fail (`test_premium_generation.py`).
- Browser evidence requires every expected route at actual 375/768/1024/1440/1920 widths, a visible route-specific heading in main content, readable full-page screenshots, no runtime/asset errors and no visible overflow. Empty/duplicate/incomplete matrices, absent browser runtime and status text alone cannot pass. HTTP shell checks are not rendered-page proof.
- Local QA and final hosted QA have separate evidence reports. Hosted QA runs after API-origin rebuild and CORS locking; either failure blocks delivery even when QA failure was allowed for investigation. Handoff names both reports and failing route/width samples; local-only runs must never claim live verification (`test_factory_pipeline.py`).
- Four archetypes must change page composition and section order, not only colors. Preserve real contact/auth/records/realtime behavior; interpolate owner text safely and remove unsupported marketing claims or inactive controls.
- Requested 3D requires a real lazy WebGL scene, explicit activation, labeled working controls and static fallback. Supplied GLB/GLTF assets are local, bounded and validated; no traversal, remote fetches or API-exposed local filesystem paths. A desktop fallback or canvas attribute alone is never 3D proof: require nonblank rendered pixels and pixel changes after user interaction. Unsupported generation lanes fail closed.
- **Auto-repair must emit runnable JSX, not just plausible text.** The Canvas Suspense repair once inserted `className=\"…\"` and wrapped a self-closing `<Canvas />` without a closing boundary; generation passed artifact checks and only the production build failed. Repair-engine edits get a real build/regression test (`test_repair_canvas_suspense_wrapper_emits_valid_jsx`), never marker assertions alone.
- Correct generators and regenerate outputs; never hand-patch a delivered product to make acceptance pass. Keep migration, database, auth/tenant, realtime and video gates intact.

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

**Full-stack delivery is the default, not a manual step.** Hosting the database and the
API used to be work I did by hand outside the pipeline, so a run could report `delivered`
while shipping a form that posted into nothing. A run that finds `backend/package.json`
and was not given `--factory-api-url` now does all of it itself, in this order:
`db_provision.provision_database()` creates one Neon database per product →
`deploy_engine.deploy_backend()` creates `<slug>-api`, publishes the runtime env and
deploys → that origin is baked as `VITE_API_URL` and the frontend is deployed →
`deploy_backend` runs a second pass with `cors_origin` pinned to the live frontend URL →
`live_verify.verify_contact_write()` POSTs a real contact row and demands an id back.
- **`delivered` requires the write, not just the health check.** A 200 from `/health`
  proves the process booted; only an INSERT returning a row id proves a client can save.
  A probe accepted *without* validation is also a failure (`validation-not-enforced`) —
  a form that stores garbage is not "working".
- **`delivered` now walks the whole client journey, not one route.** `verify_api_surface()`
  registers, logs in, lists, creates, reads the row back, updates it, is refused on a blank
  title, then registers a **second** account and demands it cannot read, list or delete the
  first one's row, and that `GET /records` without a token is not a 2xx, and finally deletes
  the probe row and expects a 404. Each step has its own status (`create-failed`,
  `update-failed`, `tenant-isolation-broken`, `auth-not-enforced`, `delete-failed`) because
  these routes shipped broken *independently*, and an IDOR is not visible from `/health`
  (`test_a_route_that_breaks_the_client_journey_is_not_delivered`).
- **"Live updates" is a measured claim.** `verify_realtime_feed()` opens `GET /api/v1/events`
  with the token in the query string — the only transport EventSource can use — waits for
  `event: ready`, writes a row, and requires a `record:changed` frame carrying that row's id
  within the event budget. A feed that opens but never fires leaves the client's polling
  fallback in place, so the page *looks* alive while the push is dead (`no-event`). A frame
  that carries `email`/`message`/`body`/`name`/`phone` fails as `pii-in-feed`: the signal is
  an id and a timestamp, not the inquiry text broadcast to every open dashboard.
- **Every generated product ships the feed, and the feed closes itself.** `routes/events.js`
  serves `GET /api/v1/events` (query-string token, since EventSource cannot set headers),
  self-terminates at `SSE_MAX_MS=45000` — below the 60 s platform function limit — resumes by
  `Last-Event-ID` over a `(created_at, id)` keyset cursor, caps concurrency at
  `SSE_MAX_CLIENTS=64` with a 503, and answers with `Cache-Control: no-cache, no-transform`
  plus `X-Accel-Buffering: no` so no proxy buffers the frames. The client hook
  `useRealtime.js` degrades to polling after 4 failed streams and reconciles every 60 s. A
  stream that outlives the platform timeout is a feed that looks live and is not.
- **The probes clean up after themselves, on the failure paths too.** `leftovers` must be
  empty: a proof that dies mid-way still deletes its row, or the buyer's demo opens on
  factory data. The probe identity is per-product (`probe_email_for()` derives it from the
  API host) so two delivered projects sharing a DB cluster never share a user, and the
  session token the surface proof mints is passed to the feed call but is **never** copied
  into `report.json`/`report.md` (`test_the_session_the_probe_signed_with_never_reaches_the_report`).
- **A health payload with no `db` field is no evidence** (`db-not-proven`): the retired
  static `{status: healthy}` is exactly what an unreachable-database deployment reported as live.
- **`FACTORY_DATABASE_TEMPLATE_URL` in `ai-agent/.env` is the one credential the owner supplies**
  (`NEON_TEMPLATE_DATABASE_URL` is still read as its legacy spelling; the new name wins, and
  every blocking message names both plus the two server requirements: a role that can
  `CREATE DATABASE`, and TLS). The runner shells out to `pg`, so Neon, Supabase, Render,
  Railway, any managed Postgres or a self-hosted cluster works — nothing in the factory is
  provider-specific. Without it a backend run stops as `database not provisioned` *before*
  invoking any CLI — it never deploys an API that cannot connect, and never silently reuses
  one shared database for every product. `ai-agent/.env` is read directly because
  `config/settings.py` stops at the first `.env` it finds (repo root).
- **Secrets travel by stdin or env, never argv**, are CR-stripped, are generated once and
  persisted into `backend/.env` so a redeploy never rotates `JWT_SECRET` mid-demo, and never
  appear in `report.json`/`report.md` — those carry env **names** and a `db@host`, not a
  connection string (`test_no_credential_appears_anywhere_in_the_evidence`,
  `test_a_report_is_written_without_any_secret_value`).
- **A cleared `os.environ` is not isolation.** `db_provision.template_url()` also reads
  `ai-agent/.env`, so a test that only did `patch.dict(os.environ, {}, clear=True)` resolved
  the owner's live Neon URL and printed it in its own assertion diff. Every test that clears
  the environment and still resolves a credential must stub `_ENV_CANDIDATES`; a static guard
  fails the suite when one does not (`test_no_test_resolves_a_credential_from_the_real_env_files`).
- **The report ends with `## Client handoff`** (every live URL, the database, the video, the
  probe row id to delete before the demo) **and `## Not proven`** when anything failed. Give
  the client that block; never retype URLs from memory.
- **`backend/node_modules` is installed by the pipeline, and a backend with no test
  files is a failure.** The factory only ever installed the *frontend's* dependencies, so
  `npm test` in `backend/` ran smoke assertions that imported nothing, and the Neon
  creation runner — which shells out to `node` with `backend/` as its cwd — died on
  `Cannot find module 'pg'` while the stage still reported `done`. `test_backend()` now
  installs first, refuses to run when the project owns no `*.test.js` (a dependency's
  suite never counts), and fails the stage if the install fails, because `pg`, `sequelize`
  and the migration runner are all needed before any hosting claim is true
  (`test_dependencies_are_installed_before_the_generated_tests_run`,
  `test_a_backend_with_no_test_files_is_not_a_pass`).
- **A Windows policy block is an environment fact, not a build failure.** App Control /
  Smart App Control refuses a freshly written native bundler binary by file hash, so
  `npm run build` died with `ERR_DLOPEN_FAILED` on code that was never wrong (2026-10-27:
  `@rollup/rollup-win32-x64-msvc` 4.65.1 blocked while a 4.65.0 copy already loaded
  elsewhere on the machine). `agent/native_binary_repair.py` reads the blocked path out of
  the refusal, restores the same package from a sibling install in this repository (exact
  version first, then the same `major.minor`), and retries — max `MAX_SWAP_ATTEMPTS` times,
  and only inside the project being built. It downloads nothing, and the swap is recorded
  in the report as a build warning with both versions, so the substitution is auditable
  rather than silent. An ordinary compile error is still a hard stop after one attempt
  (`test_an_ordinary_build_error_is_never_retried`,
  `test_a_path_outside_this_project_is_never_written_to`).
- **A hosted product must be reachable by the client, not by the account.** A project
  created with `vercel project create` inherits the team's "Require Vercel Authentication"
  default, so every `*.vercel.app` URL answered HTTP 200 with a login page — the API was
  genuinely deployed, health said `not-json`, and no probe or buyer could get past the wall
  (2026-10-27: `ledgerline-api`). `deploy_engine.open_project_for_public_demo()` runs
  `vercel project protection disable <name> --sso` before the first probe, re-opens the
  project and re-probes when a wall is nevertheless detected, and a wall that survives is
  reported as `deployed-protected` (never `live`) with the exact command in the report
  (`test_a_project_the_pipeline_creates_is_opened_for_public_demo`,
  `test_a_walled_frontend_is_opened_and_verified_again`,
  `test_an_api_behind_a_login_page_names_the_setting_that_blocks_it`). A broken bundle is
  NOT answered by touching this setting (`test_a_broken_bundle_is_not_answered_by_touching_protection`).
- **Only the `Aliased` production domain is baked into a shipped bundle.** `vercel deploy
  --prod` prints both a permanent domain and a per-deployment URL
  (`<name>-<hash>-<team>.vercel.app`, minted fresh every run); baking the unstable one means
  the next redeploy moves the API out from under a bundle already delivered. A short
  `https://<name>.vercel.app` is global and may belong to another tenant, so it is used only
  when the CLI printed it — guessing one would post a client's contact form to a stranger
  (`test_the_aliased_project_domain_is_the_one_baked`,
  `test_a_domain_the_cli_never_printed_is_never_assumed`).
- **A provisioned database is written into the delivered `backend/.env`.** The hosted
  API is handed its URL as an argument, so a run could provision Neon, publish the var on
  Vercel, verify `db: connected` — and still deliver a folder whose own
  `npm run db:migrate` and `node server.js` read an env file with no `DATABASE_URL` and
  talk to localhost (2026-10-27: `shipsignal`). `backend_runtime_env()` persists the
  resolved URL next to the generated secrets. `CORS_ORIGIN` is deliberately excluded: the
  CORS-lock pass passes the production origin, and writing it locally would make the
  delivered server refuse its own dev client
  (`test_the_provisioned_database_lands_in_the_delivered_env_file`,
  `test_locking_the_hosted_cors_never_moves_the_local_dev_origin`).
- **A `delivered` report may not contain a failed stage — and `_write_report` is the
  projection that enforces it.** The markdown labels a stage PASS from `ok`, else
  `verified`, else a `{live, skipped}` allowlist. `_host_database` rebuilt its evidence
  from `status/database/host/message` and dropped the `ok` the provisioner returned, so a
  run that created the database, proved `db: connected` and stored a real inquiry printed
  `## database — FAIL/UNVERIFIED` two lines under its own `delivered` headline
  (2026-10-27: `shipsignal`). Every stage dict carries `ok`; the missing-flag direction stays
  loud on purpose, because an unproven stage must never render as a pass
  (`test_a_delivered_report_never_labels_a_stage_as_failed`).
- **The product's own migrations run inside the pipeline, and they are idempotent — or
  `delivered` is a lie.** Creating the database left it empty, so the only thing that ever
  made tables was `sequelize.sync()` on the API's first cold request. The buyer's
  `npm run db:migrate` then died on `relation already exists`, and a redeploy shipped a
  product that could not migrate its own schema (2026-10-27: `fieldpulse` failed live on
  `records_user_id`, an *index* name — Postgres gives tables and indexes one namespace, so
  both surface as 42P07). Two gates now:
  `factory_pipeline._apply_schema()` runs `backend/migrations/run.js` right after
  provisioning and refuses `delivered` as `schema-incomplete` when it fails — never deploys
  an API against an empty schema (a `missing` runner is a warning, because the live health,
  write, surface and feed proofs all require real tables); and every generated `up()`/`down()`
  goes through `agent/schema_guards.py`'s `_guards.js` (`createTableIfMissing`,
  `addIndexIfMissing`, `dropTableIfExists`), which asks Postgres what exists — inside the
  migration's own transaction when there is one — and creates only the gap. The helper is
  named `_guards.js` because the umzug runner globs `00*.js`; a digit-leading name would run
  as a migration. The runner answers one machine-readable JSON line on stdout (`ok`,
  `applied`, `names`, `pending`) with progress on stderr, and `db_provision.run_migrations()`
  refuses `ok: true` from a process that exited non-zero — an exit code alone is not proof.
  Proved on a real Neon database: old runner exits 1 on `already exists`, guarded runner
  reports `applied: 3` then `uptodate` (`test_no_generator_module_writes_a_migration_that_is_not_guarded`
  fails any generator template that emits a bare `queryInterface.createTable(`/`dropTable(`/`addIndex(`).

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
| 2026-10-27 | 8.33 | **Factory v5 — the product's own migrations run inside delivery, guarded and idempotent; provider-neutral database credential**: `agent/schema_guards.py` ships `_guards.js` (`createTableIfMissing`/`addIndexIfMissing`/`dropTableIfExists`) into every generator, `_apply_schema()` runs `migrations/run.js` after provisioning and blocks `delivered` as `schema-incomplete` on failure, runners answer one machine-readable JSON line, and `FACTORY_DATABASE_TEMPLATE_URL` replaces `NEON_TEMPLATE_DATABASE_URL` (legacy still resolves) |
| 2026-10-27 | 8.32 | **Factory v4 — `delivered` proves the client journey and the live push**: `verify_api_surface()` walks register → login → list → create → read-back → update → blank-title rejection → second-tenant isolation → anonymous-denied → delete-then-404 over the live origin; `verify_realtime_feed()` requires a `record:changed` frame for a row written while the stream was open and rejects frames carrying customer PII; both probes delete their own rows even when they fail, and the session token they mint never enters the report |
| 2026-10-27 | 8.31 | **Factory v3 — one prompt leaves the whole stack live**: auto-provisioned Postgres (`db_provision.py`), auto-hosted Express API with `db: connected` proof, Vercel Deployment Protection opened for demo (`deployed-protected` when it survives), only the `Aliased` domain baked, Windows native-bundler policy block self-repaired, provisioned `DATABASE_URL` persisted into the delivered `backend/.env`, and the report can no longer label a passing stage as failed. Proven end to end by ShipSignal in 551 s with zero manual steps |
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
