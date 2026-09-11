"""Async subprocess layer for the Agent Reach integration.

Every external tool invocation (agent-reach doctor, gh, twitter, opencli, rdt,
mcporter) goes through `run_cli`, which spawns native Python asyncio subprocesses
via `asyncio.create_subprocess_exec`. Standard blocking `subprocess.*` calls are
strictly forbidden here — they must never stall the core FastAPI event loop.
"""
import asyncio
import os
import shutil
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ProcessResult:
    """Result of an async subprocess invocation (mirrors quality_gate.CommandResult)."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_secs: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def resolve_tool(name: str) -> Optional[str]:
    """Locate an executable, preferring the .cmd shim on Windows."""
    candidates = [name]
    if os.name == "nt":
        candidates += [f"{name}.cmd", f"{name}.exe"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


async def run_cli(
    args: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = 45.0,
) -> ProcessResult:
    """Execute an external CLI asynchronously and capture stdout/stderr.

    Uses ONLY `asyncio.create_subprocess_exec` (no synchronous system calls).
    Never raises on subprocess failures — a ProcessResult always returned.
    """
    command_line = " ".join(args)
    start = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError as te:
            try:
                process.kill()
                await process.communicate()
            except Exception:
                pass
            return ProcessResult(
                command=command_line,
                returncode=124,
                stdout="",
                stderr=f"Command timed out ({te!r})",
                timed_out=True,
                duration_secs=round(time.time() - start, 3),
            )
        return ProcessResult(
            command=command_line,
            returncode=process.returncode or 0,
            stdout=(stdout or b"").decode("utf-8", errors="replace").strip(),
            stderr=(stderr or b"").decode("utf-8", errors="replace").strip(),
            duration_secs=round(time.time() - start, 3),
        )
    except Exception as exc:
        return ProcessResult(
            command=command_line,
            returncode=1,
            stdout="",
            stderr=str(exc),
            duration_secs=round(time.time() - start, 3),
        )


def _running_loop() -> bool:
    """True when the CURRENT thread already has a live event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def in_worker_loop(coro_factory: Callable[[], Any], timeout: Optional[float] = None) -> Optional[Any]:
    """Run a coroutine in a fresh event loop bound to the CURRENT thread.

    Safe by design:
      - FastAPI request threads always have a running loop -> returns None
        immediately (caller must schedule via `asyncio.create_task`).
      - Worker threads (server runs the sync orchestrator via run_in_executor)
        and the CLI have no running loop -> a dedicated loop is created, run,
        and closed here, so the main FastAPI loop is never blocked.
    """
    if _running_loop():
        return None
    previous = None
    try:
        previous = asyncio.events.get_event_loop()
    except RuntimeError:
        previous = None
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        coro = coro_factory()
        if timeout:
            coro = asyncio.wait_for(coro, timeout=timeout)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.close()
        finally:
            if previous is not None:
                asyncio.set_event_loop(previous)


async def fire_and_forget(coro: Any) -> None:
    """Schedule a coroutine on the current thread's running loop without awaiting.

    Keeps a strong reference so the task is not garbage collected mid-flight.
    """
    loop = asyncio.get_running_loop()
    pending = getattr(loop, "_agent_reach_pending", None)
    if pending is None:
        pending = set()
        setattr(loop, "_agent_reach_pending", pending)
    task = loop.create_task(coro)
    pending.add(task)
    task.add_done_callback(pending.discard)