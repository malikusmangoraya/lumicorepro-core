# INSTRUCTIONS — BlogForge

Production-ready full-stack application (React 19 + Vite · Express · PostgreSQL · Docker).

## 1. Prerequisites

| Tool | Version |
|------|---------|
| Node.js | >= 20 |
| Docker + Docker Compose | 24+ |
| PostgreSQL | 16 (or use the bundled container) |

## 2. Local Setup (no Docker)

```bash
# Backend
cd backend
cp .env.example .env          # set DATABASE_URL, JWT_SECRET
npm install
npm run db:migrate            # creates users + records tables
npm run dev                   # http://localhost:5000

# Frontend (second terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## 3. One-Command Docker Run

```bash
cp .env.example .env          # repo root — set POSTGRES_PASSWORD + JWT_SECRET
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:5000/api/v1 |
| PostgreSQL | internal (db:5432) |

Rebuild from scratch: `docker compose down -v && docker compose up --build`

## 4. Environment Variables

### Root (.env — used by docker-compose)

| Key | Required | Purpose |
|-----|----------|---------|
| `POSTGRES_PASSWORD` | yes | Postgres superuser password |
| `POSTGRES_USER` | no | default `postgres` |
| `JWT_SECRET` | yes | signs auth tokens (openssl rand -hex 32) |
| `ENCRYPTION_KEY` | yes* | 64-hex; encrypts stored AI API keys (*required for AI routes) |
| `AI_PROVIDER` | no | `openai` (default) / `gemini` / `openrouter` / `deepseek` |
| `OPENAI_API_KEY` | no* | one provider key is needed for AI features |
| `PGVECTOR_URL` | no | enables pgvector RAG; in-memory fallback without it |

### Backend (backend/.env)

| Key | Purpose |
|-----|---------|
| `DATABASE_URL` / `DB_*` | PostgreSQL connection |
| `JWT_SECRET` | token signing (rotate carefully) |
| `ENCRYPTION_KEY` | keyVault AES-256-GCM master key |

### Frontend (frontend/.env)

| Key | Purpose |
|-----|---------|
| `VITE_API_URL` | default `http://localhost:5000/api/v1` |

## 5. API Surface

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/api/v1/auth/register` | POST | name/email/password (bcrypt) |
| `/api/v1/auth/login` | POST | returns JWT |
| `/api/v1/records` | GET/POST | list/create — JWT required |
| `/api/v1/records/:id` | GET/PUT/DELETE | owner-scoped |
| `/api/v1/ai/generate` | POST | JSON or SSE stream (`stream:true`) |
| `/api/v1/ai/chat` | POST | RAG w/ sources |
| `/api/v1/ai/files` | POST | pdf/docx/txt upload -> indexed for RAG |
| `/api/v1/ai/health` | GET | provider + key status |
| `/api/v1/health` | GET | uptime probe (Docker HEALTHCHECK) |

## 6. Security Notes

- Passwords: bcrypt (10 rounds). Tokens: JWT (verify `JWT_SECRET` in prod).
- All DB writes: Sequelize parameterized queries (SQLi-safe).
- All request bodies: schema-validated + XSS-escaped (`middleware/validate.js`).
- Rate limiting on auth; helmet security headers on every response.
- Backend runs as non-root `appuser` inside Docker; uploads are 10 MB-capped + MIME-allowlisted.

## 7. TypeScript

The backend ships `tsconfig.json` (`checkJs: false`, JSDoc types retained) and shared domain types in
`backend/types/index.d.ts`. Run `npm run typecheck` in `backend/` to type-check.
The generated code is JavaScript with JSDoc types — incrementally migrate any
file to `.ts` and add `ts-node`/`tsc` when your team is ready.

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| ECONNREFUSED (backend) | Postgres not up: `docker compose up -d db` first |
| Migration failed | Check `DATABASE_URL`; run `npm run db:migrate` inside `backend/` |
| 401 on records | Token missing/expired — login again, check `Authorization: Bearer` |
| SSE shows nothing | Any proxy in front must disable buffering (nginx sample included) |
| AI 422 | `ENCRYPTION_KEY` wrong length (needs 64 hex) or provider key missing (`/api/ai/health`) |

## BlogForge API (AI Blog & SEO Content Generator)

| Endpoint | Method | Auth | Behavior |
|----------|--------|------|-------------|
| `/api/v1/auth/register` | POST | - | Account + **50 free credits** |
| `/api/v1/auth/login` | POST | - | JWT (7 days) |
| `/api/v1/blog/generate` | POST (SSE) | JWT | Streaming article: `meta` -> `chunk`s -> `done`. 1 credit/attempt, auto-refund on failure |
| `/api/v1/blog/history` | GET | JWT | Saved articles (paginated) |
| `/api/v1/blog/articles/:id` | GET/DELETE | JWT | Full article / delete |
| `/api/v1/blog/credits` | GET | JWT | Balance + usage |
| `/api/v1/blog/credits/topup` | POST | JWT | 10-5000 credits add |

**AI mode:** set `OPENAI_API_KEY` (or GEMINI/OPENROUTER/DEEPSEEK) in `.env` for real streamed articles.
**Demo mode:** with no key configured, a deterministic demo article is generated (UI shows a "demo" badge) ? the product runs without a key.
