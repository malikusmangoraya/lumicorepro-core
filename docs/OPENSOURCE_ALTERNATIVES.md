# Open-Source Alternatives Map

> Last updated: 2026-10-06 · LumicorePro Core 8.2

This page answers one question honestly: **which open-source / internet-only
alternatives are actually wired into this repo, and which are not.**

It exists because "add the alternative of Lovable" is ambiguous. There are three
different categories in that request, and only one of them is a thing you add to a
provider table:

| Category | Examples | What "adding it" means |
|---|---|---|
| **Inference hosts** (who runs the model) | Cerebras, Together, Qwen/DashScope, Groq | A row in the vendor table + env var — **done, 15 of them** |
| **AI app builders / coding agents** (the product) | Lovable, v0, Bolt.new, Replit, Cursor | A *feature set*. This monorepo **is** the self-hosted alternative |
| **Developer tooling** (test, deploy, QA) | Lighthouse CI, Playwright, k6, Docker | A dependency + config + script |

Nothing below is claimed as integrated unless it is in the repo and covered by a
test or a live check.

---

## 1. Added: internet-only open-weight inference (15 hosts)

Every one of these serves **open-weight** models over a public HTTPS API. There is
no local/offline GPU path anywhere in the provider layer — `OFFLINE_ONLY_SLUGS` in
`ai-agent/providers/openweight_provider.py` records that decision and
`ai-agent/tests/test_open_weight_cloud.py` enforces it.

| Slug | Vendor | Endpoint | Env var | Weights |
|---|---|---|---|---|
| `cerebras` | Cerebras | `api.cerebras.ai/v1` | `CEREBRAS_API_KEY` | Qwen, gpt-oss (Apache-2.0), Llama 3.3 |
| `groq` / `grok` | Groq Cloud | `api.groq.com/openai/v1` | `GROK_API_KEY` | Llama, Qwen, gpt-oss |
| `nebius` | Nebius Token Factory | `api.tokenfactory.nebius.com/v1` | `NEBIUS_API_KEY` | DeepSeek, Qwen, Llama |
| `hyperbolic` | Hyperbolic | `api.hyperbolic.xyz/v1` | `HYPERBOLIC_API_KEY` | Qwen, Llama, DeepSeek |
| `zai` | Z.ai (ex Zhipu) | `api.z.ai/api/paas/v4` | `ZAI_API_KEY` | **GLM** — MIT for the 4.5 family |
| `dashscope` | Alibaba Model Studio | `dashscope-intl.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` | **Qwen3** — Apache-2.0 |
| `together` | Together AI | `api.together.xyz/v1` | `TOGETHER_API_KEY` | 200+ open models |
| `deepinfra` | DeepInfra | `api.deepinfra.com/v1/openai` | `DEEPINFRA_API_KEY` | Llama, Qwen, DeepSeek |
| `fireworks` | Fireworks AI | `api.fireworks.ai/inference/v1` | `FIREWORKS_API_KEY` | Llama, Qwen, DeepSeek |
| `sambanova` | SambaNova | `api.sambanova.ai/v1` | `SAMBANOVA_API_KEY` | Llama, DeepSeek, Qwen |
| `novita` | Novita AI | `api.novita.ai/v3/openai` | `NOVITA_API_KEY` | Llama, Qwen, DeepSeek |
| `huggingface` | HF Inference Providers | `router.huggingface.co/v1` | `HUGGINGFACE_TOKEN` | full HF catalogue |
| `featherless` | Featherless | `api.featherless.ai/v1` | `FEATHERLESS_API_KEY` | full HF catalogue |
| `chutes` | Chutes | `llm.chutes.ai/v1` | `CHUTES_API_KEY` | DeepSeek, Qwen, Llama |
| `minimax` | MiniMax | `api.minimax.io/v1` | `MINIMAX_API_KEY` | M-series, open weights |
| `cohere` | Cohere | `api.cohere.ai/compatibility/v1` | `COHERE_API_KEY` | Command A/R — **CC-BY-NC (non-commercial)** |

Plus these already-present internet hosts, which are not classified as
"open-weight cloud" in the vendor table but serve the same role:
`nvidia` (NIM), `gemini`, `deepseek`, `claude`, `openai`, `openrouter`, `mistral`,
`kimi`.

**Total fallback chain: 24 internet hops.** Run
`python -c "from config.providers import FALLBACK_ORDER; print(len(FALLBACK_ORDER))"`
to confirm.

### Licence caution

`cohere` is served through a compatibility layer but its Command A/R weights are
**CC-BY-NC-4.0 — non-commercial**. Do not use that hop for client work or
marketplace deliverables. It sits near the bottom of `FALLBACK_ORDER` for that
reason. The Apache-2.0 / MIT / Llama-Community hosts above it are the safe ones.

### Deliberately NOT listed

| Host | Why not |
|---|---|
| Kluster.ai | Shut down 2026-06-09 |
| GitHub Models | Retired 2026-07-30 |
| Ollama, vLLM, llama.cpp, LM Studio, LocalAI | Local GPU runtimes — require hardware on the operator's machine |
| Perplexity | `sonar` models are not open-weight |
| xAI (`grok-*`) | Grok weights are not published |

A dead or non-open endpoint in the table is worse than an absent one: it looks
configured while never answering.

---

## 2. The named products — and what the actual alternative is

### Google AI Studio
Google AI Studio is Google's model playground; the API behind it is the **Gemini
API**, which is already integrated as the `gemini` provider (with a free tier).
It is **not** an open-weight host, so it has no "open-source alternative" in the
provider sense. Its *job* — give me a capable model over the internet for free or
cheap — is now covered by the 15 open-weight hosts above, several of which have
free tiers (`cerebras`, `groq`, `zai`, `dashscope`).

If you want a *local* substitute for AI Studio, that is Ollama/LM Studio — and
that is exactly what this repo refuses to require.

### Replit / Lovable / v0 / Bolt.new / Cursor / Windsurf
These are **AI app builders and coding agents**. This monorepo is the self-hosted
open alternative to them, so the honest mapping is capability-by-capability:

| Their capability | Open-source alternative | Status here |
|---|---|---|
| Prompt → working full-stack app | this agent's pipeline | **Integrated** (`generate_website` via MCP, `POST /api/generate`) |
| Chat-based refinement after generation | `agent/iterate_engine.py` | **Integrated** (`POST /api/iterate`) |
| Live preview + deploy | `agent/deploy_engine.py`, `agent/auto_deploy.py` | **Integrated** (GitHub Pages live; Vercel/Netlify/Cloudflare/Render/Railway/DO/AWS recipes) |
| In-browser sandbox (Bolt.new) | [`@webcontainer/api`](https://webcontainers.io/) | **Dependency present** in `package.json` |
| AI code editor (Cursor/Windsurf) | [Cline](https://github.com/cline/cline), [Continue](https://github.com/continuedev/continue), [Void](https://github.com/voideditor/void), [Aider](https://github.com/Aider-AI/aider) | **Not installed** — they consume this repo through `ai-agent/mcp_server.py` instead |
| Visual/drag-drop canvas builder (Lovable, Onlook) | [Onlook](https://github.com/onlook-dev/onlook), Dyad | **Out of scope** (separate app; the pipeline emits real JSX you can open in any editor) |
| Cloud IDE + run (Replit) | VS Code + this repo's `dev:all`, Docker, K8s | **Integrated** |
| Ephemeral cloud sandboxes (E2B/Daytona) | [E2B](https://github.com/e2b-dev/E2B), [Daytona](https://github.com/daytonaio/daytona) | **Not integrated** — see the security note in §3 |

**Bottom line:** you did not need a Lovable alternative added, because you already
own one. What was genuinely missing was *models* — 15 open-weight hosts, of which
GLM (Z.ai) and Qwen3 (Alibaba Model Studio) were the two serious gaps and are now
closed.

---

## 3. Tools that opencode and Codebuff ship — and where this repo stands

opencode (open-source terminal agent) and Codebuff are themselves coding agents.
Their tool surface is a good checklist for what a *general* agent needs:

| Tool surface | opencode | Codebuff | This repo |
|---|---|---|---|
| Run shell commands | `bash` | `run_terminal_command` | **Not exposed over MCP** |
| Read a file | `read` | `read_files` | **`read_file` MCP tool** — read-only, root-confined, secrets refused |
| Exact-string edit | `edit` | `str_replace` | **Not exposed over MCP** |
| Write a whole file | `write` | `write_file` | **Not exposed over MCP** |
| Glob / list dir | `glob`, `list` | `glob`, `list_directory` | **`glob_files` + `list_directory` MCP tools** (root-confined) |
| Content search | `grep` | `code_search` | **`search_code` MCP tool** (regex, root-confined) + internal analyzers (`agent/code_intelligence.py`) |
| Fetch a URL / web search | `webfetch` | `read_url`, `web_search` | `agent/extensions/browser_qa.py` (Playwright) + `agent/reach/*` |
| Todo list / planning | `todowrite` | `write_todos` | `plan_website` (MCP) |
| Sub-agents / fan-out | `task` | — | `map_parallel`, `AgentOrchestrator` workflow agents |
| Pause and ask the user | `question` | `ask_questions` | `chat_with_agent` (MCP) |

`ai-agent/mcp_server.py` exposes 11 tools today: 7 product tools
(`generate_website`, `plan_website`, `get_run`, `list_runs`,
`chat_with_agent`, `registries_summary`, `memory_insights`) plus 4
**read-only repo tools** added 2026-10-06 — `read_file`, `search_code`,
`glob_files`, `list_directory` — closing the read/grep/glob/list half of
the opencode/Codebuff gap.

The repo tools are scoped exactly as the security note below used to
prescribe: every path is resolved against the repository root and rejected
on `..`/symlink escape, secret files (`.env*` except `.env.example` and
friends, keys, certs) are refused, cache/build directories are pruned, and
every call is capped (500 KB per file, 200 results, 3 000 files scanned).
`ai-agent/tests/test_mcp_readonly_tools.py` (35 cases) pins those
properties, including planted-secret search skipping.

`bash` / `write` / `edit` remain **not exposed**: they would make this agent
as capable as opencode at repo work, but they are also remote code execution
on whatever machine runs the MCP server. That is a **security decision, not
a feature decision**, and it has not been reversed.

---

## 4. Test + deployment tooling inventory

### Already present

| Area | Tools |
|---|---|
| Frontend test | Vitest 8, `@vitest/coverage-v8`, Testing Library, MSW |
| Backend test | Jest, Jest jsdom |
| E2E | Playwright (`e2e/` — auth, home, products) |
| A11y | `@axe-core/playwright`, `eslint-plugin-playwright` |
| Python test | pytest 8, pytest-asyncio, pytest-cov (`ai-agent/requirements-dev.txt`) |
| Lint / format | ESLint (flat config), Prettier, Pylint, Black, Bandit, Radon |
| Perf budget | `scripts/check-bundle-budget.mjs` (`npm run size`) |
| Core Web Vitals | **Lighthouse CI**: `@lhci/cli` + `.lighthouserc.json` + `npm run test:perf` (3 runs × 2 URLs, Chromium auto-found from the Playwright cache) |
| Deploy | `Dockerfile.frontend`, `docker-compose*.yml`, 7 K8s manifests, 4 Nginx configs, 6 GitHub Actions workflows, GitHub Pages live deploy |
| Docs | VitePress (`npm run docs:dev` / `docs:build`) |
| Agent bridge | MCP stdio server (`mcp>=1.9.0,<2`) |

### Missing — and worth adding, in order

| Gap | Why it matters | Suggested tool |
|---|---|---|
| **Visual regression** | Part 2 of the master prompt requires it; Playwright screenshots exist but no baseline diffing | Playwright `toHaveScreenshot()` snapshots |
| **Dependency/security gate** | `bandit` and `npm audit` are not wired into a CI workflow step | `pip-audit`, `npm audit --audit-level=high` |
| **Load test** | No throughput/latency check on the API or agent endpoints | k6 or autocannon |
| **Mutation testing** | Coverage is 37.9% backend / very low frontend; mutation testing finds the assertions that do not actually assert | Stryker (JS), mutmut (Python) |

None of these are installed, and none are claimed as working. Two gates are
enforced today: the size budget (`npm run size`) and the Lighthouse assertions
(`npm run test:perf` — **green since the fixes below**, EXIT=0 on 2026-10-06).

### First measured Lighthouse baseline (2026-10-06)

`npm run test:perf` → reports in `.lighthouseci/reports/` (gitignored),
3 runs per URL, mobile emulation with simulated throttling, static
`vite preview` without a backend:

| URL | Performance | LCP | TBT | CLS | Accessibility |
|---|---|---|---|---|---|
| `/` | **0.10–0.12** | 7.0–9.4 s | 11.5–15.9 s | **0.343 — fails the <0.1 hard limit** | 0.98 |
| `/login` | 0.31–0.34 | 5.5–6.1 s | 10.6–13.5 s | 0.06 | 0.95 |

Causes from the report JSON: the Sentry browser SDK v11.4.0 ships as an
eagerly loaded chunk (`esm-*.js`, 149 KB transferred / 115 KB unused),
Google Fonts CSS was render-blocking (~1.8 s wasted), total main-thread
work is 31 s under 4× CPU throttle, and one unattributed 0.343 shift of
the home footer moves the page after first paint. Console errors come from
the absent backend during a static run.

### Fixed the same day — measured again (2026-10-06)

Two root causes were found and fixed; the gate now exits **0**:

1. **Fonts loaded twice** (index.html `<link>` + duplicate `@import` in
   `globals.css`), both `display=swap` — each swap reflowed the page (+90px
   hero growth, probe-measured). Now a single async stylesheet with
   `display=optional`, so a late font can never reflow (render-blocking
   font CSS also gone).
2. **The footer mounted already visible** in a short intermediate React
   commit — proven from the Chrome trace (`old_rect [0,0,0,0] →
   [0,541,412,282]`, distance 6987px). `MainLayout`’s `<main>` now carries
   `min-h-[100svh]`, so the footer can only ever mount below the fold.

Latest autorun (`npm run test:perf`, EXIT=0): `/` **CLS 0.0000 ×3**,
performance 0.27–0.30, LCP 8.3–10.0 s, a11y 0.95; `/login` **CLS 0.0000**
(was 0.056), performance 0.36–0.41. **Performance and LCP still miss the
95+ / 1.5 s targets** — those remain WARN-level and honestly unmet;
TBT (main-thread, Sentry at boot when `VITE_SENTRY_DSN` is set) is the
next lever. Diagnostic tool: `scripts/_cls_probe.cjs`.

---

## 5. What to add next

Done on 2026-10-06: **Lighthouse CI** (measured baseline in §4, CLS
hard-limit failure **fixed the same day** — gate green), the **read-only
repo tools over MCP** (§3), and the **Unique Project Playbook** (Design
group in the docs sidebar). Remaining, in order:

1. **Performance and LCP toward the 95+ / 1.5 s targets** — CLS is now
   0.000 but TBT (Sentry at boot, main-thread work) keeps the score at
   0.27–0.41; measure, then fix (lazy-idle Sentry init is the first lever).
2. **Visual-regression baselines** — required by the master prompt, and the
   screenshots are already being captured.
3. **Dependency/security gate** — wire `pip-audit` + `npm audit --audit-level=high`
   into a CI workflow step.
4. **License gate on the provider table** — refuse a `cohere`-style CC-BY-NC hop
   when the run is for a paid deliverable.
