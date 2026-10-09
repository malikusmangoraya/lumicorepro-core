# Project Design Uniqueness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for completed work.

**Goal:** Make new Lumicore-generated websites use distinct, reproducible design signatures compared with prior generated projects while preserving user constraints and all current quality-gate semantics.

**Architecture:** Add a deterministic portfolio-aware selector that reads prior `design-manifest.json` signatures without modifying projects. Integrate its selected final UI style and safe palette into the existing orchestrator before code generation and post-build restyling, then persist the applied signature through the existing manifest writer. Existing project iterations keep their design by default.

**Tech Stack:** Python 3, pathlib, hashlib, JSON, pytest/unittest, existing Lumicore design planner and orchestrator.

**Spec:** `docs/superpowers/specs/2026-10-07-project-design-uniqueness.md`

## Global Constraints

- Existing score fields, gate results, and pass/fail behavior remain unchanged.
- Read existing manifests beneath `GENERATED_PROJECTS_DIR` as read-only comparison input.
- User constraints, accessibility, responsive behavior, performance, and reduced-motion constraints take precedence over forced visual variation.
- Do not claim uniqueness against every public website or design ever made.
- Do not add a new database, third-party API, or remote website scraping.
- Preserve existing manifest fields and compatibility with legacy manifests.
- Do not commit changes unless explicitly requested.

## Review Focus

- Empty or missing output directory: selection must use current decisions and continue; tested in Task 1.
- Malformed, unreadable, or legacy manifests: skip invalid data and use available legacy dimensions without modifying files; tested in Task 1.
- Existing target project appears in the portfolio: exclude it from new-project comparison; tested in Task 1.
- Explicit user visual/color/style constraints conflict with novelty: keep the user-selected values; tested in Task 1 and Task 2.
- A design change is requested on an existing project: preserve unrelated manifest decisions; tested by confirming iteration leaves `design-manifest.json` unchanged in Task 3.

---

## File Map

- Create `ai-agent/agent/intelligence/design_uniqueness.py`: signature normalization, read-only portfolio loading, deterministic selection, and comparison provenance.
- Modify `ai-agent/agent/orchestrator.py`: supply portfolio context and apply selected decisions before code generation.
- Modify `ai-agent/agent/intelligence/design_manifest.py`: persist versioned signature data without dropping existing manifest fields.
- Modify `ai-agent/agent/pro_design.py`: accept validated optional palette overrides in the final restyle and write the resolved palette to `DESIGN_PLAN.md`.
- Create `ai-agent/tests/test_design_uniqueness.py`: isolated tests for scan, comparison, determinism, constraints, and malformed inputs.
- Modify `ai-agent/tests/test_orchestrator.py`: assert uniqueness decisions reach generation input and score/gate contracts are unchanged.
- Modify `ai-agent/tests/test_iterate_engine.py`: assert an existing design manifest is preserved during ordinary iteration.
- Tests in `ai-agent/tests/test_design_uniqueness.py`: verify final restyle palette overrides.

## Task 1: Portfolio-Aware Design Selector

**Files:**
- Create: `ai-agent/agent/intelligence/design_uniqueness.py`
- Create: `ai-agent/tests/test_design_uniqueness.py`

**Interfaces:**
- Produces `extract_design_signature(decision: Dict[str, Any], design_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`.
- Produces `load_portfolio_signatures(projects_dir: Path, exclude_project: Optional[Path] = None) -> List[Dict[str, Any]]`.
- Produces `apply_design_uniqueness(decision: Dict[str, Any], design_plan: Dict[str, Any], prior_signatures: Sequence[Dict[str, Any]], seed: str, explicit_constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`.
- Produces `normalize_palette_overrides(values: Optional[Dict[str, Any]]) -> Dict[str, str]` for supported hex colors only.
- `apply_design_uniqueness` returns `{"decision": ..., "design_plan": ..., "design_signature": ..., "comparison": ...}`. The signature contains `version`, stable `fingerprint`, and normalized `dimensions`. It must not mutate inputs.
- Signature dimensions include only applied, available values: brand archetype, visual direction, hero, navigation, grid/composition, typography, palette tokens, image ratio/treatment, motion, 3D, CTA, surface, and card usage.
- Candidate UI styles use the existing ProDesign catalog: `glassmorphism`, `minimalist`, `flat`, `bento`, `neobrutalism`, `neumorphism`, `claymorphism`, `skeuomorphism`, and `dark`. Other available decision dimensions vary deterministically, while explicit user and reference-derived constraints are preserved.

- [x] **Step 1: Write focused failing tests** for stable fingerprints, meaningful-dimension differences, no prior manifests, exclusion of the target project, malformed and legacy manifests, deterministic alternative selection, explicit constraint preservation, no input mutation, and no prior-file mutation.
- [x] **Step 2: Run the focused tests and confirm they fail**

Run from repository root: `python -m pytest ai-agent/tests/test_design_uniqueness.py -q`
Expected: FAIL because the uniqueness module/functions do not exist.

- [x] **Step 3: Implement the selector interfaces** in `ai-agent/agent/intelligence/design_uniqueness.py`. Scan only `design-manifest.json` below the supplied output root. Normalize values before hashing. When a candidate overlaps prior signatures, select a deterministic alternative across supported decision dimensions; never override keys supplied as explicit user constraints. Skip invalid files individually.
- [x] **Step 4: Re-run the focused tests**

Run: `python -m pytest ai-agent/tests/test_design_uniqueness.py -q`
Expected: PASS, with prior manifests unchanged.

## Task 2: Main Generation Integration

**Files:**
- Modify: `ai-agent/agent/orchestrator.py`
- Test: `ai-agent/tests/test_orchestrator.py`

**Interfaces:**
- Consumes Task 1's `load_portfolio_signatures` and `apply_design_uniqueness`.
- Produces `spec["design_signature"]`, selected `spec["design_decision"]`, and comparison provenance before `plan["spec"]` is copied for code generation. Also attach the same signature to `design_decision["design_manifest"]["design_signature"]`, because the existing manifest writer receives that nested decision.
- Produces `spec["ui_style"]`, `spec["design_blueprint"]`, and `spec["design_palette_override"]` so the builder and final restyler use the same selected visual direction.
- Reads portfolio root from `config.settings.GENERATED_PROJECTS_DIR`; excludes `project_dir` when it identifies the current target.
- Explicit constraints come only from existing user-derived inputs: detected `ui_style`, `primary_color_hint`/`color_palette_hints`, measured screenshot palette/sections, and user-provided `style_preference` values. Do not treat automatic defaults as explicit requests.
- The selector seed is `spec["design_seed"]` when provided; otherwise derive it from the normalized original prompt, project name, and sorted prior signature fingerprints so identical inputs with the same portfolio reproduce the same choice.

- [x] **Step 1: Add failing orchestrator tests** proving prior signatures are loaded, selected decisions are present in the spec passed to generation, user-derived explicit constraints are preserved, and the existing `quality_gates` report fields are unchanged.
- [x] **Step 2: Run the targeted orchestrator tests and confirm failure**

Run: `python -m pytest ai-agent/tests/test_orchestrator.py -q`
Expected: FAIL because the generation path does not yet apply portfolio-aware selection.

- [x] **Step 3: Integrate selection** after the design decision is created and before code generation consumes the final spec. Keep selection observationally safe: if portfolio scanning fails, retain current decisions and record that comparison was unavailable; do not add or modify any quality gate or score logic. Feed the resolved UI style and validated palette override to the final ProDesign restyler.
- [x] **Step 4: Re-run targeted tests**

Run: `python -m pytest ai-agent/tests/test_orchestrator.py -q`
Expected: PASS; generation receives the selected design contract, and gate/report fields remain unchanged.

## Task 3: Persist and Preserve Design Signatures

**Files:**
- Modify: `ai-agent/agent/intelligence/design_manifest.py`
- Test: `ai-agent/tests/test_design_uniqueness.py`
- Test: `ai-agent/tests/test_iterate_engine.py`

**Interfaces:**
- `DesignManifestWriter.write_manifest(decision, extra=None)` accepts `decision["design_signature"]` and writes it to `design-manifest.json` while retaining current schema fields.
- `DesignManifestWriter.load_manifest()` continues to return `{}` for missing or malformed files and reads old manifests without a signature.
- Existing iteration does not regenerate or overwrite the design signature unless a future explicit redesign path is implemented.

- [x] **Step 1: Add failing tests** for signature write/read round-trip, legacy manifest reads, preservation of all existing schema fields, and iteration leaving the existing `design-manifest.json` bytes unchanged.
- [x] **Step 2: Run the focused manifest and iteration tests and confirm failure**

Run: `python -m pytest ai-agent/tests/test_design_uniqueness.py ai-agent/tests/test_iterate_engine.py -q`
Expected: signature round-trip/preservation assertions fail before the writer accepts the new field.

- [x] **Step 3: Extend manifest persistence** to store the signature as an additive field. Keep iteration behavior unchanged and avoid rewriting old project manifests during portfolio scans.
- [x] **Step 4: Re-run focused tests**

Run: `python -m pytest ai-agent/tests/test_design_uniqueness.py ai-agent/tests/test_iterate_engine.py -q`
Expected: PASS; old projects remain readable and iteration preserves their original design manifest.

## Task 4: Compatibility Verification

**Files:**
- Test: `ai-agent/tests/test_v72_engines.py`
- Tests: Tasks 1–3 files

- [x] **Step 1: Run design and uniqueness regression tests**

Run: `python -m pytest ai-agent/tests/test_design_uniqueness.py ai-agent/tests/test_design_planner_and_browser.py ai-agent/tests/test_orchestrator.py ai-agent/tests/test_iterate_engine.py ai-agent/tests/test_v72_engines.py -q`
Expected: PASS; existing Hyper-Unique helper API remains compatible, and no gate semantics change.

- [x] **Step 2: Run all collectable AI-agent test modules**

Run: four non-overlapping pytest shards covering all `ai-agent/tests/test_*.py` modules except `test_mcp_readonly_tools.py` and `test_mcp_server.py`.
Expected: PASS. Actual: 995 passed and 103 subtests passed across 57 test modules. The two excluded MCP modules cannot collect in this environment because `mcp` is not installed, although `ai-agent/requirements.txt` declares `mcp>=1.9.0,<2`; direct full-suite collection reports `ModuleNotFoundError: No module named 'mcp'`.

## Self-Review

- Spec coverage: portfolio scanning and malformed/legacy fallback (Task 1); deterministic meaningful variation, explicit constraints, and no mutation (Tasks 1–2); pre-generation integration, final UI-style/palette application, and provenance (Task 2); manifest persistence and existing-project preservation (Task 3); stable API and unchanged gate behavior (Task 4).
- Review-focus cases each have a focused test assigned above.
- Public quality-gate fields are not edited; the orchestrator test checks their contract.
- Focused tests passed: 74 passed and 14 subtests passed after the final palette/style handoff changes.
- Broad regression run before the final palette handoff changes: all 57 collectable agent test modules passed in four shards (995 passed and 103 subtests passed). Two MCP suites remain unverified due to the missing declared dependency.
- No database migration, provider/API change, generated-project bulk rewrite, or commit is included.
