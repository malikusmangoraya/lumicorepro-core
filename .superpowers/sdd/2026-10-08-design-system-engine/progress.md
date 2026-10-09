# SDD ledger — plan: docs/superpowers/plans/2026-10-08-design-system-engine.md

Ruling: Execute in the existing shared branch — the user explicitly approved implementation here and requested incremental commits; the dirty worktree contains extensive pre-existing changes, so do not create/switch worktrees. Stage only files owned by this plan.

Pre-flight: Task 1 produces deterministic `design_dna` with `layout.pages.Home.section_order`; Task 2 consumes that exact structure. Catalog ownership is split by implementation order: selector owns the declarative catalog and `layout_recipes.py` later re-exports it, preventing duplicate definitions.

Task 1 RED: `python -m pytest ai-agent/tests/test_design_system_engine.py ai-agent/tests/test_design_registry.py -q` → 2 collection errors, both expected `ModuleNotFoundError` for the not-yet-created selector/registry modules. `pytest` executable is not on PATH; Python module invocation works.

Workflow note: the skill's `task-start`/`task-done` helpers cannot run because `bash.exe` requires an uninstalled WSL distribution and the sibling `subagent-driven-development` scripts are unavailable. Continue natively; record exact commands/results here.

Task 1: complete — added deterministic design DNA selection, 12 hero/8 nav/16 section records, and SQLite signature upsert/list behavior. RED confirmed missing modules. GREEN: `python -m pytest ai-agent/tests/test_design_system_engine.py ai-agent/tests/test_design_registry.py -q` → 9 passed; compatibility `python -m pytest ai-agent/tests/test_design_system_engine.py ai-agent/tests/test_design_registry.py ai-agent/tests/test_design_uniqueness.py -q` → 19 passed.

Task 1: Ruling — collision threshold is exact match on all three required dimensions (hero, navigation, full Home section order); candidates avoid repeating prior hero/nav values within the three-attempt window, and fixed explicit collisions remain failed after three attempts.
