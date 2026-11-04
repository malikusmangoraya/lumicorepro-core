# LumicorePro Hardening — Design Spec

**Date:** 2026-10-29
**Target:** `D:\lumicorepro-core-premium-delivery` (branch base `master` @ `539fecbf`)
**Status:** Awaiting user review
**Author:** Qoder agent session

---

## 1. Problem

The request was "make everything perfect in LumicorePro". A repository audit on
2026-10-29 found that this is not one task but eight independent workstreams,
and that several of the repository's existing gates do not measure what they
claim to measure. The most serious finding is that CI reports success while a
majority of the Python test suite never executes.

Every number in this document was measured against the live working tree, not
inferred from documentation. Where a claim in the repository's own docs
contradicts the code, the code is treated as authoritative and the doc drift is
itself listed as a defect.

---

## 2. Measured baseline

All figures below were produced by running the tools against
`D:\lumicorepro-core-premium-delivery` at commit `539fecbf` plus its
uncommitted work.

### 2.1 Python test execution (CRITICAL)

| Runner | Tests collected |
|--------|-----------------|
| `python -m unittest discover -s tests -t .` (what CI runs) | **774** |
| `python -m pytest tests --collect-only` | **2110** |
| **Never executed in CI** | **1336** |

`ai-agent/tests/` contains 113 test files. Only 54 contain a
`unittest.TestCase` subclass; the other 59 use bare `def test_*` functions that
`unittest discover` cannot collect. Every engine test added in the current
uncommitted work is in that uncollected set — `test_mobile_verify.py`,
`test_pwa_kit.py`, `test_browser_qa.py`, `test_production_spec_kit.py`,
`test_android_toolchain.py`, `test_app_delivery.py`, `test_premium_generation.py`.

`pytest==8.2.0` is already pinned in `ai-agent/requirements.txt:73`. No new
dependency is required to fix this.

The regression was introduced by commit `8c20a79a`, which replaced
`python -m pytest tests -q` with the `unittest` command. Three other
workflows (`ci-cd.yml:69`, `test.yml:72`, `autopilot.yml:137`) still use
pytest, so `ci.yml` is the sole outlier.

### 2.2 CI generated-project leg

`.github/workflows/ci.yml:81-115` operates on `generated-projects/blogforge`.
That path is matched by `.gitignore:55` (`generated-projects/`) and is
untracked (`git ls-files generated-projects` returns nothing). No workflow
generates it before use. The leg therefore cannot pass on a clean checkout.

Three additional broken links inside that leg:

| CI call | Reality |
|---------|---------|
| `npm run test:backend --prefix generated-projects/blogforge/backend` | `blogforge/backend/package.json` defines `test`, not `test:backend` |
| `npm run test:e2e --prefix generated-projects/blogforge` | `blogforge/package.json` has no `test:e2e`; the Playwright config lives in `blogforge/frontend/` |
| `npm run db:migrate --prefix .../blogforge/backend` | Script exists, but requires a reachable Postgres, which the job does not provide |

A real BlogForge source tree does exist at
`D:\lumicorepro-core\generated-projects\blogforge` (236 real source files,
one backend test file, one Playwright spec).

### 2.3 Delivery product verification

| Fact | Measurement |
|------|-------------|
| Scripts that exist but are wired into no workflow | `final_verify_delivery.py`, `verify_delivery_builds.py`, `harden_delivery_package.py` |
| `delivery/` directories | 96 |
| Directories with real source | **1** (`orbitboard`, 41 files) |
| Directories holding only `dist/` build output | 90 |
| Manifest rows failing the manifest's own brand rule | **26 of 95** |
| Products with real source in `products/sell-today/` | 11 (498-653 files each) |

`delivery/` is a build-output directory, not a source-of-truth location. The
real product sources are `products/sell-today/*`.

### 2.4 Backend envelope and validation

| Fact | Measurement |
|------|-------------|
| Raw `res.status(...).json(...)` calls in `backend/routes` + `backend/middleware` | **315** |
| Calls routed through the canonical helper (`backend/utils/response.js`) | 51 |
| Route files with raw JSON but zero envelope usage | 27 of 34 |
| Route files with no request validation at all | **23 of 34** |

Only `auth.routes.js` and `order.routes.js` use the shared `validateRequest`
middleware; 10 more use `express-validator` inline.

### 2.5 i18n

| Fact | Measurement |
|------|-------------|
| Distinct `t('...')` keys used in `src/` | 337 |
| Leaf keys present in `src/i18n/locales/en.json` | 443 |
| `t()` keys **missing** from `en.json` | **245** |
| Effective translation coverage | **27.3%** |
| JSX/TSX files importing `useTranslation` | 22 of 395 |

Most rendered strings fall back to the raw key. `AGENTS.md` §10 forbids
hardcoded strings; nothing enforces it.

### 2.6 Python static analysis

No `pyproject.toml`, `setup.cfg`, `ruff.toml`, `.flake8`, `mypy.ini` or
`pytest.ini` exists. `eslint.config.js:8-9` globally ignores `ai-agent` and
`backend`, so no JavaScript linter reaches the backend either (the backend has
its own `backend/eslint.config.js`, invoked by `ci.yml:54-58`).

`pylint>=3.0.3` and `bandit>=1.7.7` are already declared in
`ai-agent/requirements.txt`. Only a config and a CI step are missing — again no
new dependency.

### 2.7 Documentation drift

| Document | Defect |
|----------|--------|
| `docs/STATUS.md:5-6` | Cites commit `44fcfa3`; the branch head is `539fecbf`. Generated 2026-10-07. |
| `docs/STATUS.md:3` | Claims "CI enforces freshness with `generate_status.py --check`" — no workflow calls it. |
| `docs/STATUS.md` | Backend coverage stated as 26.29%; `AGENTS.md` §6 states 74.79%. |
| `docs/FACTORY.md:45` | "Exit code is 0 only when the run is `delivered`"; `ai-agent/main.py:11` defines `_OK_STATUSES = {"delivered", "built"}` and `main.py:246` exits 0 for `built`. |
| `docs/LUMICOREPRO_IMPROVEMENTS_ROADMAP.md` | Lists `I1 CI/CD pipeline`, `C3 Stripe checkout`, `B5 React 18 vs 19` and `I4 OpenAPI` as pending; all four are shipped. |

### 2.8 Repository topology

Four divergent work streams, each holding uncommitted work:

| Location | Branch | State |
|----------|--------|-------|
| `D:\lumicorepro-core` | `agents/lumicorepro-core-integration-query` @ `eb55f96d` | 5 commits behind master; uncommitted Orbitboard CI steps; untracked `delivery/` and `.backup/` |
| `D:\lumicorepro-core-premium-delivery` | `feature/premium-delivery-gates` @ `539fecbf` | 30+ uncommitted premium files (mobile/PWA/engine work) |
| `D:\lumicorepro-core-stack-catalog` | `feature/backend-stack-catalog` @ `e5155864` | 40 uncommitted files (backend stack catalog + 12 locale files); its commit is already merged into master |
| `feat/orbitboard-live-completion` | @ `98650aa1` | Not merged into master; carries the real `delivery/orbitboard/app` source |
| `chore/orbitboard-actions-node24` | @ `87c14737` | Not merged into master |

`master` is 15 commits ahead and 2 behind `origin/master` (`800de001`), which
has no Python CI step at all. The divergence is expected to be resolved by a
rebase rather than a force-push.

---

## 3. Non-goals

- Rewriting the AI agent, the factory pipeline, or the backend architecture.
- Adding new product features. Every item here removes a false signal or
  restores an already-promised guarantee.
- Migrating the backend off MySQL/Postgres, or off Express.
- Changing the delivery product catalogue or adding new generated products
  beyond the CI fixture.
- Lowering any existing coverage ratchet to make a run pass.

---

## 4. Approach and sequencing

The work is ordered so that every later phase is verified by gates repaired in
earlier phases. Fixing product quality before the test runner works would
produce changes with no way to prove them.

```
Phase 0  Consolidate the four work streams into one branch
Phase 1  Repair the gates that currently report false success
Phase 2  Backend envelope + validation conformance
Phase 3  i18n coverage
Phase 4  Documentation truth
```

### Phase 0 — Consolidation

Target: `D:\lumicorepro-core-premium-delivery`, new branch
`feature/hardening-v8` off `master` @ `539fecbf`.

1. Commit the 30+ uncommitted premium files in the premium-delivery worktree
   as `chore(save): preserve premium delivery work`. Nothing is discarded.
2. Cherry-pick `e5155864` (backend stack catalog design spec, already an
   ancestor of master) and commit the 40 uncommitted stack-catalog files as
   `feat(backend-stack): backend stack catalog selection`.
3. Cherry-pick `98650aa1` and `87c14737` for the Orbitboard product and its
   CI wiring.
4. Land the original checkout's uncommitted `ci.yml` Orbitboard steps and
   `delivery/orbitboard/app` — only if they are not already carried by the
   cherry-picks above.
5. Produce `feature/hardening-v8` containing all of the above.

Safety rules for this phase:

- Every stash is committed before any branch operation. No `reset --hard`, no
  `checkout --`, no `clean`.
- The original checkout `D:\lumicorepro-core` is never modified except to read
  from it. Its `.backup/` directory is protected and untouched.
- If a cherry-pick conflicts, resolve in favour of keeping master, and record
  the conflict in the phase report.

Exit criteria: `feature/hardening-v8` contains every uncommitted change from
all four work streams; the working tree of the premium-delivery worktree is
clean; the original checkout still shows its uncommitted work untouched.

### Phase 1 — Gates that report false success

#### 1.1 Python test runner

Replace `ci.yml:78` with `python -m pytest tests -q`. The
`--ignore=tests/test_cli_e2e_progress.py` flag used by the other three
workflows is retained.

Anti-gate (required): a test asserts that the CI workflow file runs pytest and
not `unittest discover`. Without it, a future edit can silently restore the
regression. The regression test must fail against the current `ci.yml` and pass
after the fix.

#### 1.2 Generated-project fixture

Commit the real BlogForge source from
`D:\lumicorepro-core\generated-projects\blogforge` into
`generated-projects/blogforge` on `feature/hardening-v8`, excluding
`node_modules/`, `dist/`, `frontend_node_modules_old/` and `*.log`
(already covered by `.gitignore`). `.gitignore:55` is narrowed from
`generated-projects/` to the specific volatile subpaths so the fixture can be
tracked while generated output stays ignored.

The CI leg is corrected to the script names that actually exist:

| Step | Corrected call |
|------|----------------|
| Backend tests | `npm run test:backend --prefix generated-projects/blogforge` (the root script that forwards to `backend`) |
| Frontend E2E | `npm run test:e2e --prefix generated-projects/blogforge/frontend` |
| Migrations | runs against the CI service Postgres, not a local socket |

The job gains a `postgres` service container and the generated backend's
`DATABASE_URL` is pointed at it, so `db:migrate` has a real database. A step
that cannot reach a database is reported as `not_measured`, never as a pass.

The `quality_gate.py` verification step at `ci.yml:99-115` is kept and pointed
at the committed fixture.

#### 1.3 Delivery verification wiring

`scripts/verify_delivery_builds.py` and `scripts/final_verify_delivery.py` are
invoked from a new CI job that operates on `products/sell-today/*` — the eleven
products that carry real source — rather than on `delivery/*`, which holds only
build output.

The job reports, per product: build success, backend test result, and the
brand checks the manifest already defines. The 26 manifest rows that fail the
brand rule are reported as failures, not skipped.

Anti-gate: a test asserts the workflow references the verification script, so
the wiring cannot be dropped silently.

#### 1.4 Python static analysis

Add `ai-agent/pyproject.toml` with `ruff` configured, plus a `bandit`
configuration, and a CI step that runs both. Ruff is added to
`ai-agent/requirements.txt` because it is not currently present.

The ruff and bandit thresholds are **ratchets**: the first run establishes the
measured baseline, the config records exactly that baseline, and the CI step
fails only on a violation count above it. `ruff --fix` output is not applied
automatically, because an autofix across 64K lines is a behaviour change, not a
lint gate.

Anti-gate: the ratchet test asserts the configured threshold equals the
measured count, so the floor cannot be lowered to make a run pass.

### Phase 2 — Backend conformance

#### 2.1 Envelope

Convert raw `res.status(...).json({...})` calls in `backend/routes/` and
`backend/middleware/` to the helpers in `backend/utils/response.js`. The
helper already emits exactly the shape `AGENTS.md` §4 requires and guards
against double-sending after headers are flushed.

The 315 raw calls are converted in mechanical batches, one route file at a
time, with the route's own tests run after each batch.

The gate is a ratchet on the raw-call count, stored in a checked-in baseline
file. CI fails if the count rises. The floor starts at 315 and may only fall.

Anti-gate: a test asserts the baseline file's number is less than or equal to
the count in the previous revision, so lowering the floor is a visible diff.

#### 2.2 Validation

The 23 route files with no validation get the shared `validateRequest`
middleware or inline `express-validator` chains, matching whichever pattern
the file's neighbours already use. Per `AGENTS.md` §3, validation is a
server-side requirement regardless of client-side checks.

The gate is a ratchet on the count of unvalidated route files, starting at 23.

#### 2.3 Security spot-check

`middleware/security.js:171-174` and `middleware/auth.js:76-79` return
`{success:false, error}` without `status`, `message`, `data` or `timestamp`.
These are included in the Phase 2.1 conversion.

### Phase 3 — i18n

1. Add the 245 missing keys to `src/i18n/locales/en.json` with real English
   copy, not the key name repeated back.
2. Propagate to the other 12 locale files that already exist in
   `src/i18n/locales/`, using each locale's existing translation where one is
   available and English where it is not.
3. Extract the ~140 hardcoded JSX string literals.

The gate is an ESLint rule or a script that fails CI when a `t('...')` key is
absent from `en.json`. The threshold is a ratchet on the missing-key count,
starting at 245, so a newly introduced untranslated key fails the build even
before the full extraction is finished.

Anti-gate: the rule must also prove it does not fire on a key that exists, so
a broken extractor cannot disable the check by making it fail on everything.

### Phase 4 — Documentation truth

1. Regenerate `docs/STATUS.md` with `scripts/generate_status.py` and wire
   `generate_status.py --check` into CI, so the claim on its own line 3
   becomes true.
2. Correct `docs/FACTORY.md:45` to describe the real exit-code contract from
   `ai-agent/main.py:11`.
3. Rewrite `docs/LUMICOREPRO_IMPROVEMENTS_ROADMAP.md` against the shipped
   state, moving completed items out and keeping the genuinely open ones.
4. Update `AGENTS.md` §6 with the measured Python test count, and add a rule
   recording that a CI step must exercise the behaviour it certifies.

Gate: `generate_status.py --check` in CI.

---

## 5. Enforcement summary

Every fix ships with an enforcement mechanism and a written rule, following the
existing pattern in `AGENTS.md` §13 and §18.

| Gate | Mechanism | Baseline |
|------|-----------|----------|
| Python tests actually run | CI runs pytest | 774 → 2110 collected |
| CI cannot revert to unittest | Test asserting the workflow command | fails on `unittest` |
| Generated project builds | Committed fixture + corrected CI script names | fixture must pass |
| Delivery products verified | CI job invoking `verify_delivery_builds.py` | 11 products |
| Python static analysis | ruff + bandit with ratchet floors | measured on first run |
| Backend envelope | Ratchet on raw `res.json()` count | 315 (may only fall) |
| Route validation | Ratchet on unvalidated route-file count | 23 (may only fall) |
| i18n completeness | Ratchet on missing `t()` key count | 245 (may only fall) |
| Docs freshness | `generate_status.py --check` | regenerated |

Each gate pairs with a test proving it does not fire when its condition is
satisfied, and each gate is run once against the live tree with its actual
output recorded.

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| pytest surfaces 1336 previously-unrun tests that fail | Expected and intended. Failures are triaged into genuine defects (fixed) and environment-dependent tests (marked and documented). The count cannot exceed the baseline without being reported. |
| The 315-call envelope conversion breaks route tests | Batches are small and each batch runs the route's tests. The ratchet keeps the count visible throughout. |
| 245 i18n keys is a large, low-value diff | Split into mechanical key addition (bulk) and JSX extraction (per area), keeping each commit reviewable. |
| Consolidation conflicts across four work streams | Every change is committed before any branch operation; conflicts resolve toward master; the original checkout is read-only. |
| The BlogForge fixture adds repository weight | The fixture is 236 source files with `node_modules` and `dist` excluded. It replaces a CI leg that currently fails. |
| A ratchet floor is set too high and blocks legitimate work | Floors are set at the measured baseline and only ever move down for the count-based gates. |

---

## 7. Out of scope, recorded for later

These were measured and confirmed but are not part of this work:

- `docs/STATUS.md` backend coverage figure (26.29% vs 74.79%) — regenerated in Phase 4.
- The 26 brand-noncompliant manifest rows — the Phase 1.3 job will report them;
  repairing the branding of 26 products is a separate content task.
- The 90 `delivery/` directories holding only build output — these are release
  artifacts, not source, and `products/sell-today/` is the source of truth.
- iOS signing and store submission — explicitly unsupported delivery claims
  under `AGENTS.md` §13.
