import os
from typing import Any, Callable, Dict, List
from utils.logger import agent_logger
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
    OMNIROUTE_API_KEY,
    OMNIROUTE_MODEL,
    NINEROUTER_API_KEY,
    NINEROUTER_MODEL,
)

FREELLMAPI_API_KEY = os.getenv("FREELLMAPI_API_KEY", "")
FREELLMAPI_MODEL = os.getenv("FREELLMAPI_MODEL", "auto")
FREELLMAPI_BASE_URL = os.getenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:3001/v1")

# ── New provider keys (read from env at import time) ──────────────────────
MISTRAL_API_KEY    = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL      = os.getenv("MISTRAL_MODEL",     "mistral-large-latest")

# Anthropic Claude — Messages API (ANTHROPIC_API_KEY, CLAUDE_API_KEY accepted as alias)
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
ANTHROPIC_MODEL    = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# DeepSeek — OpenAI-compatible REST
DEEPSEEK_API_KEY   = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL     = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# NVIDIA NIM Free Tier — free cloud API, no credit card required
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL   = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4.1-flash")

# ── $0-tariff vendors ─────────────────────────────────────────────────────
#: Vendors whose API can serve this agent without spend, with the reason it is
#: free. A batch lane that must not incur cost (the free-only rebuild) validates
#: against this table instead of re-declaring the set, so "which vendors are
#: free" has exactly one owner: this file.
FREE_TIER_PROVIDERS: Dict[str, str] = {
    "openrouter": "rotation across OpenRouter ':free' models",
    "gemini": "Google AI Studio free tier",
    "nvidia": "NVIDIA NIM free developer credits",
}

# Moonshot AI (Kimi) — OpenAI-compatible. KIMI_API_KEY, or MOONSHOT_API_KEY.
KIMI_API_KEY  = os.getenv("KIMI_API_KEY", "") or os.getenv("MOONSHOT_API_KEY", "")
KIMI_MODEL    = os.getenv("KIMI_MODEL",   "kimi-k2.7-code")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "")

# OpenCode — MIT-licensed open-source coding agent CLI (the free, open-source
# Claude Code alternative: https://github.com/sst/opencode). Local CLI adapter,
# so there is no API key here: OpenCode holds its own provider credentials.
OPENCODE_BIN   = os.getenv("OPENCODE_BIN", "opencode")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "")

# ── Internet-only open-weight cloud inference ─────────────────────────────
# Open models (Llama, Qwen, DeepSeek, GLM, Mistral, gpt-oss) served over a
# cloud HTTP API. There is deliberately no local/offline path here: an offline
# runtime needs a GPU on the operator's machine, which is out of scope. Keys,
# base URLs and model candidates all come from providers/openweight_provider.py
# so a vendor is a data change, not a new file.
from providers.openweight_provider import (
    OPENWEIGHT_VENDORS,
    vendor_api_key,
    vendor_base_url,
    vendor_models,
)

PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ── Active providers ──────────────────────────────────────────────
    "omniroute": {
        "provider_name": "omniroute",
        "api_key": OMNIROUTE_API_KEY,
        "model": OMNIROUTE_MODEL,
        "env_var_name": "OMNIROUTE_API_KEY",
        "class_path": "providers.omniroute_provider.OmnirouteProvider",
        "keyless": True,  # local gateway works without any API key; key optional
    },
    "ninerouter": {
        "provider_name": "ninerouter",
        "api_key": NINEROUTER_API_KEY,
        "model": NINEROUTER_MODEL,
        "env_var_name": "NINEROUTER_API_KEY",
        "class_path": "providers.ninerouter_provider.NinerouterProvider",
        "keyless": True,  # local gateway; requires connected provider + DSL key to reply
    },
    "freellmapi": {
        "provider_name": "freellmapi",
        "api_key": FREELLMAPI_API_KEY,
        "model": FREELLMAPI_MODEL,
        "base_url": FREELLMAPI_BASE_URL,
        "env_var_name": "FREELLMAPI_API_KEY",
        "class_path": "providers.freellmapi_provider.FreeLLMAPIProvider",
        "keyless": True,  # local router API key is optional; upstream provider keys may still be required
        "open_source": True,
        "dynamic_env": True,
    },
    "opencode": {
        "provider_name": "opencode",
        "api_key": "",
        "model": OPENCODE_MODEL,
        "env_var_name": "OPENCODE_BIN",
        "class_path": "providers.opencode_provider.OpenCodeProvider",
        "keyless": True,  # local CLI agent; OpenCode carries its own credentials
        "open_source": True,
    },
    "gemini": {
        "provider_name": "gemini",
        "api_key": GEMINI_API_KEY,
        "model": GEMINI_MODEL,
        "env_var_name": "GEMINI_API_KEY",
        "class_path": "providers.gemini_provider.GeminiProvider",
    },
    "pollinations": {
        "provider_name": "pollinations",
        "api_key": "",
        "model": os.getenv("POLLINATIONS_TEXT_MODEL", "openai-fast"),
        "env_var_name": "POLLINATIONS_API_KEY",
        "class_path": "providers.pollinations_provider.PollinationsProvider",
        "keyless": True,  # text + image generation over the internet, no key ever
        "docs": "https://github.com/pollinations/pollinations (MIT-ish; community free tier)",
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
    # Groq Cloud serves open models. The historical slug is `grok` (the class
    # hits api.groq.com); `groq` is accepted as the natural spelling.
    "grok": {
        "provider_name": "grok",
        "api_key": GROK_API_KEY,
        "model": GROK_MODEL,
        "env_var_name": "GROK_API_KEY",
        "class_path": "providers.grok_provider.GrokProvider",
        "open_source": True,
    },
    "groq": {
        "provider_name": "grok",  # alias of `grok` -> Groq Cloud
        "api_key": GROK_API_KEY,
        "model": GROK_MODEL,
        "env_var_name": "GROK_API_KEY",
        "class_path": "providers.grok_provider.GrokProvider",
        "open_source": True,
    },
    "mistral": {
        "provider_name": "mistral",
        "api_key": MISTRAL_API_KEY,
        "model": MISTRAL_MODEL,
        "env_var_name": "MISTRAL_API_KEY",
        "class_path": "providers.mistral_provider.MistralProvider",
    },
    "deepseek": {
        "provider_name": "deepseek",
        "api_key": DEEPSEEK_API_KEY,
        "model": DEEPSEEK_MODEL,
        "env_var_name": "DEEPSEEK_API_KEY",
        "class_path": "providers.deepseek_provider.DeepSeekProvider",
    },
    "claude": {
        "provider_name": "claude",
        "api_key": ANTHROPIC_API_KEY,
        "model": ANTHROPIC_MODEL,
        "env_var_name": "ANTHROPIC_API_KEY",
        "class_path": "providers.claude_provider.ClaudeProvider",
    },
    "anthropic": {
        "provider_name": "claude",  # alias of `claude`
        "api_key": ANTHROPIC_API_KEY,
        "model": ANTHROPIC_MODEL,
        "env_var_name": "ANTHROPIC_API_KEY",
        "class_path": "providers.claude_provider.ClaudeProvider",
    },
    "kimi": {
        "provider_name": "kimi",
        "api_key": KIMI_API_KEY,
        "model": KIMI_MODEL,
        "base_url": KIMI_BASE_URL,
        "env_var_name": "KIMI_API_KEY",
        "class_path": "providers.kimi_provider.KimiProvider",
        "open_source": True,  # K2 family weights are published; KIMI_BASE_URL may self-host
    },
    "moonshot": {
        "provider_name": "kimi",
        "api_key": KIMI_API_KEY,
        "model": KIMI_MODEL,
        "base_url": KIMI_BASE_URL,
        "env_var_name": "KIMI_API_KEY",
        "class_path": "providers.kimi_provider.KimiProvider",
        "open_source": True,
    },
    "nvidia": {
        "provider_name": "nvidia",
        "api_key": NVIDIA_API_KEY,
        "model": NVIDIA_MODEL,
        "env_var_name": "NVIDIA_API_KEY",
        "class_path": "providers.nvidia_provider.NvidiaProvider",
    },
}

# Priority order: OmniRoute gateway first — its 'auto' model internally routes
# to the FASTEST available model, compresses tokens, and auto-fallbacks across
# 350+ providers (150+ free tiers) inside ONE call chain. Native providers
# below stay as offline fallbacks if the gateway is unreachable.
#
# INVARIANT: every name listed here must have a builder in `_PROVIDER_BUILDERS`
# (see `instantiate_provider`). A name without a constructor silently loses its
# hop while `/api/providers` still advertises it — `test_provider_wiring.py`
# is the regression guard for exactly that bug (nvidia was listed first and
# returned None).
FALLBACK_ORDER: List[str] = [
    "nvidia",       # NVIDIA NIM free tier — DeepSeek V4.1 Flash, GLM 5.3, Kimi K3 (free, no credit card)
    "cerebras",     # open-weight cloud — fastest time-to-first-token
    "groq",         # Groq Cloud — LPU, open models
    "nebius",       # open-weight cloud — fast + cheap (Token Factory)
    "hyperbolic",   # open-weight cloud — open-access GPU cloud
    "zai",          # open-weight cloud — GLM (MIT for the 4.5 family)
    "dashscope",    # open-weight cloud — Qwen3 (Apache-2.0), Alibaba Model Studio
    "together",     # open-weight cloud — 200+ open models
    "deepinfra",    # open-weight cloud — cheapest per token
    "fireworks",    # open-weight cloud — high throughput
    "sambanova",    # open-weight cloud — dataflow hardware
    "novita",       # open-weight cloud — low-cost
    "huggingface",  # HF Inference Providers router — one key, many backends
    "featherless",  # open-weight cloud — largest catalogue, no cold start
    "chutes",       # open-weight cloud — decentralised, very low cost
    "minimax",      # open-weight cloud — M-series, long context, agentic
    "cohere",       # open-weight cloud — Command A/R (CC-BY-NC: non-commercial only)
    "gemini",       # Google — fast, free tier (primary native)
    "deepseek",     # DeepSeek — cheap reasoning/code tier
    "claude",       # Anthropic — strongest reasoning tier when a key is present
    "openai",       # GPT-4/4o — standard
    "openrouter",   # aggregator — 200+ models, routing + fallbacks
    "mistral",      # open-weight + frontier, multilingual
    "opencode",     # OpenCode CLI — local MIT coding agent (free Claude Code); keyless
    "kimi",         # Moonshot AI — open-weight K2, strong coder
    "pollinations", # Pollinations — keyless free fast tier (openai-fast), last resort
]

# NOTE: every provider above is reached over the public internet. Local GPU
# runtimes (Ollama, vLLM, llama.cpp, LM Studio) are intentionally absent — they
# need hardware on the operator's machine, which this agent must not require.
# `providers/openweight_provider.OFFLINE_ONLY_SLUGS` records that decision and
# tests/test_open_weight_cloud.py enforces it.

def active_provider_name(env: Any = os.environ, default: str = "grok") -> str:
    """Resolve the configured active provider from `ACTIVE_AI_PROVIDER`/`AI_PROVIDER`."""
    raw = env.get("ACTIVE_AI_PROVIDER", env.get("AI_PROVIDER", default))
    return str(raw or default).strip().lower() or default


def validate_active_provider(
    env: Any = os.environ,
    supported: Any = None,
    default: str = "grok",
) -> Dict[str, Any]:
    """Fail-fast validation for the configured active provider.

    An unsupported provider name used to surface deep inside generation as a
    `ValueError`. Callers should validate at startup/CLI entry instead.
    """
    names = tuple(supported) if supported is not None else tuple(PROVIDER_CONFIGS)
    active = active_provider_name(env, default)
    if active not in names:
        return {
            "ok": False,
            "active": active,
            "supported": sorted(names),
            "error": (
                f"Unsupported ACTIVE_AI_PROVIDER '{active}'. "
                f"Supported: {', '.join(sorted(names))}"
            ),
        }
    return {"ok": True, "active": active, "supported": sorted(names), "error": None}


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
    """Dynamically instantiate a provider by name. Returns provider instance or None.

    Every provider that can appear in `FALLBACK_ORDER` must have an entry in
    `_PROVIDER_BUILDERS`; a missing entry is logged as an error and returns
    `None` (never a silent `None` from a swallowed import error only).
    """
    try:
        cfg = dict(get_active_provider_config(provider_name))
        if cfg.get("dynamic_env"):
            cfg["api_key"] = os.getenv(cfg["env_var_name"], cfg.get("api_key", ""))
            cfg["model"] = os.getenv("FREELLMAPI_MODEL", cfg.get("model", "auto"))
            cfg["base_url"] = os.getenv("FREELLMAPI_BASE_URL", cfg.get("base_url", ""))
    except ValueError:
        agent_logger.warning("instantiate_provider: unknown provider '%s'", provider_name)
        return None

    canonical = cfg["provider_name"]
    builder = _PROVIDER_BUILDERS.get(canonical)
    if builder is None:
        agent_logger.error(
            "instantiate_provider: no constructor registered for '%s' (class_path=%s) — "
            "this hop cannot serve calls",
            canonical,
            cfg.get("class_path"),
        )
        return None

    try:
        return builder(cfg)
    except Exception as exc:  # import error / constructor signature drift
        agent_logger.warning("instantiate_provider('%s') failed: %s", canonical, exc)
        return None


def _build_gemini(cfg: Dict[str, Any]):
    from providers.gemini_provider import GeminiProvider
    return GeminiProvider(cfg["api_key"], cfg["model"])


def _build_openai(cfg: Dict[str, Any]):
    from providers.openai_provider import OpenAIProvider
    return OpenAIProvider(cfg["api_key"], cfg["model"])


def _build_openrouter(cfg: Dict[str, Any]):
    from providers.openrouter_provider import OpenRouterProvider
    return OpenRouterProvider(cfg["api_key"], cfg["model"], model_names=cfg.get("models"))


def _build_grok(cfg: Dict[str, Any]):
    from providers.grok_provider import GrokProvider
    return GrokProvider(cfg["api_key"], cfg["model"])


def _build_mistral(cfg: Dict[str, Any]):
    from providers.mistral_provider import MistralProvider
    return MistralProvider(cfg["api_key"], cfg["model"])


def _build_omniroute(cfg: Dict[str, Any]):
    from providers.omniroute_provider import OmnirouteProvider
    return OmnirouteProvider(cfg["api_key"], cfg["model"])


def _build_ninerouter(cfg: Dict[str, Any]):
    from providers.ninerouter_provider import NinerouterProvider
    return NinerouterProvider(cfg["api_key"], cfg["model"])


def _build_freellmapi(cfg: Dict[str, Any]):
    from providers.freellmapi_provider import FreeLLMAPIProvider
    return FreeLLMAPIProvider(
        api_key=cfg["api_key"], model_name=cfg["model"], base_url=cfg["base_url"]
    )


def _build_opencode(cfg: Dict[str, Any]):
    from providers.opencode_provider import OpenCodeProvider
    return OpenCodeProvider(cfg.get("api_key", ""), cfg.get("model", ""))


def _build_kimi(cfg: Dict[str, Any]):
    from providers.kimi_provider import KimiProvider
    return KimiProvider(cfg["api_key"], cfg["model"], base_url=cfg.get("base_url") or None)


def _build_openweight(slug: str):
    """Build a cloud open-weight provider for one vendor slug."""
    def _builder(cfg: Dict[str, Any]):
        from providers.openweight_provider import OpenWeightCloudProvider
        return OpenWeightCloudProvider(
            slug,
            api_key=cfg.get("api_key") or None,
            model_name=cfg.get("model") or None,
            base_url=cfg.get("base_url") or None,
        )
    return _builder


def _build_nvidia(cfg: Dict[str, Any]):
    from providers.nvidia_provider import NvidiaProvider
    return NvidiaProvider(cfg["api_key"], cfg["model"])


def _build_claude(cfg: Dict[str, Any]):
    from providers.claude_provider import ClaudeProvider
    return ClaudeProvider(cfg["api_key"], cfg["model"])


def _build_deepseek(cfg: Dict[str, Any]):
    from providers.deepseek_provider import DeepSeekProvider
    return DeepSeekProvider(cfg["api_key"], cfg["model"])


def _build_pollinations(cfg: Dict[str, Any]):
    from providers.pollinations_provider import PollinationsProvider
    return PollinationsProvider(cfg.get("api_key") or None, cfg.get("model") or None)



# Canonical provider name (PROVIDER_CONFIGS[…]["provider_name"]) -> constructor.
# Aliases such as "moonshot" (kimi) and "anthropic" (claude) resolve through the
# canonical name, so one entry fixes every alias at once.
_PROVIDER_BUILDERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "gemini": _build_gemini,
    "openai": _build_openai,
    "openrouter": _build_openrouter,
    "grok": _build_grok,
    "mistral": _build_mistral,
    "omniroute": _build_omniroute,
    "ninerouter": _build_ninerouter,
    "freellmapi": lambda cfg: _build_freellmapi(cfg),
    "opencode": _build_opencode,
    "kimi": _build_kimi,
    "nvidia": _build_nvidia,
    "claude": _build_claude,
    "deepseek": _build_deepseek,
    "pollinations": _build_pollinations,
}

# Register every internet-only open-weight vendor from the single vendor table,
# so adding a vendor is a data change and can never drift from its constructor.
for _slug in OPENWEIGHT_VENDORS:
    PROVIDER_CONFIGS[_slug] = {
        "provider_name": _slug,
        "api_key": vendor_api_key(_slug),
        "model": vendor_models(_slug)[0],
        "models": vendor_models(_slug),
        "base_url": vendor_base_url(_slug),
        "env_var_name": OPENWEIGHT_VENDORS[_slug]["env_var"],
        "class_path": "providers.openweight_provider.OpenWeightCloudProvider",
        "open_source": True,
        "internet_only": True,  # reachable over HTTPS; never a local runtime
        "docs": OPENWEIGHT_VENDORS[_slug]["docs"],
    }
    _PROVIDER_BUILDERS[_slug] = _build_openweight(_slug)


#: API-key placeholders shipped in `.env.example` — never a configured key.
_PLACEHOLDER_KEYS = {
    "your_gemini_api_key_here",
    "your_openai_api_key_here",
    "your_openrouter_api_key_here",
    "your_mistral_api_key_here",
    "your_grok_api_key_here",
    "your_kimi_api_key_here",
    "your_cerebras_api_key_here",
    "your_deepinfra_api_key_here",
    "your_together_api_key_here",
    "your_fireworks_api_key_here",
    "your_sambanova_api_key_here",
    "your_novita_api_key_here",
    "your_huggingface_token_here",
    "your_nebius_api_key_here",
    "your_hyperbolic_api_key_here",
    "your_featherless_api_key_here",
    "your_chutes_api_key_here",
    "your_zai_api_key_here",
    "your_dashscope_api_key_here",
    "your_minimax_api_key_here",
    "your_cohere_api_key_here",
    "your_anthropic_api_key_here",
    "your_claude_api_key_here",
    "your_deepseek_api_key_here",
    "your_nvidia_api_key_here",
    "aq.",
    "",
}

#: Short example-key prefixes that may appear in copied `.env` files. A real
#: provider key never starts with one of these markers.
_PLACEHOLDER_PREFIXES = ("your_", "test_", "test-", "example", "placeholder", "changeme", "change-this")


def is_placeholder_key(key: str) -> bool:
    """Detect example keys without depending on an exhaustive literal list."""
    normalized = str(key or "").strip().lower()
    if not normalized:
        return True
    if normalized in _PLACEHOLDER_KEYS:
        return True
    return normalized.startswith(_PLACEHOLDER_PREFIXES)


def key_present(provider_name: str) -> bool:
    """True when the provider has a real (non-placeholder) API key configured."""
    cfg = get_active_provider_config(provider_name)
    key = str(cfg.get("api_key", "") or "").strip()
    # Accept both old (AIza...) and new (AQ.Ab8...) Gemini key formats
    if key.startswith("AQ.") and len(key) >= 10:
        return True
    return not is_placeholder_key(key)


def _local_runtime_ready(provider: Any) -> bool:
    """Reachability self-check for a *keyless* adapter.

    A keyless provider fronts a local runtime — a gateway server or, for
    `opencode`, an installed CLI. Providers that expose `is_available()` answer
    for themselves; those that cannot (the gateway adapters) stay assumed
    reachable, which preserves their existing behaviour.
    """
    probe = getattr(provider, "is_available", None)
    if not callable(probe):
        return True
    try:
        return bool(probe())
    except Exception:
        return False


def provider_status(provider_name: str) -> Dict[str, Any]:
    """Honest per-provider wiring report.

    `/api/providers` used to advertise a provider as available purely because a
    key existed, even when `instantiate_provider` had no branch for it (nvidia
    was the live example). Every fact is now reported separately and
    `configured` requires all of them: a working constructor, a real key (unless
    the provider is keyless) and, for keyless adapters, a reachable local
    runtime — so an uninstalled CLI is never advertised as an available hop.
    """
    cfg = get_active_provider_config(provider_name)
    keyless = bool(cfg.get("keyless"))
    try:
        key_ok = key_present(provider_name)
    except ValueError:
        key_ok = False

    provider = None
    try:
        provider = instantiate_provider(provider_name)
        constructor_ok = provider is not None
    except Exception:
        constructor_ok = False

    local_ready = _local_runtime_ready(provider) if (keyless and provider is not None) else True

    return {
        "name": cfg.get("provider_name", provider_name),
        "model": cfg.get("model", ""),
        "env_var": cfg.get("env_var_name", ""),
        "keyless": keyless,
        "key_present": key_ok,
        "constructor_ok": constructor_ok,
        "local_ready": local_ready,
        "configured": constructor_ok and local_ready and (keyless or key_ok),
    }


def validate_provider_key(provider_name: str = None, require_key: bool = True) -> bool:
    """Validate that required API key is configured for the selected provider."""
    cfg = get_active_provider_config(provider_name)

    # Keyless providers (e.g. local OmniRoute gateway) are always valid.
    if cfg.get("keyless"):
        return True

    key_valid = key_present(provider_name)

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
    """Providers that are genuinely usable: key present (or keyless) AND constructible.

    Key presence alone is not availability — a provider with no working
    constructor cannot serve a call, so it must not be advertised.
    """
    available = []
    for name in FALLBACK_ORDER:
        try:
            if provider_status(name)["configured"]:
                available.append(name)
        except Exception:
            continue
    return available


def describe_providers() -> List[Dict[str, Any]]:
    """Per-provider wiring report for `GET /api/providers` (FALLBACK_ORDER order)."""
    described: List[Dict[str, Any]] = []
    for name in FALLBACK_ORDER:
        try:
            status = provider_status(name)
        except Exception as exc:  # pragma: no cover - defensive
            status = {
                "name": name,
                "model": "",
                "env_var": "",
                "keyless": False,
                "key_present": False,
                "constructor_ok": False,
                "local_ready": False,
                "configured": False,
                "error": str(exc)[:200],
            }
        status["available"] = bool(status.get("configured"))
        described.append(status)
    return described
