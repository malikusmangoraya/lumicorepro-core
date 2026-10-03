"""Tests for the open-weight providers: Kimi (Moonshot) and OpenMuse (local)."""
import os

import pytest
from unittest.mock import MagicMock, patch

from providers.kimi_provider import CHINA_BASE, INTERNATIONAL_BASE, KimiProvider
from providers.openmuse_provider import DEFAULT_BASE_URLS, OpenMuseProvider


# ── Registration / config wiring ────────────────────────────────────────────
def test_both_providers_are_registered():
    from config.providers import FALLBACK_ORDER, PROVIDER_CONFIGS, instantiate_provider

    for name in ("kimi", "moonshot", "openmuse"):
        assert name in PROVIDER_CONFIGS, f"{name} missing from PROVIDER_CONFIGS"
    # Local/offline hops go last so a dead local server never blocks a real call.
    assert FALLBACK_ORDER.index("kimi") > FALLBACK_ORDER.index("mistral")
    assert FALLBACK_ORDER.index("openmuse") == len(FALLBACK_ORDER) - 1
    assert PROVIDER_CONFIGS["openmuse"]["keyless"] is True
    assert PROVIDER_CONFIGS["kimi"]["open_source"] is True


def test_instantiate_returns_real_provider_classes():
    from config.providers import instantiate_provider

    assert isinstance(instantiate_provider("kimi"), KimiProvider)
    assert isinstance(instantiate_provider("moonshot"), KimiProvider)
    assert isinstance(instantiate_provider("openmuse"), OpenMuseProvider)


def test_placeholder_keys_are_rejected():
    from config.providers import validate_provider_key

    # openmuse is keyless, kimi is not: a placeholder key must not count as configured.
    assert validate_provider_key("openmuse", require_key=False) is True
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


# ── OpenMuse ────────────────────────────────────────────────────────────────
def test_openmuse_is_keyless_and_omits_authorization():
    provider = OpenMuseProvider(api_key="", model_name="qwen3-coder")
    assert "Authorization" not in provider._headers()
    response = MagicMock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "def f(): ..."}}]}
    with patch("providers.openmuse_provider.requests.post", return_value=response) as post:
        assert provider.generate_code("task") == "def f(): ..."
    assert "Authorization" not in post.call_args.kwargs["headers"]


def test_openmuse_placeholder_key_is_not_sent():
    provider = OpenMuseProvider(api_key="your_openmuse_api_key_here")
    assert "Authorization" not in provider._headers()
    provider = OpenMuseProvider(api_key="real-token")
    assert provider._headers()["Authorization"] == "Bearer real-token"


def test_openmuse_targets_a_local_openai_compatible_server():
    provider = OpenMuseProvider()
    assert provider.base_url == DEFAULT_BASE_URLS[0]
    assert provider.base_url.startswith("http://127.0.0.1")
    # The documented local runtimes must all be probed.
    ports = {url.rsplit(":", 1)[-1] for url in DEFAULT_BASE_URLS}
    assert ports == {"8080/v1", "11434/v1", "8000/v1", "1234/v1"}


def test_openmuse_error_message_names_the_unreachable_endpoint():
    provider = OpenMuseProvider(base_url="http://127.0.0.1:9/v1", model_name="qwen3-coder")
    provider.timeout = 1
    with patch("providers.openmuse_provider.requests.post", side_effect=OSError("connection refused")):
        with pytest.raises(RuntimeError) as exc:
            provider._raw_call("hi")
    assert "127.0.0.1:9" in str(exc.value)


def test_openmuse_lists_models_from_the_local_server():
    provider = OpenMuseProvider(timeout=5)
    response = MagicMock(status_code=200)
    response.json.return_value = {"data": [{"id": "qwen3-coder"}, {"id": "llama3.1:8b"}]}
    with patch("providers.openmuse_provider.requests.get", return_value=response):
        assert provider.list_models() == ["llama3.1:8b", "qwen3-coder"]


# ── Lazy import contract ────────────────────────────────────────────────────
def test_providers_package_exports_new_classes():
    import providers

    assert providers.KimiProvider is KimiProvider
    assert providers.OpenMuseProvider is OpenMuseProvider
    assert "KimiProvider" in dir(providers)
    assert "OpenMuseProvider" in dir(providers)
