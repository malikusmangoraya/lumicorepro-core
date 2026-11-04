# Prompt-Controlled App System — Design Spec

**Status:** Design approved; surface routing clarified 2026-10-28; awaiting spec review
**Scope owner:** LumicorePro factory
**Related spec:** `2026-10-28-premium-delivery-gates-design.md`
**Plan:** to be written after this spec is reviewed

## 1. Goal

Extend the existing website factory with a **prompt-controlled app system**. The
request decides the surfaces:

- “website” / “web” → only the existing web lane.
- “app” / “mobile app” → only a React Native (Expo) mobile app plus backend.
- “web and app” / “both” → the requested web surface **and** the mobile app.
- “PWA” / “installable” → add PWA to the requested web surface.

All selected surfaces share one Express/PostgreSQL backend, one auth system, one
records domain and one real-time change feed. A surface the user did not ask for
is never generated.

Mobile delivery is only certified after a real debug APK is built, installed and
launched on a local Android emulator and its core journey is exercised. A missing
toolchain blocks mobile delivery; it never degrades into a source-only claim.

## 2. Non-goals

- Play Store / App Store submission, release signing keys or paid EAS builds.
- iOS simulator/device proof on this Windows machine. iOS project files may be
  generated, but iOS verification is reported `not_measured`.
- Multi-tenant organisation administration, billing, or invented role management.
  The app uses only capabilities the generated backend already proves.
- Native modules beyond Expo-managed packages.
- Automatic toolchain installation during a delivery run.
- Redesigning the existing website lane. Default website output must stay
  behaviourally identical.

## 3. Delivery contract

`resolve_generation_contract(spec)` keeps version 1 and adds an **optional** `app`
block. Absence of `app` means the existing website lane, so current equality tests
and callers remain valid.

```json
{
  "version": 1,
  "layout_mode": "enterprise",
  "database": "postgresql",
  "auth": true,
  "features": ["jwt_auth", "users", "contact"],
  "requirements": [],
  "app": {
    "web": "web_app",
    "pwa": false,
    "mobile": {
      "platforms": ["android"],
      "verification": "apk_emulator"
    }
  }
}
```

Rules:

- The request says exactly which surfaces to build. **Do not add a surface the
  user did not ask for.**
- `web`: `"website"` (existing marketing/records product), `"web_app"`
  (authenticated dashboard shell), or `"none"` (no web frontend).
- `mobile`: absent when no mobile app is requested; otherwise
  `{platforms, verification}`.
- `pwa`: `true` only when the user asks for PWA/installable/offline or passes the
  explicit flag. It is independent of the web surface and requires a web surface.
- The `app` block is absent for a plain website request, so current callers,
  equality tests and website output remain unchanged.
- An `app` block with `web: "none"` and mobile enabled is an **app-only** build:
  backend + `mobile/`, no `frontend/`, no browser QA and no frontend deployment.
- An `app` block with a web surface and mobile enabled is a **web + app** build:
  the requested web surface plus `mobile/`, sharing the same backend.
- `mobile.platforms` currently accepts `["android"]`; `"ios"` may be listed for
  project generation, but verification stays `not_measured`.
- `mobile.verification` is `"apk_emulator"` or `"none"`. A mobile request with
  `"none"` generates source and exportable bundles only: APK/emulator stages are
  skipped, the report says `mobile: not_verified`, and the overall result can be at
  most `partial` — never `delivered`.
- Explicit `app` input always wins. Without it, prompt intent resolves surfaces:

| Prompt says | `web` | `mobile` | Result |
|---|---|---|---|
| website, landing page, storefront, web only | `website` | absent | web only (existing lane) |
| web app, internal app, admin dashboard, management system | `web_app` | absent | authenticated web app only |
| app, mobile app, android app, ios app, react native | `none` | android | mobile app only |
| web and app, website and app, web + mobile, both | `website` | android | website + mobile |
| web app and app, dashboard and mobile app | `web_app` | android | web app + mobile |
| add PWA / installable / offline app (with a web surface) | as stated | as stated | PWA enabled for that web surface |

- Conflicting/ambiguous combinations (mobile intent with no web words in a
  “both” phrase) resolve to **web + app**, never silently drop a surface.
- CLI: `--deliver-web website|web-app|none`, `--deliver-mobile android|none`,
  `--deliver-pwa`, `--deliver-mobile-verify apk-emulator|none`.
- HTTP: the factory delivery payload may carry `app` but never a local model or
  filesystem path. No credentials travel in this block.

## 4. Shared backend

No second API is introduced. The generated Express backend keeps:

- `/api/v1/auth/login`, `/api/v1/auth/register`
- `/api/v1/records` CRUD, tenant-scoped
- `/api/v1/events` SSE feed
- `/api/v1/health`
- `/api/v1/contact`

### 4.1 Idempotent record creation (required for offline queues)

`POST /api/v1/records` accepts an optional `id` field:

- Must be a canonical UUID v4 when present; otherwise 422.
- The insert is scoped to the authenticated user. If a row with that id already
  exists for this user, the route returns the existing row with 200 instead of
  creating a duplicate.
- If the id belongs to another user, the route returns 409 without revealing the
  row.
- Without `id`, behaviour is unchanged (server-generated UUID, 201).
- Web and mobile offline queues generate the UUID client-side, so a retry after an
  ambiguous network failure cannot duplicate a record.

This needs no schema change (`records.id` is already a UUID primary key) but does
need route tests for create, retry, wrong tenant and invalid id.

## 5. Web surfaces

The web surface is exactly what the request names:

- `web: "website"` → existing `premium_layouts` website, unchanged. It already has
  auth, records and realtime, so a website + mobile build shares that backend.
- `web: "web_app"` → new authenticated app shell from
  `agent/app_layouts.py` (kept separate from `premium_layouts.py`).
- `web: "none"` → no `frontend/` at all; app-only builds use `mobile/` + `backend/`.

`render_app_files(brand, industry, design) -> dict[relative_path, source]`

Routes and independent headings for the `web_app` surface:

| Route | Heading | Behaviour |
|---|---|---|
| `/login` | Sign in | token form, error/loading states |
| `/register` | Create your account | validation, duplicate-email error |
| `/dashboard` | Your workspace | record totals by status, recent records |
| `/records` | All records | search, status filter, create/edit/delete |
| `/settings` | Account settings | email/name read-only, sign out |

- `/` redirects to `/dashboard` when a token exists, otherwise `/login`.
- Auth guard wraps app routes; no marketing navbar/footer on auth screens.
- All data comes from the real API; no invented metrics or roles.
- The existing `qa-contract.json` carries these headings and is the independent
  browser-QA expectation.
- Browser QA for authenticated app routes seeds a test token and fulfils bounded
  API fixtures declared in the QA contract. This proves rendering, states and PWA
  behavior; it does **not** prove the real backend. The factory handshake and the
  mobile `full_stack` journey remain the backend proofs.
- A marketing website is not generated in `web_app`, and the app shell is not
  generated in `website`.

## 6. PWA

PWA is built only when the request says PWA/installable/offline or `--deliver-pwa`
is passed, and only when a web surface exists. `pwa: true` with `web: "none"` is a
sanitized `ValueError`. For a `website` surface, PWA adds the offline shell; for a
`web_app` surface it also owns the offline write queue.

- `frontend/public/manifest.webmanifest` with name, short name, theme/background
  from design tokens, `display: standalone`, icons 192/512 (locally generated PNGs
  from the brand mark, no remote fetches).
- `frontend/public/sw.js`:
  - precaches the app shell and hashed static assets;
  - navigation requests: network-first with cached shell fallback;
  - API requests: network-only (no private data in Cache Storage);
  - versioned cache name; old caches deleted on activate.
- `frontend/public/offline.html` as the last-resort shell.
- Registration in production only; update prompt on new service worker.
- Offline write queue in IndexedDB for record create/update, max 50 operations,
  flushed on `online`; uses the idempotent record id from §4.1.
- Visible offline banner and queued-count; no fake "saved" state while offline.

Verification (`pwa` stage, real Chromium):

1. Load `/dashboard`, wait for `navigator.serviceWorker.ready` and a reload so the
   worker controls the page.
2. `context.set_offline(True)`, reload: the offline shell/app frame must render a
   visible heading and no uncaught errors.
3. Restore online, reload: app content returns.
4. With a mocked API, go offline, submit a record, assert it is queued and the UI
   says so; go online, assert exactly one POST with the client UUID and the queue
   clears.
5. Missing worker control, a blank offline page, duplicate POSTs or private API
   data in cache fail the stage.

## 7. Mobile app (Expo + TypeScript)

Built only when `app.mobile` is present (prompt says app/mobile, or the explicit
flag is passed). An app-only request generates `backend/` + `mobile/` and no
`frontend/`.

New module `agent/mobile_app_engine.py`:

`generate_mobile_app(project_dir, brand, industry, design, contract, *, api_base="") -> {success, files, errors, app}`

Output under `mobile/`:

```
mobile/
  app.json
  package.json
  tsconfig.json
  babel.config.js            # only if required by the pinned Expo SDK
  app/_layout.tsx
  app/(auth)/sign-in.tsx
  app/(auth)/register.tsx
  app/(tabs)/_layout.tsx
  app/(tabs)/index.tsx       # summary
  app/(tabs)/records.tsx
  app/(tabs)/settings.tsx
  app/record/[id].tsx
  app/record/new.tsx
  src/api/client.ts
  src/api/auth.ts
  src/api/records.ts
  src/auth/AuthContext.tsx
  src/realtime/useRecordFeed.ts
  src/offline/queue.ts
  src/theme.ts
  assets/icon.png
  assets/adaptive-icon.png
  assets/splash.png
  .maestro/smoke.yaml
  .maestro/records.yaml
  README.md
```

### 7.1 Runtime behaviour

- Expo Router with TypeScript; the SDK major is pinned to the installed Expo CLI
  at implementation time and exact versions are written into `package.json`.
- Auth token stored with `expo-secure-store`; never logged, never placed in URLs
  other than the SSE query token the backend already requires.
- API base from `EXPO_PUBLIC_API_URL`; a debug build defaults to
  `http://10.0.2.2:5000/api/v1` (emulator host loopback). A release build requires
  an `https://` origin; generation fails otherwise.
- Records list/detail/create/edit/delete with loading, empty, error and retry
  states.
- Realtime via `react-native-sse` on `/events`; on failure/background it falls back
  to bounded polling (15 s) and resumes SSE on foreground.
- Offline queue in `AsyncStorage`: create/update operations carry a client UUID,
  flush sequentially on reconnect, cap 50, surface queued count, never mark
  success before the server confirms.
- Theme tokens generated from `design_forge` as plain TypeScript objects.
- App icon, adaptive icon and splash generated locally with Pillow from the brand
  colors and vector mark; sizes 1024×1024, 1024×1024, 1284×2778. No remote assets.
- Android package id derived from the brand slug (`com.lumicore.<slug>`), validated.

### 7.2 Mobile build verification

Stages (all fail closed when mobile is requested):

1. **`mobile_export`** — `npx expo export --platform android --platform ios --platform web`
   and `npx tsc --noEmit` in `mobile/`. Missing bundles or type errors fail.
2. **`mobile_apk`** — `npx expo prebuild --platform android --no-install` then
   `gradlew assembleDebug` with pinned JDK 17 and `ANDROID_HOME`. Output
   `mobile/android/app/build/outputs/apk/debug/app-debug.apk`; verify it exists,
   hash it with SHA-256, and read package/minSdk with `aapt dump badging`.
3. **`mobile_emulator`** — boot the configured AVD headless, wait for
   `sys.boot_completed=1` (bounded 240 s), `adb install -r`, launch the package,
   scan logcat for `FATAL EXCEPTION`/`ANR in`, run Maestro flows, capture
   screenshots, and check API health from the emulator.

### 7.3 Verification tiers

- **`app_runs`** — APK installs, launches, auth screen renders, navigation works
  against a labeled in-memory fixture API. Proves the app binary, not the real
  stack. Delivery result may be `partial`, never `delivered`.
- **`full_stack`** — the same journey (register → create record → see it in the
  list) runs against the factory-hosted API and PostgreSQL. Required for
  `delivered` when mobile is requested.

The report always names the tier used. A fixture-API run cannot be presented as
full-stack proof.

### 7.4 Maestro flows

- `smoke.yaml`: launch, assert Sign in, open Register, assert Create your account.
- `records.yaml`: register with a unique email, create a record, assert it appears,
  open detail, edit the title, assert the updated title, screenshot at each step.
- Credentials come from per-run environment variables, never committed.
- The test account remains in the database; the handoff notes it, like the existing
  contact probe row.

### 7.5 iOS

`expo export --platform ios` must produce a bundle. iOS simulator/device proof is
reported `not_measured` on Windows. No claim of iOS delivery.

## 8. Android toolchain bootstrap

New module `agent/android_toolchain.py`:

```python
check_environment() -> {
  "ready": bool, "java17": bool, "sdk": bool, "adb": bool,
  "emulator": bool, "avd": bool, "maestro": bool,
  "disk_free_gb": float, "missing": [...]
}
install_toolchain(root: str, *, accept_licenses: bool = False, progress=None) -> dict
```

- CLI: `python ai-agent/main.py --android-toolchain check|install --accept-licenses`.
- Default root `D:\android-sdk`; JDK `D:\tools\jdk17`; AVD home `D:\android-avd`;
  Maestro `D:\tools\maestro`; Gradle cache `D:\gradle-cache`.
- Required packages: `platform-tools`, `build-tools;35.0.0`,
  `platforms;android-35`, `emulator`,
  `system-images;android-35;google_apis;x86_64`.
- AVD `lumicore_api35`, Pixel-class device, 2 GB RAM.
- Downloads only from official HTTPS hosts (Adoptium, Google, GitHub releases),
  verified by the repository checksum or ZIP integrity before extraction.
- Requires `--accept-licenses`; without it, installation prints what would happen
  and exits non-zero if anything is missing.
- Aborts before download when free disk space on the target drive is below 14 GB.
- Does not modify global `JAVA_HOME`/`PATH`; it returns env values and writes
  `ai-agent/.env.android` (no secrets) for factory use.
- Delivery never installs anything; a missing toolchain is `blocked` with the exact
  missing list and the install command.

## 9. Factory integration

`deliver_from_prompt(..., app=None)` resolves the contract before generation and
returns early on an invalid app request. Generation adds a `mobile_generate` stage
when mobile is requested; any failure stops later stages.

`run_factory` runs only the stages required by the selected surfaces:

```
web present:   build → backend_tests → qa → [pwa] → database/api/handshake
               → deploy → live_qa
mobile present: [mobile_export] → [mobile_apk] → [mobile_emulator]
               (after a hosted API exists for full_stack; app-only builds run
                backend_tests → database/api → mobile stages, with no web build,
                browser QA or frontend deployment)
report → video → final status
```

- `web: "none"` skips build/qa/deploy/live_qa entirely; the run cannot claim a
  frontend or hosted website.
- Mobile stages run after a hosted API exists so `full_stack` can use it. When no
  hosted API is available, only the labeled `app_runs` tier may run.
- `mobile_emulator` failure blocks `delivered` when mobile verification is
  requested; a missing toolchain produces `blocked` and `partial`.
- PWA failure blocks `delivered` when `pwa` is requested.
- When `web: "none"`, `delivered` requires a verified API+DB and a `full_stack`
  mobile journey; otherwise the result is `partial`.
- Evidence under `.factory/mobile/`: `apk.json` (hash, package, minSdk),
  `emulator.json` (boot, launch, logcat scan), `maestro/` (flows, screenshots,
  result), `health.json`, and the verification tier.
- The handoff lists APK path/hash, verification tier, Maestro journey and test
  account note. A fixture-API tier is explicitly labeled and never written as a
  full-stack delivery.

## 10. Security and privacy

- No secrets in mobile bundles or reports. API origins are public config; tokens
  live only in SecureStore/IndexedDB and are never printed.
- Debug builds may use `http://10.0.2.2`; release configuration rejects cleartext
  non-local origins.
- Fixture API is bound to loopback and is test-only; it never touches real data.
- Test credentials are per-run, random, and recorded only as an email in the
  report, never a password.
- Logcat capture is filtered and capped; no token or payload dumps.
- APK SHA-256 is recorded for traceability.

## 11. Failure rules (fail closed)

| Condition | Result |
|---|---|
| Missing JDK 17 / SDK / emulator / Maestro | `blocked`, `partial`, exact missing list |
| `expo export` or TypeScript fails | `failed`, no APK claim |
| Gradle build fails / no APK / bad package metadata | `failed` |
| Emulator boot timeout or app crash/ANR | `failed` |
| API unreachable from emulator | `partial` (`app_runs` only) |
| Maestro journey fails | `failed` |
| PWA offline test fails | `failed` when `pwa` was requested |
| iOS proof requested on Windows | `not_measured`, explicitly reported |

## 12. Testing

- Unit: contract normalization, prompt intent, app file contracts, idempotent
  record id validation, queue retry/no-duplicate, PWA worker source contracts,
  toolchain `check` (no download), failure injection for every new stage.
- Real browser: web-app routes at 5 widths, auth/records journeys against a mocked
  API, PWA offline/reconnect/queue flush.
- Real mobile: `expo export` + `tsc`, Gradle debug APK, emulator boot/install,
  Maestro flows, logcat scan, API health.
- The mobile/emulator suite is opt-in by environment; when requested and the
  toolchain is absent it fails, never skips silently.
- Existing website suites must stay green; default contract equality unchanged.

## 13. Acceptance criteria

1. **Prompt routing:** a website prompt creates only the website; an app prompt
   creates only `backend/` + `mobile/`; a “web and app” prompt creates the stated
   web surface + `mobile/`. No surface is added without a request.
2. Default website generation is unchanged and existing suites pass.
3. A web-app project builds and passes a 5-route × 5-width browser matrix. When
   PWA is requested, the offline/queue proof also passes.
4. A web + app project generates `frontend/`, `backend/`, `mobile/` and one
   `qa-contract.json`; mobile export and TypeScript check pass.
5. The debug APK builds, installs and launches on `lumicore_api35`; logcat has no
   fatal/ANR.
6. With a hosted API+DB, the Maestro register→create→list journey passes and the
   delivery is `delivered` with tier `full_stack`.
7. Without credentials/toolchain, the run stops at the named stage with `blocked`
   or `partial`; no fake APK, live URL or full-stack claim.
8. iOS is reported `not_measured`, never passed.
9. AGENTS.md, CHANGELOG.md and docs/FACTORY.md document the surface routing and
   gates.

## 14. Implementation phases

The implementation plan will keep these as reviewable phases; each phase must leave
the website lane green:

1. **Contract + web surfaces + PWA** — `app` block, surface routing, prompt/CLI
   plumbing, app shell, idempotent record id, PWA worker/queue, browser proofs.
2. **Mobile generator** — Expo project, auth/records/realtime/offline, icons,
   contract tests and `expo export`/TypeScript verification.
3. **Toolchain + APK/emulator** — `android_toolchain` check/install, Gradle build,
   emulator boot, Maestro flows, failure gates and evidence.
4. **Factory acceptance + docs** — web-only, app-only and web+app representatives
   end to end, PWA representative, fail-closed negative fixtures,
   AGENTS/CHANGELOG/FACTORY updates, independent review.

## 15. Risks and limitations

- Android SDK/AVD/Gradle consume ~10–14 GB; this machine has ~19 GB free. The
  installer aborts below 14 GB.
- First Gradle build downloads dependencies and can take 20–40 minutes.
- Hyper-V is present, but emulator acceleration can still fail; failure is
  reported, not bypassed.
- Windows cannot verify iOS.
- The fixture-API tier is weaker evidence; it is labeled and cannot earn
  `delivered`.
- Store signing/submission remains a separate, credential-dependent phase.
