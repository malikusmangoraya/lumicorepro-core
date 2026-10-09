# Product Sellability Audit

_Generated 2026-10-06T11:49:19_

| Product | Score | Pass | Warn | Fail | Verdict |
|---|---:|---:|---:|---:|---|
| [apex](apex/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [aurelia-estates](aurelia-estates/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [aurum-fitness](aurum-fitness/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [claimflow-ai](claimflow-ai/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [flowpilot](flowpilot/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [meridian-capital](meridian-capital/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [nuage-events](nuage-events/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [prestige-studio](prestige-studio/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [resupro](resupro/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [saffron-voyage](saffron-voyage/) | 100/100 | 66 | 0 | 0 | ✅ sellable |
| [studio-lumen](studio-lumen/) | 100/100 | 66 | 0 | 0 | ✅ sellable |

## apex — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 15 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 35 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 9 page components: about, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 66 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (179 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 179 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, apex-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml, test.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/apex-digital |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/apex-digital |
| ✅ PASS | Documentation | `doc-readme` | README.md (9,562 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,045 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (807 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (3,982 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,588 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,499 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,337 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 9,212 chars |
| ✅ PASS | Documentation | `support-contact` | 7 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 150 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 143 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## aurelia-estates — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 33 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 84 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (314 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 314 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, aurelia-estates-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/aurelia-estates |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/aurelia-estates |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,526 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,070 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (827 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,004 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,643 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,517 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,348 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,180 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 146 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## aurum-fitness — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 32 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 57 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (216 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 216 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, aurum-fitness-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/aurum-fitness |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/aurum-fitness |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,431 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,064 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (819 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,000 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,633 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,505 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,346 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,079 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 143 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## claimflow-ai — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 15 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 35 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 9 page components: about, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 50 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (174 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 174 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, claimflow-ai-002-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/claimflow |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/claimflow |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,641 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,058 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (806 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,006 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,648 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,481 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,345 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,293 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 34 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 150 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 142 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## flowpilot — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 15 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 35 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 9 page components: about, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 66 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (179 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 179 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, flowpilot-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml, test.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/flowpilot |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/flowpilot |
| ✅ PASS | Documentation | `doc-readme` | README.md (9,581 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,052 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (803 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (3,992 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,686 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,481 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,342 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 9,231 chars |
| ✅ PASS | Documentation | `support-contact` | 7 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 150 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 142 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## meridian-capital — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 32 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 50 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (189 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 189 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, meridian-capital-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/meridian-capital |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/meridian-capital |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,378 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,073 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (831 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,006 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,648 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,523 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,349 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,025 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 143 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## nuage-events — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 32 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 67 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (189 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 189 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, nuage-events-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/nuage-events |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/nuage-events |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,470 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,061 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (815 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (3,998 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,628 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,499 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,345 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,117 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 144 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## prestige-studio — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 33 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 67 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (190 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 190 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, prestige-studio-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/prestige-studio |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/prestige-studio |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,364 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,070 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (827 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,004 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,643 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,517 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,348 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,014 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 143 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## resupro — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 15 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 33 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 48 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (231 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 231 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, resupro-002-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/resupro |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/resupro |
| ✅ PASS | Documentation | `doc-readme` | README.md (7,927 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,046 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (795 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (3,996 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,623 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,469 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,340 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 7,578 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 121 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## saffron-voyage — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 33 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 67 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (193 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 193 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, saffron-voyage-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/saffron-voyage |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/saffron-voyage |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,370 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,067 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (823 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (4,002 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,638 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,511 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,347 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,019 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 144 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |

## studio-lumen — 100/100

| Status | Category | Check | Detail |
|---|---|---|---|
| ✅ PASS | Security | `no-hardcoded-credentials` | no hardcoded password literals in runtime code |
| ✅ PASS | Security | `no-committed-secrets` | no private keys or provider tokens in the tree |
| ✅ PASS | Security | `no-env-file-shipped` | no live .env file in the deliverable |
| ✅ PASS | Security | `backend-hardening` | helmet + cors + rate limiting wired in server.js |
| ✅ PASS | Security | `gitignore-coverage` | .gitignore covers .env and node_modules |
| ✅ PASS | Provenance | `no-developer-paths` | no absolute developer paths |
| ✅ PASS | Provenance | `no-generator-attribution` | no generator attribution |
| ✅ PASS | Provenance | `no-stray-vcs-or-archives` | no .git directory or bundled archives |
| ✅ PASS | Dependencies | `frontend-version-pins` | 16 dependency ranges resolve |
| ✅ PASS | Dependencies | `frontend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Dependencies | `backend-version-pins` | 33 dependency ranges resolve |
| ✅ PASS | Dependencies | `backend-lockfile` | package-lock.json present (npm ci reproducible) |
| ✅ PASS | Frontend / UI-UX | `frontend-pages` | 11 page components: about, admin, checkout, contact, home, login, pricing, privacy, register, services, terms |
| ✅ PASS | Frontend / UI-UX | `login-page` | login page: login.jsx |
| ✅ PASS | Frontend / UI-UX | `signup-page` | signup page: register.jsx |
| ✅ PASS | Frontend / UI-UX | `auth-routed` | auth screens routed in App.jsx: Login, Register |
| ✅ PASS | Frontend / UI-UX | `privacy-page` | frontend/src/pages/Privacy.jsx |
| ✅ PASS | Frontend / UI-UX | `terms-page` | frontend/src/pages/Terms.jsx |
| ✅ PASS | Frontend / UI-UX | `design-tokens` | design tokens present (design-tokens.json) |
| ✅ PASS | Frontend / UI-UX | `reduced-motion` | honours prefers-reduced-motion |
| ✅ PASS | Frontend / UI-UX | `layout-system` | utility layout system (Tailwind) configured |
| ✅ PASS | Internationalisation | `i18n-coverage` | 14 locales: ar, de, en, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh |
| ✅ PASS | Internationalisation | `rtl-support` | RTL styles for ar, ur in rtl.css |
| ✅ PASS | Internationalisation | `currency-localisation` | 67 currency/locale-formatting reference(s) |
| ✅ PASS | Internationalisation | `i18n-translated` | all 13 non-English locales fully translated (190 keys each, 0 English leftovers) |
| ✅ PASS | Internationalisation | `i18n-key-parity` | every locale carries exactly the 190 English keys |
| ✅ PASS | Docker | `dockerfiles` | frontend/Dockerfile and backend/Dockerfile present |
| ✅ PASS | Docker | `compose-services` | 5 services: db, backend, frontend, postgres_data, studio-lumen-network (healthchecks present) |
| ✅ PASS | Docker | `docker-multistage` | frontend Dockerfile is multi-stage |
| ✅ PASS | Docker | `docker-pinned-base` | pinned alpine base image |
| ✅ PASS | CI/CD | `workflows-present` | workflows: ci.yml, deploy.yml |
| ✅ PASS | CI/CD | `ci-runs-install` | CI installs dependencies with npm ci |
| ✅ PASS | CI/CD | `ci-no-error-masking` | no `|| true` failure masking in CI |
| ✅ PASS | CI/CD | `ci-build` | CI runs the frontend build |
| ✅ PASS | CI/CD | `ci-boot-probe` | CI boots the API and probes /health |
| ✅ PASS | CI/CD | `deploy-pages` | GitHub Pages deploy workflow: deploy.yml |
| ✅ PASS | Live demo | `vite-base` | vite base is env-driven via VITE_BASE_PATH — correct for a Pages subpath and for a custom domain alike |
| ✅ PASS | Live demo | `vite-env-config` | vite config reads environment variables |
| ✅ PASS | Live demo | `spa-routing` | BrowserRouter with a 404.html fallback regenerated on every build |
| ✅ PASS | Live demo | `live-url-recorded` | live URL recorded: https://malikusmangoraya.github.io/studio-lumen |
| ✅ PASS | Live demo | `live-url-consistent` | every shipped reference matches https://malikusmangoraya.github.io/studio-lumen |
| ✅ PASS | Documentation | `doc-readme` | README.md (8,424 bytes) |
| ✅ PASS | Documentation | `doc-deployment-guide` | DEPLOYMENT.md (5,061 bytes) |
| ✅ PASS | Documentation | `doc-license` | LICENSE.md (815 bytes) |
| ✅ PASS | Documentation | `doc-security-policy` | SECURITY.md (2,379 bytes) |
| ✅ PASS | Documentation | `doc-changelog` | CHANGELOG.md (1,480 bytes) |
| ✅ PASS | Documentation | `doc-buyer-docs` | BUYER_DOCUMENTATION.md (3,998 bytes) |
| ✅ PASS | Documentation | `doc-seller-kit` | LEMON_SQUEEZY_SELLER_KIT.md (4,628 bytes) |
| ✅ PASS | Documentation | `doc-commercial-license` | COMMERCIAL_LICENSE.md (1,499 bytes) |
| ✅ PASS | Documentation | `doc-contributing` | CONTRIBUTING.md (1,345 bytes) |
| ✅ PASS | Documentation | `readme-no-placeholders` | README is free of placeholder text |
| ✅ PASS | Documentation | `readme-substance` | README is 8,072 chars |
| ✅ PASS | Documentation | `support-contact` | 6 support email reference(s) in docs |
| ✅ PASS | Licensing | `license-present` | LICENSE.md references a recognised licence |
| ✅ PASS | Licensing | `license-seal` | LICENSE-SEAL.md present |
| ✅ PASS | Licensing | `third-party-notices` | THIRD_PARTY_NOTICES.md present |
| ✅ PASS | Content hygiene | `no-placeholder-text` | no placeholder or filler text in shipped code or docs |
| ✅ PASS | Backend | `backend-routes` | 33 route modules |
| ✅ PASS | Backend | `backend-auth-endpoints` | auth.routes.js exposes both register and login |
| ✅ PASS | Backend | `backend-jwt` | JWT dependency declared |
| ✅ PASS | Backend | `backend-health` | health endpoint present |
| ✅ PASS | Backend | `backend-env-example` | backend/.env.example present |
| ✅ PASS | Backend | `database-schema` | database schema files: 3 |
| ✅ PASS | Code health | `backend-syntax` | all 145 backend JavaScript files parse |
| ✅ PASS | Code health | `frontend-imports-resolve` | every relative import in 143 frontend files resolves |
| ✅ PASS | Code health | `service-worker-subpath` | service worker URLs and scope are base-relative |
