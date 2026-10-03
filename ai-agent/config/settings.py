import os
from pathlib import Path
from typing import Mapping, Optional

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Base Paths (Normalizing workspace root path)
AI_AGENT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AI_AGENT_DIR.parent.resolve()


def resolve_generated_projects_dir(
    project_root: Path,
    environ: Optional[Mapping[str, str]] = None,
) -> Path:
    """Resolve the project-output root, allowing isolated batch generations."""
    environment = os.environ if environ is None else environ
    configured = environment.get("GENERATED_PROJECTS_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (project_root / "generated-projects").resolve()

# ── Agent Reach (open-source decentralized search routing CLI) ───────────────
AGENT_REACH_ENV = os.getenv("AGENT_REACH_ENV", "auto").strip().lower()
AGENT_REACH_HOME = Path(os.getenv("AGENT_REACH_HOME", "") or (Path.home() / ".agent-reach")).resolve()
AGENT_REACH_VERIFY_CMD = "agent-reach install --env=auto"
AGENT_REACH_DOCTOR_TIMEOUT = int(os.getenv("AGENT_REACH_DOCTOR_TIMEOUT", "30"))
AGENT_REACH_SEARCH_TIMEOUT = int(os.getenv("AGENT_REACH_SEARCH_TIMEOUT", "45"))
AGENT_REACH_SKILL_DIRS = [
    (PROJECT_ROOT / ".cursor" / "skills" / "agent-reach").resolve(),
    (Path.home() / ".cursor" / "skills" / "agent-reach").resolve(),
    (Path.home() / ".openclaw" / "skills" / "agent-reach").resolve(),
]

# Specific Directories
REGISTRY_DIR = (PROJECT_ROOT / "registry").resolve()
GENERATED_PROJECTS_DIR = resolve_generated_projects_dir(PROJECT_ROOT)
TEMPLATES_DIR = (PROJECT_ROOT / "src" / "templates").resolve()
COMPONENTS_DIR = (PROJECT_ROOT / "src" / "components").resolve()
BACKEND_LIBRARY_DIR = (PROJECT_ROOT / "backend-library").resolve()
DATABASE_SCHEMAS_DIR = (PROJECT_ROOT / "database" / "schemas").resolve()
ASSETS_DIR = (PROJECT_ROOT / "src" / "assets").resolve()
ICONS_DIR = (PROJECT_ROOT / "src" / "icons").resolve()
STYLES_DIR = (PROJECT_ROOT / "src" / "styles").resolve()

# Database & Memory
AGENT_DB_PATH = (AI_AGENT_DIR / "database" / "agent.db").resolve()

# AI Configuration
AI_PROVIDER = os.getenv("ACTIVE_AI_PROVIDER", os.getenv("AI_PROVIDER", "grok")).lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.8-27b:free")

# ── OpenRouter free-tier models, priority-ordered (fast + reasoning first) ──
# Live-verified against GET /api/v1/models (2026-09-24): gemma-4-31b-it:free
# dropped off $0 pricing (returned 404) so it was removed; qwen3.8-27b:free
# (multimodal vision + tools) became default and cohere/north-mini-code:free
# verified working live. Rotation: on failure the provider falls through to
# the next model. Auto-router last-ish as catchall.
OPENROUTER_MODELS = [
    "qwen/qwen3.8-27b:free",                                    # multimodal vision-language 27B + tools
    "cohere/north-mini-code:free",                              # agentic code (live-verified OK)
    "nvidia/nemotron-3-super-120b-a12b:free",                   # reasoning 120B
    "nvidia/nemotron-3-ultra-550b-a55b:free",                   # reasoning 550B
    "nex-agi/nex-n2.5-pro:free",                                # agentic coding
    "thinkingmachines/inkling:free",                            # deep reasoning 1M ctx
    "thinkingmachines/inkling-small:free",                      # fast multimodal reasoner
    "nvidia/nemotron-3.5-lightning:free",                       # 1M ctx fast gen
    "poolside/laguna-s-2.1:free",                               # code
    "poolside/laguna-xs-2.1:free",                              # code, small fast
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",       # perception + reasoning
    "nex-agi/nex-n2.5-mini:free",                               # mini fast
    "liquid/lfm-2.5-2.6b:free",                                 # tiny fast
    "dots-studio/dots-3-note-preview:free",                     # notes 512K
    "inclusionai/ling-3.0-flash-fin:free",                      # finance MoE
    "inclusionai/ling-3.0-flash-sante:free",                    # health MoE
    "z-ai/glm-5.2:free",                                        # reasoning (no tools)
    "nvidia/nemotron-3.5-content-safety:free",                  # safety filter
    "openrouter/free",                                          # auto-router catchall
]

ALLOW_AI_FALLBACK = os.getenv("ALLOW_AI_FALLBACK", "true").lower() == "true"

# ── Bespoke Design / Reasoning Intelligence (Phase 5.5) ──────────────────
REASONING_PROVIDER = os.getenv("REASONING_PROVIDER", "grok").lower()
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "openrouter").lower()
VISION_MODEL = os.getenv("VISION_MODEL", "qwen/qwen3.8-27b:free")
VISION_MODEL_IMAGE: str = os.getenv("VISION_MODEL_IMAGE", "qwen/qwen3.8-27b:free")

# Smart context injection limits (expandable AST context, not the old 3-file cap)
AI_MAX_CONTEXT_FILES = int(os.getenv("AI_MAX_CONTEXT_FILES", "40"))
AI_MAX_PATCH_FILES = int(os.getenv("AI_MAX_PATCH_FILES", "25"))
AI_STRUCTURE_CONTEXT_CHARS = int(os.getenv("AI_STRUCTURE_CONTEXT_CHARS", "12000"))

# ── VFS / Diff patching (Feature: 50+ file patches via one unified diff) ──
AI_DIFF_PATCHING = os.getenv("AI_DIFF_PATCHING", "1") in ("1", "true", "yes")

# ── Self-correction loop (compiler feedback → AI diff fix → rebuild) ──────
SELF_CORRECT_ENABLED = os.getenv("SELF_CORRECT_ENABLED", "1") in ("1", "true", "yes")
SELF_CORRECT_MAX_ROUNDS = int(os.getenv("SELF_CORRECT_MAX_ROUNDS", "3"))

# ── Offline Public-Development Benchmark (real bug-fixing tasks) ─────────────
# Corpus bundle root: tasks.jsonl + snapshots/*.tgz + graphs/ + embeddings/ +
# wheels/*.whl + HARNESS_README. Nothing here is fetched at runtime — the whole
# benchmark runs offline. `python -m agent.benchmarks doctor` verifies it.
BENCH_DATA_DIR = Path(os.getenv("BENCH_DATA_DIR", "") or (PROJECT_ROOT / "benchmarks-data")).resolve()
BENCH_WORKSPACES_DIR = Path(
    os.getenv("BENCH_WORKSPACES_DIR", "") or (GENERATED_PROJECTS_DIR / ".bench" / "workspaces")
).resolve()
BENCH_REPORT_DIR = Path(
    os.getenv("BENCH_REPORT_DIR", "") or (GENERATED_PROJECTS_DIR / "bench-out")
).resolve()
BENCH_JOBS = max(1, int(os.getenv("BENCH_JOBS", "1")))
BENCH_PYTEST_TIMEOUT_SECS = max(30, int(os.getenv("BENCH_PYTEST_TIMEOUT_SECS", "300")))
BENCH_MAX_CONTEXT_CHARS = max(2000, int(os.getenv("BENCH_MAX_CONTEXT_CHARS", "24000")))
BENCH_KEEP_WORKSPACES = os.getenv("BENCH_KEEP_WORKSPACES", "false").lower() in ("1", "true", "yes")

# ── Mistral ────────────────────────────────────────────────────────────────
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# ── Moonshot AI / Kimi (open-weight K2 family) ────────────────────────────
# KIMI_API_KEY (MOONSHOT_API_KEY accepted as an alias). KIMI_BASE_URL may point
# at a self-hosted vLLM/SGLang build of the open K2 weights — the compliant
# option when the hosted endpoint's China-side processing is not acceptable.
KIMI_API_KEY  = os.getenv("KIMI_API_KEY", "") or os.getenv("MOONSHOT_API_KEY", "")
KIMI_MODEL    = os.getenv("KIMI_MODEL", "kimi-k2.7-code")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")

# ── OpenMuse / local open-weight server (keyless) ─────────────────────────
# OpenMuse (MIT, CopilotKit) is a self-hosted Meta-Muse-style agent that brings
# its own model, so this targets any OpenAI-compatible endpoint: the OpenMuse
# gateway, Ollama (:11434), vLLM/SGLang (:8000), llama.cpp (:8080), LM Studio
# (:1234). All variables optional.
OPENMUSE_API_KEY  = os.getenv("OPENMUSE_API_KEY", "")
OPENMUSE_MODEL    = os.getenv("OPENMUSE_MODEL", "qwen3-coder")
OPENMUSE_BASE_URL = os.getenv("OPENMUSE_BASE_URL", "http://127.0.0.1:8080/v1")

# ── OpenAI ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")

# ── xAI Grok / Groq Cloud ───────────────────────────────────────────────
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL   = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-3.2-11b-vision-preview")

# ── OmniRoute AI Gateway (keyless local install supported) ─────────────
# One OpenAI-compatible endpoint that routes 'auto' to the fastest available
# backend first and auto-fallbacks across 350+ providers (150+ free tiers).
# Install: npm i -g omniroute  →  then run: omniroute  (boots on :20128)
OMNIROUTE_API_KEY   = os.getenv("OMNIROUTE_API_KEY", "")
OMNIROUTE_MODEL     = os.getenv("OMNIROUTE_MODEL", "auto")
OMNIROUTE_BASE_URL  = os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")

# ── 9Router AI Gateway (free router + token saver, boots on :20128) ────
# Dashboard http://localhost:20128 → Providers → connect a FREE provider
# (Kiro AI / OpenCode Free) → Dashboard → API Keys → copy key → set
# NINEROUTER_API_KEY. Auto-falls back to free tiers, round-robins accounts,
# RTK compresses tool output (saves 20-40% tokens). OpenAI-compatible /v1.
# Model id format: <provider-prefix>/<model> (e.g. kr/claude-sonnet-4.5).
NINEROUTER_API_KEY   = os.getenv("NINEROUTER_API_KEY", "")
NINEROUTER_MODEL     = os.getenv("NINEROUTER_MODEL", "kr/claude-sonnet-4.5")
NINEROUTER_BASE_URL  = os.getenv("NINEROUTER_BASE_URL", "http://127.0.0.1:20128/v1")
