# Apex

> **Live demo:** https://malikusmangoraya.github.io/apex-digital · **Source code:** https://github.com/malikusmangoraya/apex-digital/tree/main

Enterprise full-stack hydration (Mode 2) — `Saas` SaaS / marketplace / dynamic application with persistent database, Redis-backed background jobs and an Nginx gateway.

## Architecture

```
Browser → Vite SPA (frontend/) → Axios (relative /api/*)
→ Nginx gateway (nginx/nginx.conf) → Express (:5000) → Sequelize (PostgreSQL/MySQL)
                                                          → Redis + BullMQ workers
```

The frontend Axios instance (`frontend/src/services/api.js`) is pre-configured for relative `/api/*` routes and ships complete auth/error interceptors.

## 1. Backend setup (copy-paste)

```bash
cd backend
npm install
cp .env.example .env        # then edit DATABASE_URL / REDIS_URL / JWT_SECRET
npm run seed               # optional seed data
npm run dev                # API on http://localhost:5000
```

### Database — PostgreSQL or MySQL

`backend/config/database.js` uses `DATABASE_URL` (Sequelize). Default is PostgreSQL (`pg` installed). For MySQL: `npm i mysql2`, flip `dialect` to `'mysql'`, set the `mysql://` DATABASE_URL above. Tables are synced in development; use migrations/indexes via `npm run db:indexes`.

### 2. Redis + BullMQ background jobs

```bash
redis-server            # Redis 6+ required (REDIS_URL)
cd backend
npm run worker          # BullMQ consumers (separate process)
```

Queues live in `backend/services/queue/` (queue.service.js, deadLetter.js, inlineJobs.js) and consumers in `backend/workers/worker.js`.

## 3. Frontend setup (copy-paste)

```bash
cd frontend
npm install
npm run dev                # http://localhost:5173
```

The Axios layer targets relative `/api/*` — locally set `VITE_API_URL=http://localhost:5000` in `frontend/.env` or let Vite proxy `/api` to :5000; in production Nginx does the routing.

## 4. Serve behind the Nginx gateway (copy-paste)

```bash
# Tune upstream backend:5000 vars in nginx/nginx.conf for your host.
sudo cp nginx/nginx.conf /etc/nginx/sites-available/apex.conf
sudo ln -s /etc/nginx/sites-available/apex.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

`location /api/` proxies to the Express upstream; static assets are served with cache + security headers.

## REST API surface

25 route groups mapped on `/api/*`:

- `address`
- `ai`
- `analytics`
- `audit`
- `auth`
- `booking`
- `business`
- `cart`
- `coupon`
- `dashboard`
- `health`
- `license`
- `notification`
- `order`
- `org`
- `payment`
- `plan`
- `playbook`
- `product`
- `search`
- `settings`
- `subscription`
- `upload`
- `user`
- `wishlist`

## Data model — Sequelize

25 models (PostgreSQL/MySQL ready):

- `Address`
- `AnalyticsEvent`
- `AuditLog`
- `Booking`
- `Cart`
- `CartItem`
- `Category`
- `Coupon`
- `Doctor`
- `Membership`
- `Notification`
- `Order`
- `Organization`
- `Payment`
- `Permission`
- `Plan`
- `Product`
- `Review`
- `Role`
- `Service`
- `Subscription`
- `SystemConfig`
- `User`
- `WebhookEvent`
- `Wishlist`

## 5. Production build

```bash
cd frontend && npm run build && cd ..
cd backend  && npm start
```

Serve `frontend/dist` behind Nginx and keep `backend` + `worker` behind the same gateway.

# Apex

Build a complete runnable full-stack premium automotive commerce platform named Apex Motion. Use React 19, Vite, Tailwind, Express REST API, and PostgreSQL schema, migrations, and realistic seed vehicles. Create a cinematic animated 3D supercar showroom hero using React Three Fiber when available, graceful non-WebGL fallback, responsive layout, and prefers-reduced-motion support. Include searchable/filterable/sortable inventory, vehicle details, interactive paint and wheel configurator with live price updates, compare and wishlist, cart and reservation checkout demo, financing calculator, validated test-drive/contact forms with loading/success/error states, login/register demo, and admin inventory dashboard. Add validated vehicle, inquiry, reservation, auth, and admin endpoints; safe demo-only payments; env example; Docker/dev scripts; SEO; accessible controls; automated tests; and exact README setup commands. Implement working interactions, no placeholders, and do not publish or deploy.

**Type:** Saas | **Audience:** agencies, founders, and digital-product buyers | **Quality bar:** marketplace / ThemeForest grade

## Features

- Animation System
- Countdown Timer
- Seo
- Social Proof
- Metrics
- I18n Multilingual
- Responsive Design
- Responsive
- Cart
- Cookie Consent
- Whatsapp Float
- Analytics Dashboard
- Authentication
- Pwa Support
- Seo Meta Tags
- Ai Chat
- Auth Flow
- Search
- Social Share
- Live Chat
- Pricing Table
- Accessibility Wcag
- Personalization
- Dashboard
- Exit Intent Popup
- Payments
- Security Hardening
- Wishlist
- Testimonial Slider
- Feature Grid
- Checkout

## Tech Stack

| Layer    | Technology   |
| -------- | ------------ |
| Frontend | React        |
| Backend  | Node Express |
| Database | Postgresql   |

## Prerequisites

- Node.js 18+ (20 LTS recommended)
- npm 9+
- PostgreSQL 14+ (or MySQL 8 if you switch dialect)
- Redis 6+ when using background jobs

## Getting Started

```bash
# 1. Backend
cd backend
cp .env.example .env      # set DATABASE_URL and JWT_SECRET
npm install
npm run dev               # http://localhost:5000

# 2. Frontend (new terminal)
cd frontend
cp .env.example .env      # set VITE_API_URL=http://localhost:5000
npm install
npm run dev               # http://localhost:5173
```

Optional Docker:

```bash
docker compose up --build
```

## Environment Variables

Copy `.env.example` to `.env`. Never commit `.env`.

| Variable       | Purpose                                                                                                                                         | Example                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `PORT`         | API port                                                                                                                                        | `5000`                                    |
| `DATABASE_URL` | PostgreSQL or MySQL connection string                                                                                                           | `postgres://user:pass@localhost:5432/app` |
| `JWT_SECRET`   | REQUIRED. Random 32+ char secret. Generate: node -e "console.log(require('crypto').randomBytes(48).toString('hex'))" (or: openssl rand -hex 32) | ``                                        |
| `CORS_ORIGIN`  | Allowed frontend origin                                                                                                                         | `http://localhost:5173`                   |
| `VITE_API_URL` | Frontend API base URL                                                                                                                           | `http://localhost:5000`                   |
| `REDIS_URL`    | Redis for queues (enterprise)                                                                                                                   | `redis://localhost:6379`                  |

## Project Structure

```
├── README.md                 # This file — details and start guide
├── LICENSE.md                # End-user license
├── .env.example              # Safe env template
├── frontend/                 # React 19 + Vite + Tailwind
├── screenshots/              # Marketplace preview images
├── backend/                  # Express API
├── database/                 # SQL schema
├── docker-compose.yml
├── INSTRUCTIONS.md           # Extended install and deploy
└── DEPLOYMENT_CHECKLIST.md
```

## Scripts

| Command         | Where              | Action            |
| --------------- | ------------------ | ----------------- |
| `npm run dev`   | frontend / backend | Local development |
| `npm run build` | frontend           | Production bundle |
| `npm run lint`  | frontend           | ESLint            |
| `npm test`      | where present      | Unit tests        |

## International

- UI copy in English; extra locales under `frontend/src/i18n` when generated
- RTL-ready layout tokens
- Currency display via Intl (USD, EUR, GBP, PKR, INR, AED, SAR)
- Privacy / Terms pages and cookie consent for EU buyers

## Troubleshooting

- **Blank page / 5173 refused:** run `npm install` inside `frontend`, then `npm run dev`.
- **API CORS / 401:** confirm `CORS_ORIGIN` and `VITE_API_URL` match the running backend.
- **Database errors:** create the database, apply `database/schema.sql`, restart the API.
- **Env not applied:** Vite inlines `VITE_*` at build time — rebuild after changing `.env`.

## Screenshots

Place desktop and mobile previews in `screenshots/` before listing on Gumroad, Lemon Squeezy, or ThemeForest.

## License

Paid end-user license. You may deploy and customize for client work. You may not resell this source as a competing template without a reseller license. See `LICENSE.md` and `LICENSE-SEAL.md`.
