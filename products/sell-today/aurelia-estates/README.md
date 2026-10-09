# Aurelia Estates

> **Live demo:** https://malikusmangoraya.github.io/aurelia-estates · **Source code:** https://github.com/malikusmangoraya/aurelia-estates/tree/main

Enterprise full-stack hydration (Mode 2) — `Realestate` SaaS / marketplace / dynamic application with persistent database, Redis-backed background jobs and an Nginx gateway.

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
sudo cp nginx/nginx.conf /etc/nginx/sites-available/aurelia-estates.conf
sudo ln -s /etc/nginx/sites-available/aurelia-estates.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

`location /api/` proxies to the Express upstream; static assets are served with cache + security headers.

## REST API surface

24 route groups mapped on `/api/*`:

- `address`
- `ai`
- `analytics`
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

# Aurelia Estates

Build a luxury international real-estate platform showcasing exclusive villas and penthouses in Dubai, Paris and Miami. Brand: 'Aurelia Estates' - refined minimal with editorial typography. Audience: global HNWI investors and expats. Full features: user auth (register/login/reset, JWT), Stripe payment for viewings and holding deposits, hero with cinematic listing imagery, property listing grid with filters and bookmarking, agent concierge booking, i18n (English, Arabic, Spanish) with RTL support, multi-currency (USD, EUR, AED, SAR), WhatsApp float, GDPR consent, cookies policy, privacy and terms pages, SEO meta + OG + JSON-LD + sitemap, dark luxury theme. React 19 + Vite + Tailwind, Express + MySQL, structure identical to Aurelia Estates. Everything real and production-ready.

**Type:** Realestate | **Audience:** agencies, founders, and digital-product buyers | **Quality bar:** marketplace / ThemeForest grade

## Features

- Virtual Tour
- Social Share
- Mortgage Calculator
- Contact Agent
- Filters
- Property Search
- Whatsapp
- Responsive Design
- Cookie Consent
- Seo Meta Tags
- Security Hardening
- Seo
- Wishlist Compare
- Ai Chat
- Map
- Whatsapp Float
- Accessibility Wcag
- Booking
- Animation System
- Stripe
- Map View
- I18n Multilingual
- Newsletter Signup
- Authentication
- Pwa Support
- Testimonial Carousel
- Live Chat
- Social Proof

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
