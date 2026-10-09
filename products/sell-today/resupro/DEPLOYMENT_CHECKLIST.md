# ✅ PRODUCTION DEPLOYMENT CHECKLIST — RESUPRO-002

---

## 🔐 Security (Before going live)

- [ ] Change ALL default passwords and JWT secrets in `.env`
- [ ] Enable HTTPS / SSL certificate (Let's Encrypt or Cloudflare)
- [ ] Set `NODE_ENV=production` on backend
- [ ] Configure CORS to only allow your production domain
- [ ] Enable rate limiting on all API endpoints
- [ ] Run OWASP ZAP security scan
- [ ] Ensure `.env` files are in `.gitignore` — NEVER commit secrets
- [ ] Review all admin routes — require auth middleware

## ⚡ Performance (Before going live)

- [ ] Run `npm run build` — check bundle size < 500KB gzipped
- [ ] Enable Cloudflare CDN or AWS CloudFront
- [ ] Compress images to WebP format
- [ ] Test Lighthouse score ≥ 90 on mobile
- [ ] Enable gzip/brotli compression on Nginx
- [ ] Add `Cache-Control` headers for static assets

## 🌐 SEO & Discoverability

- [ ] Submit `sitemap.xml` to Google Search Console
- [ ] Verify `robots.txt` is accessible at `/robots.txt`
- [ ] Add all Open Graph images (1200×630px)
- [ ] Test Open Graph with https://developers.facebook.com/tools/debug/
- [ ] Test Twitter Card with https://cards-dev.twitter.com/validator
- [ ] Add Google Analytics 4 / Plausible tracking code
- [ ] Add JSON-LD structured data (already generated in `structured-data.json`)

## 📱 Mobile & PWA

- [ ] Test on real mobile devices (iOS Safari + Android Chrome)
- [ ] Verify PWA install prompt works (check `manifest.json`)
- [ ] Test offline mode if PWA enabled
- [ ] Check tap target sizes (minimum 44×44px)
- [ ] Test WhatsApp float button on mobile

## 💳 Payments (if applicable)

- [ ] Switch Stripe from TEST keys to LIVE keys
- [ ] Test full checkout flow with real card
- [ ] Set up Stripe webhook endpoint and verify signature
- [ ] Configure Stripe for correct currency (PKR/USD/EUR)
- [ ] Test refund flow

## 🗄️ Database

- [ ] Run `schema.sql` on production PostgreSQL
- [ ] Set up automated database backups (daily minimum)
- [ ] Create read replica for analytics queries
- [ ] Test database connection pool under load

## 📧 Email & Notifications

- [ ] Configure SMTP (SendGrid/AWS SES/Mailgun) — not localhost
- [ ] Test transactional emails: welcome, reset password, order confirm
- [ ] Set up email monitoring for bounces and spam complaints
- [ ] WhatsApp Business API setup (if using Twilio/360dialog)

## 🔍 Monitoring & Alerts

- [ ] Set up Sentry for error tracking (frontend + backend)
- [ ] Configure uptime monitoring (UptimeRobot / Better Uptime)
- [ ] Set up server resource alerts (CPU > 80%, RAM > 85%)
- [ ] Enable CloudFlare Analytics or similar

## 🚀 CI/CD (GitHub Actions — already generated)

- [ ] Add `VERCEL_TOKEN` to GitHub Secrets
- [ ] Add `RENDER_DEPLOY_HOOK_URL` to GitHub Secrets
- [ ] Add `VITE_API_URL` to GitHub Secrets
- [ ] Test full CI pipeline on a feature branch first

## 🌍 International / Compliance

- [ ] GDPR cookie consent banner is visible on first visit (EU)
- [ ] Privacy Policy and Terms of Service pages published
- [ ] CCPA compliance if serving California users
- [ ] PCI DSS compliance if storing card data (use Stripe — never store raw cards)
- [ ] Verify multilingual content if i18n enabled

## ✅ Final Launch Check

- [ ] All environment variables set in production
- [ ] Test complete user journey: signup → browse → purchase/book → confirm
- [ ] Test on 3 browsers: Chrome, Safari, Firefox
- [ ] Test on iOS and Android mobile
- [ ] Set up domain DNS (A record or CNAME to hosting)
- [ ] Verify HTTPS works and HTTP redirects to HTTPS
- [ ] Announce launch on social media with WhatsApp status 🎉

---

_Deployment checklist generated for production readiness._
