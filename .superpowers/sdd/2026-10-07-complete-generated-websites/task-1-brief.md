# Task 1 brief — Establish full-stack generation defaults

**Plan:** `docs/superpowers/plans/2026-10-07-complete-generated-websites.md`
**BASE:** `44fcfa31cc0733f9ad0fbb98a765c1c255546bde`

## Objective

Default newly generated websites to enterprise/full-stack, preserve an explicit static-only opt-out, and keep baseline auth/user/contact features separate from optional SaaS and payment features.

## Actual decision points found

- `ProjectModeEngine.select_mode` in `ai-agent/agent/project_mode_engine.py` currently selects static from website-type heuristics.
- The orchestrator in `ai-agent/agent/orchestrator.py` currently forces storefront prompts into client-static.
- `GenerationPlanner.create_plan` in `ai-agent/agent/planner.py` carries the registered prompt but does not normalize layout mode or baseline/optional features.
- `APIGenerator.generate_full_backend` in `ai-agent/agent/api_generator.py` adds an unconditional SaaS base set; Task 2 removes that behavior after Task 1 defines baseline feature selection.
- `docs/AI_WEBSITE_GENERATION_STANDARD.md` currently suggests ordinary sites may omit backend/database; update it to the user's new default with explicit static opt-out and conditional payment.

## Test-first acceptance

- Ordinary portfolio, business, and ecommerce types resolve to enterprise/full-stack.
- Explicit `buyer_type=static` or `deployment_mode=static` resolves to client-static.
- Planner emits baseline `jwt_auth`, `users`, and `contact` only in full-stack mode; it does not infer payment, OAuth, MFA, subscriptions, or analytics from industry.
- Legacy registry prompt still includes the active website-generation runtime rules.
- Run: `.\venv\Scripts\python.exe -m pytest ai-agent\tests\test_project_mode_engine.py ai-agent\tests\test_reach_integration.py ai-agent\tests\test_orchestrator.py -q`
