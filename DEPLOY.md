# LumiCorePro — Free-Tier Deployment Guide

Deploy the full stack for **free**. No paid subscriptions required.

| Part | Host | Plan (free) |
|------|------|-------------|
| Frontend (React/Vite) | Vercel | Hobby |
| Backend (Express) | Railway OR Render | Starter / Free |
| AI Agent (FastAPI) | Railway OR Render | Starter / Free (optional) |
| Database (PostgreSQL) | Railway / Supabase / Render | Free limit |
| Cache/Queue (Redis) | Railway / Upstash | Free limit |
| Captcha | Cloudflare Turnstile | Unlimited free |
| Analytics | Plausible (self-hosted) or PostHog | Free |

---

## 1. Frontend → Vercel

1. Push repo to GitHub and import in Vercel.
2. Framework preset: **Vite** (auto-detected); build `npm run build`, output `dist`.
   `vercel.json` is already committed (SPA rewrites + service-worker headers).
3. Project Settings → Environment Variables (all `VITE_`):

```
VITE_API_URL=https://<your-backend>.railway.app        (or render)
VITE_ENABLE_MOCK_API=false
VITE_SITE_URL=https://your-frontend.vercel.app
VITE_ENABLE_ANALYTICS=true
VITE_ANALYTICS_PROVIDER=plausible
VITE_PLAUSIBLE_DOMAIN=your-frontend.vercel.app
VITE_TURNSTILE_SITE_KEY=0x...                          (Cloudflare Turnstile)
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_LOGGING=true
```

---

## 2. Backend → Railway

1. Import repo, set root directory **`backend`**. `railway.json` is committed
   (Nixpacks build, `npm run start`, health check `/api/health`).
2. Add a PostgreSQL plugin + Redis plugin (free limits) and copy their URLs.
3. Environment variables — everything needed to boot (secrets only live in
   the Railway dashboard, never in the repo):

```
NODE_ENV=production
PORT=5000
DATABASE_URL=postgres://...                     (from Railway Postgres plugin)
DB_SSL=true
REDIS_URL=redis://...                           (from Railway Redis plugin)
FRONTEND_URL=https://your-frontend.vercel.app
ALLOWED_ORIGINS=https://your-frontend.vercel.app
JWT_SECRET=<64-char random>
JWT_EXPIRE=7d
SESSION_SECRET=<random>
AI_AGENT_URL=http://localhost:8000               (set to AI-agent URL when you deploy it)
AGENT_API_KEY=<random internal key>

# AI cost protection (launch values — server enforced)
DEMO_MODE=true                                   ← set TRUE for the free demo
AI_DAILY_GEN_LIMIT=3
AI_DAILY_CHAT_LIMIT=20
AI_DAILY_VISION_LIMIT=10
AI_MAX_TOKENS_GENERATION=12000
AI_MAX_TOKENS_CHAT=4000
AI_MAX_TOKENS_VISION=2000
AI_CB_MAX_REQUESTS=10
AI_CB_BLOCK_SECS=300
AI_MAX_CONCURRENT=2
AI_TOKEN_BUDGET=40000
AI_TOKEN_COST_PER_1K=0.02

# Payments — launch: Stripe + PayPal only
PAYMENT_GATEWAYS_ENABLED=stripe,paypal
STRIPE_SECRET_KEY=sk_test_...                   (test keys for demo)
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_MODE=sandbox

# Captcha (Cloudflare Turnstile — free)
TURNSTILE_SECRET_KEY=0x...
TURNSTILE_SITE_KEY=0x...
TURNSTILE_ENABLED=true

# Email (free: Resend/Brevo/Mailtrap)
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
EMAIL_FROM=noreply@lumicorepro.com

# AI provider key (backend direct calls)
GEMINI_API_KEY=...                              (or OPENAI/ANTHROPIC/OPENROUTER)
ACTIVE_AI_PROVIDER=gemini
```

4. Optional: run `npm run seed` once to seed pricing plans
   (`backend/scripts/seedPlans.js`) and `npm run db:indexes`.

---

## 3. AI Agent (FastAPI) → Railway/Render (optional for live AI)

Demo mode (`DEMO_MODE=true`) does **not** need the AI agent — generations are
simulated locally and cost nothing. To enable real AI generations later:
1. Deploy `ai-agent/` (Python, `uvicorn server:app --port 8000`).
2. Set `AI_AGENT_URL=https://your-agent.railway.app` and the same
   `AGENT_API_KEY` on both backend and agent.
3. Add your provider key (e.g. `GEMINI_API_KEY`) on the agent.

---

## 4. Demo Mode (the important part)

With `DEMO_MODE=true` the `/api/ai/generate` route returns an instant
simulated result **without calling the AI agent** — so thousands of demo
visitors cost you **$0** in AI credits. Daily generation limit still applies
per IP/user. Switch it to `false` when you launch real AI behind paid plans.

---

## 5. Turnstile captcha (frontend + backend already wired)

1. Cloudflare Dashboard → Turnstile → "Add Site" → domain(s).
2. Copy the **Site Key** → `VITE_TURNSTILE_SITE_KEY` (frontend, public).
3. Copy the **Secret Key** → `TURNSTILE_SECRET_KEY` (backend, private).
4. `TURNSTILE_ENABLED=true`. Register now requires the captcha; login runs
   an optional check when a token is present.

---

## 6. Post-deploy smoke test

```
curl https://<backend>/api/health           → { "success": true, ... }
curl https://<backend>/api/ai/my-quota      → { "success":true, "data":{ "limit":3 ... } }
curl https://<frontend>/                    → landing page loads
```