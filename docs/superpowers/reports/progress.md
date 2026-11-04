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
| 1. Consolidate work streams | in progress | |
| 2. Campaign parity test | pending | |
| 3. pytest in CI | pending | |
| 4. BlogForge fixture | pending | |
| 5. Delivery verification wiring | pending | |
| 6. Python lint ratchet | pending | |
| 7. AGENTS.md rules | pending | |
| 8. Phase 1 report | pending | |

## Fix rounds

(none yet)
