# BlogForge — AI Blog & SEO Content Generator

Turn one keyword into a publish-ready, SEO-structured article in seconds. BlogForge streams
markdown from an AI provider, stores every article with its SEO metadata, and meters usage
with a credit system — a complete, deployable SaaS starter.

**Live demo**

| Surface | URL |
|---------|-----|
| Web app | https://blogforge-lumicorepro.vercel.app |
| API | https://blogforge-api.vercel.app/api/v1 |
| Health check | https://blogforge-api.vercel.app/api/v1/health |

Register with any email to get **50 free credits** — no API key needed, the app falls back to a
built-in demo generator so the whole flow works out of the box.

## Features

- **Streamed generation** — Server-Sent Events deliver `meta` → `chunk`… → `done`; the article
  renders progressively instead of waiting for the full completion.
- **SEO output** — H1/H2/H3 structure, meta title, meta description, keyword list and word count
  extracted from every generated draft.
- **Credits that cannot go negative** — atomic `UPDATE … WHERE balance > 0 RETURNING`; failed
  generations are refunded automatically.
- **Demo mode** — no provider key configured? A deterministic, well-structured article is streamed
  anyway, so demos and QA never depend on a paid API.
- **History workspace** — list, reopen and delete saved articles; per-user isolation enforced
  server-side.
- **Real auth** — JWT (7 days), bcrypt password hashing, schema validation and XSS escaping on
  every request body.
- **Production UI** — React 19 + Vite + Tailwind, split-view generator, skeleton shimmer, toast
  notifications, dark-mode-ready design tokens, reduced-motion support, Markdown → sanitized HTML.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, Tailwind CSS 3, lucide-react, marked |
| Backend | Node.js, Express 4, Sequelize 6, Umzug migrations |
| Database | PostgreSQL (Neon on Vercel, local Postgres for development) |
| AI | OpenAI-compatible provider (OpenAI / OpenRouter / DeepSeek / Gemini), optional |
| Deployment | Vercel (static frontend + serverless Express API) |

## Quick start (local)

Prerequisites: Node 20+, PostgreSQL 14+.

```bash
# 1. Database
createdb blogforge

# 2. Backend
cd backend
npm install
cp ../.env.example .env          # set DB_* and JWT_SECRET / ENCRYPTION_KEY
npm run db:migrate
npm run dev                      # http://localhost:5000

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env             # VITE_API_URL=http://localhost:5000/api/v1
npm run dev                      # http://localhost:5173
```

Generate secrets:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"  # JWT_SECRET
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"  # ENCRYPTION_KEY (64 hex chars)
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Prod | Postgres connection string (Neon/Supabase/RDS). Enables SSL automatically |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Local | Used when `DATABASE_URL` is absent |
| `JWT_SECRET` | Yes | ≥ 32 chars, signs access tokens |
| `ENCRYPTION_KEY` | Yes | Exactly 64 hex chars (AES-256-GCM for stored provider keys) |
| `PORT` | No | API port, default `5000` |
| `OPENAI_API_KEY` | No | Enables real generation; demo mode is used when absent |
| `OPENROUTER_API_KEY` / `DEEPSEEK_API_KEY` / `GEMINI_API_KEY` | No | Alternative providers |
| VITE_API_URL | Frontend | Base API URL, e.g. https://blogforge-api.vercel.app/api/v1 |
| CORS_ORIGINS | Prod | Comma-separated browser origins allowed against the API. Defaults to the shipped demo origins plus localhost:5173 |
| ENABLE_DEMO_TOPUP | No | Set to 1 only to re-enable the free evaluation credit top-up (ships disabled in production) |
| TEST_DATABASE_URL | Tests | Isolated database for 
pm test; tests refuse to run against any other URL |

## API

| Endpoint | Method | Auth | Behavior |
|----------|--------|------|----------|
| `/api/v1/auth/register` | POST | — | Create account, grants 50 credits |
| `/api/v1/auth/login` | POST | — | Returns JWT (7 days) |
| `/api/v1/blog/generate` | POST (SSE) | JWT | Streams `meta` → `chunk`… → `done`; 1 credit, refunded on failure |
| `/api/v1/blog/history` | GET | JWT | Paginated article list |
| `/api/v1/blog/articles/:id` | GET / DELETE | JWT | Full article / delete |
| `/api/v1/blog/credits` | GET | JWT | Balance, granted, used |
| `/api/v1/blog/credits/topup` | POST | JWT | Add 10–5000 credits |
| `/api/v1/health` | GET | — | Liveness probe |

SSE event contract:

```
event: meta   data: {"keyword":"…","tone":"…","balance":49,"demo":true}
event: chunk  data: "# Article markdown chunk…"
event: done   data: {"articleId":"…","creditsUsed":1,"balance":49}
event: error  data: {"message":"…"}          # credit refunded
```

## Quality & international readiness

This package is audited with a Playwright **Global Market Audit** run against the live
deployment (performance desktop + mobile, SEO, i18n/currency signals, legal trust surface,
conversion) and graded STANDARD 80 / PREMIUM 88 / SIGNATURE 92. Latest run:

| Metric | Result |
|---|---|
| Overall | **90 / 100 - PREMIUM** |
| Performance | 75 (LCP 1.9s, well under the 2.5s hard limit) |
| SEO | 100 |
| International | 90 (currency switcher pending a payment provider) |
| Legal / trust | 100 (Privacy, Terms, Refund policy, cookie consent) |
| Conversion | 100 (CTA above fold, labeled forms, sanitized exports) |

Full evidence: [docs/MARKET_PERFORMANCE.md](docs/MARKET_PERFORMANCE.md). Re-run any time:

```bash
POST https://<your-agent>/api/market-audit {"url": "https://your-site.vercel.app"}
```
## Deploy to Vercel (as shipped)

The repository contains two deployable units and a matching Vercel setup:

1. **Database** — add the Neon integration to the project (Storage → Neon, free plan). Vercel
   injects `DATABASE_URL`. Migrate once from your machine:

   ```bash
   cd backend
   DATABASE_URL="postgresql://…" node migrations/run.js
   ```

2. **API** — project `blogforge-api`, root `backend/`. `vercel.json` rewrites every path to
   `api/index.js`, which boots the Express app lazily and awaits `sequelize.sync()`. Set
   `DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `NODE_ENV=production`.

   ```bash
   cd backend && vercel link --project blogforge-api && vercel deploy --prod
   ```

3. **Frontend** — project `blogforge`, root `frontend/`. Set `VITE_API_URL` to the API production
   URL, then:

   ```bash
   cd frontend && vercel link --project blogforge && vercel deploy --prod
   ```

Full runbook, including disabling Deployment Protection and verifying the live flow:
see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Project structure

```
blogforge/
├── backend/
│   ├── api/index.js              # Vercel serverless entry (Express adapter)
│   ├── models/                   # Sequelize models (User, Article, Credit)
│   ├── migrations/               # Umzug migrations (users, records, articles, credits)
│   ├── routes/                   # auth, blog (SSE), records, ai, health
│   ├── middleware/               # JWT auth, validation + XSS, errors
│   └── server.js                 # Express app + local listen
├── frontend/
│   ├── src/pages/                # Generator, History, Credits, Login, Register, marketing
│   ├── src/layouts/              # Workspace shell with live credit balance
│   └── vercel.json               # Vite build + SPA fallback
├── docker-compose.yml            # Local Postgres + API + web
├── INSTRUCTIONS.md               # Extended operator guide
├── DEPLOYMENT.md                 # Vercel + Neon runbook
└── LICENSE.md
```

## Scripts

| Location | Command | Action |
|----------|---------|--------|
| `backend/` | `npm run dev` | API with nodemon |
| `backend/` | `npm run db:migrate` | Apply migrations |
| `backend/` | `npm run typecheck` | `tsc --noEmit` over JSDoc-typed JS |
| `frontend/` | `npm run dev` | Vite dev server |
| `frontend/` | `npm run build` | Production build (`dist/`) |

## Security

- Parameterized SQL through Sequelize; no string-built queries.
- Request bodies validated and HTML-escaped before persistence.
- JWT bearer auth, bcrypt (10 rounds), rate limiting, Helmet headers, CORS allow-list.
- Credit mutations are atomic and ownership-scoped (`userId` part of every query).
- Secrets only via environment variables; `.env` files are git-ignored.

## License

Commercial license — see [LICENSE.md](./LICENSE.md). One license per end product.
