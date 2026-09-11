"""Neon Serverless Postgres — Auto-Provisioning Service
=========================================================
Creates ephemeral PostgreSQL databases via the Neon API and returns
connection strings that are injected into generated projects.

Requires: NEON_API_KEY environment variable.
Docs: https://neon.tech/docs/manage/neon-api
"""
import json
import os
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger


NEON_API_BASE = "https://console.neon.tech/api/v2"
DEFAULT_BRANCH = "main"


class NeonProvisionError(Exception):
    """Raised when Neon API provisioning fails."""
    pass


class NeonService:
    """Manages ephemeral Neon Postgres databases for generated projects."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEON_API_KEY", "")
        self.enabled = bool(self.api_key and not self.api_key.startswith("your_"))

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> Dict[str, Any]:
        """Make an authenticated request to the Neon API."""
        if not self.enabled:
            raise NeonProvisionError("NEON_API_KEY not configured")

        url = f"{NEON_API_BASE}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(
            url,
            method=method,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode() if exc.fp else str(exc)
            raise NeonProvisionError(f"Neon API error {exc.code}: {error_body}")

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all Neon projects."""
        result = self._request("GET", "/projects")
        return result.get("projects", [])

    def create_project(self, name: str, region: str = "us-east-1") -> Dict[str, Any]:
        """Create a new Neon project. Returns project with connection URIs."""
        payload = {
            "project": {
                "name": name,
                "region_id": region,
            }
        }
        result = self._request("POST", "/projects", payload)
        project = result.get("project", {})
        connection_uris = result.get("connection_uris", [])
        agent_logger.info(f"Neon project created: {project.get('id')} ({name}) in {region}")
        return {
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "region": project.get("region_id"),
            "connection_uris": connection_uris,
            "host": project.get("connection_uris", [{}])[0].get("host") if connection_uris else "",
            "branch_id": project.get("default_branch_id"),
        }

    def create_branch(self, project_id: str, branch_name: str = "lumicore") -> Dict[str, Any]:
        """Create a branch in an existing project (for isolation)."""
        payload = {
            "branch": {
                "name": branch_name,
            }
        }
        result = self._request("POST", f"/projects/{project_id}/branches", payload)
        branch = result.get("branch", {})
        connection_uris = result.get("connection_uris", [])
        return {
            "branch_id": branch.get("id"),
            "branch_name": branch.get("name"),
            "connection_uris": connection_uris,
            "host": connection_uris[0].get("host") if connection_uris else "",
        }

    def get_connection_string(self, project_id: str, branch_id: Optional[str] = None,
                               database: str = "neondb", role: str = "neondb_owner") -> str:
        """Get the connection string for a project/branch."""
        params = urllib.parse.urlencode({"branch_id": branch_id or "", "database": database, "role": role})
        result = self._request("GET", f"/projects/{project_id}/connection_uri?{params}")
        return result.get("uri", "")

    def provision_database(self, project_name: str, region: str = "us-east-1") -> Dict[str, Any]:
        """Full provisioning: create project → get connection string → return payload."""
        if not self.enabled:
            agent_logger.info("Neon provisioning disabled (no API key) — returning mock")
            return {
                "status": "mock",
                "host": "ep-mock-123456.us-east-1.aws.neon.tech",
                "database": "neondb",
                "connection_string": "postgresql://neondb_owner:xxxx@ep-mock-123456.us-east-1.aws.neon.tech/neondb?sslmode=require",
                "project_id": "",
                "region": region,
            }

        slug = project_name.lower().replace(" ", "-").replace("_", "-")[:40]
        try:
            project = self.create_project(slug, region)
            conn_str = self.get_connection_string(project["project_id"], project.get("branch_id"))
            return {
                "status": "live",
                "project_id": project["project_id"],
                "branch_id": project.get("branch_id"),
                "host": project.get("host"),
                "database": "neondb",
                "connection_string": conn_str,
                "region": region,
            }
        except NeonProvisionError as exc:
            agent_logger.warning(f"Neon provision failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "region": region,
            }

    def delete_project(self, project_id: str) -> bool:
        """Delete a Neon project (cleanup ephemeral databases)."""
        if not self.enabled:
            return False
        try:
            self._request("DELETE", f"/projects/{project_id}")
            agent_logger.info(f"Neon project deleted: {project_id}")
            return True
        except NeonProvisionError:
            return False


def inject_neon_env(connection_string: str, project_dir: str) -> Dict[str, str]:
    """Inject NEON connection string into .env file of a generated project."""
    env_path = os.path.join(project_dir, ".env")
    env_example_path = os.path.join(project_dir, ".env.example")
    env_content = ""
    if os.path.exists(env_path):
        env_content = open(env_path, "r", encoding="utf-8").read()
    elif os.path.exists(env_example_path):
        env_content = open(env_example_path, "r", encoding="utf-8").read()

    if "DATABASE_URL" in env_content:
        lines = env_content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("DATABASE_URL"):
                lines[i] = f"DATABASE_URL={connection_string}"
                env_content = "\n".join(lines)
                break
    else:
        env_content += f"\nDATABASE_URL={connection_string}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    return {"env_path": env_path, "key": "DATABASE_URL"}


def run_migrations(connection_string: str, schema_path: str) -> Dict[str, Any]:
    """Run SQL schema against a Neon database using the Neon SQL endpoint."""
    if not os.path.exists(schema_path):
        return {"status": "skipped", "reason": f"Schema file not found: {schema_path}"}

    try:
        import psycopg2
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        cur = conn.cursor()
        schema = open(schema_path, "r", encoding="utf-8").read()
        cur.execute(schema)
        cur.close()
        conn.close()
        return {"status": "applied", "schema": schema_path}
    except ImportError:
        return {"status": "skipped", "reason": "psycopg2 not installed — run migrations manually"}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
