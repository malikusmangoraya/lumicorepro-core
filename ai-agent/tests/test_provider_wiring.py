"""Regression coverage for provider wiring and example-key handling."""
import importlib

import pytest
import requests
from unittest.mock import MagicMock, patch

from config import providers as provider_module
from config.providers import (
    FALLBACK_ORDER,
    PROVIDER_CONFIGS,
    _PROVIDER_BUILDERS,
    active_provider_name,
    get_active_provider_config,
    instantiate_provider,
    key_present,
    validate_active_provider,
)
from providers.base_provider import BaseAIProvider
from providers.nvidia_provider import NvidiaProvider


def test_every_fallback_provider_has_an_importable_constructor():
    """Every advertised fallback hop must resolve to a real provider class."""
    for name in FALLBACK_ORDER:
        config = get_active_provider_config(name)
        module_name, class_name = config["class_path"].rsplit(".", 1)
        provider_cls = getattr(importlib.import_module(module_name), class_name)
        assert issubclass(provider_cls, BaseAIProvider)
        assert config["provider_name"] in _PROVIDER_BUILDERS


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("chatgpt", "openai"),
        ("moonshot", "kimi"),
        ("anthropic", "claude"),
    ],
)
def test_aliases_resolve_through_their_canonical_constructor(monkeypatch, alias, canonical):
    """One canonical constructor must fix every alias at once."""
    sentinel = object()
    monkeypatch.setattr(
        provider_module,
        "_PROVIDER_BUILDERS",
        {canonical: lambda config: sentinel},
    )

    assert instantiate_provider(alias) is sentinel


@pytest.mark.parametrize(
    "example_key",
    [
        "your_gemini_api_key_here",
        "your_gemini_key",
        "your_openrouter_key",
        "test-key",
        "EXAMPLE-KEY",
        "changeme",
        "AQ.",
        "",
    ],
)
def test_example_keys_are_never_treated_as_configured(monkeypatch, example_key):
    """Copied `.env.example` values must not advertise a provider as available."""
    monkeypatch.setitem(
        PROVIDER_CONFIGS,
        "example-provider",
        {
            "provider_name": "example-provider",
            "api_key": example_key,
            "env_var_name": "EXAMPLE_API_KEY",
        },
    )

    assert key_present("example-provider") is False


@pytest.mark.parametrize("real_key", ["sk-live-123", "AQ.Ab8-example"])
def test_real_keys_are_accepted(monkeypatch, real_key):
    monkeypatch.setitem(
        PROVIDER_CONFIGS,
        "example-provider",
        {
            "provider_name": "example-provider",
            "api_key": real_key,
            "env_var_name": "EXAMPLE_API_KEY",
        },
    )

    assert key_present("example-provider") is True


def test_env_example_documents_every_fallback_provider():
    """The documented ACTIVE_AI_PROVIDER list must match FALLBACK_ORDER."""
    example = (
        provider_module.__file__
        and (provider_module.__file__.rsplit("config", 1)[0] + ".env.example")
    )
    options_lines = []
    in_options = False
    for line in open(example, encoding="utf-8"):
        if line.startswith("# Options:"):
            in_options = True
            options_lines.append(line)
        elif in_options and line.startswith("#"):
            options_lines.append(line)
        elif options_lines:
            break
    options = " ".join(options_lines)

    for name in FALLBACK_ORDER:
        assert name in options


def test_freellmapi_provider_wiring_is_optional_and_does_not_change_defaults(monkeypatch):
    """FreeLLMAPI is opt-in; existing provider priority and default remain unchanged."""
    assert "freellmapi" not in FALLBACK_ORDER
    assert provider_module.AI_PROVIDER != "freellmapi"
    monkeypatch.setenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:4300/v1")
    monkeypatch.setenv("FREELLMAPI_MODEL", "auto")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "")

    provider = instantiate_provider("freellmapi")

    assert provider is not None
    assert provider.model_name == "auto"
    assert provider.base_url == "http://127.0.0.1:4300/v1"
    assert provider.api_key == ""
    assert provider_module.validate_provider_key("freellmapi") is True


def test_freellmapi_uses_openai_compatible_chat_endpoint(monkeypatch):
    from providers.freellmapi_provider import FreeLLMAPIProvider

    monkeypatch.setenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:4300/v1")
    provider = FreeLLMAPIProvider(api_key="", model_name="auto")
    response = MagicMock(status_code=200)
    response.json.return_value = _valid_nvidia_payload("connected")

    with patch("providers.freellmapi_provider.requests.post", return_value=response) as post:
        assert provider._raw_call("hello") == "connected"

    assert post.call_args.args[0] == "http://127.0.0.1:4300/v1/chat/completions"
    assert "Authorization" not in post.call_args.kwargs["headers"]
    assert post.call_args.kwargs["json"]["model"] == "auto"


def test_nvidia_provider_is_concrete_and_instantiable():
    """The former abstract NVIDIA hop must resolve to a usable provider object."""
    provider = instantiate_provider("nvidia")

    assert isinstance(provider, NvidiaProvider)
    assert isinstance(provider, BaseAIProvider)


def _nvidia_response(status_code, payload=None, text=""):
    response = MagicMock(status_code=status_code)
    response.json.return_value = payload
    response.text = text
    return response


def _valid_nvidia_payload(text="code"):
    return {"choices": [{"message": {"content": text}}]}


def test_nvidia_fails_fast_on_authentication_errors():
    """A wrong key must not burn calls across every fallback model."""
    provider = NvidiaProvider(api_key="sk-test")

    with patch(
        "providers.nvidia_provider.requests.post",
        return_value=_nvidia_response(401, text="unauthorized"),
    ) as post:
        with pytest.raises(RuntimeError, match="authentication failed"):
            provider._raw_call("hi")

    assert post.call_count == 1


def test_nvidia_falls_back_only_for_missing_models():
    provider = NvidiaProvider(api_key="sk-test")

    with patch(
        "providers.nvidia_provider.requests.post",
        side_effect=[
            _nvidia_response(404, text="model not found"),
            _nvidia_response(200, _valid_nvidia_payload("ok")),
        ],
    ) as post:
        assert provider._raw_call("hi") == "ok"

    assert post.call_count == 2


def test_nvidia_does_not_retry_rate_limits_or_transport_errors():
    """Rotation belongs to the router; one logical call means one HTTP attempt."""
    provider = NvidiaProvider(api_key="sk-test")

    with patch(
        "providers.nvidia_provider.requests.post",
        return_value=_nvidia_response(429, text="slow down"),
    ) as limited:
        with pytest.raises(RuntimeError, match="rate limited"):
            provider._raw_call("hi")
    assert limited.call_count == 1

    with patch(
        "providers.nvidia_provider.requests.post",
        side_effect=requests.RequestException("connection refused"),
    ) as unreachable:
        with pytest.raises(RuntimeError, match="request failed"):
            provider._raw_call("hi")
    assert unreachable.call_count == 1


def test_nvidia_rejects_malformed_api_shapes():
    provider = NvidiaProvider(api_key="sk-test")

    with patch(
        "providers.nvidia_provider.requests.post",
        return_value=_nvidia_response(200, {"choices": []}),
    ) as post:
        with pytest.raises(RuntimeError, match="Unexpected NVIDIA response shape"):
            provider._raw_call("hi")

    assert post.call_count == 1


def test_nvidia_availability_matches_placeholder_policy():
    assert NvidiaProvider(api_key="your_nvidia_api_key_here").is_available() is False
    assert NvidiaProvider(api_key="sk-live-test").is_available() is True


def test_providers_package_exports_every_configured_class():
    """`from providers import X` must work for every advertised constructor."""
    import providers

    for config in PROVIDER_CONFIGS.values():
        module_name, class_name = config["class_path"].rsplit(".", 1)
        expected = getattr(importlib.import_module(module_name), class_name)
        assert getattr(providers, class_name) is expected
        assert class_name in providers.__all__


def test_active_provider_prefers_active_over_legacy_variable(monkeypatch):
    """ACTIVE_AI_PROVIDER is canonical; AI_PROVIDER remains a legacy fallback."""
    monkeypatch.setenv("ACTIVE_AI_PROVIDER", "Gemini")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    assert active_provider_name() == "gemini"

    monkeypatch.delenv("ACTIVE_AI_PROVIDER")
    assert active_provider_name() == "openai"


@pytest.mark.parametrize("name", sorted(PROVIDER_CONFIGS))
def test_validate_active_provider_accepts_every_configured_name(monkeypatch, name):
    """Startup validation must accept exactly the names the factory supports."""
    monkeypatch.setenv("ACTIVE_AI_PROVIDER", name)
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    result = validate_active_provider()

    assert result == {
        "ok": True,
        "active": name,
        "supported": sorted(PROVIDER_CONFIGS),
        "error": None,
    }


def test_validate_active_provider_rejects_unknown_names(monkeypatch):
    """A typo must fail fast with the supported list, not deep in generation."""
    monkeypatch.setenv("ACTIVE_AI_PROVIDER", "not-a-provider")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    result = validate_active_provider()

    assert result["ok"] is False
    assert result["active"] == "not-a-provider"
    assert result["supported"] == sorted(PROVIDER_CONFIGS)
    assert "not-a-provider" in result["error"]
    assert "gemini" in result["error"]


def test_validate_active_provider_defaults_to_grok(monkeypatch):
    monkeypatch.delenv("ACTIVE_AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    result = validate_active_provider()

    assert result["ok"] is True
    assert result["active"] == "grok"
