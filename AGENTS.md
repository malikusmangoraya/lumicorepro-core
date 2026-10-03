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
- **Branding**: Never plain text. Always generate dynamic vector SVG logos (`UniqueLogo` / `BrandLogo`) with geometric symbols & dual-color gradients.
- **Footers**: Never a single plain line. Always multi-column professional footers (`ModernFooter`) with live status badge (`🟢 99.99% Operational`), newsletter signup, categorized sitemap, and social links.
- **Motion UI**: Bento grids (`BentoGrid`), Spotlight cursor illumination (`SpotlightGrid`), 3D tilt (`HolographicCard`), border beams (`BorderBeam`), and text morphing (`TextMorph`).
- **Variants**: primary/secondary/success/danger/warning/info/outline/ghost/glow. Sizes: xs/sm/md/lg/xl.

### Backend
Response: `{success,status,message,data,timestamp}`. Errors: `success:false` + code + user message. Middleware: auth → validate → route → error. Sequelize models + validation. Structured logging.

### Database
Snake case. Foreign keys + constraints. Index queried columns. Versioned migrations. Soft deletes (`deleted_at`).

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

| Type | Tool | Location | Target | Measured (2026-09-28) |
|------|------|----------|--------|------------------------|
| Frontend | Vitest 5 | `src/**/__tests__/` | 80%+ | **Very low — 27 tests / 4 files, no coverage gate** |
| Backend | Jest | `backend/__tests__/`, `backend/tests/` | 80%+ | **37.9% statements (871/2300) — 21 suites / 210 tests** |
| AI agent | pytest | `ai-agent/tests/` | 80%+ | 629 tests green |
| E2E | Playwright | `e2e/` | Key paths | 1 file, 3 tests green |
| Mock | MSW | `src/test/` | As needed | In place |

Targets are goals, **not** the current state. Measured on 2026-09-28: backend
statement coverage is 37.9% (871/2300 statements covered, 32.8% branches, 34.3%
functions, 38.6% lines) against an 80% target, up from 26.3% (598/2274) earlier the
same day. The frontend has 27 tests across 4 files and no coverage gate at all.
Backend and frontend coverage remain the largest open gaps in the repo. `ai-agent` is
the only suite near its target, and its count is a test count, not a measured
coverage percentage. Run the backend suite from `backend/` with
`node --experimental-vm-modules ./node_modules/jest/bin/jest.js --coverage`; the
root `npm run test:backend` script is not the instrumented path.

Still at 0% or near-0% and worth covering next: `middleware/usageGuard.js`,
`services/systemConfig.service.js`, `services/aiCost/*`, `utils/monitoring.js`,
`services/email.service.js`, and the remaining payment gateways (PayPal, Stripe,
Flutterwave, Paytm, Mollie, MercadoPago, Razorpay, LiqPay, Square).

Mock externals (MSW). Test error paths. Isolated tests. Descriptive names. Await async.

---

## 7. PERFORMANCE

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Lighthouse Performance | 95+ | — |
| Bundle (gzip) | <200KB | <300KB |
| JS Bundle (gzip) | <150KB | <200KB |
| CSS (gzip) | <30KB | <50KB |
| LCP | <1.5s | — |
| CLS | <0.05 | <0.1 |

- `React.lazy()` + `Suspense` for routes. Vendor chunking. Tree-shake. Lazy-load Three.js/GSAP/Lottie/Recharts
- WebP preferred, `loading="lazy"`, `font-display: swap`
- `useMemo`/`useCallback` for expensive ops. Windowing >100 items. Debounce 300ms. Animate `transform`/`opacity` only
- React Query: `staleTime: 5min`, `gcTime: 30min`. SW: hashed assets indefinite. `localStorage` for prefs only

Measured 2026-09-28 (`npm run size`): initial JS **193.2 KB** gzip across 9 chunks, CSS 24.7 KB, largest chunk `HeroCanvas` 219.5 KB. This **passes the enforced script budgets** (200 KB initial JS, 50 KB CSS, 300 KB largest chunk) but **misses the 150 KB "JS Bundle" target row** by 43 KB. Report the two claims separately — do not describe the 200 KB gate as if it were the 150 KB target. Headroom is ~7 KB and most of the earlier saving is committed, so treat a small regression here as a gate failure, not noise.

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
Reference Intelligence → `design_intelligence.py`, `competitive_benchmark.py`, `design_style.py` · Playbooks → `theme_matrix.py`, `design_vault.py` · Blueprint → `planner.py`, `project_mode_engine.py` · Manifest/Memory → `memory_retriever.py`, `.artifacts/` · Benchmark/Lint → `vision_pipeline.py`, `quality_gates.py` · Scoring → `quality_gate.py`, `quality_gates.py` · Self-heal/Redesign → `enterprise_repair.py`, `iterate_engine.py`, `restyle_all.py` · Orchestration → `orchestrator.py`, `pipeline.py`. Central orchestrator controls task/state; agents must not randomly modify files outside the plan.

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
| 2026-10-03 | 8.0 | Audit remediation: repo hygiene + `.gitignore`, P0 email-logger crash fix, CI gate un-masked, security / tenancy / AI-agent / frontend / ops workstreams |
| 2026-09-24 | 7.13 | 10 vertical AI-agent SaaS products shipped — 69/69 full-stack packaged |
| 2026-09-21 | 7.12 | Full-stack delivery completed — 59/59 packaged with honest manifests |
| 2026-09-18 | 7.11 | Per-brand content pipeline + comparison table + full routes 43/43 |
| 2026-09-17 | 7.10 | System-level anatomy verification + changelog honesty inventory |

Older entries: see `CHANGELOG.md` or `git log`.
