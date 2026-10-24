# Optional Reflex Project Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicitly selected Reflex project output mode without changing existing React/Vite generation.

**Architecture:** Implement a dedicated Reflex generator and route only explicit `reflex` requests to it. Keep Reflex optional and avoid constructing success-shaped outputs when the dependency or validation runtime is unavailable.

**Tech Stack:** Existing Python agent; optional Reflex Python package; existing pytest suite.

**Spec:** [2026-10-22-reflex-generation-design.md](../specs/2026-10-22-reflex-generation-design.md)

## Global Constraints

- Existing default remains React/Vite and has no new required Reflex dependency.
- Reflex mode without its optional dependency returns an actionable error and never silently falls back.
- Do not claim production deployment, auth, database, or security capabilities that are not implemented.
- Confirm upstream package identity, license, supported Python versions, installation method, and run/validation command from authoritative sources before pinning or documenting them.
- Do not globally install packages or introduce external service credentials.

## Review Focus

- Missing optional Reflex package: request must fail explicitly, with no success report or partial misleading project.
- Invalid or absent mode: defaults to existing React path unchanged.
- Destination already contains files: generator must avoid silently overwriting unrelated content.
- Unsupported Python/Reflex version: validation must report the incompatibility instead of claiming success.
- Generated app syntax/import/launch errors: end-to-end validation catches issues beyond file-presence assertions.

---

### Task 1: Define and test the isolated Reflex generator contract

**Files:**
- Create: `ai-agent/agent/reflex_project_generator.py`
- Test: `ai-agent/tests/test_reflex_project_generator.py`
- Modify: `ai-agent/requirements.txt` only after upstream and license verification

**Interfaces:**
- Produces: `ReflexProjectGenerator.generate(destination_dir: str, project_name: str) -> dict`; explicit unavailable/runtime failures raise a specific `ReflexGenerationError`.
- Consumes: destination and project name; optional Reflex package and validated upstream invocation.

- [ ] Write tests `test_generate_writes_minimal_reflex_project`, `test_reflex_missing_dependency_fails_without_success`, `test_rejects_unsafe_project_name`, and `test_does_not_overwrite_nonempty_destination`.
- [ ] Run `pytest ai-agent/tests/test_reflex_project_generator.py -q`; confirm failures are due to the missing generator/contract.
- [ ] Verify official Reflex package, license, supported Python versions, project scaffold/run and validation commands. If authoritative sources remain inaccessible, stop before adding a dependency and report the blocker.
- [ ] Implement the smallest generator that writes the confirmed minimal Python app, dependency file, and setup README; keep version constraints in an isolated optional requirements file if appropriate.
- [ ] Run `pytest ai-agent/tests/test_reflex_project_generator.py -q`; expected: all tests pass.

### Task 2: Route explicit Reflex mode without changing the default generator

**Files:**
- Modify: `ai-agent/main.py` (CLI mode selection)
- Modify: `ai-agent/agent/orchestrator.py` only at the existing generation entrypoint after exact call sites are rechecked
- Test: `ai-agent/tests/test_reflex_project_generator.py` or a focused CLI/orchestrator test file

**Interfaces:**
- CLI: an explicit `--framework reflex` option; default value preserves current React/Vite behavior.
- Orchestrator: route explicit Reflex selection to the dedicated generator and return the existing report conventions plus explicit framework provenance.

- [ ] Add tests `test_default_framework_keeps_current_fullstack_path`, `test_reflex_framework_routes_to_reflex_generator`, and `test_unknown_framework_is_rejected`.
- [ ] Run the focused tests and confirm expected failures before implementation.
- [ ] Add the opt-in route, validate accepted values, and leave the existing React code path unchanged.
- [ ] Run focused tests and relevant existing CLI/fullstack generation tests.

### Task 3: Verify generated output and document limitations

**Files:**
- Modify: `ai-agent/README.md`
- Test: `ai-agent/tests/test_reflex_project_generator.py`

- [ ] Add a test that runs the generated project’s authoritative Reflex validation/check command in an isolated temporary directory when the optional package exists; skip only with an explicit test report for missing external runtime, not a false pass.
- [ ] Run static output assertions and the end-to-end command in the supported environment; verify a launch/validation result, not merely file creation.
- [ ] Document optional install, CLI usage, generated output, and precise runtime limitations.
- [ ] Run relevant agent tests and verify the normal React generation smoke path remains unchanged.

---
