# Backend Stack Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose or auto-recommend a generated project's backend stack from a validated catalog, while accurately preserving the current Node/Express-only scaffold capability.

**Architecture:** Store the canonical compatibility catalog in `registry/technology-stack-catalog.json`, seed it into the AI agent's existing SQLite registry, and resolve selections in a focused Python catalog/selector module. Carry one validated `backend_stack` object through the React UI, Express proxy, FastAPI requests, planner, and generation report; do not alter the project builder's implementation language.

**Tech Stack:** React 19, Vite, Tailwind, Axios, Express, FastAPI/Pydantic, Python, SQLite, pytest, Jest, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-10-backend-stack-catalog-design.md`

## Global Constraints

- The catalog covers Node.js, Python, PHP, Java, Go, C#/.NET, and Ruby.
- Database choices are PostgreSQL, MySQL/MariaDB, SQLite, SQL Server, and MongoDB; Redis is cache/queue infrastructure, not a primary database.
- API styles are REST, GraphQL, and gRPC; architectures are modular monolith, microservices, and serverless.
- Authentication choices are JWT, OAuth2/OIDC, and session authentication; compatibility is explicit and incompatible combinations are rejected.
- Auto is the default; manual values override only the dimensions explicitly selected.
- Non-Node backend scaffolds are not implemented in this phase; the existing project builder remains Node.js/Express-based and reports scaffold availability honestly.
- Existing domain-specific SQL schema selection stays unchanged and is not represented as portable across database engines.
- Invalid catalog IDs or incompatible combinations must return a client validation error before generation starts.
- Without `backend_stack`, current Node.js/Express generation behavior remains unchanged.

## Review Focus

- **Partial manual selection:** an explicitly chosen language with omitted framework/database must complete to a compatible recommendation; test in Task 2.
- **Cross-field mismatch:** a framework or database belonging to another language must fail with a field-specific validation error; test in Task 2.
- **Unknown or malformed values:** unknown IDs and non-object request values must fail before run creation/credit reservation; test in Task 3.
- **Catalog availability outage:** UI reports catalog-load failure, keeps Auto usable where possible, and does not present stale/manual options as live; test in Task 4.
- **Unsupported scaffold request:** selecting Python/PHP/Java/etc. must not claim their backend code was generated; test in Task 2 and Task 4.

---

### Task 1: Create and seed the canonical technology catalog

**Files:**
- Create: `registry/technology-stack-catalog.json`
- Create: `ai-agent/agent/technology_catalog.py`
- Modify: `ai-agent/database/init_db.py`
- Test: `ai-agent/tests/test_technology_catalog.py`

**Interfaces:**
- Catalog JSON top-level keys: `version`, `languages`, `databases`, `api_styles`, `architectures`, `authentication`, `cache_options`, `queue_options`, `testing_options`, `observability_options`, and `deployment_options`.
- Each language entry has `id`, `label`, `frameworks`, and `scaffold_supported`; framework entries have `id`, `label`, `orms`, and compatible `databases`.
- `load_catalog() -> dict` loads and validates the canonical JSON.
- `seed_technology_catalog(cursor, catalog=None) -> None` writes the catalog to a singleton row in `technology_catalog_index`, keyed by `catalog_id = 1`; store `version`, serialized `catalog_json`, and an update timestamp.
- `get_seeded_catalog(db_path=None) -> dict` reads that SQLite row and returns the catalog; missing/uninitialized storage raises a clear error.

- [ ] **Step 1: Write failing tests** in `test_technology_catalog.py` for catalog values, framework/database compatibility, singleton table seeding, re-seeding without duplicate rows, and preservation of unrelated registry rows.
- [ ] **Step 2: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py -q`; confirm failures identify the missing catalog/table/loader.
- [ ] **Step 3: Add** the JSON catalog with the seven specified language families and framework choices: Express/NestJS/Fastify; FastAPI/Django/Flask; Laravel/Symfony/Slim; Spring Boot/Quarkus/Micronaut; Gin/Echo/Fiber; ASP.NET Core; Rails/Sinatra. Include common ORM, database, API, architecture, auth, cache/queue, test, observability, and deployment options with explicit compatibility metadata.
- [ ] **Step 4: Implement** catalog loading/shape validation and SQLite retrieval in `technology_catalog.py`; create and idempotently seed `technology_catalog_index` during existing `init_database()` startup without dropping or rewriting unrelated tables.
- [ ] **Step 5: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py ai-agent/tests/test_memory_retriever.py -q`; both catalog and existing registry retrieval tests pass.

### Task 2: Resolve selections and report scaffold capability

**Files:**
- Modify: `ai-agent/agent/tech_stack_selector.py`
- Modify: `ai-agent/agent/planner.py`
- Modify: `ai-agent/agent/orchestrator.py`
- Modify: `ai-agent/agent/project_builder.py` (only where the plan's stack is recorded in report metadata)
- Test: `ai-agent/tests/test_technology_catalog.py`
- Test: `ai-agent/tests/test_orchestrator.py`

**Interfaces:**
- `validate_backend_stack(selection: dict | None) -> dict` validates mode and catalog IDs, and returns normalized selection; `None` normalizes to legacy Auto behavior.
- `resolve_backend_stack(spec: dict, selection: dict | None = None) -> dict` returns `mode`, `language`, `framework`, `database`, `orm`, `api_style`, `architecture`, `authentication`, `cache`, `queue`, `testing`, `observability`, `deployment`, `scaffold_supported`, and `scaffold_status`.
- Set `scaffold_status` to `generated` when using the existing Node.js/Express backend path and `catalog_only_not_generated` for every other language; keep `scaffold_supported` as the matching boolean.
- `TechStackSelector.select(spec, selected_backend, selected_schemas, backend_stack=None) -> dict` preserves its existing first three parameters and includes the resolved stack as `backend_stack`.
- `GenerationPlanner.create_plan(..., selected_schemas, tech_stack=None) -> dict` preserves existing call compatibility and records `tech_stack` and `backend_stack` in the plan.
- `AgentOrchestrator.run(..., extra_spec=None)` reads optional `extra_spec["backend_stack"]`, passes it through selection/planning, and includes resolved stack data in the report's selected resources.

- [ ] **Step 1: Write failing tests** for Auto legacy default (Node/Express), each of the seven language families, partial manual override, language/framework/database incompatibility, unknown IDs, `scaffold_supported` true only for Node.js, and plan/report inclusion.
- [ ] **Step 2: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py ai-agent/tests/test_orchestrator.py -q`; confirm the new resolution tests fail before implementation.
- [ ] **Step 3: Implement** validation and deterministic recommendation in `tech_stack_selector.py` using the canonical catalog; prompt signals may recommend only valid catalog combinations, while supplied dimensions override their matching recommendations.
- [ ] **Step 4: Wire** the optional stack through orchestration and planning; keep builder output Node/Express and mark non-Node selections `catalog_only_not_generated` in generated reports.
- [ ] **Step 5: Run** `python -m pytest ai-agent/tests/test_technology_catalog.py ai-agent/tests/test_orchestrator.py ai-agent/tests/test_reach_integration.py -q`; confirm old plan callers still work and all new assertions pass.

### Task 3: Expose catalog and validate generation requests

**Files:**
- Modify: `ai-agent/server.py`
- Modify: `backend/routes/ai.routes.js`
- Test: `ai-agent/tests/test_server_security.py`
- Test: `backend/tests/unit/aiAgent.test.js` (or a focused catalog route test beside it)

**Interfaces:**
- FastAPI `GET /api/technology-catalog` returns `{ "catalog": <catalog JSON> }`; follow current agent API authentication behavior.
- FastAPI `GenerateRequest.backend_stack: Optional[Dict[str, Any]] = None` and `DryRunRequest.backend_stack: Optional[Dict[str, Any]] = None`.
- FastAPI `POST /api/generate` and `/api/generate/stream` validate the optional selection before creating a run, reserving credits, or scheduling generation; invalid input returns HTTP 422 with safe field-specific detail.
- FastAPI `POST /api/dry-run` passes the same selection into stack resolution and returns `backend_stack` plus `scaffold_status`.
- Express `GET /api/ai/technology-catalog` proxies to `/api/technology-catalog` and uses the established safe upstream-failure response.
- Express `/api/ai/generate` and `/api/ai/generate/stream` forward only an object-valued `backend_stack`; reject malformed/non-object values with HTTP 400 before proxying.

- [ ] **Step 1: Write failing tests** proving catalog endpoint shape, valid selection forwarding, malformed selection rejection before agent dispatch, and dry-run resolved stack/scaffold status.
- [ ] **Step 2: Run** `python -m pytest ai-agent/tests/test_server_security.py -q` and `cd backend; node --experimental-vm-modules ./node_modules/jest/bin/jest.js tests/unit/aiAgent.test.js --coverage=false --runInBand`; confirm the new route contracts initially fail.
- [ ] **Step 3: Implement** catalog response and request fields in FastAPI; validate via `validate_backend_stack` at route entry and pass the normalized value into both standard and streaming pipeline calls and dry-run.
- [ ] **Step 4: Implement** the Express catalog proxy and strict generation payload forwarding; keep upstream errors safe and do not turn a malformed value into an implicit Auto request.
- [ ] **Step 5: Run** the focused Python and Jest tests above; valid and invalid paths pass without external provider calls.

### Task 4: Add UI controls, API client, and user-facing documentation

**Files:**
- Modify: `src/pages/Generate.jsx`
- Modify: `src/services/api.js`
- Modify: `ai-agent/README.md`
- Modify: `ai-agent/MASTER_PROMPT.md`
- Modify: `src/i18n/locales/en.json`, `src/i18n/locales/ur.json`, and remaining locale JSON files for new UI labels
- Test: `src/__tests__/api.msw.test.js`
- Test: add focused `src/__tests__/Generate.test.jsx`

**Interfaces:**
- `aiAgentAPI.getTechnologyCatalog() -> Promise<AxiosResponse<{ catalog: Catalog }>>`.
- Generation payload includes `backend_stack` with `mode` plus only explicitly selected catalog IDs.
- UI default is Auto; the standard panel exposes backend language, framework, and database; an advanced panel exposes API style, architecture, authentication, cache, queue, testing, observability, and deployment.

- [ ] **Step 1: Write failing tests** for catalog API client response, Auto default payload, manual language/framework/database payload, advanced options payload, disabled controls while generating, and accessible error/loading behavior.
- [ ] **Step 2: Run** `npm run test -- src/__tests__/api.msw.test.js src/__tests__/Generate.test.jsx`; confirm new contract tests fail before implementation.
- [ ] **Step 3: Add** `getTechnologyCatalog()` and load options in `Generate.jsx`; display clear loading/error state, keep Auto generation available if catalog fetch fails, and prevent stale catalog values from being submitted.
- [ ] **Step 4: Add** accessible labeled manual and advanced selectors; submit only chosen values; include resolved stack and honest scaffold status in the result view without changing existing result behavior when the selection is Auto.
- [ ] **Step 5: Document** supported catalog families, Auto/manual request behavior, endpoint fields, database/schema portability limits, and non-Node scaffold limitation in the agent README and master prompt; add matching labels to every locale JSON with English fallback text where a translated value is unavailable.
- [ ] **Step 6: Run** `npm run test -- src/__tests__/api.msw.test.js src/__tests__/Generate.test.jsx`, `npm run lint -- --no-warn-ignored src/pages/Generate.jsx src/services/api.js`, and `npm run build`; resolve regressions before handoff.

### Final integration verification

- [ ] Run `python -m pytest ai-agent/tests -q`.
- [ ] Run `cd backend; npm run test:unit`.
- [ ] Run `npm run test -- src/__tests__/api.msw.test.js src/__tests__/Generate.test.jsx`.
- [ ] Run `npm run lint` and `npm run build`.
- [ ] Inspect an Auto dry run and a manual non-Node dry run; verify the selected stack is compatible, non-Node scaffold status is explicit, and no non-Node backend files are represented as generated.
