# Migration & Exit Path — No Lock-in

> LumicorePro produces standard, portable code. This document is the guarantee —
> what happens when you stop using the generator entirely.

## 1. What you actually receive

Every generation delivers a **ZIP archive** containing a complete, conventional
project:

```
<site>/
├── frontend/        # React 19 + Vite + Tailwind (standard, npm-runnable)
├── backend/         # Express + Postgres (optional, standard npm-run)
├── mobile/          # (optional) React Native scaffold
└── *.md             # COMPLIANCE.md, SECURITY-CHECKLIST.md, docs, deploy guides
```

Nothing in the output requires the LumicorePro agent to run. There is:

- **No proprietary runtime** — plain Node/Vite/Express.
- **No hidden API calls** — the generated site talks only to its own backend and
  the services you configure (Stripe, etc.). The AI agent is never called at
  runtime.
- **No telemetry, tracking or license gate** in the generated code.

## 2. Running without the generator

All commands are standard tooling:

```bash
# Frontend
cd frontend && npm install && npm run dev        # or npm run build

# Backend (if included)
cd backend && npm install && npm run dev         # Express + Postgres

# Databases
postgres  # schema is exported SQL in database/migrations (if included)
```

Hosting: the included deploy recipes (Vercel, Railway, Render, AWS, GCP)
require no LumicorePro account. `gh repo create` + push works.

## 3. Continuing to improve the site

You are free to:

- Edit the code in any IDE;
- Add your own CI/CD (the project ships a GitHub Actions template);
- Use LumicorePro again later — the iteration loop
  (`POST /api/iterate`) re-edits *only the affected files* and re-verifies,
  still keeping the rest of your manual edits byte-identical.

## 4. What would be hard to migrate (honest limits)

| Area | Constraint | Workaround |
|---|---|---|
| Visually-rich custom layouts | Generated structure is template-based | Edit component code directly; full source is yours |
| Non-React stacks | Frontend is React/Vite/Tailwind | Rewrite or keep as-is — it's standard React |
| No-code users | Requires some code familiarity to edit | Use the iteration-chat loop instead |
| Serverless-specific logic | Generated backend is Express+Postgres | Deploy on Railway/Render/AWS EC2, or refactor to functions |

## 5. Data, keys and cost

| Item | Status |
|---|---|
| Your API keys | Live in your `.env` only; the agent never stores or sends them anywhere else |
| Generated site data | Lives in your Postgres/MySQL under your control |
| Per-seat/royalty fees | None. One self-hosted stack, no license gate |
| Estimation guardrail | `estimate_running_cost` in the report tells you expected hosting cost up front, so you never get a surprise bill |

## 6. TL;DR

If you stop using LumicorePro tomorrow, the code still builds, deploys and runs
with standard tooling, on any host, with no license, no account, and no
dependency on the generator. **Output is yours, forever.**