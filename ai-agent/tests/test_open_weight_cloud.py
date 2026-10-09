"""Guard tests for the internet-only open-weight cloud providers.

The point of this file is the *constraint*: every open-weight vendor the agent
can reach must be a public HTTPS host, reachable over the internet, and must
never be a local/offline GPU runtime. A future "just add Ollama" change has to
delete a test here, not merely edit a table.

Covers:
  1. every vendor base URL is public https, never loopback/private
  2. the offline-only slugs never reappear in the registry or routing
  3. every vendor is registered, marked internet-only, and instantiable
  4. model fallback on 400/404, and a key-naming error on 401/403
  5. `list_models()` degrades to [] instead of raising on a dead endpoint
"""
import os

import pytest
from unittest.mock import MagicMock, patch

from providers.openweight_provider import (
    OFFLINE_ONLY_SLUGS,
    OPENWEIGHT_VENDORS,
    OpenWeightCloudProvider,
    vendor_api_key,
    vendor_base_url,
    vendor_models,
)

VENDORS = sorted(OPENWEIGHT_VENDORS)
#: Hosts that must never be reachable by a provider: loopback/private ranges plus
#: the bare "localhost" string, which would defeat the internet-only guarantee.
LOOPBACK_MARKERS = ("127.0.0.1", "localhost", "0.0.0.0", "::1", "192.168.", "10.0.0.")


# ── 1. Every endpoint is public internet ────────────────────────────────────
def test_registry_is_not_empty():
    assert len(VENDORS) >= 8, f"expected a broad vendor set, got {VENDORS}"


@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_base_url_is_public_https(slug):
    url = OPENWEIGHT_VENDORS[slug]["base_url"]
    assert url.startswith("https://"), f"{slug} must be https, got {url}"
    assert not url.startswith("http://"), f"{slug} must not be plain http"
    for marker in LOOPBACK_MARKERS:
        assert marker not in url, f"{slug} points at {marker}: {url}"


@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_base_url_is_a_real_host_not_an_ip(slug):
    """A hostname means the call crosses the internet; a raw IP does not prove that."""
    host = OPENWEIGHT_VENDORS[slug]["base_url"].split("//", 1)[1].split("/", 1)[0]
    assert "." in host and not host.replace(".", "").isdigit(), f"{slug} host looks like an IP: {host}"


@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_declares_key_models_and_docs(slug):
    spec = OPENWEIGHT_VENDORS[slug]
    for field in ("env_var", "base_url", "default_model", "models", "docs", "note"):
        assert spec.get(field), f"{slug} is missing {field}"
    assert spec["default_model"] in spec["models"], f"{slug} default is not in its model list"
    assert spec["docs"].startswith("https://")


# ── 2. No offline/GPU runtime may reappear ──────────────────────────────────
def test_offline_only_slugs_are_absent_from_the_registry():
    assert not (set(OPENWEIGHT_VENDORS) & OFFLINE_ONLY_SLUGS)
    # The decision itself must stay recorded.
    assert {"ollama", "vllm", "llamacpp", "lmstudio"} <= OFFLINE_ONLY_SLUGS


@pytest.mark.parametrize("slug", sorted(OFFLINE_ONLY_SLUGS))
def test_offline_only_slugs_are_never_configurable(slug):
    from config.providers import FALLBACK_ORDER, PROVIDER_CONFIGS

    assert slug not in PROVIDER_CONFIGS, f"{slug} is an offline runtime and must not be configurable"
    assert slug not in FALLBACK_ORDER, f"{slug} must not be in the fallback chain"


def test_no_routing_tier_names_an_offline_runtime():
    from agent.ai_routing import DEFAULT_TIERS

    names = {name for members in DEFAULT_TIERS.values() for name in members}
    assert not (names & OFFLINE_ONLY_SLUGS), f"offline runtime in DEFAULT_TIERS: {names & OFFLINE_ONLY_SLUGS}"


def test_the_openweight_module_declares_no_loopback_url():
    """The open-weight module must stay internet-only.

    Scoped to this module on purpose: the keyless gateway providers
    (`ninerouter`, `omniroute`) legitimately default to a loopback address, but
    an open-weight vendor never may. Only URL literals are inspected, so prose
    that happens to say "not localhost" stays legal.
    """
    import re
    from pathlib import Path

    import providers.openweight_provider as mod

    text = Path(mod.__file__).read_text(encoding="utf-8", errors="replace")
    urls = re.findall(r"https?://[^\s\"'`)]+", text)
    assert urls, "expected the module to declare vendor/documentation URLs"
    for url in urls:
        lowered = url.lower()
        for marker in LOOPBACK_MARKERS:
            assert marker not in lowered, f"openweight_provider.py declares {url}"


# ── 3. Registration + instantiation ─────────────────────────────────────────
@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_is_registered_in_fallback_order(slug):
    from config.providers import FALLBACK_ORDER, PROVIDER_CONFIGS

    assert slug in PROVIDER_CONFIGS, f"{slug} missing from PROVIDER_CONFIGS"
    assert slug in FALLBACK_ORDER, f"{slug} is configured but unreachable (not in FALLBACK_ORDER)"


@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_config_reports_internet_only(slug):
    from config.providers import PROVIDER_CONFIGS

    cfg = PROVIDER_CONFIGS[slug]
    assert cfg["provider_name"] == slug
    assert cfg["internet_only"] is True
    assert cfg["open_source"] is True
    assert cfg["env_var_name"] == OPENWEIGHT_VENDORS[slug]["env_var"]
    assert cfg["base_url"] == OPENWEIGHT_VENDORS[slug]["base_url"]
    assert not cfg.get("keyless"), f"{slug} must require a key; it is not a local gateway"


@pytest.mark.parametrize("slug", VENDORS)
def test_vendor_instantiates_to_the_cloud_provider(slug):
    from config.providers import instantiate_provider

    provider = instantiate_provider(slug)
    assert isinstance(provider, OpenWeightCloudProvider), f"{slug} -> {type(provider).__name__}"
    assert provider.slug == slug
    assert provider.chat_endpoint == f"{OPENWEIGHT_VENDORS[slug]['base_url']}/chat/completions"
    assert provider.models_endpoint == f"{OPENWEIGHT_VENDORS[slug]['base_url']}/models"


@pytest.mark.parametrize("slug", VENDORS)
def test_describe_providers_reports_every_vendor_honestly(slug):
    from config.providers import describe_providers

    by_name = {item["name"]: item for item in describe_providers()}
    assert slug in by_name, f"{slug} missing from /api/providers output"
    entry = by_name[slug]
    assert entry["env_var"] == OPENWEIGHT_VENDORS[slug]["env_var"]
    assert entry["constructor_ok"] is True
    # No key in the test environment, so it must NOT claim to be available.
    assert entry["available"] is False


def test_unknown_slug_is_rejected():
    with pytest.raises(ValueError, match="Unknown open-weight vendor"):
        OpenWeightCloudProvider("not-a-real-vendor")


# ── 4. Model fallback + auth errors ─────────────────────────────────────────
def _ok(content: str) -> MagicMock:
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def _provider(slug: str = "cerebras", **kwargs) -> OpenWeightCloudProvider:
    kwargs.setdefault("api_key", "sk-test")
    return OpenWeightCloudProvider(slug, **kwargs)


def test_missing_key_names_the_env_var():
    provider = _provider("together", api_key="")
    with pytest.raises(ValueError, match="TOGETHER_API_KEY"):
        provider._raw_call("hi")


def test_rejected_key_names_the_env_var_and_does_not_retry_other_models():
    provider = _provider("fireworks")
    rejected = MagicMock(status_code=401, text="nope")
    with patch("providers.openweight_provider.requests.post", return_value=rejected) as post:
        with pytest.raises(RuntimeError, match="FIREWORKS_API_KEY"):
            provider._raw_call("hi")
    # A rejected key is fatal: exactly one request, not one per fallback model.
    assert post.call_count == 1


def test_forbidden_also_names_the_env_var():
    provider = _provider("novita")
    with patch("providers.openweight_provider.requests.post", return_value=MagicMock(status_code=403, text="nope")):
        with pytest.raises(RuntimeError, match="NOVITA_API_KEY"):
            provider._raw_call("hi")


def test_auth_error_is_a_runtime_error_subclass():
    from providers.openweight_provider import ProviderAuthError

    assert issubclass(ProviderAuthError, RuntimeError)


@pytest.mark.parametrize("status", [400, 404])
def test_retired_model_walks_to_the_next_candidate(status):
    provider = _provider("sambanova", model_name="retired-model")
    bad = MagicMock(status_code=status, text="model not found")
    with patch("providers.openweight_provider.requests.post", side_effect=[bad, _ok("print(1)")]) as post:
        assert provider._raw_call("write code") == "print(1)"
    assert post.call_count == 2
    assert post.call_args_list[0].kwargs["json"]["model"] == "retired-model"
    # The requested (unknown) id is tried first, then the registry default.
    assert post.call_args_list[1].kwargs["json"]["model"] == provider.FALLBACK_MODELS[0]


def test_all_candidates_exhausted_raises_with_the_endpoint():
    provider = _provider("deepinfra", model_name="retired")
    bad = MagicMock(status_code=404, text="model not found")
    with patch("providers.openweight_provider.requests.post", return_value=bad):
        with pytest.raises(RuntimeError) as exc:
            provider._raw_call("hi")
    message = str(exc.value)
    assert provider.chat_endpoint in message
    assert "models tried" in message


def test_connectivity_failure_is_reported_not_swallowed():
    provider = _provider("huggingface")
    with patch("providers.openweight_provider.requests.post", side_effect=OSError("connection refused")):
        with pytest.raises(RuntimeError, match="connection refused"):
            provider._raw_call("hi")


def test_successful_call_sends_bearer_auth_and_the_system_prompt():
    provider = _provider("cerebras", model_name="qwen-3.8-27b")
    with patch("providers.openweight_provider.requests.post", return_value=_ok("ok")) as post:
        assert provider._raw_call("hello", "be terse") == "ok"
    headers = post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-test"
    assert post.call_args.kwargs["json"]["messages"][0] == {"role": "system", "content": "be terse"}


def test_empty_content_falls_through_to_the_next_model():
    provider = _provider("chutes", model_name="retired")
    empty = _ok("")
    with patch("providers.openweight_provider.requests.post", side_effect=[empty, _ok("real")]) as post:
        assert provider._raw_call("hi") == "real"
    assert post.call_count == 2


# ── 5. Overrides + list_models ──────────────────────────────────────────────
def test_model_override_is_tried_first(monkeypatch):
    monkeypatch.setenv("CHUTES_MODEL", "my/custom-model")
    assert vendor_models("chutes")[0] == "my/custom-model"
    provider = OpenWeightCloudProvider("chutes", api_key="sk-test")
    assert provider.model_name == "my/custom-model"
    # The registry default stays in the candidate list as a fallback.
    assert OPENWEIGHT_VENDORS["chutes"]["default_model"] in provider.FALLBACK_MODELS


def test_base_url_override_keeps_https_and_replaces_the_default(monkeypatch):
    monkeypatch.setenv("NEBIUS_BASE_URL", "https://proxy.internal.example/v1/")
    assert vendor_base_url("nebius") == "https://proxy.internal.example/v1"
    provider = OpenWeightCloudProvider("nebius", api_key="sk-test")
    assert provider.chat_endpoint == "https://proxy.internal.example/v1/chat/completions"


def test_vendor_models_are_deduplicated(monkeypatch):
    monkeypatch.setenv("CEREBRAS_MODEL", OPENWEIGHT_VENDORS["cerebras"]["default_model"])
    models = vendor_models("cerebras")
    assert len(models) == len(set(models))


def test_vendor_api_key_reads_the_documented_env_var(monkeypatch):
    monkeypatch.setenv("SAMBANOVA_API_KEY", "sk-samba")
    assert vendor_api_key("sambanova") == "sk-samba"
    assert vendor_api_key("deepinfra") == ""


def test_list_models_sorts_and_parses_ids():
    provider = _provider("nebius")
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"data": [{"id": "b-model"}, {"id": "a-model"}, {"no_id": 1}]}
    with patch("providers.openweight_provider.requests.get", return_value=resp):
        assert provider.list_models() == ["a-model", "b-model"]


def test_list_models_survives_a_dead_endpoint():
    provider = _provider("featherless")
    with patch("providers.openweight_provider.requests.get", side_effect=OSError("down")):
        assert provider.list_models() == []


def test_list_models_returns_empty_on_a_non_200():
    provider = _provider("hyperbolic")
    with patch("providers.openweight_provider.requests.get", return_value=MagicMock(status_code=500)):
        assert provider.list_models() == []


# ── Lazy import contract ────────────────────────────────────────────────────
def test_providers_package_exports_the_cloud_provider():
    import providers

    assert providers.OpenWeightCloudProvider is OpenWeightCloudProvider
    assert "OpenWeightCloudProvider" in dir(providers)
