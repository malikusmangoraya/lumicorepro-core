# External Open-Source Coding Bridge

LumicorePro can delegate tasks to the two strongest open-source coding agents.
Both CLIs are optional and free; every bridge degrades gracefully.

| Tool | Source | License | Status (2026-10-22) |
|------|--------|---------|---------------------|
| **opencode** | github.com/anomalyco/opencode | MIT | working (`opencode v2.1.3`) |
| **freebuff** | github.com/CodebuffAI/freebuff | Apache-2.0 | npm shim installed; the codebuff.com release host was unreachable at install time - binary downloads lazily on first successful run |
| **market audit** | repo-local Playwright + `ai-agent/utils/market_audit.cjs` | repo | working - live, keyless, no external APIs |

## Capabilities

Both bridges execute the external agent inside the generated project's
directory and return structured results. Only an argv list is passed to the
subprocess (no shell), with a hard timeout and an output tail - the calls are
injection-safe and never able to hang the FastAPI event loop.

### Global Market Audit (`agent/market_audit.py`)

Playwright-driven audit of any live URL against international-market
standards, scored to the design-gate scale (STANDARD 80 / PREMIUM 88 /
SIGNATURE 92):

| Category | Weight | Checks |
|----------|--------|--------|
| Performance | 30% | LCP (1.5s target / 2.5s hard), CLS, TTFB, transfer bytes, console/page errors - desktop 1440x900 + mobile 390x844 |
| SEO | 25% | title/description lengths, canonical, OG, twitter card, JSON-LD, robots.txt, sitemap.xml, h1 |
| International | 20% | `lang`/`dir` attrs, hreflang alternates, currency signals + switcher, no placeholder copy |
| Legal / trust | 15% | Privacy, Terms, Refund/Returns, cookie/GDPR consent surface |
| Conversion | 10% | above-the-fold CTA, labeled inputs, image alt, heading hierarchy |

Endpoint: `POST /api/market-audit` - `{"url": "https://..."}` → graded HTML-ready JSON report the orchestrator can write into the delivery package.

| Function (internal) | Endpoint | Notes |
|---------------------|----------|-------|
| `agent/external_agents.py :: tool_status()` | `GET /api/external-agents/status` | presence + version + probe error per CLI |
| `run_opencode()` | `POST /api/external-agents/opencode` | runs `opencode run <task> --format {default,json} --auto` within the project |
| `run_freebuff()` | `POST /api/external-agents/freebuff` | task is passed to `freebuff <task>` (attach `extra_args` for flags) |

## Usage (examples)

```bash
curl http://localhost:8000/api/external-agents/status \
  -H "Authorization: Bearer $AGENT_API_KEY"

curl http://localhost:8000/api/external-agents/opencode \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task":"Add jest coverage for the credits route", "project_dir":"generated-projects/blogforge", "model":"anthropic/claude-3-sonnet"}'
```

> All `/api/external-agents/*` endpoints require the agent API key.

## Performance notes

- opencode keeps session state on the machine - reruns are warm, not cold.
- freebuff offers free limited-access models paid for via text ads; the CLI
  downloads its engine binary on first run from `codebuff.com`.
- If either CLI is missing, status is `not_available` with HTTP 503 - the
  pipeline's own generation/verify path is never at risk.

*Created 2026-10-22: bridge module + 3 endpoints (status / opencode / freebuff).*
