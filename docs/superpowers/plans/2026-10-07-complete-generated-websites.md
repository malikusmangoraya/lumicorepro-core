# Complete Generated Websites Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each newly generated LumicorePro website a tested, documented, Docker-runnable full-stack application with real authentication, persistent forms/data, and payment integration only when the product takes payments.

**Architecture:** Keep the existing Express/Sequelize generator architecture and make its default output internally consistent around PostgreSQL, with an explicit user-requested static opt-out. Generate real database-backed auth and form flows, wire corresponding frontend journeys, and treat payment as a conditional provider integration. A completeness gate checks actual generated files and verification evidence before the run may be called complete or release-ready.

**Tech Stack:** Python 3.14 agent, Express/Node.js generated backends, Sequelize/PostgreSQL, React/Vite generated frontends, Docker Compose, existing Stripe Checkout scaffolder, pytest/unittest, generated backend Jest/Supertest tests.

**Spec:** `docs/superpowers/specs/2026-10-07-complete-generated-websites-design.md`

## Global Constraints

- New generated websites are full-stack by default; only an explicit frontend-only/static request opts out of backend, database, authentication, and Docker.
- New full-stack sites include PostgreSQL persistence, versioned migrations, signup/login/profile, validated persistent forms, Docker Compose, setup documentation, and tests.
- Authentication uses bcrypt cost ≥12, 15-minute access JWTs, rotating 7-day refresh tokens, HttpOnly/Secure/SameSite cookies, and hashed refresh-token storage.
- Payments are required only when the product requirements include collecting money; payment state is authoritative only after verified server-side provider events.
- Do not add OAuth, MFA, subscriptions, analytics, Redis, queues, or payment secrets to every project without a product requirement.
- Never ship a working default secret/password, store raw card data, claim an unconfigured integration passed, or treat a diagnostic archive as complete.
- Existing-site upgrades preserve the established architecture and behavior and touch only required surfaces.

## Review Focus

- Implicit or conflicting static/full-stack signals must resolve to full-stack unless the user explicitly opts out; test both an ordinary new brief and a static-only brief.
- User-controlled project features must not accidentally enable money collection; test payment inclusion only for explicit purchase/subscription requirements and explicit supported payment features.
- Auth/form error paths (duplicate account, malformed input, invalid credentials, database outage) must never return success; test these outcomes at generated backend boundaries.
- Missing Docker secrets, database readiness, or provider credentials must fail clearly or report blocked/not measured; test configuration rendering and gate/report outcomes.
- Legacy prompt-registry entries and pre-existing projects must not silently bypass new defaults or be destructively rewritten; test old-baseline planner resolution and upgrade/static mode preservation.

---

### Task 1: Establish full-stack generation defaults

**Files:**
- Modify: `ai-agent/agent/planner.py`
- Modify: `ai-agent/agent/orchestrator.py`
- Modify: `ai-agent/agent/project_mode_engine.py`
- Modify: `ai-agent/config/master_prompt.py`
- Modify: `docs/AI_WEBSITE_GENERATION_STANDARD.md`
- Test: `ai-agent/tests/test_reach_integration.py`
- Test: `ai-agent/tests/test_orchestrator.py`
- Test: `ai-agent/tests/test_project_mode_engine.py`

**Interfaces:**
- `GenerationPlanner.create_plan(spec, selected_template, selected_components, selected_assets, selected_backend, selected_schemas) -> Dict[str, Any]` remains the planner entry point.
- The plan/spec records an explicit normalized `layout_mode` (`enterprise` by default, `client-static` only from an explicit static request) and separates baseline features from requested business features.
- Baseline full-stack capabilities are `jwt_auth`, `users`, and persistent `contact`/form handling; optional OAuth, MFA, analytics, subscriptions, and payment features stay request-driven.
- Payment features are selected only by explicit `features` entries such as `stripe_payments`, `paypal_payments`, or `subscriptions`; the project industry is not sufficient.

- [ ] **Step 1: Add planner tests for defaults and opt-out**
  - Verify ordinary new `portfolio`, `business`, and `ecommerce` specs choose enterprise/full-stack mode, including when a storefront is detected.
  - Verify only an explicit static-only buyer/deployment mode chooses `client-static`.
  - Verify the normalized full-stack/static result controls whether baseline auth, user, and form capabilities are added.
  - Verify legacy `master_prompt` registry content still receives current runtime contract.
- [ ] **Step 2: Run planner tests and confirm the new assertions fail**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_project_mode_engine.py ai-agent\tests\test_reach_integration.py -k "select or planner or static" -q`

Expected: the new default-mode and baseline-feature assertions fail before implementation.

- [ ] **Step 3: Normalize generation mode and feature inputs**
  - Update `ProjectModeEngine.select_mode` so website type alone defaults to full-stack; preserve explicit buyer/deployment static opt-out.
  - Remove/gate the orchestrator's automatic ecommerce/storefront client-static override so a shop receives its requested full-stack default unless the user explicitly opts out.
  - Have planner/orchestrator propagate the normalized mode and baseline features consistently to project builder and API generator.
  - Preserve the runtime website-generation contract when the persisted prompt registry serves an older master prompt.
  - Do not use website type/industry alone to add optional SaaS or payment features.
- [ ] **Step 4: Run planner and orchestrator tests**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_project_mode_engine.py ai-agent\tests\test_reach_integration.py ai-agent\tests\test_orchestrator.py -q`

Expected: PASS; static opt-out and existing mode behavior remain covered.

### Task 2: Generate secure, persistent backend journeys

**Files:**
- Modify: `ai-agent/agent/api_generator.py`
- Modify: `ai-agent/agent/project_builder.py`
- Modify: `ai-agent/agent/project_mode_engine.py`
- Test: `ai-agent/tests/test_enterprise_engines.py`
- Test: `ai-agent/tests/test_schema_contract_injection.py`
- Add or generate: backend auth/form integration tests in each generated full-stack project's `backend/tests/`

**Interfaces:**
- `APIGenerator.generate_full_backend(target_dir: Path, plan: Dict[str, Any]) -> None` generates backend modules from normalized plan features.
- Generated auth routes expose `POST /api/auth/register`, `POST /api/auth/login`, and protected `GET /api/auth/profile`.
- Auth responses use `{success: true, data: {user, accessToken}}`; refresh token is cookie-only. `POST /api/auth/refresh` rotates the refresh token and `POST /api/auth/logout` revokes its database session.
- Generated `POST /api/contact` accepts `{name, email, message}`, validates and persists submissions through Sequelize models, and returns safe, stable error responses.
- Generated migrations are runnable and repeatable through documented backend commands; Sequelize/PostgreSQL is the full-stack default.

- [ ] **Step 1: Add tests for generated backend artifacts and negative paths**
  - Assert default auth/form dependencies, controllers, models, routes, and migration files are generated.
  - Assert password handling uses a hash and login verifies persisted credentials.
  - Assert invalid/duplicate registration, invalid login, invalid form input, and database failures cannot return success.
  - Assert static mode does not generate backend artifacts.
- [ ] **Step 2: Run focused generator tests and confirm new expectations fail**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py -k "api_generator or auth or form or migration" -q`

Expected: FAIL on missing persistent behavior, migration contract, or mode-aware generation.

- [ ] **Step 3: Replace stub authentication and request-echo persistence**
  - Generate database-backed registration/login/profile, refresh, and logout behavior; hash passwords with bcrypt cost ≥12, use 15-minute access JWTs, rotate 7-day refresh tokens in HttpOnly/Secure/SameSite cookies, and store only refresh-token hashes.
  - Generate a persistent contact-submission model/controller/route for `POST /api/contact` with `{name, email, message}` validation.
  - Remove unconditional SaaS feature injection; generate only the baseline and features present in the normalized spec.
  - Keep Sequelize/PostgreSQL configuration consistent; remove or gate conflicting placeholder Prisma/SQLite output rather than generating two competing schemas.
- [ ] **Step 4: Add migrations and generated backend test commands**
  - Generate versioned schema migrations for baseline user and form data.
  - Generate/run backend tests for success and failure paths using the project's existing Jest/Supertest conventions and a supported isolated database strategy.
  - Ensure app startup does not report ready before configuration and required schema setup are valid.
- [ ] **Step 5: Run focused backend tests and verify generated files**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py ai-agent\tests\test_schema_contract_injection.py -q`

Expected: PASS; generated projects contain executable auth/form routes, models, migrations, and test commands.

### Task 3: Wire signup/login and forms in generated frontends

**Files:**
- Modify: `ai-agent/agent/project_mode_engine.py`
- Modify: `ai-agent/agent/project_builder.py`
- Modify: relevant generated frontend template/page modules under `src/templates/`
- Test: `ai-agent/tests/test_enterprise_engines.py`
- Test: `ai-agent/tests/test_orchestrator.py`
- Add or generate: frontend auth/form tests in each generated full-stack project's frontend test suite

**Interfaces:**
- Generated `/login` and `/register` journeys call the generated auth API and expose validated fields, pending, error, and success states.
- The primary contact/business form posts to its generated API route and reports success only after persisted API success.
- API configuration uses the existing generated `frontend/src/services/api.js` convention and does not embed backend secrets.

- [ ] **Step 1: Add generated-frontend tests for real API wiring and states**
  - Verify login/signup routes exist and submit through the API client.
  - Verify invalid input, API failure, pending state, and successful response are represented accessibly.
  - Verify the generated contact/business form does not display a success message on network/API failure.
- [ ] **Step 2: Run focused tests and confirm the assertions fail**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py -k "frontend_auth or frontend_form" -q`

Expected: FAIL until generated forms and API wiring meet the contract.

- [ ] **Step 3: Generate frontend authentication and persisted-form UX**
  - Ensure existing template routes/components are reused rather than appending duplicate pages or replacing established design.
  - Add associated labels, field-level validation/error descriptions, keyboard operation, loading/disabled state, and preserved user input on recoverable failures.
  - Keep local demo data clearly separate from real authenticated or persisted server state.
- [ ] **Step 4: Run focused frontend-generation tests and generated build checks**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py -k "frontend_auth or frontend_form" -q`

Expected: PASS; a fixture-generated frontend also completes its configured build.

### Task 4: Make Docker, environment, and generated docs runnable and consistent

**Files:**
- Modify: `ai-agent/agent/project_builder.py`
- Modify: `ai-agent/agent/api_generator.py`
- Modify: `ai-agent/agent/project_mode_engine.py`
- Modify: `docs/AI_WEBSITE_GENERATION_STANDARD.md`
- Test: `ai-agent/tests/test_enterprise_engines.py`
- Test: generated-project Docker/config/docs checks

**Interfaces:**
- `_generate_docker_setup(target_dir: Path, plan: Dict[str, Any]) -> None` remains the Docker generation entry point for full-stack projects.
- Full-stack `.env.example` files define every required runtime variable with explanatory safe placeholders and no actual usable secret.
- Generated `README.md`/`docs/` provide consistent commands for install, migrations, tests, local Docker startup, and external setup.

- [ ] **Step 1: Add tests for Docker safety/readiness and documentation consistency**
  - Assert Compose has frontend, backend, and PostgreSQL with health/readiness dependencies.
  - Assert no default usable password/JWT secret is present and required secrets fail clearly when absent.
  - Assert migration execution is connected to backend startup and docs reference existing commands/files.
  - Assert static opt-out does not claim or require Docker/backend setup.
- [ ] **Step 2: Run focused Docker/docs generation tests and confirm they fail**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py -k "docker or env or docs" -q`

Expected: FAIL on any missing or contradictory full-stack setup.

- [ ] **Step 3: Correct generated Docker, database configuration, and setup documentation**
  - Remove insecure Compose defaults and source all required values from documented environment configuration.
  - Ensure healthchecks, dependency ordering, migration command, ports, and generated project names align with generated services.
  - Document frontend/backend setup, schema/migrations, test commands, auth/API behavior, form persistence, Docker, optional payments, external credentials, and unverified limitations.
- [ ] **Step 4: Run focused checks and validate Compose syntax when Docker tooling is available**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_enterprise_engines.py -k "docker or env or docs" -q`

Expected: PASS. If Docker is installed, also run `docker compose -f <generated-project>\docker-compose.yml config`; otherwise record Compose runtime validation as not measured.

### Task 5: Make payments conditional, verifiable, and durable

**Files:**
- Modify: `ai-agent/agent/extensions/checkout_stripe.py`
- Modify: `ai-agent/agent/orchestrator.py`
- Modify: `ai-agent/agent/api_generator.py`
- Test: `ai-agent/tests/test_enterprise_engines.py`
- Test: payment scaffolder tests under `ai-agent/tests/`
- Add or generate: sandbox-oriented payment integration tests in commerce projects

**Interfaces:**
- `CheckoutScaffolder(project_dir).scaffold() -> Dict[str, Any]` remains the provider scaffolding entry point but is called only for explicit payment/purchase/subscription requirements.
- Payment state is updated only after signature-verified, idempotently processed provider events; unconfigured/misconfigured webhook verification returns a failure, never `{success: true}`.
- Missing provider credentials are reported as blocked/not measured; no client-visible flow claims a payment succeeded until provider-confirmed state is read.

- [ ] **Step 1: Add payment condition and failure-path tests**
  - Verify ordinary non-payment website generation does not add Stripe dependencies, env keys, routes, or UI.
  - Verify explicit payment features invoke the existing scaffolder.
  - Verify missing signature/secret and invalid signature fail closed; repeated verified event IDs do not apply payment state twice.
- [ ] **Step 2: Run payment tests and confirm failures before implementation**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests -k "checkout or payment or webhook" -q`

Expected: FAIL on accidental payment inclusion, success-shaped webhook fallback, or non-idempotent state.

- [ ] **Step 3: Wire explicit requirements to the existing provider integration**
  - Derive payment inclusion from explicit purchase/subscription/payment features, not generic industry text.
  - Connect checkout to a persisted order/payment record, reconcile state only from verified provider events, and use the provider SDK's supported idempotency behavior.
  - Remove memory-only/unverified webhook success paths and ensure provider configuration errors are surfaced safely.
- [ ] **Step 4: Run payment tests and sandbox checks when credentials are available**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests -k "checkout or payment or webhook" -q`

Expected: PASS for deterministic unit/integration cases. Provider sandbox checks run only when configured; otherwise report them as blocked/not measured.

### Task 6: Gate completeness and report status truthfully

**Files:**
- Modify: `ai-agent/agent/orchestrator.py`
- Modify: `ai-agent/agent/quality_gate.py`
- Modify: `ai-agent/agent/quality_gates.py`
- Modify: `ai-agent/agent/enterprise_architect.py`
- Test: `ai-agent/tests/test_orchestrator.py`
- Test: `ai-agent/tests/test_quality_gate.py`
- Test: `ai-agent/tests/test_enterprise_architect.py`
- Modify: `docs/AI_WEBSITE_GENERATION_STANDARD.md`

**Interfaces:**
- Add a deterministic completeness validator (prefer a focused module under `ai-agent/agent/`, e.g. `generated_project_completeness.py`) returning structured required checks, optional payment checks, status, and blockers for a project directory plus normalized spec.
- A full-stack project cannot receive `complete` or `release-ready` status while any required backend/database/auth/form/Docker/docs check fails.
- Static opt-out evaluates only its explicitly scoped frontend/build/docs requirements.
- Diagnostic ZIP creation remains possible but is separately labeled incomplete and cannot authorize deployment.

- [ ] **Step 1: Add tests for completeness outcomes and release gating**
  - Required artifacts pass for a complete generated fixture; a missing auth endpoint, migration, Docker file, or setup doc creates a specific blocker.
  - Explicit static mode does not fail for intentionally omitted backend files.
  - Payment specs require payment artifacts; non-payment specs do not.
  - Diagnostic ZIP remains available on failure but release/deployment remains blocked and final status is not complete.
  - Guardrail/gate execution order verifies output checks finish before release/deployment decisions.
- [ ] **Step 2: Run focused gate tests and confirm assertions fail**

Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_orchestrator.py ai-agent\tests\test_quality_gate.py ai-agent\tests\test_enterprise_architect.py -k "complete or release or guardrail or static" -q`

Expected: FAIL where current pipeline allows incomplete projects to be called complete or reaches deploy before mandatory output checks.

- [ ] **Step 3: Implement structured completeness validation and gate ordering**
  - Validate generated artifacts and test/build results against normalized project mode and payment scope.
  - Run mandatory output guardrails/completeness checks before deployment; preserve cancellation, diagnostics, and error reporting.
  - Keep external credentials, live provider calls, and live deployment separately marked blocked/not measured when unavailable.
- [ ] **Step 4: Run focused gate tests and final suite**

Run:
`.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_orchestrator.py ai-agent\tests\test_quality_gate.py ai-agent\tests\test_enterprise_architect.py -q`

Expected: PASS. Then run the focused generation/backend/payment test modules from Tasks 1–5. Run the full agent suite with a bounded timeout; if it stalls, report exact completed scope and the blocker without claiming the suite passed.

- [ ] **Step 5: Build documentation and inspect final generated-project fixture**

Run: `npm run docs:build`

Expected: PASS; generation standard documents the full-stack default, explicit static opt-out, conditional payment, verification, and credential limitations.

Review one generated full-stack project and one explicit static fixture. Record actual test/build/Docker/provider outcomes and blockers; do not call an unconfigured live integration deployed or verified.
