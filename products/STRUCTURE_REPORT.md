# Structure & Work Report — 11 products

Generated from the working tree plus a real `vite build` of every product.

**Every bundle figure is gzip transfer size, measured on 2026-10-06 by
`scripts/measure_product_bundles.py`, which installs and builds each product
and reads `dist/index.html` for exactly what a browser fetches first.**

- *1st-paint JS* — module entry + every `modulepreload` the HTML lists
- *Largest chunk* — the biggest single JS chunk, so it is the same unit as above
- *CSS* — stylesheets the browser blocks on

Budgets (AGENTS.md §7): initial JS target < 150 KB gzip, hard < 200 KB ·
largest chunk hard < 300 KB · CSS target < 30 KB gzip.

## Summary

| # | Product | Niche | Pages | API routes | Models | Components | Locales | Docs | ZIP | 1st-paint JS | Largest chunk | CSS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [apex](apex/) | precision commerce / SaaS | 12 | 33 | 27 | 94 | 14 | 42 | 1731 KB | 106.3 KB | 63.6 KB | 11.1 KB |
| 2 | [aurelia-estates](aurelia-estates/) | luxury real estate | 13 | 33 | 27 | 95 | 14 | 43 | 1379 KB | 109.5 KB | 63.6 KB | 10.9 KB |
| 3 | [aurum-fitness](aurum-fitness/) | fitness coaching | 13 | 33 | 27 | 92 | 14 | 43 | 1342 KB | 106.5 KB | 63.6 KB | 10.9 KB |
| 4 | [claimflow-ai](claimflow-ai/) | insurance claims | 12 | 34 | 27 | 93 | 14 | 42 | 1384 KB | 106.1 KB | 63.6 KB | 10.6 KB |
| 5 | [flowpilot](flowpilot/) | SaaS (projects + billing + insight) | 12 | 33 | 27 | 93 | 14 | 42 | 1485 KB | 106.3 KB | 63.6 KB | 10.7 KB |
| 6 | [meridian-capital](meridian-capital/) | fintech / portfolio intelligence | 13 | 33 | 27 | 92 | 14 | 43 | 1457 KB | 106.0 KB | 63.6 KB | 10.8 KB |
| 7 | [nuage-events](nuage-events/) | events & ticketing | 13 | 33 | 27 | 93 | 14 | 43 | 2024 KB | 106.0 KB | 63.6 KB | 11.1 KB |
| 8 | [prestige-studio](prestige-studio/) | creative studio / portfolio | 13 | 33 | 27 | 92 | 14 | 43 | 1260 KB | 106.0 KB | 63.6 KB | 10.8 KB |
| 9 | [resupro](resupro/) | career / résumé SaaS | 13 | 33 | 27 | 69 | 14 | 38 | 2721 KB | 105.8 KB | 63.6 KB | 10.4 KB |
| 10 | [saffron-voyage](saffron-voyage/) | curated travel | 13 | 33 | 27 | 93 | 14 | 43 | 1953 KB | 106.0 KB | 63.6 KB | 11.2 KB |
| 11 | [studio-lumen](studio-lumen/) | photography / portfolio | 13 | 33 | 27 | 92 | 14 | 43 | 1500 KB | 106.0 KB | 63.6 KB | 10.7 KB |

All 11 products were built successfully. Worst case: first paint **109.5 KB** gzip (target 150, hard 200), largest chunk **63.6 KB** gzip (hard 300), CSS **11.2 KB** gzip (target 30).

## Per product

### apex

- **Live:** https://malikusmangoraya.github.io/apex-digital
- **Source:** https://github.com/malikusmangoraya/apex-digital
- **Niche:** precision commerce / SaaS
- **Pages (12):** About, Account, Admin, Contact, Home, Insights, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 94
- **Locales:** 14
- **Docs:** 42 markdown files
- **Media:** hero-poster.jpg (36 KB), hero.mp4 (340 KB)
- **Build:** 33 JS chunks · first-paint JS 106.3 KB gzip · largest chunk 63.6 KB gzip · CSS 11.1 KB gzip · built in 8.3s
- **Sale archive:** 1731 KB

### aurelia-estates

- **Live:** https://malikusmangoraya.github.io/aurelia-estates
- **Source:** https://github.com/malikusmangoraya/aurelia-estates
- **Niche:** luxury real estate
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Listings, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 95
- **Locales:** 14
- **Docs:** 43 markdown files
- **Build:** 34 JS chunks · first-paint JS 109.5 KB gzip · largest chunk 63.6 KB gzip · CSS 10.9 KB gzip · built in 8.3s
- **Sale archive:** 1379 KB

### aurum-fitness

- **Live:** https://malikusmangoraya.github.io/aurum-fitness
- **Source:** https://github.com/malikusmangoraya/aurum-fitness
- **Niche:** fitness coaching
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Login, Pricing, Privacy, Programs, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 92
- **Locales:** 14
- **Docs:** 43 markdown files
- **Build:** 34 JS chunks · first-paint JS 106.5 KB gzip · largest chunk 63.6 KB gzip · CSS 10.9 KB gzip · built in 8.9s
- **Sale archive:** 1342 KB

### claimflow-ai

- **Live:** https://malikusmangoraya.github.io/claimflow
- **Source:** https://github.com/malikusmangoraya/claimflow
- **Niche:** insurance claims
- **Pages (12):** About, Account, Admin, Claims, Contact, Home, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (34)**
- **DB models (27)**
- **Frontend components:** 93
- **Locales:** 14
- **Docs:** 42 markdown files
- **Build:** 34 JS chunks · first-paint JS 106.1 KB gzip · largest chunk 63.6 KB gzip · CSS 10.6 KB gzip · built in 9.0s
- **Sale archive:** 1384 KB

### flowpilot

- **Live:** https://malikusmangoraya.github.io/flowpilot
- **Source:** https://github.com/malikusmangoraya/flowpilot
- **Niche:** SaaS (projects + billing + insight)
- **Pages (12):** About, Account, Admin, Contact, Home, Login, Pricing, Privacy, Projects, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 93
- **Locales:** 14
- **Docs:** 42 markdown files
- **Build:** 33 JS chunks · first-paint JS 106.3 KB gzip · largest chunk 63.6 KB gzip · CSS 10.7 KB gzip · built in 7.3s
- **Sale archive:** 1485 KB

### meridian-capital

- **Live:** https://malikusmangoraya.github.io/meridian-capital
- **Source:** https://github.com/malikusmangoraya/meridian-capital
- **Niche:** fintech / portfolio intelligence
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Login, Portfolio, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 92
- **Locales:** 14
- **Docs:** 43 markdown files
- **Build:** 34 JS chunks · first-paint JS 106.0 KB gzip · largest chunk 63.6 KB gzip · CSS 10.8 KB gzip · built in 7.4s
- **Sale archive:** 1457 KB

### nuage-events

- **Live:** https://malikusmangoraya.github.io/nuage-events
- **Source:** https://github.com/malikusmangoraya/nuage-events
- **Niche:** events & ticketing
- **Pages (13):** About, Account, Admin, Checkout, Contact, Events, Home, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 93
- **Locales:** 14
- **Docs:** 43 markdown files
- **Media:** hero-poster.jpg (37 KB), hero.mp4 (538 KB)
- **Build:** 34 JS chunks · first-paint JS 106.0 KB gzip · largest chunk 63.6 KB gzip · CSS 11.1 KB gzip · built in 8.1s
- **Sale archive:** 2024 KB

### prestige-studio

- **Live:** https://malikusmangoraya.github.io/prestige-studio
- **Source:** https://github.com/malikusmangoraya/prestige-studio
- **Niche:** creative studio / portfolio
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Login, Pricing, Privacy, Register, Services, Terms, Work
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 92
- **Locales:** 14
- **Docs:** 43 markdown files
- **Build:** 34 JS chunks · first-paint JS 106.0 KB gzip · largest chunk 63.6 KB gzip · CSS 10.8 KB gzip · built in 7.8s
- **Sale archive:** 1260 KB

### resupro

- **Live:** https://malikusmangoraya.github.io/resupro
- **Source:** https://github.com/malikusmangoraya/resupro
- **Niche:** career / résumé SaaS
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Login, Pricing, Privacy, Register, Services, Templates, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 69
- **Locales:** 14
- **Docs:** 38 markdown files
- **Build:** 34 JS chunks · first-paint JS 105.8 KB gzip · largest chunk 63.6 KB gzip · CSS 10.4 KB gzip · built in 7.7s
- **Sale archive:** 2721 KB

### saffron-voyage

- **Live:** https://malikusmangoraya.github.io/saffron-voyage
- **Source:** https://github.com/malikusmangoraya/saffron-voyage
- **Niche:** curated travel
- **Pages (13):** About, Account, Admin, Checkout, Contact, Home, Itineraries, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 93
- **Locales:** 14
- **Docs:** 43 markdown files
- **Media:** hero-poster.jpg (40 KB), hero.mp4 (469 KB)
- **Build:** 34 JS chunks · first-paint JS 106.0 KB gzip · largest chunk 63.6 KB gzip · CSS 11.2 KB gzip · built in 7.8s
- **Sale archive:** 1953 KB

### studio-lumen

- **Live:** https://malikusmangoraya.github.io/studio-lumen
- **Source:** https://github.com/malikusmangoraya/studio-lumen
- **Niche:** photography / portfolio
- **Pages (13):** About, Account, Admin, Checkout, Contact, Galleries, Home, Login, Pricing, Privacy, Register, Services, Terms
- **API route modules (33)**
- **DB models (27)**
- **Frontend components:** 92
- **Locales:** 14
- **Docs:** 43 markdown files
- **Build:** 34 JS chunks · first-paint JS 106.0 KB gzip · largest chunk 63.6 KB gzip · CSS 10.7 KB gzip · built in 7.8s
- **Sale archive:** 1500 KB

