# Apex International Dealer Commerce — Design Spec

**Status:** Draft for user review; no implementation plan or code changes authorized yet.  
**Product:** Apex Motor Collective — single-dealer performance and collector-car showroom.

## 1. Intent and success

Transform Apex from a generic marketing/demo website into a trustworthy international dealership experience. The first milestone is the premium dealer storefront, backed by an operational inventory and inquiry journey. Apex owns and sells its own inventory; this is not a multi-seller marketplace. Customers can browse without an account, then use an account for saved vehicles, inquiry history, and reservation status.

Vehicle balances are not collected online in this milestone. A clearly disclosed, configurable reservation deposit can be paid online only after staff confirm availability and provide the applicable deposit terms. Vehicle balance, tax/duties, shipping, inspection and title transfer are settled through a separately agreed process.

Success means visitors can find an actual active vehicle, understand its condition/provenance and location, submit a traceable inquiry, optionally reserve through an approved provider, and manage the resulting activity in an account. Staff can securely maintain inventory and process leads/reservations.

## 2. Reference intelligence (patterns, not copied layouts)

Observed public interfaces: [Collecting Cars](https://collectingcars.com/) presents global listings with location/currency, marque browsing, saved items and timed auction status; [Bring a Trailer](https://bringatrailer.com/) emphasizes vehicle-specific histories and listing detail; [Hemmings](https://www.hemmings.com/) positions a broad automotive marketplace with discovery across inventory types.

Translation to Apex: retain single-dealer, fixed-price/negotiated inventory; adopt actionable search and marque/body-style discovery, transparent location and currency display, rich vehicle detail/provenance, save/inquiry account tools, and trustworthy editorial photography. Do not imitate auction countdowns, bidding, user comments, or third-party seller onboarding. Apex's differentiator is curated inspection and concierge service, not marketplace scale.

## 3. Approaches considered

1. **Recommended — dealer commerce, staged deposit:** Apex-only inventory, inquiry-first, and an optional refundable reservation deposit after staff confirmation. Fits high-value vehicle sales and avoids implying the car can be fully purchased with an unverified checkout.
2. **Marketplace:** add third-party sellers, seller KYC, payouts and dispute operations. Excluded from this stage due to materially different legal and payments architecture.
3. **Full direct checkout:** charge entire vehicle price online. Excluded until Apex specifies delivery, tax, cancellation, ownership transfer, consumer-law and provider rules by jurisdiction.

## 4. Experience and information architecture

- **Home:** automotive-specific editorial hero, live featured inventory from the catalog (no fabricated metrics or fictitious press endorsements), search entry point, verified services/provenance and advisor CTA.
- **Inventory:** searchable and filterable stock; make, model, year, price range, body style, mileage, fuel/transmission, location and availability. URL-synchronized filters, sort, pagination, empty/error/loading states, accessible controls, and explicit units.
- **Vehicle detail:** curated gallery; title, asking price and base currency; status; specifications; mileage with km/mi; condition and inspection report; ownership/service history; seller/dealer location; included/excluded details; transport/import caveat; inquiry, save, viewing and reserve actions. Only staff-verified fields appear as facts.
- **Accounts:** secure registration/login and recovery; saved cars; inquiry threads/status; reservation/deposit state and receipts; communication preferences and profile export/deletion. Public browsing remains available.
- **Admin:** role-protected inventory CRUD and publishing, image/provenance moderation, inquiry pipeline, reservation/deposit status, audit history and basic operational summaries. Every state-changing operation records actor/time and validates server-side.
- **Internationalization:** preserve existing i18next/RTL direction; launch with available English and existing locales only where translations are complete. Locale-aware number/currency rendering, km/mi preference, country/region/time zone, accessible RTL layouts. Do not imply FX conversion is a quoted payable amount: show listing currency as authoritative; any converted estimate must disclose its rate/time and be informational.

## 5. Data and API boundaries

Reuse the existing Express/Sequelize/PostgreSQL and React Query/Zustand foundations. Existing `Product`/`Order`/`Payment` schemas are generic shop abstractions; the plan should introduce a migration-backed vehicle inventory model (or a carefully mapped extension) with validated vehicle-specific attributes, immutable price/currency snapshot, listing status, location, inspection/provenance references, and media ordering. Avoid putting arbitrary trusted data in JSON blobs where fields need filtering or audit.

Introduce explicit inquiry and reservation records. A reservation ties one buyer to one vehicle and an immutable deposit amount/currency/terms version, expires or is cancelled under an explicit state machine, and records provider transaction identifiers. Enforce one active reservation per vehicle transactionally. Webhooks are the authoritative payment state transition; browser return URLs never mark payments paid. Use idempotency keys and unique provider event IDs.

Use versioned `/api/v1` endpoints following existing repository conventions: public vehicle list/detail, authenticated saved vehicles and inquiry/reservation operations, and admin-only inventory/lead operations. Validate query/body input, use parameterized ORM filters, enforce ownership and role authorization on every route, and return a consistent success/error envelope. Do not expose payment secrets or raw provider responses.

## 6. Authentication and security

Build on the existing auth implementation rather than adding a new identity provider in this phase. The current app already includes registration/login, refresh-token handling, reset/verification/2FA-related routes and rate limiting; front-end login code currently stores tokens in localStorage and contains non-automotive/incorrect copy. Design calls for short-lived access sessions and refresh tokens only in secure, httpOnly cookies in production; eliminate persistent browser storage of refresh tokens. Configure CORS/CSRF/origin protections, secure cookies, rate limits, password reset/verification, generic credential errors, and role checks. Admin access must be verified server-side and should require 2FA for privileged accounts.

Treat account inquiry and saved-item data as private, scope every query to the authenticated user, apply GDPR consent and deletion/export workflows, and avoid logging credentials or sensitive payment details. Demo accounts remain disabled in production.

## 7. Payment and reservation safety

Apex is the merchant of record for its own vehicles, not a marketplace. Initially, staff confirms availability and deposit terms; then the buyer can pay a fixed deposit amount in the displayed transaction currency. Disclose refund/cancellation deadline, deposit treatment, reservation expiry, and that the deposit is not the full vehicle price. Do not collect card details directly.

Provider integration stays behind the existing payment-provider abstraction. Evaluate Stripe Checkout Sessions and PayPal Checkout for the deposit transaction only, with signed webhook verification, replay/idempotency protection, server-calculated amount/currency, and refund/reconciliation controls. Before enabling live payments, Apex must obtain written provider confirmation for its jurisdiction, merchant category, high-value vehicle reservations, refund terms and supported currencies; assess local consumer, tax, AML/KYC and vehicle-sale obligations. Provider availability/approval is **not verified in this design research**. No provider credentials or account configuration are assumed. If approval is pending, ship inquiry-only and keep reservation checkout disabled.

## 8. Visual direction and content integrity

Premium editorial automotive: restrained dark graphite/ivory foundation with one warm metallic accent from existing theme tokens, generous whitespace, precise typographic hierarchy, wide vehicle photography, discreet borders, minimal motion, mobile-first. Avoid generic SaaS metrics, fake testimonials, unsupported inspection/press claims, stock-car model names presented as owned inventory, and placeholder prices. Reuse existing branding/components where compatible; replace false copy and mock vehicles with catalog-driven content. Respect reduced-motion, keyboard and screen-reader use, contrast, responsive layouts, and consent choices.

## 9. Rollout boundaries

**Phase 1:** correct brand and content, live inventory model/API/admin controls, public search/detail, inquiry flow, responsive/i18n foundations, SEO metadata and structured data only for verified inventory.  
**Phase 2:** buyer accounts, saved vehicles, inquiry history, recovery/security hardening, admin lead workflow.  
**Phase 3:** reservation state machine and provider sandbox/webhook/refund workflows; enable live deposit checkout only after approval and jurisdictional terms are supplied.  

Out of scope: auction/bidding, third-party marketplace sellers, financing origination, automatic tax determination, international shipping quotes, full vehicle-price checkout, unverifiable reviews, and AI-driven pricing.

## 10. Failure handling and observability

Inventory APIs provide useful loading, empty, retry and not-found states. Failed inquiries are retained only after successful server validation and shown with a recoverable confirmation path; prevent duplicate submissions. A provider timeout leaves a reservation pending/unknown until webhook or reconciliation, never silently failed/paid. Record structured audit events for admin and payment lifecycle without card data, tokens or secrets. Alert staff to stale pending deposits and inventory/reservation conflicts.

## 11. Verification criteria for implementation plan

- Public inventory search/filter/sort and detail function with URL state, server validation and real catalog data.
- No fabricated vehicles, endorsements, inspection claims or admin KPI totals.
- Buyer can save a vehicle and submit/view an inquiry; another buyer cannot access it.
- Only authorized staff can create/publish/change listings; every action is audited.
- Reservation prevents concurrent double-booking; amount/currency/terms come from server snapshot.
- In sandbox, duplicate/out-of-order/invalid-signature webhooks cannot duplicate or forge paid state; return URL alone cannot fulfill.
- Checkout is disabled if provider or jurisdiction approval is absent; no full car balance is taken.
- Authentication/session changes, reset, rate-limit and authorization paths have automated tests.
- Responsive and keyboard checks at 375, 768, 1024, 1440 and 1920 widths; reduced-motion and RTL checks; no console/network errors on primary journeys.
- Build, relevant frontend/backend tests, and local browser walkthrough pass before any deployment. Live deployment is not part of this spec.

## 12. Known constraints and open decisions

Research used live public marketplace pages for product-pattern observations. Search integration was unavailable in this BYOK session, and Stripe docs were not successfully validated; no legal or provider eligibility claim is made. Before the implementation plan, confirm Apex's legal operating/merchant country, initial target markets/currencies, actual vehicle data source, deposit/refund policy and approved payment providers. Until supplied, plan only provider-neutral payment interfaces and a disabled sandbox-gated deposit flow; do not invent live terms or credentials.
