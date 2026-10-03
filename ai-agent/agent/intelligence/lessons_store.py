"""Cross-Project Lessons Store — LumicorePro Part 3 intelligence.

Self-learning loop ("the more you build, the better"): every completed build
records its score, gate outcome, weakest metrics, and blueprint decision into a
small JSONL store scoped to industry + brand. Future builds consult the store to
bias the design decision — the agent learns from its own previous output scoring
instead of rebuilding every project from a cold start.

Design guarantees:
  - Observational: record_lesson / lessons_for must never raise; they may only
    read/write JSONL under `ai-agent/intelligence/lessons/`.
  - Bounded: capped rows per (industry, brand) so the file never grows unbounded.
  - Deterministic bias: only metrics that failed the design gate below the
    benchmark threshold are surfaced back as `attention`, never opinions.
"""
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

_LOCK = threading.Lock()
_DEFAULT_DIR = Path(__file__).resolve().parent / "lessons"
_MAX_ROWS_PER_BUCKET = 8
_BENCHMARK_PASS_THRESHOLD = 85.0  # matches design_gate threshold


class LessonsStore:
    """Persistent memory of past build scores keyed by industry + brand."""

    def __init__(self, store_dir: Optional[str] = None):
        self.store_dir = Path(store_dir) if store_dir else _DEFAULT_DIR
        self.pass_threshold = _BENCHMARK_PASS_THRESHOLD

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _row_path(self, industry: str, brand: str) -> Path:
        safe_industry = "".join(c if c.isalnum() else "_" for c in industry)
        safe_brand = "".join(c if c.isalnum() else "_" for c in brand)
        return self.store_dir / f"{safe_industry}__{safe_brand}.jsonl"

    def _read_rows(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return [json.loads(line) for line in fh if line.strip()]
        except Exception:
            return []

    def record_lesson(self, industry: str, brand: str,
                      score: Optional[float], gate: Optional[Dict[str, Any]],
                      decision: Optional[Dict[str, Any]],
                      metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Persist one build outcome. Never raises; returns saved-on-success."""
        try:
            bucket = (industry or "general") or "general"
            brand = (brand or "general") or "general"
            score_num = float(score or 0.0)
            if score_num <= 0:
                return False

            # Only the metrics that failed the benchmark are worth remembering.
            attention: Dict[str, float] = {}
            for name, value in (metrics or {}).items():
                try:
                    num = float(value)
                except (TypeError, ValueError):
                    continue
                if num < self.pass_threshold:
                    attention[name] = round(num, 1)

            row = {
                "industry": bucket,
                "brand": brand,
                "score": round(score_num, 1),
                "passed": bool(gate and gate.get("passed")),
                "failing": gate.get("failing") if gate else [],
                "attention": attention,
                "weakest": (decision or {}).get("weakest_metric") or
                           sorted(attention.items(), key=lambda kv: kv[1])[0][0]
                           if attention else "",
                "reference_hints": len((decision or {}).get("reference_hints") or []),
                "ts": json.dumps({}),  # placeholder kept for schema stability
            }

            with _LOCK:
                path = self._row_path(bucket, brand)
                path.parent.mkdir(parents=True, exist_ok=True)
                rows = self._read_rows(path)
                rows.append(row)
                # Trim oldest rows so the store stays bounded per bucket.
                if len(rows) > _MAX_ROWS_PER_BUCKET:
                    rows = rows[-_MAX_ROWS_PER_BUCKET:]
                with open(path, "w", encoding="utf-8") as fh:
                    for r in rows:
                        fh.write(json.dumps(r) + "\n")
            agent_logger.info(
                f"[LESSONS] recorded {bucket}/{brand} score={row['score']} "
                f"attention={list(attention)}"
            )
            return True
        except Exception as exc:
            agent_logger.warning(f"[LESSONS] record skipped: {exc}")
            return False

    # ------------------------------------------------------------------
    # Consultation
    # ------------------------------------------------------------------
    def lessons_for(self, industry: str, brand: str = "general",
                    limit: int = 4) -> List[Dict[str, Any]]:
        """Best-known lessons for a bucket, most valuable (low score) first."""
        try:
            path = self._row_path(industry or "general", brand or "general")
            rows = self._read_rows(path)
            rows.sort(key=lambda r: r.get("score", 0.0))
            return rows[:limit]
        except Exception:
            return []

    def consensus_attention(self, industry: str,
                            brand: str = "general") -> List[str]:
        """Metrics that repeatedly failed the gate for this industry/brand."""
        try:
            counter: Dict[str, int] = {}
            for row in self.lessons_for(industry, brand, limit=_MAX_ROWS_PER_BUCKET):
                for metric in row.get("attention", {}):
                    counter[metric] = counter.get(metric, 0) + 1
            if not counter:
                return []
            threshold = max(1, len([r for r in self.lessons_for(industry, brand)]))
            return sorted(
                [m for m, count in counter.items() if count >= threshold],
                key=lambda m: counter[m], reverse=True,
            )
        except Exception:
            return []

    def to_bias_payload(self, industry: str, brand: str = "general",
                        limit: int = 3) -> Dict[str, Any]:
        """Compact, decision-engine-friendly summary of prior weak spots."""
        lessons = self.lessons_for(industry, brand, limit=limit)
        attention = self.consensus_attention(industry, brand)
        return {
            "prior_builds": len(lessons),
            "attention": attention,
            "worst_last_score": round(min((l.get("score", 100) for l in lessons), default=0), 1),
            "evidence": [
                {
                    "score": l.get("score"),
                    "passed": l.get("passed"),
                    "attention": l.get("attention"),
                } for l in lessons
            ],
        }


if __name__ == "__main__":
    import sys
    store = LessonsStore()
    demo = {
        "industry": "automotive", "brand": "luxury",
        "score": 93.4, "passed": False,
        "failing": ["originality"],
        "metrics": {"originality": 45, "brand_fit": 75},
    }
    store.record_lesson(demo["industry"], demo["brand"], demo["score"],
                        {"passed": demo["passed"], "failing": demo["failing"]},
                        {}, demo["metrics"])
    bias = store.to_bias_payload("automotive", "luxury")
    print(json.dumps(bias, indent=2))
    if not bias["attention"]:
        sys.exit(0)
    print("consensus attention:", bias["attention"])