"""Provision one Postgres database per generated project on an existing server.

Delivery used to stop at the frontend: hosting ``backend/`` and creating its
database were manual steps done outside the pipeline, so a fresh prompt could
never honestly claim a working full-stack product. This module automates the
database half using credentials the owner already has — ``NEON_TEMPLATE_DATABASE_URL``
points at any database on the target server, and the new project database is
created alongside it.

The runner is Node, executed inside the generated ``backend/`` directory: that
package already depends on ``pg``, so provisioning installs nothing new and uses
exactly the driver the deployed app will use.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict

DATABASE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")
TEMPLATE_ENV_VAR = "NEON_TEMPLATE_DATABASE_URL"
_TIMEOUT_SECONDS = 120

# The database name is the one part of CREATE DATABASE that PostgreSQL will not
# accept as a bind parameter: it is validated in provision_database() above and
# double-quoted here.
#
# The credential arrives through the environment, never argv: subprocess errors
# echo their argument list, and a dropped connection timed out that way, printing
# a live Neon password into a log. A pg error also cannot drop the database it is
# connected to, so the runner connects with the template database and targets the
# new name only in SQL.
_CREATE_SCRIPT = """
const { Client } = require('pg');
const url = process.env.LUMICORE_DB_TEMPLATE_URL;
const target = process.argv[1];  // `node -e` puts the first script argument at argv[1]
const client = new Client({ connectionString: url, ssl: { require: true } });
const report = (payload) => console.log(JSON.stringify(payload));
client.connect()
  .then(async () => {
    const found = await client.query('select 1 from pg_database where datname = $1', [target]);
    if (!found.rowCount) {
      await client.query('CREATE DATABASE "' + target.replace(/"/g, '""') + '"');
      report({ ok: true, status: 'created', database: target });
    } else {
      report({ ok: true, status: 'exists', database: target });
    }
    await client.end();
  })
  .catch((error) => {
    report({ ok: false, message: String((error && error.message) || error) });
  });
"""


def _ENV_CANDIDATES():
    """Env files the agent reads, in precedence order.

    ``config.settings`` stops at the first ``.env`` it finds, so a repository-root
    file hides ``ai-agent/.env``; the provisioning credential is read from both.
    """
    agent_root = Path(__file__).resolve().parent.parent
    return [agent_root / ".env", agent_root.parent / ".env"]


def _from_env_files(name: str) -> str:
    for path in _ENV_CANDIDATES():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip().replace("\r", "")
            if stripped.startswith(f"{name}="):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    return ""


def template_url(env_value: str | None = None) -> str:
    """The configured server-wide credential, or "" when the owner has not set one."""
    if env_value is not None:
        return (env_value or "").strip()
    return (os.getenv(TEMPLATE_ENV_VAR, "") or "").strip() or _from_env_files(TEMPLATE_ENV_VAR)


def database_name(slug: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", (slug or "").strip().lower())


def redact(url: str) -> Dict[str, str]:
    """Host and database only — credentials never leave through an evidence dict."""
    parts = urllib.parse.urlsplit(url if "://" in url else f"postgres://{url}")
    return {"host": parts.netloc.split("@")[-1], "database": (parts.path or "").lstrip("/")}


def _run_create(name: str, url: str, backend_dir: str | Path) -> Dict[str, Any]:
    node = shutil.which("node")
    if not node:
        return {"ok": False, "message": "node is unavailable, so the project database cannot be created"}
    env = dict(os.environ, LUMICORE_DB_TEMPLATE_URL=url)
    try:
        proc = subprocess.run([node, "-e", _CREATE_SCRIPT, name], cwd=str(backend_dir), env=env,
                              capture_output=True, text=True, timeout=_TIMEOUT_SECONDS,
                              encoding="utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError) as exc:
        # TimeoutExpired carries the command list; the name is safe, the URL is not.
        return {"ok": False, "message": _scrub(f"database creation did not complete: {type(exc).__name__}", url)}
    lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
    try:
        payload = json.loads(lines[-1]) if lines else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict) or "ok" not in payload:
        tail = ((proc.stderr or "") + " ".join(lines)).strip()[-240:]
        return {"ok": False, "message": _scrub(f"the database runner returned no machine-readable result: {tail}", url)}
    payload["message"] = _scrub(str(payload.get("message", "")), url)
    return payload


def _scrub(text: str, secret: str) -> str:
    """Remove the credential from any message a server error might echo.

    Short fragments are skipped: a one-character password would otherwise match
    ordinary letters in the message it is being scrubbed from.
    """
    if not secret:
        return text
    masked = text.replace(secret, "[connection string]")
    parts = [p for p in re.findall(r"//[^:@/]+:([^@]+)@", secret) + re.findall(r"://([^@]+)@", secret)
             if len(p) >= 4]
    for part in sorted(parts, key=len, reverse=True):
        masked = masked.replace(part, "[credentials]")
    return masked


def provision_database(slug: str, template: str = "", backend_dir: str | Path = ".") -> Dict[str, Any]:
    """Create (or reuse) a database for ``slug`` on the server named by ``template``.

    The returned evidence is safe to put in a report: it names the host and the
    database, never the credentials. ``database_url`` is deliberately absent —
    callers build it with :func:`database_url_for`.
    """
    name = database_name(slug)
    url = (template or "").strip()
    if not DATABASE_NAME_RE.match(name):
        return {"ok": False, "status": "blocked", "database": name,
                "message": f"project name {slug!r} cannot be made into a safe database identifier "
                           "(must start with a letter; lowercase letters, digits and underscores; "
                           "2-31 characters)"}
    if not url:
        return {"ok": False, "status": "blocked", "database": name,
                "message": f"no database server is configured; set {TEMPLATE_ENV_VAR} in ai-agent/.env "
                           "to a connection string for any database on the target server"}
    result = _run_create(name, url, backend_dir)
    if not result.get("ok"):
        return {"ok": False, "status": "failed", "database": name,
                "message": result.get("message", "database creation failed")}
    status = result.get("status", "exists")
    return {"ok": True, "status": status, "database": name, "host": redact(url)["host"],
            "message": "" if status == "created" else "database already existed, reused as-is"}


def database_url_for(template: str, database: str) -> str:
    """Swap the database in the template string for the project's own."""
    parts = urllib.parse.urlsplit(template)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, parts.fragment))
