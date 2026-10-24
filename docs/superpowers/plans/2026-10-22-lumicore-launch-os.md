# Lumicore Launch OS Implementation Plan

## Goal

Introduce a reusable authenticated Agent OS shell around existing product routes, add an evidence-first overview and shared Launch Loop language, and preserve current generation/workspace behavior.

## Task 1 — Map authenticated product routes and shell boundaries

- Inspect route configuration, MainLayout, auth gates, existing navigation, Home, Generate, Workspace, Templates, Pricing, and shared theme/i18n components.
- Identify which routes are public and which are authenticated.
- Record any existing shell or navigation behavior that must remain unchanged.
- Expected: a route map and a small set of shell integration points; no API changes.

## Task 2 — Add shell tests first

- Add focused tests for authenticated navigation landmarks, active route label, mobile navigation toggle, and shell rendering around existing pages.
- Add overview tests for honest empty/unavailable states and a continue-last-run affordance.
- Run the focused tests and observe the expected failures before implementation.

## Task 3 — Implement reusable Agent OS shell

- Add the smallest reusable shell components under existing component conventions.
- Integrate shell at the authenticated layout boundary rather than duplicating it per page.
- Use existing BrandLogo, theme, language, Button, Card, and icons.
- Provide desktop rail, mobile menu, page context, notifications/profile affordances, focus states, and dark mode.
- Preserve public page layouts and route guards.
- Expected: all authenticated product routes share navigation without changing API behavior.

## Task 4 — Implement Overview and shared Launch Loop presentation

- Add or adapt the authenticated overview page to provide continuation, recent activity, provider health, and launch readiness using only existing available data.
- Add a shared presentational Launch Loop component that accepts phase/status data and renders honest queued/unavailable states.
- Connect Generate/Workspace where existing route data permits; do not invent polling or backend endpoints.
- Expected: overview is useful in signed-out/backend-unavailable states and passes focused tests.

## Task 5 — Integrate and polish existing pages

- Wrap Generate, Workspace, Templates, Analytics, Integrations, Billing, and Settings routes where applicable.
- Replace only inconsistent page-level navigation/framing; preserve functional controls and API calls.
- Add responsive and reduced-motion utility classes consistent with current Tailwind conventions.
- Expected: no broken routes, no duplicate navigation, no visual overflow at 320px.

## Task 6 — Verify through the user interface

- Run focused Vitest tests, full frontend tests, lint, production build, bundle budget, and Playwright/axe.
- Start/reuse the production preview and inspect authenticated shell at desktop and mobile widths.
- Check console/network output, signed-out redirect, mobile menu, navigation, Generate, Workspace, and honest unavailable state.
- Fix any regressions, rerun affected checks, and report measured results separately from unmeasured targets.

## Constraints

- No commit, deploy, or push without explicit user request.
- No new third-party dependency unless required and verified.
- Do not overwrite unrelated pre-existing working-tree changes.
- Existing Workspace and Generate API contracts are compatibility boundaries.
