# Remediation Log

Every entry records a change, the evidence that proves it, and the exact command that
produced the evidence. Nothing here is marked done without an artifact: a fix that has
not been verified says `pending verification`.

Started 2026-10-03 from `AUDIT_REPORT.md`.

---

## Phase 1 — Trust and hygiene

### 1.1 P0 — backend email failures crashed instead of returning an error
- **Root cause:** `backend/services/email.service.js` loaded the logger with
  `const { logger } = await import('../utils/logger.js')`, but `backend/utils/logger.js`
  only had a **default** export. `logger` was therefore `undefined`, so the catch branch
  threw `TypeError: Cannot read properties of undefined (reading 'warn')`. Every SMTP
  failure (welcome, password reset, verification, order confirmation, OTP) turned into an
  unhandled exception instead of `{ sent: false, error }`. This is what made the backend
  suite red (7 failed tests, exit 1).
- **Fix:**
  - `backend/utils/logger.js` — added the named `logger` export alongside the default so
    both `import logger from` and `const { logger } = await import(...)` work.
  - `backend/services/email.service.js` — static default import instead of a dynamic import
    inside a catch block; failure result is now `{ sent:false, error, code:'EMAIL_SEND_FAILED' }`.
  - `backend/services/email.service.js` — the pooled transporter is now cached per SMTP
    config signature instead of forever, so rotating credentials in the admin panel takes
    effect without a restart (previously the stale pool kept sending with old credentials).
  - `getTransporter()` / `closeTransporter()` are exported for tests and settings smoke-checks.
- **Regression test:** `backend/tests/unit/emailService.test.js` rewritten (18 cases):
  failure path resolves `{sent:false,error,code}` **and** logs a warning (the exact crash),
  dry-run path, pooled-transporter reuse, credential rotation rebuild + close, DB-config
  precedence, and one assertion per email template (reset URL, verify URL, OTP code, order totals).
- **Evidence:** pending verification — run `cd backend && npm test`.

### 1.2 Repository hygiene — 1.7 GB of duplicates removed from the working tree
- **Finding:** the checkout contained five orphaned git worktrees (`git worktree list`
  reported them **prunable**; their real path is `../lumicorepro-core.worktrees/<name>`),
  plus `archive/`, `delivery-new/`, `new rebuilt/`, `lumicorepro-core-integration-query/`,
  `vendors/`, `playwright-report/`, `test-results/`, `coverage/`, `logs/` and 11 scratch
  files at the repo root. `delivery/`, `archive/`, `delivery-new/` were **not** gitignored,
  so `git add -A` could have committed gigabytes. 141,387 files / 1,905 MB excluding
  `node_modules` and `.git`.
- **Fix:** `git worktree prune`; the 14 duplicate/artifact directories were **moved** (not
  deleted) to `D:\lumicorepro-core-legacy\`, and the 11 scratch files to
  `D:\lumicorepro-core-legacy\_root-scratch\`. `.gitignore` was rewritten to cover
  `.env.*` (except `*.example`), `delivery/*` (except the manifest), the duplicate trees,
  `pgdata/`, `vendors/`, `playwright-report/`, `test-results/`, `.artifacts/`.
- **Evidence:** `D:\lumicorepro-core-legacy\_phase1-report.txt` (every move logged).
  `pgdata/` was intentionally **kept** — a postgres process was running and moving a live
  data directory would have been unsafe.

### 1.3 AGENTS.md was over the instruction budget (its own last sections were truncated)
- **Finding:** AGENTS.md was 65,737 bytes — larger than the 65,536-byte workspace
  instruction budget — so the last sections were silently truncated on every session load.
  It also contained a pasted tool-output artifact (`(Showing lines 317-326 of 346. Use
  offset=327 to continue.)` and a stray `</content>`) inside its changelog table, and its
  header said `v5.1` while its own log reached `7.13`.
- **Fix:** the changelog moved to `CHANGELOG.md` (rows copied verbatim, artifact lines and
  the duplicated table header dropped); AGENTS.md §19 is now a short summary table pointing
  at it; the header is `v7.13 ... audit remediation in progress (target v8.0)`.
  AGENTS.md went from 373 to 349 lines and is now well inside the instruction budget.
- **Evidence:** `D:\lumicorepro-core-legacy\_changelog-report.txt`; AGENTS.md §19 and
  CHANGELOG.md on disk.

### 1.4 Delivery manifest is now evidence-based
- **Finding:** `scripts/final_verify_delivery.py` reported `real live: 95` from a
  `LIVE-LINK.txt` that merely *contained* `github.io` — no HTTP probe. Its `Blue` column
  meant "contains blue" while the header counted "blue-free" (inverted labels), and
  "unique logos: 69" was the number of distinct hashes, which silently hid 26 collisions.
- **Fix:** the script now performs the checks it claims: CRC pass over every zip entry,
  per-project blue scan of the built CSS, per-project sha256 logo uniqueness, unique-URL
  counting, and (with `--probe`) a real HTTP request per live link. Column names now say
  what they measure, and `delivery/DELIVERY_EVIDENCE.json` stores the raw per-project rows.
- **Evidence:** `delivery/DELIVERY_MANIFEST.md` + `delivery/DELIVERY_EVIDENCE.json`.
  Measured 2026-10-03: 95 projects | dist built 95 | blue-free 69 | logos unique **69/95**
  (26 collisions) | zips present 95 | **zips valid 95/95 (CRC)** | live links 95 with
  **95 unique URLs** and **95/95 HTTP 2xx**.

### 1.5 Status single-source-of-truth
- **Finding:** three version numbers (README `v2.0.0-ultra`, AGENTS.md `v5.1`, changelog
  `7.13`) and three different test counts (README 12 suites/45 tests, AGENTS.md 21/210,
  reality 22 files/217 tests).
- **Fix:** `scripts/generate_status.py` generates `docs/STATUS.md` — versions, declared test
  inventory, gate commands, and last-measured metrics read from artifacts on disk (a metric
  with no artifact prints `not measured`). `--check` makes it a CI freshness gate.
  README and AGENTS.md no longer carry hand-maintained numbers.
- **Evidence:** pending verification — run `python scripts/generate_status.py`.

---

## Pending verification (commands to run next)
```powershell
cd backend; npm test                              # 1.1 email fix + regression suite
python scripts/generate_status.py                 # 1.5 STATUS.md
npm run lint; npm run test; npm run build; npm run size   # frontend gates
venv\Scripts\python.exe -m pytest ai-agent/tests -q       # AI agent gates
```
