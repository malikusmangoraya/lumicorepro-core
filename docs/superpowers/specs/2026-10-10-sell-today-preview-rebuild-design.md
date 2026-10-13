# Sell Today Rebuild and Preview Deployment — Design Specification

## Status

Proposed for user review. This supersedes the earlier catalog-only rebuild and generated-agent-first specs as the immediate milestone. The user has selected all Sell Today products, local asset bundling with provenance, one-command full-stack buyer setup, phased rebuild, and preview/staging first using separate GitHub Pages staging repositories/sites. No implementation, repo creation, push, deployment, or production publishing is authorized until this spec is approved and the exact target repositories are confirmed.

## User intent and success

Rebuild all 11 existing Sell Today websites so they are polished, reliable products the user can present to prospective clients and later list for sale. Each website must retain its own brand and industry-specific user experience. Core functionality, required assets and local configuration examples should be built in. Client-owned account setup such as payment provider accounts/credentials, hosting accounts, and domain registration remains the client’s responsibility and must be clearly documented.

The user now wants deployed previews so they can show the websites. Because the existing GitHub Pages workflows target public live URLs and do not provide isolated staging, previews must go to separate staging repositories/sites, not overwrite current live sites. The user chose to append `-staging` to original repo names; confirm the resolved repo list, GitHub ownership/access, and target URLs before any repo creation or push. After preview verification, production promotion remains a separate explicit approval.

Success means each product builds and passes its agreed local tests, its required runtime images/media are locally bundled with provenance and rights caveats, its buyer setup is reproducible, its separate preview deploy is successful, and that preview is actually checked in a browser for content/assets/routes/runtime errors. “Deployed” and “verified” must be reported as separate facts.

## Agreed decisions

- Scope: all 11 under `products/sell-today/`: apex, aurelia-estates, aurum-fitness, claimflow-ai, flowpilot, meridian-capital, nuage-events, prestige-studio, resupro, saffron-voyage, studio-lumen.
- Strategy: phased catalog audit and rebuild in batches, with product-specific layouts and fixes; share fixes only when common root causes are confirmed.
- Assets: bundle external runtime media locally; preserve suitable existing assets; replace only unavailable, broken, or unsuitable media. Record exact source, retrieval date, known license/terms and attribution; unresolved rights block unqualified sale-ready claims.
- Buyer setup: one-command local full-stack start per product using its actual stack, with documented prerequisites and client-provided secrets.
- Hosting: GitHub Pages for public static previews, but in isolated separate staging repositories/sites with original names plus `-staging`. Current production/live sites must not be overwritten in this preview milestone.
- Client-owned setup: payment accounts/keys, hosting backend where required, domains/DNS and similar external accounts are not created or claimed configured by this work.
- Delivery: local source/package plus deployed staging preview URLs and evidence. Production promotions, marketplace listings and further feature additions require separate approval.

## Existing environment and constraints

The catalog has 11 projects and existing deployment workflows. Audit found each existing `.github/workflows/deploy.yml` builds a frontend and publishes to the project’s GitHub Pages site, triggered by pushes to `main` or manual workflow dispatch. These are public production/live targets, not isolated preview environments. `LIVE_URL.txt` records current URLs. Therefore, triggering existing deploy workflows or pushing to their configured repositories risks updating public live pages; do not use those routes for preview.

The repository has pre-existing untracked frontend `.gitignore` files across the 11 projects and unrelated dirty/untracked work. Preserve all pre-existing changes. Do not stage, overwrite or package broad directories blindly. Inspect scripts before executing; catalog automation can mutate many products. GitHub repo/site creation and push are external, consequential operations and require exact target/access confirmation. Never publish secrets or `.env` files.

## Scope

### In scope

1. Audit all 11 products’ source, brand/industry journeys, frontend/backend scripts, env examples, database/cache setup, tests, media references, licensing notes, package docs and existing deployment config.
2. Establish a per-product baseline/verification ledger and a bounded completeness definition.
3. Repair evidenced build/runtime/UX/functional buyer blockers per product while preserving its identity; do not apply one generic layout across the catalog.
4. Download and bundle required external runtime media from existing references where terms permit, validate file content/type/dimensions/size/rendering, update references to local assets, and document provenance/license/attribution. Replace only broken or unsuitable items with documented attributable alternatives. Report unresolved media rights accurately.
5. Standardize each product’s buyer experience: prerequisites, environment-variable table, copy/paste `.env.example` flow, safe secret handling, database migration/seed, one-command full-stack start, expected URLs, test/smoke steps, deployment guide, troubleshooting, license and asset credits.
6. Build and verify local packages/archives with safe exclusions and clean-extraction checks where feasible.
7. After code/assets pass local checks, create/configure isolated GitHub Pages staging repositories/sites using confirmed `<original-repo-name>-staging` names and deploy each product’s static frontend there. Keep the API/full-stack limitations and required client setup visible on each preview and in buyer docs.
8. Verify actual preview URLs in a browser: HTTP/HTML, correct base paths, JS/CSS/media content and content types, routes/SPA fallback, console/network failures, key UI journey and responsive checks at 375/768/1024/1440 where relevant. Record URL, commit/artifact identity, timestamp, results and limitations.
9. Refresh catalog documentation with actual staging URLs and accurately separated build, deployed, live-verified, backend, payment and client-configuration status.

### Out of scope

- Updating/replacing the existing current public production/live sites during preview work.
- Production promotion, public listing publication, marketplace account changes, custom domain purchases/DNS, payment processor account creation or real charges.
- Creating/pushing staging repositories before confirming exact repo names, owner/organization, access and GitHub account context.
- Deploying full-stack APIs to an unselected host; Pages previews cover static frontend only unless a separate backend host is explicitly approved later.
- Bundling media without a defensible usage basis or stating unknown license as cleared.
- Rebuilding unrelated catalog projects or adding unrelated new product features.
- Destructive cleanup/reset or changes to unrelated worktree files.

## Proposed phased design

### Phase 1 — Audit and deployment safety

Inventory each product and confirm existing repo identity, workflow/base-path assumptions, package scripts, API dependencies and public URL. Mark all current Pages deploy workflows as production-targeting. Identify the site-specific changes required for a separate `<repo>-staging` project, including its repository name/base path, SPA routing fallback, workflow and public URL. Do not trigger existing deployment workflows. Produce the exact staging repository list and ask the user to confirm ownership/access before external creation or push.

### Phase 2 — Rebuild and local verification in batches

Fix products in small batches selected by shared root-cause evidence. For each, verify install/build, API boot and health/smoke paths where local dependencies permit, migrations/seed, core frontend journeys, console/network issues, key responsive states and package command accuracy. Preserve unique design and content. Ensure frontend preview mode can run without an unavailable API by clearly supported demo/local behavior or a clear non-fabricated unavailable state; do not disguise fake payment success as real processing.

### Phase 3 — Asset localization and buyer package

Inventory remote runtime assets in markup/CSS/code/demo data and necessary seed data. Download only permitted assets, verify each file, store in product-owned directories, update references and produce asset provenance records. Keep external service APIs distinct from visual media, documented as client configuration, and make no claims of provider authorization. Standardize buyer docs and safe archive exclusions. Open each package and test clean extraction where feasible.

### Phase 4 — Isolated staging deployment

Only after explicit approval of the exact staging repo list and sufficient account permissions, create or configure separate staging repos/sites. Build with the correct repo-specific `base` path and ensure SPA fallback. Configure GitHub Pages actions with least required workflow permissions. Never reuse the original production repository’s GitHub Pages environment. A push to an approved staging repo is allowed only after confirmation of the exact repo/destination and content scope; do not push to production repositories.

### Phase 5 — Live preview verification and report

For each staged preview, inspect the actual public origin with browser automation and validate routes, static assets, media, content types, console/network, representative interactions, and responsive layout. Confirm that no secret or dev-only data is public. Record a per-project status with explicit values for local build, API/backend check, preview deployment, live browser verification, client-owned setup, asset-rights status and known limitations. A successful CI deploy or HTTP 200 alone does not count as visual/runtime verification. If preview setup, account access, or rights evidence is blocked, report blocked—not passed.

## Readiness/report status

Keep statuses distinct and evidence-backed:

- `local_build`: passed / failed / blocked / not run.
- `local_runtime_and_smoke`: passed / failed / blocked / not run (state frontend-only vs full-stack).
- `asset_bundle_and_rights`: verified / issues / blocked / not applicable, with provenance file and unresolved rights listed.
- `package_extract_and_setup`: passed / failed / blocked / not run.
- `staging_deploy`: not requested / blocked / failed / deployed, with exact repo and URL.
- `staging_live_verification`: not run / failed / blocked / verified, with actual browser evidence.
- `production`: unchanged / pending separate authorization / promoted only after later approval and independent verification.
- `client_setup_required`: provider/domain/hosting/service, owner=client, configuration status and required variable names—never values.

No aggregate score may imply an unverified status has passed. Do not call an item sale-ready if required media rights or critical functionality remain unresolved.

## Acceptance criteria

1. An inventory and current per-product verification record exists for all 11 named projects.
2. All 11 existing deploy workflows are treated as production-targeting; preview work never triggers them or overwrites the current live Pages sites.
3. Exact staging repo names follow the chosen `-staging` suffix and are confirmed with owner/access before creation or push.
4. Each product retains its distinct brand and industry-specific UX, and no single generic layout is stamped across the catalog.
5. Each product has a locally tested build and a documented one-command full-stack setup, or a specific blocker with honest status.
6. Required runtime media is locally stored and actually renders in build/preview; provenance and known rights are documented, with unresolved rights clearly blocking an unqualified sale claim.
7. Product docs accurately state whether the public staging preview is frontend-only, what backend/provider setup is client-owned, and which environment variables are required without exposing their values.
8. Local tests/builds and key browser/user-flow checks run per product where dependencies/tools permit; failures/blocked checks remain explicit.
9. Each staging deployment succeeds to its separate destination; the exact URL and deployed artifact/commit are recorded.
10. Every deployed preview is opened and checked on its actual origin for routes, HTML/JS/CSS/media loads, content types, console/network errors, a representative user interaction and relevant responsive widths.
11. Staging and production results are reported separately. Production remains unchanged until the user explicitly authorizes a production promotion and confirms exact targets.
12. Archives include required source/docs/assets/licenses/schema and exclude secrets, `.env`, dependencies/caches, dev artifacts and unrelated files; archives are opened and safety-checked.
13. Payment accounts/keys, custom domains, DNS, production backend hosting and marketplace listing remain client/user tasks unless separately specified and authorized.
14. No external staging repo/site creation, push, production deploy, domain purchase, account creation, real payment, or destructive cleanup occurs outside the stated authorization gates.

## Risks and limitations

- Separate staging repositories may require account/organization rights and may create new public URLs; exact ownership/access must be confirmed before creation/push.
- GitHub Pages only serves static frontend assets. Projects relying on APIs need a documented demo mode or a separately authorized backend host; do not imply full-stack is online when only the frontend is deployed.
- Existing current sites may already be public/live; the requested preview work must not replace them.
- External media may have rights incompatible with redistribution; only record what is evidenced, and leave unclear items as blockers.
- Eleven full-stack products may not all build in the current environment; record real command results, and never infer pass from historical reports.
- Existing working-tree changes and untracked `.gitignore` files must be preserved and excluded from unrelated commits/packages.

## Handoff

After the user approves this written spec, produce a detailed implementation plan with exact files, per-project verification commands, local asset mapping, staging repo mapping, deployment and live-verification checks. Then the user reviews the plan and selects the execution method. Before any external staging repo creation or push, confirm the exact owner/repo mapping and authorization. Production promotion remains a later explicit decision.