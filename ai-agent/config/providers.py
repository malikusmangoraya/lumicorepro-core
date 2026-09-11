import os
from typing import Dict, Any, List
from .settings import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    GEMINI_MODEL,
    OPENROUTER_MODEL,
    OPENROUTER_MODELS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GROK_API_KEY,
    GROK_MODEL,
)

# ── New provider keys (read from env at import time) ──────────────────────
MISTRAL_API_KEY    = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL      = os.getenv("MISTRAL_MODEL",     "mistral-large-latest")

PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ── Active providers ──────────────────────────────────────────────
    "gemini": {
        "provider_name": "gemini",
        "api_key": GEMINI_API_KEY,
        "model": GEMINI_MODEL,
        "env_var_name": "GEMINI_API_KEY",
        "class_path": "providers.gemini_provider.GeminiProvider",
    },
    "openai": {
        "provider_name": "openai",
        "api_key": OPENAI_API_KEY,
        "model": OPENAI_MODEL,
        "env_var_name": "OPENAI_API_KEY",
        "class_path": "providers.openai_provider.OpenAIProvider",
    },
    "chatgpt": {
        "provider_name": "openai",
        "api_key": OPENAI_API_KEY,
        "model": OPENAI_MODEL,
        "env_var_name": "OPENAI_API_KEY",
        "class_path": "providers.openai_provider.OpenAIProvider",
    },
    "openrouter": {
        "provider_name": "openrouter",
        "api_key": OPENROUTER_API_KEY,
        "model": OPENROUTER_MODEL,
        "models": OPENROUTER_MODELS,
        "env_var_name": "OPENROUTER_API_KEY",
        "class_path": "providers.openrouter_provider.OpenRouterProvider",
    },
    "grok": {
        "provider_name": "grok",
        "api_key": GROK_API_KEY,
        "model": GROK_MODEL,
        "env_var_name": "GROK_API_KEY",
        "class_path": "providers.grok_provider.GrokProvider",
    },
    "mistral": {
        "provider_name": "mistral",
        "api_key": MISTRAL_API_KEY,
        "model": MISTRAL_MODEL,
        "env_var_name": "MISTRAL_API_KEY",
        "class_path": "providers.mistral_provider.MistralProvider",
    },
}

# Priority order: reasoning-tier first when a capable key exists, fast/cheap
# fallback otherwise.
FALLBACK_ORDER: List[str] = [
    "grok",         # primary — Groq Cloud, fast + reliable
    "gemini",       # Google — fast, free tier
    "openai",       # GPT-4/4o — standard
    "mistral",      # cheap, multilingual
    "openrouter",   # aggregator — last resort
]

def get_reasoning_provider() -> Any:
    """Instantiate the reasoning-tier provider for bespoke AI design (Phase 5.5)."""
    from .settings import REASONING_PROVIDER
    name = (os.getenv("REASONING_PROVIDER") or REASONING_PROVIDER or "grok").lower()
    candidates = [name] + [p for p in FALLBACK_ORDER if p != name]
    for p_name in candidates:
        try:
            if validate_provider_key(p_name, require_key=False):
                inst = instantiate_provider(p_name)
                if inst:
                    return inst
        except Exception:
            continue
    return None

def get_active_provider_config(provider_name: str = None) -> Dict[str, Any]:
    """Retrieve configuration for specified or active AI provider."""
    provider = (provider_name or AI_PROVIDER).lower()
    if provider not in PROVIDER_CONFIGS:
        supported = list(PROVIDER_CONFIGS.keys())
        raise ValueError(
            f"Unsupported AI Provider '{provider}'. "
            f"Supported: {supported}"
        )
    return PROVIDER_CONFIGS[provider]


def instantiate_provider(provider_name: str):
    """Dynamically instantiate a provider by name. Returns provider instance or None."""
    try:
        cfg = get_active_provider_config(provider_name)
        p_name = cfg["provider_name"]
        api_key = cfg["api_key"]
        model = cfg["model"]

        if p_name in ("gemini",):
            from providers.gemini_provider import GeminiProvider
            return GeminiProvider(api_key, model)
        elif p_name in ("openai",):
            from providers.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key, model)
        elif p_name in ("openrouter",):
            from providers.openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(api_key, model, model_names=cfg.get("models"))
        elif p_name in ("grok",):
            from providers.grok_provider import GrokProvider
            return GrokProvider(api_key, model)
        elif p_name in ("mistral",):
            from providers.mistral_provider import MistralProvider
            return MistralProvider(api_key, model)
    except Exception:
        return None


def validate_provider_key(provider_name: str = None, require_key: bool = True) -> bool:
    """Validate that required API key is configured for the selected provider."""
    cfg = get_active_provider_config(provider_name)
    key = cfg.get("api_key", "").strip()

    placeholder_keys = {
        "your_gemini_api_key_here",
        "your_openai_api_key_here",
        "your_openrouter_api_key_here",
        "your_mistral_api_key_here",
        "your_grok_api_key_here",
        "",
    }

    # Accept both old (AIza...) and new (AQ.Ab8...) Gemini key formats
    key_valid = key not in placeholder_keys or key.startswith("AQ.")

    if not key_valid:
        if require_key:
            raise ValueError(
                f"\n[CONFIGURATION ERROR] API key for provider '{cfg['provider_name']}' "
                f"is missing or invalid.\n"
                f"Please set '{cfg['env_var_name']}' in your 'ai-agent/.env' file."
            )
        return False
    return True


def get_available_providers() -> List[str]:
    """Return list of providers that have a configured (non-placeholder) API key."""
    available = []
    for name in FALLBACK_ORDER:
        try:
            if validate_provider_key(name, require_key=False):
                available.append(name)
        except Exception:
            pass
    return available
