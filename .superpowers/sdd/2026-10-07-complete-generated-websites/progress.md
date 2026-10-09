# SDD ledger — plan: docs/superpowers/plans/2026-10-07-complete-generated-websites.md

Execution target: `D:\lumicorepro-core` on `master`, explicitly requested as the sole LumicorePro project; do not use or modify the integration worktree. Existing changes were present before this implementation and must be preserved.

Ruling: Execute directly in the requested LumicorePro master checkout instead of creating an isolated worktree — the user repeatedly specified that work belongs in LumicorePro and not a separate worktree; cost if wrong: uncommitted project changes share a branch with this work.

Ruling: Choose native inline execution when the user was unavailable to select an execution method — the six tasks share generator interfaces and native execution avoids handing those interfaces across separate implementers; cost if wrong: a fresh implementer/reviewer per task could catch issues earlier.

Ruling: Treat the unavailable-user fallback on plan review as selecting the recommended native method and approving the pragmatic full-stack design — autopilot was asked to choose a pragmatic default; cost if wrong: the user may have wanted scope or execution changes before implementation.

Ruling: The installed executing-plans skill's `sdd-workspace`, `task-brief`, `task-start`, and `task-done` companion scripts are unavailable in this environment; use this plan-scoped ignored workspace and record each brief, test result, and task completion here manually — no task automation files exist under the installed skill directories; cost if wrong: bookkeeping lacks the companion script's automated output capture.

Pre-flight interface check: Task 1 produces normalized `layout_mode` and separates baseline/requested features; Tasks 2, 3, 5, and 6 consume them. Align on `enterprise` default, explicit `client-static`, baseline `jwt_auth`/`users`/`contact`, and payment only from explicit payment features.

Pre-flight interface check: Task 2 produces auth/contact APIs and migrations consumed by Task 3 frontend, Task 4 Docker/docs, Task 5 payment persistence, and Task 6 completeness checks. Contract: register/login return `{success: true, data: {user, accessToken}}`; refresh token is a cookie; `/api/auth/refresh`, `/api/auth/logout`, protected `/api/auth/profile`; contact `POST /api/contact` accepts `{name,email,message}`.

Pre-flight interface check: Task 4 runtime configuration and migrations are consumed by Task 6 completeness/release checks. Check generated env example, Docker service names/ports, migration command, and required-file names consistently before implementing the validator.

Pre-flight interface check: Task 5 conditional payment files and report are consumed by Task 6. Check the same explicit payment feature keys and missing-credentials status in both scaffolder and gate.

Pre-flight: no unresolved interface conflicts after the above contracts were added to the plan.

Task 1: Ruling: The plan initially assigned mode normalization to the planner alone, but repository inspection found `ProjectModeEngine.select_mode` chooses client-static by default for many site types and `orchestrator.py` force-routes storefronts to static. Update Task 1 to change and test those actual decision points — otherwise the requested full-stack default would remain bypassed; cost if wrong: unrelated mode behavior could regress, so retain explicit static buyer/deployment overrides and verify existing mode tests.

Task 1: complete (commits 44fcfa3..44fcfa3, tests: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_project_mode_engine.py ai-agent\tests\test_reach_integration.py ai-agent\tests\test_orchestrator.py -q` → 68 passed)

Task 2: Ruling: Make the generated PostgreSQL migration chain the only schema authority; preserve planner SQL as non-executable references and remove the competing Prisma/SQLite schema and fake paid-success controller — otherwise generated Docker/runtime configuration could target incompatible databases or report simulated payment as real; cost if wrong: projects that relied on implicit SQLite/demo behavior must configure PostgreSQL and explicit payment providers.

Task 2: complete. Generated default full-stack backend now includes PostgreSQL/Sequelize dependencies, startup-gated database readiness and transactional versioned migrations, bcrypt-cost-12 password persistence, 15-minute access tokens, hashed rotating refresh sessions in HttpOnly cookies, login rate limits, database-backed profile/logout/refresh routes, validated persistent contact submissions, and guarded generated integration tests requiring a dedicated PostgreSQL test database. Removed unrequested SaaS dependencies, phantom route mounts, stale SQLite/Prisma metadata, and fake `paid_simulation` checkout code. Docker no longer auto-runs a competing schema file and requires an explicit database password. Generated database instructions now use migrations.

Task 2 verification: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_generated_website_backend.py ai-agent\tests\test_enterprise_engines.py::TestEnterpriseEngines::test_api_generator ai-agent\tests\test_schema_contract_injection.py::SchemaContractTest::test_render_static_reports_schema_not_applicable -q` → 8 passed. `node --check` passed for every generated JavaScript file. Project-mode and reach-integration tests → 48 passed. A prior wider targeted run found the old schema test still relied on portfolio sites defaulting to static; updated it to request `buyer_type="static"` explicitly, matching the new opt-out contract. PostgreSQL-backed integration tests were generated but not executed because no dedicated PostgreSQL test database was configured.
