# Sell Today Catalog Rebuild — Design Specification

## Status

Superseded. This earlier catalog-only design has been replaced by [Generated Websites: Production Readiness](2026-10-10-generated-websites-production-readiness-design.md), then superseded as the immediate milestone by [Sell Today Catalog Rebuild and Preview Deployment](2026-10-10-sell-today-preview-rebuild-design.md). The current approved direction is to rebuild the Sell Today catalog and deploy verified previews to separate staging sites; implementation requires approval of the current written spec.

## User intent and success

Rebuild all 11 existing Sell Today products so the owner can sell them as independent, professional products. Each product must retain a distinct industry and brand identity, be straightforward for a buyer to load, and include its required code, data/configuration, and media locally. External media should be downloaded and bundled with source/license notes; retain suitable current assets and replace only assets that are broken or unsuitable. The delivery is a set of locally prepared sale-ready packages; it does not include publishing or listing products on marketplaces.

Success means a buyer can unpack a product, follow its concise setup guide, configure secrets safely, start the full frontend/API/database/cache stack with one documented command, and verify the app using product-specific smoke checks. Builds and delivered archives must be checked rather than assumed correct.

## Agreed decisions

- **Scope:** all 11 products under `products/sell-today/`.
- **Relationship to earlier spec:** this catalog rebuild supersedes the earlier “new projects only” design-engine spec for this milestone. Its industry/brand-aware layout intent remains a quality constraint, not a separate implementation deliverable.
- **Execution strategy:** phased catalog rebuild, with per-product brand-specific work; common tooling is shared only when an audit confirms the same defect or repetition.
- **Assets:** bundle external runtime media locally, record source and license/provenance where available, retain suitable assets, replace only broken/unsuitable assets.
- **Buyer setup:** one-command local full-stack setup using the existing project stack; do not add paid services or change production data/deployments.
- **Delivery:** local sale-ready packages only. No publishing, marketplace listings, pushing, or deployment is authorized.

## Catalog and current constraints

The current catalog contains: apex, aurelia-estates, aurum-fitness, claimflow-ai, flowpilot, meridian-capital, nuage-events, prestige-studio, resupro, saffron-voyage, and studio-lumen. Projects have separate frontend/backend/database and deployment material, existing buyer and marketing documentation, and varied package scripts and assets. The repository also contains extensive automation and generated product artifacts; inspect each script before running it, because some may rewrite many product directories. Existing working-tree changes are present outside and inside catalog-adjacent paths; preserve all pre-existing work and make only tracked, intentional changes for this task.

Treat current audit scores and old verification claims as historical until rerun. Check package manifests, environment examples, compose services, frontend build and backend boot for every product. Do not assume all 11 have equivalent scripts or all external images are valid/licensable.

## Scope

### In scope

1. Inventory each product’s UI, features, scripts, environment variables, database/cache requirements, existing tests, media references, licenses and buyer documentation.
2. Establish a catalog-level definition of package completeness and a per-product rebuild/verification record.
3. Improve each product’s own UI/UX where audit evidence shows that rebuilding is necessary; preserve its name, target audience, industry journey, and distinct visual identity. Do not mass-copy one landing template across the catalog.
4. Make product-specific code, sample/demo content, and required assets available locally. Download externally referenced runtime media to product-owned asset locations, update references to local paths, and document source/license/provenance and any unresolved rights questions. Use an allowed, attributable replacement only when the existing media is unavailable, broken, or demonstrably unsuitable.
5. Standardize buyer onboarding sufficiently to provide prerequisites, copy-paste setup, environment-variable table, one-command full-stack start, verification, troubleshooting, deployment notes, and license/asset notices per package.
6. Validate each product through its actual user-facing frontend and full-stack boot path where local dependencies/services are available. Build a deterministic local sale archive and verify archive contents and exclusion rules.
7. Update catalog-level index/reporting only with verified, current results.

### Out of scope

- Marketplace account creation, listing publication, repository push, public deployment, or production data changes.
- Rebuilding unrelated products outside `products/sell-today/`.
- Replacing all product-specific branding, layouts, or content with a common template.
- Adding paid APIs, services, or unnecessary dependencies.
- Downloading assets without a source/provenance record or representing unknown licensing as cleared.
- Guaranteeing legal clearance, WCAG conformance, performance scores, or production readiness without the corresponding review/check.
- Destructive cleanup of existing project content or unrelated working-tree changes.

## Proposed design

### Phase 1 — Catalog audit and baseline

Create a per-product inventory of entry points, install/build/start/test commands, env vars, backend/database/cache dependencies, current package docs, visual flows, external media references, and package artifacts. Run existing safe/read-only audits and inspect any mutating automation before use. Record baseline build/boot/asset failures, distinguishing not-run from failed. Choose small batches based on shared failure classes, not arbitrary product similarity.

### Phase 2 — Rebuild products in verified batches

For each product, first resolve concrete buyer blockers and broken UX/build/runtime paths found in the audit. Maintain that product’s brand system and its industry-specific information architecture. Write or update tests/smoke checks around defects before fixes where practical. Use focused shared fixes only when the same root cause is demonstrably present in multiple products; test shared tooling independently and re-run all affected product checks. Avoid polishing unrelated features while critical launch blockers remain.

### Phase 3 — Local media and provenance

Enumerate runtime media references in frontend code, CSS, HTML, sample/demo data and required backend seed paths. Download image/video/font/media assets only from their currently referenced sources when retrieval and usage terms permit. Verify the downloaded file type, dimensions/size where applicable, successful decode, and correspondence to the intended UI slot. Store them within the owning product; use descriptive stable names and optimized suitable formats. Replace remote references with local paths and preserve lazy loading/appropriate alternatives. Record exact source URL, retrieval date, creator/provider, known license/terms and attribution requirement in an asset manifest or buyer-facing credits. Unknown rights remain an explicit unresolved item; do not claim safe resale. Keep truly optional third-party service links separate from core UI assets and document them.

### Phase 4 — Buyer setup and verification

Standardize each package’s buyer guide without erasing product-specific requirements. The quick start must cover supported runtime versions, dependency installation, `.env.example` copying, required secrets (never include real secrets), database initialization/migrations/seeds, the one-command full-stack start, expected local URLs, health/smoke verification, troubleshooting and production deployment caveats. Prefer existing Docker Compose setup when it genuinely starts the complete stack; otherwise repair the product’s setup path rather than documenting a command that does not work. Build and boot each project from its own directory using the documented buyer commands. Verify representative core user journeys in browser automation or the project’s existing test mechanism. Run responsive checks at 375/768/1024/1440px for materially changed UI; report unmeasured checks honestly.

### Phase 5 — Sale archives and catalog evidence

Build one deterministic archive per product using existing packaging conventions only after inspecting the packager and confirming its exclusion list. Include source, license, buyer docs, required local assets and required schemas/migrations. Exclude credentials, `.env` secrets, `node_modules`, build caches, temporary files, developer-specific paths, and unrelated repository changes. Open each archive and run a content safety/completeness check; where feasible, perform a clean extraction and follow the buyer quick start. Refresh the catalog index/audit report from actual current verification, including per-product blockers and known asset-license caveats. Do not mark a product sale-ready if a required setup, test, or rights check is blocked.

## Quality and safety requirements

- Every product preserves a coherent, distinguishable brand/industry identity; no universal visual template.
- All runtime-required imagery/media is local and verified; remote dependencies remaining are disclosed.
- Asset provenance and known license/attribution terms ship with each package; uncertain rights are flagged, never silently cleared.
- Buyer setup is reproducible from a clean extraction and does not depend on developer-local paths or hidden credentials.
- Environment variables have examples and descriptions; actual secrets are excluded.
- Build, backend boot, smoke tests, and archive safety are reported per product with exact outcomes.
- Responsive/accessibility/performance results are reported only if actually measured. Use existing tooling and avoid claiming universal compliance from static inspection alone.
- Scope changes are isolated from unrelated ongoing backend/security work and preserve pre-existing user changes.

## Acceptance criteria

1. All 11 named products have an inventory and a current status record.
2. Each product retains its own brand, niche, and appropriate user journey; the rebuild does not clone one visual template across projects.
3. Every product has a working documented one-command full-stack local start from a clean package, or a precisely documented blocker is reported instead of claiming completion.
4. The documented commands, env names, ports/URLs, migrations and health checks match the actual package implementation.
5. Required external runtime images/media are stored locally, render successfully, and no longer require third-party image hosting for the core experience.
6. Every bundled media item has source/provenance and known license/attribution information recorded; unresolved usage rights are clearly flagged and prevent an unqualified “sale-ready” claim.
7. Broken/unsuitable media is replaced only with appropriate, attributable alternatives, and replacement source/terms are recorded.
8. Per-product frontend build and backend/full-stack boot/smoke verification are run where dependencies permit; failures and blocked checks remain visible.
9. Material UI changes are verified through the buyer-facing interface and responsive widths; measured accessibility/performance findings are reported with evidence, not assumptions.
10. Each delivered archive contains required code/docs/assets/schema and excludes secrets, dependency folders, caches and unrelated files; archives are opened and checked.
11. Catalog-level docs/report use only current measured results and distinguish verified, failed, blocked and not measured states.
12. No marketplace publishing, deployment, push, or destructive cleanup occurs.

## Risks and explicit limits

- The existing tree may contain repeated, stale, or fabricated “verified” claims; verify current artifacts rather than copying the claims.
- Existing media URLs may be unavailable or have terms that do not permit resale/redistribution. Keep the asset unbundled or use a properly licensed substitute and flag any unresolved rights issue.
- A full-stack one-command setup may depend on Docker availability, runtime/database versions, or missing secrets. Test cleanly and state prerequisites; do not hide external service requirements.
- Eleven large products are too broad for an unverified single-pass rewrite. Batch work, keep a verification ledger, and stop/adjust if shared fixes cause regressions.
- User changes already in the working tree must be preserved; never blanket format, reset, or package unrelated content.

## Handoff

After this written spec is reviewed and approved, create a detailed implementation plan with file-by-file tasks, per-product checks, asset acquisition strategy, packager safety checks and execution method. No product code, asset downloading, install/build, or packaging changes are included in this design deliverable.