"""Quality-score trend tracking + regression detection.

Every build records {quality_score, accessibility, status, provider} into an
append-only JSONL (one JSON object per line — trivially diffable/backupable).
``evaluate()`` compares the newest score against the rolling window
(default 20 runs): a REGRESSION is flagged when the score drops more than
``max(2*stddev, regression_floor)`` below the mean, or below the absolute
floor. The evaluation is embedded in run reports and exposed at
``GET /api/v1/quality/trends`` so drift is visible before buyers notice.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

DEFAULT_WINDOW = int(os.getenv("QUALITY_TREND_WINDOW", "20"))
DEFAULT_REGRESSION_FLOOR = float(os.getenv("QUALITY_REGRESSION_FLOOR", "5.0"))
DEFAULT_ABSOLUTE_FLOOR = float(os.getenv("QUALITY_ABSOLUTE_FLOOR", "75.0"))

_lock = threading.Lock()


def _default_store_path() -> Path:
    return Path(__file__).resolve().parent.parent / "database" / "quality_trends.jsonl"


class QualityTrendTracker:
    def __init__(self, store_path: Optional[Path] = None,
                 window: int = DEFAULT_WINDOW,
                 regression_floor: float = DEFAULT_REGRESSION_FLOOR,
                 absolute_floor: float = DEFAULT_ABSOLUTE_FLOOR):
        self.store_path = Path(store_path) if store_path else _default_store_path()
        self.window = max(5, int(window))
        self.regression_floor = float(regression_floor)
        self.absolute_floor = float(absolute_floor)
        self._records: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            if self.store_path.exists():
                for line in self.store_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            agent_logger.warning("Quality trends file unreadable; starting empty (%s)", self.store_path)
            self._records = []

    def _append(self, record: Dict[str, Any]) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with self.store_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError:
            agent_logger.warning("Quality trend append failed; trend may be incomplete")

    # ── API ────────────────────────────────────────────────────────────────
    def record(self, quality_score: Optional[float], project: str = "",
               status: str = "succeeded", provider: str = "",
               accessibility: Optional[float] = None, run_id: str = "") -> Dict[str, Any]:
        score = float(quality_score) if quality_score is not None else 0.0
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_id": run_id,
            "project": (project or "")[:120],
            "quality_score": round(score, 2),
            "accessibility": round(float(accessibility), 2) if accessibility is not None else None,
            "status": status,
            "provider": provider or "",
        }
        with _lock:
            self._records.append(entry)
            self._records = self._records[-5000:]
            self._append(entry)
        return entry

    def _stats(self, scores: List[float]) -> Dict[str, float]:
        n = len(scores)
        if not n:
            return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "count": 0}
        mean = sum(scores) / n
        variance = sum((s - mean) ** 2 for s in scores) / n
        return {
            "mean": round(mean, 2),
            "stddev": round(math.sqrt(variance), 2),
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "count": n,
        }

    def evaluate(self, latest: Optional[float] = None) -> Dict[str, Any]:
        """Trend + regression verdict for the newest score (or the last record)."""
        with _lock:
            records = list(self._records)
        if latest is None:
            latest = records[-1]["quality_score"] if records else None
        if latest is None:
            return {"state": "no_data", "stats": {"count": 0}}

        history = [r["quality_score"] for r in records[:-1]][-self.window:]
        stats = self._stats(history)
        verdict: Dict[str, Any] = {
            "latest_score": round(float(latest), 2),
            "stats": stats,
        }
        if stats["count"] < 5:
            verdict["state"] = "insufficient_history"
            return verdict

        drop_threshold = max(2 * stats["stddev"], self.regression_floor)
        delta = float(latest) - stats["mean"]
        verdict["delta_vs_mean"] = round(delta, 2)
        if float(latest) < self.absolute_floor:
            verdict["state"] = "regression"
            verdict["reason"] = f"score below absolute floor {self.absolute_floor}"
        elif delta < -drop_threshold:
            verdict["state"] = "regression"
            verdict["reason"] = (
                f"score {round(float(latest), 2)} is {round(-delta, 2)} below the "
                f"{self.window}-run mean {stats['mean']} (threshold {round(drop_threshold, 2)})"
            )
        elif float(latest) > stats["mean"]:
            verdict["state"] = "improved"
        else:
            verdict["state"] = "stable"
        return verdict

    def describe(self) -> Dict[str, Any]:
        with _lock:
            records = list(self._records)
        recent = records[-self.window:]
        return {
            "total_recorded": len(records),
            "window": self.window,
            "recent": recent,
            "trend": self.evaluate(),
        }


_tracker: Optional[QualityTrendTracker] = None


def get_quality_tracker() -> QualityTrendTracker:
    global _tracker
    if _tracker is None:
        _tracker = QualityTrendTracker()
    return _tracker
