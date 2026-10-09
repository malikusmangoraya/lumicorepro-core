# Seller Catalogue — 11 Products

Audit state: **11/11 sellable, 100/100, 0 fail, 0 warn** — 66 checks per product
(`AUDIT.md`, 2026-10-06).
Sale archives: `../release/products/` — 11 deterministic ZIPs + SHA-256 manifest,
`verify_release` 11/11 PASS. Upload a ZIP as the version file of each Lemon
Squeezy product below.

## What was verified, and how

Every claim below was measured, not assumed. Re-run any of it:

| Claim | Check | Result |
|---|---|---|
| Every product builds from a clean clone | `npm ci && npm run build` per product (`scripts/measure_product_bundles.py`) | **11/11 built** |
| Bundle budgets | worst case first paint **109.5 KB** gzip (target 150, hard 200), largest chunk **63.6 KB** (hard 300), CSS **11.2 KB** (target 30) | **inside every budget** |
| Every locale really is translated | `scripts/audit_products.py` → `i18n-translated`, `i18n-key-parity` | **0 English leftovers, 179–314 keys per locale** |
| Archives are complete and safe to sell | `scripts/verify_release.py` — opens each ZIP, checks forbidden paths, required files, internal fixes and SHA-256 | **11/11 PASS** |
| Live demos are up | HTTP GET on all 11 GitHub Pages URLs | **11/11 HTTP 200** |
| Source repositories are public | GitHub API on all 11 repos | **11/11 HTTP 200** |

Rebuilt on 2026-10-06 to fold in two fixes a buyer would have noticed:
locale files that still had English UI strings in all 13 non-English locales,
and three archives that predated their own hero video and poster (so the apex,
nuage-events and saffron-voyage hero clips would have 404'd on first run).

Support contact shipped in every file: `malikusmangoraya786@gmail.com`.

## Source code + live demo map

| Product | Source (`main`) | Live demo |
|---|---|---|
| Apex Digital | https://github.com/malikusmangoraya/apex-digital/tree/main | https://malikusmangoraya.github.io/apex-digital |
| Aurelia Estates | https://github.com/malikusmangoraya/aurelia-estates/tree/main | https://malikusmangoraya.github.io/aurelia-estates |
| Aurum Fitness | https://github.com/malikusmangoraya/aurum-fitness/tree/main | https://malikusmangoraya.github.io/aurum-fitness |
| ClaimFlow | https://github.com/malikusmangoraya/claimflow/tree/main | https://malikusmangoraya.github.io/claimflow |
| FlowPilot | https://github.com/malikusmangoraya/flowpilot/tree/main | https://malikusmangoraya.github.io/flowpilot |
| Meridian Capital | https://github.com/malikusmangoraya/meridian-capital/tree/main | https://malikusmangoraya.github.io/meridian-capital |
| Nuage Events | https://github.com/malikusmangoraya/nuage-events/tree/main | https://malikusmangoraya.github.io/nuage-events |
| Prestige Studio | https://github.com/malikusmangoraya/prestige-studio/tree/main | https://malikusmangoraya.github.io/prestige-studio |
| ResuPro | https://github.com/malikusmangoraya/resupro/tree/main | https://malikusmangoraya.github.io/resupro |
| Saffron Voyage | https://github.com/malikusmangoraya/saffron-voyage/tree/main | https://malikusmangoraya.github.io/saffron-voyage |
| Studio Lumen | https://github.com/malikusmangoraya/studio-lumen/tree/main | https://malikusmangoraya.github.io/studio-lumen |

Each repo carries the full product on `main` and serves the built demo from
`gh-pages`. Buyer listings should link both.

---

## What every product contains (do not repeat per listing — link it once)

- **Frontend** — React 19 + Vite SPA, Tailwind, 9–11 pages (Home, About,
  Services, Pricing, Contact, Login, Register, Checkout, Admin, Privacy, Terms),
  11-section conversion landing, dark mode, `prefers-reduced-motion` support,
  skip-to-content link, semantic landmarks, PWA (manifest, icons, SW, offline).
- **Backend** — Node 22 + Express, 33–34 route modules, JWT access + rotating
  refresh (httpOnly cookie), TOTP two-factor, OAuth, password reset,
  email verification, RBAC, rate limiting, Helmet + CORS, GDPR account
  export/deletion endpoints, Umzug migrations (`npm run migrate`), Jest +
  supertest suite incl. a live-server integration test.
- **Data + cache** — PostgreSQL (Sequelize, versioned Umzug migrations plus
  baseline schema) and Redis (cache service with TTL + in-memory fallback;
  health reports cache mode). Backup script `backend/scripts/backup.js`
  (`npm run backup`) with restore docs in BACKUP.md.
- **Payments** — Lemon Squeezy merchant-of-record: hosted/API checkout, signed
  HMAC webhooks, plan variants, buyer-tested config endpoint.
- **International** — 14 locales (ar, de, en, es, fr, hi, id, ja, ko, pt, ru,
  tr, ur, zh), RTL stylesheets, locale-aware dates/numbers/currency.
- **Ship it** — Docker multi-stage images + Compose (db, backend, frontend,
  healthchecks, no default passwords), CI (install → build → boot probe, no
  masked failures), GitHub Pages deploy workflow with SPA fallback.
- **Brand kit** — unique vector logo (favicon, PWA icons, Apple touch icon,
  OG share image, React `BrandMark`/`BrandLockup`), per-product palette and
  fonts (`BRAND_GUIDELINES.md`).
- **Docs (17)** — README, DEPLOYMENT, SECURITY, CHANGELOG, CONTRIBUTING,
  THIRD_PARTY_NOTICES, BUYER_DOCUMENTATION, COMMERCIAL_LICENSE,
  LEMON_SQUEEZY_SELLER_KIT, BRAND_GUIDELINES, LICENSE, LICENSE-SEAL,
  SUPPORT (support + update policy), ROADMAP, DEMO (demo seed),
  BACKUP (backup/restore), ACCESSIBILITY (baseline + audit guidance).

---

## Recommended pricing (uniform catalogue)

Comparable 2026 full-stack starters sell **$99–$399** one-time (Gumroad /
standalone). Niche-complete apps with backend + payments + Docker + docs sit
above bare templates. Recommended Lemon Squeezy variants, identical for all 11:

| Variant | Price (USD) | Licence |
|---|---|---|
| Standard | **$49** | 1 project / 1 client, 1 year updates |
| Agency | **$129** | Unlimited client deployments, priority email |
| Reseller | **$249** | Redistribution / whitelabel rights |

Tactics: launch at **$39 introductory** for 14 days, then $49. Offer an
**all-11 bundle at $199** (buyer psychology: 11 × $49 = $539 perceived value).
Lemon Squeezy is merchant of record (tax/VAT handled). These are
recommendations — the final price is yours.

---

## The 11 products

### 1. Apex Digital — B2B conversion analytics platform
- Niche: precision commerce / SaaS. Live demo: `apex-digital`.
- 12 pages, 33 routes. Niche page: Insights. **Cinematic video hero** (verified streamable abstract
  data-network loop, poster-first, reduced-motion safe).
- Sells to: revenue teams, agencies selling analytics setups.
- Listing blurb: "Apex Digital turns scattered intent data into a forecast the
  whole revenue team trusts — account scoring, sequence automation and
  multi-touch attribution in one workspace, with auth, billing and Docker
  included."

### 2. Aurelia Estates — luxury real-estate brokerage
- Niche: luxury real estate. Live demo: `aurelia-estates`.
- 13 pages, 33 routes. Niche page: Listings. Typographic hero, off-market listings, concierge
  service copy, portfolio stats.
- Sells to: realtors, property developers, relocation concierges.
- Listing blurb: "A white-glove brokerage site — private listings, concierge
  viewings, international portfolios — with accounts, admin KPIs and checkout
  ready for reservations and retainers."

### 3. Aurum Fitness — performance coaching club
- Niche: fitness coaching. Live demo: `aurum-fitness`.
- 13 pages, 33 routes. Niche page: Programs. Dopamine-saturated design, programs, coaching, metrics.
- Sells to: gyms, personal trainers, coaching programs.
- Listing blurb: "A high-energy coaching platform — programs, private coaching,
  recovery lab and performance metrics — with memberships, billing and member
  accounts out of the box."

### 4. ClaimFlow — insurance claims intake
- Niche: insurance claims. Live demo: `claimflow`.
- 12 pages, 34 routes. Niche page: Claims. Claims intake without the backlog; tracker-style UX.
- Sells to: insurers, brokers, claims startups.
- Listing blurb: "Claims intake without the backlog — guided filing, status
  tracking and admin review, with secure auth, audit logging and payments."

### 5. FlowPilot — SaaS work operating system
- Niche: SaaS (projects + billing + insight). Live demo: `flowpilot`.
- 12 pages, 33 routes. Niche page: Projects. Newest build: emerald/indigo identity, orbital-flow logo.
- Sells to: founders, agencies, freelancers needing a client-work OS.
- Listing blurb: "The whole operation on one calm screen — project plans that
  stay current, self-sending invoices and team insight boards, on a codebase
  that already handles auth, billing, cache and Docker."

### 6. Meridian Capital — private-capital portfolio site
- Niche: fintech / portfolio intelligence. Live demo: `meridian-capital`.
- 13 pages, 33 routes. Niche page: Portfolio. Institutional-minimal design, reporting, access-gated
  content patterns.
- Sells to: funds, family offices, advisors, fintech startups.
- Listing blurb: "Institutional-grade presence — concentrated portfolios,
  research and transparent reporting — with gated access, admin dashboards and
  compliance-ready security headers."

### 7. Nuage Events — event production studio
- Niche: events & ticketing. Live demo: `nuage-events`.
- 13 pages, 33 routes. Niche page: Events. **Cinematic video hero** (verified rooftop-dance loop),
  festival/gala copy, past-events showcase.
- Sells to: event agencies, venues, festival organizers.
- Listing blurb: "Event production that sells the night — launches, festivals
  and galas with a cinematic video hero, booking flow, ticketing-ready checkout
  and multilingual pages."

### 8. Prestige Studio — creative agency site
- Niche: creative studio / portfolio. Live demo: `prestige-studio`.
- 13 pages, 33 routes. Niche page: Work. Asymmetric editorial design, case-work structure,
  project-inquiry flow.
- Sells to: design studios, freelancers, agencies.
- Listing blurb: "An agency site with the craft to match the work — identity,
  digital product and motion case sections, inquiry pipeline and admin inbox."

### 9. ResuPro — résumé builder
- Niche: career / résumé SaaS. Live demo: `resupro`.
- 13 pages, 33 routes. Niche page: Templates. Builder UX, templates, career-growth positioning.
- Sells to: career coaches, HR startups, edtech.
- Listing blurb: "Résumés that get the interview — guided builder, templates
  and exports, with subscriptions, user accounts and reminder emails."

### 10. Saffron Voyage — boutique travel studio
- Niche: curated travel. Live demo: `saffron-voyage`.
- 13 pages, 33 routes. Niche page: Itineraries. **Cinematic video hero** (verified aerial-beach loop),
  itineraries, destinations, storyteller positioning.
- Sells to: travel agencies, tour operators, retreat organizers.
- Listing blurb: "Travel the way it once felt — small-group journeys,
  itineraries and booking inquiry, with a cinematic video hero, 14 languages
  and multi-currency pricing."

### 11. Studio Lumen — photography collective
- Niche: photography / portfolio. Live demo: `studio-lumen`.
- 13 pages, 33 routes. Niche page: Galleries. Editorial masonry galleries, commission flow, print
  sales structure.
- Sells to: photographers, studios, galleries.
- Listing blurb: "Photography in pursuit of light — galleries, commissions and
  print sales, with client accounts, order management and payments."

---

## Listing checklist per product (Lemon Squeezy)

1. Product name + blurb above + tags (`react-19`, `vite`, `tailwind`,
   `full-stack`, `lemon-squeezy`, niche tag, `docker`, `i18n`).
2. Upload the matching ZIP from `release/products/` as the version file.
3. Add 3 variants ($49 / $129 / $249) with the licence text from
   `COMMERCIAL_LICENSE.md`.
4. Thumbnails: OG image is inside each product (`frontend/public/og-image.png`,
   1200×630) — reuse as cover; record a 60-second walkthrough of the live demo
   for the gallery.
5. Publish one demo repo per product to GitHub Pages (workflow included) and
   paste the demo URL in the listing — buyers convert on live demos.

## Remaining before publishing (all local work is done)

1. Revoke the once-exposed GitHub token (removed from tree; revoke in GitHub).
2. Push each product to its own repo (`main`), Pages source = GitHub Actions.
3. Open each live demo once; run the API section of `DEPLOYMENT.md` on a clean
   machine (all 11 live demos returned HTTP 200 on 2026-10-07; all 11 backends
   pass `npm test`, 2 suites / 4 tests each, incl. a live-server integration
   test — measured before packaging; the Sentry wiring added afterwards is
   DSN-gated and re-verified green on flowpilot).

## 2026-10-07 hardening addendum (verified, in the archives above)

- Backend `.env.example` regenerated from real `process.env` usage (159 keys,
  grouped and documented); frontend examples scrubbed to `VITE_` only.
- Umzug migrations (`npm run migrate`), Jest + supertest suite (`npm test`),
  GDPR export/delete endpoints, `routes/package.json` ESM typing.
- Dead `mongoose` removed (prestige-studio, resupro); missing `zustand` added
  (resupro); `models/index.js` undefined Invoice/Transaction refs removed.
- Niche page per product (Insights, Listings, Programs, Claims, Projects,
  Portfolio, Events, Work, Templates, Itineraries, Galleries), Admin page
  where missing (apex, flowpilot, claimflow-ai), GDPR `/account` page, demo
  banner on Login, Sentry wiring, `backup.js` + BACKUP.md, SUPPORT/ROADMAP/
  DEMO/ACCESSIBILITY docs, Dependabot + `npm run audit`.
