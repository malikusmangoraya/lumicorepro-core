# Agent Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Productize the existing generation and extensions surfaces into an international, evidence-based Agent Control Center without breaking current generation behavior.

**Architecture:** Keep `/generate` as the creation surface and make `/workspace` the post-generation control center. Reuse existing API services, run-id persistence, extension endpoints, UI primitives, tokens, i18n, and auth; add only focused presentational/state utilities and tests needed to make run state, handoffs, QA evidence, recovery, and automation understandable and safe.

**Tech Stack:** React 19, React Router, Tailwind CSS 3, Lucide React, Vitest, Testing Library, Playwright, axe-core, existing FastAPI agent APIs and n8n JSON template.

**Spec:** `docs/superpowers/specs/2026-10-22-agent-control-center-design.md`

## Global Constraints

- Preserve existing `/generate` API request/response behavior and offline fallback behavior.
- Use existing tokens/components/services; do not add a new UI library or external service.
- Render only evidence present in API responses; distinguish passed, failed, unavailable, skipped, and not measured.
- Support 375/768/1024/1440/1920px, keyboard focus, RTL-safe layout, and reduced motion.
- Never expose prompts, generated output, provider credentials, API keys, or secrets in notification metadata or logs.
- Do not stage, overwrite, or discard unrelated existing worktree changes.

## Review Focus

- Unknown lifecycle/phase/role values must not crash rendering or appear as false success.
- Backend unavailable or stale run IDs must preserve user input and expose a recoverable action.
- Partial/fallback generation must show provenance and not claim release readiness.
- Mobile tab/action overflow must remain operable at 375px and in RTL.
- QA endpoints returning unavailable/failed data must not render pass badges or fabricated metrics.

### Task 1: Add pure Agent Control Center view-model utilities

**Files:**
- Create: `src/utils/agentControlCenter.js`
- Test: `src/__tests__/agentControlCenter.test.js`

**Interfaces:**
- Produces `normalizeRunState(value)`, `normalizePhaseState(value)`, `getPhaseGroups(phases)`, `getEvidenceState(value)`, and `getNextAction(run)` for Workspace and tests.
- Each function accepts nullable/unknown input and returns stable serializable values; unknown values map to explicit `unknown`/`unavailable` states.

- [ ] **Step 1: Write failing tests** for queued/running/done/error/cancelled/unknown states, grouped 16-phase ordering, evidence state mapping, fallback provenance, and next-action selection.
- [ ] **Step 2: Run `npm test -- --run src/__tests__/agentControlCenter.test.js`** and verify the new tests fail because the utility module does not exist.
- [ ] **Step 3: Implement the pure utilities** with no React or browser dependencies and preserve unknown fields rather than inventing success.
- [ ] **Step 4: Run the focused test again** and verify all cases pass.

### Task 2: Build the Agent Control Center Workspace surface

**Files:**
- Modify: `src/pages/Workspace.jsx`
- Modify: `src/components/common/PageSEO.jsx` only if the existing API cannot express the required page metadata
- Test: `src/__tests__/Workspace.test.jsx`

**Interfaces:**
- Consumes existing `extensionsAPI.watchtower`, `browserQA`, `marketingKit`, `deliveryReport`, `editElement`, webhook methods, and the persisted `lmc_last_run_id`.
- Consumes Task 1 view-model utilities.
- Produces accessible sections: run overview, grouped pipeline/evidence, workflow handoffs, recovery/operator controls, and automation controls.

- [ ] **Step 1: Write failing tests** that render Workspace with mocked API responses and assert overview, unknown state, workflow handoffs, evidence unavailable state, run ID preservation, and recoverable error action.
- [ ] **Step 2: Run the focused test** and verify failure from missing test setup/expected Control Center semantics.
- [ ] **Step 3: Refactor Workspace presentation/state in focused sections** while retaining existing API actions, adding semantic tab roles, active-state attributes, labels, live status messaging, confirmation for cancellation/destructive actions, and mobile-safe layout.
- [ ] **Step 4: Add honest evidence/provenance rendering** for Browser QA, accessibility, performance, deployment, provider fallback, and partial/skipped states.
- [ ] **Step 5: Run focused Workspace tests** and verify all expected states pass.

### Task 3: Connect generation completion to the control center contract

**Files:**
- Modify: `src/pages/Generate.jsx`
- Test: `src/__tests__/Generate.test.jsx` or the nearest existing generation test file

**Interfaces:**
- Consumes the current WebSocket `complete` payload and offline fallback result.
- Produces a complete persisted run context containing `run_id` when available, project name, lifecycle/generation status, quality score, `workflowAgents`, provider/fallback provenance, skipped phases, and preview/deployment URLs without changing API calls.

- [ ] **Step 1: Write failing tests** for live completion provenance, fallback completion, and absent/unknown report fields.
- [ ] **Step 2: Run the focused tests** and verify they fail against the current result contract.
- [ ] **Step 3: Normalize/persist the completion context** and link the result CTA to `/workspace` with the current run ID.
- [ ] **Step 4: Run focused generation tests** and verify live/fallback/unknown cases pass.

### Task 4: Add browser/accessibility/performance verification coverage

**Files:**
- Modify: `e2e/` existing relevant smoke spec or create `e2e/agent-control-center.spec.js`
- Modify: `scripts/` only if an existing check cannot be invoked for the new route
- Modify: `.github/workflows/ci.yml` only if the existing CI lacks an appropriate focused command

**Interfaces:**
- Tests the user-visible `/workspace` route through the existing Vite/Playwright setup.
- Uses installed `@axe-core/playwright` and existing bundle-budget tooling; no new dependency or external service.

- [ ] **Step 1: Add Playwright smoke coverage** for route render, tab keyboard navigation, run ID input, unavailable backend state, and responsive layouts at 375px and 1440px.
- [ ] **Step 2: Add axe assertions** for serious/critical violations on the rendered Workspace route, allowing only documented backend/network limitations.
- [ ] **Step 3: Run the focused Playwright test and inspect screenshots, console, and network output.**
- [ ] **Step 4: Run `npm run lint`, `npm run build`, and `npm run check:budget`; preserve and inspect each command's exit code.

### Task 5: Final regression verification and documentation

**Files:**
- Modify: `ai-agent/integrations/n8n/README.md` only if the UI setup guidance exposes a mismatch
- Modify: `docs/` QA handoff/report only if an existing project convention requires a report artifact

- [ ] **Step 1: Run focused frontend tests plus the relevant existing AI-agent tests for server/security, extensions, and n8n templates.**
- [ ] **Step 2: Run the full frontend test suite and inspect failures rather than filtering them away.
- [ ] **Step 3: Review changed files and `git diff --check`; confirm unrelated worktree changes remain untouched.
- [ ] **Step 4: Record blocked checks explicitly: live n8n import/execution and backend-dependent browser actions require operator/runtime availability.

## Verification commands

- `npm test -- --run src/__tests__/agentControlCenter.test.js src/__tests__/Workspace.test.jsx src/__tests__/Generate.test.jsx`
- `npm test`
- `npm run lint`
- `npm run build`
- `npm run check:budget`
- `npm run test:e2e -- e2e/agent-control-center.spec.js`
- `python -m pytest ai-agent/tests/test_server_security.py ai-agent/tests/test_v65_extensions.py ai-agent/tests/test_n8n_workflow_templates.py -q`
- `git diff --check`
