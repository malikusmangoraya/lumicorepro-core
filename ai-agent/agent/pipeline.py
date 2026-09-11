"""Event-Driven Streaming Pipeline
===================================
Replaces sequential 15-phase execution with a DAG-aware parallel pipeline.

Critical Path (fast TTFR): P1→P2→P3→P4→P5→P6→P7  (~8-15s)
Background Workers:         P8,P9,P10,P11,P12,P13,P14 (run after P7, finish asynchronously)

Usage:
    pipeline = StreamPipeline(progress_callback=ws_emit)
    result = await pipeline.run(prompt, orchestrator)
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from utils.logger import agent_logger


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class PhaseNode:
    name: str
    status: PhaseStatus = PhaseStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    start_time: float = 0.0
    end_time: float = 0.0
    retries: int = 0

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 3)
        return 0.0

    @property
    def is_terminal(self) -> bool:
        return self.status in (PhaseStatus.DONE, PhaseStatus.FAILED, PhaseStatus.SKIPPED, PhaseStatus.CANCELLED)


# ── Phase execution graph ─────────────────────────────────────────────
# Critical path phases run sequentially (fastest path to code output).
# Background phases run in parallel after critical path completes.

CRITICAL_PATH = [
    "market_analysis",
    "requirement_analysis",
    "tech_stack_selection",
    "trending_features_injection",
    "resource_assembly_planning",
    "code_generation",
    "quality_verification",
]

BACKGROUND_PHASES = [
    "improvement_recommendations",
    "competitive_benchmark_delivery",
    "international_delivery",
    "localization_and_i18n",
    "compliance_and_accessibility",
    "seo_and_cdn_optimization",
    "performance_growth_and_webhooks",
    "multi_cloud_global_deployment",
]

# Background phases that share dependencies (can all run after quality_verification)
BACKGROUND_DEPENDENCIES: Dict[str, List[str]] = {
    "improvement_recommendations": ["quality_verification"],
    "competitive_benchmark_delivery": ["quality_verification"],
    "international_delivery": ["code_generation"],
    "localization_and_i18n": ["code_generation"],
    "compliance_and_accessibility": ["code_generation"],
    "seo_and_cdn_optimization": ["code_generation"],
    "performance_growth_and_webhooks": ["code_generation"],
    "multi_cloud_global_deployment": ["code_generation"],
}

# Retries for non-critical background phases
BACKGROUND_MAX_RETRIES = 2
BACKGROUND_TIMEOUT_SECS = 90


class StreamPipeline:
    """DAG-aware parallel pipeline with critical path + background workers."""

    def __init__(
        self,
        progress_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        cancel_check: Optional[Callable[[], None]] = None,
        max_background_workers: int = 4,
    ):
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check
        self.max_background_workers = max_background_workers
        self.phases: Dict[str, PhaseNode] = {}
        self._build_graph()
        self.start_time: float = 0.0

    def _build_graph(self) -> None:
        """Initialize phase nodes."""
        for name in CRITICAL_PATH + BACKGROUND_PHASES:
            self.phases[name] = PhaseNode(name=name)

    def _emit(self, phase: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit a progress event."""
        if self.progress_callback:
            try:
                self.progress_callback(phase, event, data or {})
            except Exception:
                pass

    def _checkpoint_cancel(self) -> None:
        """Raise PipelineCancelled if cooperative abort is set."""
        if self.cancel_check:
            try:
                self.cancel_check()
            except Exception as e:
                raise type(e)(str(e)) from e

    def get_ttfr_estimate(self) -> float:
        """Estimate Time-To-First-Render (critical path only)."""
        return 8.0

    def get_status_summary(self) -> Dict[str, Any]:
        """Return current pipeline status for streaming."""
        done = sum(1 for p in self.phases.values() if p.status == PhaseStatus.DONE)
        total = len(self.phases)
        critical_done = sum(
            1 for p in self.phases.values()
            if p.name in CRITICAL_PATH and p.status == PhaseStatus.DONE
        )
        bg_running = sum(
            1 for p in self.phases.values()
            if p.name in BACKGROUND_PHASES and p.status == PhaseStatus.RUNNING
        )
        return {
            "total_phases": total,
            "completed": done,
            "critical_completed": critical_done,
            "critical_total": len(CRITICAL_PATH),
            "background_running": bg_running,
            "elapsed": round(time.time() - self.start_time, 2) if self.start_time else 0,
            "ttfr_estimate": self.get_ttfr_estimate(),
            "critical_path_done": critical_done == len(CRITICAL_PATH),
        }

    def run_critical_path(
        self,
        phase_handlers: Dict[str, Callable],
        phase_args: Dict[str, list],
        phase_kwargs: Dict[str, dict],
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Execute critical path phases sequentially (fastest path to first render).

        This is a SYNCHRONOUS method designed to be called inside run_in_executor.
        It runs P1-P7 in order, stopping at the first critical failure.
        Returns a dict of phase_name -> result for downstream background phases.
        """
        self.start_time = time.time()
        results: Dict[str, Any] = {}
        market_analysis = {}
        spec: Dict[str, Any] = {}
        tech_stack: Dict[str, Any] = {}
        project_dir = ""
        validation_report = {"valid": True, "errors": [], "warnings": []}
        quality_report = {"overall_score": 0, "enterprise_ready": False}

        for phase_name in CRITICAL_PATH:
            self._checkpoint_cancel()
            node = self.phases[phase_name]
            node.status = PhaseStatus.RUNNING
            node.start_time = time.time()
            self._emit(phase_name, "phase_start", {"ts": node.start_time, "path": "critical"})

            handler = phase_handlers.get(phase_name)
            args = phase_args.get(phase_name, [])
            kwargs = phase_kwargs.get(phase_name, {})

            if not handler:
                node.status = PhaseStatus.SKIPPED
                node.end_time = time.time()
                self._emit(phase_name, "phase_done", {"duration": node.duration, "path": "critical"})
                continue

            attempt = 0
            while attempt <= max_retries:
                try:
                    result = handler(*args, **kwargs)
                    node.result = result
                    node.status = PhaseStatus.DONE
                    node.end_time = time.time()
                    results[phase_name] = result
                    self._emit(phase_name, "phase_done", {
                        "duration": node.duration,
                        "path": "critical",
                        "result_summary": str(result)[:200] if result else "",
                    })

                    # Capture key results for downstream phases
                    if phase_name == "market_analysis":
                        market_analysis = result or {}
                    elif phase_name == "requirement_analysis":
                        spec = result or {}
                        results["spec"] = spec
                    elif phase_name == "tech_stack_selection":
                        tech_stack = result or {}
                    elif phase_name == "code_generation":
                        project_dir = (result or {}).get("project_dir", "")
                        results["project_dir"] = project_dir
                    elif phase_name == "quality_verification":
                        validation_report = (result or {}).get("validation", validation_report)
                        quality_report = (result or {}).get("quality", quality_report)
                        results["validation_report"] = validation_report
                        results["quality_report"] = quality_report
                    break

                except Exception as exc:
                    attempt += 1
                    if attempt > max_retries:
                        node.error = exc
                        node.status = PhaseStatus.FAILED
                        node.end_time = time.time()
                        self._emit(phase_name, "phase_error", {
                            "error": str(exc),
                            "path": "critical",
                        })
                        if phase_name in ("requirement_analysis", "code_generation"):
                            raise  # Critical failure — abort pipeline
                        agent_logger.warning(f"Critical phase {phase_name} failed (non-fatal): {exc}")
                        break
                    agent_logger.warning(f"Retrying critical phase {phase_name} ({max_retries - attempt} left)...")

        elapsed = round(time.time() - self.start_time, 2)
        results["critical_elapsed"] = elapsed
        agent_logger.info(f"Critical path complete in {elapsed}s — {sum(1 for p in CRITICAL_PATH if self.phases[p].status == PhaseStatus.DONE)}/{len(CRITICAL_PATH)} phases done")
        return results

    def run_background_phases(
        self,
        phase_handlers: Dict[str, Callable],
        phase_args: Dict[str, list],
        phase_kwargs: Dict[str, dict],
    ) -> Dict[str, Any]:
        """Execute background phases in parallel using a thread pool.

        This is also SYNCHRONOUS (called via run_in_executor). It uses
        ThreadPoolExecutor to run up to max_background_workers phases concurrently.
        """
        import concurrent.futures

        results: Dict[str, Any] = {}
        ready: Set[str] = set(BACKGROUND_PHASES)
        completed: Set[str] = set()
        bg_start = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_background_workers) as executor:
            futures: Dict[str, concurrent.futures.Future] = {}

            while ready or futures:
                # Submit ready phases (all deps satisfied)
                newly_submitted = []
                for phase_name in list(ready):
                    deps = BACKGROUND_DEPENDENCIES.get(phase_name, [])
                    if all(d in completed or d not in BACKGROUND_PHASES for d in deps):
                        node = self.phases[phase_name]
                        node.status = PhaseStatus.RUNNING
                        node.start_time = time.time()
                        self._emit(phase_name, "phase_start", {"ts": node.start_time, "path": "background"})

                        handler = phase_handlers.get(phase_name)
                        args = phase_args.get(phase_name, [])
                        kwargs = phase_kwargs.get(phase_name, {})

                        if handler:
                            future = executor.submit(self._run_with_timeout, phase_name, handler, args, kwargs)
                            futures[future] = phase_name
                        else:
                            node.status = PhaseStatus.SKIPPED
                            node.end_time = time.time()
                            completed.add(phase_name)
                        ready.discard(phase_name)
                        newly_submitted.append(phase_name)

                if not futures:
                    break

                # Wait for next completion
                done_futures, _ = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

                for future in done_futures:
                    phase_name = futures.pop(future)
                    node = self.phases[phase_name]
                    node.end_time = time.time()

                    try:
                        result = future.result()
                        node.result = result
                        node.status = PhaseStatus.DONE
                        results[phase_name] = result
                        self._emit(phase_name, "phase_done", {
                            "duration": node.duration,
                            "path": "background",
                        })
                    except PipelineCancelled:
                        node.status = PhaseStatus.CANCELLED
                        raise
                    except Exception as exc:
                        node.error = exc
                        node.status = PhaseStatus.FAILED
                        agent_logger.warning(f"Background phase {phase_name} failed: {exc}")
                        self._emit(phase_name, "phase_error", {
                            "error": str(exc),
                            "path": "background",
                        })

                    completed.add(phase_name)

        elapsed = round(time.time() - bg_start, 2)
        results["background_elapsed"] = elapsed
        done_count = sum(1 for p in BACKGROUND_PHASES if self.phases[p].status == PhaseStatus.DONE)
        agent_logger.info(f"Background phases complete in {elapsed}s — {done_count}/{len(BACKGROUND_PHASES)} done")
        return results

    def _run_with_timeout(self, phase_name: str, func: Callable, args: list, kwargs: dict) -> Any:
        """Run a single phase with timeout."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(func, *args, **{k: v for k, v in kwargs.items() if not k.startswith("_")})
            try:
                return future.result(timeout=BACKGROUND_TIMEOUT_SECS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Phase {phase_name} timed out after {BACKGROUND_TIMEOUT_SECS}s")

    def to_full_result(self, critical_results: Dict[str, Any], background_results: Dict[str, Any]) -> Dict[str, Any]:
        """Merge critical + background results into the existing pipeline output format."""
        all_results = {**critical_results, **background_results}
        total_elapsed = round(time.time() - self.start_time, 2) if self.start_time else 0

        return {
            "phases_completed": sum(1 for p in self.phases.values() if p.status == PhaseStatus.DONE),
            "phases_total": len(self.phases),
            "critical_elapsed": critical_results.get("critical_elapsed", 0),
            "background_elapsed": background_results.get("background_elapsed", 0),
            "total_elapsed": total_elapsed,
            "phase_timings": {name: node.duration for name, node in self.phases.items()},
            "phase_status": {name: node.status.value for name, node in self.phases.items()},
            "critical_path_done": all(
                self.phases[p].status == PhaseStatus.DONE for p in CRITICAL_PATH
            ),
        }
