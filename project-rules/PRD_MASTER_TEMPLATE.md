# PRD_MASTER_TEMPLATE.md — LumicorePro Product Requirements (Generation Matrix Baseline)

> Source of truth: TRD #1 *Generation Matrix* — the "Modern Era Baseline" PRD layer.
> Every generated project must ship the feature scope below and satisfy the
> acceptance criteria before the ZIP archive is compiled.

---

## Feature Scope

### 1. Responsive Fluid UI
- `clamp()`-based spacing/type scale in `frontend/src/index.css`:
  `--fluid-space-1` … `--fluid-space-6`, `--fluid-page`.
- Custom utilities: `.fluid-container`, `.fluid-section`, `.fluid-gap-*`,
  `.p-fluid-*`, `.py-fluid-*`, `.text-fluid-hero`, `.text-fluid-lg`, `.fluid-bleed`,
  `.fluid-ease`.
- RTL-safe (logical properties `margin-inline`/`padding-block`). No viewport
  breakpoint lock-in.

### 2. Micro-Interactions
- `frontend/src/hooks/useInView.js` — IntersectionObserver reveal primitive.
- `frontend/src/components/common/MotionCanvas.jsx` — scroll-triggered ambient
  canvas loop (DPR-capped, auto-pause, `prefers-reduced-motion` safe).
- `frontend/src/components/common/MotionSystems.jsx` — `Reveal`, `MagneticButton`,
  `TiltCard`, `HoverGlow` micro-states (framer-motion).
- `MotionCanvas` auto-mounted in `frontend/src/App.jsx`.

### 3. Lead Capture & Dynamic Pipelines
- `frontend/src/components/common/LeadForm.jsx` — endpoint-resolved conversion
  form (Formspree → webhook → dev mock), honeypot, analytics events.
- `frontend/src/components/checkout/CheckoutFlow.jsx` — single-page checkout with
  trust badges, order summary, `begin_checkout` → `purchase` analytics.
- `frontend/src/services/analyticsBus.js` — provider-agnostic event bus.

### 4. Dual Runtime Surface
- `spec.runtime_mode` is explicit: **static** (`layout_mode=static`, API-less SPA,
  Vercel/Netlify drop-in) or **transactional** (`layout_mode=enterprise`, Express +
  Redis + MySQL/Postgres backend, nginx gateway, real `/api/*`).
- `runtime_mode` must be persisted in the spec, the layout report, and
  `GENERATION-MATRIX.md`.

---

## Acceptance Criteria

| Pillar | Required artifact | Gate reference |
|--------|-------------------|----------------|
| Fluid UI | `--fluid-space-*` tokens + `.fluid-*` utilities in `index.css` | `prd.checks.fluid_ui` |
| Micro-interactions | `useInView.js`, `MotionCanvas.jsx`, `MotionSystems.jsx`, App mount | `prd.checks.micro_interactions` |
| Lead capture | `LeadForm.jsx`, `CheckoutFlow.jsx`, `analyticsBus.js` | `prd.checks.lead_capture` |
| Dual runtime | `GENERATION-MATRIX.md` present; declared `runtime_mode` matches `spec.layout_mode` | `prd.checks.runtime_mode` |

**Hard rule:** any missing artifact is a PRD scope violation and is routed to the
self-healing pipeline. The ZIP archive is not compiled while the PRD scope check
is red.