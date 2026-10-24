"""External open-source coding agents - opencode + freebuff bridges.

LumicorePro delegates heavy coding work to battle-tested open source agents
instead of re-implementing their loops. Both CLIs are optional and free:

  opencode run <task> --auto   (github.com/anomalyco/opencode, MIT)
  freebuff <task>              (github.com/CodebuffAI/freebuff, Apache-2.0)

Design rules:
  * argv-list subprocess only (no shell, no injection surface).
  * hard timeout + output tail; never blocks the FastAPI loop for good.
  * not_available is a first-class status, never an exception - callers
    (`server.py` endpoints) degrade gracefully to the built-in engines.
"""
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

_MAX_TASK_CHARS = 8000
_DEFAULT_TIMEOUT = 1800
_TAIL_CHARS = 6000


def _resolve_tool(name: str) -> Optional[str]:
    candidates = [name]
    if shutil.which(name):
        return shutil.which(name)
    for candidate in (f"{name}.cmd", f"{name}.exe", f"{name}.ps1"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return shutil.which(name)


def _tail(text: str, max_chars: int = _TAIL_CHARS) -> str:
    cleaned = (text or "").strip()
    return cleaned[-max_chars:]


def tool_status() -> Dict[str, Any]:
    """Cheap availability probe for both external CLIs."""
    status = {}
    for name in ("opencode", "freebuff"):
        resolved = _resolve_tool(name)
        entry: Dict[str, Any] = {
            "installed": bool(resolved),
            "path": resolved or "",
        }
        if resolved:
            try:
                probe = subprocess.run(
                    [resolved, "--version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                )
                entry["version"] = _tail(
                    f"{probe.stdout}\n{probe.stderr}".strip(), 240
                )
            except Exception as exc:  # noqa: BLE001 - probe must never raise
                entry["version"] = ""
                entry["probe_error"] = str(exc)[:200]
        status[name] = entry
    return status


def _run_agent(
    binary: str,
    args: List[str],
    project_dir: str,
    timeout_s: int,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    workdir = cwd or (str(Path(project_dir)) if project_dir and Path(project_dir).is_dir() else None)
    started = time.time()
    try:
        proc = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            cwd=workdir,
        )
        ok = proc.returncode == 0
        return {
            "status": "passed" if ok else "failed",
            "exit_code": proc.returncode,
            "duration_secs": round(time.time() - started, 2),
            "cwd": workdir or "",
            "output": _tail(proc.stdout),
            "error": _tail(proc.stderr),
        }
    except FileNotFoundError:
        return {"status": "not_available", "message": f"CLI not found: {binary}"}
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": -1,
            "message": f"timeout after {timeout_s}s",
            "duration_secs": round(time.time() - started, 2),
        }
    except Exception as exc:  # noqa: BLE001
        agent_logger.warning(f"[EXTERNAL AGENT] {binary} failed: {exc}")
        return {"status": "failed", "message": str(exc)[:300]}


def run_opencode(
    project_dir: str,
    task: str,
    model: Optional[str] = None,
    agent: Optional[str] = None,
    auto: bool = True,
    format: str = "default",
    timeout_s: int = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Run opencode headlessly on a project (`opencode run <task>`)."""
    binary = _resolve_tool("opencode")
    if not binary:
        return {"status": "not_available", "message": "opencode CLI not installed"}
    task = (task or "").strip()
    if not task:
        return {"status": "failed", "message": "task is required"}
    if len(task) > _MAX_TASK_CHARS:
        return {"status": "failed", "message": f"task exceeds {_MAX_TASK_CHARS} chars"}
    if format not in ("default", "json"):
        return {"status": "failed", "message": "format must be 'default' or 'json'"}
    args = ["run", task, "--format", format]
    if model:
        args.extend(["--model", model])
    if agent:
        args.extend(["--agent", agent])
    if auto:
        args.append("--auto")
    return _run_agent(binary, args, project_dir, timeout_s)


def run_freebuff(
    project_dir: str,
    task: str,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Run the freebuff CLI headlessly on a project."""
    binary = _resolve_tool("freebuff")
    if not binary:
        return {"status": "not_available", "message": "freebuff CLI not installed"}
    task = (task or "").strip()
    if not task:
        return {"status": "failed", "message": "task is required"}
    if len(task) > _MAX_TASK_CHARS:
        return {"status": "failed", "message": f"task exceeds {_MAX_TASK_CHARS} chars"}
    args = [task, *(extra_args or [])]
    return _run_agent(binary, args, project_dir, timeout_s)
