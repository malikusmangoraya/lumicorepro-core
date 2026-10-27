"""Provider liveness: a placeholder key or a retired model id must stop the
factory before it writes a half-finished project, not minutes into generation."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent import factory_pipeline
from config import providers


def _cfg(name="groq", model="openai/gpt-oss-120b", key="gsk_realkey", env_var="GROK_API_KEY", **extra):
    base = {
        "provider_name": "grok",
        "api_key": key,
        "model": model,
        "env_var_name": env_var,
        "class_path": "providers.grok_provider.GrokProvider",
    }
    base.update(extra)
    return base


class _Response:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload


def _wired(monkeypatch, cfg=None, provider=None):
    cfg = cfg or _cfg()
    monkeypatch.setattr(providers, "get_active_provider_config", lambda name=None: cfg)
    monkeypatch.setattr(providers, "key_present", lambda name: not providers.is_placeholder_key(cfg["api_key"]))
    monkeypatch.setattr(providers, "instantiate_provider", lambda name: provider or SimpleNamespace(
        endpoint="https://api.groq.com/openai/v1/chat/completions"))
    monkeypatch.setattr(providers, "active_provider_name", lambda *a: "groq")
    monkeypatch.setattr(providers, "provider_status", lambda name: {
        "name": "grok", "model": cfg["model"], "env_var": cfg["env_var_name"],
        "keyless": bool(cfg.get("keyless")), "key_present": providers.key_present(name),
        "constructor_ok": True, "local_ready": True,
        "configured": providers.key_present(name),
    })


# ── probe_model ──────────────────────────────────────────────────────────────

def test_probe_model_accepts_a_listed_model(monkeypatch):
    _wired(monkeypatch)
    body = {"data": [{"id": "openai/gpt-oss-120b"}, {"id": "qwen/qwen3.8-27b"}]}
    with patch("requests.get", return_value=_Response(body)) as get:
        out = providers.probe_model("groq")
    assert out["probed"] is True
    assert out["model_offered"] is True
    assert out["available_models"] == 2
    assert "api.groq.com/openai/v1/models" in get.call_args[0][0]


def test_probe_model_flags_a_retired_model_and_suggests_replacements(monkeypatch):
    _wired(monkeypatch, cfg=_cfg(model="llama-3.3-70b-versatile"))
    body = {"data": [{"id": "openai/gpt-oss-120b"}, {"id": "allam-2-7b"}]}
    with patch("requests.get", return_value=_Response(body)):
        out = providers.probe_model("groq")
    assert out["probed"] is True
    assert out["model_offered"] is False
    assert out["suggested_models"] == ["allam-2-7b", "openai/gpt-oss-120b"]
    assert "llama-3.3-70b-versatile" in out["reason"]
    assert "GROK_MODEL" in out["reason"]


def test_probe_model_reports_an_authorized_error_instead_of_raising(monkeypatch):
    _wired(monkeypatch)
    with patch("requests.get", return_value=_Response({}, status=401)):
        out = providers.probe_model("groq")
    assert out["probed"] is False
    assert out["model_offered"] is None
    assert "HTTP 401" in out["reason"]


def test_probe_model_survives_a_network_failure(monkeypatch):
    _wired(monkeypatch)
    with patch("requests.get", side_effect=OSError("dns down")):
        out = providers.probe_model("groq")
    assert out["probed"] is False
    assert "OSError" in out["reason"]


def test_probe_model_skips_a_placeholder_key(monkeypatch):
    _wired(monkeypatch, cfg=_cfg(key="your_grok_api_key_here"))
    with patch("requests.get") as get:
        out = providers.probe_model("groq")
    get.assert_not_called()
    assert out["probed"] is False
    assert "not probed" in out["reason"]


def test_probe_model_skips_keyless_providers(monkeypatch):
    _wired(monkeypatch, cfg=_cfg(key="", keyless=True))
    with patch("requests.get") as get:
        out = providers.probe_model("groq")
    get.assert_not_called()
    assert out["probed"] is False


def test_probe_model_skips_providers_without_a_model_list(monkeypatch):
    _wired(monkeypatch, provider=SimpleNamespace(endpoint="https://example.test/messages"))
    with patch("requests.get") as get:
        out = providers.probe_model("groq")
    get.assert_not_called()
    assert "no OpenAI-compatible model list" in out["reason"]


def test_probe_model_rejects_an_unparsable_body(monkeypatch):
    _wired(monkeypatch)
    with patch("requests.get", return_value=_Response({"unexpected": json.dumps([])})):
        out = providers.probe_model("groq")
    assert out["probed"] is False
    assert "empty" in out["reason"]


def test_probe_model_rejects_an_unknown_provider(monkeypatch):
    def _boom(name=None):
        raise ValueError("no such provider")

    monkeypatch.setattr(providers, "get_active_provider_config", _boom)
    out = providers.probe_model("definitely-not-real")
    assert out["probed"] is False
    assert "unknown provider" in out["reason"]


# ── factory preflight gate ───────────────────────────────────────────────────

def test_provider_health_is_green_when_the_model_is_offered(monkeypatch):
    _wired(monkeypatch)
    with patch("requests.get", return_value=_Response({"data": [{"id": "openai/gpt-oss-120b"}]})):
        health = factory_pipeline.provider_health()
    assert health["usable"] is True
    assert health["provider"] == "grok"
    assert health["model_offered"] is True


def test_provider_health_blocks_a_retired_model(monkeypatch):
    _wired(monkeypatch, cfg=_cfg(model="llama-3.2-11b-vision-preview"))
    with patch("requests.get", return_value=_Response({"data": [{"id": "openai/gpt-oss-120b"}]})):
        health = factory_pipeline.provider_health()
    assert health["usable"] is False
    assert "not offered" in health["message"]
    assert health["suggested_models"] == ["openai/gpt-oss-120b"]


def test_provider_health_blocks_a_missing_key(monkeypatch):
    _wired(monkeypatch, cfg=_cfg(key=""))
    health = factory_pipeline.provider_health()
    assert health["usable"] is False
    assert "GROK_API_KEY" in health["message"]


def test_provider_health_treats_an_unreachable_probe_as_unverified(monkeypatch):
    _wired(monkeypatch)
    with patch("requests.get", side_effect=OSError("timeout")):
        health = factory_pipeline.provider_health()
    assert health["usable"] is True
    assert health["model_offered"] is None
    assert "OSError" in health["message"]


def test_preflight_publishes_provider_health(monkeypatch, tmp_path):
    _wired(monkeypatch)
    monkeypatch.setattr(factory_pipeline, "_npm", lambda: "npm")
    with patch("requests.get", return_value=_Response({"data": [{"id": "openai/gpt-oss-120b"}]})):
        info = factory_pipeline.preflight()
    assert info["provider"]["provider"] == "grok"
    assert info["provider"]["usable"] is True


# ── delivery refuses before touching the disk ────────────────────────────────

def test_deliver_refuses_before_creating_the_destination(monkeypatch, tmp_path):
    _wired(monkeypatch, cfg=_cfg(key=""))
    monkeypatch.setattr(factory_pipeline, "provider_health", lambda: {
        "provider": "grok", "model": "", "usable": False, "key_present": False,
        "message": "GROK_API_KEY is missing or still a placeholder",
    })
    events = []
    out = factory_pipeline.deliver_from_prompt(
        "Build CortexDesk, an AI copilot for support teams, deploy it and make a video",
        dest_root=str(tmp_path),
        progress=lambda event: events.append((event["stage"], event["status"])),
    )
    assert out["status"] == "failed"
    assert "GROK_API_KEY" in out["message"]
    assert ("generate", "blocked") in events
    assert not (tmp_path / "cortexdesk").exists()


def test_deliver_records_the_provider_it_generated_with(monkeypatch, tmp_path):
    _wired(monkeypatch)
    monkeypatch.setattr(factory_pipeline, "provider_health", lambda: {
        "provider": "grok", "model": "openai/gpt-oss-120b", "usable": True,
        "key_present": True, "model_offered": True, "available_models": 11, "message": "",
    })
    boom = SimpleNamespace(generate_project=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stop here")))
    monkeypatch.setattr("agent.fullstack_ultra_engine.FullStackUltraEngine", lambda: boom)
    with pytest.raises(RuntimeError):
        factory_pipeline.deliver_from_prompt(
            "Build CortexDesk, an AI copilot for support teams", dest_root=str(tmp_path),
        )
    assert (tmp_path / "cortexdesk").is_dir()


@pytest.mark.parametrize("model", ["llama-3.3-70b-versatile", "meta-llama/llama-3.2-11b-vision-preview"])
def test_retired_groq_ids_are_not_the_defaults(model):
    """Live-checked on 2026-10-27: both return model_not_found from api.groq.com."""
    from config import settings

    assert model != settings.GROK_MODEL
    assert model != settings.GROQ_VISION_MODEL
