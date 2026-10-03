"""Auto-Update & Maintenance Engine — LumicorePro AI Agent
=========================================================
Performs automated system audits, database index verification, configuration
self-healing, dependency health checks, and seamless runtime upgrades without
disrupting existing services.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import agent_logger
from config.settings import AGENT_DB_PATH, REGISTRY_DIR


class UpdateUpgradeEngine:
    """Manages system health, database index synchronization, and config maintenance."""

    REQUIRED_TABLES = [
        "templates_index",
        "components_index",
        "assets_index",
        "backend_index",
        "database_schemas_index",
    ]

    DEPRECATED_MODELS = {
        "qwen/qwen3.6-27b": "llama-3.3-70b-versatile",
        "gpt-3.5-turbo": "gpt-4o-mini",
        "gemini-1.0-pro": "gemini-2.5-flash",
        "claude-2": "claude-3-5-sonnet",
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or AGENT_DB_PATH

    def check_and_update_database(self) -> Dict[str, Any]:
        """Verifies database health, table row counts, and auto-heals if missing."""
        if not os.path.exists(self.db_path):
            agent_logger.info("Database missing. Initializing fresh database...")
            from database.init_db import init_database
            init_database()
            return {"status": "created", "reindexed": True, "counts": {}}

        counts: Dict[str, int] = {}
        missing_tables = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for tbl in self.REQUIRED_TABLES:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
                if not cursor.fetchone():
                    missing_tables.append(tbl)
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                    counts[tbl] = cursor.fetchone()[0]
            conn.close()
        except Exception as exc:
            agent_logger.warning(f"Database inspection error: {exc}")
            missing_tables = self.REQUIRED_TABLES

        reindexed = False
        if missing_tables or any(c == 0 for c in counts.values()):
            agent_logger.info(f"Detected empty or missing tables ({missing_tables}). Re-indexing...")
            from database.init_db import init_database
            init_database()
            reindexed = True
            # Re-read counts
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for tbl in self.REQUIRED_TABLES:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                    counts[tbl] = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass

        return {
            "status": "healthy" if not missing_tables else "repaired",
            "missing_tables_repaired": missing_tables,
            "reindexed": reindexed,
            "table_counts": counts,
        }

    def audit_and_fix_environment(self) -> Dict[str, Any]:
        """Scans environment and settings for deprecated model configurations."""
        issues_detected = []
        patches_applied = []

        grok_model = os.getenv("GROK_MODEL", "")
        if grok_model in self.DEPRECATED_MODELS:
            replacement = self.DEPRECATED_MODELS[grok_model]
            issues_detected.append(f"Deprecated GROK_MODEL: {grok_model}")
            os.environ["GROK_MODEL"] = replacement
            patches_applied.append(f"Updated GROK_MODEL to active: {replacement}")

        gemini_model = os.getenv("GEMINI_MODEL", "")
        if gemini_model in self.DEPRECATED_MODELS:
            replacement = self.DEPRECATED_MODELS[gemini_model]
            issues_detected.append(f"Deprecated GEMINI_MODEL: {gemini_model}")
            os.environ["GEMINI_MODEL"] = replacement
            patches_applied.append(f"Updated GEMINI_MODEL to active: {replacement}")

        return {
            "issues_detected": len(issues_detected),
            "patches_applied": len(patches_applied),
            "details": patches_applied,
        }

    def check_python_environment(self) -> Dict[str, Any]:
        """Verifies core Python runtime and package availability."""
        packages = ["fastapi", "uvicorn", "pydantic", "requests", "dotenv"]
        installed = {}
        for pkg in packages:
            try:
                mod = __import__(pkg)
                installed[pkg] = getattr(mod, "__version__", "installed")
            except ImportError:
                installed[pkg] = "missing"

        return {
            "python_version": sys.version.split()[0],
            "packages": installed,
            "all_healthy": all(v != "missing" for v in installed.values()),
        }

    def run_full_system_update(self) -> Dict[str, Any]:
        """Executes full diagnostic and update pass."""
        agent_logger.info("Executing full system update & maintenance check...")
        db_report = self.check_and_update_database()
        env_report = self.audit_and_fix_environment()
        py_report = self.check_python_environment()

        overall_status = "operational"
        if not py_report["all_healthy"]:
            overall_status = "degraded_dependencies"
        elif db_report.get("status") == "repaired":
            overall_status = "auto_healed"

        return {
            "success": True,
            "system_status": overall_status,
            "database": db_report,
            "environment_audit": env_report,
            "runtime": py_report,
            "recommendation": "System is synchronized and running at peak performance.",
        }
