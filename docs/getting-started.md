# Getting Started

> Complete step-by-step guide to set up and run LumicorePro Core.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Node.js** | 18+ | 20+ |
| **npm** | 9+ | 10+ |
| **Python** | 3.9+ | 3.12+ |
| **pip** | 21+ | 24+ |
| **Python venv** | Required | — |
| **PostgreSQL** | 14+ (for generated projects) | 16+ |
| **Disk Space** | 2 GB | 5 GB+ |

### Linux/macOS (Pip/Venv)

```bash
python3 -m venv venv && source venv/bin/activate
```

## Clone & Install

### Step 1: Clone Repository

```bash
git clone <repo-url>
cd lumicorepro-core
```

### Step 2: Install Frontend Dependencies

```bash
npm install
```

### Step 3: Install Python Dependencies

#### Windows (Pip/venv)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r ai-agent\requirements.txt
```

#### Linux/macOS (Pip/venv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r ai-agent/requirements.txt
```

## Configure AI Providers

LumicorePro supports 3 AI providers (all optional — the system works **offline** without them).

### Provider 1: Google Gemini (Recommended)

```bash
# Get API key from: https://aistudio.google.com/apikey
# Edit ai-agent/.env:
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_key
GEMINI_MODEL=gemini-2.5-flash
```

### Provider 2: DeepSeek (Alternative)

```bash
# Get API key from: https://platform.deepseek.com
# Edit ai-agent/.env:
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_actual_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
```

### Provider 3: OpenRouter

```bash
# Get API key from: https://openrouter.ai/keys
# Edit ai-agent/.env:
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_actual_openrouter_key
OPENROUTER_MODEL=deepseek/deepseek-chat
```

### No AI Provider? (Offline Mode)

Leave `AI_PROVIDER=default` and the system runs offline using local rule-based analysis. You get ~85% of full AI capabilities with zero cost.

### Verify AI Provider

```bash
# Test Gemini:
python -c "from ai-agent.providers.gemini_provider import GeminiProvider; p = GeminiProvider('your_key'); print(p._call_api('Hello, respond with just OK.'))"

# Test DeepSeek:
python -c "from ai-agent.providers.deepseek_provider import DeepSeekProvider; p = DeepSeekProvider('your_key'); print(p._call_api('Hello, respond with just OK.'))"
```

If you see `OK.`, your provider is working.

## Verify Installation

Run through this checklist:

### Check 1: Python environment

```bash
python ai-agent/database/init_db.py
```

### Check 2: Frontend build

```bash
npm run build
```

Output should show a `dist/` folder created.

## Run Your First Generation

### Method 1: Command Line

```bash
cd ai-agent
python main.py --prompt "Build me a premium electronics e-commerce store with product catalog, shopping cart, and review system." --provider gemini
```

### Method 2: Interactive Menu

```bash
cd ai-agent
python main.py
```

### Method 3: Dry-Run (Plan Only)

```bash
cd ai-agent
python main.py --dry-run --prompt "Build me a SaaS dashboard with analytics"
```

### Expected Output

```
[SUCCESS]
  Project built:  generated-projects/{project-name}/
```

## Running the Core Demo

```bash
npm run dev                     # Frontend (5173)
npm run dev:full                # Frontend + Backend
npm run dev:all                 # Frontend + Backend + AI Agent
npm run test                    # Vitest unit tests
npm run test:backend            # Jest backend tests
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'google.genai'"

```bash
pip install -r ai-agent/requirements.txt
```

## Next Steps

- [API Reference](/api-reference) — Explore REST endpoints
- [Deployment Guide](/deployment) — Production deployment options
- See `docs/` folder for: `MASTER_AGENT_PROMPT_v3.md`, `SECURITY_AUDIT.md`, and `LUMICOREPRO_IMPROVEMENTS_ROADMAP.md`