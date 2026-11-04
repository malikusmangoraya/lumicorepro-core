# LumicorePro — Project Inventory

**Generated:** 2026-10-29 | **Source of truth:** live filesystem scan of both worktrees
**Manifest:** `delivery/DELIVERY_MANIFEST.md` (95 rows) | **Scanner:** `scripts/inventory_projects.py`

## Summary

| Category | Count | What it really is |
|---|---|---|
| Manifest projects with real source (full stack) | 8 | frontend + backend + tests, in `products/sell-today/` |
| Manifest projects, frontend only | 1 | `orbitboard` — static Supabase app |
| Manifest projects, **build output only** | 86 | only `delivery/<slug>/dist/`; **no source anywhere** |
| Manifest projects missing entirely | 0 | — |
| Manifest rows failing its own brand rule | 26 | `blue-free: no` and/or `logo: missing` |
| Full-stack products **not** in the manifest | 3 | `apex`, `claimflow-ai`, `flowpilot` |
| Factory build snapshots (`generated-projects/build-*`) | 24 | repeated demo runs, full stack |
| Template categories | 21 | `src/templates/`; registry lists 100 template entries |

### Manifest claims that are false

| Claim | Reality |
|---|---|
| `zips present: 95` / `zips valid: 95` | **0 zip files exist** under `delivery/` |
| `blue-free: 69` | 26 products use a blue-family colour |
| `logos unique: 69/95` | 26 have no `logo.svg` at all |

## Full-stack projects with real source (8 manifest + 3 extra sell-today)

| slug | industry | frontend | backend | tests | where |
|---|---|---|---|---|---|
| aurelia-estates | real-estate | 166 | 152 | 4 | premium/products |
| aurum-fitness | sports | 163 | 152 | 4 | premium/products |
| meridian-capital | fintech | 163 | 152 | 4 | premium/products |
| nuage-events | entertainment | 164 | 152 | 4 | premium/products |
| prestige-studio | portfolio | 163 | 152 | 4 | premium/products |
| resupro | saas | 145 | 152 | 4 | premium/products |
| saffron-voyage | hospitality | 164 | 152 | 4 | premium/products |
| studio-lumen | portfolio | 163 | 152 | 4 | premium/products |
| apex |  | 177 | 165 | 9 | premium/products/sell-today |
| claimflow-ai |  | 163 | 157 | 4 | premium/products/sell-today |
| flowpilot |  | 163 | 157 | 5 | premium/products/sell-today |

## Frontend-only (1)

| slug | brand | industry | frontend | where |
|---|---|---|---|---|
| orbitboard | Orbitboard | saas | 24 | premium/delivery |

## Build output only — no source anywhere (86)

These ship a working `dist/` and a live URL, but the source tree was never kept. They cannot be rebuilt, fixed or resold as source.

| slug | brand | industry | blue_free | logo | live |
|---|---|---|---|---|---|
| adjusterly | Adjusterly | fintech | no | missing | HTTP 200 |
| apex-commerce | Apex Commerce | ecommerce | no | missing | HTTP 200 |
| apex-digital | Apex Digital | saas | no | missing | HTTP 200 |
| appointly | Appointly | healthcare | yes | unique | HTTP 200 |
| atlas-mobility | Atlas Mobility | saas | yes | unique | HTTP 200 |
| aurora-cloud | Aurora Cloud | saas | yes | unique | HTTP 200 |
| beacon-dental | Beacon Dental | healthcare | yes | unique | HTTP 200 |
| bellweather | Bellweather | fintech | no | missing | HTTP 200 |
| blume-botanics | Blume Botanics | ecommerce | yes | unique | HTTP 200 |
| brass-basil | Brass & Basil | food | yes | unique | HTTP 200 |
| bristle-co | Bristle & Co | ecommerce | yes | unique | HTTP 200 |
| capstone-advisors | Capstone Advisors | saas | yes | unique | HTTP 200 |
| cartwheel | Cartwheel | ecommerce | no | missing | HTTP 200 |
| cascade-hq | Cascade HQ | saas | yes | unique | HTTP 200 |
| cinder-steel | Cinder & Steel | food | yes | unique | HTTP 200 |
| cirrus-travel | Cirrus Travel | hospitality | yes | unique | HTTP 200 |
| claimflow | ClaimFlow | saas | yes | unique | HTTP 200 |
| clausecheck | ClauseCheck | saas | yes | unique | HTTP 200 |
| clover-dental | Clover Dental | healthcare | yes | unique | HTTP 200 |
| copperline | Copperline | industrial | no | missing | HTTP 200 |
| create-studio | Create Studio | saas | no | missing | HTTP 200 |
| deckflow | Deckflow | saas | yes | unique | HTTP 200 |
| deploydock | DeployDock | saas | yes | unique | HTTP 200 |
| ember-salt | Ember & Salt | food | yes | unique | HTTP 200 |
| fitly-academy | Fitly Academy | education | yes | unique | HTTP 200 |
| fleetwood-events | Fleetwood Events | entertainment | yes | unique | HTTP 200 |
| forgekit | Forgekit | saas | yes | unique | HTTP 200 |
| foxglove-care | Foxglove Care | healthcare | no | missing | HTTP 200 |
| groundswell | Groundswell | sports | no | missing | HTTP 200 |
| halo-retail | Halo Retail | ecommerce | yes | unique | HTTP 200 |
| harbor-insurance | Harbor Insurance | fintech | yes | unique | HTTP 200 |
| harborline | Harborline | logistics | no | missing | HTTP 200 |
| heritage-trails | Heritage Trails | entertainment | yes | unique | HTTP 200 |
| insightpipe | InsightPipe | saas | yes | unique | HTTP 200 |
| ironwood-realty | Ironwood Realty | real-estate | no | missing | HTTP 200 |
| juniper-goods | Juniper Goods | ecommerce | yes | unique | HTTP 200 |
| kestrel-fleet | Kestrel Fleet | logistics | no | missing | HTTP 200 |
| kinetiq-health | Kinetiq Health | healthcare | yes | unique | HTTP 200 |
| launchbay | Launchbay | saas | yes | unique | HTTP 200 |
| leadscout-ai | LeadScout AI | real-estate | yes | unique | HTTP 200 |
| ledgerai | LedgerAI | fintech | yes | unique | HTTP 200 |
| ledgerline | Ledgerline | saas | yes | unique | HTTP 200 |
| ledgerpoint | Ledgerpoint | fintech | no | missing | HTTP 200 |
| linguagrid | LinguaGrid | saas | yes | unique | HTTP 200 |
| lumen-studio | Lumen Studio | portfolio | no | missing | HTTP 200 |
| lumina-academy | Lumina Academy | education | yes | unique | HTTP 200 |
| luxemart | Luxemart | ecommerce | yes | unique | HTTP 200 |
| maison-noir | Maison Noir | fashion | yes | unique | HTTP 200 |
| marble-run-hotels | Marble Run Hotels | hospitality | yes | unique | HTTP 200 |
| marlow-fitness | Marlow Fitness | healthcare | no | missing | HTTP 200 |
| metrica-pulse | Metrica Pulse | saas | yes | unique | HTTP 200 |
| mirage-beauty | Mirage Beauty | fashion | yes | unique | HTTP 200 |
| noir-frames | Noir Frames | portfolio | yes | unique | HTTP 200 |
| noora-khan | Noora Khan | portfolio | yes | unique | HTTP 200 |
| northbeam | Northbeam | saas | no | missing | HTTP 200 |
| northpeak-outfitters | Northpeak Outfitters | ecommerce | yes | unique | HTTP 200 |
| nova-forge | Nova Forge | saas | yes | unique | HTTP 200 |
| onboarder | Onboarder | saas | yes | unique | HTTP 200 |
| orbit-studios | Orbit Studios | portfolio | yes | unique | HTTP 200 |
| orchard-grid | Orchard Grid | saas | no | missing | HTTP 200 |
| petrichor | Petrichor | hospitality | no | missing | HTTP 200 |
| pinnacle-events | Pinnacle Events | entertainment | no | missing | HTTP 200 |
| pinnacle-fitness | Pinnacle Fitness | sports | yes | unique | HTTP 200 |
| pulselabs | PulseLabs | healthcare | yes | unique | HTTP 200 |
| quarry-learning | Quarry Learning | education | no | missing | HTTP 200 |
| recruitiq | RecruitIQ | saas | yes | unique | HTTP 200 |
| roark-analytics | Roark Analytics | saas | yes | unique | HTTP 200 |
| sable-fit | Sable Fit | fashion | no | missing | HTTP 200 |
| sheetstack | Sheetstack | saas | yes | unique | HTTP 200 |
| signalbase | Signalbase | saas | no | missing | HTTP 200 |
| solstice-energy | Solstice Energy | industrial | no | missing | HTTP 200 |
| stacksail | Stacksail | saas | yes | unique | HTTP 200 |
| stonemark-realty | Stonemark Realty | real-estate | yes | unique | HTTP 200 |
| sundial-media | Sundial Media | entertainment | no | missing | HTTP 200 |
| supportdesk-ai | SupportDesk AI | ecommerce | yes | unique | HTTP 200 |
| tablehost-ai | TableHost AI | food | yes | unique | HTTP 200 |
| ternion-instruments | Ternion Instruments | electronics | yes | unique | HTTP 200 |
| terravista | TerraVista | real-estate | yes | unique | HTTP 200 |
| tidewater-travel | Tidewater Travel | hospitality | no | missing | HTTP 200 |
| vantage-3d-estates | Vantage 3D Estates | real-estate | yes | unique | HTTP 200 |
| vantage-hr | Vantage HR | saas | no | missing | HTTP 200 |
| vaultline | Vaultline | fintech | yes | unique | HTTP 200 |
| veridian-e-catalog | Veridian E-Catalog | electronics | yes | unique | HTTP 200 |
| vine-vale | Vine & Vale | food | yes | unique | HTTP 200 |
| voltus-atelier | Voltus Atelier | electronics | yes | unique | HTTP 200 |
| zephyr-way | Zephyr Way | hospitality | yes | unique | HTTP 200 |

## Factory build snapshots (24)

Repeated runs of the generator; each is a full stack. Working directories, not products.

| slug | frontend | backend | tests | where |
|---|---|---|---|---|
| build | 72 | 173 | 5 | premium/generated-projects |
| build-002 | 137 | 173 | 5 | premium/generated-projects |
| build-003 | 137 | 173 | 5 | premium/generated-projects |
| build-004 | 137 | 173 | 5 | premium/generated-projects |
| build-005 | 137 | 170 | 5 | original/generated-projects |
| build-006 | 137 | 170 | 5 | original/generated-projects |
| build-007 | 137 | 170 | 5 | original/generated-projects |
| build-008 | 137 | 173 | 5 | original/generated-projects |
| build-009 | 137 | 173 | 5 | original/generated-projects |
| build-010 | 137 | 175 | 5 | original/generated-projects |
| build-011 | 137 | 172 | 5 | original/generated-projects |
| build-012 | 137 | 172 | 5 | original/generated-projects |
| build-013 | 137 | 170 | 5 | original/generated-projects |
| build-014 | 137 | 170 | 5 | original/generated-projects |
| build-015 | 137 | 170 | 5 | original/generated-projects |
| build-016 | 137 | 170 | 5 | original/generated-projects |
| build-017 | 137 | 170 | 5 | original/generated-projects |
| build-018 | 137 | 170 | 5 | original/generated-projects |
| build-019 | 137 | 170 | 5 | original/generated-projects |
| build-020 | 137 | 170 | 5 | original/generated-projects |
| build-021 | 125 | 164 | 4 | original/generated-projects |
| build-022 | 137 | 170 | 5 | original/generated-projects |
| build-023 | 137 | 171 | 5 | original/generated-projects |
| build-024 | 137 | 171 | 5 | original/generated-projects |

## Other generated demos (8)

| slug | status | frontend | backend | tests | where |
|---|---|---|---|---|---|
| blogforge | FULL_STACK | 31 | 20 | 7 | premium/generated-projects |
| premium-layout-emitter | FULL_STACK | 17 | 23 | 1 | premium/generated-projects |
| premium-verification | FRONTEND_ONLY | 240 | 0 | 26 | premium/generated-projects |
| scene-runtime | FRONTEND_ONLY | 7 | 0 | 0 | premium/generated-projects |
| cortexdesk | FULL_STACK | 16 | 20 | 1 | original/generated-projects |
| factory-smoke | FULL_STACK | 16 | 19 | 1 | original/generated-projects |
| products | EMPTY | 0 | 0 | 0 | original/generated-projects |
| shipsignal | FULL_STACK | 16 | 20 | 1 | original/generated-projects |

## Templates (not projects)

`src/templates/` holds 21 categories: _shared, agency, ai, automotive, business, creative, dashboard, ecommerce, education, fitness, gym, healthcare, insurance, marketplace, newsletter, podcast, portfolio, realestate, restaurant, travel, wedding.

`registry/templates.json` lists **100** template entries (id, category, industry, tags) that the generator selects from. A template is a starting point, not a generated product.

## Missing

- **0** manifest slugs are missing as a directory.
- **86** are missing their **source** — the directory holds only `dist/`.
- Only the 11 products in `products/sell-today/` have a committed, buildable package that CI verifies.

