import os
from pathlib import Path

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
GENERATED_PROJECTS_DIR = (PROJECT_ROOT / "generated-projects").resolve()
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
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

# ── OpenRouter free-tier models, priority-ordered (fast + reasoning first) ──
# All 22 are $0 on OpenRouter (verified 2026-09-11). Rotation: on failure the
# provider falls through to the next model. Auto-router last-ish as catchall.
OPENROUTER_MODELS = [
    "google/gemma-4-31b-it:free",                          # #1 fast gen (bench 2.7s)
    "nvidia/nemotron-3-super-120b-a12b:free",              # reasoning 120B
    "nvidia/nemotron-3-ultra-550b-a55b:free",              # reasoning 550B
    "nex-agi/nex-n2.5-pro:free",                           # reasoning
    "thinkingmachines/inkling-small:free",                 # fast reasoner
    "thinkingmachines/inkling:free",                       # deep reasoning 1M ctx
    "openrouter/free",                                     # auto-router catchall
    "google/gemma-4-26b-a4b-it:free",                      # fast MoE 26B
    "nvidia/nemotron-3.5-lightning:free",                  # lite/fast
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",  # small reasoning
    "cohere/north-mini-code:free",                         # code
    "poolside/laguna-s-2.1:free",                          # code
    "poolside/laguna-xs-2.1:free",                         # code, small fast
    "liquid/lfm-2.5-2.6b:free",                            # tiny fast
    "nex-agi/nex-n2.5-mini:free",                          # mini fast
    "dots-studio/dots-3-note-preview:free",                # notes
    "inclusionai/ling-3.0-flash-vl:free",                  # vision
    "inclusionai/ling-3.0-flash-fin:free",                 # finnish
    "inclusionai/ling-3.0-flash-sante:free",               # niche lang
    "google/lyria-3-clip-preview",                         # music
    "google/lyria-3-pro-preview",                          # music
    "nvidia/nemotron-3.5-content-safety:free",             # safety filter
]

ALLOW_AI_FALLBACK = os.getenv("ALLOW_AI_FALLBACK", "true").lower() == "true"

# ── Bespoke Design / Reasoning Intelligence (Phase 5.5) ──────────────────
REASONING_PROVIDER = os.getenv("REASONING_PROVIDER", "grok").lower()
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "openrouter").lower()
VISION_MODEL = os.getenv("VISION_MODEL", "google/gemma-4-31b-it:free")
VISION_MODEL_IMAGE: str = os.getenv("VISION_MODEL_IMAGE", "google/gemma-4-31b-it:free")

# Smart context injection limits (expandable AST context, not the old 3-file cap)
AI_MAX_CONTEXT_FILES = int(os.getenv("AI_MAX_CONTEXT_FILES", "40"))
AI_MAX_PATCH_FILES = int(os.getenv("AI_MAX_PATCH_FILES", "25"))
AI_STRUCTURE_CONTEXT_CHARS = int(os.getenv("AI_STRUCTURE_CONTEXT_CHARS", "12000"))

# ── VFS / Diff patching (Feature: 50+ file patches via one unified diff) ──
AI_DIFF_PATCHING = os.getenv("AI_DIFF_PATCHING", "1") in ("1", "true", "yes")

# ── Self-correction loop (compiler feedback → AI diff fix → rebuild) ──────
SELF_CORRECT_ENABLED = os.getenv("SELF_CORRECT_ENABLED", "1") in ("1", "true", "yes")
SELF_CORRECT_MAX_ROUNDS = int(os.getenv("SELF_CORRECT_MAX_ROUNDS", "3"))

# ── Mistral ────────────────────────────────────────────────────────────────
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# ── OpenAI ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")

# ── xAI Grok / Groq Cloud ───────────────────────────────────────────────
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL   = os.getenv("GROK_MODEL", "qwen/qwen3.6-27b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-3.2-11b-vision-preview")
