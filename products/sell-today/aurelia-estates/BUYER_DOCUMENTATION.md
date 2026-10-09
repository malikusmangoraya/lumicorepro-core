# 📘 Aurelia Estates — Customer Setup & Quick Start Guide

Thank you for purchasing **Aurelia Estates**! Follow this 3-step guide to launch your application.

---

## 1. Quick Installation (3 Minutes)

### Prerequisites

- Node.js 18+ or 20+ installed.

### Step 1: Install Dependencies

```bash
# Install frontend
cd frontend
npm install

# Install backend (if using the API)
cd ../backend
npm install
```

### Step 2: Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# In frontend:
cp .env.example .env

# Configure your Lemon Squeezy Store (optional):
# VITE_LEMONSQUEEZY_STORE_ID=your_store_id
```

### Step 3: Start Development Server

```bash
# In frontend:
npm run dev
```

Visit `http://localhost:5173` to see your live site!

---

## 2. Connecting Lemon Squeezy Payments

Lemon Squeezy is the **merchant of record**, so sales tax, VAT, invoices and payouts are handled for you. Connect it once and both the demo and the live site use it.

### 2.1 Create the product

1. Create an account at [app.lemonsqueezy.com](https://app.lemonsqueezy.com) and activate the store (identity verification).
2. Create one product with a variant per tier (Starter / Pro / Enterprise). Copy each **Variant ID**.
3. Copy the **Store ID** from *Settings → Stores* and, for server-created checkouts, an **API key** from *Settings → API*.

### 2.2 Add the keys

`backend/.env` (the API process):

```bash
LEMONSQUEEZY_STORE_ID=123456
LEMONSQUEEZY_STORE_URL=https://acme.my.lemonsqueezy.com
LEMONSQUEEZY_WEBHOOK_SECRET=            # Settings -> Webhooks -> Signing secret
LEMONSQUEEZY_VARIANT_STARTER=111111     # one variant id per pricing tier
LEMONSQUEEZY_VARIANT_PRO=222222
LEMONSQUEEZY_VARIANT_ENTERPRISE=333333
LEMONSQUEEZY_API_KEY=                   # optional, only for API-created checkouts
```

`frontend/.env` (the storefront — Vite reads this at build time):

```bash
VITE_LEMONSQUEEZY_STORE_ID=123456
VITE_LEMONSQUEEZY_STORE_URL=https://acme.my.lemonsqueezy.com
VITE_LEMONSQUEEZY_VARIANT_ID=111111
```

Set `PAYMENT_GATEWAYS_ENABLED=stripe,paypal,lemonsqueezy` (or `all` while testing every gateway).

### 2.3 Point the pricing table at the variants

Each plan in `frontend/src/components/ecommerce/PricingTable.jsx` may carry a `variantId`; without it the app falls back to `LEMONSQUEEZY_VARIANT_<PLAN>` from the backend, and finally to `VITE_LEMONSQUEEZY_VARIANT_ID`.

### 2.4 Register the webhook

In *Settings → Webhooks* add:

| Field | Value |
| --- | --- |
| URL | `https://your-domain.com/api/lemonsqueezy/webhook` |
| Events | `order_created`, `order_refunded`, `subscription_created`, `subscription_updated`, `subscription_cancelled`, `license_key_created`, `license_key_updated` |
| Signing secret | copy into `LEMONSQUEEZY_WEBHOOK_SECRET` |

Deliveries are verified with HMAC-SHA256 (`X-Signature`), replayed deliveries are ignored through the webhook ledger, and a failed step returns a non-2xx so the sender retries.

### 2.5 What the endpoints do

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/lemonsqueezy/config` | GET | Store id, checkout mode, webhook URL (public) |
| `/api/lemonsqueezy/checkout` | POST | Hosted checkout URL for a plan or an open order |
| `/api/lemonsqueezy/webhook` | POST | Signed purchase, refund and subscription events |

### 2.6 Other gateways in the box

Stripe, PayPal, Paddle, Razorpay, Square, Mollie, Flutterwave, Mercado Pago, LiqPay, Paytm and bKash are already implemented (`backend/services/payment/`). Add their keys to `backend/.env` and list them in `PAYMENT_GATEWAYS_ENABLED`.

Without any keys the pricing buttons open a clearly labelled preview dialog, so the demo on GitHub Pages keeps working before the store is connected.

---

## 3. 1-Click Production Deployment

- **Vercel**: Import your repository, select Vite preset, and click Deploy.
- **Netlify**: Connect your Git repo; `netlify.toml` is pre-configured.
- **Docker**: Run `docker compose up -d` for an isolated full-stack instance.
