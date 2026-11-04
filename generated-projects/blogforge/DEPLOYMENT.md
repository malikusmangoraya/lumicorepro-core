# Deployment Runbook — Vercel + Neon

This is the exact configuration used for the live demo:

| Surface | URL | Vercel project |
|---------|-----|----------------|
| Web app | https://blogforge-lumicorepro.vercel.app | `blogforge` (root `frontend/`) |
| API | https://blogforge-api.vercel.app | `blogforge-api` (root `backend/`) |
| Database | Neon Postgres (free plan) | Marketplace integration on `blogforge` |

## 1. Provision the database

1. Vercel dashboard → your project → **Storage** → **Neon** → install (free plan).
2. Neon injects `DATABASE_URL` (pooled) into the project. Copy the value, or pull it:

   ```bash
   vercel env pull .env.local
   ```

3. Apply migrations once from your machine (use the **unpooled** URL for DDL):

   ```bash
   cd backend
   DATABASE_URL="postgresql://user:pass@ep-…-pooler.region.aws.neon.tech/db?sslmode=require" \
     node migrations/run.js
   ```

   Expected output: `001_create_core_tables` → `002_create_records_table` →
   `003_create_articles_and_credits`, each `migrated`.

> `sequelize.sync()` also runs at API cold start, so a fresh database self-heals. Migrations
> remain the source of truth for schema changes.

## 2. Deploy the API

```bash
cd backend
vercel link --project blogforge-api
vercel env add DATABASE_URL production        # pooled Neon URL
vercel env add JWT_SECRET production          # node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
vercel env add ENCRYPTION_KEY production      # node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
vercel env add NODE_ENV production            # value: production
vercel deploy --prod
```

What `backend/vercel.json` does:

```json
{
  "functions": { "api/index.js": { "maxDuration": 60 } },
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index.js" }]
}
```

- `api/index.js` awaits `app.initDb()` (Sequelize sync) once per cold start, then forwards the
  request to the Express app. The original path is preserved, so `/api/v1/...` routes match.
- `maxDuration: 60` keeps SSE generation inside the Hobby limit.

Verify:

```bash
curl https://blogforge-api.vercel.app/api/v1/health
# {"status":"healthy","timestamp":"…","uptime":…}
```

## 3. Deploy the frontend

```bash
cd frontend
vercel link --project blogforge
vercel env add VITE_API_URL production        # https://blogforge-api.vercel.app/api/v1
vercel deploy --prod
```

`frontend/vercel.json` pins the Vite build and SPA fallback:

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

`VITE_API_URL` is baked in at build time — re-deploy after changing it.

## 4. Make the deployment public

New Vercel projects enable **Deployment Protection** (Vercel Authentication), which shows a
Vercel SSO login instead of your app. Disable it per project:

- Dashboard → Project → **Settings → Deployment Protection** → Vercel Authentication → **Disabled**;
  or via REST:

  ```bash
  TOKEN=$(node -e "console.log(require(process.env.APPDATA + '/com.vercel.cli/Data/auth.json').token)")
  curl -X PATCH "https://api.vercel.com/v9/projects/PROJECT_ID?teamId=TEAM_ID" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"ssoProtection":null}'
  ```

  `PROJECT_ID`/`TEAM_ID` live in `.vercel/project.json`.

## 5. Live verification checklist

```bash
# 1. Landing page returns the app (not Vercel SSO)
curl -s https://blogforge-lumicorepro.vercel.app/ | grep -o '<title>[^<]*'

# 2. API health
curl -s https://blogforge-api.vercel.app/api/v1/health

# 3. Register → 50 credits
curl -s -X POST https://blogforge-api.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo","email":"demo+1@example.com","password":"Password123!"}'

# 4. Stream an article (requires JWT from step 3)
curl -N -X POST https://blogforge-api.vercel.app/api/v1/blog/generate \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"keyword":"ai seo tools","tone":"professional","length":"short","audience":"marketers"}'
```

Expected: `event: meta` (`demo:true` when no provider key), 20+ `event: chunk`, one `event: done`;
the credits balance decreases by 1 and the article appears in `/blog/history`.

## 6. Enabling real AI output

Add one provider key to the API project and redeploy (or store it at runtime through the key
vault):

```bash
vercel env add OPENAI_API_KEY production
vercel deploy --prod --yes
```

Without a key the product stays fully functional in demo mode.

## 7. Local ↔ production parity

| Concern | Local | Vercel |
|---------|-------|--------|
| Database | `DB_*` env vars | `DATABASE_URL` (SSL auto-enabled) |
| API URL | `http://localhost:5000/api/v1` | `https://blogforge-api.vercel.app/api/v1` |
| Build | `npm run dev` | `npm run build` → `dist/` |
| Migrations | `npm run db:migrate` | run once against Neon |
| SSE | native | Node streaming, `maxDuration: 60` |

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Vercel SSO page instead of app | Deployment Protection still on — disable it (step 4) |
| `401 Authorization required` | Missing/expired JWT — log in again, send `Authorization: Bearer <token>` |
| `503 Database unavailable` | `DATABASE_URL` missing on the API project or Neon suspended |
| `relation "articles" does not exist` | Run migrations against the production `DATABASE_URL` |
| SSE arrives all at once | A proxy is buffering — disable buffering; Vercel streams natively |
| `ENCRYPTION_KEY must be 64-char hex` | Generate with `randomBytes(32).toString('hex')` |
| Frontend calls `localhost` | `VITE_API_URL` missing at build time — set it and redeploy |
