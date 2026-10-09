"""Prompt registry — versioning, A/B rollout and per-run provenance.

Prompts were previously hardcoded (config/master_prompt.py) with no record of
which prompt text produced which build, which made A/B testing and regression
triage impossible. This module gives every prompt a versioned, content-hashed
home:

* The default version is the code-baseline prompt (auto-imported on first run).
* New versions are registered via ``register_version`` (API or file edit) with
  an explicit ``rollout`` percentage (0–100).
* ``resolve()`` deterministically picks a version for a run — a stable hash of
  (prompt name + version key + run seed) — so a given seed always gets the same
  variant across processes and restarts.
* Every resolution is recorded (``resolved`` counter + last-used version), and
  the run report can embed ``prompt_provenance`` linking prompt name →
  version → sha256 → rollout.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

_REGISTRY_VERSION = 1

_lock = threading.Lock()


def _default_store_path() -> Path:
    custom = os.getenv("PROMPT_REGISTRY_PATH")
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parent.parent / "database" / "prompt_registry.json"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class PromptRegistry:
    """File-backed registry of versioned prompts with deterministic A/B rollout."""

    def __init__(self, store_path: Optional[Path] = None, seed_defaults: Optional[Dict[str, str]] = None):
        self.store_path = Path(store_path) if store_path else _default_store_path()
        self._data: Dict = {"schema_version": _REGISTRY_VERSION, "prompts": {}}
        self.resolved_log: List[Dict] = []
        if seed_defaults:
            for name, text in seed_defaults.items():
                self.seed_default(name, text)
        self._load()

    # ── persistence ────────────────────────────────────────────────────────
    def _load(self) -> None:
        if not self.store_path.exists():
            self._save()
            return
        try:
            self._data = json.loads(self.store_path.read_text(encoding="utf-8"))
            if "prompts" not in self._data:
                self._data = {"schema_version": _REGISTRY_VERSION, "prompts": {}}
        except (json.JSONDecodeError, OSError):
            # Corrupt registry must not take generation down — start fresh.
            self._data = {"schema_version": _REGISTRY_VERSION, "prompts": {}}

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.store_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self.store_path)

    # ── registration ───────────────────────────────────────────────────────
    def seed_default(self, name: str, text: str, label: str = "baseline") -> None:
        """Register the code-baseline prompt (idempotent, never overrides)."""
        with _lock:
            entry = self._data["prompts"].setdefault(name, {"active": label, "versions": {}})
            if label not in entry["versions"]:
                entry["versions"][label] = {
                    "text": text,
                    "sha256": _hash_text(text),
                    "rollout": 100,
                    "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "baseline": True,
                }
                self._save()

    def register_version(self, name: str, label: str, text: str, rollout: int = 0,
                         notes: str = "") -> Dict:
        """Register a new prompt version. rollout=0 shadows it until promoted."""
        if not name or not label:
            raise ValueError("prompt name and version label are required")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("prompt text must be a non-empty string")
        rollout = max(0, min(100, int(rollout)))
        with _lock:
            entry = self._data["prompts"].setdefault(name, {"active": label, "versions": {}})
            entry["versions"][label] = {
                "text": text,
                "sha256": _hash_text(text),
                "rollout": rollout,
                "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "notes": notes,
            }
            self._save()
            return dict(entry["versions"][label])

    def set_active(self, name: str, label: str) -> None:
        with _lock:
            entry = self._data["prompts"].get(name)
            if not entry or label not in entry["versions"]:
                raise KeyError(f"unknown prompt/version: {name}/{label}")
            entry["active"] = label
            self._save()

    def set_rollout(self, name: str, label: str, rollout: int) -> None:
        with _lock:
            entry = self._data["prompts"].get(name)
            if not entry or label not in entry["versions"]:
                raise KeyError(f"unknown prompt/version: {name}/{label}")
            entry["versions"][label]["rollout"] = max(0, min(100, int(rollout)))
            self._save()

    # ── resolution ─────────────────────────────────────────────────────────
    @staticmethod
    def _bucket(name: str, label: str, seed: str) -> int:
        digest = hashlib.sha256(f"{name}:{label}:{seed}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 100

    def resolve(self, name: str, seed: str = "default") -> Optional[Dict]:
        """Pick the prompt version for this run: active version, or the
        active one shadowed by a higher-priority experiment bucket."""
        entry = self._data["prompts"].get(name)
        if not entry:
            return None
        versions = entry.get("versions", {})
        if not versions:
            return None

        chosen_label = entry.get("active") if entry.get("active") in versions else next(iter(versions))
        # Deterministic experiment pick: every version with rollout>0 competes
        # for the seed's bucket. Highest rollout wins; ties go to the most
        # recently registered version, so promoting a new version to 100%
        # (the same rollout as the baseline) actually takes over.
        best = None
        best_key = None
        for label, meta in versions.items():
            rollout = int(meta.get("rollout", 0))
            if rollout <= 0:
                continue
            if self._bucket(name, label, str(seed)) < rollout:
                key = (rollout, str(meta.get("registered_at", "")), label)
                if best_key is None or key > best_key:
                    best_key = key
                    best = label
        if best:
            chosen_label = best

        meta = versions[chosen_label]
        record = {
            "prompt": name,
            "version": chosen_label,
            "sha256": meta.get("sha256"),
            "rollout": meta.get("rollout", 0),
            "seed": str(seed),
        }
        self.resolved_log.append(record)
        return {"text": meta["text"], **record}

    # ── provenance / reporting ─────────────────────────────────────────────
    def provenance(self) -> List[Dict]:
        """What this registry resolved (per process) — embed in run reports."""
        return list(self.resolved_log)

    def describe(self) -> Dict:
        out = {}
        for name, entry in self._data["prompts"].items():
            out[name] = {
                "active": entry.get("active"),
                "versions": {
                    label: {"sha256": meta.get("sha256"), "rollout": meta.get("rollout"),
                            "baseline": meta.get("baseline", False)}
                    for label, meta in entry["versions"].items()
                },
            }
        return out


_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    """Process-wide registry singleton (seeds the baseline master prompt)."""
    global _registry
    if _registry is None:
        from config.master_prompt import get_master_prompt

        _registry = PromptRegistry()
        try:
            _registry.seed_default("master_prompt", get_master_prompt())
        except Exception:  # pragma: no cover - master prompt import must not crash boot
            pass
    return _registry
