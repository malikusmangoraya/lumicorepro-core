"""Auto mode — one-call, zero-prompt, budget-enforced generation runs.

This module is the single autonomous contract for the LumicorePro website
factory. ``run_auto()`` wraps the 18-phase orchestrator with three guarantees
the raw ``run(interactive=False)`` path cannot give on its own:

1. **No interactive input, ever.** ``builtins.input`` is patched to raise
   :class:`AutoModeInputBlocked` for the duration of the run, so any engine
   that still tries to prompt (planner, design customizer, ambiguity
   re-prompt) fails loud instead of hanging on a terminal that is not there.
2. **A total wall-clock budget.** :data:`AUTO_RUN_TIMEOUT_SECS` caps the whole
   run (not just individual phases). On expiry the orchestrator's cooperative
   cancellation hook is tripped so the worker stops at the next phase
   boundary instead of burning provider spend in the background, and
   :class:`AutoModeTimeout` is raised.
3. **An enforced failure budget.** The orchestrator declares
   ``NON_CRITICAL_FAILURE_LIMIT`` but never checks it; auto mode does. A run
   whose non-critical failure count exceeds the limit is downgraded to
   ``failed`` with reason ``auto_failure_budget_exceeded`` instead of shipping
   a heavily degraded build as ``partial``.

An optional post-run autopilot audit (guardrails + self-heal + quality) can be
attached with ``run_autopilot=True``.
"""

from __future__ import annotations

import builtins
import concurrent.futures
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from utils.logger import agent_logger

#: Total wall-clock budget for one auto run (seconds). Override per call.
AUTO_RUN_TIMEOUT_SECS = 1800

#: Reason code recorded when the failure budget is exceeded.
REASON_FAILURE_BUDGET = "auto_failure_budget_exceeded"
#: Reason code recorded when the wall-clock budget is exceeded.
REASON_TIMEOUT = "auto_timeout_exceeded"


class AutoModeError(RuntimeError):
    """Base error for auto-mode contract violations."""


class AutoModeInputBlocked(AutoModeError):
    """Raised when an engine attempts interactive input during an auto run."""


class AutoModeTimeout(AutoModeError):
    """Raised when an auto run exceeds its total wall-clock budget."""


@contextmanager
def block_interactive_input() -> Iterator[None]:
    """Patch ``input()`` to fail loud for the duration of an auto run."""
    real_input = builtins.input

    def _guarded(prompt: str = "") -> str:
        raise AutoModeInputBlocked(
            "Interactive input() was called during an auto-mode run. "
            f"Prompt text: {str(prompt)[:120]}"
        )

    builtins.input = _guarded  # type: ignore[assignment]
    try:
        yield
    finally:
        builtins.input = real_input


def _failure_count(report: Dict[str, Any]) -> int:
    failures = report.get("phase_failures") or []
    return len(failures) if isinstance(failures, list) else 0


def run_auto(
    prompt: str,
    *,
    design_style: Optional[str] = None,
    page_scaffold: Optional[str] = None,
    provider: Optional[str] = None,
    timeout_secs: int = AUTO_RUN_TIMEOUT_SECS,
    run_autopilot: bool = False,
    autopilot_fixes: bool = False,
    progress_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    cancel_check: Optional[Callable[[], None]] = None,
    extra_spec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the full factory with zero human input under hard budgets.

    Returns the orchestrator report with an ``auto_mode`` block attached::

        {
            ...orchestrator report...,
            "auto_mode": {
                "mode": "auto",
                "timeout_secs": ...,
                "elapsed_secs": ...,
                "failure_limit": ...,
                "failure_count": ...,
                "failure_budget_exceeded": bool,
                "input_guard": "enforced",
                "autopilot": {...} | None,
            },
        }

    Raises :class:`AutoModeTimeout` on budget expiry and
    :class:`AutoModeInputBlocked` if any engine prompts.
    """
    from .orchestrator import AgentOrchestrator, PipelineCancelled

    started = time.time()
    spec_extra: Dict[str, Any] = dict(extra_spec or {})
    if page_scaffold:
        constraints = dict(spec_extra.get("design_constraints") or {})
        constraints.setdefault("page_scaffold", page_scaffold)
        spec_extra["design_constraints"] = constraints

    orchestrator = AgentOrchestrator(provider_name=provider)
    failure_limit = int(getattr(orchestrator, "NON_CRITICAL_FAILURE_LIMIT", 5) or 5)

    # Cooperative timeout: tripping this event makes the orchestrator abort at
    # the next phase boundary via its cancel_check hook.
    timed_out = threading.Event()

    def _auto_cancel_check() -> None:
        if timed_out.is_set():
            raise PipelineCancelled("Auto-mode wall-clock budget exceeded")
        if cancel_check is not None:
            cancel_check()

    orchestrator.cancel_check = _auto_cancel_check

    def _target() -> Dict[str, Any]:
        with block_interactive_input():
            return orchestrator.run(
                prompt,
                interactive=False,
                progress_callback=progress_callback,
                design_style=design_style,
                extra_spec=spec_extra or None,
            )

    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="lumi-auto"
    )
    try:
        future = executor.submit(_target)
        try:
            report = future.result(timeout=max(1, int(timeout_secs)))
        except concurrent.futures.TimeoutError as exc:
            timed_out.set()
            raise AutoModeTimeout(
                f"Auto run exceeded its {timeout_secs}s wall-clock budget."
            ) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    if not isinstance(report, dict):
        raise AutoModeError("Auto run produced no report.")

    failures = _failure_count(report)
    budget_exceeded = failures > failure_limit and report.get("status") != "failed"
    if budget_exceeded:
        report["status"] = "failed"
        report["reason"] = REASON_FAILURE_BUDGET
        agent_logger.warning(
            "Auto mode: %d non-critical failures exceed limit %d — "
            "run downgraded to failed.",
            failures, failure_limit,
        )

    autopilot_report: Optional[Dict[str, Any]] = None
    if run_autopilot:
        project_dir = str(report.get("generated_project_dir") or "")
        if project_dir and os.path.isdir(project_dir):
            try:
                from .autopilot import audit_project
                autopilot_report = audit_project(Path(project_dir), apply_fixes=autopilot_fixes)
            except Exception as exc:  # noqa: BLE001 — audit is observational
                agent_logger.warning(f"Auto-mode autopilot audit skipped: {exc}")
                autopilot_report = {"ok": False, "reason": str(exc)[:200]}
        else:
            autopilot_report = {"ok": False, "reason": "no_project_directory"}

    report["auto_mode"] = {
        "mode": "auto",
        "timeout_secs": int(timeout_secs),
        "elapsed_secs": round(time.time() - started, 2),
        "failure_limit": failure_limit,
        "failure_count": failures,
        "failure_budget_exceeded": bool(budget_exceeded),
        "input_guard": "enforced",
        "page_scaffold": page_scaffold,
        "autopilot": autopilot_report,
    }
    return report


def describe_auto_mode() -> Dict[str, Any]:
    """Machine-readable auto-mode contract (budgets, guarantees, entry points)."""
    from .orchestrator import AgentOrchestrator

    return {
        "mode": "auto",
        "entry_python": "agent.auto_mode.run_auto",
        "entry_http": "POST /api/auto",
        "entry_cli": "python main.py --auto --prompt ...",
        "guarantees": [
            "zero interactive input (input() raises AutoModeInputBlocked)",
            f"total wall-clock budget (default {AUTO_RUN_TIMEOUT_SECS}s, AutoModeTimeout on expiry)",
            "failure budget enforced (NON_CRITICAL_FAILURE_LIMIT="
            f"{AgentOrchestrator.NON_CRITICAL_FAILURE_LIMIT}, downgrade to failed)",
            "cooperative cancellation on timeout (no orphaned provider spend)",
            "optional post-run autopilot audit (guardrails + self-heal + quality)",
        ],
        "report_block": "auto_mode",
    }
