# Apex International Dealer Commerce Implementation Plan

> **For agentic workers:** Use task-by-task implementation with a fresh review gate between phases. Keep each phase independently testable; do not begin implementation until the user approves this plan and chooses an execution method. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Apex into a trustworthy international single-dealer vehicle showroom with live inventory discovery, secure buyer/admin workflows, and a reservation-deposit path that remains disabled until legal/provider approval.

**Architecture:** Keep the existing React/Vite frontend and Express/Sequelize backend. Add explicit vehicle, inquiry, reservation, and payment-event boundaries through migrations and APIs; treat server-side ownership/authorization and signed idempotent provider webhooks as authoritative. Roll out showroom/inquiries first, accounts/admin next, then sandbox deposits behind a disabled-by-default feature gate.

**Tech Stack:** React 19, React Router 6, React Query 5, Zustand 5, i18next, Axios; Express 4, Sequelize 6, PostgreSQL (SQLite test fallback), Umzug, Jest/Supertest; existing Stripe SDK/payment abstraction. Add no dependency unless required and verified against project conventions.

**Spec:** [2026-10-11 Apex international dealer-commerce design](docs/superpowers/specs/2026-10-11-apex-international-dealer-commerce-design.md)

## Global Constraints

- Apex owns the inventory; no third-party seller onboarding, bidding, financing origination, full-price checkout, auto-tax or shipping quote.
- Do not publish fabricated inventory, metrics, endorsements, inspection claims, testimonials or unsupported facts.
- Listing currency is authoritative; converted prices, if added, must be clearly informational with rate/time disclosed.
- Payment amount/currency/terms must come from a server-side immutable reservation snapshot; browser redirects never confirm payment.
- Signed provider webhooks are required for payment state; idempotency and replay protection are mandatory.
- No direct card data handling. Live checkout remains disabled absent written provider and jurisdiction approval and supplied refund/cancellation terms.
- Scope private buyer queries by authenticated user; enforce admin roles server-side and audit privileged state changes.
- Preserve i18next/RTL, responsive/mobile-first behavior, reduced-motion support, keyboard/screen-reader usability, and consent/privacy workflows.
- Use versioned `/api/v1` interfaces and migrations; do not rely on schema auto-alter.

## Review Focus

- Unknown/malformed inventory filters, invalid currency and inverted price/mileage ranges return safe validation errors rather than unbounded queries — Task 2 tests.
- Concurrent reservations for the same vehicle cannot both become active — Task 7 tests.
- A buyer cannot infer/read another buyer's private saved items, inquiries, reservations or receipt — Task 5 and Task 6 tests.
- Admin role changes or stale/missing user records cannot preserve stale authorization from JWT claims — Task 5 tests.
- Duplicate, replayed, invalid-signature and out-of-order payment events cannot forge or duplicate paid state — Task 8 tests.

---

## File Structure

**Backend (`products/sell-today/apex/backend`):**
- `migrations/*-create-vehicles.js`, `*-create-inquiries.js`, `*-create-reservations.js`, `*-create-payment-events.js`: versioned DDL with indexes, constraints and rollback.
- `models/Vehicle.js`, `Inquiry.js`, `Reservation.js`, `PaymentEvent.js`: focused Sequelize records and state validation.
- `models/index.js`: associate the new records without disturbing legacy catalog models.
- `services/vehicle.service.js`, `inquiry.service.js`, `reservation.service.js`: domain rules, transactional transitions, access-scoped queries.
- `routes/vehicles.routes.js`, `inquiries.routes.js`, `reservations.routes.js`, `payment.routes.js`: public/auth/admin boundaries; preserve existing signed webhook route behavior.
- `middleware/auth.js`, relevant auth route files: load authoritative user/role and cookie-based session changes.
- `__tests__/vehicles.routes.test.js`, `inquiries.routes.test.js`, `reservations.routes.test.js`, `payments.webhook.test.js`, `auth.session.test.js`: route, ownership, transaction, security coverage.

**Frontend (`products/sell-today/apex/frontend/src`):**
- `pages/Home.jsx`, `Services.jsx`, `Login.jsx`, `Register.jsx`: correct remaining legacy copy; homepage featured inventory is API-backed.
- `pages/Inventory.jsx`, `VehicleDetail.jsx`, `Account.jsx`, `Admin.jsx`: discovery/detail, account and staff workflows.
- `App.jsx`: routes `/inventory`, `/inventory/:slug`, account subviews and admin guard.
- `components/vehicle/VehicleCard.jsx`, `InventoryFilters.jsx`, `VehicleGallery.jsx`, `VehicleInquiryForm.jsx`: focused reusable UI.
- `services/api.js`, `services/vehicleApi.js`, `services/accountApi.js`: cookie-aware API functions.
- `store/savedVehicles.js` (only if cross-page client state is necessary): lightweight client selection; server remains source of truth.
- `i18n/locales/*`: add copy to supported locales only; no untranslated key should be represented as complete localization.
- `frontend/src/__tests__/*` or existing test location: UI/API component coverage; inspect current harness before choosing exact test path.

**Deployment/operator docs:**
- `products/sell-today/apex/backend/.env.example`: document disabled-by-default deposit gate and provider webhook vars without values.
- `products/sell-today/apex/README.md` / `DEPLOYMENT.md`: migration, sandbox-only setup and explicit live approval checklist.

## Phase 1 — Inventory foundation, showroom and inquiry

### Task 1: Add vehicle schema and migration

**Files:**
- Create: `products/sell-today/apex/backend/migrations/<timestamp>-create-vehicles.js`
- Create: `products/sell-today/apex/backend/models/Vehicle.js`
- Modify: `products/sell-today/apex/backend/models/index.js`
- Test: `products/sell-today/apex/backend/__tests__/vehicle.model.test.js`

**Interfaces:**
- `Vehicle` fields: `id`, unique `slug`, `make`, `model`, `year`, `title`, `description`, `price` decimal, ISO `currency`, `mileage`, `mileageUnit` (`km|mi`), `bodyStyle`, `fuelType`, `transmission`, `locationCountry`, `locationRegion`, `status` (`draft|active|reserved|sold|withdrawn`), ordered `media`/inspection references, verified provenance/condition fields, timestamps.
- Model associations expose vehicle relations to inquiry and reservation after their tasks land; avoid requiring future tables in this migration.

- [ ] Test migration up/down and model validation for required fields, nonnegative price/mileage, allowed currency/status/unit, unique slug.
- [ ] Implement migration and model with indexes for status, make/model, year, price/currency, location; ensure SQLite-compatible test fields where feasible.
- [ ] Run: `cd products/sell-today/apex/backend && npm test -- --runInBand __tests__/vehicle.model.test.js` — expected: all focused schema/model tests pass.

### Task 2: Public vehicle query API and admin inventory API

**Files:**
- Create: `products/sell-today/apex/backend/services/vehicle.service.js`
- Create: `products/sell-today/apex/backend/routes/vehicles.routes.js`
- Create: `products/sell-today/apex/backend/__tests__/vehicles.routes.test.js`
- Modify: `products/sell-today/apex/backend/models/index.js` (associations if needed)

**Interfaces:**
- `GET /api/vehicles`: accepts `q, make, model, yearMin, yearMax, priceMin, priceMax, currency, mileageMax, mileageUnit, bodyStyle, fuelType, transmission, country, status, sort, page, limit`; public responses include active listings only.
- `GET /api/vehicles/:slug`: active detail only; inactive detail is 404 to public users.
- `POST /api/vehicles`, `PATCH /api/vehicles/:id`, `DELETE /api/vehicles/:id`: admin-only create/update/soft withdraw (do not hard-delete a vehicle with inquiry/reservation history).
- `listVehicles(filters): {items, page, limit, total}` validates bounded page/limit and whitelisted sort fields.

- [ ] Add tests for filter combinations, pagination and sort whitelist; malformed bounds, negative values and too-large limits return 400; inactive listing is not disclosed publicly; non-admin writes return 403; mass-assignment attempts cannot set ids/status flags outside authorized admin fields.
- [ ] Implement the service with ORM parameterized conditions and route validation; admin writes record audit actor/time.
- [ ] Run focused tests: `cd products/sell-today/apex/backend && npm test -- --runInBand __tests__/vehicles.routes.test.js` — expected: pass without requiring a live provider.

### Task 3: Catalog-driven international showroom and vehicle detail

**Files:**
- Create: `products/sell-today/apex/frontend/src/pages/Inventory.jsx`
- Create: `products/sell-today/apex/frontend/src/pages/VehicleDetail.jsx`
- Create: `products/sell-today/apex/frontend/src/components/vehicle/VehicleCard.jsx`
- Create: `products/sell-today/apex/frontend/src/components/vehicle/InventoryFilters.jsx`
- Create: `products/sell-today/apex/frontend/src/components/vehicle/VehicleGallery.jsx`
- Create: `products/sell-today/apex/frontend/src/services/vehicleApi.js`
- Modify: `products/sell-today/apex/frontend/src/App.jsx`, `Home.jsx`, `Navbar.jsx`, `index.css`, locale files
- Test: existing/new frontend test files under `products/sell-today/apex/frontend/src/**/__tests__/*`

**Interfaces:**
- `vehicleApi.list(filters, {signal})` and `vehicleApi.getBySlug(slug, {signal})` return backend envelope data.
- Inventory filters use `useSearchParams`; browser back/forward restores search state.
- `VehicleCard` consumes a `VehicleSummary` and displays verified location, authoritative currency and selected mileage units.

- [ ] Add tests that URL filters encode/decode, empty/loading/error/retry states render, currency is formatted by `Intl.NumberFormat`, and absent/unknown facts are omitted (never fabricated).
- [ ] Implement `/inventory` and `/inventory/:slug`, then replace home mock cards and update nav labels to collection/inventory; correct product identity and preserve brand design tokens.
- [ ] Use `LazyImage` if an existing helper is available; otherwise use native lazy loading and stable aspect ratios. No remote image source is treated as verified vehicle evidence.
- [ ] Run frontend build `cd products/sell-today/apex/frontend && npm run build` and focused UI tests using the discovered existing harness; expected: successful build and tests.

### Task 4: Inquiry capture and staff lead queue

**Files:**
- Create: `products/sell-today/apex/backend/migrations/<timestamp>-create-inquiries.js`
- Create: `products/sell-today/apex/backend/models/Inquiry.js`
- Create: `products/sell-today/apex/backend/services/inquiry.service.js`
- Create: `products/sell-today/apex/backend/routes/inquiries.routes.js`
- Create: `products/sell-today/apex/backend/__tests__/inquiries.routes.test.js`
- Create: `products/sell-today/apex/frontend/src/components/vehicle/VehicleInquiryForm.jsx`
- Modify: contact/vehicle detail UI and `products/sell-today/apex/backend/models/index.js`

**Interfaces:**
- `POST /api/inquiries` validates vehicle id, message, contact data and privacy consent; authenticated users are bound to `req.user.id`; allow anonymous inquiries only with verified contact fields and consent.
- `GET /api/inquiries/mine` returns caller-owned inquiries only.
- `GET /api/inquiries/admin`, `PATCH /api/inquiries/:id/status` are admin-only; statuses `new|contacted|viewing_scheduled|closed|spam`.

- [ ] Test valid/invalid submission, duplicate-submit idempotency strategy, user scoping (including IDOR), anonymous validation, admin-only status edits and audit trail.
- [ ] Implement repository/service and UI confirmation/retry behavior; prevent repeated form submission while in flight.
- [ ] Run focused backend tests plus frontend tests/build; expected: inquiry persists only once and is visible to owner/admin only.

## Phase 2 — Accounts, security and operations

### Task 5: Secure customer session and auth UX

**Files:**
- Modify: `products/sell-today/apex/backend/middleware/auth.js`, `backend/routes/auth.routes.js`, `backend/server.js`, relevant auth tests
- Modify: `products/sell-today/apex/frontend/src/services/api.js`, `pages/Login.jsx`, `pages/Register.jsx`, `pages/Account.jsx`
- Test: `products/sell-today/apex/backend/__tests__/auth.session.test.js` and frontend auth tests

**Interfaces:**
- Browser session: short-lived access token held in memory; refresh token only in `Secure; HttpOnly; SameSite=Lax` cookie in production, scoped to `/api/auth`; frontend requests use `withCredentials: true`.
- Auth middleware resolves active user and role authoritatively from persistence for privileged routes; token role is not sufficient for admin access.

- [ ] Test login/register/refresh/logout cookie flags, refresh rotation/reuse rejection, expired/inactive user rejection, CSRF/origin rules, role downgrade taking effect, and no credentials/tokens in localStorage.
- [ ] Implement session contract; remove `refresh_token` localStorage behavior and redirect loops; replace automotive page copy and wire forgot-password/verification UI to existing endpoints.
- [ ] Run focused auth tests and frontend build/tests; expected: auth behavior passes without weakening existing assertions.

### Task 6: Buyer saved listings and account history; secure admin screens

**Files:**
- Create or adapt migration/model for saved vehicle relation in backend migrations/models.
- Create: backend saved vehicle service/routes/tests; frontend `accountApi.js` and account panels.
- Modify: `pages/Account.jsx`, `pages/Admin.jsx`, `App.jsx`, navbar and service modules.

**Interfaces:**
- `PUT /api/account/saved-vehicles/:vehicleId`, `DELETE /api/account/saved-vehicles/:vehicleId`, `GET /api/account/saved-vehicles` are authenticated and always scope user id from session.
- Account views list saved vehicles, own inquiry history and reservation history with status; admin UI consumes admin inventory and lead endpoints.

- [ ] Test IDOR attempts against saved vehicles/inquiries, duplicate save idempotency, removed listing behavior, route guard UX, and unauthorized `/admin` API denial.
- [ ] Implement account/admin screens with loading/empty/error/retry states; no hardcoded KPI values or user-provided admin IDs.
- [ ] Run relevant API/UI tests and production frontend build; expected: ownership boundaries and rendering pass.

## Phase 3 — Reservation lifecycle and sandbox payment (live off)

### Task 7: Reservation state machine and concurrency safety

**Files:**
- Create: `products/sell-today/apex/backend/migrations/<timestamp>-create-reservations.js`
- Create: `backend/models/Reservation.js`, `backend/services/reservation.service.js`, `backend/routes/reservations.routes.js`
- Create: `backend/__tests__/reservations.routes.test.js`
- Modify: `backend/models/index.js`, buyer/admin account UI

**Interfaces:**
- `POST /api/reservations` accepts `vehicleId` and buyer-confirmed terms version only; server loads configured deposit amount/currency/expiry and snapshots terms.
- `GET /api/reservations/mine`, `GET /api/reservations/admin`, admin `PATCH /api/reservations/:id/cancel` enforce owner/admin role.
- State machine: `pending_payment -> paid -> confirmed -> completed`; permitted exits to `expired`, `cancelled`, `refund_pending`, `refunded`, `payment_failed`; illegal transitions return 409.

- [ ] Test concurrent reservation requests for one vehicle using transaction/unique constraint, quote tampering, currency mismatch, expiry, illegal transitions, cancellation and account scoping.
- [ ] Implement reservation creation/transition under database transaction and uniqueness constraint; add DB-backed conflict response.
- [ ] Run reservation suite against supported PostgreSQL test setup where available and SQLite smoke tests; expected: only one active reservation wins.

### Task 8: Provider-neutral deposit checkout and signed webhook processing

**Files:**
- Modify: `products/sell-today/apex/backend/routes/payment.routes.js`, provider abstraction/services and webhook registry only where needed.
- Create: `backend/services/payment/depositCheckout.service.js`, `backend/__tests__/payments.webhook.test.js`.
- Modify: `.env.example`, frontend reservation UI, README/DEPLOYMENT docs.

**Interfaces:**
- `POST /api/reservations/:id/checkout` returns provider redirect only when `DEPOSIT_CHECKOUT_ENABLED=false` gate is explicitly enabled for sandbox and reservation is eligible; live environment remains blocked without separate approval configuration.
- Provider service receives `{reservationId, amountMinor, currency, idempotencyKey, successUrl, cancelUrl}` from server-derived reservation snapshot and returns `{providerSessionId, redirectUrl}`.
- Signed webhook event handler verifies raw bytes/signature, persists unique provider event id, and transactionally advances reservation/payment state.

- [ ] Test feature gate default-off and production-off, server-derived amount despite client tampering, provider timeout/unknown state, invalid signatures, duplicate/replayed/out-of-order webhooks, and return URL cannot set paid state.
- [ ] Implement only sandbox-capable flow with existing Stripe/PayPal abstractions after validating current SDK APIs and provider-specific docs; do not add live credentials or assert provider eligibility.
- [ ] Add operational docs with exact sandbox env names, webhook setup, refund/reconciliation and approval checklist; verify `.env.example` has names/placeholders only.
- [ ] Run payment tests/build; expected: sandbox events are idempotent and no live charge can occur by default.

## Phase 4 — Final quality gate and operator handoff

### Task 9: International polish, SEO, responsive/a11y and end-to-end verification

**Files:**
- Modify: frontend vehicle pages, locale resources, metadata/SEO configuration, `README.md`, `DEPLOYMENT.md`.
- Create/update: `products/sell-today/apex/frontend` Playwright/E2E tests where harness already exists; test report if project convention requires.

- [ ] Add verified vehicle JSON-LD only on active vehicle detail pages, canonical URLs, localized metadata, sitemap inclusion and noindex for account/admin/private routes.
- [ ] Test primary journeys at 375/768/1024/1440/1920 widths, keyboard-only navigation, focus order, reduced motion, RTL direction, contrast and image alt text; include failed API/payment states.
- [ ] Walk through as anonymous visitor, registered buyer, second isolated buyer and admin; verify network/console logs and that demo data is not represented as real inventory.
- [ ] Run `cd products/sell-today/apex/frontend && npm run build`; `cd products/sell-today/apex/backend && npm test -- --runInBand`; plus configured e2e command discovered in repo. Expected: build/test suites green, browser walkthrough passes; report any unavailable DB/provider checks as blocked, not passed.
- [ ] Verify deployment is not performed; require a separate explicit request for publishing.

## Plan self-review notes

- **Coverage:** Spec sections 1–4 map to Tasks 1–4 and 9; sections 5–6 map to Tasks 1–7; section 7 maps to Tasks 7–8; section 8 maps to Tasks 3/9; section 9 boundaries are Global Constraints; section 10 maps to Tasks 4/7/8; section 11 is covered by phase tests and Task 9.
- **Scope:** Three independently deliverable subprojects: inventory/storefront/inquiries; accounts and staff operations; reservation payments. Payments can remain disabled while first two phases ship.
- **Interface consistency:** Reservation creation returns `pending_payment`; payment webhooks move it to `paid`; admin confirmation moves it to `confirmed`; reservation route owns user/admin authorization; provider service never trusts client amount/currency.
- **Open prerequisite:** Merchant country, markets, real inventory/data source, and deposit/refund terms remain owner-supplied. No plan step fabricates them; if absent, deploy inquiry-only behavior and keep checkout disabled.
- **Repository test harness caution:** frontend package currently declares no direct test script/dependency, so executor must inspect existing root/frontend harness and use the available test path rather than silently adding a framework or claiming UI tests ran.
