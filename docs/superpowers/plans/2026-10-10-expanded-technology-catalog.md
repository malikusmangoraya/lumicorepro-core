# Expanded Technology Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add all technologies and engineering topics from the approved reference to LumicorePro's validated catalog, selection UI, and agent guidance without claiming unsupported implementation.

**Architecture:** Keep the canonical JSON catalog and its SQLite mirror, extending them with typed groups for frontend/full-stack frameworks, backend frameworks, admin platforms, hosting, testing, CI, auth guidance, and engineering topics. Add a validated `technology_choices` object alongside the unchanged `backend_stack`; resolve it deterministically, forward it through Express/FastAPI, and report catalog-only versus genuinely generated capabilities. Build the UI as progressive-disclosure panels and keep provider pricing/limits out of durable claims.

**Tech Stack:** React 19, Vite, Tailwind, i18next, Express, FastAPI/Pydantic, Python, SQLite, pytest, Jest, Vitest.

**Spec:** [2026-10-10-expanded-technology-catalog-design.md](../specs/2026-10-10-expanded-technology-catalog-design.md)

## Global Constraints

- The catalog and agent guidance cover every technology and topic named in the supplied reference.
- The user selected catalog/guidance only; native scaffolds or deployment automation for every listed option are not in scope.
- Retain the existing backend-stack selection and Node.js/Express default.
- Distinguish selection/recommendation from implementation in plans, dry runs, and generation reports.
- Avoid treating changing vendor pricing, free-tier limits, availability, or acceptable-use rules as fixed facts.
- Validation rejects unknown IDs and combinations explicitly marked incompatible before a generation run is created.
- Auto mode recommends only combinations explicitly marked compatible; manual selections whose compatibility is unknown remain selectable but carry an `unverified` status and warning.
- Existing API paths/fields stay backward-compatible; new catalog response fields are additive.
- Do not create/configure provider accounts, CI workflows, deployment resources, or newly listed scaffolds.

## Review Focus

- **Malformed choices:** arrays/objects in scalar fields, non-string list members, empty IDs, and unknown IDs fail with a client error before run, credit, or task side effects; test in Tasks 2-3.
- **Conflicting choices:** explicitly incompatible framework/host/admin/database combinations fail; test each declared compatibility edge in Tasks 1-2.
- **Unknown compatibility:** Auto excludes it, while manual selection carries `unverified` plus a visible warning instead of claiming support; test in Tasks 1-2 and 4.
- **Mode transition:** switching Manual back to Auto clears manual overrides so old technology choices are not silently resubmitted; test in Task 4.
- **Legacy request:** omitting `technology_choices` preserves existing backend defaults, API payloads, and report shape; test in Tasks 2-3.

---

### Task 1: Extend and validate the canonical catalog

**Files:**
- Modify: `registry/technology-stack-catalog.json`
- Modify: `ai-agent/agent/technology_catalog.py`
- Test: `ai-agent/tests/test_technology_catalog.py`

**Interfaces:**
- Consumes: Current catalog v1.1.0 schema, existing language/framework/database/ORM entries, and the approved reference.
- Produces: Catalog v2.0.0 with existing keys preserved and these additive groups: `frontend_frameworks`, `admin_platforms`, `hosting_providers`, `testing_tools`, `quality_tools`, `ci_providers`, `source_control_providers`, `authentication_profiles`, `authentication_libraries`, and `engineering_topics`.
- Each option has a stable ID unique within its group, display `label`, category, and capability status `catalog_only_not_generated`, `generated`, or `verified`; compatibility relationships use group-qualified IDs and a tri-state `compatible` / `incompatible` / `unknown`.
- Extend `REQUIRED_LANGUAGES` to include Rust, Elixir, and Kotlin; associate Kotlin with Micronaut while retaining all existing framework entries and scaffold flags.

- [ ] **Step 1: Add failing `test_expanded_catalog_contains_reference_inventory`** asserting the full reference inventory (React + Vite, Next.js, SvelteKit, Nuxt, Astro, TanStack Start, React Router Framework, Qwik City, SolidStart; Hono, AdonisJS, API Platform, Litestar, Axum, Actix Web, Chi, Phoenix; Payload, Strapi, Directus, Appsmith, Budibase; all listed hosting/testing/auth references; and every advanced engineering topic).
- [ ] **Step 2: Add failing `test_catalog_rejects_duplicate_option_ids`, `test_catalog_rejects_missing_required_group`, `test_catalog_rejects_unknown_compatibility_target`, and `test_catalog_rejects_invalid_compatibility_state`; retain current ORM/database-type regression tests.**
- [ ] **Step 3: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py -q`; verify the new assertions fail against the current catalog.
- [ ] **Step 4: Extend** `technology-stack-catalog.json`; retain current database, API, architecture, authentication, cache, queue, and deployment option IDs. Add Rust, Elixir, Kotlin and their named frameworks without marking new choices scaffold-supported.
- [ ] **Step 5: Update** `_validate_catalog(catalog)` in `ai-agent/agent/technology_catalog.py` to validate exact required groups, per-group stable IDs, group-qualified compatibility targets/states, and required metadata. Keep SQLite seeding behavior unchanged so catalog migrations remain idempotent.
- [ ] **Step 6: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py -q`; all catalog and database-seeding assertions pass.

### Task 2: Resolve choices and provide safe contextual guidance

**Files:**
- Create: `ai-agent/agent/technology_choices.py`
- Modify: `ai-agent/agent/tech_stack_selector.py`
- Modify: `ai-agent/agent/planner.py`
- Modify: `ai-agent/agent/orchestrator.py`
- Test: `ai-agent/tests/test_technology_catalog.py`
- Test: `ai-agent/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `load_catalog()` and validated existing backend-stack resolution.
- Produces:
  - `validate_technology_choices(selection: Optional[Dict[str, Any]]) -> Dict[str, Any]`
  - `resolve_technology_choices(spec: Dict[str, Any], selection: Optional[Dict[str, Any]] = None, mode: str = "auto") -> Dict[str, Any]`
  - `format_technology_guidance(resolved: Dict[str, Any]) -> str`
- `TechStackSelector.select(spec, selected_backend, selected_schemas, backend_stack=None, technology_choices=None)` adds only trailing optional arguments and returns resolved choices plus `technology_guidance` in its existing stack dictionary. `GenerationPlanner.create_plan(..., tech_stack=None)` keeps its signature and copies these fields into the plan and per-run generation context.
- Accepted selection keys are exactly `frontend_framework`, `admin_platform`, `frontend_host`, `backend_host`, `database_host`, `source_control_provider`, `testing_tools`, `quality_tools`, `ci_provider`, and `authentication_profile`.
- Validate single IDs as non-empty strings and tool lists as arrays of non-empty strings. Reject unknown IDs; deduplicate list selections and return them in canonical catalog order.
- Auto recommendations use prompt signals and only `compatible` relationships; a manual explicitly selected `unknown` relationship is preserved with `compatibility_status: "unverified"` and a warning. Explicitly incompatible combinations raise `ValueError`.
- Unspecified optional choices stay unset unless a deterministic prompt match exists. The formatter emits trusted catalog guidance only; it must not interpolate unvalidated provider descriptions or claim code was implemented.

- [ ] **Step 1: Add failing tests** `test_validate_technology_choices_rejects_malformed_fields`, `test_resolve_technology_choices_matches_only_compatible_prompt_choices`, `test_manual_unknown_compatibility_returns_unverified_warning`, `test_tool_choices_deduplicate_in_catalog_order`, `test_manual_choices_override_auto_recommendations`, and `test_omitted_technology_choices_preserve_legacy_defaults`.
- [ ] **Step 2: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py -k technology_choices -q`; confirm the new resolver tests fail.
- [ ] **Step 3: Implement** validation/resolution/formatting in `technology_choices.py`; keep backend language/framework/database/ORM resolution in `tech_stack_selector.py`.
- [ ] **Step 4: Pass** `spec.get("technology_choices")` as the new trailing selector argument from `AgentOrchestrator.run(...)`; preserve existing selector callers. Record resolved choices/statuses in the tech-stack dictionary and plan; append `technology_guidance` to per-run generation context without changing `GenerationPlanner.create_plan(...)` positional parameters.
- [ ] **Step 5: Add** `test_technology_choice_override_bypasses_prompt_only_cache` proving non-default `technology_choices` cannot reuse a prompt-only cached result created for another technology selection.
- [ ] **Step 6: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py ai-agent/tests/test_orchestrator.py ai-agent/tests/test_reach_integration.py -q`; all new and legacy callers pass.

### Task 3: Validate and transport selections through FastAPI and Express

**Files:**
- Modify: `ai-agent/server.py`
- Modify: `backend/utils/aiAgent.js`
- Modify: `backend/routes/ai.routes.js`
- Test: `ai-agent/tests/test_server_security.py`
- Test: `backend/tests/unit/backendStack.test.js`
- Test: `backend/tests/feature/http.test.js`

**Interfaces:**
- Consumes: `validate_technology_choices(...)` and `resolve_technology_choices(...)` from Task 2.
- Produces: Additive optional `technology_choices: Dict[str, Any] | None` on generation, streaming, and dry-run request models; optional `technology_choices` in Express JSON payload forwarding; resolved choices in API plan and report responses.
- FastAPI remains the trusted catalog-ID/compatibility validation boundary. Express performs strict shape validation before cost guards, matching the existing backend-stack route pattern.

- [ ] **Step 1: Add failing Express tests** `validateTechnologyChoicesPayload accepts catalog fields`, `validateTechnologyChoicesPayload rejects unknown and malformed fields`, and `generation routes forward technology_choices` for ordinary and streaming request bodies. Keep detailed ID/compatibility checks at the FastAPI trust boundary.
- [ ] **Step 2: Add failing FastAPI test** `test_invalid_technology_choices_rejected_before_generation_is_queued`, parametrized over `/api/generate`, `/api/generate/stream`, and `/api/dry-run`; assert 422 before run creation, credit reservation, or background scheduling.
- [ ] **Step 3: Run** the focused Jest and pytest selectors to confirm these tests fail for missing request handling.
- [ ] **Step 4: Implement** Express validation and forwarding in `aiAgent.js` and `ai.routes.js`; retain error statuses/envelopes and existing cost-guard ordering.
- [ ] **Step 5: Implement** FastAPI Pydantic fields and route validation/propagation in `server.py`; add resolved `technology_choices` to dry-run and final report data without removing existing response keys.
- [ ] **Step 6: Run** from `backend/`: `node --experimental-vm-modules ./node_modules/jest/bin/jest.js --runInBand --runTestsByPath tests/unit/backendStack.test.js tests/feature/http.test.js`; also run `python -m pytest ai-agent/tests/test_server_security.py ai-agent/tests/test_technology_catalog.py -q`; all pass.

### Task 4: Add grouped manual controls and report states to the generation UI

**Files:**
- Create: `src/components/forms/TechnologyChoicesSelector.jsx`
- Modify: `src/pages/Generate.jsx`
- Modify: `src/i18n/locales/en.json`, `ar.json`, `de.json`, `es.json`, `fr.json`, `hi.json`, `it.json`, `ja.json`, `ko.json`, `pt.json`, `tr.json`, `ur.json`, and `zh.json`
- Test: `src/__tests__/Generate.test.jsx`

**Interfaces:**
- Consumes: `getTechnologyCatalog()` and the catalog groups from Task 1; existing `backend_stack.mode` controls Auto versus Manual.
- Produces: `TechnologyChoicesSelector({ catalog, selection, onChange, manual, loading, error, disabled })`; `Generate.jsx` submits a separate `technology_choices` object with only non-empty selected IDs/lists and displays resolved status/warnings from the response.
- Selecting Auto clears any manual `technology_choices`; Manual shows grouped, progressively disclosed controls. Compatibility filtering is applied only where catalog metadata declares a known relationship.
- Display all new human-facing text with `t('backendStack....')`/a dedicated `t('technologyChoices....')` namespace and ship equivalent keys or the established English fallback across every locale file.

- [ ] **Step 1: Add failing UI tests** `shows technology options in grouped panels`, `renders every catalog option in its capability group`, `filters incompatible options and warns on unknown compatibility`, `submits selected technology_choices and tool lists`, `clears manual technology choices when returning to Auto`, `keeps catalog loading/error/disabled states explicit`, and `reports catalog-only selections without claiming generation`.
- [ ] **Step 2: Run** `npm test -- src/__tests__/Generate.test.jsx`; confirm the new tests fail.
- [ ] **Step 3: Implement** the focused selector component and page wiring; preserve current Auto default, existing backend-stack fields, keyboard accessibility, and explicit API error/loading states.
- [ ] **Step 4: Add** locale labels/help text, including language-safe explanation that provider free tiers and limits can change and must be rechecked at official sources.
- [ ] **Step 5: Run** `npm test -- src/__tests__/Generate.test.jsx` and `npx eslint src/components/forms/TechnologyChoicesSelector.jsx src/pages/Generate.jsx src/__tests__/Generate.test.jsx`; all pass.

### Task 5: Document catalog boundaries and run integrated verification

**Files:**
- Modify: `ai-agent/README.md`
- Modify: `ai-agent/MASTER_PROMPT.md`
- Modify: `docs/superpowers/sdd/2026-10-10-backend-stack-catalog/progress.md`
- Test: focused tests listed below

**Interfaces:**
- Consumes: catalog and behavior from Tasks 1-4.
- Produces: user-facing documentation that distinguishes catalog metadata, recommendation, generated artifacts, and verified deployment; names the selectable groups; explains authentication concepts safely; links to provider official docs without hard-coded tier guarantees.

- [ ] **Step 1: Update** README and Master Prompt to enumerate new capability families, define `technology_choices`, explain Auto/manual behavior, and state that catalog selection alone does not implement code, CI, hosting, or security controls.
- [ ] **Step 2: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py ai-agent/tests/test_server_security.py ai-agent/tests/test_orchestrator.py ai-agent/tests/test_reach_integration.py -q`.
- [ ] **Step 3: Run** `npm test -- src/__tests__/Generate.test.jsx` and backend focused Jest tests (`backend/tests/unit/backendStack.test.js`, `backend/tests/feature/http.test.js`).
- [ ] **Step 4: Run** `npx eslint` on changed frontend files, `npm run build`, `npm run size`, and `git diff --check`.
- [ ] **Step 5: Review** the final diff and status, ensure no test-created state or unrelated file changes remain, and document any unrelated baseline failures without fixing them as part of this task.
