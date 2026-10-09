# Design System Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every newly generated LumicorePro website use deterministic, niche-aware layout DNA and tokenized page compositions, with portfolio uniqueness, content provenance, responsive evidence, and a read-only diversity preview CLI.

**Architecture:** Keep visual style/token resolution in the existing `DesignStyleEngine`; add a deterministic `DesignSystemEngine`, declarative layout recipe library, and isolated SQLite fingerprint registry. Resolve the canonical DNA before building, render the chosen hero/navigation/sections into generated frontend pages, persist it through `DesignManifestWriter`, and gate the artifact before release status. Existing legacy manifests and flag-based CLI use remain supported.

**Tech Stack:** Python 3, existing React/Vite/Tailwind generated frontend, SQLite (`sqlite3`), existing pytest suite, existing `agent-browser` integration where installed.

**Spec:** [2026-10-08-design-system-engine-design.md](../specs/2026-10-08-design-system-engine-design.md)

## Global Constraints

- Provide at least 12 hero archetypes, 8 navigation patterns, and 10 niche-aware section blocks.
- Selection is deterministic from normalized brief, niche, project name, and seed; explicit constraints win.
- Store portfolio fingerprints in SQLite and compare hero, navigation, and Home section order.
- Maximum three complete layout candidates; unresolved collisions remain a failed uniqueness gate.
- Design blocks use semantic tokens for all colors and layout dimensions.
- Unsupported stats, logos, testimonials, generic phrases, and cross-niche copy fail validation.
- Browser tooling unavailable means `not_measured` and release readiness blocked, never pass.
- Preview must not write project files or mutate the registry.
- Do not rewrite the existing 11 curated products or discard any existing worktree changes.
- Preserve legacy manifest fields and all existing CLI invocations.
- Commit each coherent, tested implementation task separately; stage only task-owned files.

## Review Focus

- **Legacy prompt/manifest:** older project specs omit audience, tone, seed, or DNA; resolve stable defaults and keep manifest reads backward-compatible.
- **Similarity exhaustion:** more than two prior candidates collide; stop after exactly three attempts and record a failing result instead of claiming uniqueness.
- **Explicit constraints:** user-selected hero/style/reference constraints conflict with niche weights; constraints remain unchanged and incompatibility is reported.
- **Content evidence:** user supplies real metrics/logos/testimonials; preserve those with provenance while rejecting unsupported claims and false-positive neutral wording.
- **Browser absence:** screenshots cannot run on the current host; distinguish infrastructure unavailability from a measured responsive failure and block release readiness honestly.

---

### Task 1: Build the DNA selector and SQLite registry

**Files:**
- Create: `ai-agent/agent/intelligence/design_system_engine.py`
- Create: `ai-agent/agent/intelligence/design_registry.py`
- Test: `ai-agent/tests/test_design_system_engine.py`
- Test: `ai-agent/tests/test_design_registry.py`

**Interfaces:**
- `DesignSystemEngine.resolve(spec: dict, prior: list[dict] | None = None) -> dict` returns the versioned `design_dna`, its fingerprint, similarity comparison, and up to three selection attempts. It is deterministic and does not write files.
- `DesignRegistry(db_path: Path).initialize() -> None`, `.list_signatures(exclude_project: str | None = None) -> list[dict]`, and `.record(project: str, fingerprint: str, dimensions: dict) -> None` manage only the new portfolio table using parameterized SQLite statements.
- Archetype definitions expose stable IDs, niche fit metadata, and declarative layout data; they do not embed rendered project state.

- [ ] **Step 1: Write failing selector and registry tests** for stable same-seed DNA, valid catalog minimums, niche weighting, explicit-constraint precedence, collision alternate selection, exactly three attempts, SQLite persistence/duplicate project behavior, and isolation from preview.
- [ ] **Step 2: Run the focused tests** with `pytest ai-agent/tests/test_design_system_engine.py ai-agent/tests/test_design_registry.py -q`; confirm expected missing-interface failures.
- [ ] **Step 3: Implement the catalogs, selector, fingerprinting, collision scoring, and isolated SQLite registry** with WAL/busy timeout and idempotent schema initialization.
- [ ] **Step 4: Re-run the focused tests** and verify the same seed yields the same DNA while collision retry changes an unconstrained layout dimension.
- [ ] **Step 5: Commit** as `feat(design): add deterministic DNA selection and registry`.

### Task 2: Add tokenized layout recipes and page composition

**Files:**
- Create: `ai-agent/agent/intelligence/layout_recipes.py`
- Create: `ai-agent/agent/intelligence/page_composer.py`
- Modify: `ai-agent/agent/project_builder.py`
- Test: `ai-agent/tests/test_design_page_composer.py`
- Test: `ai-agent/tests/test_generated_website_backend.py`

**Interfaces:**
- `get_layout_catalog() -> dict` provides 12+ hero archetypes, 8+ nav patterns, 10+ niche blocks, and niche-specific recipes.
- `compose_project_pages(project_dir: Path, design_dna: dict, spec: dict) -> dict` writes the selected shell, Home page, and applicable niche pages into a newly generated frontend and returns written paths plus structural evidence.
- Rendering consumes only the manifest tokens and content bindings. Navigation, hero, section order, footer, grid, card treatment, and density in output must match DNA; it cannot be a manifest-only variation.

- [ ] **Step 1: Write failing renderer tests** covering every minimum catalog count, deterministic recipe output, multiple distinct hero/nav/section structures, niche-page content binding, and no literal color or dimension styling in design blocks.
- [ ] **Step 2: Run `pytest ai-agent/tests/test_design_page_composer.py -q`** and confirm the missing composer/catalog failures.
- [ ] **Step 3: Implement the declarative catalog and small React page/shell renderers** using CSS custom properties for semantic color, type, spacing, radius, shadow, and motion tokens. Add niche-aware section blocks and avoid the existing fixed generic Home recipe for newly generated projects.
- [ ] **Step 4: Wire the composer into `ProjectBuilder` only for new generation plans carrying `design_dna`**; projects without DNA retain legacy behavior.
- [ ] **Step 5: Run focused composer and builder tests**; inspect generated JSX for valid imports, selected layout structure, and token-only visual values.
- [ ] **Step 6: Commit** as `feat(design): compose pages from tokenized niche recipes`.

### Task 3: Bind manifests, orchestration, and content gates

**Files:**
- Modify: `ai-agent/agent/intelligence/design_manifest.py`
- Modify: `ai-agent/agent/intelligence/design_uniqueness.py`
- Modify: `ai-agent/agent/orchestrator.py`
- Create: `ai-agent/agent/intelligence/design_content_guard.py`
- Test: `ai-agent/tests/test_design_uniqueness.py`
- Test: `ai-agent/tests/test_design_manifest.py`
- Test: `ai-agent/tests/test_design_content_guard.py`
- Test: `ai-agent/tests/test_orchestrator.py`

**Interfaces:**
- `DesignManifestWriter.write_manifest()` persists `design_dna` and gate/attempt evidence while preserving legacy top-level manifest keys and older reader behavior.
- `validate_design_content(spec: dict, content: dict) -> dict` reports provenance, banned phrases, unsupported claims, and cross-niche leakage as explicit findings.
- Orchestration resolves DNA after requirements/design constraints are known and before `ProjectBuilder`; it passes one canonical object through plan/spec, composer, manifest, and release gate.
- Accepted fingerprints are recorded only after successful composition; failed or preview candidates are never registered.

- [ ] **Step 1: Add failing compatibility/integration tests** for DNA persistence, legacy manifest reading, brief-backed claims, rejection of unsupported claims/logos/testimonials, niche leakage, and the orchestrator passing one selected DNA object into composition.
- [ ] **Step 2: Run the focused manifest/content/orchestrator tests** and confirm they fail on missing DNA propagation or validation.
- [ ] **Step 3: Implement content provenance and banned-generic checks**, including neutral fallback content that does not invent metrics, customer identities, media logos, or testimonials.
- [ ] **Step 4: Integrate registry lookup and deterministic resolution before project building**, preserve explicit constraints and existing design-uniqueness signatures, write the accepted DNA to the manifest, and record it only after composition passes static gates.
- [ ] **Step 5: Run focused tests plus existing `test_design_uniqueness.py`, `test_design_planner_and_browser.py`, and `test_generated_website_backend.py`** to detect legacy contract regressions.
- [ ] **Step 6: Commit** as `feat(design): bind DNA and content validation to generation`.

### Task 4: Enforce visual gates and add the diversity CLI

**Files:**
- Create: `ai-agent/agent/intelligence/design_quality_gates.py`
- Modify: `ai-agent/agent/extensions/browser_qa.py`
- Modify: `ai-agent/main.py`
- Test: `ai-agent/tests/test_design_quality_gates.py`
- Test: `ai-agent/tests/test_design_preview_cli.py`

**Interfaces:**
- `run_design_gates(project_dir: Path, design_dna: dict, browser=None) -> dict` checks uniqueness, token usage, semantic contrast, content findings, and responsive evidence. Screenshots are attempted at 375x812, 768x1024, and 1440x900 when browser QA is available.
- The CLI accepts `python ai-agent/main.py design-preview --prompt TEXT --samples N [--seed SEED]`, prints sampled signatures and pairwise hero/nav/section-order diversity, and has no writes or provider calls.
- Existing `main.py` flag-mode parsing and commands continue to behave as before.

- [ ] **Step 1: Write failing gate and CLI tests** for contrast/token failures, measured and missing browser evidence, all three viewport requests, three-attempt cap, deterministic preview output, matrix dimensions, invalid input, and no registry/filesystem mutations.
- [ ] **Step 2: Run `pytest ai-agent/tests/test_design_quality_gates.py ai-agent/tests/test_design_preview_cli.py -q`** and confirm expected missing behavior.
- [ ] **Step 3: Implement static token/content/contrast gates and responsive screenshot capture** using the existing browser integration. Missing tooling yields `not_measured`; measured failures block release and may select another candidate only within the three-attempt budget.
- [ ] **Step 4: Add the early-dispatched `design-preview` command** without changing legacy flag parsing; render a pairwise diversity matrix and collision summary using in-memory candidates.
- [ ] **Step 5: Run focused tests and existing browser integration tests**; document which browser checks are unmeasured on this host.
- [ ] **Step 6: Commit** as `feat(design): gate layouts and preview portfolio diversity`.

### Task 5: Verify compatibility and all generation modes

**Files:**
- Modify: `ai-agent/tests/test_design_system_engine.py`
- Modify: `ai-agent/tests/test_orchestrator.py`
- Modify: `ai-agent/tests/test_generated_project_completeness.py`
- Modify: `ai-agent/README.md`

- [ ] **Step 1: Add an isolated generation smoke test** using a temporary output root, deterministic local mode, at least two niches, and distinct seeds; assert composed structure and release status evidence.
- [ ] **Step 2: Run focused regressions** for design, planner, builder, orchestrator, completeness, browser QA, and CLI.
- [ ] **Step 3: Run the complete agent suite** with `pytest ai-agent/tests -q`; report all failures, including pre-existing failures, without masking them.
- [ ] **Step 4: Verify the 11 curated products remain untouched** by comparing tracked/untracked product file status and representative hashes before/after; ensure no generation command wrote into `products/` or existing generated folders.
- [ ] **Step 5: Run `python ai-agent/main.py design-preview --prompt "insurance claims intake" --samples 8 --seed audit`** and capture the actual matrix output. Run screenshot checks only if browser tooling is available; otherwise report blocked/not measured.
- [ ] **Step 6: Commit** docs and test updates as `docs(design): document DNA recipes and preview workflow` after all tests for the task pass.

## Handoff

The implementation method is native execution in this session; no subagents are
required. Begin implementation only after this plan has been reviewed and
approved. Follow TDD and the task boundaries above. Since the repository is
already dirty, inspect each staged diff and commit only files owned by the
current task; never include unrelated existing changes.