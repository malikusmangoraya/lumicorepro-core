# Sell Today Rebuild Status

Audit and rebuild activity: 2026-10-10. This ledger reports only observed evidence; older audit scores have not been revalidated.

## Scope and guardrails

Products in scope: apex, aurelia-estates, aurum-fitness, claimflow-ai, flowpilot, meridian-capital, nuage-events, prestige-studio, resupro, saffron-voyage, studio-lumen.

No archive generation, repository creation, push, deployment or production mutation occurred. The shared checkout has numerous unrelated edits; preserve them. Each product has a pre-existing untracked `frontend/.gitignore`; leave those untouched.

## Verified product work

| Product | Verified work | Remaining verification |
|---|---|---|
| apex | Automotive-specific Home, About, Services and optional conversion sections; product SEO/title metadata corrected. `npm run build` passed (Vite 8.3.1; `dist/404.html` emitted); product smoke assertions passed. Earlier Playwright local preview: HTTP 200, automotive H1 rendered, no page errors, no 375px horizontal overflow; inspected at 1440px. Backend `npm ci` passed after lockfile-only sync; backend test suite passed (2 suites / 4 tests); real server `/health` returned HTTP 200 with routes mounted. | README accuracy, asset provenance, full journeys and package checks pending. |
| claimflow-ai | Corrupted Home replaced with a product-specific workflow using existing local claim images and a decision-authority disclaimer; product SEO metadata corrected. `npm run build` passed (Vite 8.3.0; `dist/404.html` emitted); product smoke assertions passed. Earlier Playwright local preview: HTTP 200, claims H1 rendered, no page errors, no 375px horizontal overflow; inspected at 1440px. Backend `npm ci` passed after lockfile-only sync; backend test suite passed (2 suites / 4 tests); real server `/health` returned HTTP 200 with routes mounted. | README accuracy, asset provenance, full journeys and package checks pending. |
| aurelia-estates | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| aurum-fitness | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| flowpilot | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| meridian-capital | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| nuage-events | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| prestige-studio | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| resupro | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| saffron-voyage | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |
| studio-lumen | `npm run build` passed (Vite build and SPA fallback). Backend `npm ci` and tests passed (2 suites / 4 tests); real server `/health` returned HTTP 200. | Browser, docs, asset provenance and package checks pending. |

## Known environment and catalog limitations

- All 11 frontend builds passed in the latest run; all emitted `dist/404.html`. The three focused product smoke assertions passed. Several builds emitted the existing Vite warning that English locale is statically and dynamically imported; builds exited successfully.
- All 11 backend installs now pass with `npm ci`; all 11 backend test suites pass (2 suites / 4 tests each), and isolated live-server checks returned HTTP 200 from `/health` for all 11 products. The existing backend lockfiles initially omitted declared dependencies; regenerated them with `npm install --package-lock-only --ignore-scripts --no-audit --no-fund` before clean installs. Dependency installation ran with lifecycle scripts disabled; final regular `npm ci` passed for all products. Docker CLI is unavailable, so Compose/database-container/full-stack checks remain unverified; no credentials were invented.
- Python is unavailable in this shell (`python` resolved to the Windows Store alias and exited with “Python was not found”). Python-based audit/packaging remains blocked; Node/bash inventories are usable.
- Original `.github/workflows/deploy.yml` workflows target production; none were used for staging.
- Generic template testimonials and remote runtime media appeared in the catalog audit. Verify authenticity, local assets and rights independently; sale-ready rights clearance is not established.
- Apex and ClaimFlow README bodies contain contradictory SaaS/commerce details and inaccurate setup claims; documentation audit/correction remains pending. All 11 backend manifests expose `start`, `dev`, `test`, `migrate` scripts and per-product `.env.example`/Compose files; clean dependency install and health/test paths were verified, but Compose-based full-stack setup was not.
- No browser verification was run for the other nine products. Backend test and health smoke checks pass, but database/container integration, broad user journeys, asset-rights clearance and buyer-doc verification remain incomplete. No archives, staging deploy or live verification occurred.

## Next work

Complete buyer-document and product-specific asset review, full interactive browser journeys/responsive coverage, and safe archive verification. Staging deployment requires its separately confirmed destination and explicit authorization; production remains untouched.
