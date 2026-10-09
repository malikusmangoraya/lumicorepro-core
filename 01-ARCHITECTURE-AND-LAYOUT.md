# 01 — ARCHITECTURE & LAYOUT

## 1. Repo structure (Monorepo — tajweez kardah)

```
suite/
├─ packages/
│  ├─ core-backend/          # auth, rbac, payments, mail, queue, audit, health
│  ├─ core-frontend/         # UI kit, hooks, api client, i18n, a11y helpers
│  ├─ config/                # eslint, tsconfig, prettier, tailwind preset
│  └─ testing/               # shared test utils, fixtures, factories
├─ products/
│  ├─ claimflow/
│  │  ├─ backend/            # sirf niche modules + wiring
│  │  ├─ frontend/           # sirf niche pages/components
│  │  ├─ docs/
│  │  ├─ docker/
│  │  └─ product.config.ts   # naam, theme, enabled modules, feature flags
│  └─ ...
├─ tools/                    # generators, audit scripts, release scripts
├─ .github/workflows/
├─ turbo.json / nx.json      # build cache
└─ pnpm-workspace.yaml
```

**Faida:** ek bug fix core mein, 11 products mein apne aap. Har product ka apna repo/ZIP release bhi ban sakta hai (script se export).

> Agar abhi monorepo mushkil lage, to pehle sirf **ek template repo** banao aur baqi products us se generate karo. Magar long-term mein monorepo behtar hai.

## 2. Backend layout (har product ke liye)

```
backend/
├─ src/
│  ├─ app.js                 # express app (bina listen)
│  ├─ server.js              # listen + graceful shutdown
│  ├─ config/                # env validation (zod), constants
│  ├─ modules/               # FEATURE-BASED, type-based nahi
│  │  ├─ auth/
│  │  │  ├─ auth.routes.js
│  │  │  ├─ auth.controller.js
│  │  │  ├─ auth.service.js
│  │  │  ├─ auth.schema.js   # zod validation
│  │  │  └─ auth.test.js
│  │  ├─ claims/             # niche module
│  │  └─ ...
│  ├─ shared/                # middleware, errors, utils, logger
│  ├─ db/
│  │  ├─ models/
│  │  ├─ migrations/         # versioned (YYYYMMDDHHMM-name.js)
│  │  └─ seeders/
│  ├─ jobs/                  # bullmq workers
│  └─ integrations/          # stripe/, lemonsqueezy/, mail/, ai/
├─ tests/ (integration + e2e)
├─ openapi.yaml
└─ Dockerfile
```

### Rules
1. **Route -> Controller -> Service -> Model.** Business logic sirf service mein.
2. Har request body/params/query par **zod validation**.
3. Ek **central error handler**; har error ka format same:
   ```json
   { "error": { "code": "CLAIM_NOT_FOUND", "message": "...", "requestId": "..." } }
   ```
4. Har request ko `requestId` mile (logs mein trace ke liye).
5. Sirf wohi modules load hon jo `product.config` mein enable hain. 33 route modules zabardasti nahi.
6. Env variables sirf `config/env.js` se parho, `process.env` seedha na use karo. Startup par zod se validate, missing ho to saaf error.

## 3. Frontend layout

```
frontend/
├─ src/
│  ├─ app/                   # router, providers, layouts
│  ├─ features/              # claims/, billing/, auth/ ...
│  │  └─ claims/
│  │     ├─ api.ts           # react-query hooks
│  │     ├─ components/
│  │     ├─ pages/
│  │     └─ store.ts         # zustand (sirf zaroorat par)
│  ├─ components/ui/         # Button, Input, Modal, Table (core-frontend se)
│  ├─ i18n/locales/{en,ar,...}/
│  ├─ styles/                # tokens.css, rtl.css
│  └─ lib/                   # axios client, utils
├─ public/ (sw.js, manifest.json)
└─ Dockerfile
```

### Rules
1. **TypeScript** use karo (premium buyers ke liye zaroori).
2. Server state = react-query. Client state = zustand (sirf UI state). Dono ko mix na karo.
3. Design tokens (rang, spacing, font) ek jagah, product ka theme sirf token override.
4. Har page: loading, empty, error, success: **4 states** zaroor.
5. Code-split har route (lazy). Performance budget CI mein enforce.

## 4. Product page layout (Landing / marketing)

Har product ka landing page is order mein:

1. **Hero:** ek line ka wada, CTA (Demo/Buy), product screenshot
2. **Social proof:** logos / testimonials / numbers
3. **Problem -> Solution:** 3 blocks
4. **Features:** 6-8 cards, har ek ka faida
5. **How it works:** 3 steps
6. **Pricing:** Standard / Pro / Premium table
7. **FAQ**
8. **Final CTA + footer** (Privacy, Terms, Cookie settings, Support)

### Dashboard layout (app ke andar)
- Left sidebar (collapsible), top bar (search, notifications, profile)
- Main: page title + primary action (right), filters, content
- Mobile: bottom nav ya drawer
- Command palette (`Ctrl+K`), Premium feature
- Dark/light mode, RTL support

## 5. Database design rules

1. **Migrations only.** `sequelize.sync()` production mein kabhi nahi.
2. Har table: `id (uuid)`, `created_at`, `updated_at`, `deleted_at` (soft delete jahan zaroori).
3. Foreign keys + indexes (jo columns filter/join mein aate hain).
4. Money = integer (paise/cents) + currency code. Float kabhi nahi.
5. Har product sirf apne models rakhe. ClaimFlow mein `Claim`, `Policy`, `ClaimDocument`, `Adjuster`... `Doctor`/`Cart` nahi.
6. Multi-tenant ho to har table par `organization_id` + row-level filter.

## 6. Security architecture (short)

- Access token (15 min) + rotating refresh token (httpOnly, Secure, SameSite)
- Refresh token reuse detection (reuse ho to poori family revoke)
- Password: bcrypt cost ≥ 12 ya argon2id
- Helmet + strict CSP, CORS whitelist
- Rate limit: login/reset par alag, sakht limits
- Secrets kabhi frontend mein nahi, kabhi git mein nahi
- Webhooks: signature verify + idempotency key + replay protection
- File upload: type/size check, random filenames, virus scan (premium)
Detail: `05-QUALITY-SECURITY-COMPLIANCE.md`

## 7. Environments

| Env | Kis liye | DB | Notes |
|---|---|---|---|
| local | development | Docker Postgres | seed data |
| test | CI | ephemeral Postgres | har run fresh |
| staging | demo/QA | managed Postgres | production jaisa |
| production | buyer | managed + backups | secrets manager |

## 8. Feature flags / modules

`product.config.ts`:
```ts
export default {
  name: "ClaimFlow",
  modules: ["auth", "claims", "documents", "billing", "reports"],
  features: { twoFactor: true, ai: false, whiteLabel: false },
};
```
Buyer ke plan (Standard/Pro/Premium) ke hisab se modules on/off, license key se control.

## 9. Observability

- **Logs:** winston/pino JSON, requestId, user id (PII mask)
- **Errors:** Sentry (frontend + backend)
- **Metrics:** `/metrics` (Prometheus) — Premium
- **Health:** `/health` (liveness), `/ready` (DB/Redis check)
- **Audit:** har sensitive action (login, role change, payment, export) AuditLog mein

## 10. Code quality gates (CI mein)

lint -> typecheck -> unit tests -> integration tests -> build -> bundle budget -> e2e -> security scan -> deploy

Koi gate fail ho to merge nahi.
