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
| **Pages** | Home, Inventory, Vehicle detail, Services, Pricing, About, Contact, Insights, Privacy, Terms, Login, Register, Account, Admin, 404 |
| **Public API** | `GET /api/health`, `GET /api/vehicles`, `GET /api/vehicles/[slug]`, `POST /api/inquiries` |
| **Auth API** | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/auth/account/export`, `DELETE /api/auth/account` |
| **Auth** | JWT access token (15 min) + refresh token (30 day) in HttpOnly cookies, bcrypt (12 rounds), admin role gate |
| **Data** | Prisma schema with 17 models: users, vehicles, enquiries, products, carts, orders, payments, coupons, plans, subscriptions, addresses, notifications, audit log |
| **Validation** | Zod schemas on every write, shared shape between client and server |
| **Responses** | One envelope everywhere: `{ success, status, message, data, timestamp }` |
| **Safety** | Per-IP rate limits on login, register and enquiries; idempotent enquiry submission; no account enumeration on login |
| **Tests** | Vitest unit tests for formatters, validation, the API envelope and the rate limiter |
| **SEO** | Metadata API, Open Graph, canonical URLs, `sitemap.xml`, `robots.txt`, security headers |

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

### 4. Create and seed the database

```bash
npm run db:setup
```

This runs `prisma db push` (creates `prisma/dev.db`) and seeds:

| Account | Password | Role |
|---------|----------|------|
| `admin@apex.com` | `Password123!` | admin |
| `customer@apex.com` | `Password123!` | customer |

It also seeds 6 vehicles, 3 membership plans, 3 products and one enquiry.

### 5. Run

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

## Switching to Postgres

1. Change the provider in `prisma/schema.prisma`:

   ```prisma
   datasource db {
     provider = "postgresql"
     url      = env("DATABASE_URL")
   }
   ```

2. Point `DATABASE_URL` at your server (Neon, Supabase, RDS, Railway, …):

   ```
   DATABASE_URL="postgresql://user:password@host:5432/apex?sslmode=require"
   ```

3. `npm run db:push && npm run db:seed`

Nothing else changes — the schema avoids SQLite-only types by storing status columns as
`String` and structured payloads as JSON text, both of which map cleanly to Postgres.

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
