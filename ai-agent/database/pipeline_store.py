"""Durable pipeline run store (SQLite-backed, Redis-replaceable interface).

Persists generation run lifecycle + streamed events so runs survive a server
restart and can be replayed via /api/runs. The method surface is deliberately
async-agnostic and small so a future Redis-backed implementation can be swapped
in without touching server.py.

The pipeline worker streams events from a background thread, so all access is
serialized behind a lock and the single SQLite connection is created with
check_same_thread=False (safe because every method is lock-guarded).

Interface contract (implement this to move to Redis):
    create_run(run_id, **fields) -> None
    upsert_run(run_id, **fields) -> None
    set_status(run_id, status, **fields) -> None
    append_events(run_id, events) -> None
    get_run(run_id) -> dict | None
    list_runs(limit=20, status=None) -> list[dict]
    mark_interrupted(started_before_ts) -> list[str]
    prune(keep=500) -> int
"""
import os
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import AGENT_DB_PATH
from utils.logger import agent_logger

_MAX_EVENTS_DBS = 1000
_FINISHED_STATUSES = ("done", "error", "cancelled", "interrupted")


class PipelineStore:
    """SQLite-backed durable store for pipeline run state and events."""

    def __init__(self, db_path: Optional[str] = None, max_events: int = _MAX_EVENTS_DBS):
        self.db_path = str(db_path or AGENT_DB_PATH)
        self.max_events = max(20, int(max_events))
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()

    # ── connection helpers ────────────────────────────────────────────────
    def _connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.row_factory = sqlite3.Row
        self._conn = conn
        self._ensure_schema()
        return conn

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id       TEXT PRIMARY KEY,
                status       TEXT NOT NULL,
                prompt       TEXT NOT NULL,
                provider     TEXT,
                language     TEXT,
                region       TEXT,
                buyer_type   TEXT,
                design_style TEXT,
                created_at   TEXT NOT NULL,
                started_at   REAL,
                finished_at  REAL,
                error        TEXT,
                result_json  TEXT,
                events_json  TEXT,
                updated_at   TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    # ── writes ─────────────────────────────────────────────────────────────
    def create_run(self, run_id: str, **fields: Any) -> None:
        with self._lock:
            fields["status"] = fields.get("status", "queued")
            fields["events_json"] = json.dumps([])
            fields["created_at"] = fields.get("created_at", _now_iso())
            if self.get_run(run_id):
                return
            self._insert_fields(run_id, fields)

    def upsert_run(self, run_id: str, **fields: Any) -> None:
        with self._lock:
            current = self.get_run(run_id)
            fields["updated_at"] = _now_iso()
            if not current:
                self._insert_fields(run_id, fields)
                return
            columns = {
                "status", "prompt", "provider", "language", "region", "buyer_type",
                "design_style", "created_at", "started_at", "finished_at", "error",
                "result_json", "events_json",
            }
            updates = {k: self._serialize(v) for k, v in fields.items() if k in columns}
            if not updates:
                return
            if "events_json" in updates and not updates.get("events_json"):
                updates.pop("events_json")
            assign = ", ".join(f"{k} = ?" for k in updates)
            self._connect().execute(
                f"UPDATE pipeline_runs SET {assign} WHERE run_id = ?",
                list(updates.values()) + [run_id],
            )
            self._connect().commit()

    def _insert_fields(self, run_id: str, fields: Dict[str, Any]) -> None:
        columns = {
            "status", "prompt", "provider", "language", "region", "buyer_type",
            "design_style", "created_at", "started_at", "finished_at", "error",
            "result_json", "events_json",
        }
        insert = {k: self._serialize(v) for k, v in fields.items() if k in columns}
        insert.setdefault("status", "queued")
        insert.setdefault("created_at", _now_iso())
        insert["run_id"] = run_id
        names = ", ".join(insert.keys())
        marks = ", ".join("?" for _ in insert)
        self._connect().execute(
            f"INSERT OR REPLACE INTO pipeline_runs ({names}) VALUES ({marks})",
            list(insert.values()),
        )
        self._connect().commit()

    def set_status(self, run_id: str, status: str, **fields: Any) -> None:
        fields["status"] = status
        self.upsert_run(run_id, **fields)

    def append_events(self, run_id: str, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT events_json FROM pipeline_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            stored: List[Dict[str, Any]] = []
            if row and row["events_json"]:
                try:
                    stored = json.loads(row["events_json"])
                except (json.JSONDecodeError, TypeError):
                    stored = []
            stored.extend(list(events))
            del stored[:-self.max_events]
            conn.execute(
                "UPDATE pipeline_runs SET events_json = ?, updated_at = ? WHERE run_id = ?",
                (json.dumps(stored), _now_iso(), run_id),
            )
            conn.commit()

    # ── reads ──────────────────────────────────────────────────────────────
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._connect().execute(
                "SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return self._row_to_dict(row) if row is not None else None

    def list_runs(self, limit: int = 20, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            limit = max(1, min(int(limit), 100))
            if status:
                rows = self._connect().execute(
                    "SELECT * FROM pipeline_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = self._connect().execute(
                    "SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def mark_interrupted(self, started_before_ts: float) -> List[str]:
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT run_id FROM pipeline_runs WHERE status = 'running' AND started_at < ?",
                (started_before_ts,),
            ).fetchall()
            run_ids = [r["run_id"] for r in rows]
            for run_id in run_ids:
                conn.execute(
                    "UPDATE pipeline_runs SET status = 'interrupted', updated_at = ? WHERE run_id = ?",
                    (_now_iso(), run_id),
                )
            if run_ids:
                conn.commit()
            return run_ids

    def prune(
        self, keep: int = 500, finished_statuses: tuple = _FINISHED_STATUSES
    ) -> int:
        with self._lock:
            conn = self._connect()
            conn.execute(
                f"DELETE FROM pipeline_runs WHERE status NOT IN ({_mk_marks(finished_statuses)})",
                list(finished_statuses),
            )
            conn.commit()
            rows = conn.execute(
                f"SELECT run_id FROM pipeline_runs WHERE status IN ({_mk_marks(finished_statuses)})"
                " ORDER BY created_at ASC",
                list(finished_statuses),
            ).fetchall()
            delete_ids = [r["run_id"] for r in rows[:-keep]] if len(rows) > keep else []
            if delete_ids:
                conn.executemany(
                    "DELETE FROM pipeline_runs WHERE run_id = ?",
                    [(rid,) for rid in delete_ids],
                )
                conn.commit()
            return len(delete_ids)

    def count(self) -> int:
        with self._lock:
            row = self._connect().execute(
                "SELECT COUNT(*) AS n FROM pipeline_runs"
            ).fetchone()
            return int(row["n"]) if row else 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        data = {k: row[k] for k in row.keys()}
        for key in ("result_json", "events_json"):
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return data


def _mk_marks(items: tuple) -> str:
    return ", ".join("?" for _ in items)


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# Convenience singleton for the server module.
default_store = PipelineStore()