# 03 — DOCUMENTATION STANDARD

Ab har product mein 33-38 `.md` files hain. **Zyada files = behtar docs nahi.** Buyer ko wo docs chahiye jo kaam aayein. Neeche ek saaf, chhota, professional set hai.

## 1. Docs ka structure

```
/
├─ README.md                  # 1-page: kya hai, quick start, links
├─ LICENSE / COMMERCIAL_LICENSE.md
├─ CHANGELOG.md               # Keep a Changelog format
├─ SECURITY.md                # vulnerability kaise report karein
├─ CONTRIBUTING.md            # (agar open to contributions)
└─ docs/
   ├─ 01-getting-started.md
   ├─ 02-configuration.md        # har env var ki table
   ├─ 03-architecture.md
   ├─ 04-database-and-migrations.md
   ├─ 05-authentication.md
   ├─ 06-payments.md
   ├─ 07-deployment/
   │   ├─ docker.md
   │   ├─ vps-nginx.md
   │   ├─ aws.md
   │   └─ render-railway.md
   ├─ 08-customization.md        # theme, branding, modules
   ├─ 09-api.md  (+ openapi.yaml)
   ├─ 10-testing.md
   ├─ 11-troubleshooting.md      # FAQ + common errors
   ├─ 12-upgrade-guide.md
   ├─ 13-backup-restore.md
   ├─ 14-compliance.md           # GDPR, cookies, data export/delete
   └─ 15-support-policy.md
```

Marketplace/seller ke liye alag (buyer ko nahi dikhana):
`/seller/` -> LEMON_SQUEEZY_SELLER_KIT, BRAND_GUIDELINES, listing copy, screenshots

## 2. Har doc ke rules

1. **Pehle 3 line mein** batao ye doc kis liye hai aur kitna waqt lagega.
2. **Copy-paste commands**, har command ke saath expected output.
3. **Har step verify** ho sake: "Ye chala to aap ko ye dikhna chahiye".
4. Screenshots/GIF jahan UI step ho.
5. **Warnings** sirf zaroori jagah: `> ⚠️ Warning` / `> 💡 Tip`.
6. Versions likho (Node 22, Postgres 16...).
7. Har doc ke aakhir mein "Next step" link.
8. Docs ko CI mein check karo: broken links, markdown lint, code blocks test.

## 3. README template

```md
# ProductName
> Ek line ka wada.

![screenshot](docs/img/hero.png)

**Live demo:** URL (demo@product.com / Demo#12345)

## Features
- ...

## Quick start (5 minute)
\`\`\`bash
git clone ...
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
\`\`\`
Kholo http://localhost:5173

## Tech stack
React 19, Vite, Tailwind | Node 22, Express | PostgreSQL, Redis

## Docs
Getting started - Configuration - Deployment - API - Support

## License
Commercial license, details in COMMERCIAL_LICENSE.md
```

## 4. `02-configuration.md` ka template (env table)

| Variable | Zaroori? | Default | Example | Kya karta hai |
|---|---|---|---|---|
| `DATABASE_URL` | Haan | — | `postgres://u:p@db:5432/app` | Main DB |
| `JWT_SECRET` | Haan | — | 64+ random chars | Access token sign |
| `JWT_REFRESH_SECRET` | Haan | — | 64+ random chars | Refresh token sign |
| `REDIS_URL` | Nahi | in-memory | `redis://redis:6379` | Cache + rate limit |
| `SMTP_HOST` | Nahi | — | `smtp.sendgrid.net` | Email sending |
| ... | | | | |

Har variable ka section: **kahan se milega** (e.g. Google Cloud Console link), **kaise generate karein** (`openssl rand -hex 32`).

## 5. `05-authentication.md` mein kya ho

- Flow diagram (register -> verify -> login -> refresh -> logout)
- Google/GitHub OAuth setup, step-by-step with screenshots (redirect URI ka format)
- 2FA enable/disable/recovery codes
- Roles & permissions table, naya role kaise banayein
- Security notes (token lifetime, cookie flags)

## 6. `07-deployment` mein kya ho

Har platform ke liye: prerequisites -> steps -> env -> domain + SSL -> verify -> rollback.
- Docker Compose (production overrides)
- VPS + Nginx + Certbot + systemd/PM2
- Managed DB, Redis
- Zero-downtime migration order: **backup -> migrate -> deploy -> smoke test**

## 7. `11-troubleshooting.md` format

```md
### "ECONNREFUSED 5432"
**Wajah:** Postgres start nahi hua ya galat host.
**Hal:** 1) `docker compose ps` 2) `DATABASE_URL` mein host `db` rakho (localhost nahi)
```
Kam az kam 20 common errors.

## 8. CHANGELOG (Keep a Changelog)

```md
## [1.2.0] - 2026-01-15
### Added
### Changed
### Fixed
### Security
### Migration notes   <- Breaking ho to yahan batao
```
Semantic versioning: MAJOR.MINOR.PATCH.

## 9. Buyer documentation ka asal maqsad

Ek buyer 3 sawal poochta hai:
1. **Chalaun kaise?** -> Getting started (15 min)
2. **Apna kaise banaun?** -> Customization
3. **Live kaise karun aur safe kaise rakhun?** -> Deployment + Security + Backup

Agar in 3 ka jawab 3 doc mein mil jaye to docs kamyab hain.

## 10. Premium doc extras

- Video walkthroughs (Loom/YouTube, 5-10 min har topic)
- Architecture diagrams (Mermaid, repo mein hi render)
- Postman collection
- "Recipes": 10 common customizations step-by-step (naya field, naya role, naya payment gateway, naya language)
- Public docs site (Docusaurus/VitePress) with search
- Seller side: demo credentials, refund policy, support SLA

## 11. Legal docs (templates, lawyer se review zaroor karwao)

- Privacy Policy, Terms of Service, Cookie Policy, DPA template
- Third-party licenses (`THIRD_PARTY_NOTICES` auto-generate: `license-checker`)
- Commercial license: kitne projects, redistribution allowed ya nahi, refund terms

> Main lawyer nahi hoon; legal templates sirf shuruaat hain, bechne se pehle kisi qanooni mahir se zaroor check karwayein.

## 12. Docs ka checklist (release se pehle)

- [ ] Naye developer ne sirf README parh ke product chala liya (kisi aur se test karwao)
- [ ] Har env var documented
- [ ] Har command test shuda
- [ ] Koi broken link nahi
- [ ] Screenshots current version ke hain
- [ ] CHANGELOG update
- [ ] Upgrade guide likha
