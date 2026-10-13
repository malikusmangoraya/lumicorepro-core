"""Providers package initialization (lazy).

Provider classes are imported on first attribute access instead of eagerly so
that importing `providers` never drags in requests/httpx/openai SDKs at startup
(e.g. when only one provider is actually used). `from providers import X` and
`from providers.<module> import X` both keep working.
"""
import importlib
import types

_PROVIDER_MODULES = {
    "GeminiProvider": "providers.gemini_provider",
    "OpenRouterProvider": "providers.openrouter_provider",
    "MistralProvider": "providers.mistral_provider",
    "OpenAIProvider": "providers.openai_provider",
    "GrokProvider": "providers.grok_provider",
    "OmnirouteProvider": "providers.omniroute_provider",
    "NinerouterProvider": "providers.ninerouter_provider",
    "OpenCodeProvider": "providers.opencode_provider",
    "NvidiaProvider": "providers.nvidia_provider",
    "FreeLLMAPIProvider": "providers.freellmapi_provider",
    "ClaudeProvider": "providers.claude_provider",
    "DeepSeekProvider": "providers.deepseek_provider",
    "KimiProvider": "providers.kimi_provider",
    "OpenWeightCloudProvider": "providers.openweight_provider",
}

__all__ = list(_PROVIDER_MODULES.keys())


def __getattr__(name: str):
    """Resolve a provider class on demand, importing its module lazily."""
    module_name = _PROVIDER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_name)
    cls = getattr(module, name)
    # Cache on this module so repeated access avoids re-import overhead.
    globals()[name] = cls
    return cls


def __dir__():
    return sorted(set(globals().keys()) | set(__all__))