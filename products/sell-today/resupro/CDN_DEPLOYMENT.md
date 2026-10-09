# CDN & Deployment Configuration — resupro

## Quick Deploy

### Vercel (Recommended)

```bash
npm i -g vercel
vercel --prod
```

### Netlify

```bash
npm i -g netlify-cli
netlify deploy --prod --dir=dist
```

### Docker + Nginx

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Edge Regions

Configured for: **bom1**

## Security Headers Configured

- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `SAMEORIGIN`
- `X-XSS-Protection`: `1; mode=block`
- `Referrer-Policy`: `strict-origin-when-cross-origin`
- `Permissions-Policy`: `camera=(), microphone=(), geolocation=(self), payment=(self)`
- `Cross-Origin-Embedder-Policy`: `credentialless`
- `Cross-Origin-Opener-Policy`: `same-origin-allow-popups`
- `Cross-Origin-Resource-Policy`: `same-site`

## Cache Strategy

| Resource Type | Cache Control                                           |
| ------------- | ------------------------------------------------------- |
| hashed_assets | `public, max-age=31536000, immutable`                   |
| images        | `public, max-age=2592000, stale-while-revalidate=86400` |
| fonts         | `public, max-age=31536000, immutable`                   |
| html          | `public, max-age=0, must-revalidate`                    |
| api           | `private, no-store, no-cache`                           |
| manifest      | `public, max-age=86400`                                 |
| sw            | `public, max-age=0, must-revalidate`                    |

## Post-Deploy Checklist

- [ ] Verify SSL certificate is valid
- [ ] Test security headers at securityheaders.com
- [ ] Run Lighthouse from external network
- [ ] Verify CDN caching with `curl -I https://yourdomain.com/assets/*.js`
- [ ] Set up uptime monitoring (Better Uptime / UptimeRobot)
- [ ] Enable Cloudflare WAF if using Cloudflare
