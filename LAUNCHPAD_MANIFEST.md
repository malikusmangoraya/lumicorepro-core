# LAUNCHPAD_MANIFEST â€” 10 Niche Storefronts

> Generated 2026-09-12 (03:29â€“03:42) by LumicorePro 15-phase enterprise generator.
> All 10 projects: Enterprise Architect gate **passed** + DevOps QUALITY GATE **passed** (format+lint attempt 1, `npm install` ok, `vite build` exit 0) + **ZIP produced**.

## The 10 Projects

| # | Project | ZIP | Niche (Pakistan/SA focus) |
|---|---------|-----|---------------------------|
| 1 | `poultry-fresh-001` | `generated-projects/poultry-fresh-001.zip` | Poultry products â€” fresh chicken, hatching eggs, feed, farm supplies (RozanaMurghi) |
| 2 | `dairy-hub-001` | `generated-projects/dairy-hub-001.zip` | Dairy â€” milk, yogurt, butter, cheese + dairy equipment (ShahzoreDairy) |
| 3 | `fishery-baazaar-001` | `generated-projects/fishery-baazaar-001.zip` | Seafood â€” fresh fish, prawns, dried fish, aquaculture supplies (MachhliFresh) |
| 4 | `zarai-tractors-002` | `generated-projects/zarai-tractors-002.zip` | Farm equipment â€” tractor service packages, harvester hire, tools (ZaraiKirai) |
| 5 | `kiryana-mart-002` | `generated-projects/kiryana-mart-002.zip` | General store â€” groceries, household items, snacks, ration packs + full backend (BaazaarKiryana) |
| 6 | `petrolplus-001` | `generated-projects/petrolplus-001.zip` | Fuel station retail â€” lubricants, engine oil, convenience snacks, prepaid cards (PetrolPlus) |
| 7 | `expresspak-001` | `generated-projects/expresspak-001.zip` | Courier â€” shipping packages, packing supplies, label bundles (ExpressPak) |
| 8 | `madrasa-learning-001` | `generated-projects/madrasa-learning-001.zip` | Education supplies â€” uniforms, books, stationery, donation bundles (KhairMadrasa) |
| 9 | `jashn-banquet-001` | `generated-projects/jashn-banquet-001.zip` | Events â€” wedding packages, decor, catering plans, date reservations (JashnBanquet) |
| 10 | `suthra-laundry-001` | `generated-projects/suthra-laundry-001.zip` | Laundry â€” wash-and-fold plans, dry cleaning, subscriptions (SuthraLaundry) |

Every project uses the proven storefront recipe (dark mode, product pages with reviews, cart + checkout) and includes deploy configs (Vercel/Railway/AWS/nginx/docker), PWA, SEO/JSON-LD, i18n + RTL, Analytics, cookie-consent compliance.

## Stack (per project)
React 19.2 / Vite 8 / Tailwind v3 (dark-mode, RTL-ready) â€” all dependency pins verified by architect gate. `kiryana-mart-002` additionally carries the full Express/Sequelize backend (14+ models, Redis/BullMQ, RBAC + multi-tenancy).

## Run / Preview (any project)
```
cd generated-projects/<name>
cd frontend && npm install && npm run dev    # local preview (Vite)
npm run build                                 # production bundle
```
Deploy: push ZIP contents to Vercel/Netlify (static) or use the included `vercel.json`/`railway.json`/`Dockerfile` + `nginx.conf` for the full-stack kiryana project.

## Production-ready stack now shipped (12 Sep update)
Every storefront now includes a **live order backend** + **admin panel** + **editable product catalog**.

### What changed
- `backend/server.js`: Express + JSON-file order persistence (zero native deps, no DB). Endpoints:
  - `GET /api/products`, `GET /api/config`
  - `POST /api/orders` (validates + recalculates server-side from catalog)
  - `GET /api/orders/:trackingId`
  - `GET /api/admin/orders?token=ADMIN_TOKEN`, `GET /api/admin/stats?token=ADMIN_TOKEN`
- `frontend/src/pages/Store.jsx`: product grid fetched live from `/api/products`, "Add to Cart" wired
- `frontend/src/pages/Cart.jsx`: cart review + one-page checkout (COD + WhatsApp order confirmation)
- `frontend/src/data/catalog.json`: single source of truth for products (edit this to set real SKUs/prices)
- `frontend/public/admin.html`: orders dashboard (open while backend runs, enter `ADMIN_TOKEN`)
- Niche-specific content: hero text, features, about section replaced across all pages
- `render.yaml` + `Procfile` included for one-click deploy

### Deploy steps (quickest path to first order)
1. **Edit `frontend/src/data/catalog.json`** with real products (id, title, tagline, price in PKR).
2. **Backend**: set env vars `SITE_NAME`, `WHATSAPP_NUMBER`, `ADMIN_TOKEN`, `DELIVERY_FEE`, `PORT=5000` (Render/VPS).
3. **Frontend**: `npm run build`, host `dist/` on static host; proxy `/api` to your backend URL.
4. Place test order at `/shop` â†’ `/cart`, check `/admin.html`.

### Generator pipeline
`ai-agent/agent/commerce_ready.py` now hooks automatically after component injection:
- Injects backend + catalog + Store/Cart pages + admin for any static storefront
- Idempotent â€” safe to re-run on existing projects
- Run any generation; the commerce stack arrives pre-wired (add products to `catalog.json` after)

## Generator fixes landed tonight (deterministic, committed)
- VFS self-heal rewrite-intent (no more duplicated components) + 2 regression tests âžœ `4e41ee7`
- compliance_generator CookieConsent import path fix âžœ `4e41ee7`
- `deploy.yml` platform-step indentation fix âžœ `809d440`
- quality_gate lint-by-directory (Windows cmdline length) âžœ `809d440`
- backend lint fixes: taxCalculator TH dup + useless assigns, health.routes initializers, payment config âžœ `809d440`
- kiryana full-stack enterprise fix: canonical `models/index.js` (all FK contract + org_id multi-tenancy + role_permissions RBAC), 7 JSON-LD types, h3â†’h2 heading hierarchy
- **`commerce_ready.py`**: deterministic production-ready injector for all future storefront generations âžœ `TODAY`

> Note: Groq free-tier OTPM 1000/min blocks AI self-healing, so all fixes above were made deterministic â€” every project passes both gates without AI runtime healing.
