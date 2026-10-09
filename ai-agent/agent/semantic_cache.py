"""Semantic generation cache — stop paying full price for similar prompts.

Two-tier lookup:
  1. Exact match  — sha256 of the normalized prompt (whitespace/punctuation
     collapsed). Always trusted.
  2. Similar match — dependency-free semantic similarity
     (utils.semantic.semantic_similarity) across cached prompts. A hit above
     the threshold (default 0.93, env-tunable) is returned with its similarity
     recorded, so the caller can decide to surface it.

Storage: JSON file in the agent's database dir (volume-backed in production).
Thread-safe, bounded (LRU prune by created_at) and offline-safe: any I/O error
results in a MISS, never an exception — cache failure must not fail a build.

Integration: server.py checks the cache before spawning the orchestrator and
stores successful reports afterwards. Quality-score trend tracking treats
cache hits separately so they don't skew real-generation metrics.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger
from utils.semantic import semantic_similarity

DEFAULT_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.93"))
DEFAULT_MAX_ENTRIES = int(os.getenv("SEMANTIC_CACHE_MAX_ENTRIES", "200"))
_ENABLED = os.getenv("SEMANTIC_CACHE_ENABLED", "true").strip().lower() not in ("0", "false", "no", "off")

_WS_RE = re.compile(r"[^a-z0-9]+")

_lock = threading.Lock()


def normalize_prompt(prompt: str) -> str:
    """Lowercase, strip non-alphanumerics — the exact-match key."""
    return _WS_RE.sub(" ", (prompt or "").lower()).strip()


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(normalize_prompt(prompt).encode("utf-8")).hexdigest()


class SemanticCache:
    """File-backed cache of successful generation reports keyed by prompt."""

    def __init__(self, store_path: Optional[Path] = None,
                 threshold: float = DEFAULT_THRESHOLD,
                 max_entries: int = DEFAULT_MAX_ENTRIES,
                 enabled: bool = _ENABLED):
        self.store_path = Path(store_path) if store_path else (
            Path(__file__).resolve().parent.parent / "database" / "semantic_cache.json"
        )
        self.threshold = threshold
        self.max_entries = max(1, int(max_entries))
        self.enabled = enabled
        self.stats = {"hits": 0, "exact_hits": 0, "semantic_hits": 0, "misses": 0, "stores": 0}
        self._entries: List[Dict[str, Any]] = []
        self._load()

    # ── persistence ────────────────────────────────────────────────────────
    def _load(self) -> None:
        try:
            if self.store_path.exists():
                self._entries = json.loads(self.store_path.read_text(encoding="utf-8"))
                if not isinstance(self._entries, list):
                    self._entries = []
        except (json.JSONDecodeError, OSError):
            agent_logger.warning("Semantic cache unreadable; starting empty (%s)", self.store_path)
            self._entries = []

    def _save(self) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.store_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._entries[-self.max_entries:], indent=2), encoding="utf-8")
            tmp.replace(self.store_path)
        except OSError:
            agent_logger.warning("Semantic cache write failed; continuing in-memory")

    # ── lookup / store ─────────────────────────────────────────────────────
    def lookup(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Return {report, similarity, key, prompt, created_at} on a hit."""
        if not self.enabled:
            return None
        norm = normalize_prompt(prompt)
        if not norm:
            return None
        wanted = prompt_hash(prompt)
        with _lock:
            # 1. exact
            for entry in reversed(self._entries):
                if entry.get("key") == wanted:
                    entry["hits"] = int(entry.get("hits", 0)) + 1
                    self.stats["hits"] += 1
                    self.stats["exact_hits"] += 1
                    self._save()
                    return {**entry, "match": "exact", "similarity": 1.0}
            # 2. semantic (scan newest-first, bounded work)
            best = None
            for entry in reversed(self._entries[-500:]):
                stored = entry.get("prompt_normalized", "")
                if not stored:
                    continue
                score = semantic_similarity(norm, stored)
                if score >= self.threshold and (best is None or score > best["similarity"]):
                    best = {**entry, "match": "semantic", "similarity": round(score, 4)}
            if best:
                best["hits"] = int(best.get("hits", 0)) + 1
                self.stats["hits"] += 1
                self.stats["semantic_hits"] += 1
                self._save()
                return best
            self.stats["misses"] += 1
            return None

    def store(self, prompt: str, report: Dict[str, Any],
              quality_score: Optional[float] = None) -> bool:
        """Persist a successful generation report for future lookups."""
        if not self.enabled or not (prompt or "").strip():
            return False
        payload = {
            "key": prompt_hash(prompt),
            "prompt_normalized": normalize_prompt(prompt),
            "prompt": (prompt or "")[:400],
            "provider": report.get("provider") or report.get("provider_used"),
            "project_name": report.get("project_name"),
            "generated_project_dir": report.get("generated_project_dir"),
            "zip_archive_path": report.get("zip_archive_path"),
            "quality_score": quality_score,
            "status": report.get("status"),
            "report": report,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hits": 0,
        }
        with _lock:
            self._entries = [e for e in self._entries if e.get("key") != payload["key"]]
            self._entries.append(payload)
            self._entries = self._entries[-self.max_entries:]
            self.stats["stores"] += 1
            self._save()
        return True

    def invalidate(self, prompt: str) -> bool:
        wanted = prompt_hash(prompt)
        with _lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.get("key") != wanted]
            self._save()
            return len(self._entries) < before

    def clear(self) -> int:
        with _lock:
            n = len(self._entries)
            self._entries = []
            self._save()
            return n

    def describe(self) -> Dict[str, Any]:
        with _lock:
            return {
                "enabled": self.enabled,
                "entries": len(self._entries),
                "max_entries": self.max_entries,
                "threshold": self.threshold,
                "stats": dict(self.stats),
            }


_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    global _cache
    if _cache is None:
        _cache = SemanticCache()
    return _cache
