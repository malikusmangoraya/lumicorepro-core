"""External open-source coding agents - opencode + freebuff bridges.

LumicorePro delegates heavy coding work to battle-tested open source agents
instead of re-implementing their loops. Both CLIs are optional and free:

  opencode run <task> --auto   (github.com/anomalyco/opencode, MIT)
  freebuff <task>              (github.com/CodebuffAI/freebuff, Apache-2.0)

Design rules:
  * argv-list subprocess only (no shell, no injection surface).
  * `stdin` is closed so a CLI can never block waiting for a terminal.
  * hard timeout + output tail; callers run this off the event loop.
  * a missing/invalid project directory is refused instead of falling back to
    the agent's own cwd - an external agent must never edit LumicorePro itself.
  * `unsupported` is a first-class status: freebuff's CLI is a TUI with no
    headless flag, so pretending it can run unattended would hang a worker.
  * `not_available` is a first-class status, never an exception - callers
    (`server.py` endpoints) degrade gracefully to the built-in engines.
"""
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

_MAX_TASK_CHARS = 8000
_MAX_ARG_CHARS = 500
_MAX_EXTRA_ARGS = 20
_DEFAULT_TIMEOUT = 1800
_TAIL_CHARS = 6000
_PROBE_TIMEOUT = 15
_STATUS_TTL_S = 60

# Flags that prove a CLI can run one prompt and exit without a TTY.
_HEADLESS_FLAGS = ("--print", "--non-interactive", "--headless", "--prompt")

_status_cache: Dict[str, Any] = {"at": 0.0, "data": None}
_status_lock = threading.Lock()


def _resolve_tool(name: str) -> Optional[str]:
    """Resolve a CLI on PATH, accepting Windows .cmd/.exe/.ps1 shims."""
    resolved = shutil.which(name)
    if resolved:
        return resolved
    for candidate in (f"{name}.cmd", f"{name}.exe", f"{name}.ps1"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _freebuff_binary() -> Optional[str]:
    """Prefer the cached runtime over the npm shim.

    The `freebuff` npm package is only a downloader: running it re-checks
    codebuff.com on every invocation. The runtime it manages lives at
    ~/.config/manicode/freebuff[.exe] and can be probed without network.
    """
    override = os.environ.get("FREEBUFF_BIN", "").strip()
    if override and Path(override).is_file():
        return override
    cached = Path.home() / ".config" / "manicode" / (
        "freebuff.exe" if os.name == "nt" else "freebuff"
    )
    if cached.is_file():
        return str(cached)
    return _resolve_tool("freebuff")


def _opencode_binary() -> Optional[str]:
    override = os.environ.get("OPENCODE_BIN", "").strip()
    if override and Path(override).is_file():
        return override
    return _resolve_tool("opencode")


def _tail(text: str, max_chars: int = _TAIL_CHARS) -> str:
    cleaned = (text or "").strip()
    return cleaned[-max_chars:]


def _probe(
    binary: str, args: List[str], timeout_s: int = _PROBE_TIMEOUT
) -> Dict[str, Any]:
    """Run a cheap, side-effect-free CLI probe. Never raises."""
    try:
        proc = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=timeout_s,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "output": _tail(f"{proc.stdout}\n{proc.stderr}", 2000),
        }
    except Exception as exc:  # noqa: BLE001 - a probe must never raise
        return {"ok": False, "exit_code": -1, "output": "", "error": str(exc)[:200]}


def _supports_headless(binary: str, kind: str) -> bool:
    """True when the CLI can take one prompt and exit without a TTY.

    Matching is token-exact on purpose: opencode's `--print-logs` global flag
    is not a headless mode, and a substring test would misreport it as one.
    """
    if kind == "opencode":
        text = (_probe(binary, ["run", "--help"]).get("output") or "").lower()
        return "--format" in text and "--auto" in text
    text = (_probe(binary, ["--help"]).get("output") or "").lower()
    tokens = set(re.findall(r"--[a-z0-9-]+", text))
    return bool(tokens & set(_HEADLESS_FLAGS))


def tool_status(force: bool = False) -> Dict[str, Any]:
    """Cheap availability + capability probe for both external CLIs.

    Cached for 60 s: the status endpoint is polled by dashboards, and each
    uncached call spawns two short-lived processes.
    """
    now = time.time()
    with _status_lock:
        if (
            not force
            and _status_cache["data"] is not None
            and now - _status_cache["at"] < _STATUS_TTL_S
        ):
            return _status_cache["data"]

        status: Dict[str, Any] = {}
        for name, resolver in (
            ("opencode", _opencode_binary),
            ("freebuff", _freebuff_binary),
        ):
            binary = resolver()
            entry: Dict[str, Any] = {
                "installed": bool(binary),
                "path": binary or "",
                "headless": False,
            }
            if binary:
                version_args = (
                    ["--standalone", "--version"]
                    if name == "opencode"
                    else ["--version"]
                )
                version = _probe(binary, version_args)
                entry["version"] = _tail(version.get("output", ""), 240)
                entry["version_ok"] = bool(version.get("ok"))
                if version.get("error"):
                    entry["probe_error"] = version["error"]
                entry["headless"] = _supports_headless(binary, name)
                if not entry["headless"]:
                    entry["headless_reason"] = (
                        "CLI is a terminal UI; --help advertises no "
                        "--print/--non-interactive/--headless flag"
                    )
            status[name] = entry

        _status_cache["data"] = status
        _status_cache["at"] = now
        return status


def _validate(project_dir: str, task: str) -> Optional[Dict[str, Any]]:
    """Shared input validation; returns an error result or None."""
    task = (task or "").strip()
    if not task:
        return {"status": "failed", "reason": "invalid_task", "message": "task is required"}
    if len(task) > _MAX_TASK_CHARS:
        return {
            "status": "failed",
            "reason": "invalid_task",
            "message": f"task exceeds {_MAX_TASK_CHARS} chars",
        }
    if not project_dir:
        return {
            "status": "failed",
            "reason": "invalid_project_dir",
            "message": "project_dir is required",
        }
    path = Path(project_dir)
    if not path.is_dir():
        return {
            "status": "failed",
            "reason": "invalid_project_dir",
            "message": f"project_dir is not a directory: {project_dir}",
        }
    return None


def _run_agent(
    binary: str,
    args: List[str],
    project_dir: str,
    timeout_s: int,
) -> Dict[str, Any]:
    """Execute one agent run in `project_dir` with a hard timeout."""
    try:
        timeout_s = max(30, min(int(timeout_s), 7200))
    except (TypeError, ValueError):
        return {
            "status": "failed",
            "reason": "invalid_timeout",
            "message": "timeout_s must be an integer between 30 and 7200",
        }
    workdir = str(Path(project_dir))
    started = time.time()
    try:
        proc = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=timeout_s,
            cwd=workdir,
        )
        elapsed = round(time.time() - started, 2)
        stdout = _tail(proc.stdout)
        stderr = _tail(proc.stderr)
        if proc.returncode == 0:
            return {
                "status": "passed",
                "exit_code": 0,
                "duration_secs": elapsed,
                "cwd": workdir,
                "output": stdout,
                "error": stderr,
            }
        crash = "Bun has crashed" in stderr or "Segmentation fault" in stderr
        return {
            "status": "failed",
            "reason": "runtime_crash" if crash else "exit_nonzero",
            "exit_code": proc.returncode,
            "duration_secs": elapsed,
            "cwd": workdir,
            "output": stdout,
            "error": stderr,
        }
    except FileNotFoundError:
        return {"status": "not_available", "message": f"CLI not found: {binary}"}
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "reason": "timeout",
            "exit_code": -1,
            "message": f"timeout after {timeout_s}s",
            "duration_secs": round(time.time() - started, 2),
        }
    except Exception as exc:  # noqa: BLE001
        agent_logger.warning(f"[EXTERNAL AGENT] {binary} failed: {exc}")
        return {"status": "failed", "reason": "spawn_error", "message": str(exc)[:300]}


def run_opencode(
    project_dir: str,
    task: str,
    model: Optional[str] = None,
    agent: Optional[str] = None,
    auto: bool = True,
    standalone: bool = True,
    format: str = "default",
    timeout_s: int = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Run opencode headlessly on a project (`opencode run <task>`).

    `--standalone` keeps the run on a private server. Without it opencode uses
    (and may spawn) a shared background service whose detached child inherits
    the stdout pipe, which makes a finished CLI look hung to the caller.
    """
    binary = _opencode_binary()
    if not binary:
        return {"status": "not_available", "message": "opencode CLI not installed"}
    invalid = _validate(project_dir, task)
    if invalid:
        return invalid
    if format not in ("default", "json"):
        return {
            "status": "failed",
            "reason": "invalid_format",
            "message": "format must be 'default' or 'json'",
        }
    if model and len(model) > _MAX_ARG_CHARS:
        return {"status": "failed", "reason": "invalid_model", "message": "model is too long"}
    if agent and len(agent) > _MAX_ARG_CHARS:
        return {"status": "failed", "reason": "invalid_agent", "message": "agent is too long"}

    args = ["run", task.strip(), "--format", format]
    if model:
        args.extend(["--model", model])
    if agent:
        args.extend(["--agent", agent])
    if auto:
        args.append("--auto")
    if standalone:
        args.append("--standalone")
    return _run_agent(binary, args, project_dir, timeout_s)


def run_freebuff(
    project_dir: str,
    task: str,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = _DEFAULT_TIMEOUT,
    interactive: bool = False,
) -> Dict[str, Any]:
    """Run the freebuff CLI headlessly on a project.

    freebuff (codecane) ships as a terminal UI: `--help` exposes only
    `--agent`, `--clear-logs`, `--help` and `--version`. Launching it without a
    TTY starts the UI, waits for a terminal and, on the Windows build tested
    here, crashes in Bun. It therefore returns `unsupported` unless the
    installed CLI actually advertises a headless flag, or the caller explicitly
    opts into `interactive=True` (e.g. a future release with a `--print` mode).
    """
    binary = _freebuff_binary()
    if not binary:
        return {"status": "not_available", "message": "freebuff CLI not installed"}
    invalid = _validate(project_dir, task)
    if invalid:
        return invalid

    extra = [str(a) for a in (extra_args or [])]
    if len(extra) > _MAX_EXTRA_ARGS:
        return {
            "status": "failed",
            "reason": "invalid_args",
            "message": f"extra_args exceeds {_MAX_EXTRA_ARGS} entries",
        }
    if any(len(a) > _MAX_ARG_CHARS for a in extra):
        return {
            "status": "failed",
            "reason": "invalid_args",
            "message": f"an extra_arg exceeds {_MAX_ARG_CHARS} chars",
        }

    headless = _supports_headless(binary, "freebuff")
    if not headless and not interactive:
        return {
            "status": "unsupported",
            "reason": "no_headless_mode",
            "headless": False,
            "path": binary,
            "message": (
                "freebuff is a terminal UI with no headless flag "
                "(--print/--non-interactive/--headless). Run it in a terminal, "
                "or pass interactive=True to opt in to TUI execution."
            ),
        }

    args = [task.strip(), *extra]
    result = _run_agent(binary, args, project_dir, timeout_s)
    result["headless"] = headless
    return result
