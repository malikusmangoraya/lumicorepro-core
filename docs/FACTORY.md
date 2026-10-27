# Website Factory — generate, verify, deploy, film

One pipeline turns a generated project into a **delivered product**: a real website, a
tested API, a verified live deployment, and a ~2-minute demo video. Every stage emits
evidence; nothing is reported as done because a command exited 0.

```
generate → build → backend tests → browser QA → deploy → live verify → demo video → report
```

## Quick start

```bash
# 1. Generate a full-stack site (React + Express + PostgreSQL)
python ai-agent/main.py --fullstack-pro --prompt "Nimbus analytics platform" --dest generated-projects/nimbus

# 2. One prompt → generate + build + test + QA + deploy + verify + film
python ai-agent/main.py --deliver 'Build "Nimbus" an AI analytics copilot, deploy to vercel'
#    The plan is inferred from the sentence: brand, industry, deploy target
#    ("no deploy", "railway", "netlify", "github pages") and video opt-out
#    ("no video"). Override with --deliver-deploy / --factory-no-video.

# Or deliver a project that already exists on disk
python ai-agent/main.py --factory generated-projects/nimbus \
  --factory-name Nimbus --factory-tagline "Analytics for product teams"

# Build/test/video only (no external deployment)
python ai-agent/main.py --factory generated-projects/nimbus --factory-deploy none

# Verify any live URL without deploying
python ai-agent/main.py --verify-url https://example.vercel.app --verify-api /api/v1/health --factory-json
```

Exit code is `0` only when the run is `delivered` (every requested stage verified).
The report is written to `<project>/.factory/report.json` and `.factory/report.md`.

## What each stage proves

| Stage | Pass condition | Evidence |
|-------|----------------|----------|
| `build` | `npm run build` exits 0 **and** `frontend/dist/index.html` exists | command tail, dist path |
| `backend_tests` | generated backend `npm test` exits 0 (no tests = failure) | exit code, output tail |
| `qa` | browser QA reports `passed` at 375/768/1024/1440 | screenshots, console errors, overflow |
| `deploy` | platform CLI exits 0 and prints a URL | deployment id, URL |
| live verify | HTTP 200, real `<title>`, app shell, every referenced JS/CSS asset, every expected SPA route, optional marker + API health | status codes, failures, timings |
| `video` | ffprobe reports video stream + audio stream and duration within 30 % of the 120 s target | duration, resolution, codecs, scene list |

**API hosting is a separate stage by design.** Vercel/Netlify/GitHub Pages serve the
frontend only. When the project contains `backend/`, a run with a hosted API must pass
`api_health`; the live verifier then hits that endpoint and records `api_deployed: true`.
Without it the result stays `partial` with "the Express API is not deployed" — the
frontend may be live, but a full-stack claim would be false. Host `backend/` on
Railway/Render/Docker, set `VITE_API_URL` via `--factory-api-url`, and pass the health
path. The generated `backend/.env.example` lists every required variable.

`status: live` is never returned for an empty URL, a login wall, a platform error page, or
a broken bundle. The deploy result uses `deployed-unverified` instead, with the failing
checks attached.

## Deployment targets

| Platform | Mechanism | Requires |
|----------|-----------|----------|
| `vercel` | `vercel deploy --prod` (honours an existing `.vercel/project.json`) | `vercel` CLI logged in **or** `VERCEL_TOKEN` (+ `VERCEL_TEAM_SLUG`) |
| `netlify` | `netlify deploy --prod --dir <dist>` | `netlify` CLI + `NETLIFY_AUTH_TOKEN` (+ optional `NETLIFY_SITE_ID`) |
| `railway` | `railway up --detach` | `railway` CLI + `RAILWAY_TOKEN` + `RAILWAY_PUBLIC_DOMAIN` |
| `github-pages` | push `frontend/dist` to `gh-pages` and enable Pages | `GITHUB_TOKEN` (`repo` scope) or authenticated `gh` |

If credentials are missing the result is `guide` with exact commands — never a fake live URL.

## Demo video

`agent/demo_video.py` builds the film from the **real pages**:

1. Storyboard (9 scenes): intro card, home, features, pricing, register, dashboard, contact,
   mobile viewport, closing card.
2. Narration: **free online voices first** — Edge TTS, then gTTS (Google Translate,
   internet-only) — and the offline Windows SAPI voice (`Microsoft Zira Desktop`) as a
   last resort. Each scene records which backend produced the audio, so a silent or
   offline fallback is visible in the manifest, never hidden.
3. Capture: Playwright screenshots at 1920×1080 (desktop) and 430×932 (mobile). A page that
   fails to capture is replaced by a title card, and the failure is a warning — never a silent gap.
4. Assembly: ffmpeg renders one H.264/AAC clip per scene with a slow zoom, concatenates them,
   and writes `demo.srt`.
5. Verification: ffprobe must report both streams and a duration close to the target; the
   manifest lands in `.factory/video/manifest.json`.

Requirements: `ffmpeg`, `ffprobe`, Node + Playwright (repo `node_modules` is fine), and one
TTS backend: `edge-tts` (best voices), `gTTS` (free, internet-only fallback) or Windows
PowerShell (offline). `GET /api/factory/status` reports exactly what is missing.

```bash
pip install edge-tts gTTS   # both free
```

## Unique design system

`agent/design_forge.py` derives a complete visual system per brand, so two generated
projects no longer look identical:

- **Archetype** (`aurora`, `editorial`, `kinetic`, `precision`) chosen by a stable hash of
  brand + industry; industry hints (fintech → precision, legal → editorial, gaming → kinetic).
- **Tinted neutral scale** built from the brand hue: `slate-*` and `white` are overridden in
  the generated `tailwind.config.js`, so every page re-skins coherently without markup changes.
- **Two-font pairing** loaded from Google Fonts (IBM Plex Sans + Sora, Manrope + Fraunces,
  Space Grotesk, Plus Jakarta Sans) with system fallbacks.
- **Radius scale and accent glow**, plus CSS variables (`--brand-primary`, `--ink`) and a
  generated `font-display` class.

Because the palette is deterministic, the same brand always gets the same design; different
brands get measurably different systems (asserted in `tests/test_design_forge.py`).

## Hosting the Express API

Static hosts (Vercel/Netlify/Pages) serve the **frontend** only. The generated `backend/`
is a normal Express + PostgreSQL service; pick one:

| Option | Steps | Notes |
|--------|-------|-------|
| **Railway** | `railway login` → new project → add PostgreSQL → set envs → `railway up` from `backend/` | simplest; the factory can deploy with `RAILWAY_TOKEN` + `RAILWAY_PUBLIC_DOMAIN` and verify `/api/v1/health` |
| **Render** | New → Blueprint → repo's `render.yaml`, or a Web Service with `backend/` root | add the managed Postgres and copy `DATABASE_URL`; build `npm install`, start `npm start`, migrate `npm run db:migrate` |
| **Docker / VPS** | `cp .env.example .env` → `docker compose up -d --build` | the generated compose file runs Postgres + API + nginx; TLS via the proxy |
| **Vercel Functions** | `vercel link` + `vercel deploy --prod` from `backend/` | the generated backend already ships `api/index.js`, `vercel.json` and `.vercelignore`, and `server.js` only binds a port when run directly — this is the recipe verified below |

Proven path used for `cortexdesk-api` (2026-10-27, Neon + Vercel, `/api/v1/health` → `db: connected`):

```bash
cd generated-projects/<slug>/backend
npm install                                   # Vercel needs the lockfile
npx --yes vercel@latest project add <slug>-api --scope <team>
npx --yes vercel@latest link --project <slug>-api --yes --scope <team>
# one variable per line, VALUES never printed; strip CR from a Windows-authored file
while IFS= read -r l; do
  l="${l//[$'\r']/}"; k="${l%%=*}"; v="${l#*=}"
  printf '%s' "$v" | npx --yes vercel@latest env add "$k" production --scope <team>
done < api.env
npx --yes vercel@latest deploy --prod --yes --scope <team>
curl -s https://<slug>-api.vercel.app/api/v1/health
```

A trailing `\r` becomes part of the variable, so a CRLF env file silently corrupts
`DATABASE_URL`, `CORS_ORIGIN` and every API key — strip it, and never `echo` the values.

Required variables (all documented in `backend/.env.example`):

```
DATABASE_URL=postgres://user:pass@host:5432/db   # a postgresql:// URL is normalised
JWT_SECRET=<32+ random chars>
CORS_ORIGIN=https://your-frontend.example.com
AI_PROVIDER=groq
GROQ_API_KEY=<real key>          # or XAI_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY
ENCRYPTION_KEY=<64 hex chars>    # encrypts stored provider keys
PORT=5000
UPLOAD_DIR=/tmp/uploads          # serverless filesystems are read-only elsewhere
```

Managed Postgres is TLS-only and certificate verification stays on: `DB_SSL_CA`
supplies a root bundle for a self-signed host, `DB_SSL_INSECURE=true` is the
explicit opt-out. `/api/v1/health` runs `SELECT 1` and answers **503 + `db:
disconnected`** when the database is unreachable, because the delivery gate reads
this endpoint and a 200 that never opened a connection would certify a broken
deployment as live.

Then rebuild the frontend with that API base and verify both halves:

```bash
python ai-agent/main.py --factory generated-projects/my-site \
  --factory-api-url https://api.myproduct.com/api/v1
```

`--factory-api-url` is published as the Vercel project's `VITE_API_URL` **before**
the build (Vercel rebuilds the frontend from source, so a variable exported only
for the local `npm run build` never reaches the deployed bundle) and the verifier
fails the run with `api-not-baked` unless that host appears in the shipped JS.

The health endpoint itself needs no flag: it defaults to `api/v1/health`, the route
the generated `backend/` always serves. Pass `--factory-api-health` only for a
non-generated API, and write it **without a leading slash**:

```bash
--factory-api-health api/v1/health          # correct
--factory-api-health /api/v1/health         # Git Bash rewrites this
```

Git Bash/MSYS converts a leading-slash argument into `<msys-root>/api/v1/health`
before Python sees it, and `urljoin` reads the drive letter as a scheme, so the
value survives untouched and the "probe" targets a local file. The factory now
drops such a value, uses the generated default, and reports
`api-health-target-invalid` rather than probing it — the target is also logged as
`api_health_url` in the report so you can see exactly what was checked.

Only then is the run `delivered` (`api_deployed: true`). Chat features use the same
provider key: `POST /api/v1/ai/chat` performs RAG over uploaded documents and returns
sources; `/api/v1/ai/generate` streams with SSE.

## What you must provide

| Needed | Why | Where |
|--------|-----|-------|
| A real LLM key (`GROQ_API_KEY`/`GROK_API_KEY`, `XAI_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) | chat/generate endpoints; placeholders return 401 | `.env` / hosting env |
| A PostgreSQL URL | auth, records, contact, RAG | Railway/Render/Neon |
| Vercel CLI login (present on this machine) or `VERCEL_TOKEN` | frontend deploy | already configured |
| Railway token + public domain, or Render account | API deploy + health verification | Railway/Render dashboard |

## HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/factory/status` | toolchain preflight (ffmpeg, Playwright, TTS, CLIs) |
| `POST` | `/api/factory/run` | start a background delivery job |
| `GET` | `/api/factory/jobs` | recent jobs (no result payload) |
| `GET` | `/api/factory/jobs/{id}` | job status + full result |
| `POST` | `/api/factory/deliver` | one prompt → generate → full pipeline (background) |
| `POST` | `/api/factory/verify` | verify a URL (assets, routes, marker, API health) |
| `GET` | `/api/factory/jobs/{id}/events` | **SSE** progress stream (stage, status, detail, timestamp) |

### Real-time progress

`POST /api/factory/deliver` (or `/run`) returns a `job_id`. Subscribe to the SSE
stream to watch every stage as it happens:

```bash
curl -N -H "X-API-KEY: $AGENT_API_KEY" \
  http://localhost:5000/api/factory/jobs/<job_id>/events
# event: progress  {"stage":"build","status":"running"}
# event: progress  {"stage":"build","status":"done","dist":".../dist"}
# ...
# event: done      {"status":"done"}
```

The CLI prints the same events to stderr (`[generate] done`, `[deploy] done`, …)
while stdout stays machine-readable JSON under `--factory-json`.

All endpoints use the agent API key (`X-API-KEY`) and the shared rate limiter.

```json
POST /api/factory/run
{
  "project_dir": "generated-projects/nimbus",
  "platform": "vercel",
  "video": true,
  "name": "Nimbus",
  "tagline": "Analytics for product teams"
}
→ { "success": true, "data": { "job_id": "…", "status": "queued", "poll": "/api/factory/jobs/…" } }
```

## Reference run (2026-10-24)

| Artifact | Evidence |
|----------|----------|
| Live frontend | https://nimbus-analytics-demo.vercel.app/ — verified: 6 SPA routes 200, both bundle assets loaded |
| API hosting | Not hosted for this demo (no database credentials); under the current gate that run reports `partial`, never `delivered` |
| Demo video | `.factory/demo.mp4` — 120.02 s, 1920×1080, H.264 + AAC, 9 narrated scenes, SRT included |
| QA | 0 console errors, 0 page errors, 4 collapse samples at 375/768/1024/1440 |
| Backend | 5 `node --test` tests green |
| Report | `.factory/report.json` → `status: delivered`, `verified: true` |

That run used the offline Windows SAPI voice because Edge TTS returned HTTP 403 on
this network; the fallback is part of the pipeline, not a workaround.

## Failure policy

- A failed build or backend test stops the run before anything is published.
- Browser QA is a hard gate by default (`allow_qa_fail` exists for deliberate exceptions and
  is recorded in the report as a failure).
- An unverified deployment or video keeps the run `partial`; it is never `delivered`.
- Toolchain gaps return `unavailable` with the missing list instead of a half-made artifact.
