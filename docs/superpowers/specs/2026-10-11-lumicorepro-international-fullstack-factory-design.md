# LumicorePro International Full-Stack Website Factory — Design Specification

**Status:** Draft for user review. Implementation is not authorized until this spec is approved.

## Intent and success

The user wants LumicorePro to generate internationally competitive, marketplace/client-ready websites. A normal new-project request should produce a complete, usable full-stack application—not merely attractive frontend markup—with backend, PostgreSQL persistence and migrations, authentication, Docker, tests, environment examples, and project-specific setup/deployment documentation. Static-only output is permitted only when explicitly requested. Payments and other product capabilities are generated when required by the product, not invented as defaults.

Primary audience: marketplace buyers and client handoff recipients. Success means the generated project is coherent, starts from documented local setup, has working product journeys, and makes external configuration and verification status explicit. "International" means designed for the stated industry, audience and market, with localization/RTL/currency/compliance/SEO treated as real requirements rather than an unsupported quality badge. Deployment and external account provisioning are not automatic.

## Agreed decisions

- Full-stack is the default; static-only requires an explicit request.
- PostgreSQL is the default database for full-stack projects.
- Signup/login and protected account flows are included by default.
- Payments are included only when the product requires them.
- Scope includes all essential areas, but is staged into independently testable deliverables rather than one unbounded code change.
- Use current generation/orchestration/build/quality modules; do not create a parallel factory.
- No automatic deployment, marketplace publication, external account creation, or production-side effects.

## Existing architecture and constraints

Current generation is implemented through `AgentOrchestrator`, `GenerationPlanner`, `ProjectBuilder`, `ProjectModeEngine`, `generated_project_completeness`, design/page composition, platform/schema/security injection, quality gates, and deployment helpers. `FullStackUltraEngine` is another exposed generation path with its own defaults and generated scaffolds. `project-rules/MASTER_PROMPT.md` contains extensive international delivery expectations, while executable enforcement and output schemas differ across paths. The existing readiness evaluator assumes some generated filenames and tokens and must be checked against actual builder outputs. Prior design work also exists in the international layout policy, industry-aware design, and generated-site readiness specs; reconcile and reuse those decisions rather than duplicate them.

The checkout has many concurrent/user-owned edits, including AI-agent and Apex files. Before implementation, inspect status and use only approved file scopes; do not overwrite or stage unrelated work. Extend existing public interfaces compatibly where feasible. Prompts alone are not enforcement: generated artifacts and executed checks are the evidence.

## Scope and phased deliverables

This program is decomposed into sequential design/implementation cycles. Each phase gets its own reviewed spec and implementation plan where subsystem boundaries warrant it.

### Phase 1 — Full-stack generation contract and delivery baseline

- Audit every generation entry path and identify canonical vs alternate builders, mode selection, artifact writers, and testable outputs.
- Define one versioned delivery contract carried from requirements/planning to builder and completion report.
- Enforce the agreed defaults: full-stack, PostgreSQL, auth. Explicit static-only opts out of backend/database/auth. Keep feature selection product-relevant; do not add payments without a requirement.
- Ensure the standard full-stack artifact set is coherent and runnable: frontend, API, PostgreSQL configuration, versioned migrations, auth routes/flows, validation/security configuration, Dockerfiles/Compose, `.env.example`, tests, README/setup/deploy instructions, and license/handoff basics.
- Make the completion validator inspect real output files and behaviors from the canonical builder; distinguish missing, failed, blocked and not-run checks. A prompt or manifest claim cannot satisfy an artifact check.
- Verify an actual generated sample locally from documented setup as tools permit; do not deploy.

### Phase 2 — International product/design quality

- Connect existing design DNA, industry/brand playbooks, page composer, i18n/localization, RTL, currency, privacy/consent, SEO/metadata and asset provenance to emitted pages and features.
- Preserve user constraints and existing layouts during ordinary updates; redesign only when requested.
- Ensure international features are appropriate and honest: no fake testimonials, metrics, legal-compliance claims, or fabricated localized content.
- Validate representative industry outputs structurally and via the buyer-facing app.

### Phase 3 — Evidence-based QA, recovery, and package handoff

- Enforce build/test/runtime and core-journey checks; responsive, accessibility, performance, SEO, security, external-request and package checks run when tooling exists.
- Record evidence and report `not measured`, `blocked`, or `not applicable` with reason when a check did not run; never infer a pass.
- Bound repair attempts and rerun affected regressions after changes.
- Verify generated docs and archives, secret exclusion, clean extraction, and documented local startup; distinguish local readiness, deployment readiness, client setup, and live deployment.

The sequence above is a program roadmap; this first implementation plan should focus on Phase 1 only. Phases 2 and 3 follow after Phase 1 passes its acceptance gate, preventing simultaneous changes to several independently testable systems.

## Proposed architecture

A canonical generation contract should be resolved once from normalized prompt/spec and explicit user settings. The orchestrator passes it to the planner and canonical builder; the builder emits artifacts according to that contract, and a deterministic evaluator inspects those artifacts and reports blockers. Existing alternate entry paths must either consume the same contract or be explicitly marked legacy and covered by compatibility tests; they must not silently produce a weaker default.

Mode rules: absent an explicit static-only request, select full-stack. Full-stack selects PostgreSQL and auth as agreed. Static-only selects no backend/database/auth. Optional product capabilities such as payments follow analyzed/explicit requirements. User-provided technology constraints remain respected where compatible; any conflict with the fixed default must be recorded and resolved rather than silently ignored. Deployment remains an opt-in external operation.

## Acceptance criteria for Phase 1

1. The actual generation call graph and all public entry paths are documented; tests exercise the canonical path and any supported alternate path.
2. An ordinary generation request produces a full-stack contract with PostgreSQL and auth; an explicit static-only request produces a static contract without backend/database/auth.
3. Explicit product requirements for payments are propagated; absent such requirements, payment routes/SDKs are not added by default.
4. The builder and readiness evaluator agree on exact artifact paths and validate files actually emitted, not hypothetical names.
5. A full-stack output includes frontend, backend, PostgreSQL connection/configuration, versioned migrations, working auth, Docker setup, safe environment example, tests, setup/deploy instructions, and license/handoff basics.
6. No generated secret values are present in source or examples; `.env.example` contains placeholders only and frontend-exposed variables contain no server secrets.
7. Readiness distinguishes pass/fail/blocked/not-run/not-applicable and cannot mark a missing artifact or unexecuted check as passed.
8. A representative generated project is built and exercised through its intended local interface as far as available dependencies/tools allow; limitations are reported accurately.
9. Existing generation/update APIs remain compatible or receive a tested migration path; no deployment/account provisioning occurs.
10. Tests and final diff do not modify unrelated products such as Apex.

## Risks and exclusions

- The alternate `FullStackUltraEngine` may diverge materially from the canonical builder; the call-graph audit will decide whether to align it in Phase 1 or formally restrict it. It cannot be ignored if user-facing entry points call it.
- Existing test expectations may encode outdated mode defaults. Update only those made invalid by the approved contract; do not weaken assertions or mask unrelated failures.
- Generated artifact evaluation based only on token matching risks false positives; add behavioral or parse/build checks where practical.
- PostgreSQL service availability, Docker, browser tooling, or external credentials may be absent locally. Record checks as blocked/not measured; never fabricate success.
- Legal, tax, privacy and accessibility compliance cannot be guaranteed by templates; provide relevant implementation surfaces and honest limitations.

## Out of scope

Bulk rebuilding existing products; automatically deploying, publishing, buying domains, provisioning third-party accounts, or modifying production data; guaranteeing legal certification or specific performance scores without evidence; adding payment integrations to products that do not require them; replacing the framework stack wholesale; unrelated security/tenant work.

## Handoff

After approval of this written spec, create a Phase 1 implementation plan based on a fresh call-graph/artifact audit, with exact files, interfaces, red/green tests and a sample-generation verification path. The user must review the plan and choose the execution method before implementation.