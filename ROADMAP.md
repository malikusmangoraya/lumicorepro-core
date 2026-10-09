# LumiCorePro — Repository Audit & Full Roadmap

**Date:** 2026-09-28
**Repo:** `malikusmangoraya/lumicorepro-core` (origin remote)

---

## 1. GitHub Repo Audit

### 1.1 Remote Configuration

| Item | Value |
|------|-------|
| Origin | `https://github.com/malikusmangoraya/lumicorepro-core.git` |
| Default branch | `master` |
| Working tree | 463 changed entries, 334 untracked files (archived) |
| GITHUB_TOKEN | **DEAD in all 5 sources** — verified 401 Bad credentials on 2026-10-05: `.env`, `ai-agent/.env`, `.history/.env_20260929102938`, User env var, Windows Credential Manager. A NEW PAT is required. |

### 1.2 Campaign / Delivery Repos (VERIFIED list from AGENTS.md)

| Repo | Status | Note |
|------|--------|------|
| `malikusmangoraya/lumicorepro-core` | **404** | Origin repo missing or renamed |
| `malikusmangoraya/aurelia` | **404** | Deleted or renamed |
| `malikusmangoraya/aurum` | **404** | Deleted or renamed |
| `malikusmangoraya/ember` | **404** | Deleted or renamed |
| `malikusmangoraya/maison` | **404** | Deleted or renamed |
| `malikusmangoraya/meridian` | **404** | Deleted or renamed |
| `malikusmangoraya/nuage` | **404** | Deleted or renamed |
| `malikusmangoraya/prestige` | **404** | Deleted or renamed |
| `malikusmangoraya/saffron` | **404** | Deleted or renamed |
| `malikusmangoraya/studio` | **404** | Deleted or renamed |
| `malikusmangoraya/voltus` | **404** | Deleted or renamed |

**Result: 0 of 11 campaign repos are reachable.** All "10 real live links" from the previous delivery manifest are dead.

### 1.3 Vendor / Third-Party Repos (healthy)

| Repo | Status | Stars | Forks | Last Push | License |
|------|--------|-------|-------|-----------|---------|
| `gosom/google-maps-scraper` | OK | 6,160 | 971 | 2026-09-24 | MIT |
| `Thyd/codex-dev-loop` | OK | 4 | 1 | 2026-09-13 | MIT |
| `Mahanaicoach/google-maps-scraper-kit` | OK | 991 | 198 | 2026-09-07 | NOASSERTION |

All three are cloned under `vendors/` and integrated.

---

## 2. What This Roadmap Covers

```
LumiCorePro Core
├── Phase A — Foundation (backend + AI agent)
├── Phase B — Frontend (React 19 + Vite)
├── Phase C — Generated Projects (91 sites)
├── Phase D — Delivery (ZIP packaging)
├── Phase E — Vendors (scraper + dev loop)
└── Phase F — Live Deployment
```

### Phase A — Foundation

| Component | Location | Status | Tests |
|-----------|----------|--------|-------|
| Express API | `backend/` | Working | 210/210 |
| PostgreSQL schema | `database/schemas/` | Defined | Migrations unverified (no DB) |
| Redis cache | `backend/services/cache/` | Working | Covered |
| AI Agent (FastAPI) | `ai-agent/` | Working | 629/629 |
| License engine | `backend/utils/license.js` | Fixed | 9/9 |
| Auth (JWT + refresh) | `backend/services/refreshToken.service.js` | Fixed | 5/5 |
| Payment gateways | `backend/services/payment/` | 18 providers | bKash 13/13 |
| Captcha | `backend/middleware/captchaVerify.js` | Fixed | 17/17 |
| Webhook security | `backend/middleware/webhookSecurity.js` | Working | 19/19 |

### Phase B — Frontend

| Component | Location | Status |
|-----------|----------|--------|
| React 19 + Vite 8 | `frontend/` | Build 4.5s |
| Tailwind 3 | `src/styles/` | 24.7 KB gzip |
| 91 generated sites | `generated-projects/` | All built |
| Bundle budget | `scripts/check-bundle-budget.mjs` | PASS |
| E2E (Playwright) | `e2e/` | 3/3 |
| Tests (Vitest) | `src/__tests__/` | 27/27 |

### Phase C — Generated Projects (91)

| Metric | Value |
|--------|-------|
| Total projects | 91 |
| With backend | 68 |
| Frontend-only | 23 |
| Bugs fixed (redis + license) | 68 |
| Rebuilt | 91 (90 cached + 1 fresh) |
| Unique brands | 91 |
| Blue/gold audit | 0 violations |

### Phase D — Delivery

| Metric | Value |
|--------|-------|
| Old delivery (`delivery/`) | 69 dirs + 69 ZIPs |
| New delivery (`delivery-new/`) | 91 dirs + 91 ZIPs |
| Live links | **0** (all repos 404) |
| Packaging script | `scripts/_fast_package.py` |

### Phase E — Vendors

| Tool | Location | Integration |
|------|----------|-------------|
| Google Maps Scraper Kit | `vendors/google-maps-scraper-kit` | `docker-compose.scraper.yml` |
| Codextron Dev Loop | `vendors/codextron-dev` | `.codex/skills/`, `scripts/dev_loop.py` |

### Phase F — Live Deployment

| Item | Blocker |
|------|---------|
| GitHub repos | All 11 campaign repos 404 |
| GITHUB_TOKEN | Expired (401) |
| PostgreSQL | No credentials |
| Redis | No credentials |
| Domain / SSL | Not configured |
| Stripe/PayPal live keys | Not configured |

---

## 3. Roadmap — What to Do Next

### Step 1 — Restore GitHub Access (BLOCKER)

```
Priority: CRITICAL
Effort: 5 minutes
```

1. Generate a new GitHub PAT (`repo` scope) at https://github.com/settings/tokens
   (fine-grained alternative: Contents Read+Write + Workflows, Account Email Read)
2. Put the token in `.env` **unquoted** as `GITHUB_TOKEN=ghp_...`, then prove it
   before touching anything else:
   ```
   python -c "import sys;sys.path.insert(0,'ai-agent');from agent.gh_token import load_token,validate_token;print(validate_token(load_token(env_files=['.env'])))"
   ```
   Expect `True` plus your login. A `401 Bad credentials` on a token you just
   created almost always means the quotes got baked into the value, or the PAT
   was never saved. Every reader is now quote-tolerant
   (`agent/gh_token.py`), so this is a diagnostic, not a workaround.
   Optionally refresh Windows Credential Manager for `git push` over HTTPS:
   ```
   "protocol=https`nhost=github.com`nusername=malikusmangoraya`npassword=ghp_..." | git credential approve
   ```
3. Create the 11 campaign repos (they are all 404):
   ```
   aurelia-estates, aurum-fitness, ember-salt, maison-noir,
   meridian-capital, nuage-events, prestige-studio, saffron-voyage,
   studio-lumen, voltus-atelier
   ```
4. Push each generated project to its repo
5. Enable GitHub Pages on each

**Without this step, zero sites go live.**

### Step 2 — Database Migration

```
Priority: HIGH
Effort: 30 minutes
```

1. Provision PostgreSQL (local Docker or cloud)
2. Run `database/schemas/schema.sql`
3. Seed admin user
4. Test `DATABASE_URL` connection

### Step 3 — Redis Setup

```
Priority: HIGH
Effort: 10 minutes
```

1. Start Redis (`docker run -p 6379:6379 redis:7`)
2. Verify `REDIS_URL` connection
3. Test cache fallback path

### Step 4 — Payment Gateway Live Keys

```
Priority: MEDIUM
Effort: 1 hour
```

1. Create Stripe account + get live keys
2. Create PayPal developer app
3. Update `.env` with live credentials
4. Test real webhook endpoints

### Step 5 — Production Deployment

```
Priority: MEDIUM
Effort: 2 hours
```

1. Frontend: deploy `dist/` to Vercel/Netlify
2. Backend: deploy to Render/Railway/Fly.io
3. Set env vars on hosting platform
4. Configure domain + SSL
5. Enable CORS for production domain

### Step 6 — Monitoring & Observability

```
Priority: LOW
Effort: 1 hour
```

1. Add Sentry DSN to `.env`
2. Configure error tracking
3. Set up uptime monitoring

### Step 7 — Backend Coverage Expansion

```
Priority: LOW
Effort: Ongoing
```

Target: 80% statement coverage (currently 37.9%)

Modules to cover next:
- `middleware/usageGuard.js`
- `services/systemConfig.service.js`
- `services/aiCost/*`
- `utils/monitoring.js`
- `services/email.service.js`
- Payment gateways: PayPal, Stripe, Flutterwave, Paytm, Mollie, MercadoPago, Razorpay, LiqPay, Square

---

## 4. Summary

| Area | Health |
|------|--------|
| Code quality | Good — lint clean, tests pass |
| Security | Good — 2 critical bugs fixed |
| Architecture | Good — Express + PostgreSQL + Redis + FastAPI |
| Delivery | Good — 91 ZIPs ready |
| Live deployment | **Blocked** — repos 404, token expired |
| Documentation | Good — this roadmap |

**The #1 blocker is GitHub access.** Everything else is ready to deploy once repos exist and credentials are provided.
