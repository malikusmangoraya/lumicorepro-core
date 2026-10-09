# Responsive Layout Blueprint — resupro

> Modern Era Baseline: ultra-premium output layers applied to every generated project.
> Runtime: **transactional** pipeline.

## 1. Responsive Fluid UI

- Clamp-based `--fluid-space-*` token scale + `.p-fluid-*`, `.py-fluid-*`, `.fluid-gap-*` custom spacing utilities.
- `.fluid-container`, `.fluid-section`, `.fluid-bleed`, fluid hero/lead type (`text-fluid-hero`, `text-fluid-lg`).
- All defined in `frontend/src/index.css`; RTL-safe (logical properties); no viewport breakpoint lock-in.

## 2. Micro-Interactions Layer

- `MotionCanvas` — scroll-triggered ambient canvas loop (DPR-capped, auto-pause, `prefers-reduced-motion` safe).
- `MotionSystems.jsx` — `Reveal`, `MagneticButton`, `TiltCard`, `HoverGlow` hover micro-states (framer-motion).
- `useInView` — IntersectionObserver reveal primitive. Canvas auto-mounted in `App.jsx`.

## 3. Lead Capture & Dynamic Pipelines

- `LeadForm` — conversion form wired to Formspree/webhook/mock, honeypot + analytics events.
- `CheckoutFlow` — single-page conversion checkout: trust badges, order summary, `begin_checkout` → `purchase` events.
- `analyticsBus` — provider-agnostic event bus; pairs with the auto-generated `useAnalytics` hook.

## 4. Dual Runtime

- **Static** (`layout_mode=static`): API-less SPA, Vercel/Netlify drop-in, client-side form mocks.
- **Transactional** (`layout_mode=enterprise`): Express + Redis + MySQL/Postgres backend, nginx gateway, real `/api/*`.

## Go-Live Checklist

- [ ] Pair LeadForm/CheckoutFlow with real endpoints (`VITE_FORMSPREE_ID`, `VITE_LEADS_WEBHOOK`, `/api/orders`)
- [ ] Replace demo card fields with a real PSP (Stripe/PayPal) before taking payments
- [ ] Run `npm run build` and deploy both tiers independently
