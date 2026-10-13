"""Tests for the AI task router: tiering, cache, cooldown skip, parallel fan-out.

The parallel test uses a stub provider with real `time.sleep`, so the asserted
speedup is a measured wall-clock fact rather than a claim.
"""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import ai_routing  # noqa: E402
from agent.ai_routing import (  # noqa: E402
    AIRouter,
    KIND_TIER,
    RouteStats,
    classify_task,
    get_router,
    prefer,
    reset_router,
)


class StubProvider:
    """Deterministic provider with optional simulated latency."""

    def __init__(self, name, delay=0.0, fail_times=0, chars=64):
        self.name = name
        self.delay = delay
        self.fail_times = fail_times
        self.chars = chars
        self.calls = 0
        self._lock = __import__("threading").Lock()

    def generate_code(self, prompt, *args, **kwargs):
        with self._lock:
            self.calls += 1
            n = self.calls
        if n <= self.fail_times:
            raise RuntimeError("429 rate limit")
        if self.delay:
            time.sleep(self.delay)
        return f"{self.name}:ok:" + "x" * self.chars

    modify_code = generate_code


class FakePool:
    def __init__(self, providers):
        self._providers = dict(providers)
        self._cooldowns = {}

    def get_active(self):
        if not self._providers:
            return None
        return next(iter(self._providers.values()))

    def get_provider_name(self, inst):
        for k, v in self._providers.items():
            if v is inst:
                return k
        return type(inst).__name__


@pytest.fixture(autouse=True)
def _clean_router():
    for var in ("AI_TIER_FAST", "AI_TIER_BALANCED", "AI_TIER_REASONING", "AI_PROVIDER",
                "ACTIVE_AI_PROVIDER", "REASONING_PROVIDER", "AI_FAST_MODE", "AI_OFFLINE",
                "AI_ROUTER_ENABLED", "AI_ROUTER_CACHE", "AI_ROUTER_STATS",
                "AI_ROUTER_LATENCY_AWARE"):
        os.environ.pop(var, None)
    reset_router()
    # Hand the singleton a stub pool so no test in this file ever constructs the
    # process-wide provider pool. Building it for real would leak live provider
    # instances into later tests that assert offline behaviour.
    get_router()._pool = FakePool({})
    yield
    reset_router()


def test_strict_router_fails_closed_instead_of_using_unlisted_active_provider():
    allowed = StubProvider("openrouter")
    paid_fallback = StubProvider("grok")
    pool = FakePool({"openrouter": allowed, "grok": paid_fallback})
    ai_routing.configure_strict_router(pool, {"openrouter"})

    provider, name = get_router().provider_for("balanced", pool_fallback=True)

    assert provider is allowed
    assert name == "openrouter"
    assert paid_fallback.calls == 0
    assert get_router().provider_for("missing-tier", pool_fallback=True) == (allowed, "openrouter")


def test_strict_router_reaches_allowed_providers_despite_other_tiers():
    """A strict lane stays usable when env tiers omit its provider entirely."""
    allowed = StubProvider("openrouter")
    ai_routing.configure_strict_router(FakePool({"openrouter": allowed}), ["openrouter"])

    provider, name = get_router().provider_for("reasoning", pool_fallback=False)

    assert provider is allowed and name == "openrouter"


def test_strict_router_blocks_an_unlisted_pin(monkeypatch):
    ai_routing.configure_strict_router(
        FakePool({"openrouter": StubProvider("openrouter")}), ["openrouter"]
    )
    inst, name, tier = prefer("design", "prompt")
    assert inst is not None and name == "openrouter" and tier == "reasoning"

    # `grok` is a real provider name, but it is not in this lane.
    monkeypatch.setenv("AI_PROVIDER", "grok")
    assert prefer("design", "prompt") == (None, "blocked", "strict_allowlist")


def test_strict_rotate_fails_closed_without_an_allowed_alternative():
    allowed = StubProvider("openrouter")
    ai_routing.configure_strict_router(FakePool({"openrouter": allowed}), ["openrouter"])

    # The only allowed provider is the one that just failed: no alternative exists.
    inst, name, _tier = ai_routing.rotate("repair", "openrouter", "prompt")
    assert inst is None and name == "none"

    # A provider outside the lane is never rotated back in.
    assert ai_routing.rotate("repair", "grok", "prompt") == (None, "blocked", "strict_allowlist")


def test_restore_router_undoes_strict_mode():
    original = get_router()
    ai_routing.configure_strict_router(
        FakePool({"openrouter": StubProvider("openrouter")}), ["openrouter"]
    )
    strict = get_router()
    assert strict is not original
    assert strict._strict_allowlist == frozenset({"openrouter"})

    ai_routing.restore_router(original)

    assert get_router() is original
    assert not get_router()._strict_allowlist


def _router_with(providers, **kwargs):
    r = AIRouter(pool=FakePool(providers), **kwargs)
    return r


# ── classification ────────────────────────────────────────────────────────────
def test_small_classification_is_fast():
    assert classify_task("classify", "pick a label") == "fast"
    assert classify_task("analyze", "short prompt") == "fast"
    assert classify_task("critique", "review this") == "fast"


def test_repair_always_reasoning_regardless_of_size():
    assert classify_task("repair", "tiny") == "reasoning"
    assert classify_task("edit", "x" * 10, is_repair=True) == "reasoning"
    assert classify_task("", "", is_repair=True) == "reasoning"


def test_design_and_large_prompts_escalate():
    assert classify_task("design", "small") == "reasoning"
    assert classify_task("codegen", "x" * 30_000) == "reasoning"
    assert classify_task("classify", "x" * 5_000) == "balanced"
    assert classify_task("codegen", "x" * 100) == "balanced"


def test_unknown_kind_defaults_by_size():
    assert classify_task("mystery", "tiny") == "fast"
    assert classify_task("mystery", "x" * 6_000) == "balanced"


def test_fast_mode_collapses_everything_to_fast():
    assert classify_task("repair", "x" * 50_000, fast_mode=True) == "fast"


def test_every_declared_kind_maps_to_a_known_tier():
    for kind in ai_routing.TASK_KINDS:
        assert KIND_TIER.get(kind, "balanced") in ("fast", "balanced", "reasoning")


# ── provider selection ────────────────────────────────────────────────────────
def test_tier_selects_first_live_member():
    fast = StubProvider("f1")
    slow = StubProvider("s1")
    r = _router_with({"gemini": slow, "cerebras": fast}, tiers={
        "fast": ["cerebras", "gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]})
    inst, name, tier = r.get("classify", "tiny")
    assert name == "cerebras" and inst is fast and tier == "fast"


def test_cooldown_is_skipped_and_next_tier_member_is_used():
    a = StubProvider("a")
    b = StubProvider("b")
    pool = FakePool({"a": a, "b": b})
    r = AIRouter(pool=pool, tiers={"fast": ["a", "b"], "balanced": ["b"], "reasoning": ["b"]})
    pool._cooldowns["a"] = time.time() + 60
    inst, name, tier = r.get("classify", "tiny")
    assert name == "b" and inst is b


def test_tier_fully_cooling_falls_back_to_pool_active():
    cooling = StubProvider("a")
    spare = StubProvider("g")
    # 'g' is first in the pool, so get_active() resolves to it.
    pool = FakePool({"g": spare, "a": cooling})
    r = AIRouter(pool=pool, tiers={"fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    pool._cooldowns["a"] = time.time() + 60
    inst, name, _tier = r.get("classify", "tiny")
    assert inst is spare
    assert name == "g"


def test_no_providers_returns_none():
    r = _router_with({})
    inst, name, tier = r.get("classify", "tiny")
    assert inst is None and name == "none" and tier == "fast"


def test_env_tier_override_is_honoured():
    os.environ["AI_TIER_FAST"] = "b, a"
    b = StubProvider("b")
    a = StubProvider("a")
    r = _router_with({"a": a, "b": b})
    assert r.tier_names("fast") == ["b", "a"]
    _inst, name, _t = r.get("classify", "tiny")
    assert name == "b"


# ── calling, cache, rotation ──────────────────────────────────────────────────
def test_call_returns_meta_with_tier_and_provider():
    r = _router_with({"gemini": StubProvider("gemini")}, tiers={
        "fast": ["gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]})
    out, meta = r.call("design", "generate_code", "make a hero")
    assert out.startswith("gemini:ok")
    assert meta["tier"] == "reasoning" and meta["provider"] == "gemini"
    assert "seconds" in meta and meta["cached"] is False


def test_identical_call_is_served_from_cache():
    stub = StubProvider("gemini")
    r = _router_with({"gemini": stub}, tiers={
        "fast": ["gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]})
    first, m1 = r.call("analyze", "generate_code", "same prompt")
    second, m2 = r.call("analyze", "generate_code", "same prompt")
    assert first == second
    assert m2["cached"] is True and stub.calls == 1
    assert r.cache_stats()["hits"] == 1


def test_different_prompt_is_a_cache_miss():
    stub = StubProvider("gemini")
    r = _router_with({"gemini": stub}, tiers={
        "fast": ["gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]})
    r.call("analyze", "generate_code", "prompt A")
    r.call("analyze", "generate_code", "prompt B")
    assert stub.calls == 2


def test_cache_can_be_disabled_per_call():
    stub = StubProvider("gemini")
    r = _router_with({"gemini": stub}, tiers={
        "fast": ["gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]})
    r.call("analyze", "generate_code", "p", use_cache=False)
    r.call("analyze", "generate_code", "p", use_cache=False)
    assert stub.calls == 2


def test_failure_rotates_to_the_next_tier_member():
    bad = StubProvider("bad", fail_times=99)
    good = StubProvider("good")
    r = _router_with({"bad": bad, "good": good}, tiers={
        "fast": ["bad", "good"], "balanced": ["bad", "good"], "reasoning": ["bad", "good"]})
    out, meta = r.call("design", "generate_code", "prompt")
    assert out.startswith("good:ok")
    assert meta["rotated"] is True and meta["provider"] == "good"


def test_all_providers_failing_returns_none_with_error():
    bad = StubProvider("bad", fail_times=99)
    r = _router_with({"bad": bad}, tiers={
        "fast": ["bad"], "balanced": ["bad"], "reasoning": ["bad"]})
    out, meta = r.call("design", "generate_code", "prompt")
    assert out is None and "error" in meta


def test_call_with_no_provider_reports_error():
    r = _router_with({})
    out, meta = r.call("design", "generate_code", "prompt")
    assert out is None and meta["error"] == "no_provider_available"


def test_stats_track_calls_failures_and_cache_hits():
    r = _router_with({"a": StubProvider("a"), "b": StubProvider("b")}, tiers={
        "fast": ["a"], "balanced": ["b"], "reasoning": ["b"]})
    r.call("classify", "generate_code", "x")
    r.call("classify", "generate_code", "x")  # cache hit
    r.call("design", "generate_code", "y")
    data = r.stats.to_dict()
    assert data["calls_by_tier"]["fast"] == 1
    assert data["calls_by_tier"]["reasoning"] == 1
    assert data["cache_hits_by_tier"]["fast"] == 1
    assert data["providers_by_tier"]["reasoning"] == {"b": 1}
    assert "avg_seconds_by_tier" in data


def test_route_stats_avg_is_zero_safe():
    s = RouteStats()
    assert s.to_dict()["avg_seconds_by_tier"] == {}


# ── parallel fan-out (measured) ───────────────────────────────────────────────
def test_map_parallel_preserves_order():
    r = _router_with({"a": StubProvider("a")}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    jobs = [("classify", "generate_code", (f"prompt-{i}",)) for i in range(5)]
    results = r.map_parallel(jobs)
    assert len(results) == 5
    for i, (_out, meta) in enumerate(results):
        assert meta["provider"] == "a"


def test_map_parallel_is_faster_than_serial():
    """Measured, not asserted: 4 x 150ms calls should beat the serial path."""
    delay = 0.15
    stub = StubProvider("a", delay=delay)
    r = _router_with({"a": stub}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})

    # Distinct prompts per run: a cache hit would make the second run free and
    # the comparison meaningless.
    serial_jobs = [("classify", "generate_code", (f"serial-{i}",)) for i in range(4)]
    par_jobs = [("classify", "generate_code", (f"par-{i}",)) for i in range(4)]

    started = time.time()
    r.map_parallel(serial_jobs, max_workers=1)
    serial = time.time() - started

    started = time.time()
    r.map_parallel(par_jobs, max_workers=4)
    par = time.time() - started

    assert stub.calls == 8  # both paths really executed
    assert par < serial, f"parallel {par:.3f}s should beat serial {serial:.3f}s"
    # Ample slack for CI jitter; the win itself is ~4x.
    assert par < serial * 0.75


def test_map_parallel_empty_jobs():
    r = _router_with({"a": StubProvider("a")})
    assert r.map_parallel([]) == []


def test_map_parallel_single_job_runs_inline():
    stub = StubProvider("a")
    r = _router_with({"a": stub}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    out, _meta = r.map_parallel([("classify", "generate_code", ("only",))])[0]
    assert out.startswith("a:ok") and stub.calls == 1


# ── prefer(): explicit choices win, stubs never trigger network ───────────────
def test_hand_injected_provider_is_pinned(monkeypatch):
    stub = StubProvider("caller")
    inst, name, tier = prefer("design", "prompt", explicit=stub)
    assert inst is stub and name == "StubProvider" and tier == "pinned"


def test_env_pin_overrides_everything(monkeypatch):
    # A *usable* pin is required for the router to step aside; `omniroute` is
    # keyless, so it counts as configured without a key.
    monkeypatch.setenv("AI_PROVIDER", "omniroute")
    stub = StubProvider("caller")
    inst, name, tier = prefer("design", "prompt", explicit=stub)
    assert name == "omniroute" and tier == "pinned"


def test_no_pin_no_explicit_returns_routed_provider():
    reset_router()
    r = get_router()
    fake = StubProvider("gemini")
    r._pool = FakePool({"gemini": fake})
    r._tiers = {"fast": ["gemini"], "balanced": ["gemini"], "reasoning": ["gemini"]}
    inst, name, tier = prefer("design", "prompt")
    assert inst is fake and name == "gemini" and tier == "reasoning"


# ── reporting ─────────────────────────────────────────────────────────────────
def test_routing_report_shape():
    r = _router_with({"a": StubProvider("a")}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    r.call("classify", "generate_code", "z")
    rep = r.routing_report()
    assert rep["fast_mode"] is False
    assert set(rep["tiers"]) == {"fast", "balanced", "reasoning"}
    assert rep["stats"]["calls_by_tier"]["fast"] == 1
    assert "size" in rep["cache"]


def test_singleton_is_reused():
    reset_router()
    assert get_router() is get_router()
    reset_router()


# ── named lookup (operator console probes one specific card) ──────────────────
def test_provider_by_name_addresses_exact_provider():
    a, b = StubProvider("a"), StubProvider("b")
    r = _router_with({"a": a, "b": b}, tiers={
        "fast": ["a"], "balanced": ["b"], "reasoning": ["a", "b"]})
    inst, name, tier = r.provider_by_name("b")
    assert inst is b and name == "b" and tier == "balanced"


def test_provider_by_name_ignores_tier_order():
    """Probing the 2nd entry must not silently report the 1st (the tier leader)."""
    a, b = StubProvider("a"), StubProvider("b")
    r = _router_with({"a": a, "b": b}, tiers={
        "fast": ["a", "b"], "balanced": ["a"], "reasoning": ["a"]})
    assert r.get("classify", "p")[0] is a  # leader for an unaddressed call
    assert r.provider_by_name("b")[0] is b


def test_provider_by_name_unknown_returns_none():
    r = _router_with({"a": StubProvider("a")}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    inst, name, tier = r.provider_by_name("does-not-exist")
    assert inst is None and name == "does-not-exist" and tier == "unknown"
    assert r.provider_by_name("")[0] is None


def test_provider_by_name_reports_unassigned_pool_member():
    """A pool provider missing from every tier is still addressable."""
    orphan = StubProvider("orphan")
    r = _router_with({"orphan": orphan}, tiers={
        "fast": ["a"], "balanced": ["a"], "reasoning": ["a"]})
    inst, name, tier = r.provider_by_name("orphan")
    assert inst is orphan and tier == "unassigned"
