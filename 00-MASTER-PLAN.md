# 00 — MASTER PLAN (Pehle ye parho)

Is pack ka maqsad: aapke 11 products ko "AI-generated template" se **international-grade, bechne ke qabil (sellable) products** banana.

## Pack ki files

| File | Kis liye |
|---|---|
| `00-MASTER-PLAN.md` | Roadmap, phases, priority, kaam ka order |
| `01-ARCHITECTURE-AND-LAYOUT.md` | Repo layout, folder structure, shared core, code rules |
| `02-FEATURES-AND-BENEFITS.md` | Har product ke niche features, buyer ka faida, Pro/Premium tiers |
| `03-DOCUMENTATION-STANDARD.md` | Docs kaisi hon, har doc ka template |
| `04-TASK-DETAILS.md` | Har kaam ki detail: steps, Definition of Done, Pro/Premium version |
| `05-QUALITY-SECURITY-COMPLIANCE.md` | Tests, security, a11y, GDPR, performance, CI/CD |
| `06-env.example.FULL` | Mukammal backend `.env.example` template |
| `07-env.frontend.example` | Frontend `.env.example` (sirf `VITE_` keys) |

## Sab se pehle haqiqat (Honest baseline)

1. 11 products ka stack, routes (33), models (27) aur auth **identical** hain. Buyer ko ye "ek template, 11 skins" lagega.
2. Document mein likha "100/100 audit" ek **static checker** ka result lagta hai. Is ka matlab ye nahi ke product production-ready hai.
3. Tests, migrations, complete env docs, a11y aur GDPR abhi missing hain.
4. Jo claims "verify kiye" likhe hain (HTTP 200, 66 checks) unhein khud dobara verify karein, sirf AI ki report par bharosa na karein.

## Strategy: "Core + Niche"

11 alag codebases maintain karna impossible hai. Solution:

```
shared-core/        <- ek jagah: auth, payments, i18n, security, UI kit, CI
products/
  claimflow/        <- sirf niche-specific cheezein
  flowpilot/
  ...
```

Core mein ek bug fix = 11 products mein fix. Is ka tareeqa `01-ARCHITECTURE-AND-LAYOUT.md` mein hai.

## Phases (Roadmap)

### Phase 0 — Safai (1 hafta)
Bina naye feature ke, sirf jo galat hai wo theek karo.
- [ ] Backend `.env.example` mukammal (file 06 use karo)
- [ ] Frontend `.env.example` se 7 server secrets hatao (file 07)
- [ ] `mongoose` unused dependency hatao (prestige-studio, resupro)
- [ ] resupro mein zustand add ya sab mein consistent karo
- [ ] Har product ke naam ke hisab se bacha hua template code hatao (e.g. ClaimFlow se `Doctor`, `Cart`, `Wishlist`)
- [ ] `npm audit` clean, Dependabot on

### Phase 1 — Foundation (2-3 hafte) — **sirf 1 pilot product par**
Pilot: **ClaimFlow** ya **FlowPilot** (jo aap ka sab se strong niche ho).
- [ ] Real migrations (Umzug/Sequelize CLI)
- [ ] Seed data (demo)
- [ ] Automated tests (unit + integration + E2E)
- [ ] OpenAPI docs
- [ ] GDPR basics
- [ ] A11y pass (WCAG 2.2 AA)

### Phase 2 — Niche Depth (2-3 hafte per product)
Har product ko apne niche ke asal features do (file 02).

### Phase 3 — Rollout (1-2 hafte)
Pilot ke fixes baqi 10 mein `shared-core` ke zariye lagao.

### Phase 4 — Premium Layer (ongoing)
Multi-tenancy, white-label, video guides, support plan, public roadmap.

## Priority Matrix

| Priority | Kaam | Asar (Impact) | Mehnat |
|---|---|---|---|
| P0 | env fix, secrets leak fix | Bohat zyada | Kam |
| P0 | Migrations | Bohat zyada | Medium |
| P0 | Tests (auth + payments) | Bohat zyada | Zyada |
| P1 | Niche features | Bohat zyada | Zyada |
| P1 | GDPR + a11y | Zyada | Medium |
| P2 | OpenAPI, Sentry | Medium | Kam |
| P3 | White-label, video, roadmap | Medium | Medium |

## Sab se zaroori salah

**11 products ek saath bechne se behtar hai pehle 3 ko mukammal karo.** Envato/Lemon Squeezy par reviews aur refunds quality se tay hote hain, quantity se nahi. Baqi 8 ko "coming soon" rakho jab tak pilot ready na ho.

## Success Metrics (kaise pata chalega kaam ho gaya)

- Naya developer 15 minute mein `docker compose up` se product chala le
- Tests ka coverage: auth/payments ≥ 80%, overall ≥ 60%
- Lighthouse: Performance ≥ 90, Accessibility ≥ 95, Best Practices ≥ 95, SEO ≥ 95
- `npm audit --omit=dev` mein 0 high/critical
- Har product mein kam az kam 5 niche-specific features jo doosre product mein nahi
- Demo site par login credentials aur sample data maujood
