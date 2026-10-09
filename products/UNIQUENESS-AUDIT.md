# LumicorePro — 11 Products: Uniqueness, Brand Identity, Completeness & Realness

Date: 2026-10-09 · Re-checked: 2026-10-10 (`node products/_audit/verify-all.cjs`, exit 0)
Scope: `products/{apex, aurelia-estates, aurum-fitness, claimflow-ai, flowpilot,
meridian-capital, nuage-events, prestige-studio, resupro, saffron-voyage, studio-lumen}`

Every number below comes from a script in `products/_audit/` reading the files on disk.
Re-run them at any time:

```bash
node products/_audit/verify-all.cjs        # all claims, 7 check groups — exits 0 on green
node products/_audit/check-shells.mjs      # compiles the touched files with each product's own Vite
node products/_audit/resolve-imports.cjs   # UNRESOLVED_IMPORT, statically
node products/_audit/lucide-imports.cjs    # every lucide-react named import exists
node products/_audit/custom-classes.cjs    # no component class is orphaned by the stylesheet
```

---

## 1. Headline

Each product was already a complete full-stack app (174–177 source files, its own Express
backend, 14 locales, PWA, docker-compose, LICENSE, README, per-niche page set). What was **not**
unique was the design system those pages rendered, and — more seriously — **none of the eleven
products could build**.

| Dimension | Before | After | Current check |
|---|---|---|---|
| Products that build | **0/11** | **11/11** | full sweep last 11/11; 3/3 re-checked `apex/claimflow-ai/resupro exit=0` |
| Brand colour agrees across BRAND.js / design-tokens.json / index.css / tailwind.config.js | **0/11** | **11/11** | `verify-all` group 3 |
| Distinct rendered identities (`--t-primary` + `--t-canvas`) | 10/11 (apex == flowpilot) | **11/11** | `verify-all` group 2 |
| Unique vector logo (`BrandMark.jsx`) | 11/11 | 11/11 | unchanged |
| Unique 404 page (brand-aware, i18n-aware) | 0/11 | 11/11 | not identical across products |
| Unique alternative layout shells + hero | **0/11** | **11/11** | one of 6 navs + 8 hero comps; verified `verify-all` group 6 |
| Real payment front end (no mock, no card data) | **0/11** | **11/11** | `paymentProvider` calls the app's own endpoints; `verify-all` group 7 |
| 404 route + page | **0/11** | **11/11** | brand-aware, i18n-aware; `verify-all` group 7; page not byte-identical across products |
| Cookie consent actually mounted | **0/11** (shipped, never imported) | **11/11** | rendered in every router; `verify-all` group 7 |
| Per-brand service-worker cache | 11/11 | 11/11 | unchanged |

---

## 2. The design system contradicted itself (11/11)

Three colour definitions shipped in every product, and they disagreed:

1. `frontend/design-tokens.json` — the generated brand palette
2. `frontend/src/components/brand/BRAND.js` — the logo/mark palette
3. `frontend/src/index.css` `:root` — `--t-primary`, `--t-canvas`…, **the one that renders**

`tailwind.config.js` carried a fourth value for the older theme generation. Measured before the
fix:

```
product            | dt.primary | brand     | css       | verdict
-------------------|------------|-----------|-----------|----------------------
apex               | #00e5ff    | #00e5ff   | #7c3aed   | logo cyan, UI purple
aurelia-estates    | #38bdf8    | #a855f7   | #be2c2c   | three colours
aurum-fitness      | #06b6d4    | #ec4899   | #be882c   | three colours
claimflow-ai       | #dc2626    | #dc2626   | #374151   | mark red, UI slate
flowpilot          | #10b981    | #10b981   | #7c3aed   | mark emerald, UI purple
meridian-capital   | #38bdf8    | #38bdf8   | #be2c92   | mark sky, UI magenta
nuage-events       | #111827    | #0ea5e9   | #be2c4e   | three colours
prestige-studio    | #dc2626    | #2563eb   | #be502c   | three colours
resupro            | #dc2626    | #b91c1c   | #be2c44   | three colours
saffron-voyage     | #111827    | #111827   | #be702c   | mark black, UI amber
studio-lumen       | #06b6d4    | #06b6d4   | #ea580c   | mark cyan, UI orange
```

`index.css` also hard-coded hex inside its class layers (`.btn-primary`, `.section-eyebrow`,
`.section-heading`, `.hero-aurora`), so even a corrected `:root` would not have restyled the page.
**apex and flowpilot rendered byte-identical identities** (`#7c3aed` on `#f7f3ea`) despite being
different products.

### What changed

- One canonical palette per product, written to all four sources plus `public/favicon.svg`.
- **apex** returns to its own cyan/violet brand; **flowpilot** to its emerald/indigo brand — the
  two identical products are now different. The other nine keep the palette that was already
  rendering, so no product was re-skinned arbitrarily.
- Class-layer hex replaced with `var(--t-*)` reads; `tailwind.config.js` defaults and ramps
  synced; `design-tokens.json` gained a `rendered_theme` block recording what is actually applied.
- Because the de-hardcode pass half-succeeded and then damaged nine stylesheets mid-session, all
  eleven `index.css` files were **rebuilt from one validated template** (buttons, section
  typography, `card-panel`, `card-lift`, `lumi-motion`, `hero-video`, `skip-link`, reduced-motion,
  scrollbars) parameterised per product by palette, fonts and the product's own extra `--t-*` tokens
  (16–18 of them, preserved). Verified: 11/11 parse with exactly one `:root` and 11/11 distinct
  identities.

---

## 3. Layout and hero were the template's boilerplate

Byte-identical files across products (`dup` check):

```
layouts/LandingLayout.jsx   identical in 3, then identical in 7   → 0 unique
layouts/AppLayout.jsx       identical in 3, then identical in 7   → 0 unique
components/business/Hero.jsx identical in 10                      → 1 unique
components/brand/BrandLockup.jsx, LayoutSkeleton.jsx, LazyLayouts.jsx, paymentProvider.js  → 11 identical
CookieConsent.jsx           identical in 3 + 6
sw-register.js              identical in 10
assets/images/hero-desk.jpg identical in 4 products; hero.jpg in 3
```

The shells were not merely similar, they were brand-blind: `LandingLayout` hard-coded the wordmark
**`PlatformPro`** on `slate-950`/`cyan-400`, `AppLayout` hard-coded **`ConsoleAdmin`**, and neither
imported `BRAND`, the design tokens or i18n. A luxury real-estate listing site and a photography
studio shipped the same dark SaaS shell.

`components/business/Hero.jsx` also imported `{ cn, img }` from `../../utils` — and `utils.js` has
never exported `img`. It was dead code (0 importers in all 11), so nobody noticed the latent build
failure waiting for whoever wired it up.

### What changed

`LandingLayout`, `AppLayout` and `business/Hero` are now brand-true: `BRAND` + `--t-*` tokens +
`useTranslation` + `BrandLockup`, one of **6 distinct header arrangements** and **8 distinct hero
compositions** per product, chosen by niche (a luxury brokerage gets a centred hairline nav and a
cinematic search hero; a fitness brand gets a bold colour band and a stat band; a studio gets an
indexed nav and an editorial hero). Zero `PlatformPro`/`ConsoleAdmin`, zero `slate-950`. The hero's
artwork is now a real shipped asset per product, imported so the bundler fingerprints it.

Shared *infrastructure* is deliberately still one implementation — `paymentProvider.js`,
`LayoutSkeleton.jsx`, `sw-register.js`, `BrandLockup.jsx`, `CookieConsent.jsx` — because eleven
copies of one API client or one service-worker registration is a maintenance problem, not
uniqueness. They render differently per product through `BRAND` and the tokens. `verify-all.cjs`
asserts design surfaces differ and prints the shared list as `INFO`.

---

## 4. Nothing built (this was the biggest finding)

A real `npm run build` in the first product stopped at once. Across the eleven:

| Build breaker | Products | Files |
|---|---|---|
| `lucide-react` no longer exports `Spinner`, `Chrome`, `Github`, `Facebook`, `Linkedin`, `Twitter` | 11 | 42 |
| `claimflow-ai/pages/Register.jsx` declared `Navbar`/`Footer` twice | 1 | 1 |
| `resupro` was missing `services/api.js` and `services/apiConfig.js` (imported by Login/Register) | 1 | 2 |
| `apex/App.jsx` routed `/projects` to `<Projects />` with no import and no page | 1 | 1 |

The brand marks were removed from lucide entirely, so each maps to the closest available glyph
(`Chrome → Globe`, `Github → Code2`, `Facebook → Users`, `Linkedin → Briefcase`,
`Twitter → AtSign`, `Spinner → LoaderCircle`) — the button's visible label still names the brand.

**Result: `npm run build` passes in 11/11 products**, exit 0 with the SPA fallback written.
The three products that needed bespoke per-product repairs were re-built clean on 2026-10-09:
`apex exit=0`, `claimflow-ai exit=0`, `resupro exit=0`.

---

## 5. Payment: real engine, mock front door

**Backend — genuinely real (11/11).** `payment.routes.js`: Stripe PaymentIntents, Checkout
Sessions, Billing Portal, signature-verified idempotent webhooks; PayPal create/capture/refund;
Paddle merchant-of-record; refunds and HTML invoices. `lemonsqueezy.routes.js`: HMAC-SHA256
verification, an idempotency ledger (`WebhookEvent`), `Payment`/`Order` rows, a payment rate limiter.
Gateways are gated by `PAYMENT_GATEWAYS_ENABLED`; secrets live only in `.env` and `.env.example`
documents every key.

**Frontend — was not.** `lib/paymentProvider.js` was literally
`class MockPaymentProvider { … id: 'mock-checkout-session' }` and nothing imported it, while
`CheckoutFlow.jsx` collected **raw card number, expiry and CVC in the browser** and POSTed them to
`/api/orders`. That is not an integration and it is a PCI-DSS violation.

**What changed:** `paymentProvider.js` is now a real gateway client over the endpoints this app
already ships — `GET /api/payment/config`, `POST /api/payment/checkout`,
`GET /api/lemonsqueezy/config`, `POST /api/lemonsqueezy/checkout`, `POST /api/payment/portal` —
with `PaymentNotConfiguredError` surfaced from the backend's own `configured: false` answer.
`CheckoutFlow` collects contact details only, reads the live gateway list, and hands the buyer to
the gateway's hosted page. No card data reaches this codebase.

**Honest limitation:** no gateway keys exist in this repo, so no live charge was made. A request
against an unconfigured deployment correctly answers `503` / `configured: false`, and the UI now
says so instead of opening a demo dialog.

---

## 6. Cache, cookies, completeness

Already correct and left alone: `public/sw.js` per product with its own cache version
(`v1-apex` … `v1-studio-lumen`), network-first navigations, cache-first hashed assets, the API never
cached, base-relative for sub-path hosting; `sw-cache-strategy.js`; per-product cookie config
(`apex_consent` … `studiolumen_consent`, region SA/MENA, opt-in model); Redis with in-memory fallback
on the server.

Fixed:

- **404: was 0/11.** Every `App.jsx` routed `path="*"` to `<Home />`, so a mistyped URL silently
  rendered the homepage and answered 200. Each product now ships a brand-aware, i18n-aware
  `pages/NotFound.jsx` with links into that product's own signature page (Listings, Programs, Claims,
  Portfolio, Events, Work, Templates, Itineraries, Galleries).
- **Cookie consent: was mounted nowhere.** `CookieConsent.jsx` existed in all eleven with zero
  importers. It is now rendered inside every router, so consent is actually requested.
- Dangling routes removed, and `verify-all.cjs` asserts every route element resolves to a lazy import.

Per product, 18 files under `src/` were created or rewritten (plus `tailwind.config.js`,
`design-tokens.json` and `public/favicon.svg` where the palette changed).

---

## 7. Verification (what was actually run)

| Check | Command | Result |
|---|---|---|
| Consolidated claims | `node products/_audit/verify-all.cjs` | **7/7 groups pass; exit 0** |
| Specific build rechecks (2026-10-09) | `npm run build` in apex, claimflow-ai, resupro | **3/3, exit 0** |
| Production build (full sweep) | `npm run build` in all 11 products | **11/11, exit 0** |
| Touched files compile (incl. files outside the build graph) | `node products/_audit/check-shells.mjs` | **11/11, 130 file compilations** |
| Local imports resolve | `resolve-imports.cjs` | 0 unresolved |
| lucide imports exist | `lucide-imports.cjs` | 0 missing |
| Stylesheets | postcss parse, 1 `:root` each | 11/11 |
| Component classes not orphaned | `custom-classes.cjs` | `glass-panel` (was undefined, now removed from use) |

---

## 8. Remaining, not done

- **Five thinner homepages.** apex, claimflow-ai, flowpilot, resupro (and one more) ship a ~260-line
  home composed from the shared `GrowthSections`, against ~600-line bespoke homes elsewhere. The
  content and section order still differ per product, but these five are visibly simpler. Not
  rewritten — it is design authoring, not a defect.
- **Shared stock photography.** `hero-desk.jpg` is still the same file in 4 products and `hero.jpg` in 3.
  Replacing them needs licensed niche imagery per brand.
- **Cookie banner copy is English-only** although 14 locales ship. Consent keys and regions are
  per-product; the banner strings are not localised yet.
- **No live payment was transacted** (no gateway credentials in this repo) and no database was migrated
  or seeded; the backend is unchanged by this work.
- **`resupro` gained `components/business/Hero.jsx`**, which its pre-scrub revision never had, so
  the family's primitive set is consistent. It has no importers in any product.
- `products/<product>/frontend/dist/` and `node_modules/` now exist locally from the verification builds.
  `products/*` is untracked in git — nothing here was committed.
- The report itself was re-verified on 2026-10-09; no source files were changed by that re-verification.

---

## 9. Scripts in `products/_audit/`

| File | What it checks | Run |
|---|---|---|
| `verify-all.cjs` | groups 1–7: stylesheets, unique identities, one colour source, import resolution, lucide exports, distinct shells, completeness | `node products/_audit/verify-all.cjs` |
| `check-shells.mjs` | compiles every rewrite/creation with each product's own Vite | `node products/_audit/check-shells.mjs` |
| `resolve-imports.cjs` | static equivalent of the bundler's UNRESOLVED_IMPORT | `node products/_audit/resolve-imports.cjs` |
| `lucide-imports.cjs` | every named lucide import resolves; `--fix` renames the known aliases | `node products/_audit/lucide-imports.cjs [--fix]` |
| `custom-classes.cjs` | no component class is left undefined by index.css | `node products/_audit/custom-classes.cjs` |
| `brand-shells.cjs`, `fix-literals.cjs` | repair scripts already run; kept for traceability | not for re-run |

No other audit script exists in this workspace (`ui-audits.cjs` and `check-ui-audits.cjs` were never
created). If a script is gone from the list above it was not written; do not assume an audit path it
might have described.
