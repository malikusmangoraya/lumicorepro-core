# 🛍️ Aurelia Estates — Lemon Squeezy & Digital Marketplace Seller Kit

This document provides ready-to-copy marketing copy, pricing recommendations, and product metadata for listing **Aurelia Estates** on **Lemon Squeezy**, **Gumroad**, **ThemeForest**, or **Creative Market**.

---

## 1. Marketplace Listing Details

- **Product Title**: Aurelia Estates — Enterprise React 19 + Tailwind SaaS & Agency Template
- **Subtitle / Pitch**: High-converting digital product with Lemon Squeezy checkout, 12+ pre-built pages, live theme switcher, multi-currency, and full Express API backend.
- **Category**: Digital Products / Website Templates / SaaS Starters / React Themes
- **Tags**: `react-19`, `vite`, `tailwind-css`, `lemon-squeezy`, `saas-template`, `dark-mode`, `landing-page`, `pricing-table`

---

## 2. Pricing Recommendations

| Tier                           | Recommended Price | Target Audience                                      |
| ------------------------------ | ----------------- | ---------------------------------------------------- |
| **Standard Commercial**        | **$49**           | Indie hackers, single client project, freelancers    |
| **Agency Unlimited**           | **$119**          | Agencies, unlimited client deployments, priority SLA |
| **Full Whitelabel / Reseller** | **$249**          | SaaS builders requiring full redistribution rights   |

---

## 3. Ready-to-Paste Lemon Squeezy Product Description

```markdown
### 🚀 Build & Launch in Hours, Not Weeks

**Aurelia Estates** is a premium, production-tested web platform engineered with **React 19**, **Vite**, and **Tailwind CSS**. It comes equipped with seamless **Lemon Squeezy overlay checkout**, monthly/annual pricing tables, interactive theme studios, and enterprise-grade accessibility.

### 🌟 Key Highlights

- ⚡ **React 19 & Vite 8**: Sub-second builds and near-instant HMR.
- 💳 **Lemon Squeezy Direct Integration**: Pre-wired checkout overlays (`lemon.js`) and webhook verification endpoints.
- 🎨 **Live Theme Studio**: Built-in floating customizer with 5 curated color palettes and dark/light modes.
- 📱 **100% Responsive & Accessible**: WCAG 2.1 AA contrast, fluid typography, and mobile drawer navigation.
- 🔒 **Full Express API Backend**: Secure order management, JWT authentication, and rate limiting.
- 🌍 **Internationalization Ready**: Multi-currency display (USD, EUR, GBP, AED, PKR) and RTL support.

### 📦 What is Included in the Download?

1. Full Clean Source Code (Frontend + Backend + DB Schemas).
2. Production Deployment Configs (1-Click Vercel, Netlify, Docker, Railway, Render).
3. Ready-to-copy Lemon Squeezy Webhook Listeners.
4. Comprehensive Setup & Customization Guide.
5. Lifetime Free Updates.
```

---

## 4. Suggested Thumbnail & Promo Graphics Prompts

- **Main Cover (1280x720)**: Clean isometric dark laptop mockup showcasing Aurelia Estates dashboard, neon cyan glowing borders, "React 19 + Lemon Squeezy Ready" badge.
- **Feature Slide 1**: Bento Grid feature showcase with smooth drop shadows.
- **Feature Slide 2**: Monthly vs Annual Pricing Table with 20% discount pill.
- **Feature Slide 3**: Live Theme Studio with 5 color swatch circles.

---

## 5. What The Buyer Sets Up After Purchase

Hand this list to the customer with the download. It is the complete key-insertion path — no code changes are required.

1. **Store identity** — `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_STORE_URL` (both in `backend/.env`, plus `VITE_LEMONSQUEEZY_STORE_ID` / `VITE_LEMONSQUEEZY_STORE_URL` in `frontend/.env`).
2. **Plans** — one `LEMONSQUEEZY_VARIANT_<PLAN>` per pricing tier, or `variantId` on each plan in `PricingTable.jsx`.
3. **Webhooks** — `LEMONSQUEEZY_WEBHOOK_SECRET` plus an endpoint at `https://their-domain/api/lemonsqueezy/webhook` for `order_created`, `order_refunded`, `subscription_created`, `subscription_updated`, `subscription_cancelled`, `license_key_created`, `license_key_updated`.
4. **Optional** — `LEMONSQUEEZY_API_KEY` to create checkouts server-side instead of using the store overlay link.
5. **Other cards** — `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET`, `PADDLE_API_KEY`, then set `PAYMENT_GATEWAYS_ENABLED` to the list you want live (`all` enables every implemented gateway while testing).
6. **Environment on the host** — with Docker, the same variables are read straight from the host `.env` (see `docker-compose.yml`), so no rebuild is needed.

Smoke test: `GET /api/lemonsqueezy/config` must report `configured: true`, and a paid order must appear as `succeeded` in the payments table.
