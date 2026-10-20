"""Tests for the OpenCode CLI adapter (open-source coding agent, MIT).

OpenCode is a local CLI agent, so the adapter is a `subprocess` wrapper rather
than an HTTP client. These tests pin the wiring (a keyless, open-source provider
that joins the fallback chain) and the command/exit behaviour.
"""
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from providers.base_provider import BaseAIProvider
from providers.opencode_provider import OpenCodeProvider

import config.providers as provider_module
from config.providers import (
    FALLBACK_ORDER,
    PROVIDER_CONFIGS,
    instantiate_provider,
)


@pytest.fixture(autouse=True)
def _blank_opencode_env(monkeypatch):
    """No ambient OPENCODE_* config should leak into assertions."""
    for var in ("OPENCODE_BIN", "OPENCODE_MODEL", "OPENCODE_AGENT",
                "OPENCODE_DIR", "OPENCODE_ATTACH", "OPENCODE_TIMEOUT"):
        monkeypatch.delenv(var, raising=False)


# ── Registration / wiring ───────────────────────────────────────────────────
def test_opencode_is_registered_as_a_keyless_open_source_provider():
    config = PROVIDER_CONFIGS["opencode"]

    assert config["provider_name"] == "opencode"
    assert config["keyless"] is True
    assert config["open_source"] is True
    assert config["class_path"] == "providers.opencode_provider.OpenCodeProvider"


def test_opencode_joins_the_fallback_chain():
    assert "opencode" in FALLBACK_ORDER
    # `opencode` must not displace pollinations, which is pinned last by design
    # (keyless free tier = guaranteed last-resort, never in front of keyed tiers).
    assert FALLBACK_ORDER[-1] == "pollinations"
    assert FALLBACK_ORDER.index("opencode") < FALLBACK_ORDER.index("pollinations")


def test_opencode_hop_constructs_a_real_provider():
    provider = instantiate_provider("opencode")

    assert isinstance(provider, OpenCodeProvider)
    assert isinstance(provider, BaseAIProvider)


def test_opencode_provider_is_exported_from_the_providers_package():
    import providers

    assert providers.OpenCodeProvider is OpenCodeProvider
    assert "OpenCodeProvider" in providers.__all__


# ── Command construction ────────────────────────────────────────────────────
def test_build_args_defaults_to_a_bare_run():
    provider = OpenCodeProvider()

    assert provider.build_args("say hi") == ["run", "say hi"]


def test_build_args_includes_model_agent_and_dir_flags(monkeypatch):
    monkeypatch.setenv("OPENCODE_MODEL", "anthropic/claude-sonnet-4-5")
    monkeypatch.setenv("OPENCODE_AGENT", "build")
    monkeypatch.setenv("OPENCODE_DIR", "/tmp/work")
    provider = OpenCodeProvider()

    args = provider.build_args("fix the bug")

    assert args[0] == "run"
    assert args[-1] == "fix the bug"
    assert args[args.index("--model") + 1] == "anthropic/claude-sonnet-4-5"
    assert args[args.index("--agent") + 1] == "build"
    assert args[args.index("--dir") + 1] == "/tmp/work"


def test_windows_cmd_shim_is_launched_through_cmd():
    prefix = OpenCodeProvider._command_prefix("C:/tools/opencode.cmd")

    if os.name == "nt":
        assert prefix == ["cmd", "/c", "C:/tools/opencode.cmd"]
    else:
        assert prefix == ["C:/tools/opencode.cmd"]


# ── Runtime behaviour ───────────────────────────────────────────────────────
def test_missing_cli_fails_fast_as_a_connectivity_error():
    """A missing executable must rotate providers, not burn retries."""
    provider = OpenCodeProvider()

    with patch("providers.opencode_provider.shutil.which", return_value=None):
        with pytest.raises(ConnectionError, match="Cannot connect to OpenCode CLI"):
            provider._raw_call("hi")


def test_is_available_reflects_the_resolved_binary():
    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"):
        assert OpenCodeProvider.is_available() is True

    with patch("providers.opencode_provider.shutil.which", return_value=None):
        assert OpenCodeProvider.is_available() is False


def test_raw_call_returns_cli_stdout():
    provider = OpenCodeProvider()
    completed = MagicMock(returncode=0, stdout="print(1)\n", stderr="")

    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"), \
         patch("providers.opencode_provider.subprocess.run", return_value=completed) as run:
        assert provider._raw_call("write code") == "print(1)"

    invoked = run.call_args.args[0]
    assert invoked[0] == "/usr/bin/opencode"
    assert invoked[1] == "run"


def test_nonzero_exit_raises_with_the_stderr_detail():
    provider = OpenCodeProvider()
    completed = MagicMock(returncode=1, stdout="", stderr="provider not configured")

    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"), \
         patch("providers.opencode_provider.subprocess.run", return_value=completed):
        with pytest.raises(RuntimeError, match="provider not configured"):
            provider._raw_call("hi")


def test_timeout_is_reported_as_a_runtime_error():
    provider = OpenCodeProvider(timeout=1)

    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"), \
         patch("providers.opencode_provider.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="opencode", timeout=1)):
        with pytest.raises(RuntimeError, match="timed out"):
            provider._raw_call("hi")


def test_empty_output_raises_rather_than_returning_an_empty_string():
    provider = OpenCodeProvider()
    completed = MagicMock(returncode=0, stdout="   ", stderr="")

    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"), \
         patch("providers.opencode_provider.subprocess.run", return_value=completed):
        with pytest.raises(RuntimeError, match="no output"):
            provider._raw_call("hi")


# ── Honest availability reporting ───────────────────────────────────────────
def test_provider_status_hides_opencode_when_the_cli_is_absent():
    """A keyless adapter must not be advertised when its runtime is missing."""
    from config.providers import provider_status

    with patch("providers.opencode_provider.shutil.which", return_value=None):
        status = provider_status("opencode")

    assert status["constructor_ok"] is True
    assert status["local_ready"] is False
    assert status["configured"] is False


def test_provider_status_advertises_opencode_once_the_cli_exists():
    from config.providers import provider_status

    with patch("providers.opencode_provider.shutil.which", return_value="/usr/bin/opencode"):
        status = provider_status("opencode")

    assert status["local_ready"] is True
    assert status["configured"] is True
