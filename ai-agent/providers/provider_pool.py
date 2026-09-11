"""
ProviderPool — Smart provider rotation with automatic fallback and cycle-back.

When one provider hits rate limit (429), the pool:
  1. Marks that provider as rate-limited (cooldown)
  2. Switches to the next available provider
  3. When all providers are exhausted, cycles back to the first one
  4. Tracks cooldown timestamps so recovered providers are reused

Usage:
    pool = ProviderPool()              # auto-discovers available providers
    provider = pool.get_active()       # get current provider
    pool.mark_rate_limited("grok")     # call on 429
    pool.mark_failed("openai")         # call on other errors
"""

import time
import threading
from typing import Optional, List, Dict
from utils.logger import agent_logger


# Cooldown after rate limit — retry this provider after 30 seconds
RATE_LIMIT_COOLDOWN = 30
# Cooldown after general failure — 15 seconds
FAILURE_COOLDOWN = 15
# Max time to wait when ALL providers are in cooldown before rotating anyway
MAX_ALL_COOLDOWN_WAIT = 5
# Rotate to another provider when the active one exceeds this share of consecutive work
ROTATE_AFTER_FAILURES = 2


class ProviderPool:
    """Manages a rotating pool of AI providers with rate-limit awareness."""

    def __init__(self, fallback_order: List[str] = None):
        from config.providers import FALLBACK_ORDER, instantiate_provider, validate_provider_key

        self._order = fallback_order or list(FALLBACK_ORDER)
        self._providers: Dict[str, object] = {}
        self._cooldowns: Dict[str, float] = {}       # provider -> cooldown_until timestamp
        self._current_index = 0
        self._lock = threading.Lock()

        # Pre-instantiate all available providers
        for name in self._order:
            try:
                if validate_provider_key(name, require_key=False):
                    inst = instantiate_provider(name)
                    if inst:
                        self._providers[name] = inst
                        agent_logger.info(f"[POOL] Loaded provider: {name}")
            except Exception as e:
                agent_logger.warning(f"[POOL] Failed to load provider '{name}': {e}")

        available = list(self._providers.keys())
        agent_logger.info(f"[POOL] Ready — {len(available)} providers: {available}")

    @property
    def available(self) -> List[str]:
        """Return names of all loaded providers."""
        return list(self._providers.keys())

    def _is_cooled_down(self, name: str) -> bool:
        """Check if provider is still in cooldown period."""
        until = self._cooldowns.get(name, 0)
        return time.time() >= until

    def _clear_cooldown(self, name: str):
        """Clear cooldown for a provider (e.g. after successful call)."""
        self._cooldowns.pop(name, None)

    def get_active(self):
        """Return the current active provider instance, rotating if needed."""
        with self._lock:
            return self._get_active_unlocked()

    def _get_active_unlocked(self):
        """Internal: find the next available provider, cycling if necessary."""
        if not self._providers:
            agent_logger.error("[POOL] No providers available!")
            return None

        total = len(self._order)

        # Try all providers starting from current index
        for _ in range(total):
            name = self._order[self._current_index % total]
            if name in self._providers and self._is_cooled_down(name):
                return self._providers[name]
            self._current_index = (self._current_index + 1) % total

        # All providers in cooldown — find the one with shortest remaining cooldown
        best_name = None
        best_wait = float("inf")
        for name in self._providers:
            remaining = self._cooldowns.get(name, 0) - time.time()
            if remaining < best_wait:
                best_wait = remaining
                best_name = name

        if best_name:
            wait = min(max(0, best_wait), MAX_ALL_COOLDOWN_WAIT)
            if wait > 0:
                agent_logger.info(f"[POOL] All providers in cooldown — brief wait {wait:.0f}s then re-rotate")
                time.sleep(wait)
            self._current_index = self._order.index(best_name)
            return self._providers[best_name]

        return None

    def mark_rate_limited(self, name: str):
        """Mark provider as rate-limited — it will be skipped for RATE_LIMIT_COOLDOWN seconds."""
        with self._lock:
            self._cooldowns[name] = time.time() + RATE_LIMIT_COOLDOWN
            agent_logger.warning(f"[POOL] Rate limited: '{name}' — cooling down {RATE_LIMIT_COOLDOWN}s")

            # Rotate to next
            if name in self._providers:
                idx = self._order.index(name)
                self._current_index = (idx + 1) % len(self._order)

    def mark_failed(self, name: str):
        """Mark provider as failed (non-rate-limit error) — short cooldown."""
        with self._lock:
            self._cooldowns[name] = time.time() + FAILURE_COOLDOWN
            agent_logger.warning(f"[POOL] Failed: '{name}' — cooling down {FAILURE_COOLDOWN}s")

            if name in self._providers:
                idx = self._order.index(name)
                self._current_index = (idx + 1) % len(self._order)

    def mark_success(self, name: str):
        """Clear cooldown on success — provider is healthy."""
        with self._lock:
            self._clear_cooldown(name)

    def get_provider_name(self, provider_instance) -> Optional[str]:
        """Reverse-lookup: get provider name from instance."""
        for name, inst in self._providers.items():
            if inst is provider_instance:
                return name
        return None

    def get_current_name(self) -> Optional[str]:
        """Get the name of the currently active provider (includes cycle-back)."""
        with self._lock:
            total = len(self._order)
            for _ in range(total):
                name = self._order[self._current_index % total]
                if name in self._providers and self._is_cooled_down(name):
                    return name
                self._current_index = (self._current_index + 1) % total

            # All in cooldown — pick the one with shortest remaining cooldown
            if self._providers:
                return min(
                    self._providers.keys(),
                    key=lambda n: self._cooldowns.get(n, 0) - time.time(),
                )
        return None

    def status(self) -> Dict[str, any]:
        """Return pool status for diagnostics."""
        status = {}
        now = time.time()
        for name in self._providers:
            cooldown_until = self._cooldowns.get(name, 0)
            remaining = max(0, cooldown_until - now)
            status[name] = {
                "available": self._is_cooled_down(name),
                "cooldown_remaining": round(remaining, 1),
                "is_current": name == self.get_current_name(),
            }
        return status


# ── Global singleton ──────────────────────────────────────────────────────
_pool: Optional[ProviderPool] = None
_pool_lock = threading.Lock()


def get_pool() -> ProviderPool:
    """Get or create the global provider pool (thread-safe lazy init)."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ProviderPool()
    return _pool


def reset_pool():
    """Reset the global pool (for testing or config changes)."""
    global _pool
    with _pool_lock:
        _pool = None
