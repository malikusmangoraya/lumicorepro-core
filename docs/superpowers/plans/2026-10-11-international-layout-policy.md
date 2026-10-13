# International Layout Policy Implementation Plan

> **For agentic workers:** Use the account `executing-plans` skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make international-quality, industry-appropriate layout the default for new generation while preserving existing layouts on ordinary project updates unless redesign is explicitly requested.

**Architecture:** Normalize design intent at the existing generation planner and iteration-engine boundaries. New builds continue using `DesignSystemEngine` and `compose_project_pages`; project updates load existing design state and constrain any design-changing update to that state unless an explicit redesign is detected. No parallel design system or dependency is introduced.

**Tech Stack:** Python, existing AI-agent engines, unittest tests.

**Spec:** [2026-10-11-international-layout-policy-design.md](../specs/2026-10-11-international-layout-policy-design.md)

## Global Constraints

- New generation defaults to a distinctive, industry/brand-appropriate layout via existing design machinery.
- Ordinary existing-project updates preserve existing layout and design-system decisions.
- Explicit preservation takes precedence over redesign defaults; explicit redesign enables layout selection.
- Existing project update calls remain backward compatible; absent intent defaults to preserving layout.
- Apex's current automotive site remains untouched.
- Report only evidence-backed QA; do not claim unmeasured visual, responsive, accessibility, or performance scores.

## Review Focus

- Wording that requests new content while also saying keep the current design must preserve structure and tokens. Test explicit preservation overriding redesign keywords.
- Existing manifest may use either `design_dna` or the design decision schema. Test compatible extraction and byte-preserving behavior for unrelated manifest fields.
- Missing or malformed manifest must still lead to source-based preservation and a recorded fallback, not silent redesign. Test missing and invalid JSON manifests.
- Project folders may contain nested frontend paths or alternate Home filenames. Test a normal supported generated-project shape and graceful fallback when recognizable design sources are absent.
- Existing layout constraints can collide with novelty selection. Test that pinned layout choices are not altered by diversity logic.

---

### Task 1: Define and resolve normalized design intent

**Files:**
- Modify: `ai-agent/agent/intelligence/design_system_engine.py`
- Test: `ai-agent/tests/test_design_system_engine.py`
- Test: `ai-agent/tests/test_design_page_composer.py`

**Interfaces:**
- Add module-level `resolve_design_intent(spec: Dict[str, Any], *, operation: str) -> str`, returning `international_default`, `preserve_existing`, or `redesign_requested`.
- `operation` is `generation` or `update`; invalid/missing legacy values use `generation` only when called from generation and `update` only when called from iteration.
- Explicit preserve phrases/flags take precedence over redesign phrases/flags; old callers with no intent resolve to operation defaults.

- [ ] **Step 1: Write failing tests**
  - Add `test_generation_defaults_to_international_layout_intent` and assert the intent is `international_default`.
  - Add `test_update_defaults_to_preserve_existing_intent` and assert `preserve_existing`.
  - Add `test_explicit_redesign_and_explicit_preserve_are_distinguished`, including a combined request where explicit preservation wins.
  - Add `test_international_generation_stays_deterministic_for_same_seed`; assert resolved DNA and fingerprint are identical across repeated resolutions.
- [ ] **Step 2: Run focused tests and confirm they fail**

```bash
cd ai-agent && python -m pytest tests/test_design_system_engine.py -q
```

Expected: failure because intent resolution does not exist yet.

- [ ] **Step 3: Implement `resolve_design_intent`**
  Normalize explicit intent fields and clear phrase signals without changing recipe selection semantics. Keep intent results limited to the three named values; invalid explicit values fall back safely to the operation default.
- [ ] **Step 4: Use intent in generation planning**
  In `GenerationPlanner.create_plan`, set `design_intent` to `international_default` by default and pass it through `spec` and returned plan. Preserve explicit user intent from the input spec.
- [ ] **Step 5: Run generation/design tests**

```bash
cd ai-agent && python -m pytest tests/test_design_system_engine.py tests/test_design_page_composer.py -q
```

Expected: PASS, including deterministic design output and composed structural layout.

---

### Task 2: Preserve existing design context during iteration

**Files:**
- Modify: `ai-agent/agent/iterate_engine.py`
- Test: `ai-agent/tests/test_iterate_engine.py`

**Interfaces:**
- Add private `_load_existing_design_context(project_dir: str) -> Dict[str, Any]` returning `{found: bool, source: str, design_dna: dict, design_manifest: dict, preservation: str}`.
- Add private `_is_layout_change_request(instruction: str) -> bool` with explicit preserve taking precedence over redesign.
- Extend existing iteration context internally only; retain public `iterate(project_dir, instruction, provider_name=None, client_brand=None)` signature.

- [ ] **Step 1: Write failing tests**
  - Add `test_ordinary_iteration_preserves_design_manifest` with existing test fixture, additionally assert design manifest bytes and existing design DNA choices remain unchanged.
  - Add `test_update_without_manifest_records_source_inferred_preservation` using a generated Home.jsx/design-system.css fixture; assert iteration result includes inferred-preservation context and source layout remains unchanged.
  - Add `test_explicit_redesign_request_is_classified_but_keep_layout_wins` for explicit redesign and combined preserve wording.
  - Add `test_malformed_manifest_uses_source_inferred_preservation` and assert malformed input is not overwritten.
- [ ] **Step 2: Run focused tests and confirm they fail**

```bash
cd ai-agent && python -m pytest tests/test_iterate_engine.py -q
```

Expected: failure because iteration does not load design context or expose the preservation decision.

- [ ] **Step 3: Implement existing-context loading**
  Load `design-manifest.json` and `.artifacts/07-design.json` when present. Accept embedded `design_dna` as well as existing design-decision fields; do not rewrite either file. If no usable manifest exists, inspect candidate page and stylesheet source contents and return `source_inferred` preservation metadata. If no recognizable source exists, return safe preserve mode with `source_unavailable` rather than re-derive layout.
- [ ] **Step 4: Bind context to iteration patching**
  Resolve `preserve_existing` for ordinary updates and explicit keep-layout requests. Resolve `redesign_requested` only when the instruction requests redesign and does not request preservation. Include the exact resolved policy and serialized existing design context in AI edit instructions; ensure deterministic offline patch rules do not rewrite layout tokens for content-only changes. Include `design_update` metadata in the iteration result while preserving existing result keys.
- [ ] **Step 5: Run iteration tests**

```bash
cd ai-agent && python -m pytest tests/test_iterate_engine.py -q
```

Expected: PASS; manifest and source layout are preserved for ordinary updates and malformed/missing manifest cases are reported as inferred/fallback context.

---

### Task 3: Verify generation/update integration and regression boundaries

**Files:**
- Modify: `ai-agent/agent/orchestrator.py` only if needed to pass normalized update intent to the iteration engine; keep `AgentOrchestrator.iterate` signature unchanged.
- Test: `ai-agent/tests/test_orchestrator.py`
- Test: `ai-agent/tests/test_design_page_composer.py`
- Test: `ai-agent/tests/test_iterate_engine.py`

**Interfaces:**
- Generation uses `GenerationPlanner.create_plan` → `DesignSystemEngine.resolve` → `compose_project_pages`; no parallel generation path.
- Iteration returns existing success/result fields plus `design_update: {intent, source, preserved}`.

- [ ] **Step 1: Add integration assertions**
  - Verify a generated automotive spec uses the automotive niche recipe, with actual hero/navigation/section structure emitted by `compose_project_pages`.
  - Verify ordinary iteration returns `design_update.intent == "preserve_existing"` and leaves design source files untouched.
  - Verify explicit redesign is marked `redesign_requested`, while “redesign, but keep the current layout” resolves to preserve.
- [ ] **Step 2: Run focused regression tests**

```bash
cd ai-agent && python -m pytest tests/test_orchestrator.py tests/test_design_system_engine.py tests/test_design_page_composer.py tests/test_iterate_engine.py -q
```

Expected: PASS; no Apex product files change.

- [ ] **Step 3: Inspect final changes and run broader AI-agent tests**
  Run the complete AI-agent test suite using the repository's documented invocation, and inspect the diff for unintended edits to the already-modified worktree. Do not stage or modify unrelated files.

Expected: all relevant tests pass; any pre-existing/unrelated failures are reported explicitly, never masked.
