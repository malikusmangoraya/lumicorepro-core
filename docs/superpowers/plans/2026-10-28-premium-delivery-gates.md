# Premium delivery gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make generated full-stack delivery fail closed on incomplete generation, misleading content, unrendered routes and broken requested 3D, with distinct usable layouts.

**Architecture:** Preserve FullStackUltraEngine and run_factory as the integrated lane. BrowserQA owns rendered evidence; design_forge owns deterministic compositions; modern_3d_engine owns locally bundled real scenes. Generator writes an independent QA expectation manifest; factory validates local and final hosted matrices without weakening API/schema/tenant/realtime/video gates.

**Tech Stack:** Python, pytest, Python Playwright/Chromium, React 19, Vite, Tailwind 3, Express/PostgreSQL, Three.js/React Three Fiber/Drei.

**Spec:** docs/superpowers/specs/2026-10-28-premium-delivery-gates-design.md

## Global Constraints

- Work only in D:/lumicorepro-core-premium-delivery on feature/premium-delivery-gates; base 539fecbf.
- No commit, push, external hosting, live payment, provider migration or owner credentials.
- Preserve database migrations, authentication, tenant isolation, records CRUD, realtime and video blockers.
- Run focused tests only; browser/build tests are required for generated UI. Missing runtime is not success.
- Measure 375/768/1024/1440/1920 actual viewport widths; reduced-motion usability is independently checked.
- Do not repair generated products manually: fix emitters and regenerate.
- No invented certification, uptime, payment, testimonial, metric or numeric quality badge.
- Each fixed gap receives an automated regression test and an AGENTS.md note. Update CHANGELOG.md and docs/FACTORY.md.
- No arbitrary remote model downloads or API-exposed local server paths; trusted local CLI accepts owner model paths.
- No nested subagents. Runtime exposes no model override/resume; inherit session model and use fresh agents with prior reports for fix rounds.

## File responsibilities and interface map

- agent/extensions/browser_qa.py: safe built-output server, requested route/viewport matrix, bounded diagnostics, screenshot validation and fail-closed summary.
- agent/design_forge.py: deterministic composition fields plus shared generated tokens/styles.
- agent/premium_layouts.py (new): focused JSX emitter for truthful public shell/pages; keeps large fullstack module from acquiring another template block.
- agent/fullstack_ultra_engine.py: mandatory named generation stages, final artifacts, template/3D integration, QA manifest.
- agent/modern_3d_engine.py: genuine lazy scenes, safe local GLB/GLTF bundling, fallback and accessible controls.
- agent/benchmark_3d_factory.py: reject unimplemented generic lanes and surface write errors.
- agent/generation_contract.py: explicit optional scene request normalization.
- agent/factory_pipeline.py: prompt/CLI contract propagation, local/live QA evidence and delivered decision.
- main.py: trusted local --deliver-scene and --deliver-model options. API can request procedural scenes, but never pass arbitrary model paths.
- agent/live_verify.py: public route inventory remains shared; existing API proofs preserved.
- tests/test_browser_qa.py, test_premium_generation.py, test_modern_3d_engine.py and focused existing tests: regressions.

### Task 1: Replace screenshot-only success with an evidence-backed browser matrix

**Files:** Modify ai-agent/agent/extensions/browser_qa.py; create ai-agent/tests/test_browser_qa.py.

**Interfaces:** Preserve run_browser_qa(project_dir, base_url=None). Extend BrowserQA and wrapper with keyword-only route_expectations=None and viewports=None for explicit callers/tests. Default expectations load project-root qa-contract.json with shape {"version":1,"routes":{"/":{"heading":"Brand"},"/features":{"heading":"What you can do"}}}. Default routes use expected_routes(project_dir), union manifest routes; a route without a valid expectation fails identity. Optional scene contract remains available for Task 4/5. Save local qa/qa-report.json and live qa/live/qa-report.json separately.

Return {ok:bool,status:str,requested_routes:list,requested_viewports:list,results:list,failures:list,screenshots:dict,evidence:dict}. Each result contains route, requested/actual viewport, rendered_content, screenshot, console_errors, page_errors, network_errors, overflow, failures, ok. Only a nonempty complete matrix with every successful result can pass. Include a reusable evidence_passes(report) consumer check that verifies exact unique matrix keys and successful screenshot evidence rather than trusting report.ok/status alone.

- [ ] Write tests before implementation. Initial regression:
```python
def test_no_build_cannot_pass(tmp_path):
    (tmp_path / 'index.html').write_text('<main><h1>Home</h1></main>')
    result = BrowserQA(str(tmp_path)).run()
    assert result.get('ok') is False
    assert result['status'] == 'failed'
```
- [ ] Run py -m pytest tests/test_browser_qa.py -q -p no:randomly from ai-agent (through py os.chdir on Windows); observe failure.
- [ ] Implement built-only roots, urllib path parsing, reject traversal/dotfiles, only extensionless SPA fallback; missing JS/image returns 404. Live HTTP(S) target uses supplied path prefix without starting local server, rejects credentials/query/fragment and non-HTTP(S) targets.
- [ ] Implement actual viewport contexts and bounded readiness (domcontentloaded, fonts timeout, two animation frames). Collect errors per sample; screenshots are full-page PNG, check signature/positive size, route-specific names. Independent expected visible heading must be in visible main, not only header/footer. Wrong-page/blank/redirect/missing expectation must fail. Measure visible overflow even if body hides overflow, excluding intentional contained scrollers and hidden elements.
- [ ] Add tests for missing matrix member/duplicate member, screenshot failure, no runtime, CLI partial, launch failure cleanup, server shutdown, live origin/prefix, wrong-page, console/page error, broken assets, mobile overflow and intentionally contained scroller. Red then green each batch. Runtime-unavailable tests must explicitly patch acquisition; real browser fixtures must not silently skip required runs.
- [ ] Run focused tests and real Chromium clean/broken fixtures. Capture actual viewport assertions, confirm unmeasured LCP remains null. Sanitize token/credential diagnostics and cap stored messages; never store payloads/cookies.
- [ ] Review actual changes and independent task review before marking complete.

### Task 2: Fail closed on mandatory generation and validate final artifacts

**Files:** Modify ai-agent/agent/fullstack_ultra_engine.py; create ai-agent/tests/test_premium_generation.py; extend ai-agent/tests/test_factory_pipeline.py where generation failure is consumed.

**Interfaces:** generate_project retains signature/result fields and adds generation_steps:list[{name,ok}], failed_stage:string on failure. Required stages: file_write, ai_saas_kit, production_spec, schema_mirror, repair, artifacts. Any exception/explicit failure stops subsequent stages. Error messages identify stage and exception class, not raw exception text containing secrets. Valid idempotent kit applications remain acceptable even if their written list is empty.

- [ ] Write parameterized failure injection tests for each stage, using real generated files except the injected stage failure. Assert success false and no later provisioning/build. Example:
```python
def test_kit_exception_blocks_generation(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('secret-value')
    monkeypatch.setattr('agent.ai_saas_kit.inject_ai_saas_kit', fail)
    result = FullStackUltraEngine().generate_project(str(tmp_path), brand_name='North')
    assert result['success'] is False
    assert result['failed_stage'] == 'ai_saas_kit'
    assert 'secret-value' not in str(result)
```
- [ ] Observe failures using focused pytest; inspect actual kit return conventions before testing explicit status failures.
- [ ] Replace warning-and-continue mandatory paths with named stage recording and early unsuccessful result. Surface concurrent write errors, schema/repair errors, and preparation errors consistently.
- [ ] Validate nonempty emitted auth pages, auth request wiring, dashboard/records fetch wiring, realtime hook/feed and server mounts, migrations and schema mirror after repair. Validate expected markers and presence, not newly-written file counts. Keep existing schema equivalence gates intact.
- [ ] Test omitted/corrupted required artifacts after repair, explicit failure return, idempotent generation and safe brand content. Run focused generator plus existing schema/production tests.
- [ ] Review actual diff and independent task review.

### Task 3: Render truthful, structurally distinct public layouts

**Files:** Modify ai-agent/agent/design_forge.py, fullstack_ultra_engine.py and production_spec_kit.py; create ai-agent/agent/premium_layouts.py; extend test_design_forge.py and test_premium_generation.py.

**Interfaces:** build_design adds composition:{hero,section_order,content_width,spacing,surface,motion}. render_public_files(brand,industry,design) -> dict[str,str] returns frontend src App, Navbar/Footer and public pages; no filesystem side effects. Fullstack uses these instead of superseded _MARKETING_PAGES. route_expectations(brand) returns independent manifest headings for /, /features, /pricing, /about, /contact, /login ('Sign in'), /register ('Create your account'). Home heading is brand, other headings stable. Include scene mount placeholder only via explicit emitter argument scene_enabled=False.

- [ ] Write structural tests asserting four different hero structures/section orders, determinism, matching expectations, JSX-safe brand serialization, and absence of unsupported defaults. Assertions cover actual emitted structure, not just data-design.
```python
def test_archetypes_have_distinct_compositions():
    values = [build_design(b, i, '#2563eb', '#0d9488')['composition']
              for b, i in [('Aurora Brand', 'saas'), ('Editorial', 'legal'),
                           ('Kinetic', 'gaming'), ('Precision', 'fintech')]]
    assert len({v['hero'] for v in values}) == 4
```
Resolve an actual deterministic aurora brand in tests rather than assuming this sample hashes to aurora.
- [ ] Run tests red. Implement split asymmetric aurora, reading-column/divided editorial, stacked/stepped kinetic, compact two-column precision using shared tokens. Preserve all existing auth/records/contact functionality.
- [ ] Replace fabricated metrics/certification/email/pricing plans with actual capability descriptions and registration/contact CTAs. No inactive currency selector or href='#'. Navbar uses focus-visible controls, aria-expanded/controls, Escape close/focus return, skip link and mobile close-on-navigation. Lazy route loading. No autoplay motion.
- [ ] Keep contact frontend/backend validation and submission behavior, but add truthful success/error/retry states. Align auth/dashboard page surfaces/actions with tokens without changing endpoints or tenancy.
- [ ] Emit qa-contract.json independent route headings. Add actual artifact test and ensure production kit does not overwrite public design.
- [ ] Build generated representatives, start dev/preview server and browser-test all four at five widths/reduced motion. Exercise navigation, mobile keyboard, contact invalid/success/error/retry and auth/dashboard loading/empty/error/success with isolated APIs. Capture before/after screenshots; report these are UI evidence, not live DB proof.
- [ ] Review diff and independent task review.

### Task 4: Integrate optional genuine 3D with safe assets and explicit capability evidence

**Files:** Modify ai-agent/agent/modern_3d_engine.py, generation_contract.py, fullstack_ultra_engine.py, benchmark_3d_factory.py, main.py; create ai-agent/tests/test_modern_3d_engine.py; extend test_premium_generation.py and test_benchmark_3d_factory.py.

**Interfaces:** Contract optional scene={archetype:'floating_crystal'|'cyber_grid'|'particle_cosmos'|'product_viewer',model_path?:str}. Trusted local generation/CLI can supply model_path; HTTP factory request remains without local-file asset fields. Explicit 3D prompt defaults floating_crystal; showroom/model-viewer prompt with no model fails with actionable missing model reason. inject_3d_experience adds keyword-only model_path=None, validates actual frontend root, installs package manifest dependencies, writes lazy Modern3DScene shell + SceneCanvas, mounts through public emitter. Output includes success, files and scene contract; no direct npm installation inside emitter.

- [ ] Red tests for absent frontend motion directory selecting wrong root, unknown/CSS archetype rejection for genuine scenes, product without model, malformed/missing/oversized GLB/GLTF, traversal/absolute/remote external glTF URI, symlink escapes, model copies, dependencies and lazy mount.
- [ ] Implement local model bundle validation (50 MiB total ceiling; glTF version 2, GLB header/length/JSON chunk; bounded local binary/image references; no script content or arbitrary URI network fetch). Store under public/assets/models, preserve safe relative resource structure; never persist original local path in public files/reports.
- [ ] Implement lazy shell activated by visible Enable 3D button, fallback explanation, error boundary and context-loss recovery; no remote environment preset. Use on-demand rendering, actual geometry/model, lights, OrbitControls and labeled Rotate left/right, Zoom in/out, Reset view buttons. Keyboard controls work with buttons; reduced motion has no continuous animation; mobile remains static until activated.
- [ ] Emit scene root data-scene-state and renderer frame count/draw-call observations for QA, but do not use attributes alone as rendering proof. Retain nonzero canvas and static content if activation fails.
- [ ] Generic Benchmark3DFactory unsupported verticals return success=false before file writes; consumed futures report write exceptions instead of unconditional success. Existing realestate lane stays explicitly separate, not certified by integrated factory claims.
- [ ] Run actual generated browser WebGL checks: activate, validate nonblank canvas pixels via captured canvas PNG, rotate/zoom changes pixels, supplied fixture model loads, context loss/missing model fails. Test mobile fallback and reduced motion plus ordinary page regressions.
- [ ] Review actual changes and independent task review.

### Task 5: Require final hosted browser evidence and requested 3D proof

**Files:** Modify ai-agent/agent/factory_pipeline.py, extensions/browser_qa.py and main.py; extend test_factory_pipeline.py and test_browser_qa.py.

**Interfaces:** run_qa(project_dir,base_url=None) calls browser wrapper and evidence_passes; forwards bounded failures/results/report path. deliver_from_prompt(...,scene=None) resolves optional scene intent, preserves ordinary contract and returns early on generation failure. CLI passes trusted asset contract; server's existing payload does not expose asset paths. run_factory adds stages.live_qa after deployment/CORS/API proofs and before video/final status; no live URL means not delivered.

- [ ] Red tests: status='passed' without evidence fails; qa/live_qa failed/partial/missing matrix blocks delivered even allow_qa_fail; final deployed origin selected after API rebuild and CORS. Tests must build meaningful report fixtures, not mocks returning status text only.
- [ ] Use evidence_passes on both stages. Preserve all existing blockers, no removal of local failure at final accumulation. Store separate local/live reports and concise route/width failure summaries.
- [ ] Browser scene proof consumes manifest scene requirement on home at desktop width (1440 preferred, chosen tested width >=1024 otherwise); activate, wait bounded, capture canvas pixels, require nonblank colors and changed pixels after rotate/zoom plus draw-call/frame observations. Check context state and propagate asset/runtime errors. Mobile static fallback stays separate evidence. A fallback never satisfies desktop 3D proof.
- [ ] Add real fixture/mocked unit tests for requested 3D rendered/fallback/blank/context-loss; preserve ordinary 2D behavior. Run focused factory, browser, contract and existing API/schema/realtime tests.
- [ ] Review actual diff and independent task review.

### Task 6: Complete generated-output verification and permanent guidance

**Files:** Modify AGENTS.md, CHANGELOG.md and docs/FACTORY.md; extend focused generator/browser tests as needed. Add ai-agent/tests/test_premium_browser.py for explicit opt-in generated UI browser acceptance if useful.

- [ ] Run all affected unit/regression suites and generated backend tests. Do not run unrelated repository suites or deploy externally.
- [ ] Generate four real archetype representatives and a supplied-model 3D representative through FullStackUltraEngine, build them, run dev/preview servers and exercise the acceptance journeys described in Tasks 3–5. Use locally authored procedural GLB test fixture, not an unlicensed downloaded model.
- [ ] Save browser evidence per project, inspect screenshots with Read. Confirm real viewports, meaningful headings, keyboard focus/mobile controls, contrast, no overflow/console/asset errors, contact and auth/dashboard states, 3D rendering/interaction/context loss. Negative fixtures must fail. No manual generated-code edits.
- [ ] Replace contradictory AGENTS footer fake-status rule with truthful implemented-only controls. Add concise enforceable rules for complete browser matrices/local+live evidence, mandatory generation, composition/content, safe 3D assets and genuine rendering proof. Document covered/unsupported lanes and external/live evidence not rerun.
- [ ] Run git diff --check, inspect actual changes and request whole-change review. Fix confirmed issues, rerun covering tests; keep work uncommitted.
- [ ] Report verified evidence and remaining limitations in concise user-facing summary, with no universal perfection claim.

## Execution record

Plan self-review: Tasks 1/5 share browser report interface; Task 1 creates core matrix, Task 5 adds scene proof. Tasks 2/3/4 share generator sequentially. Tasks 3/4 share scene mount argument. Tasks 4/5 share scene contract/CLI propagation. Task 6 consumes all evidence. Each task's tests target its declared files and interfaces; no contradictory completion criterion found.

Ruling: Existing AGENTS fake operational badge guidance is superseded by the approved truthful-content spec; replace it in Task 6. Cost if wrong: footer copy review, not lost functionality.
Ruling: No commits authorized, so reviews inspect unstaged and new-file diffs rather than BASE..HEAD commit-only packages. Task state is tracked here and in session tasks; no automatic git-ignore/config changes or workspace deletion.

Task 1: complete. `browser_qa.py` enforces complete unique route×width matrices (375/768/1024/1440/1920), visible main headings, full-page PNG width evidence, bounded diagnostics, required assets including below-fold lazy images, overflow, and reduced-motion measured from navigation in its own context. Independent review confirmed 3 critical + 1 important defects; all fixed with regressions. `tests/test_browser_qa.py`: 99 real-Chromium tests pass.
Task 2: complete. Named mandatory stages fail closed, sanitized errors, migration export contracts, corrupt idempotent AI files, missing imported dependencies and internal repair I/O are regression-covered. Independent review's fourth finding (disconnected migration `up`/`down`/exports) fixed with 4 regressions. `test_premium_generation.py` + focused suites: 153 passed with factory gates.
Task 3: complete. `design_forge` composition + `premium_layouts` emitter are integrated into the generator; `qa-contract.json` and favicon are emitted. Four representatives generated and built: Evergreen/saas, Northstar/legal, Meridian/gaming, Ledger/finance — each passed 35/35 real browser samples with zero diagnostics. The opt-in generated-UI suite (mobile keyboard nav, auth shell, contact invalid/error/retry/success) passed 25/25 against Evergreen. The browser gate initially missed a legitimate `<header>` hero inside `<main>`; fixed with a regression. The mobile-nav test locator was corrected to a stable selector after the accessible name legitimately changed to "Close navigation".
Task 4: complete. Genuine lazy Three.js engine, safe local GLB/glTF bundling, scene contract/CLI flags and generator `scene` stage implemented; unsupported benchmark lanes fail closed. Prism3D built and proved: 1 frame, 26 draw calls, 523-colour 1054×513 canvas, 10.15 % pixel change after rotate, static mobile fallback. PrismViewer loaded a local original glTF 2.0 fixture and proved 2 frames, 1 draw call, 36 colours and 4.32 % pixel change. The real build exposed an `omni_repair_engine` defect (escaped JSX quotes + unterminated Suspense around self-closing Canvas); fixed with a build-level regression. Final review fixes: legacy CLI failure formatting, generic-product intent narrowed to procedural, and manifest-vs-node_modules install check for reuse.
Task 5: complete for local evidence. Factory `live_qa` runs after rebuild/CORS against the final origin; scene proof requires nonblank canvas pixels, frame/draw calls, pixel change after rotate and static mobile fallback. Positive real browser report, supplied-model scene proof and real scene failure flow are regression-tested. External hosting was not authorized and was not run.
Task 6: complete. Baseline, four 2D representatives, Prism3D and PrismViewer evidence captured under `generated-projects/premium-verification/`; AGENTS/component standards updated to truthful controls; FACTORY.md and CHANGELOG updated; affected suites 382 passed + 14 opt-in skips + 5 subtests, then 208 targeted after final review fixes. Whole-change review returned NOT READY on four issues; all were fixed and a scoped re-review returned PASS. Its two residuals (self-closing Canvas with arrow props, stale server archetype description) were also fixed with regressions. Work remains uncommitted as authorized.

Ruling: Disjoint controller work on generator/factory proceeds during the browser agent's implementation; no source files are shared. All changed areas still require independent review. Cost if wrong: integration rework, contained to this worktree.
