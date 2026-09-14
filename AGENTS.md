# AGENTS.md — LumicorePro Core

> v5.1 (Marketplace Delivery) | 2026-09-12
> Monorepo: React 19 + Vite + Tailwind 3 | Express + MySQL + Redis | Python FastAPI AI Agent

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

Architecture: `User → React → Hook/Context → Axios → Express → MySQL/Redis`

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
Response: `{success,status,message,data,timestamp}`. Errors: `success:false` + code + user message. Middleware: auth → validate → route → error. Mongoose schemas + validation. Structured logging.

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

| Type | Tool | Location | Target |
|------|------|----------|--------|
| Unit | Vitest | `src/__tests__/` | 80%+ |
| Backend | Jest | `backend/__tests__/` | 80%+ |
| Integration | Jest | `backend/__tests__/` | 70%+ |
| E2E | Playwright | `e2e/` | Key paths |
| Mock | MSW | `src/test/` | As needed |

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

## 18. SELLABLE PROJECT DELIVERY (mandatory)

Every **new project** this agent creates must be listable on Gumroad, Lemon Squeezy, ThemeForest, Creative Market, GitHub, and Product Hunt.

- **README.md (required):** product pitch, features, stack, prerequisites, copy-paste Getting Started, env table, structure, scripts, deploy, i18n/compliance, troubleshooting, license. Never a one-liner that only points at INSTRUCTIONS.md.
- **International:** English buyer copy, i18n + RTL, multi-currency, GDPR consent, Privacy/Terms, SEO + OG + JSON-LD, robots/sitemap.
- **Pro UI only:** UniqueLogo/BrandLogo, GlassNavbar, ModernFooter, Lucide + labels, real images, dark mode, motion, mobile-first. No placeholders, no text-only logos, no single-line footers.
- **Zero errors:** no TODO/lorem/dummy keys; lint/build clean; `.env.example` only.
- **Ship with:** LICENSE.md, .gitignore, seller kit when generated via the pipeline.

Rule file: `.cursor/rules/marketplace-ready-projects.mdc`

---

## 17. CHANGE LOG

| Date | Ver | Changes |
|------|-----|---------|
| 2026-09-14 | 5.5 | Full-stack hardening — `repair_any_layout` last-gate `repair_component_imports` fixes broken `@/` imports (known stubs input/textarea/select, passthrough stubs, default→named alias `export { defaultName as X }`); project-builder rejects non-project templates; api_generator backend gets npm auto-fix; schema/template seeding only keeps real files |
| 2026-09-14 | 5.4 | Planning-first: new `design_brand_planning` phase resolves the full international design blueprint (style + region + palette + vault source) BEFORE code generation; writes DESIGN_PLAN.md + style/region-aware design-tokens.json; palette resolution shared between plan and restyle via `_resolve_style_blueprint` |
| 2026-09-14 | 5.3 | International design — region-aware color combos (GCC/South-Asia/East-Asia/EU/NA/LatAm/Africa) + Design Vault that registers legally-obtained kits (e.g. HorizonX exports) as agent-native ui_styles via token extraction |
| 2026-09-14 | 5.2 | UI Style Wheel — 9 design languages (minimal/glass/neo-brutalism/bento/neumorphism/flat/clay/skeuomorphism/dark) auto-detected from prompt; style-aware palette/CSS/tailwind/home/nav; JSON-safe self-heal; package.json pin-merge; JSON-LD @graph + OG meta + tinyshining-cs-vars gate scaffold |
| 2026-09-12 | 5.1 | Marketplace delivery — sellable README, pro UI, international, zero-error bar |
| 2026-09-04 | 5.0 | Speed optimized — 867→compact, merged duplicates, removed verbosity |
| 2026-09-04 | 4.0 | Enterprise — a11y, i18n/RTL, PWA, state tree, performance budgets |
