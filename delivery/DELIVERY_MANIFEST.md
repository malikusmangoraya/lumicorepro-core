# Delivery Manifest (evidence-based)

Every column below is produced by a check that actually ran in
`scripts/final_verify_delivery.py` at the time this file was written. Nothing is
assumed: `live` is an HTTP probe result, `blue-free` is a scan of the built CSS, and
`zip valid` includes a CRC pass over every archive entry.

> 95 projects | dist built: 95 | blue-free: 69 | logos unique: 69/95 | zips present: 95 | zips valid: 95 | live links present: 95 (unique URLs: 95) | probed: 95 | probe ok: 95

Column meanings: `blue-free` = built CSS free of blue-family hex literals;
`logo` = sha256 of `public/logo.svg` is unique across the fleet; `zip` = archive opens
and passes CRC; `live` = HTTP status of the URL in the zip's `LIVE-LINK.txt`.

| # | Brand | Slug dir | Industry | Dist | Blue-free | Logo | Zip | Live |
|---|-------|----------|----------|------|-----------|------|-----|------|
| 1 | Adjusterly | adjusterly | fintech | yes | no | missing | valid | HTTP 200 |
| 2 | Apex Commerce | apex-commerce | ecommerce | yes | no | missing | valid | HTTP 200 |
| 3 | Apex Digital | apex-digital | saas | yes | no | missing | valid | HTTP 200 |
| 4 | Appointly | appointly | healthcare | yes | yes | unique | valid | HTTP 200 |
| 5 | Atlas Mobility | atlas-mobility | saas | yes | yes | unique | valid | HTTP 200 |
| 6 | Aurelia Estates | aurelia-estates | real-estate | yes | yes | unique | valid | HTTP 200 |
| 7 | Aurora Cloud | aurora-cloud | saas | yes | yes | unique | valid | HTTP 200 |
| 8 | Aurum Fitness | aurum-fitness | sports | yes | yes | unique | valid | HTTP 200 |
| 9 | Beacon Dental | beacon-dental | healthcare | yes | yes | unique | valid | HTTP 200 |
| 10 | Bellweather | bellweather | fintech | yes | no | missing | valid | HTTP 200 |
| 11 | Blume Botanics | blume-botanics | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 12 | Brass & Basil | brass-basil | food | yes | yes | unique | valid | HTTP 200 |
| 13 | Bristle & Co | bristle-co | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 14 | Capstone Advisors | capstone-advisors | saas | yes | yes | unique | valid | HTTP 200 |
| 15 | Cartwheel | cartwheel | ecommerce | yes | no | missing | valid | HTTP 200 |
| 16 | Cascade HQ | cascade-hq | saas | yes | yes | unique | valid | HTTP 200 |
| 17 | Cinder & Steel | cinder-steel | food | yes | yes | unique | valid | HTTP 200 |
| 18 | Cirrus Travel | cirrus-travel | hospitality | yes | yes | unique | valid | HTTP 200 |
| 19 | ClaimFlow | claimflow | saas | yes | yes | unique | valid | HTTP 200 |
| 20 | ClauseCheck | clausecheck | saas | yes | yes | unique | valid | HTTP 200 |
| 21 | Clover Dental | clover-dental | healthcare | yes | yes | unique | valid | HTTP 200 |
| 22 | Copperline | copperline | industrial | yes | no | missing | valid | HTTP 200 |
| 23 | Create Studio | create-studio | saas | yes | no | missing | valid | HTTP 200 |
| 24 | Deckflow | deckflow | saas | yes | yes | unique | valid | HTTP 200 |
| 25 | DeployDock | deploydock | saas | yes | yes | unique | valid | HTTP 200 |
| 26 | Ember & Salt | ember-salt | food | yes | yes | unique | valid | HTTP 200 |
| 27 | Fitly Academy | fitly-academy | education | yes | yes | unique | valid | HTTP 200 |
| 28 | Fleetwood Events | fleetwood-events | entertainment | yes | yes | unique | valid | HTTP 200 |
| 29 | Forgekit | forgekit | saas | yes | yes | unique | valid | HTTP 200 |
| 30 | Foxglove Care | foxglove-care | healthcare | yes | no | missing | valid | HTTP 200 |
| 31 | Groundswell | groundswell | sports | yes | no | missing | valid | HTTP 200 |
| 32 | Halo Retail | halo-retail | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 33 | Harbor Insurance | harbor-insurance | fintech | yes | yes | unique | valid | HTTP 200 |
| 34 | Harborline | harborline | logistics | yes | no | missing | valid | HTTP 200 |
| 35 | Heritage Trails | heritage-trails | entertainment | yes | yes | unique | valid | HTTP 200 |
| 36 | InsightPipe | insightpipe | saas | yes | yes | unique | valid | HTTP 200 |
| 37 | Ironwood Realty | ironwood-realty | real-estate | yes | no | missing | valid | HTTP 200 |
| 38 | Juniper Goods | juniper-goods | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 39 | Kestrel Fleet | kestrel-fleet | logistics | yes | no | missing | valid | HTTP 200 |
| 40 | Kinetiq Health | kinetiq-health | healthcare | yes | yes | unique | valid | HTTP 200 |
| 41 | Launchbay | launchbay | saas | yes | yes | unique | valid | HTTP 200 |
| 42 | LeadScout AI | leadscout-ai | real-estate | yes | yes | unique | valid | HTTP 200 |
| 43 | LedgerAI | ledgerai | fintech | yes | yes | unique | valid | HTTP 200 |
| 44 | Ledgerline | ledgerline | saas | yes | yes | unique | valid | HTTP 200 |
| 45 | Ledgerpoint | ledgerpoint | fintech | yes | no | missing | valid | HTTP 200 |
| 46 | LinguaGrid | linguagrid | saas | yes | yes | unique | valid | HTTP 200 |
| 47 | Lumen Studio | lumen-studio | portfolio | yes | no | missing | valid | HTTP 200 |
| 48 | Lumina Academy | lumina-academy | education | yes | yes | unique | valid | HTTP 200 |
| 49 | Luxemart | luxemart | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 50 | Maison Noir | maison-noir | fashion | yes | yes | unique | valid | HTTP 200 |
| 51 | Marble Run Hotels | marble-run-hotels | hospitality | yes | yes | unique | valid | HTTP 200 |
| 52 | Marlow Fitness | marlow-fitness | healthcare | yes | no | missing | valid | HTTP 200 |
| 53 | Meridian Capital | meridian-capital | fintech | yes | yes | unique | valid | HTTP 200 |
| 54 | Metrica Pulse | metrica-pulse | saas | yes | yes | unique | valid | HTTP 200 |
| 55 | Mirage Beauty | mirage-beauty | fashion | yes | yes | unique | valid | HTTP 200 |
| 56 | Noir Frames | noir-frames | portfolio | yes | yes | unique | valid | HTTP 200 |
| 57 | Noora Khan | noora-khan | portfolio | yes | yes | unique | valid | HTTP 200 |
| 58 | Northbeam | northbeam | saas | yes | no | missing | valid | HTTP 200 |
| 59 | Northpeak Outfitters | northpeak-outfitters | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 60 | Nova Forge | nova-forge | saas | yes | yes | unique | valid | HTTP 200 |
| 61 | Nuage Events | nuage-events | entertainment | yes | yes | unique | valid | HTTP 200 |
| 62 | Onboarder | onboarder | saas | yes | yes | unique | valid | HTTP 200 |
| 63 | Orbit Studios | orbit-studios | portfolio | yes | yes | unique | valid | HTTP 200 |
| 64 | Orbitboard | orbitboard | saas | yes | yes | unique | valid | HTTP 200 |
| 65 | Orchard Grid | orchard-grid | saas | yes | no | missing | valid | HTTP 200 |
| 66 | Petrichor | petrichor | hospitality | yes | no | missing | valid | HTTP 200 |
| 67 | Pinnacle Events | pinnacle-events | entertainment | yes | no | missing | valid | HTTP 200 |
| 68 | Pinnacle Fitness | pinnacle-fitness | sports | yes | yes | unique | valid | HTTP 200 |
| 69 | Prestige Studio | prestige-studio | portfolio | yes | yes | unique | valid | HTTP 200 |
| 70 | PulseLabs | pulselabs | healthcare | yes | yes | unique | valid | HTTP 200 |
| 71 | Quarry Learning | quarry-learning | education | yes | no | missing | valid | HTTP 200 |
| 72 | RecruitIQ | recruitiq | saas | yes | yes | unique | valid | HTTP 200 |
| 73 | ResuPro | resupro | saas | yes | yes | unique | valid | HTTP 200 |
| 74 | Roark Analytics | roark-analytics | saas | yes | yes | unique | valid | HTTP 200 |
| 75 | Sable Fit | sable-fit | fashion | yes | no | missing | valid | HTTP 200 |
| 76 | Saffron Voyage | saffron-voyage | hospitality | yes | yes | unique | valid | HTTP 200 |
| 77 | Sheetstack | sheetstack | saas | yes | yes | unique | valid | HTTP 200 |
| 78 | Signalbase | signalbase | saas | yes | no | missing | valid | HTTP 200 |
| 79 | Solstice Energy | solstice-energy | industrial | yes | no | missing | valid | HTTP 200 |
| 80 | Stacksail | stacksail | saas | yes | yes | unique | valid | HTTP 200 |
| 81 | Stonemark Realty | stonemark-realty | real-estate | yes | yes | unique | valid | HTTP 200 |
| 82 | Studio Lumen | studio-lumen | portfolio | yes | yes | unique | valid | HTTP 200 |
| 83 | Sundial Media | sundial-media | entertainment | yes | no | missing | valid | HTTP 200 |
| 84 | SupportDesk AI | supportdesk-ai | ecommerce | yes | yes | unique | valid | HTTP 200 |
| 85 | TableHost AI | tablehost-ai | food | yes | yes | unique | valid | HTTP 200 |
| 86 | Ternion Instruments | ternion-instruments | electronics | yes | yes | unique | valid | HTTP 200 |
| 87 | TerraVista | terravista | real-estate | yes | yes | unique | valid | HTTP 200 |
| 88 | Tidewater Travel | tidewater-travel | hospitality | yes | no | missing | valid | HTTP 200 |
| 89 | Vantage 3D Estates | vantage-3d-estates | real-estate | yes | yes | unique | valid | HTTP 200 |
| 90 | Vantage HR | vantage-hr | saas | yes | no | missing | valid | HTTP 200 |
| 91 | Vaultline | vaultline | fintech | yes | yes | unique | valid | HTTP 200 |
| 92 | Veridian E-Catalog | veridian-e-catalog | electronics | yes | yes | unique | valid | HTTP 200 |
| 93 | Vine & Vale | vine-vale | food | yes | yes | unique | valid | HTTP 200 |
| 94 | Voltus Atelier | voltus-atelier | electronics | yes | yes | unique | valid | HTTP 200 |
| 95 | Zephyr Way | zephyr-way | hospitality | yes | yes | unique | valid | HTTP 200 |
