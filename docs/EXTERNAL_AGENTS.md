# External Open-Source Coding Bridge

LumicorePro can delegate tasks to the two strongest open-source coding agents.
Both CLIs are optional and free; every bridge degrades gracefully and reports
what it actually verified instead of assuming a binary works.

| Tool | Source | License | Status (2026-11-04) |
|------|--------|---------|---------------------|
| **opencode** | github.com/anomalyco/opencode | MIT | working - `opencode v2.1.3`, headless via `run --standalone --auto` |
| **freebuff** | github.com/CodebuffAI/freebuff | Apache-2.0 | installed - `0.2.34`; terminal UI only (`login`/`--continue`/`--cwd`/`--trust-agents`, no prompt or `--print`), so the bridge answers `unsupported` (HTTP 501) |
| **market audit** | repo-local Playwright + `ai-agent/utils/market_audit.cjs` | repo | working - live, keyless, no external APIs |

## Capabilities

Both bridges execute the external agent inside the generated project's
directory and return structured results. Only an argv list is passed to the
subprocess (no shell), with a hard timeout and an output tail - the calls are
injection-safe.

Additional hardening (2026-11-04):

- `stdin` is `DEVNULL`, so a CLI can never block waiting for a terminal.
- `project_dir` must be an existing directory. An invalid path is refused; the
  bridge never falls back to LumicorePro's own working directory.
- `tool_status()` caches its probes for 60 s; the status endpoint spawns no
  processes on repeat calls.
- The FastAPI endpoints are declared `def`, not `async def`: FastAPI runs them
  in its worker threadpool, so a multi-minute agent run cannot block the event
  loop.
- opencode runs with `--standalone`, a private server per run. The shared
  background service keeps a detached child alive that inherits the stdout
  pipe, which makes a finished CLI look hung until the timeout.
- A Bun segfault (`panic(main thread): Segmentation fault`) is classified as
  `runtime_crash` instead of a generic non-zero exit.

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
| `agent/external_agents.py :: tool_status()` | `GET /api/external-agents/status` | `installed`, `path`, `headless`, `version`, `version_ok`, `probe_error` per CLI; 60 s cache |
| `run_opencode()` | `POST /api/external-agents/opencode` | runs `opencode run <task> --format {default,json} --auto --standalone` within the project |
| `run_freebuff()` | `POST /api/external-agents/freebuff` | returns `unsupported` (501) when the installed CLI has no headless flag; `interactive=True` is the explicit opt-in |

## Status response

```json
{
  "success": true,
  "data": {
    "opencode": {
      "installed": true,
      "path": "D:\\agent-tools\\npm-global\\opencode.CMD",
      "headless": true,
      "version": "opencode v2.1.3",
      "version_ok": true
    },
    "freebuff": {
      "installed": true,
      "path": "C:\\Users\\<user>\\.config\\manicode\\freebuff.exe",
      "headless": false,
      "version": "0.2.34",
      "version_ok": true,
      "headless_reason": "CLI is a terminal UI; --help advertises no --print/--non-interactive/--headless flag"
    }
  }
}
```

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

### Binary overrides

Both resolvers accept an environment override, useful when a CLI lives outside
`PATH`:

| Variable | Default resolution |
|----------|--------------------|
| `OPENCODE_BIN` | `opencode` on `PATH` (`.cmd`/`.exe`/`.ps1` accepted) |
| `FREEBUFF_BIN` | `~/.config/manicode/freebuff[.exe]`, then `freebuff` on `PATH` |

The freebuff resolver prefers the cached runtime over the npm shim: the shim
re-checks `codebuff.com` on every invocation, which is slow and fails offline.

## Freebuff: why `unsupported`

The launcher-installed `freebuff` `0.2.34` exposes only a `login` command plus
`--continue`, `--cwd` and `--trust-agents`; there is no one-shot prompt and no
`--print` / `--non-interactive` mode. The standalone `codecane` release build
(`1.0.420-beta.185`) does accept a prompt, but launching it without a TTY
starts the terminal UI and exits with a Bun segfault
(`panic(main thread): Segmentation fault`). Reporting `unsupported` is the
honest outcome - starting a TUI inside an API worker would block until the
timeout and then fail anyway.

When a release advertises a headless flag, `tool_status()` flips `headless` to
`true` automatically and `run_freebuff()` starts using it with no code change.
Until then, run freebuff in a real terminal for interactive work; LumicorePro's
own generation, verification and repair engines remain the unattended path.

## Performance notes

- opencode keeps session state on the machine - reruns are warm, not cold.
- `--standalone` trades a little startup time for isolation and a reliable exit.
- freebuff offers free limited-access models paid for via text ads; the CLI
  downloads its engine binary on first run from `codebuff.com`.
- If either CLI is missing, status is `not_available` with HTTP 503 - the
  pipeline's own generation/verify path is never at risk.
- Every bridge call has a hard timeout (`30..7200 s`, default `1800`).

*Created 2026-10-22: bridge module + 3 endpoints (status / opencode / freebuff).*
*Updated 2026-11-04: threadpool endpoints, stdin closed, project-dir validation,
60 s status cache, `--standalone`, freebuff TUI-only detection + `unsupported`.*
