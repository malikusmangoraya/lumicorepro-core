# LumicorePro Core: Python AI Website Generation Agent

Production-ready, local-first Python AI Website Generation Agent built for **LumicorePro Core**.

The agent analyzes natural language website generation prompts, queries the local reusable library (templates, React components, images, icons, animations, Node.js/Express backend micro-modules, and PostgreSQL database schemas) **first**, and invokes external LLM APIs strictly when required for missing features or custom code logic.

---

## Key Features

- ⚡ **Local-First Assembly Engine**: Prioritizes local component, template, and backend reuse to achieve **~95% token savings** and **<1s generation speeds**.
- 🛡️ **Hardened Security & Path Protection**: Includes path traversal bounds, code injection regex & syntax sanitization, and SQL parameterized query enforcement.
- 🔄 **Multi-Provider Fallback & Retries**: 24-hop **internet-only** fallback chain with 3-attempt exponential backoff — open-weight clouds first (Groq, Cerebras, Nebius, Hyperbolic, Z.ai GLM, Qwen/DashScope, Together, DeepInfra, Fireworks, SambaNova, Novita, Hugging Face, Featherless, Chutes, MiniMax, Cohere), then native vendors (Gemini, DeepSeek, Claude, OpenAI, OpenRouter, Mistral, Kimi). No local GPU runtime is required or supported; with `AI_OFFLINE=1` the agent still produces a full site from the deterministic local assembler. See [docs/OPENSOURCE_ALTERNATIVES.md](../docs/OPENSOURCE_ALTERNATIVES.md) for the full map, including licence cautions.
- 🗄️ **SQLite WAL Concurrency**: WAL journal mode with lock-retry logic for concurrent database access.
- 📦 **End-to-End Stack Generation**: React.js + Vite + Tailwind CSS frontend, Express.js backend, PostgreSQL database schema.
- 🚀 **Evidence-Gated Delivery**: build → backend tests → browser QA → deploy → live verification → demo video, with `status: delivered` only when every stage produced verifiable evidence (`docs/FACTORY.md`).
- 🎬 **Automated Demo Video**: a ~2-minute narrated tour of the real pages (Playwright capture + TTS + ffmpeg), ffprobe-verified before it is reported as ready.
- 🧭 **Backend Stack Catalog**: Auto-recommended or manually selected Node.js, Python, PHP, Java, Go, C#/.NET, or Ruby frameworks, databases, and advanced architecture options.
- 📦 **Honest Scaffold Reporting**: The current project generator scaffolds Node.js + Express only; other catalog selections are validated and reported but are not represented as generated backend code.
- 🔍 **Deep Validation & Testing**: Deep validator checking NPM packages, env vars, component props, and SQL foreign keys; comprehensive `pytest` test suite.

## Backend Stack Selection

Generation requests may select a backend stack automatically from the prompt or
provide compatible manual choices. The catalog covers:

- **Languages/frameworks**: Node.js (Express, NestJS, Fastify), Python (FastAPI,
  Django, Flask), PHP (Laravel, Symfony, Slim), Java (Spring Boot, Quarkus,
  Micronaut), Go (Gin, Echo, Fiber), C#/.NET (ASP.NET Core), and Ruby (Rails,
  Sinatra).
- **Databases and ORMs**: PostgreSQL, MySQL, MariaDB, SQLite, SQL Server, and
  MongoDB, with framework- and database-compatible ORM choices.
- **Advanced options**: REST/GraphQL/gRPC, modular monolith/microservices/serverless,
  authentication, caching, queues, testing, observability, and deployment targets.

The FastAPI catalog endpoint is `GET /api/technology-catalog`. Include a
`backend_stack` object in a generation request; for example:

```json
{
  "mode": "manual",
  "language": "python",
  "framework": "fastapi",
  "database": "postgresql",
  "api_style": "rest",
  "architecture": "modular-monolith"
}
```

The API validates catalog IDs and framework/database/ORM compatibility before
queueing a generation run. Omitted manual fields can still be recommended from
the prompt. `mode: "auto"` lets the agent choose compatible options.

**Scaffold limitation:** catalog availability is not native code generation.
Only Node.js + Express is currently scaffold-supported. Other languages and
frameworks are reported as catalog selections and do not produce Python, PHP,
Java, Go, .NET, or Ruby backend files. A selected database likewise does not
guarantee a database-specific schema or migrations. Check the generation report's
`backend_stack.scaffold_status` before treating a stack as implemented.

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd ai-agent
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your preferred provider in `.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 3. Initialize SQLite Database

```bash
python database/init_db.py
```

---

## Running the Agent

### Run via Interactive CLI

```bash
python main.py
```

### Run Generation with CLI Flags

```bash
python main.py --prompt "Create a modern electronics e-commerce website with 20 categories..."
```

### Dry-Run Simulation (No Disk Writes)

```bash
python main.py --prompt "Create a modern electronics store" --dry-run
```

### Verbose Debug Logging

```bash
python main.py --prompt "Create a modern electronics store" --verbose
```

### Deliver a Generated Project (build → test → QA → deploy → live verify → video)

**One prompt does the whole job:**

```bash
python main.py --deliver 'Build "CortexDesk" an AI knowledge copilot, deploy to vercel'
```

The agent infers the brand, industry, deploy target (`no deploy`, `railway`, `netlify`,
`github pages`) and video opt-out from the sentence. Generation, tests, QA, deployment,
live verification and the demo video all run from that one command.

```bash
# Full delivery to Vercel (uses the logged-in CLI or VERCEL_TOKEN)
python main.py --factory generated-projects/my-site \
  --factory-name "My Product" --factory-tagline "One-line pitch"

# Build, test, QA and video only — no external deployment
python main.py --factory generated-projects/my-site --factory-deploy none

# Machine-readable evidence (stdout is JSON; logs go to stderr)
python main.py --factory generated-projects/my-site --factory-json

# Verify any live URL without deploying
python main.py --verify-url https://my-site.vercel.app --verify-api /api/v1/health --factory-json
```

Exit code is `0` only when the run is `delivered`. Reports land in
`<project>/.factory/report.json`, `.factory/report.md`, `.factory/deploy-report.json`,
`.factory/demo.mp4` and `.factory/video/manifest.json`. See
[`docs/FACTORY.md`](../docs/FACTORY.md) for the gate definitions, supported platforms
and the HTTP endpoints (`/api/factory/run`, `/api/factory/verify`, `/api/factory/status`).

Requirements for the video stage: `ffmpeg`, `ffprobe`, Node + Playwright, and a TTS
backend — `edge-tts` (best voices), `gTTS` (free, internet-only fallback) or Windows
PowerShell (offline SAPI). Missing tools are reported by `GET /api/factory/status` — the
pipeline never fabricates an artifact.

Designs are brand-derived (`agent/design_forge.py`): four archetypes, a tinted neutral
scale, a two-font pairing and a radius system, so two generated brands never look alike.
Progress is streamed in real time at `GET /api/factory/jobs/{id}/events` (SSE).

### Optional Reflex Mode

Reflex generation is opt-in and does not change the default React/Vite path. Install the generated project's pinned optional dependency, then run the CLI with an explicit framework and valid package name:

```bash
python -m pip install reflex==0.10.0
python main.py --framework reflex --project-name sample_app --dest generated-projects/sample_app
```

The CLI validates that Reflex is importable before writing files. It creates a minimal Python app, `rxconfig.py`, `requirements.txt`, README, and `generation-report.json`; it does not configure auth, databases, payments, deployment, or credentials. The generated README contains the local `reflex init` / `reflex run` commands. The pinned version and runtime behavior should be rechecked against the upstream Reflex release before production use.

---

## Running Test Suite

Run unit and integration tests using `pytest` or `unittest`:

```bash
pytest ai-agent/tests
```

or using standard Python unittest runner:

```bash
python -m unittest discover ai-agent/tests
```

---

## Output Location

Generated projects are created inside `generated-projects/`:

```
generated-projects/
└── electronics-dashboard-001/
    ├── frontend/               # React + Vite Application
    ├── backend/                # Node.js + Express API Server
    ├── database/
    │   └── schema.sql          # Consolidated PostgreSQL Schema
    ├── README.md               # Project Quickstart Guide
    └── generation-report.json  # Comprehensive Generation Metrics & Deep Validation Report
```
