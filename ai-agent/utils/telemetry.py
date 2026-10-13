"""Structured pipeline telemetry (JSONL, thread-safe).

Records generation run lifecycle as machine-readable events on disk so ops
dashboards, error-rate tracking and latency analysis can be built on top of
real pipeline data:

    ai-agent/logs/telemetry.jsonl
    {"ts": ..., "run_id": "...", "event": "phase_start", "phase": "Phase 1 - Market Analysis", ...}
    {"ts": ..., "run_id": "...", "event": "run_done", "duration_secs": 12.3, "quality_score": 87, ...}

Enabling: TELEMETRY_ENABLED=0 disables writes (default on). Retention is handled
by rotating the file at 5MB; `prune` keeps the newest file.
"""
import os
import json
import time
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import agent_logger

# Computed locally (the ai-agent/ root) instead of importing config.settings, so
# utils carries no dependency on config. This breaks the
# config -> providers -> utils -> config import cycle while resolving to the
# exact same directory (config.settings.AI_AGENT_DIR is this same expression).
_AI_AGENT_DIR = Path(__file__).resolve().parent.parent
_LOGS_DIR = (_AI_AGENT_DIR / "logs").resolve()
_TELEMETRY_FILE = _LOGS_DIR / "telemetry.jsonl"
_MAX_BYTES = 5 * 1024 * 1024
# Shared across instances: concurrent writers (threads + processes) must not
# interleave lines, so the lock is module-global, not per-instance.
_LOCK = threading.Lock()


class Telemetry:
    """Append-only structured event log with rotation + read-side aggregation."""

    def __init__(self, path: Optional[str] = None, enabled: Optional[bool] = None):
        self.path = str(path or _TELEMETRY_FILE)
        if enabled is None:
            enabled = os.getenv("TELEMETRY_ENABLED", "1").strip().lower() not in ("0", "false", "no")
        self.enabled = bool(enabled)

    def record(self, run_id: str, event: str, **fields: Any) -> None:
        if not self.enabled:
            return
        entry = {
            "ts": time.time(),
            "iso": _now_iso(),
            "run_id": run_id,
            "event": event,
        }
        entry.update(fields)
        line = json.dumps(entry, default=str) + "\n"
        try:
            with _LOCK:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                if os.path.exists(self.path) and os.path.getsize(self.path) > _MAX_BYTES:
                    self._rotate()
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(line)
        except OSError as exc:
            agent_logger.warning(f"telemetry write failed: {exc}")

    def _rotate(self) -> None:
        prev = f"{self.path}.1"
        try:
            if os.path.exists(prev):
                os.remove(prev)
            os.replace(self.path, prev)
        except OSError:
            pass

    def prune(self, keep: int = 3) -> int:
        """Delete rotated telemetry files beyond `keep`."""
        removed = 0
        try:
            for idx in range(keep, 50):
                candidate = f"{self.path}.{idx}" if idx else self.path
                if os.path.exists(candidate):
                    os.remove(candidate)
                    removed += 1
        except OSError:
            pass
        return removed

    def summary(self, since_ts: Optional[float] = None) -> Dict[str, Any]:
        """Aggregate the current (non-rotated) telemetry file for dashboards."""
        counts: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        by_phase: Dict[str, int] = {}
        durations: list = []
        errors: int = 0
        total: int = 0
        if os.path.exists(self.path):
            with _LOCK:
                with open(self.path, encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if since_ts and entry.get("ts", 0) < since_ts:
                            continue
                        total += 1
                        event = entry.get("event", "")
                        counts[event] = counts.get(event, 0) + 1
                        phase = entry.get("phase", "")
                        if phase:
                            by_phase[phase] = by_phase.get(phase, 0) + 1
                        status = entry.get("status")
                        if status:
                            by_status[status] = by_status.get(status, 0) + 1
                        if entry.get("duration_secs") is not None:
                            durations.append(float(entry["duration_secs"]))
                        if entry.get("error") or event == "run_error":
                            errors += 1
        n_durs = len(durations)
        return {
            "events": total,
            "by_event": counts,
            "by_status": by_status,
            "by_phase": by_phase,
            "error_count": errors,
            "avg_run_duration_secs": round(sum(durations) / n_durs, 3) if n_durs else 0.0,
            "max_run_duration_secs": round(max(durations), 3) if n_durs else 0.0,
            "path": self.path,
        }


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


default_telemetry = Telemetry()