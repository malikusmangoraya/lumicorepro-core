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

# 2. Deliver it: build, test, QA, deploy to Vercel, verify, film
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
2. Narration: Edge TTS when the network allows it, otherwise the offline Windows SAPI voice
   (`Microsoft Zira Desktop`); each scene records which backend produced the audio.
3. Capture: Playwright screenshots at 1920×1080 (desktop) and 430×932 (mobile). A page that
   fails to capture is replaced by a title card, and the failure is a warning — never a silent gap.
4. Assembly: ffmpeg renders one H.264/AAC clip per scene with a slow zoom, concatenates them,
   and writes `demo.srt`.
5. Verification: ffprobe must report both streams and a duration close to the target; the
   manifest lands in `.factory/video/manifest.json`.

Requirements: `ffmpeg`, `ffprobe`, Node + Playwright (repo `node_modules` is fine), and either
`edge-tts` or Windows PowerShell. `GET /api/factory/status` reports exactly what is missing.

## HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/factory/status` | toolchain preflight (ffmpeg, Playwright, TTS, CLIs) |
| `POST` | `/api/factory/run` | start a background delivery job |
| `GET` | `/api/factory/jobs` | recent jobs (no result payload) |
| `GET` | `/api/factory/jobs/{id}` | job status + full result |
| `POST` | `/api/factory/verify` | verify a URL (assets, routes, marker, API health) |

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
| Live site | https://nimbus-analytics-demo.vercel.app/ — verified: 6 SPA routes 200, both bundle assets loaded |
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
