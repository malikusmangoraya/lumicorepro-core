# Premium delivery gates — Option A

Date: 2026-10-28
Design approval: Option A, master base, approved in conversation.
Written-spec status: approved; real-3D extension and implementation authorized in conversation.
Base: master at 539fecbf.
Workspace: D:/lumicorepro-core-premium-delivery, feature/premium-delivery-gates.

## Outcome and boundaries

Strengthen the existing factory rather than replace it: genuinely rendered browser evidence, mandatory generation steps that fail closed, truthful generated content, and structurally distinct brand layouts. A successful build or screenshot alone must never certify a usable product.

This slice changes generators, delivery/QA tooling, regression tests and project guidance. Generated application changes must come from the generator, not hand edits to delivered products. Preserve the existing database, migration, auth, tenant-isolation, realtime and video gates.

The initial integration target is FullStackUltraEngine -> run_factory, including every project delivered through that path. Shared BrowserQA callers inherit its corrected verdict. Tests must identify the covered callers and explicitly identify other generation lanes; one factory run is not evidence that every independent engine or arbitrary custom route was verified. Extending a bypassing lane requires a separate integration slice, not a fabricated universal-completion claim.

No database-provider migration, new billing service, live payment, mass regeneration, credential rotation, deployment-protection change, push, or unrelated root-frontend redesign. No new numerical premium/WCAG/performance badge without supporting measurement.

## Evidence that motivates the design

Source locations refer to the approved master revision.

| Evidence | Current consequence |
| --- | --- |
| ai-agent/agent/extensions/browser_qa.py:134-224 | One navigation sets ok=True; missing screenshots, console/page errors and overflow do not determine the passed verdict. |
| ai-agent/agent/extensions/browser_qa.py:153-192 | Breakpoint measurements reuse a 1440px context without resizing. Empty measurement lists also appear clean. |
| ai-agent/agent/extensions/browser_qa.py:102-119 | QA navigates to /index.html, not the SPA home route; the supplied base_url does not select the live origin. |
| ai-agent/agent/factory_pipeline.py:561-575,645-687 | Factory trusts the QA status; local QA precedes the API-origin rebuild. |
| ai-agent/agent/live_verify.py:273-283,1081-1103 | Public-route HTTP checks accept an HTML shell; they do not execute React or prove route content. The existing route inventory is filename-based. |
| ai-agent/agent/fullstack_ultra_engine.py:769-814 | Mandatory kit failures are warnings while success depends only on initial file-write errors. |
| ai-agent/agent/design_forge.py:61-171 | Archetypes vary fonts, colors, radii and glow, not page composition. |
| ai-agent/agent/fullstack_ultra_engine.py:222-609,1119-1131,1196-1307 | Marketing copy includes unproven capabilities and metrics, invented contact details, disconnected currency selection and dead legal links. |

## Architecture and data flow

Keep the responsibilities in the existing modules:

- design_forge.py: deterministic brand tokens plus concrete composition decisions.
- fullstack_ultra_engine.py: render those decisions and capability-backed content; require mandatory generation stages to succeed.
- production_spec_kit.py: existing source of working auth, records dashboard and realtime behavior; preserve these while aligning their visual states.
- extensions/browser_qa.py: one browser execution and evidence-verdict implementation for local and hosted targets.
- live_verify.py: reuse public-route discovery and retain independent HTTP/API proofs.
- factory_pipeline.py: sequence stages, consume evidence, and enforce final delivery status.

Flow: generate -> build -> backend tests -> local browser QA -> database/schema/API hosting -> API-origin rebuild -> frontend deployment -> CORS lock and existing API proofs -> live browser QA -> requested demo verification -> final status.

Local QA catches defects before external hosting. Hosted delivery additionally requires live QA against the final deployed frontend origin after the API rebuild and CORS lock. Local-only runs remain built, never delivered. Do not overwrite local evidence with live evidence.

## 1. Honest browser evidence

### Target and coverage

Without base_url, serve the built distribution on loopback and open /. Do not serve the project root, source files or env files as a substitute for a missing build. With an explicit HTTP(S) base_url, navigate to that target and do not start or silently fall back to a local server. Preserve path prefixes and reject non-HTTP(S) targets. Resolve route URLs within the intended origin.

Use expected_routes() as the existing public-route inventory and include any new public page emitted by this slice. Record every requested route. An authenticated dashboard needs a separate authenticated journey and must not be marked covered merely because login redirected successfully.

For each public route, actually set and verify viewport widths 375, 768, 1024 and 1440 before measurements; add 1920 to satisfy the existing project regression rule. Wait for document/fonts/layout readiness with bounded waits, not unbounded network-idle waits that can hang on a live stream. Capture full-page screenshots with route/viewport-specific filenames.

Check that the route has visible main content corresponding to that requested page, not just header/footer, an empty React root, a generic not-found screen or an unrelated redirect. Match a route-specific visible heading or primary control against an expectation supplied independently of the current DOM; a pathname or data attribute alone is insufficient. Home rendered at /pricing without redirecting must fail. If a caller supplies no page-content expectation, label that route identity unproven rather than inferring a pass. Collect console errors, uncaught page errors, failed required page/assets and rendered overflow. Overflow evidence includes visible clipped content; overflow-x-hidden must not hide a broken layout from the checker. Intentionally contained horizontal scrollers are not page overflow.

### Verdict contract

Return ok, status, failures, requested routes/viewports and per-route/per-viewport evidence. Every result includes actual viewport dimensions, rendered-content outcome, screenshot path, console/page/network failures and overflow offenders. Counts come from actual results, never constants.

Passed requires the complete requested matrix, successful captures, visible route content, no unexpected console/page errors, no required-resource failures and no unintended overflow. Known findings produce failed. Missing runtime produces not_measured; screenshot-only CLI fallback remains partial. Every incomplete state has ok=false. A lost page, missing sample, capture exception or unreadable screenshot cannot pass. Always close browser contexts and the local server.

Keep raw diagnostics bounded and scrub secrets, authenticated URLs and query-string tokens before persisting reports. Do not save auth tokens, cookies or form payloads in QA evidence. Absent performance observations remain null/not_measured, never zero-as-success.

### Factory integration

run_qa consumes the evidence-backed verdict rather than treating status text alone as proof. Both qa and the new live_qa stage must pass for hosted delivery. allow_qa_fail may permit diagnostics to continue, but it must never permit delivered. Existing API, schema and video failures remain independent blockers. Stage summaries and client handoff identify which route/viewport failed and point to saved evidence.

## 2. Mandatory generation and truthful content

File writing, required AI SaaS kit injection, production-spec application, schema mirror generation and required artifact validation are named generation steps. Exceptions or explicit failure results stop generation with success=false and a sanitized stage-specific reason. The factory must not build, provision or deploy after that failure. Missing optional provider credentials remain the existing explicit unavailable-feature behavior; do not require a paid key merely to generate the project.

Validate emitted required artifacts after all generation/repair passes: working auth pages, dashboard/records wiring, realtime hook/feed, migrations and server mounts. Idempotent reruns must pass based on existing valid artifacts, not on a nonempty newly-written list. A swallowed failure or omitted file must not survive as success.

Generated marketing content must describe implemented capabilities and the supplied product context. Remove unsupported certifications, uptime/latency statistics, SLA/proration/trial promises, team invitations and monitoring claims. Do not invent email addresses, customer counts, testimonials or working payment plans. Owner-supplied text is input, not independent certification evidence.

Every emitted navigation link resolves to an implemented route or a real in-page target. Omit unavailable legal destinations rather than fabricate legal policies. Remove the isolated currency selector unless prices genuinely consume its state; this slice does not build new billing or localization subsystems. A plans CTA that only opens registration must say so, not imply a completed purchase or active subscription.

Use focused source/contract checks plus rendered interaction checks. A banned-phrase list alone is not a general truth verifier; report exactly which unsupported defaults and dead controls were removed and guarded.

## 3. Structural premium design

Extend the existing deterministic design object with hero composition, section order, content width, spacing rhythm, surface/card treatment and restrained motion decisions. Reuse existing repository design contracts where compatible; do not introduce a second competing design engine. Preserve repeatability for the same prompt, brand and industry.

| Archetype | Concrete composition |
| --- | --- |
| Aurora | Split introduction with a clearly labeled product/workflow explanation, followed by asymmetric capability sections; no fake live dashboard metrics. |
| Editorial | Left-aligned typographic introduction, reading-column narrative and open divided sections rather than a repeated card grid. |
| Kinetic | Bold stacked introduction, stepped workflow and alternating sections; motion is user-driven or restrained and never required to reveal content. |
| Precision | Compact two-column introduction, structured workflow/details and restrained borders; no decorative status/uptime claims. |

These decisions change rendered markup and section order, not only a data-design attribute or colors. All branches retain the same working public routes, auth entry points and contact submission behavior. Brand/industry context changes appropriate terminology and hierarchy without inventing business features. Explicit prompt requirements unsupported by the existing capability set are reported, not presented as implemented.

Apply one visual system consistently to public pages, auth and dashboard states. Reuse tokens for text, action colors, spacing and surfaces. Check text/button contrast on rendered surfaces, heading hierarchy, visible focus, labeled controls and mobile navigation keyboard behavior. Reduced-motion mode removes nonessential movement without hiding content or controls. Empty/loading/error/success/retry states remain usable.

Automated structural checks prove composition differences and functioning controls. Screenshot review proves whether each rendered design actually meets the intended composition, readability and mobile hierarchy; a hash difference is not proof of premium quality. No numeric taste score is invented.

## 4. Verification and acceptance

Use focused tests during iteration; no full-suite or paid/live generation run by default.

1. Browser unit/regression tests cover console/page error, overflow, missing viewport, failed screenshot, blank route, wrong page at a valid URL, missing content expectation, missing asset, missing runtime, CLI-only capture, live-target selection, SPA root navigation and cleanup.
2. Real local-browser fixtures include both clean and deliberately broken pages: mobile-only overflow, runtime error, missing route content, Home rendered at /pricing without a redirect and broken asset. Assert actual viewport dimensions and that each injected defect fails.
3. Factory tests prove local/live QA failures and partial evidence block delivered, including allow_qa_fail; live QA uses the deployed origin after rebuild/CORS handling. Existing schema/API/tenant/realtime/video blockers remain green.
4. Generator tests inject each mandatory failure and missing-artifact case; generation must stop before downstream work. Valid idempotent application remains successful.
5. Generate representative brands spanning all four archetypes through the actual generator. Build outputs, run affected generated backend tests, start their dev/preview servers and exercise navigation, mobile menu, contact validation and auth/dashboard states in the browser. External calls are isolated for deterministic UI tests; these are not represented as live database proof.
6. For modified form controls, verify success plus invalid-input, server-failure and retry behavior. Keep the existing real API/database/realtime proofs; mocked UI checks do not replace them.
7. Capture/review generated outputs at 375/768/1024/1440/1920 and reduced motion; show actual before/after visual evidence and concrete findings. Review console/network evidence and regressions on unchanged routes.
8. Add enforced regression tests and a concise AGENTS.md rule for each fixed gap. Update CHANGELOG.md and docs/FACTORY.md to describe measured behavior and remaining limitations, not aspirational coverage.

Baseline in the isolated worktree: tests/test_design_forge.py and tests/test_factory_pipeline.py — 59 passed, 2 subtests passed in 2.09 seconds. This is baseline unit evidence only, not a claim that current browser QA or generated visuals are correct.

A subsequent explicitly authorized live delivery must show final frontend browser evidence, API/database/schema/tenant/realtime proofs and the requested demo. Until it runs, report live delivery as not re-verified.

## 5. Approved genuine 3D extension

Optional Three.js / React Three Fiber scenes use the same FullStackUltraEngine and factory gates, not an alternate unverified deployment lane. Explicit 3D prompt intent or a supplied scene contract enables an interactive procedural hero; product-viewer requests require an owner-supplied licensed GLB/GLTF model. Missing product assets are reported as unavailable, never replaced with an unrelated torus and called a product. Custom photorealistic modeling is outside this slice.

Copy supplied assets into the generated public assets directory after validating format, size and local references. Do not fetch arbitrary remote model URLs or allow traversal outside a model bundle; embedded/external glTF resources must resolve within the supplied bundle. API requests must not expose arbitrary server files. Prefer an explicit trusted local CLI asset path and generated-project-relative API references.

Lazy-load the scene and its dependencies. Render a useful static explanation before loading and on mobile or WebGL failure; provide explicit activation, labeled rotate/zoom/reset controls, keyboard operation, nonzero canvas size and reduced-motion support. No automatic rotation is required. Context loss and load failures preserve ordinary navigation/auth/contact functions.

QA distinguishes requested, loading, rendered, fallback and failed 3D capability. A canvas or ready attribute alone is insufficient: check renderer output and actual nonblank canvas pixels, then prove that rotate/zoom changes rendered output. Model failure and context loss must not pass requested 3D delivery. Mobile/reduced-motion usability and supported desktop rendering are separate evidence; intentional mobile fallback does not erase a desktop-rendering requirement.

Regression tests cover dependency/mount integration, invalid/missing assets, all supported scene requests, keyboard interaction, reduced motion, context loss, and real WebGL rendering. Existing incomplete benchmark lanes must fail closed rather than report a README-only website as successful; their coverage remains explicit.

## Delivery and review boundaries

Implementation is sequenced into reviewable changes: browser verdict and matrix -> mandatory generation and content integrity -> structural design rendering -> genuine 3D capability -> factory live-QA integration and complete generated-output verification. They form one approved slice; do not label Option A complete after only its first change.

Self-review must check scope, missing evidence, integration order, cleanup, secret handling and preservation of prior blockers. The written design and genuine 3D extension are approved; implementation is authorized. Keep all work on the isolated branch. No commit, push or external deployment is implied by this spec.
