# LumicorePro Core: Python AI Website Generation Agent

Production-ready, local-first Python AI Website Generation Agent built for **LumicorePro Core**.

The agent analyzes natural language website generation prompts, queries the local reusable library (templates, React components, images, icons, animations, Node.js/Express backend micro-modules, and PostgreSQL database schemas) **first**, and invokes external LLMs (Gemini, DeepSeek, OpenRouter) strictly when required for missing features or custom code logic.

---

## Key Features

- ⚡ **Local-First Assembly Engine**: Prioritizes local component, template, and backend reuse to achieve **~95% token savings** and **<1s generation speeds**.
- 🛡️ **Hardened Security & Path Protection**: Includes path traversal bounds, code injection regex & syntax sanitization, and SQL parameterized query enforcement.
- 🔄 **Multi-Provider Fallback & Retries**: 3-attempt exponential backoff with automatic fallback chain (`Gemini` ➔ `DeepSeek` ➔ `OpenRouter` ➔ `Local Offline Mode`).
- 🗄️ **SQLite WAL Concurrency**: WAL journal mode with lock-retry logic for concurrent database access.
- 📦 **End-to-End Stack Generation**: React.js + Vite + Tailwind CSS frontend, Express.js backend, PostgreSQL database schema.
- 🔍 **Deep Validation & Testing**: Deep validator checking NPM packages, env vars, component props, and SQL foreign keys; comprehensive `pytest` test suite.

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
