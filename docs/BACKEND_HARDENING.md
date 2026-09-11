# Backend Hardening — LumicorePro API

Production-grade hardening of the Express/Sequelize backend. All features are
designed to **degrade gracefully offline** (Redis/DB down → still boots), use the
standardized response contract, and follow the AGENTS.md security checklist.

## 1. Caching & Redis
- `services/cache/redis.client.js` — ioredis singleton that falls back to an
  in-memory Map when Redis is unreachable/implicitly `REDIS_DISABLED`. Offline-safe.
- `services/cache/cache.service.js` — typed `get/set/remember/bust/invalidateNamespace`
  with TTL tiers (60s/300s/3600s); used by dashboard stats, product lists, search.
- Writes invalidate (`bust`) affected namespaces so stale data never lingers.

## 2. Queue System (BullMQ)
- `services/queue/queue.service.js` — named queues + producers:
  email, ai-generation, image-processing, report, webhook-retry.
  Exponential backoff (2s base), `attempts: 5`, TTL-based completion cleanup.
- `workers/worker.js` — separate consumer process (`npm run worker`), concurrency 5,
  per-queue limiter; failed jobs retried, exhaustion → `sendToDLQ`.
- `services/queue/deadLetter.js` — per-source DLQ for permanent failures.
- Note: BullMQ forbids `:` in queue names, so names use `lh-*` (hyphen).

## 3. Structured Logging & Redaction
- `utils/logger.js` — winston JSON console + rotating files (`error.log`, `combined.log`).
- Deep-redacts password/secret/token/JWT/card/OTP/pin/authorization values regardless
  of case or nesting. `withRequestId(rid)` tags every record for correlation.

## 4. Request ID & Standardized Responses
- `middleware/requestId.js` — sets `X-Request-Id` (accepts inbound, else crypto UUID);
  surfaced in logs via morgan `:reqId` and used for correlation.
- `utils/response.js` — unified contract:
  - success → `{ success, data, meta? }`
  - failure   → `{ success:false, error:{ code, message }, details? }`
  - `notFound`/error handler use this shape (`{ code:'NOT_FOUND', message }`).

## 5. Rate Limiting (Redis-backed)
- `middleware/rateLimit.js` — exported limiters + a loose global `apiLimiter`.
  - auth 5/min, payment 30/15min, api 300/15min, upload.
  - Returns 429 with `Retry-After`; uses `rate-limit-redis` pointer store
    (falls back to memory store when Redis unavailable).

## 6. Input Validation (DTO)
- `middleware/validateRequest.js` — Zod schema-driven validation for bodies
  (`req.validated.body`) plus params/query; 400 on failure with field details.
- Examples wired into auth/order for typed payloads (never trust the client).

## 7. Refresh-Token Rotation & Revocation
- `services/refreshToken.service.js` — tokens are **rotated on every refresh**;
  using an already-rotated token revokes the whole token family; logout revokes.
- Stored in Redis (set) keyed by user+jti; requires `sadd/smembers/srem` which the
  in-memory fallback now implements too.
- Refresh cookie is `httpOnly` (and `secure` in production).

## 8. Webhook Security
- `middleware/webhookSecurity.js` — Stripe signature verification
  (`t`/`v1` timestamp + `sha256` HMAC) + idempotency key dedup.
- `routes/payment.routes.js` mounts the raw-body middleware before `express.json()`
  so signatures verify on the untouched body.

## 9. Transaction & Row-Locking (Order checkout)
- `services/orderService.js` — the entire order-create + stock-decrement runs in one
  `sequelize.transaction` with `FOR UPDATE` row locks, preventing oversell under concurrency.
- **DI seam:** `_setDeps()` lets tests inject fake models/sequelize (no DB needed);
  `orderService.test.js` covers success / insufficient-stock / not-found.

## 10. Advanced SQL & Query Audit
- `services/analyticsService.js` — CTE + window functions for `top-products` and
  `revenue-report`.
- `config/database.js` — SLOW_QUERY_THRESHOLD_MS flags + logs slow statements
  (non-blocking); `LOG_QUERIES=true` to debug in dev.

## 11. DB Indexes
- `scripts/apply-indexes.js` + `database/schemas/indexes.sql` — index audit on
  queried columns (FKs, order/created_at, status). Run `npm run db:indexes`.

## 12. Env Validation (fail-fast)
- `config/env.js` — validates required vars and types; fails hard in `production`,
  warnings + JWT length/port range checks in dev. `.env.example` is source of truth.
- `.env.example` extended: `REDIS_DISABLED`, `WORKER_CONCURRENCY`,
  `SLOW_QUERY_THRESHOLD_MS`, `LOG_QUERIES`, `RATE_LIMIT_*`.

## DI & Repository Layer
- `config/container.js` — Awilix container; `repositories/base.repository.js` +
  `user.repository.js`; `services/userService.js` + `controllers/user.controller.js`
  wired through the container as the reference pattern for new modules.

## Fixes Landed While Hardening
- **Boot blocker:** swagger JSDoc in `notification.routes.js` contained a plain-text
  `NOTE:` line that `swagger-jsdoc` parsed as YAML → `YAMLSyntaxError` at startup.
  Moved the note to a real `//` comment. Server now boots.
- **BullMQ queue names** contained `:` → replaced with `lh-*` (hygienic).

## Testing
- `npm run test:unit` / `test:integration` / `test:feature` / `test:ci` from `backend/`.
- All backend suites green: **11 suites, 38 tests passing**.
- Feature test boots the full Express app (DB/Redis/logger mocked) and checks
  health, `X-Request-Id`, standardized 404, and rate-limit plumbing.
