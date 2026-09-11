# LumicorePro Core — Complete System Master Prompt

**Version:** 1.0  
**Status:** Production-ready blueprint  
**Scope:** Frontend (React + Vite) · Backend (Node + Express) · Database (MySQL) · AI

---

## System architecture

```
End User → React Frontend → Axios API Gateway → Express Backend → MySQL
                              ↘ Stripe / AI providers / Email / Uploads
```

---

## Frontend (`src/`)

| Area | Purpose |
|------|---------|
| `components/ui` | Primitives (Button, Card, Modal, …) |
| `components/*` | Domain UI (dashboard, ecommerce, ai, business, forms, auth) |
| `templates/` | 20 production page templates |
| `pages/` | App routes (Home, Templates hub, Auth) |
| `layouts/` | Main / Auth / Dashboard shells |
| `hooks/` | useApi, useForm, useAuth, useCart, useReveal, … |
| `context/` | App, Auth, Cart, Theme |
| `services/` | api, auth, product, order, ai |
| `styles/` | tokens, animations |
| `config/` | app + theme config |

**Rules:** Tailwind-first · design tokens · a11y · motion 150–300ms · Lucide icons **with visible labels** (icon + name side by side).

---

## Backend (`backend/`)

```
backend/src/
  config/     database, env, cors, jwt
  routes/     auth, users, products, orders, cart, payments, ai, admin
  controllers/
  services/
  models/
  middleware/ auth, error, validation, rateLimit
  validators/
  utils/
  server.js
```

Standard response:

```json
{ "success": true, "status": 200, "message": "...", "data": {}, "timestamp": "..." }
```

---

## Database (MySQL)

Core domains:

1. **Auth** — users, sessions, password_resets  
2. **Catalog** — categories, products, product_images, product_variants, reviews  
3. **Commerce** — carts, cart_items, orders, order_items, payments  
4. **AI** — conversations, messages, ai_usage  
5. **SaaS** — plans, subscriptions, invoices  
6. **Admin** — audit_logs, settings  

SQL lives in `database/schema.sql`.

---

## API surface (summary)

- `POST/GET /api/auth/*` — register, login, logout, refresh, me, password reset  
- `GET/PUT /api/users/:id` — profile, avatar, password  
- `GET/POST /api/products` — list, detail, search, reviews (admin CRUD)  
- `GET/POST /api/cart` — items, coupon  
- `GET/POST /api/orders` — create, cancel, invoice, track  
- `POST /api/payments/stripe/*` — intent, confirm, webhook  
- `POST/GET /api/ai/*` — chat, conversations, generate, usage, models  
- `GET/PUT /api/admin/*` — users, stats, logs, settings  

Full endpoint list: see `docs/API.md` (when expanded) and `backend/src/routes/`.

---

## Security

- Access JWT ~15m · Refresh ~7d (httpOnly cookie preferred)  
- bcrypt (12 rounds) · parameterized SQL · CORS whitelist · rate limits · HTTPS in prod  

---

## Phases

| Phase | Focus | Status in repo |
|-------|--------|----------------|
| 1 | Vite + React foundation | Done |
| 2 | Config, hooks, standards | Done |
| 3 | Design system + motion | Done |
| 4 | 20 templates | Done |
| 5+ | Backend + DB + AI agent | Scaffolded / next |

---

## Success criteria

- Reusable UI + 20 templates  
- Auth + commerce + AI flows  
- MySQL schema + Express API scaffold  
- Professional UX: **every icon paired with a clear label**  
- Deployable frontend; backend ready to flesh out  

---

## Commands

```bash
# Frontend
npm run dev

# Backend (from backend/)
npm install && npm run dev
```

Open `/templates` for the gallery.
