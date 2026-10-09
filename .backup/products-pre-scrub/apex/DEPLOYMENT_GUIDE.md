# Deployment Guide — apex

## Recommended Deployment Order

1. **Vercel** — free+, Global Edge Network (40+ regions)
2. **Railway** — $5/mo+, US West, US East, EU West, AP Southeast
3. **Render** — free+, US, EU, Singapore
4. **AWS** — pay-as-you-go, 30+ regions globally

## Quick Deploy (Recommended: Railway)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Link project
railway link

# 4. Set environment variables
railway variables set NODE_ENV=production
railway variables set MONGODB_URI='your_uri'
railway variables set JWT_SECRET='<node -e "console.log(require('crypto').randomBytes(48).toString('hex'))">'
railway variables set STRIPE_SECRET_KEY='sk_live_xxx'
railway variables set STRIPE_WEBHOOK_SECRET='whsec_xxx'

# 5. Deploy
railway up
```

## Pre-Deploy Checklist

- [ ] All environment variables set in target platform
- [ ] Database created and connection string configured
- [ ] SMTP/email service configured
- [ ] Domain name pointed to deployment
- [ ] SSL certificate provisioned (usually automatic)
- [ ] Stripe webhook endpoint registered: `POST /api/payments/webhook`
- [ ] Stripe live mode keys configured (not test keys)
- [ ] Sentry DSN configured for error monitoring
- [ ] CDN configured (Cloudflare recommended)
- [ ] Health check endpoint working: `GET /api/health`

## Platform Comparison

| Platform      | Best For              | Cost          | Regions                                 |
| ------------- | --------------------- | ------------- | --------------------------------------- |
| Vercel        | saas, portfolio       | free+         | Global Edge Network (40+ regions)       |
| Railway       | ecommerce, saas       | $5/mo+        | US West, US East, EU West, AP Southeast |
| Render        | ecommerce, saas       | free+         | US, EU, Singapore                       |
| AWS           | enterprise, fintech   | pay-as-you-go | 30+ regions globally                    |
| GCP Cloud Run | saas, fintech         | pay-as-you-go | 35+ regions globally                    |
| DigitalOcean  | ecommerce, restaurant | $12/mo+       | NYC, AMS, SGP, BLR, LON, FRA, TOR       |
