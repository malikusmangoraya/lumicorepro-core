# Agent Control Center Productization — Design Specification

**Status:** Draft for review
**Date:** 2026-10-22

## Goal

Make LumicorePro's existing generation and extension surfaces feel like an international, professional agent control center while preserving current generation behavior and integrating visible, evidence-based n8n, Playwright, accessibility, and performance workflows.

## Current context

LumicorePro already has a React/Vite frontend, a FastAPI AI agent, a 16-phase generation UI, WebSocket progress updates, a post-generation Workspace page, a Playwright browser-QA extension, and an n8n generate-and-monitor workflow template. The repository also contains unrelated uncommitted changes; this work must modify only files directly needed for the Agent Control Center and must not discard or stage unrelated work.

## Product architecture

- `/generate` remains the prompt and generation surface.
- `/workspace` becomes the post-generation Agent Control Center and uses the existing `run_id` local-storage/API contract.
- Existing APIs and response contracts are reused. A new backend endpoint is added only if a verified missing capability blocks the UI and its contract is covered by tests.
- Existing design tokens, Tailwind conventions, Lucide icons, React Query/API services, i18n, auth guards, and reusable UI primitives are preferred over duplicate components.
- The UI presents generation provenance and quality evidence honestly: passed, failed, unavailable, skipped, and not measured are distinct states.

## Information architecture

### Run overview

Show lifecycle status, elapsed time, project name, quality score, provider/fallback provenance, preview/export actions, and the next best action. The header must work without a backend response by showing a clear unavailable/stale state.

### Pipeline timeline

Group the 16 phases into Discover, Design, Build, Verify, and Deliver. Each phase exposes current/completed/skipped/failed state, a concise description, and a safe reason when skipped. Unknown phase names must render an explicit unknown state rather than breaking the page.

### Agent handoffs

Render `workflow_agents` role cards with status, handoff summary, and evidence links when present. Never infer success from a missing role or fabricate metrics.

### QA evidence

Expose Browser QA, accessibility, performance, and deployment reports using the existing Workspace actions and result data. A missing optional dependency or unavailable backend is an honest unavailable state, not a pass badge.

### Recovery actions

Support existing retry/cancel/revise/open-log actions where available. All asynchronous actions need disabled/loading/success/error states. Destructive or cancellation actions require confirmation and must not leak secrets into logs or notifications.

### Automation panel

Keep n8n setup, webhook configuration, and operator automation visible but secondary to run control. The UI can link to setup guidance and show configured webhook state; live n8n import/execution is not claimed unless tested against an actual n8n instance.

## Visual and interaction direction

Use an international SaaS control-room aesthetic: restrained ink/navy surfaces, semantic status colors with sufficient contrast, clear typography hierarchy, generous spacing, responsive two-column desktop layout collapsing to a single-column mobile layout, RTL-safe logical spacing, visible focus styles, and reduced-motion support. Avoid gratuitous glow, glass, gradients, or dense card nesting. Use existing project tokens and components instead of introducing a new UI library.

Responsive targets are 375px, 768px, 1024px, 1440px, and 1920px. Keyboard navigation must reach tabs, actions, confirmations, and report links in a logical order. Screen readers must receive meaningful labels and live updates for state changes.

## Data, error, and security behavior

- Missing backend: show a recoverable connection error and preserve the entered run ID.
- Stale or unknown run: show the last known state and a refresh/retry action.
- Unknown phase/role/status: show a safe “unknown” state and continue rendering the rest of the page.
- Fallback generation: show provider/fallback provenance from the server response.
- Incomplete QA: label it not measured or unavailable; never claim WCAG, Lighthouse, or Playwright success without evidence.
- Prompt text, generated project content, provider credentials, API keys, and secrets must not be sent to notification metadata or browser logs.
- Existing authentication and backend authorization remain the security boundary.

## Acceptance criteria

1. Existing `/generate` behavior and API request/response contracts remain compatible.
2. `/workspace` has a coherent Agent Control Center hierarchy with overview, grouped pipeline timeline, agent handoffs, QA evidence, recovery actions, and separated automation controls.
3. The layout is usable at 375/768/1024/1440/1920px and supports keyboard navigation, visible focus, RTL-safe layout, and reduced motion.
4. Run states include loading, queued, running, completed, partial/skipped, failed, cancelled, unavailable, and unknown without false success claims.
5. Provider/fallback provenance and workflow-agent data are rendered only from actual response fields.
6. Playwright/browser QA and accessibility results distinguish pass, fail, unavailable, and not measured.
7. n8n setup remains credential-safe and existing workflow behavior is unchanged unless a separately tested UI integration requires a compatible change.
8. Focused frontend tests, relevant AI-agent tests, lint, production build, bundle budget, and Playwright smoke checks pass; failures or blocked external checks are reported explicitly.
9. No secrets, unrelated files, generated dependencies, or broad refactors are added.

## Out of scope

- Replacing the existing generation engine or React/Vite output.
- Embedding or provisioning n8n.
- Adding a new hosted provider, database, auth system, payment service, or external API.
- Claiming live n8n compatibility without an actual n8n import/execution check.
- Rebuilding the entire design system or changing unrelated marketplace/template pages.
