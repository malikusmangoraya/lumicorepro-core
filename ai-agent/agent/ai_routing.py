"""
AI Task Router — LumicorePro AI Agent
=====================================
Makes the pipeline *measurably* faster and stronger by routing every AI call to
the cheapest model that is actually adequate for that job, instead of sending
design work and throwaway classification to the same model.

What this genuinely buys (and what it does not):
  - it cannot make any model faster; it reduces total work.

Four real levers, all implemented here:

1. **Tiering** - every call is classified into `fast` / `balanced` / `reasoning`
   from its task kind, prompt size and whether it is a repair. Small
   classification/critique work goes to a fast model; compiler-error repair and
   bespoke design go to a strong reasoner. A weak model stops being asked
   architecture questions, and an expensive reasoner stops being asked to
   rename a variable.
2. **Parallel fan-out** - `map_parallel` runs independent calls concurrently
   (AI_COMBINE_TASKS collapses the *prompt*; this collapses the *wall clock*).
3. **Dedupe cache** - identical (tier, method, prompt) calls are memoised on a
   content hash, so re-entered prompts and repeated self-heal targets cost
   nothing the second time.
4. **Fail-fast, no dead ends** - tier members on cooldown are skipped; a call
   rotates down the tier list once, then falls through to the global pool.

This module is the ONE place that decides which provider serves a call. The
orchestrator resolves its provider through `prefer()` and rotates through
`rotate()`; it never calls `ProviderPool.get_active()` itself. Tier choice,
explicit pins, offline mode, cooldowns/circuit breakers and the EWMA latency
ranking all live here, so there is exactly one routing implementation.

Configuration (all optional, env):
  AI_TIER_FAST       = "openmuse,grok,gemini,ninerouter"
  AI_TIER_BALANCED   = "gemini,openai,kimi,openrouter,mistral"
  AI_TIER_REASONING  = "kimi,openai,grok,gemini,openmuse"
  AI_FAST_MODE       = 1        # force every call onto the fast tier
  AI_ROUTER_CACHE    = 1        # 0 disables the dedupe cache
  AI_ROUTER_PARALLEL = 6        # default fan-out width
  AI_ROUTER_STATS    = 1        # per-tier call/latency counters
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils.logger import agent_logger

TIERS: Tuple[str, ...] = ("fast", "balanced", "reasoning")

# Task kinds the pipeline actually issues. Unknown kinds degrade to `balanced`.
TASK_KINDS = (
    "analyze",     # prompt -> spec JSON            (requirement_analyzer)
    "classify",    # tiny labels / routing decisions
    "critique",    # measurable review of rendered output
    "research",    # reference/benchmark lookups
    "plan",        # architecture + page plan
    "design",      # bespoke visual design (Phase 5.5)
    "codegen",     # write new files
    "edit",        # modify one existing file
    "repair",      # fix a build/lint/compiler error
    "vision",      # screenshot / image understanding
)

# Prompt sizes (chars) that force an upgrade, independent of task kind.
_BALANCED_MIN_CHARS = 4_000
_REASONING_MIN_CHARS = 24_000

# Default tier membership. The first entry of each tier is its preferred model.
# A local `openmuse` entry keeps the last tier honest offline: when every hosted
# provider is rate-limited, an air-gapped build still gets real work done.
DEFAULT_TIERS: Dict[str, List[str]] = {
    "fast": ["ninerouter", "omniroute", "grok", "gemini", "openmuse"],
    "balanced": ["gemini", "openai", "kimi", "openrouter", "mistral", "openmuse"],
    "reasoning": ["kimi", "openai", "grok", "gemini", "openrouter", "openmuse"],
}

# Task kind -> default tier, before size/prompt upgrades.
KIND_TIER: Dict[str, str] = {
    "classify": "fast",
    "analyze": "fast",
    "critique": "fast",
    "research": "fast",
    "vision": "fast",
    "edit": "balanced",
    "codegen": "balanced",
    "plan": "balanced",
    "design": "reasoning",
    "repair": "reasoning",
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except (TypeError, ValueError):
        return default


def _tier_order() -> List[str]:
    return list(TIERS)


def classify_task(
    task_kind: str = "",
    prompt: str = "",
    *,
    is_repair: bool = False,
    fast_mode: bool = False,
) -> str:
    """Pick the cheapest tier that is still adequate for this call.

    Precedence: repair wins over everything, then explicit kind, then prompt
    size. `fast_mode` collapses every decision onto the fast tier, which is how
    the pipeline trades quality for latency on an explicit request.
    """
    if fast_mode or _env_flag("AI_FAST_MODE"):
        return "fast"

    size = len(prompt or "")
    if is_repair or task_kind == "repair":
        # A failed build is the one job where a wrong answer costs a whole loop.
        return "reasoning"

    kind = (task_kind or "").strip().lower()
    tier = KIND_TIER.get(kind)
    if tier is None:
        tier = "balanced" if size >= _BALANCED_MIN_CHARS else "fast"

    if size >= _REASONING_MIN_CHARS and tier != "reasoning":
        tier = "reasoning"
    elif size >= _BALANCED_MIN_CHARS and tier == "fast":
        tier = "balanced"
    return tier


@dataclass
class RouteStats:
    """Per-tier telemetry so speed claims can be checked, not asserted."""

    calls: Dict[str, int] = field(default_factory=dict)
    failures: Dict[str, int] = field(default_factory=dict)
    cache_hits: Dict[str, int] = field(default_factory=dict)
    total_seconds: Dict[str, float] = field(default_factory=dict)
    chosen: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def record(self, tier: str, provider: str, seconds: float) -> None:
        self.calls[tier] = self.calls.get(tier, 0) + 1
        self.total_seconds[tier] = round(self.total_seconds.get(tier, 0.0) + seconds, 3)
        self.chosen.setdefault(tier, {})
        self.chosen[tier][provider] = self.chosen[tier].get(provider, 0) + 1

    def record_failure(self, tier: str) -> None:
        self.failures[tier] = self.failures.get(tier, 0) + 1

    def record_cache_hit(self, tier: str) -> None:
        self.cache_hits[tier] = self.cache_hits.get(tier, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calls_by_tier": dict(self.calls),
            "failures_by_tier": dict(self.failures),
            "cache_hits_by_tier": dict(self.cache_hits),
            "providers_by_tier": {k: dict(v) for k, v in self.chosen.items()},
            "avg_seconds_by_tier": {
                tier: round(self.total_seconds.get(tier, 0.0) / self.calls[tier], 3)
                for tier in self.calls
                if self.calls.get(tier)
            },
        }


# ── latency-aware selection ─────────────────────────────────────────────────

# Per-provider performance sample. EWMA keeps the estimate responsive to a
# provider that has suddenly slowed down without letting one fast call erase a
# long history of slowness.
@dataclass
class ProviderPerf:
    name: str
    ewma_latency: float = 0.0
    samples: int = 0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    last_used: float = 0.0
    circuit_open: bool = False
    circuit_opened_at: float = 0.0

    @property
    def quality(self) -> float:
        total = self.successes + self.failures
        return self.successes / total if total else 1.0

    @property
    def p95(self) -> float:
        # EWMA is a mean; p95 ≈ mean * 1.65 for a roughly normal tail. This is
        # an estimate, reported as such — not a measured percentile.
        return self.ewma_latency * 1.65 if self.samples else 0.0

    def record(self, seconds: float, success: bool, alpha: float) -> None:
        self.samples += 1
        self.last_used = time.time()
        if success:
            self.successes += 1
            self.consecutive_failures = 0
            self.circuit_open = False
        else:
            self.failures += 1
            self.consecutive_failures += 1
        if self.samples == 1:
            self.ewma_latency = seconds
        else:
            self.ewma_latency = alpha * seconds + (1 - alpha) * self.ewma_latency

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ewma_latency_ms": round(self.ewma_latency * 1000, 1),
            "p95_ms_est": round(self.p95 * 1000, 1),
            "samples": self.samples,
            "quality": round(self.quality, 3),
            "consecutive_failures": self.consecutive_failures,
            "circuit_open": self.circuit_open,
        }


class LatencyTracker:
    """Tracks per-provider latency + quality so routing picks the fastest
    *capable* model, not just the first configured one.

    "Capable" is derived from tier membership (a provider must be in the tier
    for the task kind) plus a measured quality floor. A fast provider that
    fails half its calls is not capable, however low its latency.
    """

    def __init__(self) -> None:
        # RLock: rank() holds the lock while sort_key() re-enters is_available().
        self._lock = threading.RLock()
        self._perf: Dict[str, ProviderPerf] = {}
        self.alpha = self._env_float("AI_ROUTER_EWMA_ALPHA", 0.3)
        self.max_latency_ms = self._env_float("AI_ROUTER_MAX_LATENCY_MS", 0)
        self.min_quality = self._env_float("AI_ROUTER_MIN_QUALITY", 0.5)
        self.circuit_threshold = self._env_int("AI_ROUTER_CIRCUIT_THRESHOLD", 3)
        self.circuit_cooldown_s = self._env_int("AI_ROUTER_CIRCUIT_COOLDOWN_S", 60)
        self.enabled = _env_flag("AI_ROUTER_LATENCY_AWARE", True)

    @staticmethod
    def _env_float(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, "") or default)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _env_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, "") or default)
        except (TypeError, ValueError):
            return default

    def perf(self, name: str) -> ProviderPerf:
        with self._lock:
            if name not in self._perf:
                self._perf[name] = ProviderPerf(name=name)
            return self._perf[name]

    def record(self, name: str, seconds: float, success: bool) -> None:
        with self._lock:
            p = self.perf(name)
            p.record(seconds, success, self.alpha)
            if (
                self.circuit_threshold > 0
                and p.consecutive_failures >= self.circuit_threshold
                and not p.circuit_open
            ):
                p.circuit_open = True
                p.circuit_opened_at = time.time()

    def is_available(self, name: str, now: Optional[float] = None) -> bool:
        with self._lock:
            p = self._perf.get(name)
            if p is None:
                return True
            if not p.circuit_open:
                return True
            now = now or time.time()
            if now - p.circuit_opened_at >= self.circuit_cooldown_s:
                p.circuit_open = False
                p.consecutive_failures = 0
                return True
            return False

    def capable(self, name: str) -> bool:
        with self._lock:
            p = self._perf.get(name)
            if p is None:
                return True
            return p.quality >= self.min_quality

    def within_latency(self, name: str) -> bool:
        if not self.max_latency_ms:
            return True
        with self._lock:
            p = self._perf.get(name)
            if p is None or not p.samples:
                return True
            return (p.ewma_latency * 1000) <= self.max_latency_ms

    def rank(self, names: Sequence[str]) -> List[str]:
        """Order `names` fastest-first among capable, healthy providers.

        Providers with no samples keep their configured order (they are tried
        first, so latency data is gathered). A provider with samples is ranked
        by EWMA latency; a provider that is circuit-open, below the quality
        floor, or over the latency cap is pushed to the end but never dropped,
        so a tier with one slow member still has a fallback.
        """
        now = time.time()
        with self._lock:
            def sort_key(name: str):
                p = self._perf.get(name)
                if p is None or not p.samples:
                    return (0, 0.0, names.index(name) if name in names else 99)
                healthy = self.is_available(name, now)
                ok = healthy and self.capable(name) and self.within_latency(name)
                return (0 if ok else 1, p.ewma_latency, names.index(name) if name in names else 99)
            return sorted(names, key=sort_key)

    def report(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "ewma_alpha": self.alpha,
                "max_latency_ms": self.max_latency_ms or None,
                "min_quality": self.min_quality,
                "circuit_threshold": self.circuit_threshold,
                "providers": {n: p.to_dict() for n, p in self._perf.items()},
            }


ROUTER_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".router.json")


def _tiers_from_file() -> Optional[Dict[str, List[str]]]:
    """Tier membership saved by the console page, if the file exists.

    Precedence: `AI_TIER_*` env wins, then this file, then the built-in defaults.
    """
    import json

    try:
        with open(ROUTER_CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    resolved: Dict[str, List[str]] = {}
    for tier in TIERS:
        names = data.get(tier)
        if isinstance(names, list):
            clean = [str(n).strip().lower() for n in names if str(n).strip()]
            if clean:
                resolved[tier] = clean
    return resolved or None


class AIRouter:
    """Routes AI calls to an adequate, live, and cheap-enough provider."""

    _instance: Optional["AIRouter"] = None
    _instance_lock = threading.Lock()

    def __init__(self, pool: Any = None, tiers: Optional[Dict[str, List[str]]] = None):
        self._lock = threading.Lock()
        self._pool = pool
        self._tiers = tiers or self._tiers_from_env()
        self._instances: Dict[str, Any] = {}
        self._cache: Dict[str, str] = {}
        self._cache_lock = threading.Lock()
        self.stats = RouteStats()
        self._latency = LatencyTracker()
        self.parallelism = max(1, _env_int("AI_ROUTER_PARALLEL", 6))
        self._cache_enabled = _env_flag("AI_ROUTER_CACHE", True)
        self._stats_enabled = _env_flag("AI_ROUTER_STATS", True)
        self._fast_mode = _env_flag("AI_FAST_MODE")

    # ── construction ────────────────────────────────────────────────────────
    @staticmethod
    def _tiers_from_env() -> Dict[str, List[str]]:
        from_file = _tiers_from_file() or {}
        resolved: Dict[str, List[str]] = {}
        for tier in TIERS:
            raw = os.getenv(f"AI_TIER_{tier.upper()}", "")
            names = [n.strip().lower() for n in raw.split(",") if n.strip()]
            resolved[tier] = names or from_file.get(tier) or list(DEFAULT_TIERS[tier])
        return resolved

    @classmethod
    def instance(cls) -> "AIRouter":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._instance_lock:
            cls._instance = None

    @property
    def tiers(self) -> Dict[str, List[str]]:
        """Current tier membership (env, then .router.json, then defaults)."""
        return {tier: self.tier_names(tier) for tier in TIERS}

    def pool(self) -> Any:
        if self._pool is None:
            from providers.provider_pool import get_pool

            self._pool = get_pool()
        return self._pool

    # ── provider resolution ─────────────────────────────────────────────────
    def tier_names(self, tier: str) -> List[str]:
        return list(self._tiers.get(tier) or self._tiers.get("balanced") or [])

    def _usable(self, name: str, cooling: Dict[str, Any], now: float) -> Optional[Any]:
        """The live instance for `name` if it is not cooling down or circuit-open.

        Single place where "may this provider serve a call right now?" is
        decided, so primary selection and post-failure rotation cannot drift
        apart (rotation must never land back on the provider that just failed).
        """
        inst = self._instances.get(name) or (getattr(self.pool(), "_providers", {}) or {}).get(name)
        if inst is None:
            return None
        # pool cooldown semantics: an entry is usable once `now >= until`
        if name in cooling and now < float(cooling[name]):
            return None
        if self._latency.enabled and not self._latency.is_available(name, now):
            return None
        return inst

    def provider_for(
        self,
        tier: str,
        exclude: Sequence[str] = (),
        *,
        pool_fallback: bool = True,
    ) -> Tuple[Optional[Any], str]:
        """Return (instance, name) for a tier, skipping providers on cooldown.

        When latency-aware routing is on, tier members are tried fastest-first
        among those that are healthy, capable and within the latency cap. The
        configured order is the tie-breaker for providers with no samples yet.

        `exclude` drops names entirely (used by retry rotation). With
        `pool_fallback=False` an exhausted list returns `(None, "none")` instead
        of the pool's current provider — a rotation must not silently retry the
        provider that just failed.
        """
        pool = self.pool()
        cooling: Dict[str, Any] = getattr(pool, "_cooldowns", {}) or {}
        now = time.time()

        names = [n for n in self.tier_names(tier) if n not in set(exclude)]
        if self._latency.enabled:
            names = self._latency.rank(names)

        for name in names:
            inst = self._usable(name, cooling, now)
            if inst is None:
                continue
            self._instances[name] = inst
            return inst, name

        if not pool_fallback:
            return None, "none"

        # Everything in the tier is unavailable: hand back the pool's live choice
        # rather than failing the call.
        inst = pool.get_active() if pool else None
        if inst is not None:
            return inst, pool.get_provider_name(inst) or type(inst).__name__
        return None, "none"

    def provider_by_name(self, name: str) -> Tuple[Optional[Any], str, str]:
        """(instance, name, tier) for one *specific* provider, ignoring tier order.

        Needed by anything that addresses a provider directly (the operator
        console's per-card probe, diagnostics). Returns a `None` instance when
        the provider is unknown or has no usable instance, and reports the tier
        it belongs to so the caller can label the result.
        """
        wanted = (name or "").strip().lower()
        if not wanted:
            return None, "none", "none"
        for tier in TIERS:
            for candidate in self.tier_names(tier):
                if candidate.lower() != wanted:
                    continue
                pool = self.pool()
                live: Dict[str, Any] = getattr(pool, "_providers", {}) or {}
                inst = self._instances.get(candidate) or live.get(candidate)
                if inst is not None:
                    self._instances[candidate] = inst
                return inst, candidate, tier
        # Known to the pool but absent from every tier: still addressable.
        pool = self.pool()
        live = getattr(pool, "_providers", {}) or {}
        for candidate, inst in live.items():
            if candidate.lower() == wanted:
                return inst, candidate, "unassigned"
        return None, wanted, "unknown"

    def get(self, task_kind: str = "", prompt: str = "", *, is_repair: bool = False) -> Tuple[Optional[Any], str, str]:
        """(provider, provider_name, tier) for a call — no network happens here."""
        tier = classify_task(task_kind, prompt, is_repair=is_repair, fast_mode=self._fast_mode)
        inst, name = self.provider_for(tier)
        return inst, name, tier

    # ── cache ───────────────────────────────────────────────────────────────
    def _cache_key(self, tier: str, method: str, payload: Sequence[Any]) -> str:
        digest = hashlib.sha256()
        digest.update(f"{tier}|{method}|".encode("utf-8", "replace"))
        for item in payload:
            digest.update(repr(item).encode("utf-8", "replace")[:20_000])
            digest.update(b"\x00")
        return digest.hexdigest()

    def cache_stats(self) -> Dict[str, int]:
        return {"size": len(self._cache), "hits": sum(self.stats.cache_hits.values())}

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    # ── calling ─────────────────────────────────────────────────────────────
    def call(
        self,
        task_kind: str,
        method: str,
        *args: Any,
        is_repair: bool = False,
        use_cache: Optional[bool] = None,
        **kwargs: Any,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Call `method` on an adequate provider, with cache + one rotation.

        Returns `(result, meta)` where meta carries tier/provider/duration/cache so
        callers and the report layer can show what actually happened.
        """
        prompt_hint = next((a for a in args if isinstance(a, str) and len(a) > 200), "")
        inst, name, tier = self.get(task_kind, prompt_hint, is_repair=is_repair)
        meta: Dict[str, Any] = {
            "tier": tier,
            "provider": name,
            "method": method,
            "cached": False,
            "rotated": False,
        }
        if inst is None:
            meta["error"] = "no_provider_available"
            if self._stats_enabled:
                self.stats.record_failure(tier)
            return None, meta

        wants_cache = self._cache_enabled if use_cache is None else use_cache
        key = self._cache_key(tier, method, list(args) + list(kwargs.values())) if wants_cache else ""
        if key:
            with self._cache_lock:
                hit = self._cache.get(key)
            if hit is not None:
                meta["cached"] = True
                if self._stats_enabled:
                    self.stats.record_cache_hit(tier)
                return hit, meta

        started = time.time()
        try:
            result = getattr(inst, method)(*args, **kwargs)
        except Exception as exc:
            if self._stats_enabled:
                self.stats.record_failure(tier)
            if self._latency.enabled:
                self._latency.record(name, time.time() - started, False)
            # One rotation down the tier list, then out to the pool.
            alt = self._rotate(tier, exclude=name)
            if alt is not None:
                alt_inst, alt_name = alt
                meta["rotated"] = True
                try:
                    result = getattr(alt_inst, method)(*args, **kwargs)
                    meta["provider"] = alt_name
                    if self._latency.enabled:
                        self._latency.record(alt_name, time.time() - started, True)
                except Exception as exc2:
                    meta["error"] = f"{exc}; rotation failed: {exc2}"
                    if self._latency.enabled:
                        self._latency.record(alt_name, time.time() - started, False)
                    return None, meta
            else:
                meta["error"] = str(exc)
                return None, meta

        duration = time.time() - started
        meta["seconds"] = round(duration, 3)
        if self._stats_enabled:
            self.stats.record(tier, meta["provider"], duration)
        if self._latency.enabled:
            self._latency.record(meta["provider"], duration, True)
        if key and isinstance(result, str) and result.strip():
            with self._cache_lock:
                self._cache[key] = result
        return result, meta

    def _rotate(self, tier: str, exclude: str = "") -> Optional[Tuple[Any, str]]:
        """Next healthy tier member after `exclude` (same decision as `provider_for`)."""
        inst, name = self.provider_for(
            tier, exclude=(exclude,) if exclude else (), pool_fallback=False
        )
        if inst is None:
            return None
        return inst, name

    # ── fan-out ─────────────────────────────────────────────────────────────
    def map_parallel(
        self,
        jobs: Sequence[Tuple[str, str, tuple]],
        max_workers: Optional[int] = None,
    ) -> List[Tuple[Any, Dict[str, Any]]]:
        """Run independent `(task_kind, method, args)` jobs concurrently.

        Order is preserved, so callers can keep positional correspondence with
        the job list. This is the wall-clock win: ten independent 3s calls take
        ~3s here instead of ~30s serially.
        """
        if not jobs:
            return []
        workers = max(1, min(max_workers or self.parallelism, len(jobs)))
        if workers == 1 or len(jobs) == 1:
            return [self.call(kind, method, *args) for kind, method, args in jobs]

        started = time.time()
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ai-router") as pool:
            futures = [pool.submit(self.call, kind, method, *args) for kind, method, args in jobs]
            results = [f.result() for f in futures]
        elapsed = time.time() - started
        if self._stats_enabled:
            self.stats.record("parallel", f"{workers}w", elapsed)
        return results

    # ── reporting ───────────────────────────────────────────────────────────
    def routing_report(self) -> Dict[str, Any]:
        """Human-readable summary of where work went (used by the CLI/report)."""
        report: Dict[str, Any] = {
            "fast_mode": self._fast_mode,
            "cache_enabled": self._cache_enabled,
            "parallelism": self.parallelism,
            "tiers": {t: self.tier_names(t) for t in _tier_order()},
        }
        if self._stats_enabled:
            report["stats"] = self.stats.to_dict()
            report["cache"] = self.cache_stats()
        if self._latency.enabled:
            report["latency"] = self._latency.report()
        return report


_router: Optional[AIRouter] = None
_router_lock = threading.Lock()


def get_router() -> AIRouter:
    """Process-wide router singleton."""
    global _router
    with _router_lock:
        if _router is None:
            _router = AIRouter()
        return _router


def reset_router() -> None:
    global _router
    with _router_lock:
        _router = None
    AIRouter.reset()


def offline() -> bool:
    """`AI_OFFLINE=1` forces every AI entry point to no-provider (local-first).

    This is a real product switch (air-gapped builds, deterministic reruns) and
    it is also what makes offline tests hermetic: no provider is resolved, so no
    hosted call can happen and no timing can vary between runs.
    """
    return _env_flag("AI_OFFLINE", False)


def enabled() -> bool:
    """Master switch. `AI_ROUTER_ENABLED=0` restores pre-router behaviour."""
    return _env_flag("AI_ROUTER_ENABLED", True) and not offline()


def route(task_kind: str = "", prompt: str = "", *, is_repair: bool = False) -> Tuple[Optional[Any], str, str]:
    """Convenience wrapper: `(provider, provider_name, tier)`."""
    if offline():
        return None, "offline", "offline"
    if not enabled():
        try:
            from providers.provider_pool import get_pool

            pool = get_pool()
            inst = pool.get_active()
            return inst, (pool.get_provider_name(inst) if inst else "none"), "disabled"
        except Exception:
            return None, "none", "disabled"
    return get_router().get(task_kind, prompt, is_repair=is_repair)


def call(task_kind: str, method: str, *args: Any, **kwargs: Any) -> Tuple[Any, Dict[str, Any]]:
    """Convenience wrapper around `AIRouter.call`."""
    return get_router().call(task_kind, method, *args, **kwargs)


def map_parallel(jobs: Sequence[Tuple[str, str, tuple]], max_workers: Optional[int] = None):
    """Convenience wrapper around `AIRouter.map_parallel`."""
    return get_router().map_parallel(jobs, max_workers=max_workers)


def _pinned(pin: Optional[str] = None) -> Optional[str]:
    """Name of a provider the user explicitly chose, if any.

    An explicit `AI_PROVIDER` / `ACTIVE_AI_PROVIDER` / `REASONING_PROVIDER` (or a
    caller-supplied `pin`, e.g. the API's `provider` field) is a deliberate
    decision, so the router steps aside instead of second-guessing it.
    """
    candidates = [pin] if pin else []
    candidates += [
        os.getenv("AI_PROVIDER"),
        os.getenv("ACTIVE_AI_PROVIDER"),
        os.getenv("REASONING_PROVIDER"),
    ]
    for raw in candidates:
        name = (raw or "").strip().lower()
        if name and name not in ("auto", "none"):
            return name
    return None


def _is_real_provider(explicit: Any) -> bool:
    """True when `explicit` is a genuine `BaseAIProvider` instance.

    Every shipped provider (gateway, Gemini, OpenAI, Mistral, Kimi, OpenMuse)
    subclasses `BaseAIProvider`, while a hand-injected stub used by a caller or
    a unit test does not. Deciding on the type — rather than asking the pool —
    means this check can never construct the process-wide provider pool, which
    would leak live instances into unrelated offline tests.
    """
    if explicit is None:
        return False
    try:
        from providers.base_provider import BaseAIProvider

        return isinstance(explicit, BaseAIProvider)
    except Exception:  # pragma: no cover - import failure means "not real"
        return False


def _pool_managed(explicit: Any) -> bool:
    """True when `explicit` is one of the pool's live providers."""
    if explicit is None:
        return False
    try:
        # Consult the active router's own pool first: a router that was handed
        # a pool must never reach for (and construct) the process-wide one.
        pool = None
        try:
            pool = get_router()._pool
        except Exception:
            pool = None
        if pool is None:
            from providers.provider_pool import get_pool

            pool = get_pool()
        managed = getattr(pool, "_providers", {}) or {}
        return any(inst is explicit for inst in managed.values())
    except Exception:  # pragma: no cover - pool unavailable means "not managed"
        return False


def prefer(
    task_kind: str,
    prompt: str = "",
    *,
    is_repair: bool = False,
    explicit: Any = None,
    pin: Optional[str] = None,
) -> Tuple[Optional[Any], str, str]:
    """Provider to use for this call, honouring explicit choices.

    Precedence:
      1. a pin (`pin` argument, else `AI_PROVIDER`/`ACTIVE_AI_PROVIDER`/
         `REASONING_PROVIDER`) that resolves to a *usable* provider -> `"pinned"`
      2. a hand-injected `explicit` instance (not a real provider) -> `"pinned"`
      3. otherwise the routed tier provider, with `explicit` as fallback

    A pin whose key is missing or whose name is unknown is NOT silently used: it
    would make the run look model-served while every call fails. It is logged and
    the call falls through to routing (where the offline path is reported
    honestly).

    Returns `(provider, provider_name, tier)`.
    """
    pinned = _pinned(pin)
    if pinned:
        if _pin_is_usable(pinned):
            from config.providers import instantiate_provider

            inst = explicit or instantiate_provider(pinned)
            if inst is not None:
                return inst, pinned, "pinned"
        agent_logger.warning(
            "[ROUTER] pinned provider '%s' is not usable (missing key or no constructor) "
            "— routing instead",
            pinned,
        )

    if offline():
        return None, "offline", "offline"

    if not enabled():
        if explicit is not None:
            return explicit, type(explicit).__name__, "disabled"
        inst, name, _tier = route(task_kind, prompt, is_repair=is_repair)
        return inst, name, "disabled"

    if explicit is not None and not _is_real_provider(explicit):
        return explicit, type(explicit).__name__, "pinned"

    inst, name, tier = route(task_kind, prompt, is_repair=is_repair)
    if inst is None:
        if explicit is not None:
            return explicit, type(explicit).__name__, "fallback"
        return None, "none", tier
    return inst, name, tier


def _pin_is_usable(name: str) -> bool:
    """True when a pinned provider name is known and has a usable key."""
    try:
        from config.providers import validate_provider_key

        return bool(validate_provider_key(name, require_key=False))
    except Exception:
        return False


def rotate(
    task_kind: str = "",
    current: str = "",
    prompt: str = "",
) -> Tuple[Optional[Any], str, str]:
    """Next provider for a retry after `current` failed.

    This is the same decision path as `route` (tier classification, then that
    tier's remaining members ranked by health/EWMA latency), so a retry never
    lands back on the provider that just failed and never bypasses a cooldown or
    an open circuit. Returns `(None, "none", tier)` when no alternative exists —
    the caller then keeps its current provider rather than inventing one.
    """
    if offline():
        return None, "offline", "offline"
    if _pinned():
        # An explicit pin cannot be rotated away from without overriding the user.
        return None, "pinned", "pinned"
    if not enabled():
        return None, "none", "disabled"

    router = get_router()
    primary = classify_task(task_kind or "repair", prompt, is_repair=True)
    for tier in (primary,) + tuple(t for t in TIERS if t != primary):
        inst, name = router.provider_for(tier, exclude=(current,), pool_fallback=False)
        if inst is not None:
            return inst, name, tier
    return None, "none", primary

