# 📘 Studio Lumen — Customer Setup & Quick Start Guide

Thank you for purchasing **Studio Lumen**! Follow this 3-step guide to launch your application.

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

1. Log into your [Lemon Squeezy Dashboard](https://app.lemonsqueezy.com).
2. Create a product or variant (e.g. Starter \$29, Pro \$79).
3. Copy your **Store ID** and **Variant ID**.
4. In `frontend/src/components/ecommerce/PricingTable.jsx`, update the `plans` array with your variant IDs.
5. In `backend/.env`, set `LEMONSQUEEZY_WEBHOOK_SECRET=your_secret` to receive instant purchase webhook notifications at `/api/v1/lemonsqueezy/webhook`.

---

## 3. 1-Click Production Deployment

- **Vercel**: Import your repository, select Vite preset, and click Deploy.
- **Netlify**: Connect your Git repo; `netlify.toml` is pre-configured.
- **Docker**: Run `docker compose up -d` for an isolated full-stack instance.
