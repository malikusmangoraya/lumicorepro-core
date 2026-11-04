# Customization Guide — make BlogForge yours

Everything a buyer needs to rebrand, configure and monetize the package.
Follow this top-to-bottom; each section is independent.

## 1. Rename the brand

| Where | What to change |
|---|---|
| `frontend/src/components/common/GlassNavbar.jsx`, `ModernFooter.jsx`, `UniqueLogo.jsx` | Brand name prop + logo colors |
| `frontend/index.html` | `<title>`, meta description, OG/Twitter tags, JSON-LD `name` |
| `frontend/src/App.jsx` | `<GlassNavbar brand="...">`, `<ModernFooter brand="...">` |
| `backend/.env.example` / production env | `BRAND_NAME` |

Then rebuild (`cd frontend && npm run build`) — the demo URLs in
`README.md`/`DEPLOYMENT.md` are documentation only, the app reads none of them.

## 2. Change the color system

Tailwind tokens live in `frontend/tailwind.config.js` (`brand-primary`,
`brand-accent`, surfaces in `slate`). Change the two brand tokens and rebuild;
no hardcoded hex is used in components.

## 3. Languages / RTL

- UI strings live in `frontend/src/i18n.js` and `frontend/src/i18n/locales/*.json`.
- RTL is already designed for (`dir="rtl"` support, logical CSS properties).
- Add a locale: copy `en.json`, translate, register it in `i18n.js`, add the
  language toggle entry in `GlassNavbar.jsx`.

## 4. AI provider

Set any one key in the backend environment:

| Key | Effect |
|---|---|
| `OPENAI_API_KEY` | Real generation (default provider) |
| `OPENROUTER_API_KEY` / `DEEPSEEK_API_KEY` / `GEMINI_API_KEY` | Alternatives |
| none of the above | Built-in deterministic demo generator (good for demos/QA) |

Store keys in Vercel env or at runtime via the keyVault admin route — never in
client code.

## 5. Turn on real payments

This build ships with honest evaluation semantics: tier pages label credits as
evaluation grants and the demo top-up endpoint answers **402 TOPUP_DISABLED**.

1. Connect a payment provider (Stripe/PayPal), add webhook + price IDs.
2. Create real credit products and satisfy tax/VAT requirements for your
   markets (EU VAT, US sales tax, Pakistan FBR as applicable).
3. Update the Pricing page copy from "evaluation tiers" to real pricing
   (`frontend/src/pages/Pricing.jsx`) — the copy must match your legal obligation.
4. Flip in the backend env: `ENABLE_DEMO_TOPUP=1` only if you still want the
   free grant active during rollout.

## 6. Deployment

Full runbook with the exact commands: [DEPLOYMENT.md](../DEPLOYMENT.md)
(Vercel + Neon). One-command local run: [INSTRUCTIONS.md](../INSTRUCTIONS.md).

## 7. Security posture (what a buyer inherits)

- JWT auth (7-day tokens, bcrypt 12, fail-closed secret > 32 chars)
- CORS allow-list (`CORS_ORIGINS`) — no wildcard
- Rate limits: default 200/15min global, 20/h auth, 30/h AI
- `/api/v1/ai/*` requires JWT (it spends your provider keys)
- All destructive/credit ops validated server-side; transactions for the
  multi-table register path
- `/api/v1/health` checks the real DB connection
- Frontend exports run through an allow-list HTML sanitizer (no LLM-payload XSS)

## 8. Quality gate

Re-run the included tests after any change:

```bash
cd backend  && npm test          # isolated; needs TEST_DATABASE_URL
cd frontend && npm test          # node --test, no DB needed
cd frontend && npm run build     # production bundle
```

Market-audit endpoint (external check): `POST /api/market-audit` — see
[MARKET_PERFORMANCE.md](MARKET_PERFORMANCE.md).
