# LumicorePro International Full-Stack Factory Implementation Plan

> **For agentic workers:** Use the executing-plans skill to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make website generation consistently honor a versioned delivery contract and produce verifiably complete full-stack PostgreSQL/auth projects by default, with explicit static-only and requirement-driven payments.

**Architecture:** Resolve a canonical contract from normalized spec and explicit settings, persist it through the planner and builders, and validate emitted artifacts against the same contract. Align the direct FullStackUltraEngine entry point with the canonical contract without breaking its existing public arguments or result fields.

**Tech Stack:** Python 3, existing LumicorePro agent/orchestrator, pytest, generated React/Vite + Express/Sequelize projects, PostgreSQL, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-11-lumicorepro-international-fullstack-factory-design.md`

## Global Constraints

- Full-stack is the default; static-only requires an explicit request.
- PostgreSQL and signup/login/protected account flows are included by default for full-stack projects.
- Payments are included only when the product requires them.
- Do not deploy, provision external accounts, or perform production-side effects.
- Preserve public APIs compatibly; do not alter unrelated products, especially Apex.
- Keep generated `.env.example` placeholders-only and never emit secret values.
- A prompt or manifest claim cannot satisfy an artifact check; inspect generated files and executed evidence.

## Review Focus

- Legacy callers using buyer_type/deployment_mode aliases must retain explicit-static behavior; test aliases and precedence in `test_project_mode_engine.py`.
- Specs expressing payment requirements through feature aliases or absent features must not gain/lose payments; cover in `test_generation_contract.py` and completeness tests.
- Alternate FullStackUltraEngine callers must receive equivalent defaults without breaking arguments/results; cover direct and orchestrator entry points in `test_fullstack_ultra_engine.py`.
- Missing or malformed generated files must not be reported complete; cover missing paths, placeholders/secrets, and parse failures in `test_generated_project_completeness.py`.
- Generation failures / unavailable tools must be represented as blocked or not-run rather than pass; cover evaluator state schema in `test_generated_project_completeness.py`.

---

## File Map

- Create `ai-agent/agent/generation_contract.py`: versioned normalization/resolution for mode, database, auth, feature requirements.
- Modify `ai-agent/agent/planner.py`: resolve and attach contract once while retaining current plan fields.
- Modify `ai-agent/agent/project_builder.py`: consume contract for database/backend scaffold, document/install artifacts, and preserve existing generated-project conventions.
- Modify `ai-agent/agent/project_mode_engine.py`: ensure contract mode drives rendering, retaining compatibility for callers that pass only a spec.
- Modify `ai-agent/agent/fullstack_ultra_engine.py` and `ai-agent/agent/orchestrator.py`: apply the contract to alternate public generation entry path.
- Modify `ai-agent/agent/generated_project_completeness.py`: evaluate actual artifacts against contract and report status/evidence per check.
- Modify `ai-agent/tests/test_project_mode_engine.py`, `ai-agent/tests/test_generated_project_completeness.py`, `ai-agent/tests/test_fullstack_ultra_engine.py`; create `ai-agent/tests/test_generation_contract.py`.

## Task 1: Define and test the generation contract

**Files:** Create `ai-agent/agent/generation_contract.py`; create `ai-agent/tests/test_generation_contract.py`.

**Interfaces:**
- `resolve_generation_contract(spec: dict[str, Any]) -> dict[str, Any]` returns a JSON-serializable contract with `version: 1`, `layout_mode`, `database`, `auth`, `features`, and `requirements`.
- Full-stack contract: `layout_mode="enterprise"`, `database="postgresql"`, `auth=true`; static contract: `layout_mode="client-static"`, `database=null`, `auth=false`.
- Preserve explicitly requested payment feature names; do not infer payment requirement from industry alone.

- [ ] Write tests for ordinary defaults, explicit static aliases, explicit enterprise, payment requested/not-requested, and invalid features input.
- [ ] Run `cd ai-agent && python -m pytest tests/test_generation_contract.py -q`; confirm expected failures.
- [ ] Implement resolver, reusing `ProjectModeEngine.select_mode` semantics rather than duplicating alias lists.
- [ ] Rerun the focused tests and `tests/test_project_mode_engine.py`.

## Task 2: Carry contract through planner and builder

**Files:** Modify `ai-agent/agent/planner.py`, `ai-agent/agent/project_builder.py`, `ai-agent/agent/project_mode_engine.py`; add/extend tests in `ai-agent/tests/test_generation_contract.py` and `test_generated_project_completeness.py`.

**Interfaces:**
- Planner adds `plan["generation_contract"]` and retains `layout_mode`/`features` for compatibility.
- `ProjectBuilder.build_project(plan: dict[str, Any]) -> str` keeps its signature; consumes `generation_contract` when present, resolving from `plan["spec"]` only for legacy callers.
- Project mode rendering keeps existing method signatures; contract mode is authoritative when supplied.

- [ ] Test that planner defaults preserve enterprise/auth features, set PostgreSQL, retain explicit static opt-out, and propagate payment requirements.
- [ ] Test legacy plans without a contract resolve equivalent behavior.
- [ ] Run focused tests to confirm failures.
- [ ] Implement contract propagation and ensure PostgreSQL config/migrations are generated for full-stack and omitted for static-only.
- [ ] Verify existing builder artifact names before changing any generated path; update contract outputs only to match emitted canonical paths.
- [ ] Run planner, builder, and mode tests.

## Task 3: Align the alternate FullStackUltraEngine entry path

**Files:** Modify `ai-agent/agent/fullstack_ultra_engine.py`, `ai-agent/agent/orchestrator.py`; extend `ai-agent/tests/test_fullstack_ultra_engine.py`.

**Interfaces:**
- Preserve `FullStackUltraEngine.generate_project(destination_dir, prompt, brand_name, industry, primary_color)` and `AgentOrchestrator.generate_fullstack_project(...)` arguments and existing result keys.
- Add optional contract support compatibly (keyword-only if needed); existing callers default to full-stack PostgreSQL/auth.

- [ ] Add tests asserting generated output includes PostgreSQL config, migrations, auth, Docker, setup docs, license, and `.env.example`, with no real secrets.
- [ ] Add orchestrator-helper assertion that the effective contract is full-stack/PostgreSQL/auth.
- [ ] Run `cd ai-agent && python -m pytest tests/test_fullstack_ultra_engine.py -q`; confirm new expectations fail where applicable.
- [ ] Generate required files or delegate to shared builder primitives; avoid a second independent contract policy.
- [ ] Test explicit static-only and payment-required behavior if the alternate path exposes those options; otherwise document/validate its supported contract scope and do not silently misrepresent it.
- [ ] Rerun alternate-path suite; report the existing speed threshold without relaxing it.

## Task 4: Make readiness evidence-based and contract-aware

**Files:** Modify `ai-agent/agent/generated_project_completeness.py`; extend `ai-agent/tests/test_generated_project_completeness.py`.

**Interfaces:**
- `evaluate_generated_project(project_dir, spec) -> dict` remains callable as-is and accepts optional `generation_contract` in `spec`.
- Each check reports `name`, `path`, `required`, `status` (`passed`, `failed`, `blocked`, `not_run`, `not_applicable`), and reason/evidence; preserve `passed` booleans for compatible consumers.
- Top-level status is `complete` only when every required applicable artifact check passes; report blockers and payment checks.

- [ ] Add tests that fail on missing artifacts, missing PostgreSQL/migration/auth/Docker/docs/license, unsafe env values, and payment artifacts without a payment requirement.
- [ ] Add tests for static-only non-applicability and blocked/not-run states.
- [ ] Confirm tests fail before implementation.
- [ ] Validate actual generated paths/content from both builders; add parsing/build checks only where the local tooling is available and expose unavailable checks honestly.
- [ ] Implement statuses and contract-aware checks without relying solely on token substrings for critical readiness.
- [ ] Run evaluator tests plus relevant planner/builder suites.

## Task 5: End-to-end generated sample verification

**Files:** Tests only unless a concrete defect is found in files above; do not change unrelated products.

- [ ] Run focused suites: `cd ai-agent && python -m pytest tests/test_generation_contract.py tests/test_project_mode_engine.py tests/test_generated_project_completeness.py tests/test_fullstack_ultra_engine.py -q`.
- [ ] Generate a representative default project using the documented canonical entry point into a temporary directory; inspect the complete output tree and evaluator report.
- [ ] Run frontend install/build, backend install/tests/migrations, and Docker Compose validation only when dependencies/tools are available; record unavailable checks as blocked/not-run.
- [ ] Generate an explicit static-only sample and confirm no backend/database/auth artifacts; generate without payment requirement and confirm no payment integration added.
- [ ] Run relevant broader AI-agent tests and inspect final diff/status to ensure no unrelated or user-owned changes were included.
- [ ] Report exact verification evidence and limitations; do not deploy.

## Self-review

- Spec coverage: defaults, static opt-out, PostgreSQL/auth, requirement-driven payments, artifact validator, alternate entry path, local sample verification, API compatibility, no deployment, and unrelated-file protection are assigned above.
- Artifact paths are to be reconciled against actual generator output in Tasks 2–4; no hypothetical filename is accepted as a completion condition.
- Existing extensive concurrent edits are not owned by this task. Implementer must inspect status before edits and isolate only files/hunks relevant to this plan.
- Plan review and execution-method selection are required before implementation begins.
