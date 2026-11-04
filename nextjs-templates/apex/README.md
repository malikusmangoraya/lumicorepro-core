# Apex — Next.js 16 Automotive Commerce Template

> A complete, production-shaped car dealership and collector-car marketplace built on
> **Next.js 16.4.5** (App Router), **React 19.3.1**, **TypeScript**, **Tailwind CSS 4**
> and **Prisma**.

Ported from the Apex Vite/React + Express product so that the whole storefront and its
API run as **one deployable Next.js application** — no separate Express process.

---

## What's inside

| Area | Detail |
|------|--------|
| **Pages** | Home, Inventory, Vehicle detail, Shop, Product detail, Cart, Checkout, Order tracking, Trade-in, Saved, Compare, Services, Pricing, About, Contact, Insights, Privacy, Terms, Login, Register, Account, Account orders, Admin, 404 |
| **Leads** | One endpoint, four intents: enquiry, test drive with a date, finance quote with a deposit, and part-exchange valuation. Type-specific fields are required, not optional |
| **Discovery** | Favourites, 3-way compare with a spec table, eight-way filtering (search, make, body, fuel, gearbox, year, mileage, price), five sort orders, pagination, recently viewed |
| **Vehicle detail** | Multi-photo gallery with a keyboard-driven lightbox, finance estimator, share (Web Share + clipboard), `Car` JSON-LD, breadcrumbs with `BreadcrumbList` schema |
| **Polish** | Toast notifications, scroll reveal (reduced-motion safe), loading skeletons, back-to-top, newsletter capture |
| **Commerce** | Shop with stock, product detail pages with reviews, cart persisted in the browser, guest or signed-in checkout, discount codes validated server-side, server-side price and stock recomputation, customer order history with a status timeline |
| **Public API** | `GET /api/health`, `GET /api/vehicles`, `GET /api/vehicles/[slug]`, `POST /api/inquiries`, `POST /api/checkout`, `GET /api/media/[id]` |
| **Auth API** | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/auth/account/export`, `DELETE /api/auth/account` |
| **Admin** | `/admin` overview, `/admin/analytics`, `/admin/vehicles` (list, create, edit, upload, withdraw), `/admin/orders` (list, detail, status pipeline, tracking, notes, manual order), `/admin/reviews` (moderation), `/admin/inquiries` (status pipeline + notes), `/admin/newsletter`. Admin-only at the layout and at every mutating route. |
| **Auth** | JWT access token (15 min) + refresh token (30 day) in HttpOnly cookies, bcrypt (12 rounds), admin role gate |
| **Data** | Prisma schema with 20 models: users, vehicles, reviews, enquiries, products, carts, orders, payments, coupons, plans, subscriptions, addresses, notifications, media assets, webhook events, audit log |
| **Validation** | Zod schemas on every write, shared shape between client and server |
| **Responses** | One envelope everywhere: `{ success, status, message, data, timestamp }` |
| **Payments** | Stripe Checkout created over the REST API (no SDK), webhook verified against the raw body with a timestamp tolerance. No keys means 503, never a silently accepted event |
| **Reviews** | Guest or signed-in reviews with a verified-purchase flag derived from delivered orders; nothing is public until an admin approves it |
| **Analytics** | `/admin/analytics`: revenue and order trend, average order, orders by status, most enquired vehicles, best selling products, trust signals |
| **Uploads** | Admin image upload stored in Postgres (`MediaAsset`) and served from `/api/media/[id]` — no writable disk needed |
| **Theming** | Dark and light palettes from the same tokens, persisted, applied before first paint |
| **i18n** | English, Urdu and Arabic UI with RTL. Navigation, cart, checkout and shared actions are translated; listing content stays as the operator wrote it |
| **Consent** | Analytics is consent-gated: no tag is loaded until the visitor accepts, and rejecting is as easy as accepting |
| **Conversion** | Click-to-call and WhatsApp floats, business hours in the footer, optional promo strip driven by `NEXT_PUBLIC_PROMO` |
| **Safety** | Per-IP rate limits on login, register, leads, checkout, reviews, coupons and newsletter; idempotent lead submission; no account enumeration; conditional stock claim |
| **Tests** | Vitest unit tests for formatters, validation, the API envelope, rate limiter, finance maths, order transitions, totals, analytics bucketing, coupon maths, Stripe signature verification and template integrity (88 tests) |
| **SEO** | Metadata API, Open Graph, canonical URLs, `sitemap.xml` covering every vehicle, `robots.txt`, `AutoDealer` + `Car` + `Product` + `BreadcrumbList` JSON-LD, security headers |

### Design system

| Token | Value |
|-------|-------|
| Primary | `#b75cf6` |
| Secondary | `#9f28d9` |
| Accent | `#e284fc` |
| Canvas | `#070913` |
| Surface | `#121b2f` |
| Border | `#1e293b` |
| Display font | Syne |
| Body font | Inter |
| Light canvas | `#f5f6fa` |
| Light surface | `#ffffff` |

Dark-first, single palette, WCAG-conscious contrast, visible focus rings, a skip link and
`prefers-reduced-motion` support. Tokens live in `src/app/globals.css` under `@theme`.

---

## Getting started

### 1. Requirements

- **Node.js 20.9+** (Node 22 recommended)
- npm 10+

### 2. Install

```bash
npm install
```

`postinstall` runs `prisma generate`.

### 3. Configure

```bash
cp .env.example .env
```

Then set `JWT_SECRET` and `JWT_REFRESH_SECRET` to 32+ character random strings:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

The app **refuses to sign tokens** without them — there is no insecure fallback.

### 4. Point `DATABASE_URL` at a Postgres server

Neon, Supabase, RDS, Railway or a local container all work. TLS is required by most
managed providers:

```
DATABASE_URL="postgresql://user:password@host:5432/apex?sslmode=require"
```

### 5. Create and seed the database

```bash
npm run db:setup
```

This runs `prisma db push` (creates the tables) and seeds:

| Account | Password | Role |
|---------|----------|------|
| `admin@apex.com` | `Password123!` | admin |
| `customer@apex.com` | `Password123!` | customer |

It also seeds 6 vehicles, 3 membership plans, 3 products and one enquiry.

### 6. Run

```bash
npm run dev
```

Open <http://localhost:3000>.

---

## Scripts

| Script | What it does |
|--------|--------------|
| `npm run dev` | Development server |
| `npm run build` | Production build |
| `npm start` | Serve the production build |
| `npm run lint` | ESLint (Next core-web-vitals + TypeScript) |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest |
| `npm run db:push` | Sync the Prisma schema to the database |
| `npm run db:seed` | Seed demo data |
| `npm run db:setup` | `db:push` + `db:seed` |
| `npm run db:studio` | Prisma Studio |

---

## Project structure

```
apex/
├── prisma/
│   ├── schema.prisma         17 models, SQLite by default
│   └── seed.ts               demo users, vehicles, plans, products
├── public/
│   ├── vehicles/*.svg        seeded vehicle artwork (replace with photos)
│   └── og.svg                social card
├── src/
│   ├── app/
│   │   ├── layout.tsx        fonts, metadata, header/footer
│   │   ├── page.tsx          Home
│   │   ├── inventory/        listing + [slug] detail
│   │   ├── services|pricing|about|contact|insights|privacy|terms/
│   │   ├── login|register|account|admin/
│   │   ├── not-found.tsx     real 404
│   │   ├── sitemap.ts, robots.ts
│   │   └── api/              route handlers
│   ├── components/
│   │   ├── brand/            BrandMark, BrandLockup
│   │   ├── layout/           SiteHeader, SiteFooter
│   │   ├── ui/               Button, Panel, Badge, Field, Section
│   │   ├── vehicle/          VehicleCard, InventoryFilters, InquiryForm
│   │   ├── pricing/          PricingTable
│   │   └── auth/             LoginForm, RegisterForm, SignOut, DeleteAccount
│   └── lib/
│       ├── api.ts            response envelope helpers
│       ├── auth.ts           JWT, bcrypt, session cookies
│       ├── prisma.ts         singleton client
│       ├── rate-limit.ts     in-memory sliding window
│       ├── utils.ts          formatters, slugify, JSON parsing
│       ├── validation.ts     Zod schemas
│       └── vehicles.ts       typed queries with graceful DB-down fallback
└── tests/                    Vitest suites
```

---

## Switching to SQLite

Postgres is the default because the template deploys to serverless, where a SQLite file
is read-only and not shared between instances. For single-machine development without a
database server:

1. Change the provider in `prisma/schema.prisma`:

   ```prisma
   datasource db {
     provider = "sqlite"
     url      = env("DATABASE_URL")
   }
   ```

2. Set `DATABASE_URL="file:./dev.db"` in `.env`.
3. `npm run db:push && npm run db:seed`

Nothing else changes — the schema avoids engine-specific types by storing status columns
as `String` and structured payloads as JSON text, both of which map cleanly to SQLite and
Postgres.

---

## Deploying

### Vercel

1. Push the folder to a repository.
2. Import it in Vercel.
3. Add `DATABASE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `NEXT_PUBLIC_SITE_URL`.
4. Deploy.

Use a hosted Postgres (Neon/Supabase) — the bundled SQLite file is for local development
only.

### Docker

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate && npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/prisma ./prisma
EXPOSE 3000
CMD ["npm", "start"]
```

---

## Accessibility

- Skip-to-content link is the first focusable element.
- Every form control has a visible label; errors use `role="alert"`.
- Live regions (`aria-live="polite"`) announce inventory counts.
- Focus-visible rings on every interactive element.
- `prefers-reduced-motion` disables transitions and smooth scrolling.
- Colour pairs are chosen for AA contrast on the dark canvas.

---

## What this template deliberately does not do

- **No payment capture.** The pricing page states that checkout needs a configured store
  rather than pretending a button worked. Wire Lemon Squeezy or Stripe into
  `POST /api/checkout` when you have keys.
- **No image upload UI.** Vehicle media is stored as URLs; point them at your CDN.
- **No email delivery.** Enquiries are stored; add your provider in `POST /api/inquiries`.
- **No multi-tenancy.** One dealership per deployment.

Each of these is a deliberate boundary, not a missing feature that fails silently.

---

## Payments

Card payment is optional and off by default. Set `STRIPE_SECRET_KEY` and
`STRIPE_WEBHOOK_SECRET`, then point a Stripe webhook at
`https://<your-host>/api/webhooks/stripe` for `checkout.session.completed`.

Without the keys, checkout still records the order and the confirmation panel
says card payment is unavailable — it never pretends a button worked. The
webhook answers **503** when the secret is missing and **400** when the
signature does not match the raw body or is older than five minutes.

## Demo imagery

The six vehicle photos in `public/vehicles/` are **AI-generated demo renders**, not
photographs of real cars and not stock licensed from a third party. They exist so the
template looks finished out of the box and ships with clean rights.

Before launch:

1. Replace each file in `public/vehicles/` with your own photography (keep the filename).
2. Update the `media` array for each vehicle in `prisma/seed.ts` if the filenames differ.
3. Re-run `npm run db:seed`.

The social card `public/og.jpg` is composed from the Porsche render — regenerate it from
your own hero shot.

## License

MIT — see [LICENSE.md](./LICENSE.md). The demo imagery is generated specifically for this
template and carries the same MIT grant.
