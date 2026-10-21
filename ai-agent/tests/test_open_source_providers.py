"""Tests for the primary open-weight providers: Kimi (Moonshot) and Groq Cloud.

The internet-only open-weight *cloud* vendors (Cerebras, DeepInfra, Together,
Fireworks, SambaNova, Novita, Hugging Face, Nebius, Hyperbolic, Featherless,
Chutes) have their own guard file: `test_open_weight_cloud.py`.

There is deliberately no test for a local/offline runtime here. Ollama, vLLM,
llama.cpp and LM Studio are out of scope — the agent must not need a GPU on the
operator's machine — and `OFFLINE_ONLY_SLUGS` in `providers.openweight_provider`
records that decision for the guard tests to enforce.
"""
import os

import pytest
from unittest.mock import MagicMock, patch

from providers.grok_provider import GrokProvider
from providers.kimi_provider import CHINA_BASE, INTERNATIONAL_BASE, KimiProvider


# ── Registration / config wiring ────────────────────────────────────────────
def test_providers_are_registered():
    from config.providers import FALLBACK_ORDER, PROVIDER_CONFIGS

    for name in ("kimi", "moonshot", "grok", "groq"):
        assert name in PROVIDER_CONFIGS, f"{name} missing from PROVIDER_CONFIGS"
    # `groq` is the natural spelling of the historical `grok` slug; both resolve
    # to the Groq Cloud class (which hits api.groq.com).
    assert PROVIDER_CONFIGS["groq"]["provider_name"] == PROVIDER_CONFIGS["grok"]["provider_name"]
    assert PROVIDER_CONFIGS["kimi"]["open_source"] is True
    assert PROVIDER_CONFIGS["grok"]["open_source"] is True
    # Open-weight hosts are preferred; the slowest-to-reach ones sit last.
    assert FALLBACK_ORDER.index("kimi") > FALLBACK_ORDER.index("mistral")
    assert FALLBACK_ORDER[-1] == "pollinations"  # keyless free tier = last resort


def test_instantiate_returns_real_provider_classes():
    from config.providers import instantiate_provider

    assert isinstance(instantiate_provider("kimi"), KimiProvider)
    assert isinstance(instantiate_provider("moonshot"), KimiProvider)
    assert isinstance(instantiate_provider("grok"), GrokProvider)
    assert isinstance(instantiate_provider("groq"), GrokProvider)


def test_placeholder_keys_are_rejected():
    from config.providers import validate_provider_key

    # omniroute is keyless, kimi is not: a placeholder key must not count as configured.
    assert validate_provider_key("omniroute", require_key=False) is True
    with patch("config.providers.PROVIDER_CONFIGS", {
        "kimi": {"provider_name": "kimi", "api_key": "your_kimi_api_key_here", "env_var_name": "KIMI_API_KEY"}
    }):
        assert validate_provider_key("kimi", require_key=False) is False


# ── Kimi ────────────────────────────────────────────────────────────────────
def test_kimi_defaults_to_a_live_model_id():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("KIMI_MODEL", None)
        provider = KimiProvider(api_key="sk-test")
    assert provider.model_name == "kimi-k2.7-code"
    assert provider.base_url == INTERNATIONAL_BASE
    assert provider.chat_endpoint == f"{INTERNATIONAL_BASE}/chat/completions"
    # Retired ids must never be the default.
    assert "kimi-latest" not in provider.FALLBACK_MODELS
    assert not any(m.startswith("kimi-k2-0") for m in provider.FALLBACK_MODELS)


def test_kimi_reads_moonshot_key_alias_and_china_base():
    with patch.dict(os.environ, {"MOONSHOT_API_KEY": "sk-moon", "KIMI_BASE_URL": CHINA_BASE}, clear=False):
        os.environ.pop("KIMI_API_KEY", None)
        provider = KimiProvider()
    assert provider.api_key == "sk-moon"
    assert provider.base_url == CHINA_BASE
    assert provider.chat_endpoint.startswith("https://api.moonshot.cn")


def test_kimi_requires_a_key():
    with pytest.raises(ValueError, match="Kimi API key not configured"):
        KimiProvider(api_key="your_kimi_api_key_here")._raw_call("hi")


def test_kimi_returns_content_and_uses_the_configured_model():
    provider = KimiProvider(api_key="sk-test", model_name="kimi-k2.6")
    response = MagicMock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "print(1)"}}]}
    with patch("providers.kimi_provider.requests.post", return_value=response) as post:
        assert provider._raw_call("write code") == "print(1)"
    assert post.call_args.kwargs["json"]["model"] == "kimi-k2.6"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer sk-test"


def test_kimi_falls_back_to_the_next_model_on_404():
    """A retired/renamed model id must not sink the whole call."""
    provider = KimiProvider(api_key="sk-test", model_name="kimi-k2-retired")
    bad = MagicMock(status_code=404, text="model not found")
    good = MagicMock(status_code=200)
    good.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    with patch("providers.kimi_provider.requests.post", side_effect=[bad, good]) as post:
        assert provider._raw_call("hi") == "ok"
    assert post.call_count == 2
    assert post.call_args_list[1].kwargs["json"]["model"] == "kimi-k2.7-code"


def test_kimi_raises_on_rate_limit_without_hiding_the_status():
    provider = KimiProvider(api_key="sk-test")
    limited = MagicMock(status_code=429, text="rate limited")
    with patch("providers.kimi_provider.requests.post", return_value=limited):
        with pytest.raises(RuntimeError, match="429"):
            provider._raw_call("hi")


def test_kimi_list_models_survives_a_dead_endpoint():
    provider = KimiProvider(api_key="sk-test", timeout=5)
    with patch("providers.kimi_provider.requests.get", side_effect=OSError("down")):
        assert provider.list_models() == []


# ── Groq Cloud (slug `grok`, alias `groq`) ──────────────────────────────────
def test_grok_targets_groq_cloud_not_xai():
    """The historical slug is `grok`, but the class must hit Groq Cloud."""
    provider = GrokProvider(api_key="gsk_test")
    assert "groq.com" in provider.endpoint
    assert "x.ai" not in provider.endpoint


# ── Lazy import contract ────────────────────────────────────────────────────
def test_providers_package_exports_provider_classes():
    import providers

    assert providers.KimiProvider is KimiProvider
    assert providers.GrokProvider is GrokProvider
    assert "KimiProvider" in dir(providers)
    assert "GrokProvider" in dir(providers)
