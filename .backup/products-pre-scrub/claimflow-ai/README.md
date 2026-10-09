# Claimflow Ai

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
sudo cp nginx/nginx.conf /etc/nginx/sites-available/lumicorepro.conf
sudo ln -s /etc/nginx/sites-available/lumicorepro.conf /etc/nginx/sites-enabled/
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

# Claimflow Ai

Build 'ClaimFlow' — a vertical AI agent SaaS for insurance claims intake: gathers documents, triage by policy coverage, validates completeness, drafts the claim summary and routes to an adjuster with GL codes and recommended next steps. Audience: P&C insurers and MGA/broker shops still running paper claims. Product: full-stack SaaS with auth (register/login/2FA, JWT), Stripe subscription (per-claim bundles), landing page with the intake -> validate -> route funnel and a claims demo, and an Agent Console: claims queue with triage status, document checklist, coverage match and fraud-flag hints, adjuster assignment, SLA timers, audit trail and usage/billing. i18n (English, Spanish, French), multi-currency (USD, EUR, GBP), privacy/terms with compliance disclaimer, cookie consent, SEO + OG + JSON-LD + sitemap, institutional trust theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. Real and production-ready.

**Type:** Saas | **Audience:** agencies, founders, and digital-product buyers | **Quality bar:** marketplace / ThemeForest grade

## Features

- Seo
- Analytics Dashboard
- Stripe
- Pricing Table
- Social Proof
- Map
- Social Share
- Accessibility Wcag
- Exit Intent Popup
- Whatsapp Float
- Personalization
- Authentication
- Feature Grid
- Cookie Consent
- Testimonial Slider
- Auth Flow
- I18n Multilingual
- Ai Chat
- Animation System
- Seo Meta Tags
- Responsive Design
- Metrics
- Pwa Support
- Live Chat
- Countdown Timer
- Security Hardening
- Dashboard

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

| Variable       | Purpose                               | Example                                     |
| -------------- | ------------------------------------- | ------------------------------------------- |
| `PORT`         | API port                              | `5000`                                      |
| `DATABASE_URL` | PostgreSQL or MySQL connection string | `postgres://user:pass@localhost:5432/app`   |
| `JWT_SECRET`   | Random 64-character secret            | `replace_with_a_random_64_character_secret` |
| `CORS_ORIGIN`  | Allowed frontend origin               | `http://localhost:5173`                     |
| `VITE_API_URL` | Frontend API base URL                 | `http://localhost:5000`                     |
| `REDIS_URL`    | Redis for queues (enterprise)         | `redis://localhost:6379`                    |

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
