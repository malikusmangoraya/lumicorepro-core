"""Agent Reach environment & capability registration.

The setup initialization layer recognises the Agent Reach CLI footprint
(installed binary, `~/.agent-reach/config.json`, skill dirs) and injects the
structural access parameters — including the read-only verification mapping
`agent-reach install --env=auto` — into the runtime environment WITHOUT calling
blocking external token scripts.

`register_capability_flags()` is guaranteed synchronous and subprocess-free.
The optional `verify_capability()` probe runs `agent-reach doctor` (read-only)
via the async subprocess layer, so it can never stall the FastAPI loop.
"""
import os
import threading
from typing import Any, Dict, List, Optional

from config.settings import (
    AGENT_REACH_ENV,
    AGENT_REACH_HOME,
    AGENT_REACH_SKILL_DIRS,
    AGENT_REACH_VERIFY_CMD,
)
from utils.logger import agent_logger
from agent.reach.process import resolve_tool, in_worker_loop, run_cli

_CAPABILITY_LOCK = threading.RLock()
_CAPABILITY: Optional[Dict[str, Any]] = None
_VERIFY_AT = 0.0
_VERIFY_TTL = 3600.0


def _detect_skill_dirs() -> List[str]:
    found: List[str] = []
    for candidate in AGENT_REACH_SKILL_DIRS:
        if candidate.is_dir():
            found.append(str(candidate))
    config_path = AGENT_REACH_HOME / "config.json"
    if config_path.is_file():
        found.append(str(config_path))
    return found


def register_capability_flags() -> Dict[str, Any]:
    """Inject Agent Reach structural access parameters into os.environ + module state.

    Synchronous, zero subprocess, never raises. Safe to call at orchestrator
    construction and FastAPI startup.
    """
    global _CAPABILITY
    with _CAPABILITY_LOCK:
        cli = resolve_tool("agent-reach")
        skill_dirs = _detect_skill_dirs()
        footprint = {
            "available": cli is not None,
            "cli": cli or "",
            "env_mode": AGENT_REACH_ENV,
            "home": str(AGENT_REACH_HOME),
            "skill_dirs": skill_dirs,
            "verify_cmd": AGENT_REACH_VERIFY_CMD,
        }
        flags = {
            "AGENT_REACH_AVAILABLE": "1" if cli else "0",
            "AGENT_REACH_CLI": cli or "",
            "AGENT_REACH_ENV": AGENT_REACH_ENV,
            "AGENT_REACH_HOME": str(AGENT_REACH_HOME),
            "AGENT_REACH_SKILL_DIRS": os.pathsep.join(skill_dirs),
            "AGENT_REACH_VERIFY_CMD": AGENT_REACH_VERIFY_CMD,
        }
        for key, value in flags.items():
            os.environ[key] = value
        if _CAPABILITY is None:
            _CAPABILITY = footprint
            agent_logger.debug(f"Agent Reach capability footprint: {footprint}")
        return footprint


async def verify_capability(force: bool = False) -> Dict[str, Any]:
    """Read-only capability probe via `agent-reach doctor` (async subprocess).

    Never configures channels or launches token scripts; returns the same
    footprint plus the doctor summary when the CLI is present.
    """
    global _VERIFY_AT
    footprint = register_capability_flags()
    import time as _time

    now = _time.time()
    if not force and (now - _VERIFY_AT) < _VERIFY_TTL:
        return footprint
    cli = footprint.get("cli")
    verified = {"doctor_ok": False, "channels_probed": 0}
    if cli:
        result = await run_cli([cli, "doctor", "--json"], timeout=30)
        verified["doctor_ok"] = result.returncode == 0
        verified["channels_probed"] = len(result.stdout.splitlines())
        verified["output_tail"] = (result.stdout or result.stderr)[-400:]
    _VERIFY_AT = _time.time()
    return {**footprint, "verified": verified}


def capability_sync() -> Dict[str, Any]:
    """Synchronous accessor for callers that cannot await (cache-first)."""
    footprint = register_capability_flags()
    result = in_worker_loop(lambda: verify_capability())
    if result is None:
        return footprint
    return result