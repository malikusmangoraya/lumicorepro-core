# Aurum Fitness

> **Live demo:** https://malikusmangoraya.github.io/aurum-fitness · **Source code:** https://github.com/malikusmangoraya/aurum-fitness/tree/main

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
sudo cp nginx/nginx.conf /etc/nginx/sites-available/aurum-fitness.conf
sudo ln -s /etc/nginx/sites-available/aurum-fitness.conf /etc/nginx/sites-enabled/
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

# Aurum Fitness

Build a premium wellness and fitness membership platform 'Aurum Fitness' with elite coaching, virtual classes and nutrition plans. Audience: health-conscious professionals worldwide. Features: auth (register/login/one-time-code, JWT), Stripe subscription payments, hero with athlete imagery, class schedule, coach profiles and booking, nutrition plans, membership tiers with pricing toggle, progress dashboard, i18n (English, Arabic, Spanish) RTL, multi-currency (USD, EUR, AED), privacy/terms, cookie consent, SEO, clean premium light+dark theme. React 19 + Vite + Tailwind, Express + MySQL. Real.

**Type:** Saas | **Audience:** agencies, founders, and digital-product buyers | **Quality bar:** marketplace / ThemeForest grade

## Features

- Metrics
- I18n Multilingual
- Seo Meta Tags
- Ai Chat
- Analytics Dashboard
- Countdown Timer
- Video Player
- Dashboard
- Instructor Rating
- Testimonial Slider
- Live Chat
- Course Catalog
- Animation System
- Auth Flow
- Responsive Design
- Seo
- Cookie Consent
- Feature Grid
- Progress Tracking
- Booking
- Social Proof
- Security Hardening
- Social Share
- Certificates
- Personalization
- Exit Intent Popup
- Whatsapp Float
- Pricing Table
- Accessibility Wcag
- Newsletter Signup
- Authentication
- Stripe
- Payments
- Pwa Support

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
