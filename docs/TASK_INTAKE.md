# Market-First Task Intake

Every task given to the operator runs through a **market analysis first**: real
industry benchmarks, live community demand signals, achievable pricing, and
**2-4 product options**. Nothing is built until one option is selected. This
keeps delivery grounded in the target market instead of guessing.

## Flow

```
operator task  -->  POST /api/tasks/intake          market demand + pricing + options
                        |
user selects    <--  options (lean_mvp / full_saas /
                        niche_differentiated / internal_tool)
                        |
              -->  POST /api/tasks/select           blueprint + real build start
                        |
build run  (stream via /ws/generate/{run_id})
```

## Step 1 - intake

`POST /api/tasks/intake` (API-key required, rate-limited):

```json
{ "prompt": "SaaS dashboard that invoices freelance photographers", "use_live_signals": true }
```

Response highlights:

- `market` - industry benchmark data: competitors (real companies), market
  profile (size / conversion / mobile share / PK growth), conversion drivers,
  differentiation gaps, target Lighthouse score.
- `live_signals` - trimmed digest of Reddit/X community signals
  (`preferred_features`, `complaints`, `risk_flags`, evidence snippets).
  When Reddit/X is unreachable the intake still completes from benchmarks.
- `options` - 2-4 buildable variants. Each carries:
  - `demand` - score 0-100, band (`high|solid|emerging|early`) and quoted
    evidence;
  - `monthly_price` - **indicative** (`"estimate": true`) SaaS tier band for
    the market-size class; verify against the listed competitors before
    launch;
  - `features` - contract-mapped feature keys the pipeline delivers;
  - `risk` and `estimated_effort_days`.

Option types: `lean_mvp` (fast public launch, no backend), `full_saas`
(accounts, dashboard, payments-ready), `niche_differentiated` (hook taken
from a live community demand or benchmark growth gap), `internal_tool`
(private operations, no public monetization).

## Step 2 - select

`POST /api/tasks/select` (API-key required):

```json
{ "intake_run_id": "<run_id from step 1>", "option_id": "full_saas", "product_name": "LensLedger" }
```

Response:

- `blueprint` - the concrete build structure: mode
  (`client_static` vs `enterprise_fullstack`), stack, features, full page
  list, API surface, DB tables, integrations, mandatory legal pages
  (privacy / terms / refund / cookie consent), i18n/RTL posture, QA gates
  (tests + production build + **market audit >= 80**), acceptance criteria
  and deployment plan.
- `build` - a **real queued generation run** (`run_id`, `ws_url`); stream
  the same way as `POST /api/generate` runs. The selected option's features
  and positioning are injected into the build prompt and the blueprint plus
  the market analysis are handed to the orchestrator.

## Engine-level use

The same path is available without the server:

```python
from agent.task_intake import analyze_demand, build_blueprint, blueprint_summary

intake = analyze_demand("Handmade-craft ecommerce for the global market", use_live_signals=False)
bp = build_blueprint(intake, intake["options"][1]["id"])
print(blueprint_summary(bp))
```

Tests: `ai-agent/tests/test_task_intake.py` (5 cases, signals injected via a
fake runner; no network in tests).
