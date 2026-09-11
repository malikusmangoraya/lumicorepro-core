"""Platform account + project registry (SQLite, thread-safe).

Skeleton for the future LumicorePro platform: users own projects, and each
project links back to an AI-agent generation run. Users authenticate with a
per-user API key issued at registration (hashed at rest via SHA-256).

Tables (platform.db):
    users(id, email UNIQUE, display_name, api_key_hash, created_at, last_seen_at)
    projects(id, user_id FK, project_name, website_type, run_id, created_at)
"""
import os
import re
import sqlite3
import time
import hashlib
import secrets
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import AI_AGENT_DIR

_DB_PATH = (AI_AGENT_DIR / "database" / "platform.db").resolve()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    display_name   TEXT NOT NULL DEFAULT '',
    api_key_hash   TEXT NOT NULL UNIQUE,
    credits_balance REAL NOT NULL DEFAULT 0,
    credits_used   REAL NOT NULL DEFAULT 0,
    created_at     REAL NOT NULL,
    last_seen_at   REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS projects (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id),
    project_name  TEXT NOT NULL,
    website_type  TEXT NOT NULL DEFAULT '',
    run_id        TEXT NOT NULL DEFAULT '',
    created_at    REAL NOT NULL,
    UNIQUE(user_id, project_name)
);
CREATE TABLE IF NOT EXISTS credit_ledger (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    amount      REAL NOT NULL,
    kind        TEXT NOT NULL,             -- 'grant' | 'spend' | 'refund'
    run_id      TEXT NOT NULL DEFAULT '',
    reason      TEXT NOT NULL DEFAULT '',
    created_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS deployments (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id),
    project_id    TEXT NOT NULL REFERENCES projects(id),
    slug          TEXT NOT NULL UNIQUE,
    platform      TEXT NOT NULL DEFAULT 'lumicore-preview',
    deploy_url    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'preparing',
    created_at    REAL NOT NULL,
    last_accessed_at REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON credit_ledger(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_deploy_user ON deployments(user_id, created_at);
"""


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug[:48] or "project"


class AccountStore:
    """SQLite-backed user/project registry. WAL mode + module lock for safety."""

    def __init__(self, path: Optional[str] = None):
        self.path = str(path or _DB_PATH)
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)
            self._migrate(conn)
            conn.commit()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Idempotently add columns to pre-existing users tables."""
        cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        for col, ddl in (
            ("credits_balance", "ALTER TABLE users ADD COLUMN credits_balance REAL NOT NULL DEFAULT 0"),
            ("credits_used", "ALTER TABLE users ADD COLUMN credits_used REAL NOT NULL DEFAULT 0"),
        ):
            if col not in cols:
                conn.execute(ddl)
                cols.add(col)
        conn.execute("CREATE TABLE IF NOT EXISTS credit_ledger ("
                     "id TEXT PRIMARY KEY, user_id TEXT NOT NULL, amount REAL NOT NULL,"
                     " kind TEXT NOT NULL, run_id TEXT NOT NULL DEFAULT '',"
                     " reason TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS deployments ("
                     "id TEXT PRIMARY KEY, user_id TEXT NOT NULL, project_id TEXT NOT NULL,"
                     " slug TEXT NOT NULL UNIQUE, platform TEXT NOT NULL DEFAULT 'lumicore-preview',"
                     " deploy_url TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'preparing',"
                     " created_at REAL NOT NULL, last_accessed_at REAL NOT NULL DEFAULT 0)")
        deploy_cols = {row[1] for row in conn.execute("PRAGMA table_info(deployments)").fetchall()}
        if "project_dir" not in deploy_cols:
            conn.execute("ALTER TABLE deployments ADD COLUMN project_dir TEXT NOT NULL DEFAULT ''")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Users ────────────────────────────────────────────────────────────
    def create_user(self, email: str, display_name: str = "") -> Dict[str, Any]:
        """Create a user, returning the issued raw API key exactly once."""
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("A valid email is required")
        raw_key = secrets.token_urlsafe(32)
        user_id = secrets.token_hex(16)
        now = time.time()
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (id, email, display_name, api_key_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, email, display_name, _hash_api_key(raw_key), now),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with that email already exists") from exc
        return {"id": user_id, "email": email, "display_name": display_name, "api_key": raw_key}

    def resolve_api_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        """Return the user row for a given API key, or None."""
        digest = _hash_api_key(raw_key)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, display_name, created_at, last_seen_at FROM users WHERE api_key_hash = ?",
                (digest,),
            ).fetchone()
            if row:
                conn.execute("UPDATE users SET last_seen_at = ? WHERE id = ?", (time.time(), row["id"]))
                conn.commit()
            return dict(row) if row else None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, display_name, created_at, last_seen_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    # ── Projects ─────────────────────────────────────────────────────────
    def create_project(
        self,
        user_id: str,
        project_name: str,
        website_type: str = "",
        run_id: str = "",
    ) -> Dict[str, Any]:
        if not self.get_user(user_id):
            raise ValueError("Unknown user")
        project_id = secrets.token_hex(8)
        now = time.time()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (id, user_id, project_name, website_type, run_id, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, user_id, project_name, website_type, run_id, now),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM projects WHERE user_id = ? AND project_name = ?",
                (user_id, project_name),
            ).fetchone()
        return dict(row)

    def list_projects(self, user_id: str, limit: int = 50) -> list:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, project_name, website_type, run_id, created_at FROM projects"
                " WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Deployments (skeleton of the deploy-URL flow) ─────────────────────
    def create_deployment(
        self,
        user_id: str,
        project_name: str,
        run_id: str = "",
        platform: str = "lumicore-preview",
        base_host: str = "lumicorepreview.app",
        project_dir: str = "",
    ) -> Dict[str, Any]:
        """Register a deployment intent; returns a preview-URL placeholder."""
        project_name = (project_name or "").strip()
        if not project_name:
            raise ValueError("project_name is required")
        if not self.get_user(user_id):
            raise ValueError("Unknown user")
        project = self.create_project(user_id, project_name, run_id=run_id)
        slug = _make_slug(project_name)
        unique_slug = slug
        now = time.time()
        with self._lock, self._connect() as conn:
            while conn.execute(
                "SELECT 1 FROM deployments WHERE slug = ?", (unique_slug,)
            ).fetchone():
                unique_slug = f"{slug}-{secrets.token_hex(2)}"
            deploy_id = secrets.token_hex(8)
            deploy_url = f"https://{unique_slug}.{base_host}"
            conn.execute(
                "INSERT INTO deployments (id, user_id, project_id, slug, platform, deploy_url, status, created_at, last_accessed_at, project_dir)"
                " VALUES (?, ?, ?, ?, ?, ?, 'preparing', ?, ?, ?)",
                (deploy_id, user_id, project["id"], unique_slug, platform, deploy_url, now, now, project_dir),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deploy_id,)).fetchone()
        result = dict(row)
        if project_dir:
            result["project_dir"] = str(project_dir)
        return result

    def promote_deployment(self, deploy_id: str, status: str = "live") -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            updated = conn.execute(
                "UPDATE deployments SET status = ?, last_accessed_at = ? WHERE id = ?",
                (status, time.time(), deploy_id),
            ).rowcount
            if not updated:
                return None
            row = conn.execute("SELECT * FROM deployments WHERE id = ?", (deploy_id,)).fetchone()
            return dict(row)

    def list_deployments(self, user_id: str, limit: int = 20) -> list:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, project_id, slug, platform, deploy_url, status, created_at FROM deployments"
                " WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_all_deployments(self, limit: int = 500) -> list:
        """Return every deployment across users — used to hot-reload previews."""
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, slug, deploy_url, status, created_at, project_dir FROM deployments"
                " ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Credits ──────────────────────────────────────────────────────────
    def get_credits(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT credits_balance, credits_used FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    def topup(self, user_id: str, amount: float, reason: str = "manual_grant") -> Dict[str, Any]:
        """Grant credits (later backed by Stripe checkout)."""
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        now = time.time()
        with self._lock, self._connect() as conn:
            updated = conn.execute(
                "UPDATE users SET credits_balance = credits_balance + ? WHERE id = ?",
                (amount, user_id),
            ).rowcount
            if not updated:
                raise ValueError("Unknown user")
            conn.execute(
                "INSERT INTO credit_ledger (id, user_id, amount, kind, reason, created_at) VALUES (?, ?, ?, 'grant', ?, ?)",
                (secrets.token_hex(16), user_id, amount, reason, now),
            )
            balance = conn.execute(
                "SELECT credits_balance FROM users WHERE id = ?", (user_id,)
            ).fetchone()["credits_balance"]
            conn.commit()
        return {"user_id": user_id, "credits_balance": float(balance), "granted": amount}

    def spend(self, user_id: str, amount: float, run_id: str = "", reason: str = "generation") -> bool:
        """Atomically reserve credits; returns False if insufficient balance."""
        amount = float(amount)
        if amount <= 0:
            return True
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT credits_balance FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not row or float(row["credits_balance"]) < amount:
                return False
            conn.execute(
                "UPDATE users SET credits_balance = credits_balance - ?, credits_used = credits_used + ? WHERE id = ?",
                (amount, amount, user_id),
            )
            conn.execute(
                "INSERT INTO credit_ledger (id, user_id, amount, kind, run_id, reason, created_at)"
                " VALUES (?, ?, ?, 'spend', ?, ?, ?)",
                (secrets.token_hex(16), user_id, -amount, run_id, reason, time.time()),
            )
            conn.commit()
        return True

    def refund(self, user_id: str, amount: float, run_id: str = "", reason: str = "") -> bool:
        """Return credits to the balance (e.g. failed/cancelled run)."""
        amount = float(amount)
        if amount <= 0:
            return False
        with self._lock, self._connect() as conn:
            updated = conn.execute(
                "UPDATE users SET credits_balance = credits_balance + ?, credits_used = max(credits_used - ?, 0)"
                " WHERE id = ? AND credits_used >= ?",
                (amount, amount, user_id, amount),
            ).rowcount
            if not updated:
                return False
            conn.execute(
                "INSERT INTO credit_ledger (id, user_id, amount, kind, run_id, reason, created_at)"
                " VALUES (?, ?, ?, 'refund', ?, ?, ?)",
                (secrets.token_hex(16), user_id, amount, run_id, reason, time.time()),
            )
            conn.commit()
        return True


default_account_store = AccountStore()