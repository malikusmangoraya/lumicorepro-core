"""Watchtower — live analytics over the agent's own runtime.

Reads `logs/provider_calls.jsonl` (every provider request), the SQLite
pipeline store (run lifecycle), and the current provider pool state, then
returns a single evidence-based snapshot for the UI dashboard. No invented
metrics: anything not measured is reported as such.
"""
import os
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

from utils.logger import agent_logger

_PAD = "  "
_AVG_KMAP = {"ms": 1, "s": 1000}


def _fmt_ms(ms: float) -> str:
    if ms < 1:
        return f"{int(ms * 1000)}us"
    if ms < 1000:
        return f"{int(ms)}ms"
    return f"{round(ms / 1000, 2)}s"


def _parse_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except Exception as exc:
        agent_logger.warning(f"[WATCHTOWER] Cannot read {path}: {exc}")
    return rows


class Watchtower:
    """Builds an analytics snapshot from agent runtime artifacts."""

    def __init__(self, logs_dir: Optional[str] = None):
        base = Path(__file__).resolve().parent.parent.parent  # ai-agent/
        self.logs_dir = Path(logs_dir) if logs_dir else (base / "logs")
        self.jsonl = self.logs_dir / "provider_calls.jsonl"

    def _provider_usage(self) -> Dict[str, Any]:
        rows = _parse_jsonl(self.jsonl)
        per: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "success": 0, "errors": 0, "latency_ms": []}
        )
        for r in rows:
            name = r.get("provider") or r.get("model") or "unknown"
            bucket = per[name]
            bucket["calls"] += 1
            lat = r.get("latency_seconds")
            if isinstance(lat, (int, float)):
                bucket["latency_ms"].append(float(lat) * 1000)
            if r.get("success"):
                bucket["success"] += 1
            else:
                bucket["errors"] += 1

        providers = []
        for name, b in sorted(per.items(), key=lambda kv: -kv[1]["calls"]):
            lats = sorted(b["latency_ms"])
            avg = sum(lats) / len(lats) if lats else None
            p95 = lats[int(len(lats) * 0.95)] if lats else None
            providers.append({
                "provider": name,
                "calls": b["calls"],
                "success": b["success"],
                "errors": b["errors"],
                "success_rate": round(b["success"] / b["calls"], 3) if b["calls"] else None,
                "avg_latency_ms": round(avg, 1) if avg is not None else None,
                "p95_latency_ms": round(p95, 1) if p95 is not None else None,
            })
        total = len(rows)
        success = sum(1 for r in rows if r.get("success"))
        lats = sorted(r.get("latency_seconds") for r in rows if isinstance(r.get("latency_seconds"), (int, float)))
        return {
            "total_calls": total,
            "success": success,
            "errors": total - success,
            "success_rate": round(success / total, 3) if total else None,
            "avg_latency_ms": round((sum(lats) / len(lats)) * 1000, 1) if lats else None,
            "p95_latency_ms": round((lats[int(len(lats) * 0.95)] or lats[-1]) * 1000, 1) if lats else None,
            "per_provider": providers,
            "record_count": total,
            "sample_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _run_stats(self) -> Dict[str, Any]:
        try:
            from database.pipeline_store import PipelineStore
            store = PipelineStore()
            runs = store.list_runs(limit=200)
        except Exception as exc:
            agent_logger.warning(f"[WATCHTOWER] Run store unavailable: {exc}")
            return {"runs_tracked": 0, "status": "not_measured"}

        by_status: Dict[str, int] = defaultdict(int)
        avg_duration = []
        for r in runs:
            by_status[r.get("status", "unknown")] += 1
            dur = r.get("duration_seconds")
            if isinstance(dur, (int, float)):
                avg_duration.append(float(dur))
        return {
            "runs_tracked": len(runs),
            "by_status": dict(by_status),
            "avg_duration_seconds": round(sum(avg_duration) / len(avg_duration), 1) if avg_duration else None,
        }

    def _pool_health(self) -> Dict[str, Any]:
        try:
            from providers.provider_pool import get_pool
            pool = get_pool()
            status = pool.status()
            return {
                "active": pool.get_current_name(),
                "loaded": pool.available,
                "providers": status,
            }
        except Exception as exc:
            agent_logger.warning(f"[WATCHTOWER] Pool health unavailable: {exc}")
            return {"status": "not_measured"}

    def snapshot(self) -> Dict[str, Any]:
        """Return a full evidence-based snapshot for the dashboard."""
        try:
            usage = self._provider_usage()
        except Exception as exc:
            usage = {"status": "error", "detail": str(exc)}
        try:
            runs = self._run_stats()
        except Exception as exc:
            runs = {"status": "error", "detail": str(exc)}
        try:
            pool = self._pool_health()
        except Exception as exc:
            pool = {"status": "error", "detail": str(exc)}

        health = "healthy"
        if isinstance(usage, dict) and usage.get("success_rate") is not None and usage["success_rate"] < 0.8:
            health = "degraded"
        if isinstance(runs, dict) and runs.get("by_status", {}).get("error"):
            health = "needs-attention"

        return {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "health": health,
            "usage": usage,
            "runs": runs,
            "pool": pool,
        }


def snapshot() -> Dict[str, Any]:
    """Convenience: one-shot snapshot without constructing the class."""
    return Watchtower().snapshot()