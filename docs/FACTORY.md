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

# Local web-app/PWA proof (no external deployment)
python ai-agent/main.py --deliver "Build a records web app with offline support" \
  --deliver-web web-app --deliver-pwa --deliver-deploy none

# Local Android app verification (no external deployment)
python ai-agent/main.py --deliver "Build an Android records app" \
  --deliver-web none --deliver-mobile android --deliver-deploy none

# Check Android prerequisites; install is a separate, explicit action
python ai-agent/main.py --android-toolchain check
```

Exit code is `0` only when the run is `delivered` (every requested stage verified).
The report is written to `<project>/.factory/report.json` and `.factory/report.md`.
Local-only runs can report `built`; fixture-backed app runs and incomplete hosted runs
remain `partial`, never `delivered`.

## What each stage proves

| Stage | Pass condition | Evidence |
|-------|----------------|----------|
| `build` | `npm run build` exits 0 **and** `frontend/dist/index.html` exists | command tail, dist path |
| `backend_tests` | `npm install` in `backend/` succeeds, the project owns at least one `*.test.js`, and `npm test` exits 0 | install + test tails, cwd |
| `qa` | a complete rendered matrix: every expected route at 375/768/1024/1440/1920, a visible route-specific heading inside `<main>`, readable full-page PNGs at the requested width, no console/page/required-asset errors, no visible overflow, and a usable reduced-motion load (from navigation, not toggled afterwards) | `qa/qa-report.json`, per-route screenshots, bounded diagnostics |
| `pwa` | Requested PWA worker controls the app, offline reload shows the fallback, connectivity recovers, and the authenticated records queue proves UUID replay, retry, and the 50-item limit | `qa/qa-report.json`, offline screenshot, measured queue evidence |
| `mobile_export` | Expo exports Android, iOS, and web bundles and `tsc --noEmit` passes | `mobile/dist/`, command evidence |
| `mobile_apk` | Android prebuild and `assembleDebug` pass; APK package/minimum SDK match app config | APK path + SHA-256 + metadata in `.factory/mobile/` |
| `mobile_emulator` | Emulator boots; APK installs and launches; logcat is clean; Maestro smoke and records flows pass | `.factory/mobile/emulator.json`, Maestro results and screenshots |
| `live_qa` | the same matrix, plus requested-3D proof, runs against the **final hosted origin** after the API-origin rebuild and CORS lock | `qa/live/qa-report.json`; scene canvas pixels, frame/draw-call observations, interaction change |
| `database` | a per-product Postgres database exists, its URL was handed to the API **and** written into the delivered `backend/.env` | database name, host (never the credential) |
| `schema` | `node backend/migrations/run.js` answers one JSON line with `ok: true` against the URL just provisioned, **before** anything is deployed — and it may be run twice: every `up()`/`down()` goes through `_guards.js`, which creates only what Postgres does not already have | `applied` count, migration names, `uptodate`/`missing` status |
| `api` | `backend/` is deployed and its hosted `/api/v1/health` answers 200 with `db: connected` | API URL, health URL, deployment id |
| `deploy` | the platform CLI prints a URL **and** `verify_site` passes against it — an exit code alone is not a delivery | deployment id, URL, per-check evidence |
| live verify | HTTP 200, real `<title>`, app shell, every referenced JS/CSS asset, every expected SPA route, optional marker + API health | status codes, failures, timings |
| `handshake` | four proofs against the live origin: `/api/v1/health` answers `db: connected`; `POST /api/v1/contact` writes a row and returns an id; `verify_api_surface()` walks register → login → list → create → read-back → update → rejects a blank title → proves a **second** account cannot read, list or delete the first one's rows → proves `GET /records` is not world-readable → deletes the probe row and expects a 404; `verify_realtime_feed()` opens `GET /api/v1/events`, waits for `event: ready`, writes a row and requires a `record:changed` frame carrying that id | health body, probe row id, endpoints proved, feed latency in ms, rows left behind |
| `video` | ffprobe reports video stream + audio stream and duration within 30 % of the 120 s target | duration, resolution, codecs, scene list |

### App surfaces and mobile verification

Before running surface-specific stages, the factory validates `app-contract.json`;
the report records `requested_surfaces` and `skipped_surfaces`. Invalid contracts
fail closed.

Prompt routing defaults to website-only. A web app is an authenticated frontend;
“app” or “mobile” requests an Expo project, “website and app” requests both, and
PWA is an additive capability on a requested web surface. Use `--deliver-web` and
`--deliver-mobile` to make the desired surfaces explicit. `--deliver-pwa` requires
`--deliver-web website` or `--deliver-web web-app`; `--deliver-mobile-verify`
requires `--deliver-mobile android`.

The Android check is non-installing:

```bash
python ai-agent/main.py --android-toolchain check
```

Installing SDK packages is a separate, explicit operation. Run this only if you
accept the Android SDK package licenses:

```bash
python ai-agent/main.py --android-toolchain install --accept-licenses
```

The factory does not install Android tooling as a side effect of generation or
delivery. An install request without `--accept-licenses` fails before downloading
packages. If the toolchain is missing, mobile verification is `blocked`; a failed
export, APK, emulator, logcat, or Maestro step prevents a pass.

`app_runs` uses the factory's temporary, in-memory fixture API and is explicitly
not production backend evidence. It can prove that the generated app runs and
that the Android emulator reaches the fixture, but it cannot prove hosted API or
database behavior. `full_stack` requires a live API + database and the factory's
backend handshake as well as a passing emulator journey. An app-only run without
those proofs cannot be `delivered`; it remains `partial`. A website or web-app
run with its requested local stages passing and no hosting is `built`, not
`delivered`; a fixture-backed mobile run remains `partial`. Reports include the
APK hash and verification tier; they do not include test credentials.

Expo platform export and TypeScript checks do not imply iOS signing, device
verification, or App Store distribution.

### The surface contract

Every generated project ships `app-contract.json` at its root. It is written by
`fullstack_ultra_engine` and re-read by `factory_pipeline.read_app_contract` before
the first stage runs; it is the only input that decides which stages exist.

| Field | Values | Rule |
|-------|--------|------|
| `version` | the integer `1` | any other value, a missing key, a non-object or invalid JSON fails the run with `Invalid app contract: …` |
| `web` | `website`, `web_app`, `none` | decides whether `build`, `qa`, `deploy` and `live_qa` run at all |
| `pwa` | boolean | `true` requires a web surface; `pwa: true` with `web: "none"` fails closed |
| `mobile` | `null`, or `{platforms, verification}` | `platforms` is a non-empty list without duplicates drawn from `android`/`ios`; `verification` is `apk_emulator` or `none` |

`web: "none"` with `mobile: null` is rejected — a contract must request at least one
client surface. A project with no `app-contract.json` is a legacy website and keeps
the old behaviour. Validation messages name the category that failed and never echo
the rejected value.

`generation_contract._app_from_prompt` is what turns a sentence into that file:

| Prompt says | `web` | `mobile` | Generated tree |
|-------------|-------|----------|----------------|
| website, landing page, storefront, web | `website` | — | `frontend/` + `backend/` (the existing lane) |
| web app, internal app, admin app, admin dashboard, management app/system | `web_app` | — | `app_layouts.py` shell in `frontend/` + `backend/` |
| app, mobile app, android app, ios app, react native | `none` | android | `backend/` + `mobile/`, and no `frontend/` at all |
| website and app, web + mobile, mobile and web, a bare "both" | `website` | android | `frontend/` + `backend/` + `mobile/` |
| dashboard and mobile app | `web_app` | android | app shell + `backend/` + `mobile/` |
| pwa, installable, offline app | as stated | as stated | adds the PWA files to that web surface |

PWA is only ever additive: `--deliver-pwa` requires `--deliver-web website` or
`--deliver-web web-app`, and a prompt that does not name it never produces one. An
explicit `app` block from the CLI or HTTP payload always wins over prompt words, and
a surface nobody asked for is never generated.

### Tiers and statuses

`report.json` carries `requested_surfaces`, `skipped_surfaces` and `mobile_tier`. The
tier is the honest label for how far mobile got:

| `mobile_tier` | Set when | Ceiling for the run |
|---------------|----------|---------------------|
| `not_requested` | `mobile` is `null` in the contract | unchanged website lane |
| `not_run` | mobile requested, but the run never reached a mobile stage | — |
| `not_verified` | `verification: "none"` — export only, no APK, no emulator | never `delivered` |
| `blocked` | toolchain not ready, fixture API or its health evidence missing, or the volume cannot hold the AVD's declared data partition | `partial` |
| `failed` | export failed, APK build failed, the build returned no APK path, or the emulator stage failed | `partial` |
| `app_runs` | the full emulator journey passed against the loopback fixture API | `partial` — a fixture is not backend evidence |
| `full_stack` | the same journey passed against the hosted API and the provisioned database, with the handshake proven | may be `delivered` |

`delivered` is the same bar it has always been, applied to the requested surfaces: the
product's own migrations against a provisioned database, a hosted API answering
`db: connected`, a verified deployment, the handshake, and — when the contract requests
mobile — a `full_stack` mobile journey. A local-only run whose every stage passed is
`built`; an incomplete hosted run is `partial`; an invalid contract or a hard stage
failure is `failed`.

### Mobile CLI surface

| Flag | Effect |
|------|--------|
| `--deliver-web website`/`web-app`/`none` | which web surface is generated; `none` means app-only |
| `--deliver-mobile android`/`none` | whether an Expo project and the mobile stages exist at all |
| `--deliver-pwa` | adds PWA to the requested web surface; without `--deliver-web` it is a parser error |
| `--deliver-mobile-verify apk-emulator`/`none` | `none` generates and exports only, records tier `not_verified`, and keeps the run below `delivered`; requires `--deliver-mobile android` |
| `--android-toolchain check` | reports `ready`, `java17`, `sdk`, `adb`, `emulator`, `avd`, `maestro`, `gradle_home`, `cmake`, `disk_free_gb`, `missing` and `cmake_gap` — nothing downloaded, nothing changed; exits 0 only when ready |
| `--android-toolchain install --accept-licenses` | installs the pinned set (JDK 17 under `D:/tools/jdk17`, SDK at `D:/android-sdk`, AVD `lumicore_api35` in `D:/android-avd`, Maestro at `D:/tools/maestro`, Gradle cache `D:/gradle-cache`, `cmake;3.31.6` among the SDK packages) and writes the resolved paths to `ai-agent/.env.android`. It refuses to run without `--accept-licenses` and aborts before downloading when the target volume has less than 14 GB free |

`--factory-json` makes both print machine-readable JSON on stdout. Generation and
delivery never install tooling as a side effect: a missing piece is a `blocked` mobile
stage that names it.

### What the buyer receives under `.factory/mobile/`

| File | Written by | Contents |
|------|-----------|----------|
| `apk.json` | `mobile_verify.build_apk` | APK path, SHA-256, `package`, `min_sdk`, the ABI actually compiled, the JS bundle found inside `assets/` (a build that produced no bundle fails before this file is written), and the API origin baked into the bundle |
| `health.json` | `factory_pipeline` and `mobile_verify.verify_mobile` (app_runs) | the fixture API's health payload marked `"fixture": true`, with its loopback URL |
| `emulator.json` | `mobile_verify.verify_emulator` | `booted`, `boot_seconds`, `installed`, `launched`, `app_pid`, `logcat_clean`, the AVD volume with its declared data partition and free space, and the three log windows the verdict is read from (the app's own `--pid` window, the crash buffer, the events buffer) — passwords, tokens and the test account email are redacted inside them |
| `emulator-boot.log` | `verify_emulator` | the emulator's own stdout/stderr for the attempt, so a failed boot carries the emulator's diagnosis rather than a bare timeout |
| `maestro/smoke.json`, `maestro/records.json` | `verify_emulator` | per-flow pass flag, exit code and output tails, credential-redacted |
| `maestro/screenshots/…` | `_copy_maestro_screenshots` | the PNGs `maestro test` wrote under `mobile/.maestro/test-results/<flow>/` |
| `verify-mobile.json` | the local acceptance driver `generated-projects/premium-verification/run_mobile_proof.py` | one `verify_mobile` report (export, build, emulator, tier, errors). A factory run carries the same verdicts as `stages.mobile_export`, `stages.mobile_apk` and `stages.mobile_emulator` in `.factory/report.json` |

The tier, the APK path and hash, the Maestro verdict and what the test account does or
does not prove are repeated in the **Client handoff** block of `.factory/report.md`,
and every skipped, blocked or unmeasured stage is listed under **Not proven**. No
credential appears in any of these files.

### What can pass today (2026-10-29)

The state of this branch, from the execution ledger and the evidence on disk:

| Stage | Verdict today |
|-------|---------------|
| surface routing and generation | measured passing for the representatives on disk under `generated-projects/premium-verification/prompt-controlled-app-system-2026-10-28/` (website-only, web-app + PWA, app-only with no `frontend/`, website + Android); the `web_app` + mobile combination is routed and unit-covered (`test_generation_contract.py`) but has no generated representative |
| `build` and `qa` for a `web_app` | measured passing — a real Chromium matrix of 25 route/width samples against the built shell |
| `pwa` | measured passing — worker control, offline reload, recovery, and the queue with UUID replay, the 50-item cap, 3 retries and failed-flush retention |
| `build` and `qa` for a `website` | the lane is unchanged, but this branch's 35-sample run recorded one blank `/pricing` sample at 1920 px while the host was under Gradle load; the isolated route passed and the full re-run is outstanding. Note on the folder itself: `prompt-controlled-app-system-2026-10-28/website-only/qa/` currently holds 34 captures from that 35-sample matrix beside the isolated re-run's one file and a `qa-report.json` that measures only the latter — read the report, not the file count. `browser_qa` now prunes captures a run did not measure, so a re-run will not repeat that |
| `mobile_export` | measured passing — android, iOS and web bundles exported with `tsc --noEmit` clean |
| `mobile_apk` | measured passing twice, and only the second one is a deliverable: proof8's 74,101,673-byte x86_64 APK (`com.lumicore.northstar`, minSdk 24) carried no JavaScript at all — `assets/app.config` and `assets/app.fingerprint` only, because `react.debuggableVariants` defaults to listing `debug` — while proof11's gated build (sha256 `8d818fb3…`, 11m 43s Gradle) reports `js_bundle: index.android.bundle`. That same artifact, re-checked against proof11's `apk.json` by sha256 before every run, is the one proof12, proof13 and proof14 put on a real device |
| `mobile_emulator` | measured passing for boot, install, launch and logcat on twice-separated attempts, never as a whole stage: proof12 (05:42:13→05:53:44, 690 s) and proof14 (06:23:59→06:36:41, 759 s) each recorded `booted=True` (275 s and 293 s against the measured 900 s budget), `installed=True`, `launched=True` (`app_pid` 2563 and 2699), `logcat_clean=True` with an empty crash buffer, and their own `emulator.json` with the AVD volume, the 2,048 MB partition and its free megabytes (4,644 MB and 5,668 MB) — proof12's file does **not** carry `avd_ram_size`, because that field did not exist when it ran; proof14's is the first, reading `1536`. proof13 (158 s) booted in 125 s and then lost the device during `adb install` — killed by the operator mid-run, not by the product — and it is the run that proved the teardown gap: it left **no** `emulator.json` on disk at all, only `emulator-boot.log`, so its measurements existed in a scratch driver's stdout until `verify_emulator` began writing the file from its `finally`. That `finally` path has run live once, on proof14, which reached its normal end — the mid-run-death case is covered by `test_a_run_that_dies_after_the_boot_still_leaves_its_measurements_behind`, not yet by a device run. `_emulator_disk_gap` reproduces the volume blocker in milliseconds; the launch verdict is attributed to the app's pid rather than to the whole device. The proofs use an AVD whose declared data partition was lowered to 2,048 MB (`config.ini.6gb.orig` holds the 6 GB original) and whose `hw.ramSize` was lowered from 2G to 1536 (`config.ini.2g-ram.orig`) — a CI-sized rig, not a phone |
| Maestro | run against the installed app twice (proof12, proof14) and failed both times, with the cause now named by the product itself: `Maestro smoke flow failed: Assertion is false: "Sign in" is visible while the device itself was showing "System UI isn't responding"`, and the same device-owned dialog on `records` at `"Create your account"`. Screenshots and screen hierarchies do exist now, in `proof14/maestro/` — and that same folder carried proof12's 45,562-byte `step-004-assertCondition-Sign_in.png` under `screenshots/.maestro/test-results/smoke/2026-10-29_054800/` beside its own two captures, which is the inherited-evidence defect the clearing, pairing and owned-directory copy gates now close; those three have unit and mutation coverage but **no live run yet**, because proof14 predates them, so the next emulator proof has to measure them on the real tool. What is *not* claimed: that the app would have passed those assertions on a healthy device — proof12's captured hierarchy held only the ANR dialog's four strings, so the app's own screen was never observed by Maestro. Both failures were recorded while the host had 0.71–0.73 GB free of 7.89 GB, and lowering the guest from 2 GB to 1,536 MB changed nothing, so the outstanding remedy is free host RAM (CI) or a physical device |
| `full_stack` mobile | never reached |
| iOS | `not_measured`, and not a delivery claim |

So a run that requests mobile ends `partial` or `blocked` today. The gate, the
generator, the APK build and the emulator stage exist and fail closed; mobile delivery
has not yet been proven end to end, and no report should read as if it had.

**A project with `backend/` hosts itself.** When no `--factory-api-url` is passed, the
run provisions a database (`agent/db_provision.py`), deploys `backend/` to its own
`<slug>-api` project (`deploy_engine.deploy_backend`), bakes that origin into
`VITE_API_URL`, redeploys the API with `CORS_ORIGIN` pinned to the frontend, and only
then calls the API a success. `delivered` additionally requires the handshake stage — a
health endpoint alone proves the process started, not that a client can save data, that the
dashboard's own routes answer, or that the change feed pushes. Each probe deletes the rows it
created, and the session token it signed with never enters the report. This
needs `FACTORY_DATABASE_TEMPLATE_URL` in `ai-agent/.env` (the legacy
`NEON_TEMPLATE_DATABASE_URL` still resolves); without it the run stops as
`database not provisioned` instead of shipping a form that cannot write. The
server may be from any provider — the runner speaks plain PostgreSQL over `pg`,
so Neon, Supabase, Render, Railway or your own cluster all work. Two
requirements: the role must be able to `CREATE DATABASE`, and it must accept TLS.

**API hosting is a separate stage by design.** Vercel/Netlify/GitHub Pages serve the
frontend only. When the project contains `backend/`, a run with a hosted API must pass
`api_health`; the live verifier then hits that endpoint and records `api_deployed: true`.
Without it the result stays `partial` with "the Express API is not deployed" — the
frontend may be live, but a full-stack claim would be false. Host `backend/` on
Railway/Render/Docker, set `VITE_API_URL` via `--factory-api-url`, and pass the health
path. The generated `backend/.env.example` lists every required variable.

`status: live` is never returned for an empty URL, a login wall, a platform error page, or
a broken bundle. The deploy result uses `deployed-unverified` instead, with the failing
checks attached, and a deployment that answers with the Vercel login page is reported as
`deployed-protected` — hosted, unreachable, and never a delivery.

## Generated page identity and 3D

Each generated project writes an independent `qa-contract.json` beside the app:
the expected visible heading for `/`, `/features`, `/pricing`, `/about`,
`/contact`, `/login` and `/register`. The browser stage loads this manifest; a
route whose main content does not render that heading fails identity. It never
derives the expectation from the page it is checking.

Public pages come from `agent/premium_layouts.py` and the brand's composition in
`design_forge.py`. The four archetypes change hero structure and section order,
not only colours. Generated copy names only capabilities the project actually
ships (account access, editable records, contact form); it carries no invented
uptime, certification, customer count, price or payment claim. Marketing chrome
(a newsletter, currency selector, live-status badge) is emitted only when a real
implementation backs it.

### Real 3D is opt-in and request-scoped

```bash
python ai-agent/main.py --deliver "Prism records workspace" --deliver-scene cyber_grid
python ai-agent/main.py --deliver "Prism product showroom" \
  --deliver-scene product_viewer --deliver-model ./owner-assets/chair.glb
```

Supported genuine scenes: `floating_crystal`, `cyber_grid`, `particle_cosmos`,
`product_viewer`. A plain `3d`/`webgl` prompt requests `floating_crystal`; a
showroom/product prompt without a model fails before any file is written. Models
are owner-supplied local GLB/glTF 2.0 files, validated (size, header/JSON chunk,
local resources, no scripts, no traversal or symlink escape) and bundled under
`frontend/public/assets/models/<hash>/`. No remote model is fetched, and the HTTP
factory payload accepts no local model path.

The scene loads lazily only after **Enable 3D**. It renders original geometry (or
the supplied model) on demand with explicit Rotate/Zoom/Reset controls, a visible
failure and retry state, and a static mobile/fallback view. When the contract
requests a scene, delivery requires a desktop activation followed by nonblank
canvas pixels, frame and draw-call observations, and a measurable pixel change
after a rotate action. A fallback, a canvas attribute or a source marker never
satisfies that proof. A context loss or missing model fails the scene.

Generic `Benchmark3DFactory` verticals other than the implemented real-estate
lane now fail before writing files instead of emitting a README and claiming
success.

## Environment blocks

Windows App Control judges a native binary by file hash, so a freshly written
`@rollup/rollup-win32-x64-msvc` can be refused while an older copy of the same package
loads all day. `npm run build` then dies with `ERR_DLOPEN_FAILED` before anything is
deployed — on generated code that was never the problem.

`agent/native_binary_repair.py` handles it inside the build stage: it reads the blocked
path out of the refusal, finds the same package in another install **in this repository**
(exact version preferred, otherwise the same `major.minor`), copies it over, and retries —
at most twice, and only for a file inside the project being built. Nothing is downloaded,
and the report carries a warning naming both versions, so the substitution is auditable
instead of silent. With no compatible copy the run stops as `no-compatible-copy` and tells
you to unblock the file in Windows Security; it never guesses at a binary. A normal
compile error is still a hard stop after a single build attempt.

### Deployment protection

A project created by the CLI inherits the team's **Require Vercel Authentication**
default. Every `*.vercel.app` URL then answers HTTP 200 with a login page: the API is
really running, the health probe sees HTML instead of JSON, and no client — or verifier —
can get through. The factory therefore runs

```
vercel project protection disable <project> --sso
```

for the API project before the first probe, repeats it and re-verifies for a frontend that
still shows a wall, and records the result as `protection` in the deploy evidence. If the
wall survives, the stage is `deployed-protected` and the failure line names the project and
the command, because at that point it is an account permission, not something the pipeline
can switch. A missing asset never triggers this path — protection cannot fix a broken
bundle, and pretending otherwise would blame the platform for the project's own defect.

### Which API URL gets baked

`vercel deploy --prod` prints two addresses: the permanent project domain on the
`▲ Aliased` line and a per-deployment URL (`<name>-<hash>-<team>.vercel.app`) that is
minted again on the next run. Only the aliased domain is baked into the shipped bundle —
a deployment URL would move the API out from under a build the client already has. The
short `https://<name>.vercel.app` form is global and can belong to a different tenant, so
it is used only when the CLI printed it; otherwise the factory probes what the CLI
actually reported and keeps the first host that answers with the generated health payload.

## Client handoff

`.factory/report.md` ends with a **Client handoff** block generated from the real
evidence, so the message you paste to a client cannot contain an URL that was never
verified:

```
## Client handoff

- **Frontend (live):** `https://<slug>.vercel.app`
- **API (live):** `https://<slug>-api.vercel.app` (or `<slug>-api-<word>.vercel.app` when
  the short domain is already taken — the report always prints the one that answered)
- **API health:** `https://<slug>-api.vercel.app/api/v1/health`
- **Database:** `<slug>@ep-xxx-yyy.us-east-1.aws.neon.tech`
- **Demo video:** `.factory/demo.mp4` (narration and subtitles in `.factory/video/`)
- **API runtime variables set:** DATABASE_URL, JWT_SECRET, ENCRYPTION_KEY, BRAND_NAME,
  APP_URL (values are stored on the hosting platform, never in this report)
- **Form round-trip:** a real inquiry was stored (row `7`) — delete it before the demo
  if you want an empty inbox
- **Secrets:** the signing/encryption keys live in `backend/.env` and on the hosting
  platform. Rotate them if either is shared.

## Not proven

Nothing — every stage above was verified against the live deployment.
```

Anything the pipeline could not prove is listed under **Not proven** — never omitted,
never softened into a pass. The probe row exists because a 200 from `/health` does not
prove a form can save; the run inserts one real row and reports its id so you can remove
it.

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

By default the factory hosts it for you — see "A project with `backend/` hosts itself"
above. The table below is for **bringing your own** API host, in which case pass
`--factory-api-url` and the run skips provisioning and only verifies what you handed over.

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

### What lands in the delivered `backend/.env`

When the factory provisions the database itself, it writes the resolved `DATABASE_URL`
into `backend/.env` beside the generated `JWT_SECRET` and `ENCRYPTION_KEY`. The hosted API
receives the URL as an argument either way, so omitting it used to produce a delivery that
verified `db: connected` remotely while the delivered folder's own `npm run db:migrate` read
an env file with no database and quietly targeted localhost. `CORS_ORIGIN` is the one value
that is **not** written locally: the CORS-lock pass passes the production origin, and a
delivered server pinned to it would refuse its own dev client. The file is covered by
`backend/.gitignore` (`.env*`) and `.vercelignore`, so the credential is never committed
and never uploaded in the deployment source.

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
| `FACTORY_DATABASE_TEMPLATE_URL` (or the legacy `NEON_TEMPLATE_DATABASE_URL`) | the factory creates one database per product, migrates it, and the API must reach it — any Postgres provider whose role can `CREATE DATABASE` over TLS | `ai-agent/.env` (git-ignored) |
| A PostgreSQL URL | auth, records, contact, RAG | issued per product by `agent/db_provision.py`, or your own Railway/Render/Neon |
| Vercel CLI login (present on this machine) or `VERCEL_TOKEN` | frontend **and** `backend/` deploy | already configured |
| Railway token + public domain, or Render account | self-hosted API + health verification | Railway/Render dashboard |

Without `FACTORY_DATABASE_TEMPLATE_URL` a backend run stops at `database not provisioned`
rather than deploying an API that cannot connect — and it says so in the report, naming
both spellings and what the server must allow. The same run then refuses to host an API
over a database it could not migrate: `schema-incomplete` blocks `delivered`, because an
empty schema and a live-looking process is exactly how a product ships whose buyer cannot
run `npm run db:migrate`.

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

## Reference run (2026-10-27) — one prompt, nothing else

Input was exactly one sentence and nothing was touched afterwards:

```bash
py ai-agent/main.py --deliver 'Build "ShipSignal", a SaaS that turns product changelogs
into automated release notes, weekly email digests and a public status page for software teams.'
```

| Artifact | Evidence |
|----------|----------|
| Generated | 60 full-stack files from the prompt (brand, industry, pages, API, schema, tests) |
| Build | Windows App Control blocked the freshly installed rollup binary; the pipeline restored a compatible local copy, warned in the report, and the build passed |
| Database | Neon database `shipsignal` created by the run — no `createdb`, no dashboard |
| API hosting | https://shipsignal-api.vercel.app — `protection: public` (set by the pipeline), `/api/v1/health` → `{status: healthy, db: connected}` on the first probe |
| Bundle | the API origin was baked in: `api_baked.ok` true against the aliased domain |
| Frontend | https://shipsignal-lime.vercel.app/ — 7 SPA routes 200, 2/2 assets, CSS fully processed |
| Form round-trip | a real inquiry stored through the hosted API (row `46bc7b8d…`) |
| Demo video | `.factory/demo.mp4` — 136.59 s, 1920×1080, verified |
| Report | `.factory/report.md` → `delivered`, all eight stages PASS, no credential in either file |

Total elapsed: 551 s end to end for a product that is live, reachable by a stranger, and
demonstrably writing rows.

## Reference run (2026-10-24)

| Artifact | Evidence |
|----------|----------|
| Live frontend | https://nimbus-analytics-demo.vercel.app/ — verified: 6 SPA routes 200, both bundle assets loaded |
| API hosting | Not hosted for this demo (no database credentials); under the current gate that run reports `partial`, never `delivered` |
| Demo video | `.factory/demo.mp4` — 120.02 s, 1920×1080, H.264 + AAC, 9 narrated scenes, SRT included |
| QA | 0 console errors, 0 page errors, 4 collapse samples at 375/768/1024/1440 |
| Backend | 5 `node --test` tests green |
| Report | `.factory/report.json` — recorded `status: delivered` **before the full-stack gate existed**; the same run today is `partial`, because nothing hosted the API |


That run used the offline Windows SAPI voice because Edge TTS returned HTTP 403 on
this network; the fallback is part of the pipeline, not a workaround.

## Failure policy

- A failed build or backend test stops the run before anything is published.
- Browser QA is a hard gate by default (`allow_qa_fail` exists for deliberate exceptions and
  is recorded in the report as a failure).
- An unverified deployment or video keeps the run `partial`; it is never `delivered`.
- A project with `backend/` is `partial` unless its database was provisioned, its hosted
  health reports the database reachable, and the contact probe wrote a real row.
- A health payload without a `db` field is treated as no evidence at all
  (`db-not-proven`): the old static `{status: healthy}` response is exactly what a
  deployment with an offline database returns.
- Toolchain gaps return `unavailable` with the missing list instead of a half-made artifact.
- The stage lines in `report.md` are a projection of the stage evidence, never a second
  opinion: a stage that passed renders PASS. A `delivered` run whose markdown still
  contains a `FAIL/UNVERIFIED` line is a reporting bug and is pinned as one
  (`test_a_delivered_report_never_labels_a_stage_as_failed`) — a client cannot be handed a
  report that contradicts its own headline.
