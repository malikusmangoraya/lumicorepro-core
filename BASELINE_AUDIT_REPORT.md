# LumicorePro Core — Phase 0 Baseline Audit Report

**Generated:** 2026-10-12  
**Repository:** lumicorepro-core  
**Branch:** `master` (16 commits ahead of `origin/master` at audit start)

## Executive summary

The workspace is a heavily modified monorepo, so existing changes are preserved and treated as user-owned. The initial filesystem scan found **263 project-like units** across known roots. This is not equivalent to 263 independent deployable products: generated projects and category/template groupings overlap. The existing `PROJECT_INVENTORY.json` asserts 112 projects but does not list all scanned units; exact distinct product count remains unresolved.

## Inventory evidence

| Scan root / unit class | Count | Marker notes |
|---|---:|---|
| `delivery/` | 95 | 4 have a tests-directory marker |
| `products/sell-today/` | 11 | All have package/readme/license/env-example/tests/i18n markers |
| `generated-projects/` | 129 | 84 show both frontend and backend markers; no test-directory markers detected |
| `backend-library/` | 7 | One `.env` was found within the scan depth |
| `src/templates/` categories | 21 | Category groupings, not necessarily standalone projects |
| **Total scanned units** | **263** | Not a distinct deployable count |

See the marker inventory [projects-scan.json](.superpowers/phase0/projects-scan.json) and prior detailed inventory [PROJECT_INVENTORY.json](PROJECT_INVENTORY.json). The scan says nothing about runtime quality. Each project still needs purpose/audience/routes/features/deployment and its actual checks inspected before editing.

## Baseline checks

| Check | Result | Evidence / limitation |
|---|---|---|
| Full AI-agent pytest suite | **NOT RUN to completion** | Invocation was interrupted by the user; no suite result claimed |
| Focused AI-agent contract/provider/tenant tests | **PASS** | `cd ai-agent && py -3.14 -m pytest tests/test_generation_contract.py tests/test_provider_wiring.py tests/test_tenant_isolation.py -q` — 66 passed in 5.85s (before the follow-on change below) |
| Root frontend/backend test suites | **Previously reported only** | Prior audit notes list 54 frontend and 369 backend tests; not independently re-run here |
| Root lint | **NOT RUN** | Earlier invocation timed out; cause not diagnosed |
| Build / bundle measurement | **NOT independently verified** | Existing report claims prior measurements; 150 KB target and 200 KB enforced budget are distinct |
| E2E / responsive / accessibility / typecheck / security | **NOT RUN** | No completed evidence in this phase |
| Deployment config | **Inspected only** | `.github/workflows/`, `k8s/`, and `nginx/` exist; not executed |

Secret hygiene scanning records file paths, variable names, and heuristic confidence only in [secret-hygiene.json](.superpowers/phase0/secret-hygiene.json); no values are stored there. Its value-shape heuristic does not prove validity or compromise. It identifies potential exposures in root/agent/backend and legacy environment files, requiring owner review and rotation if genuine. No secret values were printed, copied, staged, or committed.

## Workspace preservation

At inspection, the checkout was `master` and 16 commits ahead of origin, with many tracked and untracked changes in AI generation/provider work, Apex, design system, specs/plans, and database artifacts. Those changes were preserved. Nothing was staged, committed, reverted, pushed, or deployed during this work.

## Prioritized roadmap

### P0 — safety and trustworthy inventory
1. Owner locally verifies potential exposed credentials and rotates any genuine values. Do not rewrite history without explicit approval.
2. Inspect deployment manifests and CI secret handling, especially `k8s/secret.yaml`, without displaying values.
3. Reconcile scan units into distinct standalone products, shared libraries, templates, and internal tools; enrich each row with purpose/audience, routes/features, deployment, dependencies, and evidence-based readiness.
4. Re-establish full baseline runs: tests, lint diagnosis, production build and bundle measurement, CI review.

### P1 — platform generation assurance (started)
- Finish contract propagation through planner, builder, and alternate entry path; keep defaults/aliases compatible.
- Make completeness checks validate real artifacts, JSON/config integrity, secret-safe env examples, and explicit requirement-driven features.
- Record build/test checks as `not_run` unless actually executed; test failures must block claims of completeness.
- Then address tenant/auth boundaries, provider behavior, backend reliability, CI/test gates, and developer setup in separate batches.

### P2 — product work
For each selected product, write a distinct project brief first, then assess its own stack and purpose before redesign. Do not use one visual template across products, add external services, split repositories, or deploy without explicit approval.

## Implementation progress — Batch A: artifact integrity

**User authorization:** The user requested implementation to proceed and explicitly asked for an improved/advanced pass. Work is constrained to the planned AI-agent generation assurance scope; no source tree-wide redesign.

**Acceptance criteria:** (1) malformed generated frontend `package.json` is a blocker with an explicit reason; (2) syntactically valid frontend package metadata without a non-empty build script is a blocker; (3) valid package with build script remains accepted; (4) tests demonstrate RED before implementation and GREEN after; (5) no unrelated user files are staged/committed.

**Changed in this batch:** [generated_project_completeness.py](ai-agent/agent/generated_project_completeness.py) now parses package JSON and verifies the frontend build script exists and is non-empty; failures report `invalid_json` or `required_content_missing`. [test_generated_project_completeness.py](ai-agent/tests/test_generated_project_completeness.py) adds both regression cases. These files were already modified before this batch; only the described new hunk is ours. No other source files were modified by this batch.

**Evidence:** The new malformed-package test failed before the fix, but initially with the generic `required_content_missing` reason; after implementing JSON parsing, it still failed because token checking short-circuited JSON validation. The implementation was corrected to validate JSON independent of token success. Final focused verification: `cd ai-agent && py -3.14 -m pytest tests/test_generated_project_completeness.py tests/test_generation_contract.py tests/test_project_mode_engine.py tests/test_fullstack_ultra_engine.py -q` → **35 passed in 6.62s**. Earlier intermediate run had 2 failures, which exposed and led to the correction. Root/full AI-agent suite, lint, and build remain unverified.

**Remaining risk:** This narrow validator enhancement does not finish the full Phase 1 contract propagation, validate every generated artifact semantically, execute generated builds/tests, or audit the whole product inventory. The full program remains in progress.
