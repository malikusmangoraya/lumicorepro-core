"""Isolated SQLite storage for generated-project design fingerprints."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import AGENT_DB_PATH


class DesignRegistry:
    """Persist portfolio signatures without changing existing registry tables."""

    TABLE_NAME = "design_portfolio_signatures_v1"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or AGENT_DB_PATH)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        project TEXT PRIMARY KEY,
                        fingerprint TEXT NOT NULL,
                        dimensions_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )"""
                )

    def list_signatures(self, exclude_project: Optional[str] = None) -> List[Dict[str, Any]]:
        self.initialize()
        query = (
            f"SELECT project, fingerprint, dimensions_json, created_at "
            f"FROM {self.TABLE_NAME}"
        )
        parameters: tuple = ()
        if exclude_project:
            query += " WHERE project <> ?"
            parameters = (exclude_project,)
        query += " ORDER BY project"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        signatures = []
        for project, fingerprint, dimensions_json, created_at in rows:
            try:
                dimensions = json.loads(dimensions_json)
            except (TypeError, json.JSONDecodeError):
                dimensions = {}
            signatures.append({
                "project": project,
                "fingerprint": fingerprint,
                "dimensions": dimensions if isinstance(dimensions, dict) else {},
                "created_at": created_at,
            })
        return signatures

    def record(self, project: str, fingerprint: str, dimensions: Dict[str, Any]) -> None:
        self.initialize()
        created_at = datetime.now(timezone.utc).isoformat()
        dimensions_json = json.dumps(dimensions or {}, sort_keys=True, separators=(",", ":"))
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    f"""INSERT INTO {self.TABLE_NAME}
                        (project, fingerprint, dimensions_json, created_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(project) DO UPDATE SET
                            fingerprint = excluded.fingerprint,
                            dimensions_json = excluded.dimensions_json,
                            created_at = excluded.created_at""",
                    (str(project), str(fingerprint), dimensions_json, created_at),
                )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5.0)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection