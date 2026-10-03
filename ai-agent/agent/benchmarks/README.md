# Offline Public-Development Benchmark

Grades the Lumicore Python agent on **real bug-fixing tasks** from real
open-source Python repositories, entirely offline. Each task carries the issue
text, a frozen git snapshot, and the upstream `test_patch`, so a fix is only ever
credited when the repository's own tests prove it.

## Corpus layout

Point `BENCH_DATA_DIR` (or `--data`) at the bundle root:

```
<data>/tasks.jsonl        129 tasks: issue, gold patch, test patch, F2P/P2P test ids
<data>/snapshots/*.tgz    frozen working trees (FastAPI, Rich, requests, httpx, ...)
<data>/graphs/*.json      per-repo AST call + dependency graphs
<data>/embeddings/*       per-repo node embedding vectors
<data>/wheels/*.whl       offline evaluation wheels (adk_eval_core)
<data>/HARNESS_README*    official harness notes
```

Field names in `tasks.jsonl` vary between releases, so every value is resolved
through a key probe (`problem_statement` / `issue` / `description` / …) and any
unrecognised key is preserved on `task.raw`. `doctor` prints exactly what
resolved, so a schema drift is visible immediately instead of silently scoring 0.

## Quick start

```powershell
cd ai-agent
$env:BENCH_DATA_DIR = "D:\path\to\benchmark-corpus"

python -m agent.benchmarks doctor                 # verify corpus + git + task integrity
python -m agent.benchmarks list --limit 10        # what each task resolves to
python -m agent.benchmarks run --solver noop      # grader sanity check (expect ~0%)
python -m agent.benchmarks run --solver ai --jobs 4
python -m agent.benchmarks report --json ..\generated-projects\bench-out\benchmark-report.json
```

Always run `--solver noop` first. If the untouched repository scores anything
above zero, grading is broken and every other number is meaningless. The no-op
solver is a *measurement*, so it is graded and reported as `unresolved` (never as
a harness error) — that is the signal you are looking for.

## Task statuses vs exit codes

| Task status | Meaning |
| --- | --- |
| `resolved` | every F2P passes, no P2P regression |
| `unresolved` | graded, but the fix did not land (includes the no-op baseline) |
| `error:no_snapshot` / `error:snapshot_extract` | corpus is missing or the archive is unsafe |
| `error:test_patch_unapplicable` | the dataset's own tests do not apply to the snapshot |
| `error:reference_leakage` | gold-patch text reached the solver — scores are invalid |
| `error:no_patch` / `error:patch_not_replayable` | the solver produced a diff that does not apply |
| `grader_error` / `timeout` | pytest, python, or the test command itself failed |

| CLI exit | Meaning |
| --- | --- |
| `0` | ran cleanly (0% resolved is a valid result) |
| `2` | no dataset found |
| `3` | at least one harness error, or leakage detected |
| `4` | ran cleanly but `--fail-under <pct>` was not met |

## How a task is graded

1. extract the snapshot into a disposable git checkout
2. apply the dataset `test_patch` and run the suite → **baseline** failures
3. `git reset --hard` back to pristine, so the solver never sees the grader's tests
4. build the context bundle and run the **leakage guard** (must be clean)
5. let the solver mutate the tree
6. capture the candidate diff, replay it onto a clean tree, re-apply `test_patch`
7. run the suite again and compare

Resolved means: every `FAIL_TO_PASS` test passes and no `PASS_TO_PASS` test
regressed. Tasks without an F2P list fall back to a whole-suite gate (exit 0, no
failures/errors) and are reported as such. Unmeasured tasks are counted
separately from failures — the report can never look better than the evidence.

## Agent tools the solver gets

| Tool | Source | Use |
| --- | --- | --- |
| code search | `embeddings/` vectors | rank the nodes most relevant to the issue |
| lexical fallback | BM25 over node ids | used automatically when vectors are missing |
| symbol graph | `graphs/` | callers, callees, transitive impact set |
| repository state | git | `status`, `log`, `diff` on a real frozen tree |
| file IO | workspace | read/write inside the checkout only (traversal-blocked) |
| test feedback | grader output | failing test ids + tracebacks fed back on retry |

The context bundle is capped by `BENCH_MAX_CONTEXT_CHARS` (default 24 000) and
lists files by rank. `assert_no_leakage` compares the bundle against the gold
patch and the F2P ids; a violation aborts that task and is reported — a run with
leakage is scored as invalid.

## Solvers

| `--solver` | Behaviour |
| --- | --- |
| `ai` (default) | provider pool → unified diff → `git apply` → retry with the real `git apply` error |
| `noop` | changes nothing; proves the grader is not free points |
| `scripted` | replays `--patch <file>`; used for patch-replay audits and tests |

`ai` needs a provider: `ACTIVE_AI_PROVIDER` + the matching key (or a running
OmniRoute/9Router gateway). With no provider it fails honestly with
`provider_unavailable` instead of inventing a result.

## Configuration

All optional; see `ai-agent/.env.example`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `BENCH_DATA_DIR` | `<repo>/benchmarks-data` | corpus root |
| `BENCH_WORKSPACES_DIR` | `generated-projects/.bench/workspaces` | per-task checkouts |
| `BENCH_REPORT_DIR` | `generated-projects/bench-out` | JSON + Markdown reports |
| `BENCH_JOBS` | `1` | concurrent tasks (grading is subprocess-bound) |
| `BENCH_PYTEST_TIMEOUT_SECS` | `300` | per-task test timeout |
| `BENCH_MAX_CONTEXT_CHARS` | `24000` | context budget per task |
| `BENCH_KEEP_WORKSPACES` | `false` | keep checkouts for debugging |

`--reuse-cache` edits the cached extraction in place (much faster, destructive);
`--keep-workspaces` and `--clean` help when a task misbehaves. `--limit 0` (or
omitting it) runs every task; `--fail-under <pct>` makes a low resolve rate exit
`4` so CI can enforce a floor.

## Running the snapshot's own test suite

Each snapshot ships its own dev environment. The grader prefers
`.venv/Scripts/python.exe` (or `venv/`, `env/`) inside the checkout and falls
back to the harness interpreter. Install a repo's dependencies once, offline,
from the bundled wheels:

```bash
python -m pip install --no-index --find-links <data>/wheels -r <repo>/requirements-dev.txt
```

Missing dependencies surface as `collection_error` / `grader_error` — reported,
never scored as a pass.

## Kaggle bundle

```powershell
python -m agent.benchmarks package --out ..\dist\bench-kaggle.zip
```

Produces a code-only zip (harness, tests, `run_benchmarks.sh`,
`install_harness.sh`, `dataset-manifest.json`, this README). The corpus itself is
mounted or downloaded separately so the upload stays small. On Kaggle:

```bash
bash run_benchmarks.sh /kaggle/input/public-dev-benchmark
```

## Notes and limits

- Windows-safe: archives are extracted with traversal, symlink and device-node
  protection; git runs with `core.autocrlf=false` so diffs are byte-faithful.
- An archive with a single wrapping directory is unpacked to the repo root.
- Snapshots are extracted once and cached, so a 129-task run does not re-unpack
  the same repository 40 times.
- `numpy` is optional — JSON/lexical search covers missing or binary embeddings.
- No task result is ever inferred: unmeasured stays unmeasured.
