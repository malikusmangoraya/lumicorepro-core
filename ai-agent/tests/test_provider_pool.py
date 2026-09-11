"""Tests for the rotating ProviderPool — rate-limit fallback + cycle-back."""
import time
import pytest
from unittest.mock import patch


from providers.provider_pool import (
    ProviderPool,
    RATE_LIMIT_COOLDOWN,
    FAILURE_COOLDOWN,
)


class _FakeA:
    name = "A"
    def __init__(self, *a, **k): pass


class _FakeB:
    name = "B"
    def __init__(self, *a, **k): pass


def _fake_validate(name, require_key=True):
    return True


def _fake_instantiate(name):
    return _FakeA() if name == "grok" else _FakeB()


@pytest.fixture
def pool():
    with patch("config.providers.validate_provider_key", _fake_validate), \
         patch("config.providers.instantiate_provider", _fake_instantiate):
        p = ProviderPool(fallback_order=["grok", "gemini"])
        p._cooldowns.clear()
        yield p


def test_initial_provider_is_primary(pool):
    assert pool.get_current_name() == "grok"
    assert isinstance(pool.get_active(), _FakeA)


def test_rate_limit_rotates_to_next(pool):
    pool.mark_rate_limited("grok")
    assert pool.get_current_name() == "gemini"
    assert isinstance(pool.get_active(), _FakeB)


def test_all_rate_limited_cycles_back(pool):
    pool.mark_rate_limited("grok")
    pool.mark_rate_limited("gemini")
    # get_current_name picks shortest cooldown — should cycle back to grok
    assert pool.get_current_name() == "grok"
    inst = pool.get_active()
    assert inst is pool._providers["grok"]


def test_success_clears_cooldown(pool):
    pool.mark_rate_limited("grok")
    assert pool.get_current_name() == "gemini"
    pool.mark_success("grok")
    # grok available again — pool can cycle back when gemini rotates away
    assert pool.status()["grok"]["available"] is True


def test_failure_cooldown_next_provider(pool):
    pool.mark_failed("grok")
    assert pool.get_current_name() == "gemini"


def test_status_reports_cooldown(pool):
    pool.mark_rate_limited("grok")
    status = pool.status()
    assert status["grok"]["available"] is False
    assert status["grok"]["cooldown_remaining"] > 0
    assert status["gemini"]["available"] is True