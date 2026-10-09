# Platform Injection Rules (TRD #2) — resupro

> Runtime architecture mandates applied to every generated project.
> Runtime: **transactional** pipeline.

## Frontend Runtime Architecture

- **Core stack pins:** React ^19.2.0 / React-DOM ^19.2.0, Vite ^8.2.0, Tailwind CSS v3.4.x.
- **State topologies:** server state → TanStack React Query cache cluster
  (`src/lib/queryClient.js` mounted via `src/lib/AppProviders.jsx`); client state →
  lightweight Zustand store wrapper (`src/store/useAppStore.js`). `src/hooks/useApiQuery.js`
  binds queries to the platform Axios client (graceful relative-fetch fallback on static).
- **Optimization budgets:** alternate layout templates loaded strictly via
  `React.lazy()` (`src/lib/LazyLayouts.jsx` → `LandingLayout` / `AppLayout`) with
  Suspense + CLS-safe `LayoutSkeleton`; CLS guard utilities in `index.css`
  (img/video sizing, `.cls-reserve` aspect-ratio, shimmer skeleton).
  **CLS budget < 0.1, zero unhandled layout shifts.**

## Backend Infrastructure Blueprint (transactional runtime)

- Express decoupled route controllers (`backend/controllers/*`) with predictable
  HTTP status codes via `backend/utils/response.js` + `backend/middleware/errorHandler.js`.
- Native Sequelize models mapped to PostgreSQL/MySQL schemas (`backend/config/db.js`).
- BullMQ delayed job clusters over protected isolated Redis nodes
  (`backend/services/cache/redis.client.js`: lazy connect, retry disabled, offline queue
  off, connect timeout) with **in-memory fallback** (`connection.isMemory` →
  `backend/services/queue/queue.service.js` in-process dispatch).
- Static runtime: backend blueprint intentionally not mounted (API-less SPA).

## Conformance

- State topology: ok —
  provider wrapped: False.
- Lazy layouts: ok.
- CLS guard: ok.
- Backend blueprint:
  - controllers: PASS ()
  - response_envelope: PASS (status-code helpers present)
  - error_handler: PASS (status-code helpers present)
  - sequelize_models: PASS ()
  - queue_service: PASS (in-memory fallback present)
  - redis_protected_fallback: PASS (in-memory fallback present)
  - **overall: CONFORMANT**
