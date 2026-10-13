# Generated Websites: Production Readiness — Design Specification

## Status

Proposed for user review. This spec supersedes the previous Sell Today catalog rebuild as the first milestone: the primary target is the website-generating agent and the quality of its future outputs. The 11 Sell Today products are possible later pilot/benchmark inputs, not the first implementation target. Implementation and planning are not authorized until this written spec is approved.

## User intent and success

The user wants websites the agent generates now to be genuinely production-ready, buyer/client handoff quality, and independently listable for sale. The user first wants confidence that the agent works reliably, then plans to add extra features and use it to attract and serve clients. The generated product’s core functionality should be built in and usable. Client-specific external/business setup—payment provider accounts and credentials, hosting, domain registration, and similar services—must be completed by the client, not silently provisioned or represented as already configured by the generator.

Success means the agent creates a complete, coherent product and package, tests the actual generated application, documents deployment and configuration honestly, provides a clear client setup boundary, and does not claim live payment/hosting/domain readiness where client action is still required. “Production-ready” means deployable and operational after documented client-owned configuration; it does not mean deployed or connected to third-party accounts automatically.

## Agreed scope decisions

- First milestone: improve the generator’s production-readiness workflow and evidence gates, not rebuild the current Sell Today catalog first.
- Generated websites must be distinct, industry/brand appropriate, functional, responsive, secure-by-default, accessible, performant, testable and handoff-ready.
- A product package should be independently transferable/sellable with source, required local assets, README, license, setup/deployment guidance, environment-variable examples and truthful QA reports.
- Payment processor accounts/keys, hosting provider/account, domain registration/DNS and analogous client-owned setup remain explicit client tasks. The agent may document integration points or provide code/configuration when requested, but must not create accounts, claim credentials exist, deploy, publish, charge, or change production resources without explicit authorization and required credentials/approval.
- Marketplace listing and deployment publication are not part of the default generator completion gate.
- Existing Sell Today products may later serve as pilot examples after the agent behavior is verified; bulk rebuild is not included in this milestone.

## Existing architecture and constraints

`project-rules/MASTER_PROMPT.md` describes a broad build, Playwright, visual/UX/accessibility/performance/SEO audit, critics, self-healing, deployment, live verification and delivery pipeline. It also contains a universal final checklist requiring `LIVE DEPLOYMENT = PASS`, which conflicts with client-owned hosting/domain setup and non-deployment delivery. The agent already has orchestration, planning, quality gate(s), design/manifest, repair, iteration, browser/vision and deployment-related modules. The implementation must audit actual call paths and enforced behavior rather than assume that prompt text equals executable enforcement.

Extend existing modules and contracts; do not create a parallel generator, quality score, manifest, or deployment system. Keep existing APIs compatible where feasible, treat current project changes as user-owned, inspect before editing, and avoid unrelated provider/auth/security work. Do not claim current tools can complete a check unless the relevant execution path actually ran.

## Scope

### In scope

1. Audit how generation currently defines completion, executes builds/tests/browser QA, handles retries/repair, produces artifacts/reports, and applies deployment gates.
2. Define a machine-readable, versioned production-readiness status/report that separates technical readiness from account-specific client setup and optional deployment.
3. Make required local quality gates evidence-driven and enforceable: build, routes/assets/runtime, relevant user journeys, responsive behavior, accessibility checks, performance/bundle checks, SEO/content/configuration checks, external request review, secrets/dependency safety, and archive/handoff completeness. Record passed, failed, blocked, skipped/not run with command/tool, artifact/evidence, and reason; a missing check is never a pass.
4. Ensure generation produces real working core features and complete UX journeys (loading, success, error, empty, retry/recovery) rather than placeholder flows or manifest-only assertions.
5. Preserve industry/brand-aware design and distinct layouts while ensuring usable responsive and accessible generated behavior.
6. Add a policy boundary for client-owned external tasks. Provide setup instructions and `.env.example` placeholders; never synthesize real credentials, claim external integrations are live, or initiate account/deployment side effects by default.
7. Produce a complete buyer/client handoff: README/product pitch, features, stack/prerequisites, copy-paste local setup, environment-variable table, structure/scripts, testing, deploy guide, customization/troubleshooting, license, asset provenance, QA/performance/a11y reports and known limitations, adapted to the generated project’s actual contents.
8. Add focused tests for gate logic, status schema, evidence provenance, client setup classification, false-pass prevention and package completeness; verify representative real generated outputs through the buyer-facing interface.

### Out of scope

- Rebuilding all 11 Sell Today projects in the first milestone.
- Adding client accounts or automatically provisioning payment, hosting, domain, email, analytics, databases, AI APIs, or other external services.
- Publishing to marketplaces, deploying to production, registering domains, using real payment credentials, or modifying production data by default.
- Guaranteeing legal compliance, licensing clearance, WCAG conformance, uptime or performance targets without the specific audit/evidence.
- Adding unrelated features to the generator before readiness is independently verified.
- Replacing the existing stack or design system wholesale.

## Proposed design

### 1. Readiness contract and honest statuses

Introduce or extend the existing quality report/manifest boundary with one authoritative readiness result, versioned and backward-readable. Represent independently:

- `local_build` and `local_runtime` results;
- automated tests and user-journey smoke checks;
- responsive, accessibility, performance, SEO and visual/UX evidence;
- security/configuration and external-request findings;
- package completeness and asset/license provenance status;
- `deployment_readiness` (configured instructions/artifacts and checks only);
- `client_setup_required` tasks (service/provider, required variable names, owner=client, status=not configured/configured/verified where evidence exists);
- `live_deployment` as `not_requested`, `blocked`, `failed`, or `verified` only when explicitly requested and actually tested;
- known limitations and evidence links/paths.

Use a closed status vocabulary with no implicit success: measured pass, measured fail, blocked, not run/not measured, and not applicable with justification. Existing consumers must not interpret missing values as passed. A weighted overall score cannot override a failed mandatory gate or disguise a blocked check.

### 2. Generator pipeline and gate enforcement

Map current prompt-to-artifact execution and designate existing orchestration points for gate evaluation. For each generated project, enforce local gates before declaring handoff ready: build and parse; route/asset integrity; core functional journeys and state recovery; browser console/network/runtime checks; responsive checks at the project’s defined breakpoints; accessibility automation plus manual-review limitations; performance/bundle measurements against the project’s declared budgets; honest SEO/metadata/structured-data checks; external request review; secret/config/package safety; complete docs and archives. Use evidence produced by tools, not LLM assertion alone.

Classify issues by severity and bounded repair attempts. After each repair, rerun all affected checks and regression breakpoints; stop after the documented retry limit and report unresolved blockers. Preserve generated source/output and evidence artifacts in traceable project-scoped locations. Do not silently weaken tests, gates, thresholds or user requirements to obtain a pass.

### 3. Client-owned integrations and deployment boundary

Generated product functionality should work with local/demo configuration where that is a safe, explicit mode. External provider integrations may be implemented as provider interfaces/adapters and documented configuration surfaces, but live mode remains unavailable until the buyer supplies and validates their own account/keys. Provide `.env.example` with names, purpose, required/optional status and safe placeholders; never include keys in source, logs, archive, frontend-exposed environment or generated claims.

Deployment-readiness means deployment instructions, build output, environment matrix, migrations and hosting-specific notes are prepared and locally verified where possible. Live deployment is a separate opt-in operation, with provider/account selected by the user, explicit environment (preview/production), credentials configured securely, and real-origin verification. Domain and payment setup remain client-owned action items unless explicitly delegated in a later request.

### 4. Package and buyer experience

Define a completeness validator against actual generated files and interfaces. Required deliverables include a product-focused README, `.env.example`, license, install/start/build/test commands, architecture/structure, feature and limitation list, deployment guide, client setup checklist, asset credits/licensing notes, and QA/accessibility/performance reports. Package only product-owned source, needed assets and docs; exclude secrets, local caches, dependencies unless specifically required, temporary artifacts and unrelated repository files. Validate archives by opening and, where feasible, clean extraction plus documented setup.

### 5. Pilot and rollout

First audit existing generation pipeline/gates and the Sell Today product set only as read-only benchmark evidence to select a small representative subset later. Implement the status contract and gate enforcement with focused unit tests, then connect it to generation. Validate a representative generated project end-to-end using the project’s buyer-facing UI and local stack. Expand industry coverage after a real pass/fail run proves the gates distinguish broken, blocked and ready states. Do not mass-edit the existing 11 products in this milestone.

## Acceptance criteria

1. The current generation-to-handoff path is mapped, including which checks are executable, advisory-only, blocked or absent.
2. A single versioned readiness report distinguishes local verified readiness, deployment readiness, client-owned configuration, and live deployment; legacy consumers remain compatible or receive an explicit migration path.
3. Missing/skipped/blocked evidence can never be represented as passed or hidden behind an aggregate score.
4. The final readiness decision is blocked by any mandatory local failure; repairs trigger affected regression checks and respect a bounded retry limit.
5. A representative generated site’s actual core workflows, loading/success/error/empty/retry states, routes and assets are tested through its user-facing interface, not just by inspecting prompts/manifests.
6. The QA flow measures or truthfully marks not measured for responsive, accessibility, performance, SEO and visual/UX evidence; no fabricated values or pass badges.
7. Generated core features function in documented local/demo mode when feasible; missing payment/hosting/domain accounts appear as explicit client-owned setup requirements, not defects mislabeled as live integration and not silently treated as configured.
8. `.env.example`, docs and archives contain no real secrets, and client keys are not placed in public frontend variables or logs.
9. The handoff/package completeness validator checks required docs, configuration examples, test/build commands, asset provenance and safe archive contents.
10. A representative package can be built, opened, cleanly extracted and started using its documented local flow, subject to explicit prerequisites; all failures/limitations are recorded.
11. No deployment, marketplace publication, domain purchase, account creation, production data mutation or push occurs without explicit later authorization.
12. Focused tests and an end-to-end pilot are run; full agent suite results and unavailable checks are reported accurately.

## Risks and limitations

- The master prompt’s documented pipeline may not match actual callable/enforced code paths; the audit must establish evidence before implementation selects modules.
- Existing quality scoring may yield false confidence if inputs are heuristic or absent; gate evidence must be independent of builder assertions.
- Third-party account setup and licensing involve client decisions and external terms; generated documentation must not imply legal or provider approval.
- A universal “production-ready” label is misleading without a defined deployment target; report readiness dimensions and client prerequisites separately.
- Browser tooling, Docker, provider credentials, or external services may be unavailable in local verification; report the exact blocked state, never simulate success.

## Handoff

After the user approves this spec, produce a detailed implementation plan based on the actual call-path audit, file-by-file interfaces, tests and one representative pilot. The user then reviews that plan and selects an execution method. No implementation or external setup is included in this design deliverable.