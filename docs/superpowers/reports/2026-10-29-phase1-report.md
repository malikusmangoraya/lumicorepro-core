# Phase 1 Report — Gates That Reported False Success

**Date:** 2026-10-29
**Branch:** `feature/hardening-v8` (base `539fecbf`)
**Worktree:** `D:\lumicorepro-core-premium-delivery`
**Spec:** `docs/superpowers/specs/2026-10-29-lumicore-hardening-design.md`
**Plan:** `docs/superpowers/plans/2026-10-29-lumicore-hardening-phase1.md`

---

## What was measured

Every number below is the literal output of a command run on this machine on
2026-10-29, not an estimate.

| Gate | Command | Result |
|------|---------|--------|
| Collection, unittest | `python -m unittest discover -s tests -t .` | **774 tests** |
| Collection, pytest | `python -m pytest tests --collect-only -q` | **2188 tests** |
| Full suite | `python -m pytest tests -q --ignore=tests/test_cli_e2e_progress.py` | **2144 passed, 22 failed, 16 skipped, 126 subtests, 1123 s** |
| The 22 failures, re-run with a working git | `pytest tests/test_benchmarks.py -q` with GitHub Desktop git on PATH | **54 passed** |
| Python lint ratchet | `python scripts/lint_ratchet.py` | exit 0 — ruff 300, bandit_high 11, bandit_medium 38 |
| Credential guard | `node scripts/check-tracked-secrets.mjs` | `clean (2 env file(s) inspected)` |
| Delivery verification | `python scripts/verify_delivery_builds.py --root products/sell-today --layout frontend --sites prestige-studio` | **PASS, first paint 75.6 KB, 53 s** |
| Frontend lint | `npm run lint` | exit 0, no output |
| Frontend build | `npm run build` | exit 0, 13.5 s |
| Bundle budget | `npm run size` | **PASS** — largest chunk 219.4 KB gzip, CSS 26.1 KB |
| Gate regression tests | `pytest tests/test_ci_workflow.py tests/test_lint_ratchet.py tests/test_campaign_seo.py` | **36 passed** |

---

## What passed

1. **The Python suite actually runs.** CI moved from `unittest discover` (774
   tests) to `pytest` (2188 collected). The 1336 tests that never executed
   include every engine added after 2026-10-28.
2. **The runner cannot silently regress.** `test_ci_workflow.py` parses the
   workflow's `run:` commands and fails if `unittest` returns. Proven by
   mutating the workflow back: the test fails.
3. **The campaign parity test is honest.** It no longer passes in one checkout
   and fails in another depending on which directories happen to exist. Three
   dist-only campaigns are declared, and two guards stop the exception list
   from rotting. Proven by injecting a bogus entry: the test fails.
4. **The generated-project leg is runnable.** A committed 88-file BlogForge
   fixture replaces a gitignored path; the leg calls `test:backend`,
   `test:e2e`, `db:migrate` and `build` on packages that actually define them,
   with a Postgres service. `TEST_DATABASE_URL` — the flag the generated suite
   actually guards on — is set and asserted, so the leg can no longer exit 0
   with zero assertions.
5. **Delivery verification runs and can fail.** `verify_delivery_builds.py`
   now accepts `--root`, `--layout frontend` and `--json`, and exits non-zero
   on FAIL. It previously returned 0 unconditionally, so no product could ever
   fail it. Proved on `prestige-studio`: PASS, 75.6 KB first paint.
6. **Python has static analysis.** ruff 0.6.9 (E9 + F only: correctness, not
   style) and bandit run against a recorded baseline. An uninstalled tool
   reports "not measured" and fails; it never passes silently.
7. **Committed production credentials are gone from the index.**
   `backend/.env.production` and `backend/.env.staging` were tracked with
   non-placeholder `JWT_SECRET`, `JWT_REFRESH_SECRET`, `DATABASE_URL`,
   `REDIS_URL`, `SMTP_PASS`, Stripe keys and `SENTRY_DSN`. Both are untracked
   (kept on disk) and a guard now runs first in CI.

## What could not be measured on this machine, and why

- **22 tests in `test_benchmarks.py`** fail locally with
  `OSError: [WinError 4551] An Application Control policy has blocked this
  file`. Those tests shell out to `git`, and Device Guard blocks
  `D:\Git\ucrt64\bin\git.exe`. Re-run with GitHub Desktop's bundled git 2.53.0
  on PATH, **all 54 pass**. This is an environment fact, not a code defect;
  CI runs on Ubuntu.
- **The CI workflow itself has not run on GitHub.** Every gate above was
  exercised locally. The workflow file parses as YAML (`jobs: [build,
  delivery]`, `services: [postgres]`), but a green badge is only earned by a
  real run.
- **Full product fleet verification.** Only `prestige-studio` was verified end
  to end (53 s). The CI job now runs all eleven sequentially; that has not been
  executed here.

## What changed

| Commit | Summary |
|--------|---------|
| `0660fef9` | Save the 49-file premium delivery work before consolidating |
| `61b87384` | Cherry-pick Orbitboard product (41 files) |
| `bda78da9` | Cherry-pick Orbitboard CI Node 24 update |
| `98de2051` | Port backend stack catalog (38 files), conflicts resolved keeping both features |
| `03bc6a3a` | Declare dist-only campaigns; guard the exception list |
| `2e22a4de` | CI runs pytest; anti-regression test |
| `09842f6c` | Commit BlogForge fixture; correct the leg's scripts and database |
| `2d837051` | Delivery verification job + python lint ratchet |
| `80054af5` | AGENTS.md rules and ledger |
| `45c47a85` | Untrack production/staging env files; credential guard |

## What Phase 2 inherits

- **315** raw `res.status().json()` calls in `backend/routes` + `backend/middleware`
  against **51** envelope-helper call sites; **27 of 34** route files use no
  envelope at all.
- **23 of 34** route files have no request validation.
- **245 of 337** `t()` keys are missing from `en.json` (27.3% coverage);
  only 22 of 395 JSX/TSX files import `useTranslation`.
- **ruff 300 / bandit 11 high / 38 medium** — the lint backlog is recorded and
  ratcheted, not fixed.
- **26 of 95** manifest rows fail the manifest's own brand rule.

## Not proven

- No CI run has happened on GitHub. Local green is not CI green.
- ten of the eleven sell-today products were not built; only `prestige-studio`.
- The 22 benchmark failures are attributed to the Device Guard block, which was
  demonstrated by making them pass with a different git — but the blocked
  binary was not repaired, so a fresh local run on this machine will fail them
  again until the policy is lifted or `GIT_BIN` is set.
- **Credential rotation has not happened.** Untracking removes the values from
  the index, not from history. Every clone made before commit `45c47a85`
  contains them. Rotate: database password, JWT secret, JWT refresh secret,
  Redis URL credential, SMTP password, Stripe keys, Sentry DSN.
- The original checkout `D:\lumicorepro-core` is being edited by another
  session concurrently (its changelog advanced to v8.36 during this work).
  That work was not merged into `feature/hardening-v8`.
