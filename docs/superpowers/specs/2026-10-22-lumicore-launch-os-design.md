# Lumicore Launch OS Design

## Intent

Make LumicorePro feel like a differentiated AI-native product operating system rather than a set of disconnected pages. The product promise is a hybrid: multi-agent creative collaboration, evidence-first delivery, and autonomous launch tooling.

## Constraints

- Preserve existing routes, API contracts, authentication behavior, and extension actions.
- Reuse the existing React 19, Vite, Tailwind, Lucide, Context, and page/component conventions.
- Avoid new dependencies unless a verified gap requires one.
- No fake metrics or fabricated run state; unavailable backend data must remain clearly unavailable.
- Support dark mode, reduced motion, keyboard navigation, readable contrast, and responsive widths from 320px to 1920px.
- Keep the existing Workspace Agent Control Center behavior and tests working.

## Experience architecture

### 1. Agent OS shell

Authenticated product pages share a consistent shell with:

- Brand/logo and workspace identity.
- Desktop rail and mobile navigation.
- Primary destinations: Overview, Generate, Projects, Agent Runs, Templates, Analytics, Integrations, Billing, Settings.
- Current page title, contextual actions, theme/language controls, notifications, and profile affordance.
- Active navigation state that is visible and keyboard accessible.

Public marketing and authentication pages retain their own layout.

### 2. Overview command surface

The overview prioritizes action over decorative dashboards:

- Continue the last run using the persisted run ID.
- Start a new generation.
- Launch readiness summary based only on available evidence.
- Provider/agent health and usage when returned by the backend.
- Recent projects and recent activity.
- Clear empty, loading, unavailable, success, and recovery states.

### 3. Launch Loop

Generation and run views use a shared phase vocabulary:

`Brief → Strategy → Design → Build → Critique → Proof → Ship`

Each phase may show a real status, handoff, timestamp, or evidence link. The UI must not imply progress when the backend has not reported it. Missing phase data is shown as queued or not reported, not as a fabricated percentage.

### 4. Generate cockpit

The existing generation flow gains a product-level framing:

- Intent/prompt composer.
- Brand, audience, locale, and currency controls where the existing flow supports them.
- Provider/model selection using existing service behavior.
- Example prompts and clear next action.
- Persistent/resumable run identity.
- Live Launch Loop status when run data is available.

Existing generation submission behavior remains the source of truth.

### 5. Workspace evidence cockpit

Workspace remains the operational center and is visually integrated with the shell. Its current tabs continue to expose Watchtower, Marketing Kit, Browser QA, Stripe Checkout, Visual Editor, Delivery Reports, Webhooks, and deployment. Evidence cards summarize browser, accessibility, performance, SEO, and deployment reports only when returned by the API.

### 6. Project and supporting destinations

Where routes already exist, the shell provides consistent framing without inventing backend functionality. Placeholder destinations must be honest and actionable: explain what is available, show a safe empty state, and link to Generate or Workspace when appropriate.

## Implementation boundaries

- Prefer a small set of reusable shell components over duplicating markup in every page.
- Keep API calls in existing services and page-level hooks.
- Keep shell state local or derived from route/context; do not add a global store for navigation-only state.
- Add tests for navigation landmarks, active route state, responsive/mobile navigation, persisted run handoff, and honest unavailable states.
- Add Playwright coverage for signed-out redirect, authenticated shell rendering, mobile navigation, Workspace access, and serious/critical axe violations.

## Acceptance criteria

1. Authenticated product pages render inside one coherent, responsive Agent OS shell.
2. Navigation exposes the approved destinations with active state and keyboard-accessible controls.
3. Overview provides a useful continuation path and honest data states without fabricated metrics.
4. Generate and Workspace remain functional through their existing APIs.
5. Launch Loop labels and evidence summaries are consistent across relevant views.
6. Dark mode, reduced-motion behavior, focus visibility, and mobile layout are preserved.
7. Existing tests, new focused tests, lint, production build, bundle budget, and Playwright/axe checks pass.
8. No unrelated backend/API changes are introduced.

## Explicit non-goals

- Replacing the existing auth system.
- Creating a new database or billing provider.
- Implementing real-time infrastructure where the backend does not expose it.
- Claiming performance, accessibility, or deployment metrics that have not been measured or returned.
