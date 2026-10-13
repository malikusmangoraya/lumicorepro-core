# Sell Today Catalog Rebuild and Staging Previews Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild all eleven Sell Today products into individually branded, locally verifiable packages and, after explicit target confirmation, deploy and verify isolated GitHub Pages staging previews without changing production sites.

**Architecture:** First establish a source-of-truth inventory and per-product verification ledger; then repair products in small root-cause-based batches with localized assets and buyer documentation. Validate local builds, backend paths, browser journeys, and package contents before any staging work. Staging repositories are separate `<original-repo-name>-staging` destinations, and no repository creation/push/deployment happens until the exact owner/repo mapping and access are confirmed. Production promotion is a separate future authorization.

**Tech Stack:** React 19, Vite, Node.js/Express, PostgreSQL, Redis, Docker Compose, GitHub Actions/Pages, Python tooling, existing project tests and browser tooling.

**Spec:** `docs/superpowers/specs/2026-10-10-sell-today-preview-rebuild-design.md`

## Global Constraints

- Work only on the eleven products listed below; preserve each product's brand and industry journey.
- Do not overwrite current public Pages/live sites or trigger their existing deploy workflows.
- Preserve all pre-existing working-tree edits; do not stage/package broad directories or unrelated files.
- No staging repo creation, push, external deployment, production promotion, real payment or account creation without its explicit authorization gate.
- Every bundled runtime asset needs source, retrieval date, known license/terms and attribution status; unresolved rights stay flagged.
- Never include `.env`, secrets, dependencies, caches, developer paths or unrelated files in packages.
- Report build, backend smoke, archive, staging deployment, and live verification separately as passed/failed/blocked/not run.
- Pages serves static frontend only; identify backend/provider dependencies honestly and never fake successful payments.

## Review Focus

- Existing Pages deployment workflow or target URL could accidentally point at production; verify exact staging repository/base URL and never reuse the original workflow target.
- `-staging` repo names can collide or belong to another owner; check exact owner/repo existence and access before creation or push.
- Remote media may not be redistributable; test provenance/rights status and leave uncertain assets unresolved rather than claiming cleared.
- A static preview may appear functional while API calls fail; test offline/API-dependent journeys and show honest unavailable/demo state.
- Existing automation and pre-existing dirty/untracked changes may mutate or leak unrelated work; inspect script effects, use narrow paths and verify archive contents.

---

### Task 1: Create an evidence-based catalog baseline

**Files:**
- Create: `products/sell-today/REBUILD_STATUS.md`
- Read-only inventory of all 11 product directories, existing `LIVE_URL.txt`, `.github/workflows/deploy.yml`, frontend/backend `package.json`, `.env.example`, `docker-compose.yml`, tests and media references.

**Products:** `apex`, `aurelia-estates`, `aurum-fitness`, `claimflow-ai`, `flowpilot`, `meridian-capital`, `nuage-events`, `prestige-studio`, `resupro`, `saffron-voyage`, `studio-lumen`.

- [ ] Record, for each product, exact repo/live URL, frontend install/build/test scripts, backend install/test/start scripts, Compose services/ports, required env variable names, migrations/seeds, asset scan status, buyer docs, current workflow target, and existing dirty/untracked paths.
- [ ] Mark each original Pages workflow as production-targeting and not usable for staging.
- [ ] Run safe read-only import/JSX/media/package checks; inspect any proposed catalog script before execution and do not run mutating automation as an audit shortcut.
- [ ] Mark historical audit claims as historical until rerun; record baseline results as passed/failed/blocked/not run.
- [ ] Verify the ledger contains exactly all eleven product names and no claims without command/artifact evidence.

### Task 2: Confirm staging mapping and product-specific deployment requirements

**Files:**
- Modify: `products/sell-today/REBUILD_STATUS.md`
- Read: each product's `.github/workflows/deploy.yml`, `frontend/vite.config.js`, `frontend/scripts/postbuild-spa-fallback.mjs`, and `LIVE_URL.txt`.

- [ ] For each product derive a proposed staging mapping `<owner>/<original-repository>-staging`, Pages URL, Vite base path, fallback strategy, and workflow isolation requirements; mark owner/repo mapping unconfirmed until verified with user.
- [ ] Confirm exact owner, all eleven repo names, GitHub account/organization access, and permission to create/push before any external action.
- [ ] Record explicit approval as a prerequisite, not as permission inferred from this plan.

### Task 3: Rebuild and locally verify the first product batch

**Files:**
- Modify only evidence-identified files under `products/sell-today/apex/`, `products/sell-today/aurelia-estates/`, `products/sell-today/aurum-fitness/`, `products/sell-today/claimflow-ai/`.
- Update each product's `README.md`, `BUYER_DOCUMENTATION.md`, `DEPLOYMENT.md`, and product asset manifest only where audit shows inaccuracies or missing requirements.
- Add/update focused product tests next to existing test conventions.

- [ ] For each product, turn one evidenced critical defect into a focused failing test/smoke assertion before fixing when practical.
- [ ] Preserve original brand/industry positioning; implement only evidence-backed UX, functional, security, build, setup or asset corrections.
- [ ] Localize permitted runtime media under that product's own assets; verify file signature/type, size, dimensions/decode and render reference; record exact source URL, retrieval date, known terms/license and attribution in `ASSET_PROVENANCE.md` (or existing manifest).
- [ ] Resolve clean setup docs to actual scripts, ports, env names, migrations and health route; document client-owned credentials and static-preview backend limitations.
- [ ] Run from each frontend directory: `npm ci` and `npm run build`; run the product's declared test command if present. Record exact outcome.
- [ ] Run backend tests and API health/smoke where dependencies/services permit; otherwise mark blocked and state the missing prerequisite.
- [ ] Exercise representative user journey through the local browser/test interface, capture console/network failures, and check 375/768/1024/1440 widths for material UI changes.
- [ ] Update only the matching ledger rows with artifact/command evidence and known unresolved rights/setup issues.

### Task 4: Rebuild and locally verify the second product batch

**Files:**
- Modify only evidence-identified files under `products/sell-today/flowpilot/`, `products/sell-today/meridian-capital/`, `products/sell-today/nuage-events/`, `products/sell-today/prestige-studio/`.
- Product buyer docs, asset provenance and focused tests as required by audit.

- [ ] Repeat the test-first, brand-preserving repair process from Task 3 for each product.
- [ ] Validate localized assets and provenance independently per product; do not reuse an asset or visual shell across unrelated brands without a documented product-specific reason.
- [ ] Run `npm ci`, `npm run build`, declared frontend/backend tests, API health/smoke where available, local browser journey, console/network checks and responsive widths; record exact status per product.
- [ ] Verify buyer quick-start commands/env names/URLs against actual manifests and scripts; correct docs instead of documenting non-working commands.

### Task 5: Rebuild and locally verify the final product batch

**Files:**
- Modify only evidence-identified files under `products/sell-today/resupro/`, `products/sell-today/saffron-voyage/`, `products/sell-today/studio-lumen/`.
- Product buyer docs, asset provenance and focused tests as required by audit.

- [ ] Repeat the test-first, brand-preserving repair process from Task 3 for each product.
- [ ] Run `npm ci`, `npm run build`, declared frontend/backend tests, API health/smoke where available, local browser journey, console/network checks and responsive widths; record exact status per product.
- [ ] Verify all external runtime media and document unresolved license issues without an unqualified sale-ready claim.

### Task 6: Verify one-command setup and create safe local sale archives

**Files:**
- Modify: each affected product's root `README.md`, `.env.example` only if audit shows real mismatch, and root setup scripts/Compose only if evidence requires it.
- Inspect before any use: `scripts/package_products.py`, `scripts/verify_release.py`, and their transitive helper functions.
- Create/update: product archives and per-product package verification entries in `products/sell-today/REBUILD_STATUS.md`.

- [ ] Inspect package scripts for output paths, deletes, inclusion/exclusion rules, and mutation scope; do not invoke broad packager until these are safe for the dirty worktree.
- [ ] Test documented one-command full-stack startup from a clean copy/extraction for each product where Docker and required services are available; verify expected health URL and representative API smoke.
- [ ] Fix setup defects at their cause; secrets remain placeholders in `.env.example` and real `.env` is excluded.
- [ ] Build deterministic per-product archives using the verified package process; inspect archive member lists for required source/docs/assets/schema and forbidden secrets, dependencies, caches, dev paths and unrelated files.
- [ ] Extract each archive into a clean temporary directory and run the documented setup/build where feasible; record exact status and blockers.

### Task 7: Build isolated staging artifacts and workflows (local-only until approval)

**Files:**
- Create or modify only product-local staging workflow/config under each approved product copy/repo; do not alter original live-target workflow to point at staging.
- Modify product Vite base/fallback config only if the staging repo requires a distinct repository path; preserve production build behavior.
- Update: `products/sell-today/REBUILD_STATUS.md` with proposed and approved mappings.

- [ ] Implement isolated staging workflow configuration targeting only the confirmed `-staging` repository and least-privilege Pages permissions.
- [ ] Build each preview artifact locally with exact staging base path and verify deep-link fallback, static asset paths, API-unavailable UI, and no secret/dev-data leakage.
- [ ] Run local preview using the project's normal Vite preview command and browser test; inspect content types, routes, media and console/network behavior.
- [ ] Confirm staging config cannot dispatch against or update any original production repository/environment.

### Task 8: External staging creation and deployment — gated

**Prerequisites:** explicit user confirmation of exact owner/repo list, existing-repo collision status, account access, allowed content, and authorization to create/push/deploy. If any are missing, stop and report blocked.

- [ ] Verify every confirmed staging destination and ensure it is separate from the original repo and Pages environment.
- [ ] Create/configure only approved staging repositories/sites; do not modify production Pages settings.
- [ ] Push only the reviewed product files/build workflow to the explicitly approved staging targets; never push `.env`, secrets, unrelated files or full-worktree content.
- [ ] Wait for the Pages build/deploy workflow and record artifact commit, run URL, staging repo and resulting public URL; a successful upload alone is not a verification pass.

### Task 9: Live browser verification and final evidence report

**Files:**
- Update: `products/sell-today/REBUILD_STATUS.md`
- Update: `products/README.md` only for verified current preview links/status, not historical/assumed claims.
- Include per-product screenshots/log references where supported by the existing evidence workflow.

- [ ] Open each actual staging URL; confirm HTML and expected branding, JS/CSS/media responses and MIME types, correct base paths, direct nested route fallback and core interaction.
- [ ] Inspect browser console/network errors and test relevant responsive widths 375/768/1024/1440; fix regressions and rerun affected local/deployed checks.
- [ ] State clearly which preview features are frontend-only, which API/backend services are not deployed, and which client-owned setup remains.
- [ ] Record staging deployment and browser verification as separate facts with URL, artifact/commit, date, findings and evidence.
- [ ] Keep production status `unchanged`; do not promote without separate explicit authorization.
- [ ] Review the final ledger against all acceptance criteria and report any failed, blocked, not-run, unresolved-rights or client-setup items without claiming completion for those items.

## Final acceptance gate

- All eleven products have current inventory/status entries.
- Every product has per-product brand-preserving rebuild/verification and actual build results, or explicitly reported blockers.
- No original production Pages site/workflow was used for staging.
- Local media is verified and provenance/rights caveats documented; uncertain rights block unqualified sale-ready claims.
- Buyer setup and package contents are checked from a clean extraction where feasible; archives contain no secrets/unrelated files.
- Each staging target was separately confirmed, deployed and browser-verified; deployment and verification results remain distinct.
- Production is unchanged and there were no unauthorized repo creation, pushes, deployments, accounts or real payments.
