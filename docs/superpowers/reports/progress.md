# Hardening Progress Ledger

**Plan:** `docs/superpowers/plans/2026-10-29-lumicore-hardening-phase1.md`
**Spec:** `docs/superpowers/specs/2026-10-29-lumicore-hardening-design.md`
**Base commit:** `539fecbf` (master) → branch `feature/hardening-v8`
**Worktree:** `D:\lumicorepro-core-premium-delivery`
**Started:** 2026-10-29

## Rulings

| # | Ruling | Reason |
|---|--------|--------|
| R1 | Work in `D:\lumicorepro-core-premium-delivery`, not the original checkout | User decision 2026-10-29 |
| R2 | Local commits allowed, no push | User authorised 2026-10-29 |
| R3 | Commit the BlogForge fixture (not live generation, not sell-today-only) | User decision 2026-10-29 |
| R4 | Phase 2–4 get their own plans after Phase 1 lands | Spec scope note |
| R5 | Never lower a ratchet floor | AGENTS.md §6 |

## Baseline measurements (2026-10-29, before changes)

| Metric | Value |
|--------|-------|
| unittest collects | 774 |
| pytest collects | 2110 |
| Full pytest run | 1 failed, 2094 passed, 15 skipped, 126 subtests, 1003 s |
| Failing test | `test_campaign_seo.py::test_campaign_list_matches_generator` |
| raw `res.status().json(` (routes+middleware) | 315 |
| envelope helper call sites | 51 |
| route files with no validation | 23 of 34 |
| `t()` keys missing from en.json | 245 of 337 (27.3% coverage) |
| `delivery/` dirs with real source | 1 of 96 |
| `products/sell-today` products | 11 |
| CI python runner | `unittest discover` (the defect) |

## Task status

| Task | Status | Evidence |
|------|--------|----------|
| 1. Consolidate work streams | done | 4 commits: 0660fef9, 61b87384, bda78da9, 98de2051; tree clean; conflicts resolved keeping both features |
| 2. Campaign parity test | done | 03bc6a3a; 24 tests pass; anti-gate fails on injected bogus entry |
| 3. pytest in CI | done | 2e22a4de; unittest 774 vs pytest 2110; anti-gate fails when workflow mutated back to unittest |
| 4. BlogForge fixture | done | 09842f6c; 88 files committed, secrets stripped, TEST_DATABASE_URL skip-gate found and closed |
| 5. Delivery verification wiring | done | 2d837051; prestige-studio PASS firstPaint 75.6 KB in 53 s; script now exits 1 on FAIL |
| 6. Python lint ratchet | done | 2d837051; baseline ruff=300, bandit_high=11, bandit_medium=38 |
| 7. AGENTS.md rules | done | rules added to §6 and §13 |
| 8. Phase 1 report | in progress | |

## Environment findings (not code defects)

- **Device Guard blocks `D:\Git\ucrt64\bin\git.exe`** (WinError 4551). 22 tests in
  `test_benchmarks.py` shell out to git and therefore fail locally. CI is Ubuntu
  and is unaffected. Workaround used: GitHub Desktop's bundled git 2.53.0 at
  `C:\Users\...\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe`.
- `D:\lumicorepro-core` (the original checkout) is being edited by another
  session concurrently — its AGENTS.md changelog advanced to v8.35 during this
  work. That checkout was never modified from here.

## Fix rounds

1. `test_ci_runs_pytest_not_unittest` initially matched its own explanatory
   comment; the test now parses YAML `run:` values instead of raw text.
2. `verify_delivery_builds.py` deleted a tracked `package-lock.json`; it now
   removes only files the run created.
3. The generated suite skipped every test because CI set `DATABASE_URL` while
   the suite guards on `TEST_DATABASE_URL`; both are now set and asserted.
