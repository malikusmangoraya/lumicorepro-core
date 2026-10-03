# ui-component-agent

A three-stage agent graph that turns a plain-language UI request into a **valid React component**.

```
FastAPI / LangGraph Agent
    │
    ├─▶ 1. inject_ui_context   pick the library components + design tokens that fit
    │
    ├─▶ 2. render_layout_base  decide the regions, order, proportions, a11y landmarks
    │
    └─▶ 3. emit_react_component  model writes the JSX, validator gates it
                                     │
                                     └─▶ React component
```

MIT licensed. No required dependencies beyond `requests`. **LangGraph is optional** — install it and the graph runs on `StateGraph`; leave it out and the identical node sequence runs through a plain executor, so the pipeline never hard-fails on a missing package and works fully offline.

---

## Why three stages instead of one prompt

One "build me a pricing page" prompt fails in predictable ways: it re-implements `<button>` when a `Button` component already exists, it invents a second `<h1>`, and it hardcodes `#3b82f6` instead of using a design token. Splitting the work makes each failure mode addressable:

| Stage | Solves | Deterministic? |
|---|---|---|
| **inject_ui_context** | the model reuses the real library instead of generic markup | yes — registry lookup + scoring |
| **render_layout_base** | structure, region order, proportions, landmarks | yes — presets + inference |
| **emit_react_component** | the JSX itself | no — this is the only model call |

The first two stages cost nothing and never fail. A bad model answer is caught by validation and replaced with a deterministic component, so the endpoint always returns buildable JSX.

---

## Install

```bash
pip install requests              # only hard requirement
pip install langgraph             # optional, enables StateGraph execution
```

## Use

### As a library

```python
from agent.ui_component_agent import run_graph

result = run_graph(
    "SaaS pricing page with three tiers",
    component_name="PricingPage",
    layout="auto",          # auto | single | section | page | dashboard | form | landing
)

print(result["code"])        # React source
print(result["source"])      # "provider" | "fallback"
print(result["context"])     # categories, matched components, registry size
print(result["layout"])      # regions + ASCII wireframe
```

### As an API

```bash
POST /api/v1/ui-component
{
  "request": "SaaS pricing page with three tiers",
  "component_name": "PricingPage",
  "layout": "auto",
  "provider": null,          // or "gemini", "openrouter", or "none" to force offline
  "limit": 8
}
```

Response is enveloped as `{success, status, message, data, timestamp}`.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ui-component \
  -H 'Content-Type: application/json' \
  -d '{"request":"login page with email and password","component_name":"LoginPage"}'
```

### Force offline / deterministic

```bash
export AI_OFFLINE=1
# or per-call:
run_graph("a page", provider="none")
```

---

## Configuration

**Component registry** — defaults to `registry/components.json`, a list of:
```json
{
  "name": "LoginForm",
  "category": "auth",
  "tags": ["login", "email", "password"],
  "description": "User login form with input validation.",
  "file_path": "src/components/auth/LoginForm.jsx",
  "dependencies": ["lucide-react"],
  "features": ["email_login", "remember_me"]
}
```
A missing or corrupt registry degrades to semantic HTML — it never raises.

**Layout presets** — `single`, `section`, `page`, `dashboard`, `form`, `landing`. `auto` infers from the request text (dashboard keywords → `dashboard`, form/login/checkout → `form`, landing/marketing → `landing`, otherwise `page`).

**Design tokens** — the emitter may only reference the tokens in `context.ALLOWED_TOKENS`. Any other `var(--t-*)` is reported as an undeclared token.

---

## Validation

Output is rejected (and replaced by the deterministic component) when it:

- is empty, or contains an unclosed markdown fence
- is missing `export default`
- has no `h1`/`h2` at all, or more than one `h1`
- exceeds 400 lines or 20 000 characters
- contains a raw hex colour instead of a token
- references a token outside the allowed set
- imports from `@/components/...` (an alias that will not resolve in a consumer project)

---

## Tests

```bash
python -m pytest tests/test_ui_component_agent.py -q
```

50 hermetic tests: no network, no API key, no LangGraph. Provider is always a stub, registry is always a fixture. One test reads the real shipped registry to prove stage 1 is not theatre.

---

## Extend

Add a node by writing a pure function that takes the state dict and returns it merged, then register it in `run_graph`:

```python
def _node_i18n(state):
    return {**state, "i18n": collect_strings(state["result"]["code"])}

NODE_SEQUENCE.append("i18n")
```

Stage functions are deliberately free of I/O so they stay testable in isolation.

## License

MIT — see `LICENSE`.
