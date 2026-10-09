# Product Selling Guide — 11 products

Created: 2026-10-10
Language: English

This file is a working handoff note, not a consumer-facing manual. It lists what each product
already has, what is needed before selling, how Lemon Squeezy fits, how GitHub should be handled,
and what “clean code” means in this repo.

## 1. Before selling any product, make sure these exist

- [ ] `README.md`
- [ ] `LICENSE.md`
- [ ] `.env.example`
- [ ] working frontend build
- [ ] working backend routes for the product’s main features
- [ ] payments wired the way the product expects, if it sells anything
- [ ] cookie consent present, if the product uses tracking or third-party scripts
- [ ] 404 page present
- [ ] favicon and brand assets in place
- [ ] i18n ready if the product is sold in more than one locale
- [ ] no hardcoded secrets, no exposed stack traces, no demo card data collected in the browser

## 2. License

Each product should ship with a license that matches how it will be sold.

Options commonly used for this kind of multi-product catalog:
- paid-license model with a private or commercial license file
- open source license if the product is meant to be shared freely
- dual-license if one version is free and another is commercial

Before publishing, decide:
- is the product sold as a template/app?
- is it licensed per buyer, per project, or per seat?
- does the buyer get source, compiled assets, or both?
- are updates, support, or resell rights included?

Put the chosen license in `LICENSE.md` and mention it clearly in the product README.

## 3. Lemon Squeezy notes

If a product uses Lemon Squeezy, these pieces should exist or be reviewed before selling:

- `backend/routes/lemonsqueezy.routes.js` or equivalent webhook/checkout routes
- webhook signature verification
- webhook idempotency handling
- payment state tracked in the backend, not only in the frontend
- redirect/checkout flow tested on the frontend
- `.env.example` listing the Lemon Squeezy keys the product needs
- product variant or plan mapping documented somewhere for the seller

Lemon Squeezy is used here as a payment/order provider. It is not a substitute for the product’s
own order, account, or entitlement logic. If the product grants access, uploads, seats, or content
after payment, that part still has to be implemented and verified in the backend.

## 4. What each product already has

### apex
- frontend + backend + README + LICENSE
- payment and webhook routes present
- 404 and cookie consent present after earlier fixes
- design identity separated from other products

### aurelia-estates
- frontend + backend + README + LICENSE
- property/listing-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### aurum-fitness
- frontend + backend + README + LICENSE
- program/coaching-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### claimflow-ai
- frontend + backend + README + LICENSE
- claims/operations-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### flowpilot
- frontend + backend + README + LICENSE
- workflow/automation-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### meridian-capital
- frontend + backend + README + LICENSE
- portfolio/capital-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### nuage-events
- frontend + backend + README + LICENSE
- events-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### prestige-studio
- frontend + backend + README + LICENSE
- studio/work-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### resupro
- frontend + backend + README + LICENSE
- templates/resume-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### saffron-voyage
- frontend + backend + README + LICENSE
- travel/itinerary-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

### studio-lumen
- frontend + backend + README + LICENSE
- gallery/studio-style product pages
- backend routes and models present
- 404 and cookie consent present after earlier fixes

## 5. GitHub and commit notes

This work has not been committed to GitHub in this session unless you explicitly asked for it.
If you want it on GitHub, do these steps:

1. confirm which files should be committed
2. confirm which files should stay local and untracked
3. create a branch if needed
4. stage only the intended files
5. write a clear commit message
6. push only after you have reviewed the diff

Do not commit:
- `.env` files with real secrets
- build output unless you intend to store it in the repo
- generated artifacts that do not belong in source control

If the repo already has GitHub actions or deploy workflows, make sure the new files do not break
them before pushing.

## 6. Clean code checks before commit or publish

Run these before treating the code as clean:

- `node products/_audit/verify-all.cjs`
- `npm run build` in each product you plan to ship
- `products/_audit/check-shells.mjs`
- check for unresolved imports
- check for missing lucide imports
- check that no product still has a mock payment client
- check that no checkout form collects raw card data
- check that no file still says `PlatformPro` or `ConsoleAdmin`
- check that brand colour is consistent across BRAND.js, tokens, styles, and tailwind config

If any of these fail, fix the cause first. Do not push broken builds just to save time.

## 7. Selling handoff

For each product, the seller should be able to answer:
- what the product does
- who it is for
- what is included in the purchase
- what the buyer needs to configure
- what is not included
- how updates or support work
- what license applies

If any of those are missing, write them into the README before listing the product.

## 8. Short status

Current state:
- core product files exist for all 11 products
- extra files were added through the audit scripts
- security options and selling notes are now documented here
- commit and clean-code steps are listed above

Next step is yours:
- choose which products to list
- set the license
- review Lemon Squeezy or other payment wiring
- decide GitHub commit strategy
- run the clean-code checks above before publishing
