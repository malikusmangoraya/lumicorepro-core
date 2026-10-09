# LumiCorePro — Product Manual

**Audience:** agencies, freelance studios and developers deploying LumiCorePro for
client work.
**Scope:** installation, configuration, day-to-day operation, marketplace
administration and troubleshooting.

---

## 1. What LumiCorePro is

LumiCorePro is a self-hosted platform for producing production-grade marketing
and commerce websites at speed. It combines four subsystems:

| Subsystem | Technology | Responsibility |
| --- | --- | --- |
| Web application | React 19 + Vite | Studio UI: generation, previews, marketplace, billing |
| API | Node.js + Express + Sequelize | Accounts, plans, orders, AI orchestration, entitlements |
| Generation engine | Python + FastAPI | 18-phase pipeline: requirement analysis → design → build → quality gates → ZIP |
| Data layer | PostgreSQL + Redis | Transactions, sessions, queues, rate limits, read cache |

Every generated website is produced by the same deterministic pipeline that the
platform itself uses for quality assurance, so output quality is measurable
rather than subjective.

---

## 2. Installation

### 2.1 Requirements

| Resource | Minimum | Recommended |
| --- | --- | --- |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB | 60 GB SSD |
| Node.js | 20 LTS | 20 LTS |
| Python | 3.11 | 3.11 |
| PostgreSQL | 14 | 16 |
| Redis | 6 | 7 |

### 2.2 Docker (recommended)

```bash
git clone <repository> lumicorepro && cd lumicorepro
cp .env.production.example .env.production
$EDITOR .env.production          # set every REQUIRED value (see §3)
docker compose -f docker-compose.prod.yml --env-file .env.production pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
curl -fsS https://<your-domain>/api/health
```

The Compose topology publishes only nginx; PostgreSQL, Redis, the API and the
generation engine stay on an internal bridge network.

### 2.3 Manual development install

```bash
npm ci && npm --prefix backend ci
npm run dev:full            # Vite (5173) + Express (5000)
npm run dev:ai              # FastAPI generation engine (8000)
```

Apply the database migrations once the schema exists:

```bash
node database/migrations/migrate.js
```

---

## 3. Configuration

All configuration is environment-driven; every variable is documented in
`backend/.env.example`. The values that decide whether production works:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string (required in production) |
| `JWT_SECRET`, `JWT_REFRESH_SECRET` | ≥32 random chars each (required) |
| `POSTGRES_PASSWORD`, `REDIS_PASSWORD` | Compose refuses to start without them |
| `PUBLIC_ORIGIN`, `SERVER_NAME` | Public origin and TLS host |
| `GEMINI_API_KEY` / `GROK_API_KEY` / `DEEPSEEK_API_KEY` / `OPENROUTER_API_KEY` | Generation providers (at least one) |
| `LICENSE_SECRET` | HMAC secret for license keys (required to sell) |
| `LEMONSQUEEZY_SIGNING_SECRET` | Webhook signature verification (required for sales) |
| `AI_DAILY_BUDGET_USD` | Hard per-user daily AI spend cap |
| `DB_REPLICA_URLS` | Optional comma-separated read replicas |

Generate secrets, never reuse them:

```bash
openssl rand -hex 32    # JWT_SECRET, LICENSE_SECRET, LEMONSQUEEZY_SIGNING_SECRET
```

---

## 4. Operating the platform

### 4.1 Health and observability

| Endpoint | Use |
| --- | --- |
| `GET /api/health` | Liveness (used by the container health check) |
| `GET /api/health/detailed` | Database, Redis and process diagnostics |
| `GET /api/metrics` | Prometheus exposition (counters, latency histograms, SLO burn rates) |
| `GET /api/metrics/slo` | JSON SLO evaluation (availability, p95, generation success) |

Prometheus scrape configuration:

```yaml
scrape_configs:
  - job_name: lumicorepro
    metrics_path: /api/metrics
    static_configs:
      - targets: ['lumicorepro-api:5000']
```

### 4.2 Distributed tracing

Every request carries a W3C `traceparent` header end to end — browser → Express
→ FastAPI → AI provider. The trace id is returned to the client in
`X-Trace-Id` and appears in every log line of that request, so a slow
generation can be reconstructed from one identifier.

### 4.3 AI cost governance

| Mechanism | Where |
| --- | --- |
| Per-run ledger (`ai_spend_ledger`) | one row per billable run: tokens, provider, cost |
| Daily per-user cap | `AI_DAILY_BUDGET_USD` → `402 DAILY_BUDGET_EXCEEDED` |
| Circuit breaker | abnormal request rates blocked for `AI_CB_BLOCK_SECS` |
| Semantic cache | repeat and near-identical prompts replay the stored build |
| Spend dashboards | `GET /api/ai/spend/ledger`, `GET /api/ai/spend-estimator` |

### 4.4 Quality operations

Autopilot audits every generated project (guardrails → self-heal → quality
gates → trend recording) and writes a report:

```bash
cd ai-agent
python -m agent.autopilot --root ../generated-projects            # dry run
python -m agent.autopilot --root ../generated-projects --fix      # apply repairs
```

Reports land in `ai-agent/logs/autopilot/`. The same sweep runs nightly in CI
(see `.github/workflows/autopilot.yml`).

---

## 5. Generation engine

| Capability | Endpoint |
| --- | --- |
| Start a build | `POST /api/ai/generate` |
| Stream progress | WebSocket `/ws/generate/{run_id}` or SSE |
| Fetch a finished run | `GET /api/ai/runs/{run_id}` |
| Download the project | `GET /api/ai/download/{run_id}` |
| Register a preview | `POST /api/ai/preview` |
| Deploy | `POST /api/ai/deploy` |

Generation always runs through the pipeline:

1. Requirement analysis and market analysis
2. Design decision, style and theme matrix
3. Template, component, asset and backend selection
4. RAG retrieval of best practices and past-build lessons
5. Project assembly (frontend, backend, schemas, docs)
6. Quality gates, self-healing, compliance, SEO, performance
7. Output guardrails (CSP, secret/PII redaction) and packaging

Prompt versions are registered and content-hashed, so any delivered project can
be traced back to the exact prompt revision that produced it
(`GET /api/v1/prompt-registry`).

---

## 6. Marketplace administration

### 6.1 Selling templates

Templates are ordinary products. A customer buys through the storefront and the
order becomes an entitlement.

### 6.2 Delivering updates to sold templates

1. Place the update package in `TEMPLATE_UPDATES_DIR` (default
   `backend/uploads/template-updates`).
2. Publish it:

```http
POST /api/template-updates
Authorization: Bearer <admin token>
Content-Type: application/json

{ "productId": 42, "version": "1.4.0", "changelog": "Fixes mobile nav", "fileName": "aurora-1.4.0.zip" }
```

Every buyer is notified in-app and over the realtime channel, and can download
the latest package from `GET /api/template-updates/{productId}/download`.
Purchase is verified server-side against paid orders — there is no URL that
works without one.

### 6.3 Licensing (Lemon Squeezy)

See [`SELLING_GUIDE.md`](./SELLING_GUIDE.md) for the complete sales workflow.

---

## 7. Security model

| Control | Implementation |
| --- | --- |
| Authentication | JWT access + rotating refresh tokens, optional 2FA |
| Authorization | Role/permission middleware, tenant scoping per organization |
| Rate limiting | Redis-backed, per route class, shared across replicas |
| Audit trail | Append-only, hash-chained; `GET /api/audit/verify` proves integrity |
| Data subject rights | Export and erasure workflows (`/api/privacy/*`) |
| Headers | Helmet, CSP on uploads, HSTS in production |
| Secret scanning | gitleaks in CI; guardrails scrub generated projects |

---

## 8. Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `503` from `/api/health/detailed` | Database unreachable | Check `DATABASE_URL`, `docker compose logs db` |
| Generation returns "AI agent is offline" | Engine not running | `curl http://localhost:8000/health` |
| Every generation fails the quality gate | Provider key missing/invalid | Verify the provider key in `.env`, restart API |
| `402 DAILY_BUDGET_EXCEEDED` | Per-user cap reached | Raise `AI_DAILY_BUDGET_USD` or wait for the UTC day rollover |
| License key reports `unconfigured` | `LICENSE_SECRET` unset | Set it and restart the API |
| Lemon Squeezy webhook returns 401 | Signing secret mismatch | Re-copy the secret from the Lemon Squeezy dashboard |
| Audit chain verification fails | Row altered outside the ORM | Restore from backup; investigate the `brokenAtId` row |

---

## 9. Support

* Operations runbook: [`RUNBOOK.md`](./RUNBOOK.md)
* Deployment procedures: [`DEPLOYMENT.md`](./DEPLOYMENT.md)
* API reference: [`API_REFERENCE.md`](./API_REFERENCE.md)
* Security policy: `../SECURITY.md` (repository root, outside this doc site)