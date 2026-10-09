# 05 — QUALITY, SECURITY, COMPLIANCE, CI/CD

## 1. Security checklist (OWASP ke mutabiq)

### Authentication & Session
- [ ] Password hashing: argon2id ya bcrypt cost ≥ 12
- [ ] Password policy: min 10 chars, breached-password check (HaveIBeenPwned k-anonymity)
- [ ] Access token 15 min, refresh token 7-30 din, **rotation + reuse detection**
- [ ] Cookies: `httpOnly; Secure; SameSite=Lax/Strict`
- [ ] Login brute-force lockout (account + IP), generic error ("email ya password galat")
- [ ] 2FA recovery codes (hashed store)
- [ ] TOTP secret database mein **encrypted** (AES-256-GCM)
- [ ] Password reset token: one-time, 15-60 min, hashed in DB
- [ ] Logout par refresh token revoke; "sab devices se logout"
- [ ] OAuth: `state` parameter + PKCE, email verified check

### Authorization
- [ ] Har endpoint par authz check (default deny)
- [ ] IDOR test: user A user B ka data nahi dekh sakta (`/claims/:id` par ownership check)
- [ ] Multi-tenant: har query mein `organization_id`

### Input / Output
- [ ] zod validation har endpoint
- [ ] Parameterized queries (Sequelize use, raw SQL se bacho)
- [ ] XSS: React default escape, `dangerouslySetInnerHTML` na ho (ya DOMPurify)
- [ ] File upload: MIME + magic bytes, size limit, random name, alag storage (S3), serve karte waqt `Content-Disposition`
- [ ] SSRF: user-supplied URLs par allowlist
- [ ] Mass assignment: sirf allowed fields

### Transport / Headers
- [ ] HTTPS only + HSTS
- [ ] CSP (strict), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`
- [ ] CORS sirf known origins
- [ ] CSRF: SameSite + double-submit/token jahan cookies auth hai

### Payments & Webhooks
- [ ] Webhook signature verification (har gateway)
- [ ] Idempotency (event id store, duplicate ignore)
- [ ] Payment amount server-side calculate, client par bharosa nahi
- [ ] Card data kabhi server par nahi (hosted checkout/Elements, PCI SAQ-A)
- [ ] Replay protection (timestamp tolerance)

### Secrets & Supply chain
- [ ] `.env` gitignore, secrets scanning (gitleaks) CI mein
- [ ] `npm audit` CI mein, Dependabot/Renovate
- [ ] Lockfile commit, Docker base images pinned + Trivy scan
- [ ] SBOM generate (CycloneDX) — Premium
- [ ] Docker: non-root user, read-only filesystem jahan ho sake

### Logging
- [ ] Password/token/card kabhi log mein nahi (redaction)
- [ ] Audit log append-only

**Pro:** Pen-test checklist (OWASP ZAP baseline CI mein).
**Premium:** Third-party penetration test report, security.txt, bug bounty policy.

---

## 2. Testing standard

| Level | Kab chale | Block merge? |
|---|---|---|
| Lint + typecheck | Har commit | Haan |
| Unit | Har PR | Haan |
| Integration (DB ke saath) | Har PR | Haan |
| E2E (critical flows) | Har PR / nightly | Haan |
| Security scan | Har PR | High/Critical par haan |
| Lighthouse + axe | Har PR | Threshold se neeche par haan |
| Load test (k6) | Release se pehle | Nahi (report) |

**Critical E2E flows (har product):**
1. Register -> email verify -> login
2. Login + 2FA
3. Password reset
4. Niche core flow (e.g. claim submit -> admin review -> status update)
5. Checkout/subscribe (test mode) -> webhook -> access mila
6. Admin: user role change
7. Language switch + RTL
8. Delete account / export data

---

## 3. Performance budgets

| Metric | Target |
|---|---|
| LCP | < 2.5s (mobile 4G) |
| INP | < 200ms |
| CLS | < 0.1 |
| First-load JS (gzip) | < 150 KB (aap already 105-110 KB) |
| API p95 | < 500ms |
| API error rate | < 1% |

Hero video: ≤ 500 KB, poster image, `preload="none"`, mobile par band ya static image.

---

## 4. Accessibility checklist (WCAG 2.2 AA)

- [ ] Keyboard-only poora app chalta hai
- [ ] Focus visible aur logical order
- [ ] Contrast 4.5:1 / 3:1
- [ ] Form labels + error announcements
- [ ] Alt text, captions on video
- [ ] Target size ≥ 24x24px (mobile 44px behtar)
- [ ] `prefers-reduced-motion`, `prefers-color-scheme`
- [ ] Zoom 200% par layout na toote
- [ ] Screen reader pass (NVDA/VoiceOver)
- [ ] Accessibility statement page

---

## 5. Privacy / Compliance

| Mamla | Kya karna hai |
|---|---|
| GDPR (EU/UK) | Consent, export, delete, retention, DPA, breach process (72 ghante) |
| CCPA (California) | "Do not sell/share" option, access/delete |
| Cookies (ePrivacy) | Analytics/marketing se pehle consent |
| PCI-DSS | Hosted checkout use karo, SAQ-A |
| Accessibility | WCAG 2.2 AA, EAA (EU) |
| Licensing | `THIRD_PARTY_NOTICES` auto-generate, GPL dependency check |
| Tax / MoR | Lemon Squeezy merchant of record hai, buyer ke liye VAT handle |
| Industry specific | ClaimFlow (insurance), Meridian (finance) mein regulatory disclaimers: "ye software compliance guarantee nahi deta" |

> Main lawyer nahi hoon. Bechne se pehle legal templates kisi professional se check karwayein.

---

## 6. CI/CD pipeline (GitHub Actions)

```yaml
name: ci
on: [push, pull_request]
jobs:
  quality:
    steps:
      - checkout
      - setup node 22 + pnpm cache
      - install --frozen-lockfile
      - lint, typecheck
      - env-check (script: .env.example vs code)
      - unit tests + coverage
  integration:
    services: postgres, redis
    steps: migrate -> seed -> supertest
  e2e:
    steps: docker compose up -> playwright test
  security:
    steps: npm audit --omit=dev, gitleaks, trivy (docker image), OWASP ZAP baseline
  perf-a11y:
    steps: build -> bundle budget -> lighthouse-ci -> axe
  deploy: (main branch only, sab pass hone par)
    steps: build -> gh-pages / registry push -> smoke test
```

**Release workflow:** tag `v1.x.x` -> changelog generate -> ZIP + SHA256 -> GitHub Release -> (optional) Lemon Squeezy upload.

---

## 7. Docker / Infra standard

- Multi-stage builds, pinned versions, non-root user
- `HEALTHCHECK` har service par
- `docker-compose.yml` (dev) + `docker-compose.prod.yml` (prod: restart policy, resource limits, no exposed DB port)
- Postgres backup: `pg_dump` cron + restore test (jo backup restore na ho wo backup nahi)
- Redis persistence on/off ka saaf bayan
- Reverse proxy (Nginx/Caddy) example config with TLS

---

## 8. Pre-release QA checklist (har product, har release)

**Install**
- [ ] Fresh machine par README se 15 min mein chala
- [ ] Docker aur non-Docker dono

**Functionality**
- [ ] 8 critical flows pass
- [ ] Sab payment gateways: configured/not-configured dono behave sahi
- [ ] Email bhejna (SMTP test)
- [ ] OAuth Google/GitHub

**Quality**
- [ ] Tests green, coverage threshold
- [ ] Lighthouse thresholds
- [ ] axe 0 serious
- [ ] `npm audit` 0 high/critical
- [ ] gitleaks clean

**Content**
- [ ] Koi "lorem ipsum", "TODO", "Doctor/Cart" (irrelevant) nahi
- [ ] Sab 14 languages mein 0 missing keys
- [ ] Docs complete, links theek

**Packaging**
- [ ] ZIP mein `node_modules`, `.env`, `.git` nahi
- [ ] LICENSE + THIRD_PARTY_NOTICES maujood
- [ ] Version + CHANGELOG match

---

## 9. "100/100 audit" ke baare mein

Aap ka maujooda audit 66 static checks karta hai. Ye achhi shuruaat hai, lekin:
- Ye **runtime behaviour** nahi parakhta (kya login asal mein chalta hai?)
- Ye **security** aur **a11y** ka badal nahi hai
- AI tool ka "100/100" khud tasdeeq nahi

Audit ko ye checks add karke mazboot karo: env parity, route-vs-OpenAPI parity, unused deps, migration up/down, bundle budgets, hardcoded secrets, i18n key coverage, aur sab se zaroori **real E2E tests**.

---

## 10. Support policy template

```md
## Support
- Channels: email support@..., (Pro+) private Discord
- Response: Standard 3 working days / Pro 48h / Premium 24h
- Includes: install help, bug fixes, answers about docs
- Excludes: custom development, third-party service issues, hosting setup (paid add-on)
- Updates: Standard 3 months / Pro 12 months / Premium lifetime (minor/patch)
- Refunds: 14 din, agar product description ke mutabiq kaam na kare
```
