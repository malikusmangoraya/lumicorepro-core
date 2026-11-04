# LumicorePro Hardening — Phase 0 + Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate four divergent work streams onto one branch and repair every CI gate that currently reports success without measuring it, so that later quality work is verified by real evidence.

**Architecture:** Work happens in `D:\lumicorepro-core-premium-delivery` on a new branch `feature/hardening-v8` cut from `master` (`539fecbf`). Each fix lands as a test-first task that pairs the gate with an anti-gate proving the check does not fire on a satisfied condition. Gates are either exact (the workflow must invoke pytest) or ratcheted (a measured count that may only fall).

**Tech Stack:** GitHub Actions, pytest 8.2.0, Node 22 + npm workspaces, Express, JavaScript test runner `node --test`, Jest, Vitest, ruff, bandit, Python 3.12.

**Spec:** `docs/superpowers/specs/2026-10-29-lumicore-hardening-design.md`

**Scope note:** This plan covers Phase 0 (consolidation) and Phase 1 (gates that report false success). Phases 2–4 of the spec (backend envelope, i18n, documentation) each get their own plan after Phase 1 lands, because each depends on the repaired gates to prove its own changes.

---

## Global Constraints

- Work only in `D:\lumicorepro-core-premium-delivery`. The original checkout `D:\lumicorepro-core` is read-only: never edit, reset, stash or clean it, and never touch its `.backup/`.
- Never run `git reset --hard`, `git checkout --`, `git clean`, or `git push --force`.
- Every uncommitted change is committed before any branch operation. Nothing is discarded.
- CI python command is `python -m pytest tests -q --ignore=tests/test_cli_e2e_progress.py` from `working-directory: ai-agent`.
- Never lower a ratchet floor to make a run pass. Floors only move down for count-based gates.
- Node version floor in CI is `"22"`; Python version floor is `"3.12"`.
- AGENTS.md rules that apply: §3 security, §4 backend envelope `{success,status,message,data,timestamp}`, §6 testing, §13 monorepo rules.
- Measured baseline at plan-writing time: unittest collects **774** tests, pytest collects **2110**; full pytest run is **1 failed, 2094 passed, 15 skipped, 126 subtests passed in 1003 s**; raw `res.status().json(` in `backend/routes` + `backend/middleware` is **315**; unvalidated route files **23 of 34**; missing i18n keys **245 of 337**.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `.github/workflows/ci.yml` | The single CI pipeline. Gains pytest, a committed fixture leg, a Postgres service, a delivery-verification step and a lint-ratchet step. |
| `.gitignore` | Narrows `generated-projects/` so the fixture is trackable while build output stays ignored. |
| `ai-agent/tests/test_ci_workflow.py` | New. Anti-gates: the CI workflow must run pytest, must reference the delivery verifier, must define a Postgres service for the fixture leg. |
| `ai-agent/tests/test_campaign_seo.py` | Modified. Dist-only campaigns declared explicitly instead of implied by whichever checkout the test runs in. |
| `scripts/fix_campaign_seo.py` | Modified. Declares `DIST_ONLY_CAMPAIGNS` so the parity rule has one source of truth. |
| `generated-projects/blogforge/` | New (committed fixture). Real BlogForge source, 236 files, excluding `node_modules/`, `dist/`, `frontend_node_modules_old/`, `*.log`. |
| `scripts/lint_ratchet.py` | New. Runs ruff and bandit, compares violation counts against a checked-in baseline, fails above it. |
| `ai-agent/lint-baseline.json` | New. The measured ruff/bandit baseline. |
| `ai-agent/pyproject.toml` | New. Ruff and bandit configuration. |
| `ai-agent/requirements.txt` | Modified. Adds `ruff`. |
| `docs/superpowers/plans/2026-10-29-lumicore-hardening-phase1.md` | This plan. |
| `docs/superpowers/specs/2026-10-29-lumicore-hardening-design.md` | The spec this plan implements. |

---

## Task 1: Consolidate the four work streams

**Files:**
- Modify (git state only): branch `feature/hardening-v8`
- Read-only source: `D:\lumicorepro-core` (original checkout), `D:\lumicorepro-core-stack-catalog`

**Interfaces:**
- Consumes: existing branches `feature/premium-delivery-gates` (`539fecbf`), `feature/backend-stack-catalog` (`e5155864`), `feat/orbitboard-live-completion` (`98650aa1`), `chore/orbitboard-actions-node24` (`87c14737`).
- Produces: branch `feature/hardening-v8` containing every uncommitted change from all four streams; clean working tree in the premium-delivery worktree.

- [ ] **Step 1: Verify nothing is lost — record the current dirty state**

Run from `D:/lumicorepro-core-premium-delivery`:

```bash
git status --short > /tmp/premium-dirty-before.txt
git -C D:/lumicorepro-core-stack-catalog status --short > /tmp/stack-dirty-before.txt
wc -l /tmp/premium-dirty-before.txt /tmp/stack-dirty-before.txt
```

Expected: premium ≈ 47 lines, stack-catalog ≈ 40 lines. Save both files; they are the checklist for Step 5.

- [ ] **Step 2: Create the integration branch**

```bash
cd D:/lumicorepro-core-premium-delivery
git checkout -b feature/hardening-v8
git rev-parse --abbrev-ref HEAD
```

Expected: `feature/hardening-v8`, based on `539fecbf`.

- [ ] **Step 3: Commit the premium-delivery uncommitted work first**

```bash
git add -A
git status --short | head -60
git commit -m "chore(save): preserve premium delivery work before hardening

Commits the mobile/PWA/engine work that was uncommitted on
feature/premium-delivery-gates so it survives the consolidation. No
functional change in this commit."
```

Expected: commit succeeds; `git status --short` prints nothing.

- [ ] **Step 4: Bring in the Orbitboard branches**

```bash
git cherry-pick 98650aa1
git cherry-pick 87c14737
git log --oneline -4
```

Expected: both cherry-picks apply, or a conflict is reported. On conflict: resolve in favour of `feature/hardening-v8` (keep master), `git add` the resolved files, `git cherry-pick --continue`, and record the conflicting paths in the phase report.

Verify the Orbitboard source arrived:

```bash
git ls-tree -r --name-only HEAD -- delivery/orbitboard/app | wc -l
```

Expected: > 0.

- [ ] **Step 5: Port the stack-catalog work**

The stack-catalog worktree holds 40 uncommitted files. Export them as a patch and apply:

```bash
cd D:/lumicorepro-core-stack-catalog
git diff > /tmp/stack-catalog.patch
wc -l /tmp/stack-catalog.patch
cd D:/lumicorepro-core-premium-delivery
git apply --3way /tmp/stack-catalog.patch
git status --short | wc -l
```

Expected: the patch applies and the file count matches the stack-catalog dirty list from Step 1. If `git apply` rejects a hunk, apply the remaining hunks, then hand-port the rejected file by comparing `D:/lumicorepro-core-stack-catalog/<path>` with the worktree copy.

- [ ] **Step 6: Commit the stack-catalog work**

```bash
git add -A
git commit -m "feat(backend-stack): backend stack catalog selection and i18n strings

Ports the 40-file backend stack catalog feature from the
feature/backend-stack-catalog worktree: catalog selection in the
orchestrator and planner, tech stack selector, backend ai route wiring,
and 13 locale files."
```

- [ ] **Step 7: Verify every dirty file survived**

```bash
cd D:/lumicorepro-core-premium-delivery
git status --short
comm -23 <(sort /tmp/premium-dirty-before.txt | sed 's/^...//') <(git ls-files | sort) | head
```

Expected: `git status --short` is empty; the `comm` output is empty for every previously modified file (untracked files now tracked).

- [ ] **Step 8: Confirm the original checkout is untouched**

```bash
git -C D:/lumicorepro-core status --short | wc -l
git -C D:/lumicorepro-core rev-parse --abbrev-ref HEAD
```

Expected: the count still matches what it was before this plan started, and the branch is still `agents/lumicorepro-core-integration-query`.

---

## Task 2: Make the campaign parity test honest

**Files:**
- Modify: `scripts/fix_campaign_seo.py:55-70`
- Test: `ai-agent/tests/test_campaign_seo.py:253-265`

**Interfaces:**
- Consumes: `fix_campaign_seo.CAMPAIGNS` (list of 10 slugs).
- Produces: `fix_campaign_seo.DIST_ONLY_CAMPAIGNS` (set of 3 slugs) — campaigns that ship as built artifacts and have no source tree.

**Why this is first:** the full pytest run has exactly one failure, and it is environmental. Until it is honest, every later pytest run is red for a reason unrelated to the change under test.

- [ ] **Step 1: Write the failing test**

Replace the body of `test_campaign_list_matches_generator` in `ai-agent/tests/test_campaign_seo.py` with:

```python
def test_campaign_list_matches_generator():
    """The repair tool and the generator must not drift apart on scope."""
    generated = {p.name for p in ipg.PROJECTS.glob("*") if p.is_dir()}
    sell_today = ROOT / "products" / "sell-today"
    if sell_today.is_dir():
        generated |= {p.name for p in sell_today.glob("*") if p.is_dir()}
    delivery = ROOT / "delivery"
    if delivery.is_dir():
        generated |= {p.name for p in delivery.glob("*") if p.is_dir()}

    # A campaign may ship as a built artifact with no source tree in this
    # checkout. Those are declared by the tool, not inferred from whichever
    # directories happen to exist locally.
    dist_only = getattr(fcs, "DIST_ONLY_CAMPAIGNS", set())
    if not any(p.is_dir() for p in ipg.PROJECTS.glob("*")):
        pytest.skip("generated-projects/ wiped for fresh regeneration; parity restores on next generator run")

    missing = set(fcs.CAMPAIGNS) - generated - dist_only
    assert not missing, f"campaigns with no generated project: {sorted(missing)}"


def test_dist_only_campaigns_are_real_campaigns():
    """A dist-only exception must not be a graveyard for typos."""
    dist_only = getattr(fcs, "DIST_ONLY_CAMPAIGNS", set())
    assert dist_only <= set(fcs.CAMPAIGNS), (
        f"dist-only campaigns that are not campaigns at all: {sorted(dist_only - set(fcs.CAMPAIGNS))}"
    )


def test_dist_only_campaigns_have_no_source_tree():
    """If a campaign gains a source tree it must leave the exception list."""
    dist_only = getattr(fcs, "DIST_ONLY_CAMPAIGNS", set())
    sell_today = ROOT / "products" / "sell-today"
    present = {p.name for p in sell_today.glob("*") if p.is_dir()} if sell_today.is_dir() else set()
    assert not (dist_only & present), (
        f"campaigns with source in products/sell-today must not be dist-only: "
        f"{sorted(dist_only & present)}"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_campaign_seo.py -q
```

Expected: `test_campaign_list_matches_generator` FAILS with `campaigns with no generated project: ['ember-salt', 'maison-noir', 'voltus-atelier']`; the two new tests PASS because `DIST_ONLY_CAMPAIGNS` defaults to an empty set.

- [ ] **Step 3: Declare the dist-only campaigns**

In `scripts/fix_campaign_seo.py`, immediately after the `CAMPAIGNS` list (line 66), add:

```python
# Campaigns that ship as built artifacts only. Their dist/ output exists under
# delivery/ (or the Pages deployment) but they have no source tree in
# products/sell-today, so the parity check cannot measure them. Declared here
# rather than inferred from whichever directories a given checkout happens to
# contain. If one of these gains a source tree, remove it from this set —
# test_dist_only_campaigns_have_no_source_tree enforces that.
DIST_ONLY_CAMPAIGNS = {
    "ember-salt",
    "maison-noir",
    "voltus-atelier",
}
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_campaign_seo.py -q
```

Expected: all tests PASS.

- [ ] **Step 5: Prove the anti-gate fires**

Temporarily add a bogus entry, run the test, confirm it fails, then revert:

```bash
cd D:/lumicorepro-core-premium-delivery
python - <<'PY'
import re, pathlib
p = pathlib.Path('scripts/fix_campaign_seo.py')
s = p.read_text(encoding='utf-8')
p.write_text(s.replace('    "voltus-atelier",\n}\n', '    "voltus-atelier",\n    "not-a-campaign",\n}\n', 1), encoding='utf-8')
PY
cd ai-agent && D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_campaign_seo.py::test_dist_only_campaigns_are_real_campaigns -q
```

Expected: FAILS naming `not-a-campaign`. Then revert:

```bash
cd D:/lumicorepro-core-premium-delivery
git checkout -- scripts/fix_campaign_seo.py
```

Note: `git checkout --` is used here on a file whose only change is the intentional probe, after the real change was committed in Step 6. Run Step 6 before this probe if the file has uncommitted work.

- [ ] **Step 6: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add scripts/fix_campaign_seo.py ai-agent/tests/test_campaign_seo.py
git commit -m "fix(seo): declare dist-only campaigns instead of inferring them from the filesystem

The parity test passed in one checkout and failed in another because three
campaigns (ember-salt, maison-noir, voltus-atelier) exist only as built
artifacts. The tool now declares them, and two guards keep the exception
honest: it must name real campaigns, and it must not shadow a campaign that
has gained a source tree."
```

---

## Task 3: Restore pytest in CI and make the regression impossible

**Files:**
- Modify: `.github/workflows/ci.yml:77-79`
- Create: `ai-agent/tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: `.github/workflows/ci.yml` YAML text.
- Produces: `test_ci_workflow.py::test_ci_runs_pytest_not_unittest`, `::test_ci_python_command_ignores_the_cli_e2e_suite`, `::test_ci_workflow_parses`.

- [ ] **Step 1: Write the failing test**

Create `ai-agent/tests/test_ci_workflow.py`:

```python
"""The CI workflow is the promise that the suite runs. These tests read it.

A workflow file is executable policy, so it gets the same treatment as code:
if a future edit swaps the test runner back to a collector that silently
skips two thirds of the suite, CI must fail here rather than stay green.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _workflow_text() -> str:
    assert WORKFLOW.is_file(), f"CI workflow is missing: {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_runs_pytest_not_unittest():
    """unittest discovers only TestCase subclasses; pytest collects the rest."""
    text = _workflow_text()
    ai_agent_steps = [line for line in text.splitlines() if "pytest" in line or "unittest" in line]
    assert ai_agent_steps, "CI has no python test runner at all"
    assert not any("unittest" in line for line in ai_agent_steps), (
        "CI must not collect python tests with unittest: it silently skips "
        "every bare def test_* function. Found: "
        + repr([line.strip() for line in ai_agent_steps if "unittest" in line])
    )
    assert any("python -m pytest" in line for line in ai_agent_steps), (
        "CI must run the suite with pytest"
    )


def test_ci_python_command_ignores_the_cli_e2e_suite():
    """The CLI e2e suite drives a live process and is excluded by contract."""
    text = _workflow_text()
    assert "tests/test_cli_e2e_progress.py" in text, (
        "the pytest invocation must keep the --ignore for the CLI e2e suite"
    )


def test_ci_workflow_parses_as_yaml():
    yaml = pytest.importorskip("yaml")
    parsed = yaml.safe_load(_workflow_text())
    assert isinstance(parsed, dict) and "jobs" in parsed
```

- [ ] **Step 2: Run it to verify it fails against the current workflow**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py -q
```

Expected: `test_ci_runs_pytest_not_unittest` FAILS naming the `unittest discover` line.

- [ ] **Step 3: Change the CI command**

In `.github/workflows/ci.yml`, replace lines 77-79:

```yaml
      - name: Test AI agent
        run: python -m unittest discover -s tests -t . -v
        working-directory: ai-agent
```

with:

```yaml
      - name: Test AI agent
        # unittest collects only TestCase subclasses, so 59 of 113 test files
        # (1336 tests, every engine added since 2026-10-28) never ran in CI.
        # pytest is already pinned in ai-agent/requirements.txt.
        run: python -m pytest tests -q --ignore=tests/test_cli_e2e_progress.py
        working-directory: ai-agent
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py -q
```

Expected: all three tests PASS.

- [ ] **Step 5: Prove the runner count actually increased**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests --collect-only -q | tail -2
D:/lumicorepro-core/venv/Scripts/python.exe -c "
import unittest, io, contextlib
l = unittest.TestLoader()
def c(s): return sum(c(x) if isinstance(x, unittest.TestSuite) else 1 for x in s)
with contextlib.redirect_stderr(io.StringIO()):
    print('unittest =', c(l.discover('tests', top_level_dir='.')))
"
```

Expected: pytest ≈ 2110, unittest = 774. Record both numbers in the commit message.

- [ ] **Step 6: Run the full suite once against the new runner**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests -q --ignore=tests/test_cli_e2e_progress.py > /tmp/pytest-after.txt 2>&1; tail -5 /tmp/pytest-after.txt
```

Expected: `2094 passed, 15 skipped` (the campaign failure is fixed in Task 2). If any other test fails, triage it: a genuine defect is fixed in this task, an environment-dependent test is marked `@pytest.mark.skipif` with the missing capability named in the reason, and either outcome is recorded in the commit message.

- [ ] **Step 7: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add .github/workflows/ci.yml ai-agent/tests/test_ci_workflow.py
git commit -m "fix(ci): run the python suite with pytest instead of unittest

unittest discovered 774 tests; pytest collects 2110. The 1336 tests that
never ran include every engine added since 2026-10-28 (mobile, PWA,
android toolchain, production spec, generation contract). Three tests
read the workflow itself so the runner cannot silently regress again."
```

---

## Task 4: Repair the generated-project CI leg with a committed fixture

**Files:**
- Create: `generated-projects/blogforge/**` (copied from `D:/lumicorepro-core/generated-projects/blogforge`, excluding build output)
- Modify: `.gitignore:55`
- Modify: `.github/workflows/ci.yml:81-115`
- Test: `ai-agent/tests/test_ci_workflow.py` (extend)

**Interfaces:**
- Consumes: the real BlogForge tree in the original checkout; its scripts `db:migrate` (backend), `test` (backend), `build` (frontend), `test:e2e` (frontend).
- Produces: `test_ci_workflow.py::test_ci_fixture_is_committed`, `::test_ci_fixture_leg_uses_scripts_that_exist`, `::test_ci_provides_a_database_for_the_fixture`.

- [ ] **Step 1: Write the failing tests**

Append to `ai-agent/tests/test_ci_workflow.py`:

```python
FIXTURE = ROOT / "generated-projects" / "blogforge"


def test_ci_fixture_is_committed():
    """A leg that runs npm ci on a gitignored path can never pass on CI."""
    assert FIXTURE.is_dir(), f"the committed fixture is missing: {FIXTURE}"
    assert (FIXTURE / "backend" / "package.json").is_file()
    assert (FIXTURE / "frontend" / "package.json").is_file()
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "generated-projects/" not in ignored, (
        "the whole generated-projects/ tree is gitignored, so the fixture "
        "cannot be committed; ignore the volatile subpaths instead"
    )


def test_ci_fixture_leg_uses_scripts_that_exist():
    """Every npm script the workflow calls must exist in the target package."""
    import json

    text = _workflow_text()
    calls = [
        ("generated-projects/blogforge", "test:backend"),
        ("generated-projects/blogforge/frontend", "test:e2e"),
        ("generated-projects/blogforge/backend", "db:migrate"),
        ("generated-projects/blogforge/frontend", "build"),
    ]
    for prefix, script in calls:
        assert f"npm run {script} --prefix {prefix}" in text, (
            f"CI no longer calls {script} on {prefix}"
        )
        package = ROOT / prefix / "package.json"
        assert package.is_file(), f"missing {package}"
        scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        assert script in scripts, f"{prefix}/package.json defines no {script} script"


def test_ci_provides_a_database_for_the_fixture():
    """db:migrate needs a reachable Postgres; a job without one cannot pass."""
    text = _workflow_text()
    assert "postgres:" in text, "the fixture job needs a postgres service container"
    assert "DATABASE_URL" in text, "the fixture backend needs DATABASE_URL pointing at the service"
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py -q
```

Expected: `test_ci_fixture_is_committed` FAILS (fixture absent, gitignore still `generated-projects/`).

- [ ] **Step 3: Copy the fixture, excluding build output**

```bash
cd D:/lumicorepro-core-premium-delivery
mkdir -p generated-projects
rsync -a \
  --exclude 'node_modules/' \
  --exclude 'frontend_node_modules_old/' \
  --exclude 'dist/' \
  --exclude '*.log' \
  --exclude '.git/' \
  D:/lumicorepro-core/generated-projects/blogforge/ generated-projects/blogforge/
find generated-projects/blogforge -type f | wc -l
```

Expected: roughly 236 files. On a machine without `rsync`, use:

```bash
cd D:/lumicorepro-core/generated-projects/blogforge
tar --exclude='node_modules' --exclude='frontend_node_modules_old' --exclude='dist' --exclude='*.log' -cf - . | (cd D:/lumicorepro-core-premium-delivery/generated-projects/blogforge && tar -xf -)
```

- [ ] **Step 4: Narrow the gitignore rule**

In `.gitignore`, replace line 55 `generated-projects/` with:

```
# Generated output stays ignored; the BlogForge fixture is committed because
# CI builds and tests it. Ignore only the volatile subpaths inside a fixture.
generated-projects/**/node_modules/
generated-projects/**/dist/
generated-projects/**/frontend_node_modules_old/
generated-projects/**/*.log
generated-projects/*.zip
generated-projects/build*/
```

- [ ] **Step 5: Confirm the fixture is now trackable and build output is not**

```bash
cd D:/lumicorepro-core-premium-delivery
git check-ignore -v generated-projects/blogforge/backend/package.json || echo "TRACKABLE"
git check-ignore -v generated-projects/blogforge/backend/node_modules 2>/dev/null | head -1
git status --short generated-projects | wc -l
```

Expected: the package.json line prints `TRACKABLE`; node_modules is ignored; the status count is > 200.

- [ ] **Step 6: Correct the CI leg**

In `.github/workflows/ci.yml`, replace the block from `- name: Install generated project dependencies (backend)` through the `quality_gate.py` step with:

```yaml
      - name: Install generated project dependencies (backend)
        run: npm ci --prefix generated-projects/blogforge/backend

      - name: Install generated project dependencies (frontend)
        run: npm ci --prefix generated-projects/blogforge/frontend

      - name: Run generated backend migrations
        # The fixture talks to the postgres service container, not localhost:
        # a migration step without a database proves nothing.
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/blogforge
          DB_DIALECT: postgres
        run: npm run db:migrate --prefix generated-projects/blogforge/backend

      - name: Test generated backend
        run: npm run test:backend --prefix generated-projects/blogforge

      - name: Build generated frontend
        run: npm run build --prefix generated-projects/blogforge/frontend

      - name: Run Playwright E2E for generated project
        # The Playwright config lives in frontend/, not at the fixture root.
        run: npm run test:e2e --prefix generated-projects/blogforge/frontend

      - name: Verify build (optional)
        env:
          QUALITY_GATE_VERIFY_BUILD: "1"
        run: |
          python - <<PY
          import asyncio, os, sys
          sys.path.insert(0, os.path.abspath('ai-agent'))
          from agent.quality_gate import run_quality_gate
          project_dir = os.path.abspath('generated-projects/blogforge')
          result = asyncio.run(run_quality_gate(project_dir))
          print(result)
          if not result.get('passed'):
              raise SystemExit('Quality gate failed')
          PY
```

Add a `postgres` service to the job, immediately under `runs-on: ubuntu-latest`:

```yaml
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: blogforge
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py -q
```

Expected: all tests PASS.

- [ ] **Step 8: Prove the fixture actually builds and tests locally**

```bash
cd D:/lumicorepro-core-premium-delivery/generated-projects/blogforge/backend
npm ci
npm test
cd ../frontend
npm ci
npm run build
```

Expected: backend tests pass; frontend build succeeds. If npm is unavailable in this shell, record the exact failure and mark the step `not_measured` in the phase report — never claim the fixture works from the file copy alone.

- [ ] **Step 9: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add .gitignore .github/workflows/ci.yml generated-projects/blogforge ai-agent/tests/test_ci_workflow.py
git commit -m "fix(ci): commit the BlogForge fixture and call the scripts that exist

The generated-project leg ran npm ci against a gitignored path and called
test:backend and test:e2e on packages that do not define them. The leg now
uses a committed 236-file fixture, the real script locations, and a
postgres service so db:migrate has a database to talk to."
```

---

## Task 5: Wire delivery-product verification into CI

**Files:**
- Modify: `.github/workflows/ci.yml` (new job `delivery`)
- Modify: `scripts/verify_delivery_builds.py` (accept `--root`; report per product)
- Test: `ai-agent/tests/test_ci_workflow.py` (extend)

**Interfaces:**
- Consumes: `products/sell-today/<slug>/` (11 products, 498–653 files each).
- Produces: `test_ci_workflow.py::test_ci_verifies_delivered_products`; `verify_delivery_builds.py --root products/sell-today --json <path>`.

- [ ] **Step 1: Write the failing test**

Append to `ai-agent/tests/test_ci_workflow.py`:

```python
def test_ci_verifies_delivered_products():
    """A verification script nothing invokes is documentation, not a gate."""
    text = _workflow_text()
    assert "verify_delivery_builds.py" in text, (
        "no workflow invokes scripts/verify_delivery_builds.py"
    )
    assert "products/sell-today" in text, (
        "delivery verification must run on the products that carry real source"
    )
    assert (ROOT / "scripts" / "verify_delivery_builds.py").is_file()
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py::test_ci_verifies_delivered_products -q
```

Expected: FAILS.

- [ ] **Step 3: Read the existing verifier before changing its interface**

```bash
cd D:/lumicorepro-core-premium-delivery
head -60 scripts/verify_delivery_builds.py
grep -n "argparse\|def main\|add_argument\|ROOT\|delivery" scripts/verify_delivery_builds.py | head -20
```

Adapt the flags to what the script already supports. Do not rewrite its checks: the point of this task is wiring, not a second verifier.

- [ ] **Step 4: Add the CI job**

Append to `.github/workflows/ci.yml`:

```yaml
  delivery:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"

      - name: Verify every sell-today product builds
        # delivery/ holds build output only; products/sell-today is the source
        # of truth for the eleven products that ship.
        run: |
          python scripts/verify_delivery_builds.py --root products/sell-today --json delivery-evidence.json
      - name: Upload delivery evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: delivery-evidence
          path: delivery-evidence.json
```

- [ ] **Step 5: Run the verifier locally and record its output**

```bash
cd D:/lumicorepro-core-premium-delivery
python scripts/verify_delivery_builds.py --root products/sell-today --json /tmp/delivery-evidence.json 2>&1 | tail -30
python -c "import json;d=json.load(open('/tmp/delivery-evidence.json'));print(json.dumps(d,indent=1)[:1200])"
```

Expected: a per-product verdict. If the script cannot run on this machine, record the exact error and mark the gate `not_measured`; do not mark it passing.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add .github/workflows/ci.yml scripts/verify_delivery_builds.py ai-agent/tests/test_ci_workflow.py delivery-evidence.json
git commit -m "feat(ci): verify the eleven sell-today products on every push

verify_delivery_builds.py existed but no workflow invoked it. The gate now
runs against products/sell-today (real source), uploads per-product evidence,
and never reads delivery/, which holds build output."
```

---

## Task 6: Add a ratcheted Python static-analysis gate

**Files:**
- Create: `ai-agent/pyproject.toml`
- Create: `scripts/lint_ratchet.py`
- Create: `ai-agent/lint-baseline.json`
- Modify: `ai-agent/requirements.txt`
- Modify: `.github/workflows/ci.yml` (new step in the build job)
- Test: `ai-agent/tests/test_lint_ratchet.py`

**Interfaces:**
- Consumes: `ruff check --output-format=json ai-agent`, `bandit -r ai-agent -f json -q`.
- Produces: `lint_ratchet.check(baseline, current) -> list[str]` returning human-readable failure lines; `lint_ratchet.count_violations(ruff_json, bandit_json) -> dict`.

- [ ] **Step 1: Write the failing test**

Create `ai-agent/tests/test_lint_ratchet.py`:

```python
"""A ratchet gate can only fall. These tests pin that behaviour."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "lint_ratchet.py"


def _module():
    spec = importlib.util.spec_from_file_location("lint_ratchet", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_rise_above_the_baseline_fails():
    module = _module()
    failures = module.check({"ruff": 100, "bandit_high": 2}, {"ruff": 101, "bandit_high": 2})
    assert failures == ["ruff: 101 > baseline 100"]


def test_a_fall_below_the_baseline_passes():
    module = _module()
    assert module.check({"ruff": 100, "bandit_high": 2}, {"ruff": 99, "bandit_high": 2}) == []


def test_an_unmeasured_tool_never_passes_silently():
    """If ruff is not installed, the run must say so, not report zero."""
    module = _module()
    failures = module.check({"ruff": 100}, {"ruff": None})
    assert failures == ["ruff: not measured (tool unavailable)"]


def test_the_committed_baseline_matches_the_measured_counts():
    module = _module()
    baseline_path = ROOT / "ai-agent" / "lint-baseline.json"
    assert baseline_path.is_file()
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert set(baseline) == {"ruff", "bandit_high", "bandit_medium"}
    assert all(isinstance(v, int) and v >= 0 for v in baseline.values())
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_lint_ratchet.py -q
```

Expected: FAILS — `scripts/lint_ratchet.py` does not exist.

- [ ] **Step 3: Write the ratchet**

Create `scripts/lint_ratchet.py`:

```python
"""Python lint ratchet: violation counts may only fall.

ruff and bandit both report a large existing backlog. A gate that demands
zero today would never pass, and a gate that is disabled to make it pass is
not a gate. This tool records the measured baseline in
ai-agent/lint-baseline.json and fails only when a count rises.

A tool that cannot be measured returns None, and None never passes: silence
is not evidence of a clean run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "ai-agent" / "lint-baseline.json"
TARGETS = ["ai-agent"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def ruff_violations() -> int | None:
    if not shutil.which("ruff"):
        return None
    proc = _run(["ruff", "check", *TARGETS, "--output-format=json", "--no-cache"])
    try:
        return len(json.loads(proc.stdout or "[]"))
    except json.JSONDecodeError:
        return None


def bandit_violations() -> dict[str, int] | None:
    proc = _run(
        [sys.executable, "-m", "bandit", "-r", *TARGETS, "-f", "json", "-q", "-x", "tests"]
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if "results" not in payload:
        return None
    counts = {"bandit_high": 0, "bandit_medium": 0}
    for finding in payload["results"]:
        severity = str(finding.get("issue_severity", "")).upper()
        if severity == "HIGH":
            counts["bandit_high"] += 1
        elif severity == "MEDIUM":
            counts["bandit_medium"] += 1
    return counts


def measure() -> dict[str, int | None]:
    current: dict[str, int | None] = {"ruff": ruff_violations()}
    bandit = bandit_violations()
    current["bandit_high"] = None if bandit is None else bandit["bandit_high"]
    current["bandit_medium"] = None if bandit is None else bandit["bandit_medium"]
    return current


def check(baseline: dict, current: dict) -> list[str]:
    """Return one failure line per tool that rose or could not be measured."""
    failures: list[str] = []
    for key, floor in baseline.items():
        value = current.get(key)
        if value is None:
            failures.append(f"{key}: not measured (tool unavailable)")
        elif value > floor:
            failures.append(f"{key}: {value} > baseline {floor}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()

    current = measure()
    if args.write_baseline:
        if any(value is None for value in current.values()):
            print(json.dumps(current, indent=1))
            print("Refusing to write a baseline containing an unmeasured tool.", file=sys.stderr)
            return 2
        BASELINE.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE}: {current}")
        return 0

    if not BASELINE.is_file():
        print(f"No baseline at {BASELINE}; run with --write-baseline once.", file=sys.stderr)
        return 2

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    failures = check(baseline, current)
    print(json.dumps({"baseline": baseline, "current": current}, indent=1))
    for line in failures:
        print(line, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add ruff to requirements and configure it**

In `ai-agent/requirements.txt`, under the `# ── Testing ──` block, add:

```
ruff==0.6.9
```

Create `ai-agent/pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
# E9 = syntax/IO errors, F = pyflakes. Both are correctness rules: a file that
# trips them is broken, not merely styled differently.
select = ["E9", "F"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["F401", "F811"]

[tool.bandit]
exclude_dirs = ["tests", "node_modules", ".venv"]
```

- [ ] **Step 5: Install ruff and write the first baseline**

```bash
cd D:/lumicorepro-core-premium-delivery
D:/lumicorepro-core/venv/Scripts/python.exe -m pip install "ruff==0.6.9"
D:/lumicorepro-core/venv/Scripts/python.exe -m pip show bandit >/dev/null 2>&1 || D:/lumicorepro-core/venv/Scripts/python.exe -m pip install bandit
D:/lumicorepro-core/venv/Scripts/python.exe scripts/lint_ratchet.py --write-baseline
cat ai-agent/lint-baseline.json
```

Expected: a JSON object with `ruff`, `bandit_high`, `bandit_medium`. If a tool cannot be installed, the script refuses to write a baseline and reports which tool is unmeasured — record that and leave the task blocked rather than committing a zero.

- [ ] **Step 6: Run the ratchet check**

```bash
D:/lumicorepro-core/venv/Scripts/python.exe scripts/lint_ratchet.py
```

Expected: exit 0, with `current` equal to `baseline`.

- [ ] **Step 7: Run the tests**

```bash
cd D:/lumicorepro-core-premium-delivery/ai-agent
D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_lint_ratchet.py -q
```

Expected: all four PASS.

- [ ] **Step 8: Add the CI step**

In `.github/workflows/ci.yml`, after `- name: Test AI agent` and before the generated-project steps, add:

```yaml
      - name: Python static analysis (ratchet)
        # ruff and bandit both carry an existing backlog; the baseline may only
        # fall. An uninstalled tool reports "not measured" and fails the step.
        run: python scripts/lint_ratchet.py
```

- [ ] **Step 9: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add ai-agent/pyproject.toml ai-agent/requirements.txt ai-agent/lint-baseline.json scripts/lint_ratchet.py ai-agent/tests/test_lint_ratchet.py .github/workflows/ci.yml
git commit -m "feat(ci): ratcheted ruff and bandit gate over the python agent

64K lines of python had no static analysis at all. The baseline records the
measured backlog and may only fall; an unmeasured tool reports itself as
unmeasured instead of passing silently."
```

---

## Task 7: Record the new constraints in AGENTS.md

**Files:**
- Modify: `AGENTS.md` §6 (Testing) and §13 (Monorepo rules)

**Interfaces:**
- Consumes: the numbers measured in Tasks 2–6.
- Produces: written rules that a future agent session inherits.

- [ ] **Step 1: Add the Python runner rule to §6**

Immediately after the AI agent row in the §6 table, add:

```markdown
**The AI agent suite runs under pytest, and only pytest.** `unittest discover`
collects only `TestCase` subclasses — measured 2026-10-29 it found 774 tests
while pytest collected 2110, so 1336 tests (including every engine added after
2026-10-28) silently never ran. `ai-agent/tests/test_ci_workflow.py` reads
`.github/workflows/ci.yml` and fails if the runner regresses. Do not add a
`unittest` collection command to any workflow, and do not disable that test.
```

- [ ] **Step 2: Add the gate-integrity rule to §13**

At the end of §13, add:

```markdown
- **A CI step must exercise the behaviour it certifies.** A workflow leg that
  runs `npm ci` against a gitignored path, or calls `npm run x` on a package
  that does not define `x`, cannot pass on a clean checkout and proves nothing
  until someone notices. `ai-agent/tests/test_ci_workflow.py` parses the
  workflow and asserts every invoked script exists in the target package.
- **Ratchet floors only fall.** `scripts/lint_ratchet.py` and
  `ai-agent/lint-baseline.json` record the measured ruff and bandit backlog.
  Raise a floor only when the backlog genuinely grows for a reason recorded in
  the commit; never raise one to make a run pass.
- **`delivery/` is build output, `products/sell-today/` is source.** Delivery
  verification runs on `products/sell-today/`; a gate that reads `delivery/`
  is measuring an artifact, not a product.
```

- [ ] **Step 3: Verify the file still parses as markdown and the numbers match**

```bash
cd D:/lumicorepro-core-premium-delivery
grep -n "774\|2110\|1336" AGENTS.md
grep -c "" AGENTS.md
```

Expected: the three numbers appear in §6; the file line count is within a few lines of the previous count (record both).

- [ ] **Step 4: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add AGENTS.md
git commit -m "docs(agents): record the pytest runner, gate-integrity and ratchet rules

Future sessions inherit the measured numbers and the reason the unittest
collector is forbidden, so the regression does not need to be rediscovered."
```

---

## Task 8: Phase 1 verification and report

**Files:**
- Create: `docs/superpowers/reports/2026-10-29-phase1-report.md`

**Interfaces:**
- Consumes: outputs of Tasks 1–7.
- Produces: an honest phase report listing what was measured, what passed, and what could not be measured on this machine.

- [ ] **Step 1: Run every gate once against the live tree**

```bash
cd D:/lumicorepro-core-premium-delivery
echo "--- collect counts ---"
(cd ai-agent && D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests --collect-only -q | tail -1)
echo "--- lint ratchet ---"
D:/lumicorepro-core/venv/Scripts/python.exe scripts/lint_ratchet.py; echo "exit=$?"
echo "--- workflow anti-gates ---"
(cd ai-agent && D:/lumicorepro-core/venv/Scripts/python.exe -m pytest tests/test_ci_workflow.py tests/test_lint_ratchet.py tests/test_campaign_seo.py -q)
```

Record the literal output of each command in the report. Do not summarise a command that did not run.

- [ ] **Step 2: Write the report**

Create `docs/superpowers/reports/2026-10-29-phase1-report.md` with these sections:

```markdown
# Phase 1 Report — Gates That Reported False Success

## What was measured
(one line per gate, with the literal command and its literal result)

## What passed
## What could not be measured on this machine, and why
## What changed
(commit hashes and one-line summaries)
## What Phase 2 inherits
(the 315 raw envelope calls, 23 unvalidated route files, 245 missing i18n keys)
## Not proven
(anything the report cannot evidence — never omit this section)
```

- [ ] **Step 3: Commit**

```bash
cd D:/lumicorepro-core-premium-delivery
git add docs/superpowers/reports/2026-10-29-phase1-report.md
git commit -m "docs: phase 1 verification report"
```

---

## Self-Review

**Spec coverage (Phase 0 + Phase 1 only):**

| Spec item | Task |
|-----------|------|
| 4.1 Phase 0 consolidation, four work streams | Task 1 |
| 4.2 1.1 pytest runner + anti-gate | Task 3 |
| 4.2 1.2 generated-project fixture, corrected scripts, Postgres | Task 4 |
| 4.2 1.3 delivery verification wiring | Task 5 |
| 4.2 1.4 Python static analysis ratchet | Task 6 |
| Enforcement summary rows for the above | Tasks 3–6, recorded in Task 7 |
| Phase 2/3/4 | deferred to their own plans, per the scope note |
| Campaign test failure surfaced by the pytest switch | Task 2 |

**Placeholder scan:** no `TBD`, no "add appropriate handling". The one deliberately adaptive step is Task 5 Step 3, which instructs the implementer to read the existing verifier's flags before wiring them — the script already exists and its interface must not be invented.

**Type consistency:** `lint_ratchet.check(baseline, current) -> list[str]` is defined once and used identically by the four tests in Task 6. `DIST_ONLY_CAMPAIGNS` is a `set[str]` produced in Task 2 and consumed only within Task 2.
