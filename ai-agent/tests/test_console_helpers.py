"""Tests for the operator console helper endpoints.

The console is the operator's only view of which models actually answer, and
`open_result_dir` hands a path to the OS shell. Both need coverage: a false
"ready" badge sends builds to a dead provider, and an unvalidated path would let
a model reply launch Explorer anywhere on the machine.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import console as console_mod  # noqa: E402


class _StubProvider:
    """Provider stub that records whether it was actually called."""

    def __init__(self, name, ok=True, error="", text="ok"):
        self.name = name
        self._ok = ok
        self._error = error
        self._text = text
        self.calls = 0

    def generate_code(self, prompt, *args, **kwargs):
        self.calls += 1
        if not self._ok:
            raise RuntimeError(self._error)
        return self._text

    def is_available(self):
        return self._ok


class _StubRouter:
    def __init__(self, tiers, providers):
        self._tiers = tiers
        self._providers = providers

    def tier_names(self, tier):
        return list(self._tiers.get(tier, []))

    def provider_by_name(self, name):
        # Real contract: (instance, resolved_name, tier).
        provider = self._providers.get(name)
        if provider is None:
            return None, None, None
        return provider, name, "fast"


@pytest.fixture
def stub_router(monkeypatch):
    """Install a stub router so probes never touch a real provider or network."""
    providers = {
        "alpha": _StubProvider("alpha", text="alpha-ok"),
        "beta": _StubProvider("beta", ok=False, error="beta 401 invalid key"),
    }
    router = _StubRouter(
        {"fast": ["alpha", "beta"], "balanced": ["beta", "alpha"], "reasoning": ["alpha"]},
        providers,
    )
    monkeypatch.setattr(console_mod, "get_router", lambda *a, **k: router, raising=False)
    monkeypatch.setattr(
        "agent.ai_routing.get_router", lambda *a, **k: router, raising=False
    )
    return router


def test_probe_provider_calls_the_named_provider(stub_router):
    result = console_mod.probe_provider("alpha")
    assert result["ok"] is True
    assert result["called"] is True
    assert stub_router._providers["alpha"].calls == 1
    assert stub_router._providers["beta"].calls == 0


def test_probe_provider_reports_failure_reason(stub_router):
    result = console_mod.probe_provider("beta")
    assert result["ok"] is False
    assert result["called"] is False
    assert "401" in result["error"]


def test_probe_all_dedupes_across_tiers(stub_router):
    result = console_mod.probe_all()
    # alpha and beta each appear in more than one tier but must be probed once.
    assert result["probed"] == 2
    assert result["working"] == ["alpha"]
    assert stub_router._providers["alpha"].calls == 1
    assert stub_router._providers["beta"].calls == 1


def test_probe_all_result_rows_are_self_describing(stub_router):
    rows = console_mod.probe_all()["results"]
    by_name = {r["name"]: r for r in rows}
    assert set(by_name) == {"alpha", "beta"}
    assert by_name["alpha"]["ok"] is True
    assert by_name["beta"]["ok"] is False
    # Every row must be renderable by the page without extra lookups.
    for row in rows:
        assert "name" in row and "ok" in row and "called" in row


def test_probe_all_with_no_tier_names():
    router = _StubRouter({}, {})
    import agent.ai_routing as routing

    original = routing.get_router
    routing.get_router = lambda *a, **k: router
    try:
        result = console_mod.probe_all()
    finally:
        routing.get_router = original
    assert result == {"ok": True, "probed": 0, "working": [], "results": []}


class TestOpenResultDir:
    """`path` arrives from a model response, so it is untrusted input."""

    def test_rejects_path_outside_repo(self):
        result = console_mod.open_result_dir({"path": "C:\\Windows\\System32"})
        assert result["ok"] is False
        assert "inside the project root" in result["error"]

    def test_rejects_traversal_out_of_repo(self):
        root = console_mod.REPO_ROOT
        result = console_mod.open_result_dir({"path": os.path.join(root, "..", "..")})
        assert result["ok"] is False
        assert "inside the project root" in result["error"]

    def test_rejects_relative_path_that_escapes(self):
        result = console_mod.open_result_dir({"path": "..\\..\\Windows"})
        assert result["ok"] is False

    def test_rejects_missing_path(self):
        result = console_mod.open_result_dir({})
        assert result["ok"] is False
        assert "path is required" in result["error"]

    def test_rejects_folder_that_does_not_exist(self):
        target = os.path.join(console_mod.REPO_ROOT, "definitely-not-here-12345")
        result = console_mod.open_result_dir({"path": target})
        assert result["ok"] is False
        assert "does not exist" in result["error"]

    def test_opens_existing_folder_inside_repo(self, monkeypatch):
        opened = []
        monkeypatch.setattr(
            console_mod.os, "startfile", lambda p: opened.append(p), raising=False
        )
        target = console_mod.REPO_ROOT
        result = console_mod.open_result_dir({"path": target})
        assert result["ok"] is True
        assert result["path"] == os.path.abspath(target)
        assert opened == [os.path.abspath(target)]
