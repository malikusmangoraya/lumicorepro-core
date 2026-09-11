# TRD_ENGINEERING_STANDARDS.md — LumicorePro Technical Requirements

> Source of truth: TRD #2 *Platform Injection Rules*.
> Enforced dependency frameworks, React 19 rules, and server patterns for every
> generated project (frontend: all modes; backend: transactional runtime only).

---

## Dependency Pins

| Package | Pin | Bucket |
|---------|-----|--------|
| `react` | `^19.2.0` | dependencies |
| `react-dom` | `^19.2.0` | dependencies |
| `@tanstack/react-query` | `^5.59.0` | dependencies |
| `zustand` | `^5.0.0` | dependencies |
| `vite` | `^8.2.0` (major ≥ 8) | devDependencies |
| `tailwindcss` | `^3.4.7` (major = 3) | devDependencies |

`frontend/package.json` must be pinned to these exact versions at compile time.

## React 19 Rules

- Functional components only. Correct dependency arrays and cleanup in
  `useEffect`/`useRef`.
- Server state lives on the **TanStack React Query cache cluster**
  (`src/lib/queryClient.js`: staleTime 5m, gcTime 30m, retry 2, no focus refetch).
- `QueryClientProvider` is auto-wrapped around the app root
  (`src/lib/AppProviders.jsx` → `App.jsx` default export).
- Client/UI state uses the lightweight **Zustand** wrapper
  (`src/store/useAppStore.js`).
- API reads go through `src/hooks/useApiQuery.js` (Axios client; static builds
  fall back to relative fetch).

## Optimization

- Alternative layout templates loaded strictly via `React.lazy()` —
  `src/lib/LazyLayouts.jsx` → `LandingLayout` / `AppLayout`, each wrapped in its
  own `Suspense` boundary with the CLS-safe `LayoutSkeleton`.
- **CLS budget < 0.1.** CLS guard utilities must be present in `index.css`
  (`img/video/iframe` sizing, `.cls-reserve`, `.skeleton-shimmer`).

## Backend Patterns (transactional runtime only)

- Express decoupled route controllers: `backend/controllers/user.controller.js`.
- Predictable `{success,status,message,data,timestamp}` envelope via
  `backend/utils/response.js` + `backend/middleware/errorHandler.js`.
- Native Sequelize models mapped to PostgreSQL/MySQL (`backend/config/db.js`,
  `backend/models/*`).
- BullMQ delayed jobs over protected, isolated Redis with **in-memory fallback**
  (`backend/services/cache/redis.client.js` exposes `isMemory`;
  `backend/services/queue/queue.service.js` dispatches in-process when offline).
- Static runtime: backend blueprint intentionally not mounted (API-less SPA) —
  conformance reports `applies: false` with reason; this is **not** a violation.

## Conformance

| Check | Gate reference |
|-------|----------------|
| Pinned `package.json` | `engineering.checks.stack_pins` |
| Provider-wrapped app root | `engineering.checks.state_topology` |
| Lazy layouts + CLS guard | `engineering.checks.optimization` |
| Backend blueprint | `engineering.checks.backend_blueprint` |

**Hard rule:** any unresolved pin or missing blueprint file is an engineering
violation routed to the self-healing pipeline; the ZIP archive is not compiled
while this check is red.