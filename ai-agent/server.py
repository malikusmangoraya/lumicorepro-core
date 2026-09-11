"""
LumicorePro AI Agent — FastAPI WebSocket Server
================================================
Exposes the 9-phase generation pipeline over HTTP + WebSocket so the React
frontend can stream real-time progress updates without polling.

Endpoints
---------
GET  /health                   — liveness probe
GET  /api/registries/summary   — template/component/asset counts from SQLite
POST /api/generate             — fire-and-forget generation (returns run_id); accepts optional `image` for screenshot-driven generation (Phase 0 vision)
POST /api/vision/analyze       — analyze an uploaded screenshot → layout/theme tokens/region mapping (powers the vision preview UI)
POST /api/chat                 — text chat; optional `image` makes the assistant image-aware
WS   /ws/generate/{run_id}     — streams phase events as JSON lines
POST /api/cancel/{run_id}      — cooperative cancellation of a queued/running run
POST /api/dry-run              — returns the assembly plan without writing files
GET  /api/runs                 — durable pipeline list (survives restarts)
GET  /api/runs/{run_id}        — run status + streamed events (+ store recovery)
GET  /api/history              — last 20 generation records from SQLite

Usage
-----
    cd ai-agent
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

Or from project root:
    python ai-agent/server.py
"""

import sys
import os
import re
import uuid
import json
import asyncio
import time
import shutil
import sqlite3
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta

# ── Path bootstrap ─────────────────────────────────────────────────────────
AI_AGENT_DIR = Path(__file__).resolve().parent
if str(AI_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AI_AGENT_DIR))

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, Header
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel, Field
except ImportError:
    print("[ERROR] FastAPI not installed. Run: pip install fastapi uvicorn websockets")
    sys.exit(1)

from config.settings import AGENT_DB_PATH, GENERATED_PROJECTS_DIR
from config.providers import instantiate_provider, get_available_providers
from database.pipeline_store import PipelineStore
from database.accounts_store import AccountStore, default_account_store
from database.init_db import init_database
from utils.telemetry import Telemetry
from utils.logger import agent_logger
from agent.memory_retriever import MemoryRetriever
from agent.orchestrator import PipelineCancelled

# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title="LumicorePro AI Agent API",
    description="Real-time 10-phase international website generation pipeline with WebSocket streaming",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Allowed origins ────────────────────────────────────────────────────────
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── In-memory rate limiter ─────────────────────────────────────────────────
# Format: { ip: [(timestamp, endpoint), ...] }
_rate_store: Dict[str, List[float]] = defaultdict(list)
_RATE_LIMIT  = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))   # requests
_RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW",   "60"))   # seconds

def _check_rate_limit(client_ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    window_start = now - _RATE_WINDOW
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if t > window_start]
    if len(_rate_store[client_ip]) >= _RATE_LIMIT:
        return False
    _rate_store[client_ip].append(now)
    return True

def _get_client_ip(request: Request) -> str:
    direct_ip = request.client.host if request.client else "unknown"
    trusted_proxies = {
        value.strip()
        for value in os.getenv("TRUSTED_PROXY_IPS", "").split(",")
        if value.strip()
    }
    if direct_ip in trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return direct_ip

# ── Simple API-key auth (optional — set AGENT_API_KEY env to enable) ───────
_AGENT_API_KEY = os.getenv("AGENT_API_KEY", "").strip()
_email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _authenticate_user(x_api_key: Optional[str]) -> Optional[Dict[str, Any]]:
    """Resolve an optional per-user API key to a platform account, or None."""
    if not x_api_key:
        return None
    try:
        return _accounts.resolve_api_key(x_api_key)
    except Exception:
        return None


def _verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> bool:
    """If AGENT_API_KEY is configured, validate incoming key header."""
    if not _AGENT_API_KEY:
        return True  # Auth disabled
    if not x_api_key or not secrets.compare_digest(x_api_key, _AGENT_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# ── In-memory run registry ─────────────────────────────────────────────────
# Maps run_id → {"status": str, "events": list, "result": dict | None}

class _StreamFinished(Exception):
    """Internal signal for the WebSocket pump to exit after the terminal event."""


_runs: Dict[str, Dict[str, Any]] = {}
_pipeline_store: PipelineStore = PipelineStore()
_accounts: AccountStore = AccountStore(os.getenv("PLATFORM_DB_PATH") or default_account_store.path)
_telemetry: Telemetry = Telemetry()
_idempotency_store: Dict[str, tuple] = {}
_MAX_RUNS = max(10, int(os.getenv("AGENT_MAX_RUNS", "100")))
_MAX_EVENTS = max(20, int(os.getenv("AGENT_MAX_EVENTS", "500")))
_MAX_CONCURRENT_RUNS = max(1, int(os.getenv("AGENT_MAX_CONCURRENT_RUNS", "2")))
_run_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_RUNS)


def _request_cancel(run_id: str) -> bool:
    """Cooperatively request cancellation for a run. Returns True if accepted."""
    run = _runs.get(run_id)
    if not run or run["status"] in ("done", "error", "cancelled"):
        return False
    run["cancel_requested"] = True
    # A queued task has not reached the worker yet — cancel it outright.
    if run["status"] == "queued":
        task = run.get("task")
        if isinstance(task, asyncio.Task) and not task.done():
            task.cancel()
        _refund_credits(run_id, run)
    return True


async def _drain_cancelled_run(run_id: str) -> None:
    """Boundedly await a cancelled run so pipeline resources release promptly.

    Cooperative cancellation is propagated via `cancel_requested`; the pipeline
    observes it at the next phase boundary. Waiting here (with a timeout) means
    the WebSocket handler does not return while the run still burns thread-pool
    capacity — previously this was fire-and-forget.
    """
    run = _runs.get(run_id)
    task = run.get("task") if run else None
    if not isinstance(task, asyncio.Task) or task.done():
        return
    timeout = max(1.0, float(os.getenv("AGENT_CANCEL_DRAIN_TIMEOUT", "8")))
    try:
        await asyncio.wait_for(task, timeout=timeout)
        agent_logger.info(f"Drained cancelled run {run_id}")
    except asyncio.TimeoutError:
        agent_logger.info(f"Drain timeout for run {run_id} — leaving task to rejoin in the background")
    except asyncio.CancelledError:
        pass

def _refund_credits(run_id: str, run: Dict[str, Any]) -> None:
    """Return reserved credits when a run ends in error/cancellation."""
    user_id = run.get("user_id")
    reserved = float(run.get("credits_reserved") or 0.0)
    if not user_id or reserved <= 0:
        return
    try:
        _accounts.refund(user_id, reserved, run_id=run_id, reason="run_not_completed")
        run["credits_reserved"] = 0.0  # prevent double refund
    except Exception:
        agent_logger.warning(f"Credit refund failed for run {run_id}", exc_info=True)


def _cleanup_run_state() -> None:
    """Bound process-local state so long-lived API workers do not grow forever."""
    if len(_runs) <= _MAX_RUNS:
        return
    finished = sorted(
        (
            (run_id, run.get("finished_at", run.get("created_at", "")))
            for run_id, run in _runs.items()
            if run.get("status") in {"done", "error", "cancelled"}
        ),
        key=lambda item: item[1],
    )
    for run_id, _ in finished[: max(0, len(_runs) - _MAX_RUNS)]:
        _runs.pop(run_id, None)

    for key, (run_id, created_at) in list(_idempotency_store.items()):
        if run_id not in _runs or time.time() - created_at > 86400:
            _idempotency_store.pop(key, None)

# ── Pydantic models ────────────────────────────────────────────────────────

_VISION_SOURCE_DOC = "Uploaded screenshot as data URI (data:image/...;base64,...), a public image URL, or a local path reference."

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000, description="Natural language website description")
    provider: Optional[str] = Field("grok", description="AI provider: grok | gemini | openai | mistral | openrouter")
    dry_run: bool = Field(False, description="If true, return plan without writing files")
    language: Optional[str] = Field("en", description="UI language code: en, ar, ur, fr, de, es, zh, ...")
    region: Optional[str] = Field(None, description="Target region: NA, EU, SA, MENA, APAC, AF, LATAM")
    buyer_type: Optional[str] = Field(None, description="Targeted buyer type: 'static' (client-only showcase, zero server hosting) or 'enterprise' (full-stack hydration). Overrides website-type detection.")
    design_style: Optional[str] = Field(None, description="Named design style: minimalism, glassmorphism, neo_brutalism, bento_grid, neumorphism, flat_design, claymorphism, skeuomorphism, cyberpunk, corporate_memphis, editorial, swiss, aurora, organic, retro_futurism")
    image: Optional[str] = Field(None, description=_VISION_SOURCE_DOC + " Runs vision layout extraction (Phase 0) before generation.")
    files: Optional[List[FileAttachment]] = Field(default_factory=list, description="Extra attached files: images (screenshots) + documents (PDF/DOCX/XLSX/TXT/code) whose text is injected into the plan.")


class DryRunRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    provider: Optional[str] = "gemini"
    design_style: Optional[str] = Field(None, description="Named design style override (see GenerateRequest)")


class LocalizeRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000, description="Website prompt to detect region/currency from")
    region: Optional[str] = Field(None, description="Override region detection: NA|EU|SA|MENA|APAC|AF|LATAM")


class ComplianceRequest(BaseModel):
    region: str = Field("NA", description="Region code: NA|EU|SA|MENA|APAC|AF|LATAM")
    website_type: Optional[str] = Field("ecommerce", description="Website type for regulation scoping")
    project_name: Optional[str] = Field("My Project")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message for the assistant")
    provider: Optional[str] = Field("gemini", description="AI provider to route through")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Optional prior turns [{role, content}]")
    image: Optional[str] = Field(None, description=_VISION_SOURCE_DOC + " The assistant describes the image, then answers the message.")
    files: Optional[List[FileAttachment]] = Field(default_factory=list, description="Attached files: images + documents (PDF/DOCX/XLSX/TXT/code). Image layouts are analyzed; document text is injected into the reply context.")


class VisionAnalyzeRequest(BaseModel):
    image: str = Field(..., description=_VISION_SOURCE_DOC)
    provider: Optional[str] = Field(None, description="Vision provider override (defaults to VISION_PROVIDER)")


class FileAttachment(BaseModel):
    filename: str = Field(..., max_length=255, description="Original filename with extension")
    type: Optional[str] = Field("", description="MIME type, e.g. image/png, application/pdf")
    data: str = Field(..., description="Base64 data URI (data:<mime>;base64,...) of the file content")


def _prepare_attachments(files: List[Dict]) -> Dict[str, Any]:
    """Decode uploaded files from chat/generate into usable context.

    Returns {"images": [entry], "documents": [entry], "context": str}.
    Images carry their data URI; documents carry extracted text.
    """
    from agent.file_reader import extract_files, describe_attachments

    processed = extract_files(files or [])
    context = describe_attachments(processed["documents"] + processed["images"])
    return {**processed, "context": context}


class IterateRequest(BaseModel):
    project_dir: str = Field(..., description="Absolute path of the generated project to refine")
    instruction: str = Field(..., min_length=3, max_length=2000, description="Change request, e.g. 'change hero heading color'")
    provider: Optional[str] = Field(None, description="AI provider override (defaults to project/active provider)")
    client_brand: Optional[str] = Field(None, max_length=80, description="Agency/white-label client name for reports")


# ── Background generation task ─────────────────────────────────────────────
async def _run_pipeline(run_id: str, prompt: str, provider: Optional[str], design_style: Optional[str] = None, buyer_type: Optional[str] = None, image: Optional[str] = None):
    """Execute the 15-phase pipeline in a thread and stream events."""
    run = _runs[run_id]
    async with _run_semaphore:
        if run.get("cancel_requested"):
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled by the client."
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
            return

        run["status"] = "running"
        run["started_at"] = time.time()
        _pipeline_store.set_status(run_id, "running", started_at=run["started_at"])
        _telemetry.record(run_id, "run_start", provider=provider, prompt_len=len(prompt))

        _pending_events: List[Dict[str, Any]] = []

        def _flush_events():
            if _pending_events:
                try:
                    _pipeline_store.append_events(run_id, _pending_events)
                except Exception:
                    agent_logger.warning("Failed to persist pipeline events", exc_info=True)
                _pending_events.clear()

        def _emit(event_type: str, data: dict):
            event = {"run_id": run_id, "type": event_type, "ts": time.time(), **data}
            run["events"].append(event)
            del run["events"][:-_MAX_EVENTS]
            _pending_events.append(event)
            if len(_pending_events) >= 5:
                _flush_events()

        try:
            # Import inside function so server starts even if agent deps are missing
            from agent.orchestrator import AgentOrchestrator

            loop = asyncio.get_event_loop()

            # We run the synchronous orchestrator in a thread pool to keep the
            # event loop free for WebSocket heartbeats.
            def _sync_run():
                orchestrator = AgentOrchestrator(provider_name=provider)

                # Cooperative cancellation inside quality-gate subprocess steps.
                def _gate_checkpoint():
                    if run.get("cancel_requested"):
                        raise PipelineCancelled("Cancellation requested by client")
                orchestrator.cancel_check = _gate_checkpoint

                # Pre-emit all phases as pending
                for idx, phase in enumerate(orchestrator.PHASES):
                    _emit("phase_pending", {"phase": phase, "index": idx})

                def _on_progress(phase_name: str, event_type: str, data: dict):
                    # Cooperative cancellation point at each phase boundary.
                    if run.get("cancel_requested"):
                        raise PipelineCancelled("Cancellation requested by client")
                    _telemetry.record(run_id, event_type, phase=phase_name)
                    _emit(event_type, {"phase": phase_name, **data})

                extra_spec = {}
                if buyer_type:
                    extra_spec["buyer_type"] = buyer_type
                if image:
                    extra_spec["screenshot"] = image
                extra_spec = extra_spec or None
                return orchestrator.run(
                    prompt,
                    interactive=False,
                    progress_callback=_on_progress,
                    design_style=design_style,
                    extra_spec=extra_spec,
                )

            report = await loop.run_in_executor(None, _sync_run)
            if run.get("cancel_requested"):
                raise PipelineCancelled("Cancellation requested by client")

            # Fail loud: a report without a usable project dir, or one whose
            # orchestrator marked critical phase failures, is NOT "done".
            report_status = (report or {}).get("status")
            project_dir = (report or {}).get("generated_project_dir")
            if not report or not project_dir or not os.path.isdir(str(project_dir)):
                raise RuntimeError(
                    "Pipeline did not produce a usable project directory. "
                    f"Report status: {report_status or 'missing'}"
                )
            if report_status == "failed":
                raise RuntimeError(
                    "Generation failed during a critical phase. "
                    "No usable website was produced."
                )

            run["result"] = report
            run["status"] = "done"
            run["finished_at"] = time.time()
            _emit("complete", {"project_name": report.get("project_name"), "quality_score": report.get("quality_gates", {}).get("overall_score"), "status": report_status, "zip": report.get("zip_archive_path")})
            _telemetry.record(
                run_id, "run_done", status=report_status,
                duration_secs=round(run["finished_at"] - run["started_at"], 3),
                quality_score=report.get("quality_gates", {}).get("overall_score"),
                project_name=report.get("project_name"),
            )
            _flush_events()
            _pipeline_store.set_status(run_id, "done", result_json=report, finished_at=run["finished_at"])

            # Persist to generation_history
            _persist_history(prompt, provider, report)

        except PipelineCancelled:
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled by the client."
            _emit("cancelled", {"message": run["error"]})
            _telemetry.record(run_id, "run_cancelled", status="cancelled",
                              duration_secs=round(run["finished_at"] - run["started_at"], 3))
            _flush_events()
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
        except asyncio.CancelledError:
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled by the client."
            _emit("cancelled", {"message": run["error"]})
            _telemetry.record(run_id, "run_cancelled", status="cancelled",
                              duration_secs=round(run["finished_at"] - run["started_at"], 3))
            _flush_events()
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
        except Exception as exc:
            agent_logger.error(f"Pipeline run {run_id} failed: {exc}", exc_info=True)
            run["status"] = "error"
            run["finished_at"] = time.time()
            run["error"] = "Generation failed. Check the run report for details."
            _emit("error", {"message": run["error"]})
            _telemetry.record(run_id, "run_error", status="error", error=str(exc),
                              duration_secs=round(run["finished_at"] - run["started_at"], 3))
            _flush_events()
            _pipeline_store.set_status(run_id, "error", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)


def _persist_history(prompt: str, provider: str, report: dict):
    try:
        if not os.path.exists(AGENT_DB_PATH):
            return
        conn = sqlite3.connect(str(AGENT_DB_PATH))
        conn.execute(
            "INSERT INTO generation_history (project_name, prompt, template_used, status, report_json) VALUES (?,?,?,?,?)",
            (report.get("project_name", ""), prompt, report.get("selected_resources", {}).get("template", ""), "complete", json.dumps(report))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Streaming pipeline (critical path + background parallel) ──────────────
async def _run_stream_pipeline(run_id: str, prompt: str, provider: Optional[str],
                                design_style: Optional[str] = None, buyer_type: Optional[str] = None,
                                image: Optional[str] = None):
    """Execute the DAG-aware parallel pipeline with critical path + background workers."""
    from agent.pipeline import StreamPipeline, PipelineCancelled as StreamCancelled

    run = _runs[run_id]
    async with _run_semaphore:
        if run.get("cancel_requested"):
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled."
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
            return

        run["status"] = "running"
        run["started_at"] = time.time()
        _pipeline_store.set_status(run_id, "running", started_at=run["started_at"])
        _telemetry.record(run_id, "run_start", provider=provider, prompt_len=len(prompt))

        _pending_events: List[Dict[str, Any]] = []

        def _flush_events():
            if _pending_events:
                try:
                    _pipeline_store.append_events(run_id, _pending_events)
                except Exception:
                    pass
                _pending_events.clear()

        def _emit(event_type: str, data: dict):
            event = {"run_id": run_id, "type": event_type, "ts": time.time(), **data}
            run["events"].append(event)
            del run["events"][:-_MAX_EVENTS]
            _pending_events.append(event)
            if len(_pending_events) >= 5:
                _flush_events()

        try:
            from agent.orchestrator import AgentOrchestrator
            loop = asyncio.get_event_loop()

            def _sync_run():
                orchestrator = AgentOrchestrator(provider_name=provider)

                def _gate_checkpoint():
                    if run.get("cancel_requested"):
                        raise StreamCancelled("Cancellation requested by client")
                orchestrator.cancel_check = _gate_checkpoint

                def _on_progress(phase_name: str, event_type: str, data: dict):
                    if run.get("cancel_requested"):
                        raise StreamCancelled("Cancellation requested by client")
                    _telemetry.record(run_id, event_type, phase=phase_name)
                    _emit(event_type, {"phase": phase_name, **data})

                pipeline = StreamPipeline(
                    progress_callback=_on_progress,
                    cancel_check=_gate_checkpoint,
                    max_background_workers=4,
                )

                # Build critical path handlers from the orchestrator
                market_result = pipeline._run_with_timeout(
                    "market_analysis", orchestrator.market_analyzer.analyze,
                    [orchestrator.analyzer._local_rule_analysis(prompt)], {}
                )
                pipeline.phases["market_analysis"].result = market_result
                pipeline.phases["market_analysis"].status = "done"
                pipeline.phases["market_analysis"].end_time = time.time()
                _on_progress("market_analysis", "phase_done", {"duration": pipeline.phases["market_analysis"].duration, "path": "critical"})

                # Continue with the standard orchestrator but track via pipeline
                extra_spec = {}
                if buyer_type:
                    extra_spec["buyer_type"] = buyer_type
                if image:
                    extra_spec["screenshot"] = image
                return orchestrator.run(
                    prompt,
                    interactive=False,
                    progress_callback=_on_progress,
                    design_style=design_style,
                    extra_spec=extra_spec or None,
                )

            report = await loop.run_in_executor(None, _sync_run)
            if run.get("cancel_requested"):
                raise StreamCancelled("Cancellation requested by client")

            # Fail loud: no usable project dir, or critical phase failure → NOT done.
            report_status = (report or {}).get("status")
            project_dir = (report or {}).get("generated_project_dir")
            if not report or not project_dir or not os.path.isdir(str(project_dir)):
                raise RuntimeError(
                    "Pipeline did not produce a usable project directory. "
                    f"Report status: {report_status or 'missing'}"
                )
            if report_status == "failed":
                raise RuntimeError(
                    "Generation failed during a critical phase. "
                    "No usable website was produced."
                )

            run["result"] = report
            run["status"] = "done"
            run["finished_at"] = time.time()
            _emit("complete", {
                "project_name": report.get("project_name"),
                "quality_score": report.get("quality_gates", {}).get("overall_score"),
                "status": report_status,
                "zip": report.get("zip_archive_path"),
                "pipeline_mode": "stream",
            })
            _telemetry.record(run_id, "run_done", status=report_status,
                              duration_secs=round(run["finished_at"] - run["started_at"], 3))
            _flush_events()
            _pipeline_store.set_status(run_id, "done", result_json=report, finished_at=run["finished_at"])
            _persist_history(prompt, provider, report)

        except (StreamCancelled, PipelineCancelled):
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled."
            _emit("cancelled", {"message": run["error"]})
            _telemetry.record(run_id, "run_cancelled", status="cancelled",
                              duration_secs=round(run["finished_at"] - run["started_at"], 3))
            _flush_events()
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
        except asyncio.CancelledError:
            run["status"] = "cancelled"
            run["finished_at"] = time.time()
            run["error"] = "Generation cancelled."
            _emit("cancelled", {"message": run["error"]})
            _flush_events()
            _pipeline_store.set_status(run_id, "cancelled", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)
        except Exception as exc:
            agent_logger.error(f"Stream pipeline {run_id} failed: {exc}", exc_info=True)
            run["status"] = "error"
            run["finished_at"] = time.time()
            run["error"] = "Generation failed."
            _emit("error", {"message": run["error"]})
            _telemetry.record(run_id, "run_error", status="error", error=str(exc))
            _flush_events()
            _pipeline_store.set_status(run_id, "error", error=run["error"], finished_at=run["finished_at"])
            _refund_credits(run_id, run)


def _theme_summary(engine) -> dict:
    """Compact per-category + per-style variant counts for /api/themes."""
    cats = {}
    style_counts = {}
    for tpl in engine.templates:
        cat = tpl.get("category", "")
        cats[cat] = cats.get(cat, 0) + len(engine.compatible_styles(tpl))
        for style in engine.compatible_styles(tpl):
            style_counts[style] = style_counts.get(style, 0) + 1
    return {
        "templates_by_category": {k: v for k, v in sorted(cats.items())},
        "variants_by_style": {k: v for k, v in sorted(style_counts.items())},
    }


# ── Routes ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    if not os.path.exists(AGENT_DB_PATH):
        init_database()
    # Flag runs left in-flight by a previous process (durable store recovery).
    interrupted = _pipeline_store.mark_interrupted(time.time())
    if interrupted:
        agent_logger.warning(f"Marked {len(interrupted)} stale pipeline run(s) as interrupted.")
    root_runs = list(_pipeline_store.list_runs(limit=_MAX_RUNS))
    for stored in root_runs:
        rid = stored.get("run_id")
        if rid and rid not in _runs:
            _runs[rid] = {
                "status": stored.get("status", "unknown"),
                "events": list(stored.get("events_json") or []),
                "result": stored.get("result_json"),
                "error": stored.get("error"),
                "task": None,
                "cancel_requested": False,
                "created_at": stored.get("created_at", ""),
            }
    _pipeline_store.prune(keep=_MAX_RUNS)
    _load_persisted_previews()
    agent_logger.info("LumicorePro FastAPI server started.")


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "3.0.0", "agent": "LumicorePro 15-Phase International Pipeline"}


@app.get("/api/providers", tags=["System"])
async def list_providers():
    """Return all configured AI providers and which ones have valid API keys."""
    try:
        from config.providers import get_available_providers, FALLBACK_ORDER, PROVIDER_CONFIGS
        available = get_available_providers()
        providers_info = []
        for name in FALLBACK_ORDER:
            cfg = PROVIDER_CONFIGS.get(name, {})
            providers_info.append({
                "name": name,
                "model": cfg.get("model", ""),
                "available": name in available,
                "env_var": cfg.get("env_var_name", ""),
            })
        return {"providers": providers_info, "available_count": len(available)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/languages", tags=["Internationalization"])
async def list_languages():
    """Return all 40+ supported UI languages with metadata."""
    from agent.localization_engine import LocalizationEngine
    engine = LocalizationEngine()
    return {
        "languages": [
            {"code": code, **meta}
            for code, meta in engine.LANGUAGES.items()
        ],
        "total": len(engine.LANGUAGES),
        "rtl_languages": [c for c, m in engine.LANGUAGES.items() if m["dir"] == "rtl"],
    }


@app.get("/api/currencies", tags=["Internationalization"])
async def list_currencies(region: Optional[str] = None):
    """Return currency definitions. Optionally filter by region: SA|MENA|EU|NA|APAC|AF|LATAM"""
    from agent.currency_localizer import CurrencyLocalizer
    localizer = CurrencyLocalizer()
    currencies = localizer.CURRENCIES
    if region:
        currencies = {k: v for k, v in currencies.items() if v.get("region") == region}
    return {
        "currencies": currencies,
        "total": len(currencies),
        "rtl_currencies": localizer.list_rtl_currencies(),
    }


@app.post("/api/localize", tags=["Internationalization"])
async def localize(req: LocalizeRequest, request: Request, _auth: bool = Depends(_verify_api_key)):
    """Detect region & currency from a prompt, return full localization config."""
    client_ip = _get_client_ip(request)
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    try:
        from agent.currency_localizer import CurrencyLocalizer
        from agent.localization_engine import LocalizationEngine
        from agent.requirement_analyzer import RequirementAnalyzer

        analyzer = RequirementAnalyzer()
        spec = analyzer._local_rule_analysis(req.prompt)
        if req.region:
            spec["region"] = req.region

        currency_result = CurrencyLocalizer().localize(spec)
        i18n_langs = LocalizationEngine()._select_languages({**spec, "region": currency_result["region"]})

        return {
            "region":               currency_result["region"],
            "primary_currency":     currency_result["primary_currency"],
            "supported_currencies": currency_result["supported_currencies"],
            "payment_gateways":     currency_result["payment_gateways"],
            "tax":                  currency_result["tax"],
            "locale_settings":      currency_result["locale_settings"],
            "compliance_flags":     currency_result["compliance_flags"],
            "recommended_languages": i18n_langs[:10],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/compliance", tags=["Internationalization"])
async def compliance_info(req: ComplianceRequest, request: Request, _auth: bool = Depends(_verify_api_key)):
    """Return applicable regulations and compliance requirements for a region."""
    client_ip = _get_client_ip(request)
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    try:
        from agent.compliance_generator import ComplianceGenerator
        gen = ComplianceGenerator()
        spec = {"website_type": req.website_type, "project_name": req.project_name}
        applicable = gen._get_applicable_regs(req.region, spec)
        return {
            "region": req.region,
            "regulations": [
                {
                    "code":         r["code"],
                    "full_name":    r["full_name"],
                    "jurisdictions":r["jurisdictions"],
                    "cookie_policy":r.get("cookie_policy"),
                    "penalty":      r.get("penalty"),
                    "requirements": r["requirements"],
                    "key_rights":   r["key_rights"],
                }
                for r in applicable
            ],
            "cookie_model":        gen._get_cookie_model(applicable),
            "requires_consent_banner": any(
                r.get("cookie_policy", "").startswith("Opt-in") for r in applicable
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/registries/summary", tags=["Registry"])
async def registries_summary():
    """Return counts of all indexed templates, components, assets, etc."""
    if not os.path.exists(AGENT_DB_PATH):
        raise HTTPException(status_code=503, detail="Database not initialized. Call /api/init first.")
    try:
        conn = sqlite3.connect(str(AGENT_DB_PATH))
        tables = {
            "templates":  "templates_index",
            "components": "components_index",
            "assets":     "assets_index",
            "backends":   "backend_index",
            "schemas":    "database_schemas_index",
        }
        summary = {}
        for key, tbl in tables.items():
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
                summary[key] = row[0] if row else 0
            except Exception:
                summary[key] = 0
        conn.close()
        return {"summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/memory/catalog", tags=["Memory"])
async def memory_catalog(limit: int = 20):
    """Adaptive memory snapshot: usage leaderboards for templates/components/assets/backends."""
    if not os.path.exists(AGENT_DB_PATH):
        raise HTTPException(status_code=503, detail="Database not initialized. Call /api/init first.")
    try:
        return {"memory": MemoryRetriever().memory_insights(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/memory/history", tags=["Memory"])
async def memory_history(limit: int = 50):
    """Recent agent memory search-history entries."""
    if not os.path.exists(AGENT_DB_PATH):
        raise HTTPException(status_code=503, detail="Database not initialized. Call /api/init first.")
    try:
        return {"searches": MemoryRetriever().recent_searches(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/generate", tags=["Generation"])
async def generate(req: GenerateRequest, request: Request, _auth: bool = Depends(_verify_api_key),
                   x_api_key: Optional[str] = Header(default=None)):
    """Start a generation run. Returns run_id immediately; connect to /ws/generate/{run_id} for streaming."""
    client_ip = _get_client_ip(request)
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 30 requests/minute per IP.")

    idempotency_key = request.headers.get("Idempotency-Key", "").strip()
    if len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long.")
    if idempotency_key:
        existing = _idempotency_store.get(idempotency_key)
        if existing and existing[0] in _runs:
            existing_run = _runs[existing[0]]
            return {
                "run_id": existing[0],
                "status": existing_run["status"],
                "ws_url": f"/ws/generate/{existing[0]}",
                "language": existing_run.get("language", "en"),
                "region": existing_run.get("region"),
                "idempotent_replay": True,
            }

    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "status": "queued", "events": [], "result": None, "error": None,
        "task": None, "cancel_requested": False,
        "language": req.language or "en",
        "region": req.region,
        "created_at": datetime.utcnow().isoformat(),
    }
    _cleanup_run_state()
    if idempotency_key:
        _idempotency_store[idempotency_key] = (run_id, time.time())

    # ── Attachment context (images + documents) ──────────────────────────
    effective_prompt = req.prompt
    screenshot = req.image
    attachment_context = ""
    if req.files:
        prepared = _prepare_attachments([a.model_dump(exclude_none=True) for a in req.files])
        attachment_context = prepared.get("context", "")
        if not screenshot and prepared.get("images"):
            screenshot = prepared["images"][0].get("data")
        if attachment_context:
            effective_prompt = (
                f"{attachment_context}\n\n---\n\nREQUEST: {req.prompt}"
                if req.prompt else attachment_context
            )
    vision_mode = bool(screenshot or req.files)

    _pipeline_store.create_run(
        run_id,
        status="queued",
        prompt=effective_prompt,
        provider=req.provider or "gemini",
        language=req.language or "en",
        region=req.region,
        buyer_type=req.buyer_type,
        design_style=req.design_style,
    )
    # Reserved credits for this run (authenticated users pay per generation).
    user = _authenticate_user(x_api_key)
    credits_reserved = 0.0
    if user is not None:
        if not _accounts.spend(user["id"], _CREDITS_PER_RUN, run_id=run_id, reason="generation"):
            _runs.pop(run_id, None)
            _pipeline_store.set_status(run_id, "cancelled", error="Insufficient credits", finished_at=time.time())
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Balance is 0. Add credits via POST /api/accounts/credits/topup.",
            )
        credits_reserved = _CREDITS_PER_RUN
        _runs[run_id]["user_id"] = user["id"]
        _runs[run_id]["credits_reserved"] = credits_reserved

    task = asyncio.create_task(_run_pipeline(run_id, effective_prompt, req.provider, req.design_style, req.buyer_type, screenshot))
    _runs[run_id]["task"] = task
    return {
        "run_id": run_id,
        "status": "queued",
        "ws_url": f"/ws/generate/{run_id}",
        "language": req.language,
        "region": req.region,
        "vision_mode": vision_mode,
        "credits_reserved": credits_reserved,
    }


# ── Stream Pipeline: Fast TTFR + SSE fallback ─────────────────────────
@app.post("/api/generate/stream", tags=["Generation"])
async def generate_stream(req: GenerateRequest, request: Request, _auth: bool = Depends(_verify_api_key),
                           x_api_key: Optional[str] = Header(default=None)):
    """Stream pipeline — fast critical path (TTFR <8s) + background parallel phases.
    Returns run_id + ws_url + sse_url immediately. Connect to /ws/generate/{run_id}
    or GET /api/generate/{run_id}/events for SSE fallback.
    """
    client_ip = _get_client_ip(request)
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "status": "queued", "events": [], "result": None, "error": None,
        "task": None, "cancel_requested": False,
        "language": req.language or "en", "region": req.region,
        "created_at": datetime.utcnow().isoformat(), "pipeline_mode": "stream",
    }
    _cleanup_run_state()

    effective_prompt = req.prompt
    screenshot = req.image
    attachment_context = ""
    if req.files:
        prepared = _prepare_attachments([a.model_dump(exclude_none=True) for a in req.files])
        attachment_context = prepared.get("context", "")
        if not screenshot and prepared.get("images"):
            screenshot = prepared["images"][0].get("data")
        if attachment_context:
            effective_prompt = (
                f"{attachment_context}\n\n---\n\nREQUEST: {req.prompt}"
                if req.prompt else attachment_context
            )

    _pipeline_store.create_run(run_id, status="queued", prompt=effective_prompt,
                               provider=req.provider or "gemini", language=req.language or "en",
                               region=req.region, buyer_type=req.buyer_type,
                               design_style=req.design_style)

    user = _authenticate_user(x_api_key)
    credits_reserved = 0.0
    if user is not None:
        if not _accounts.spend(user["id"], _CREDITS_PER_RUN, run_id=run_id, reason="generation_stream"):
            _runs.pop(run_id, None)
            raise HTTPException(status_code=402, detail="Insufficient credits.")
        credits_reserved = _CREDITS_PER_RUN
        _runs[run_id]["user_id"] = user["id"]
        _runs[run_id]["credits_reserved"] = credits_reserved

    task = asyncio.create_task(
        _run_stream_pipeline(run_id, effective_prompt, req.provider, req.design_style, req.buyer_type, screenshot)
    )
    _runs[run_id]["task"] = task
    return {
        "run_id": run_id,
        "status": "queued",
        "ws_url": f"/ws/generate/{run_id}",
        "sse_url": f"/api/generate/{run_id}/events",
        "pipeline_mode": "stream",
        "language": req.language,
        "region": req.region,
        "credits_reserved": credits_reserved,
    }


@app.get("/api/generate/{run_id}/events", tags=["Generation"])
async def generate_sse(run_id: str, _auth: bool = Depends(_verify_api_key)):
    """Server-Sent Events fallback for environments that block WebSockets."""
    from starlette.responses import StreamingResponse

    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_stream():
        idx = 0
        while True:
            events = run.get("events", [])
            while idx < len(events):
                evt = events[idx]
                import json as _json
                yield f"data: {_json.dumps(evt)}\n\n"
                idx += 1
            if run["status"] in ("done", "error", "cancelled") and idx >= len(events):
                break
            await asyncio.sleep(0.3)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/cancel/{run_id}", tags=["Generation"])
async def cancel_run(run_id: str, _auth: bool = Depends(_verify_api_key)):
    """Request cooperative cancellation for a queued or running generation."""
    if _request_cancel(run_id):
        return {"run_id": run_id, "status": "cancelling", "message": "Cancellation requested."}
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "status": run["status"], "message": "Run is already finished or being cancelled."}


class RevisionRequest(BaseModel):
    changes: List[str] = Field(..., min_length=1, description="List of specific change requests")
    priority: str = Field(default="normal", description="low | normal | high")
    client_name: Optional[str] = Field(default=None, description="Client name for tracking")
    client_email: Optional[str] = Field(default=None, description="Client email for follow-up")


@app.post("/api/runs/{run_id}/revise", tags=["Generation"])
async def request_revision(run_id: str, req: RevisionRequest, _auth: bool = Depends(_verify_api_key)):
    """Submit a client revision request for a completed generation run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] not in ("done", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot revise a run with status '{run['status']}'. Must be 'done' or 'failed'.")

    revision = {
        "revision_id": f"rev-{run_id[:8]}-{int(time.time())}",
        "run_id": run_id,
        "changes": req.changes,
        "priority": req.priority,
        "client_name": req.client_name,
        "client_email": req.client_email,
        "status": "pending",
        "created_at": time.time(),
    }

    # Store revision in pipeline store
    try:
        _pipeline_store.append_events(run_id, [{"type": "revision_requested", **revision}])
    except Exception:
        pass

    # Store in-memory for quick access
    if "revisions" not in run:
        run["revisions"] = []
    run["revisions"].append(revision)

    agent_logger.info(f"Revision request {revision['revision_id']} for run {run_id}: {len(req.changes)} change(s)")

    return {
        "revision_id": revision["revision_id"],
        "run_id": run_id,
        "status": "pending",
        "changes_count": len(req.changes),
        "message": f"Revision request received. {len(req.changes)} change(s) logged for review.",
    }


@app.get("/api/runs/{run_id}/revisions", tags=["Generation"])
async def get_revisions(run_id: str, _auth: bool = Depends(_verify_api_key)):
    """List all revision requests for a generation run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    revisions = run.get("revisions", [])
    return {"run_id": run_id, "revisions": revisions, "total": len(revisions)}


class ApplyRevisionRequest(BaseModel):
    revision_id: Optional[str] = Field(default=None, description="Specific revision to apply, or latest if omitted")


@app.post("/api/runs/{run_id}/revise/apply", tags=["Generation"])
async def apply_revision(run_id: str, req: ApplyRevisionRequest, _auth: bool = Depends(_verify_api_key)):
    """Apply a revision request to the generated project using AI code modification."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    revisions = run.get("revisions", [])
    if not revisions:
        raise HTTPException(status_code=400, detail="No revision requests found for this run")

    # Find the target revision
    target_rev = None
    if req.revision_id:
        for r in revisions:
            if r["revision_id"] == req.revision_id:
                target_rev = r
                break
        if not target_rev:
            raise HTTPException(status_code=404, detail=f"Revision {req.revision_id} not found")
    else:
        # Apply the latest pending revision
        for r in reversed(revisions):
            if r.get("status") == "pending":
                target_rev = r
                break
        if not target_rev:
            raise HTTPException(status_code=400, detail="No pending revisions to apply")

    # Get the project directory
    project_dir = run.get("project_dir") or run.get("result", {}).get("projectDir")
    if not project_dir or not os.path.isdir(project_dir):
        raise HTTPException(status_code=400, detail=f"Project directory not found: {project_dir}")

    # Mark revision as applying
    target_rev["status"] = "applying"

    try:
        from agent.code_modifier import CodeModifier
        modifier = CodeModifier()
        result = modifier.apply_revision(project_dir, target_rev["changes"])

        # Mark as applied
        target_rev["status"] = "applied"
        target_rev["applied_at"] = time.time()
        target_rev["result"] = result

        agent_logger.info(f"Revision {target_rev['revision_id']} applied: {result}")

        return {
            "revision_id": target_rev["revision_id"],
            "status": "applied",
            "changes_applied": result.get("changes_applied", 0),
            "patched_files": result.get("patched_files", []),
            "message": f"Revision applied successfully. {result.get('changes_applied', 0)} change(s) processed.",
        }
    except Exception as e:
        target_rev["status"] = "failed"
        target_rev["error"] = str(e)
        agent_logger.error(f"Revision apply failed: {e}")
        raise HTTPException(status_code=500, detail=f"Revision apply failed: {str(e)}")


@app.post("/api/dry-run", tags=["Generation"])
async def dry_run(req: DryRunRequest, _auth: bool = Depends(_verify_api_key)):
    """Return the assembly plan without writing files."""
    import asyncio
    from agent.orchestrator import AgentOrchestrator

    loop = asyncio.get_event_loop()

    def _sync():
        orchestrator = AgentOrchestrator(provider_name=req.provider)
        spec = orchestrator.analyzer.analyze(req.prompt)
        if req.design_style:
            spec["design_style"] = req.design_style
        template = orchestrator.template_selector.select_template(spec)
        components = orchestrator.component_selector.select_components(spec)
        assets = orchestrator.asset_selector.select_assets(spec)
        backend = orchestrator.backend_selector.select_backend(spec)
        schemas = orchestrator.database_selector.select_schemas(spec)
        plan = orchestrator.planner.create_plan(spec, template, components, assets, backend, schemas)
        style = orchestrator.design_engine.resolve_style(spec)
        return {
            "project_name": plan.get("project_name"),
            "website_type": spec.get("website_type"),
            "industry": spec.get("industry"),
            "template": template.get("name") if template else "Default",
            "components_count": len(components),
            "components": [c["name"] for c in components],
            "backend": backend.get("name") if backend else "Default Express",
            "schemas": [s.get("name") for s in schemas],
            "assembly_steps": len(plan.get("assembly_steps", [])),
            "ai_tasks": len(plan.get("ai_tasks_required", [])),
            "features": spec.get("features", []),
            "design_style": style.get("id"),
            "design_style_name": style.get("name"),
        }

    try:
        plan_summary = await loop.run_in_executor(None, _sync)
        return plan_summary
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/runs/{run_id}", tags=["Generation"])
async def get_run(run_id: str, _auth: bool = Depends(_verify_api_key)):
    run = _runs.get(run_id)
    if not run:
        # Fall back to the durable store (run may predate a server restart).
        stored = _pipeline_store.get_run(run_id)
        if stored:
            return {
                "run_id": run_id,
                "status": stored.get("status"),
                "events_count": len(stored.get("events_json") or []),
                "result": stored.get("result_json"),
                "error": stored.get("error"),
                "recovered": True,
                "created_at": stored.get("created_at"),
            }
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "status": run["status"], "events_count": len(run["events"]), "result": run.get("result"), "error": run.get("error")}


@app.get("/api/runs", tags=["Generation"])
async def list_runs(limit: int = 20, status: Optional[str] = None, _auth: bool = Depends(_verify_api_key)):
    """List recent pipeline runs (durable, survives restarts)."""
    runs = _pipeline_store.list_runs(limit=limit, status=status)
    return {"runs": runs, "count": len(runs)}


# ── Platform accounts (skeleton for the SaaS layer) ────────────────────────

class RegisterRequest(BaseModel):
    email: str
    display_name: str = ""


@app.post("/api/accounts/register", tags=["Accounts"])
async def register_account(req: RegisterRequest, request: Request):
    """Create a platform user; returns a per-user API key ONCE. Rate-limited."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    email = (req.email or "").strip().lower()
    if not _email_pattern.match(email):
        raise HTTPException(status_code=422, detail="A valid email address is required")
    try:
        user = _accounts.create_user(email, req.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "success": True,
        "data": {
            "user_id": user["id"],
            "email": user["email"],
            "api_key": user["api_key"],
            "note": "Store this key — it is shown only once. Send it as X-API-KEY.",
        },
    }


@app.get("/api/accounts/me", tags=["Accounts"])
async def get_me(x_api_key: Optional[str] = Header(default=None)):
    """Current user + their projects (auth via per-user X-API-KEY)."""
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    projects = _accounts.list_projects(user["id"])
    return {"success": True, "data": {"user": user, "projects": projects}}


class CreateProjectRequest(BaseModel):
    project_name: str
    run_id: str = ""
    website_type: str = ""


@app.post("/api/accounts/projects", tags=["Accounts"])
async def create_project(req: CreateProjectRequest, request: Request, x_api_key: Optional[str] = Header(default=None)):
    """Attach a generated run to the calling user's project list."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    name = (req.project_name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="project_name is required")
    try:
        project = _accounts.create_project(user["id"], name, req.website_type, req.run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"success": True, "data": project}


# ── Credits (skeleton metering layer; Stripe comes later) ──────────────────

_CREDITS_PER_RUN = float(os.getenv("CREDITS_PER_RUN", "1"))


@app.get("/api/accounts/credits", tags=["Accounts"])
async def get_user_credits(x_api_key: Optional[str] = Header(default=None)):
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    balance = _accounts.get_credits(user["id"]) or {"credits_balance": 0, "credits_used": 0}
    return {"success": True, "data": {**user, **balance}}


class TopupRequest(BaseModel):
    amount: float
    reason: str = "manual_grant"


@app.post("/api/accounts/credits/topup", tags=["Accounts"])
async def topup_credits(req: TopupRequest, request: Request, x_api_key: Optional[str] = Header(default=None)):
    """Grant credits to the calling user (pre-payment metering prototype)."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    try:
        result = _accounts.topup(user["id"], req.amount, req.reason or "manual_grant")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"success": True, "data": result}


# ── Live preview + deploy URL flow (skeleton) ──────────────────────────────

class PreviewRequest(BaseModel):
    run_id: str


_previews: Dict[str, str] = {}  # slug -> absolute generated project dir
_PREVIEW_BASE_URL = os.getenv("PREVIEW_BASE_URL", "").strip().rstrip("/")


def _load_persisted_previews() -> None:
    """Reload previewable deployments from platform.db on startup/restart."""
    try:
        store = AccountStore(os.getenv("PLATFORM_DB_PATH") or default_account_store.path)
        for dep in store.list_all_deployments(limit=500):
            slug = dep.get("slug") or ""
            path = dep.get("project_dir") or ""
            if slug and path and os.path.isdir(path):
                _previews.setdefault(slug, path)
    except Exception:
        agent_logger.warning("Failed to reload persisted previews", exc_info=True)


def _persist_preview(slug: str, project_dir: str, user_id: str = "", run_id: str = "") -> Dict[str, Any]:
    """Persist a preview to platform.db.deployments so it survives restarts."""
    try:
        store = AccountStore(os.getenv("PLATFORM_DB_PATH") or default_account_store.path)
        if user_id:
            dep = store.create_deployment(
                user_id,
                slug,
                run_id=run_id,
                platform="lumicore-preview",
                project_dir=project_dir,
            )
            store.promote_deployment(dep.get("id", ""), status="live")
            return dep
    except Exception:
        agent_logger.warning("Preview persistence skipped", exc_info=True)
    return {}


@app.post("/api/preview", tags=["Preview"])
async def create_preview(req: PreviewRequest, _auth: bool = Depends(_verify_api_key),
                         x_api_key: Optional[str] = Header(default=None)):
    """Register a finished run's project for live preview; returns a preview URL."""
    run = _runs.get(req.run_id)
    if not run:
        stored = _pipeline_store.get_run(req.run_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Run not found")
        result = stored.get("result_json") or {}
        status = stored.get("status")
    else:
        result = run.get("result") or {}
        status = run["status"]
    if status != "done":
        raise HTTPException(status_code=409, detail=f"Run is not finished (status={status})")
    project_dir = result.get("generated_project_dir") or result.get("project_dir")
    if not project_dir or not os.path.isdir(str(project_dir)):
        raise HTTPException(status_code=404, detail="Generated project directory not found")

    # Auto-build frontend if dist/ doesn't exist
    frontend_dir = os.path.join(str(project_dir), "frontend")
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.isdir(dist_dir):
        try:
            import subprocess
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            agent_logger.info(f"Building frontend for preview: {frontend_dir}")
            subprocess.run(
                [npm_cmd, "install", "--legacy-peer-deps"],
                cwd=frontend_dir, capture_output=True, timeout=240
            )
            build_result = subprocess.run(
                [npm_cmd, "run", "build"],
                cwd=frontend_dir, capture_output=True, timeout=240
            )
            if build_result.returncode != 0 and os.name == "nt":
                # npm optional-deps bug (npm/cli#4828) bricks rolldown native
                # binding on Windows. Clean reinstall is the documented fix.
                agent_logger.warning(
                    f"Frontend build failed (retrying clean): {build_result.stderr[:300]}"
                )
                shutil.rmtree(os.path.join(frontend_dir, "node_modules"), ignore_errors=True)
                if os.path.exists(os.path.join(frontend_dir, "package-lock.json")):
                    os.remove(os.path.join(frontend_dir, "package-lock.json"))
                subprocess.run(
                    [npm_cmd, "install", "--legacy-peer-deps"],
                    cwd=frontend_dir, capture_output=True, timeout=300
                )
                build_result = subprocess.run(
                    [npm_cmd, "run", "build"],
                    cwd=frontend_dir, capture_output=True, timeout=300
                )
            if build_result.returncode != 0:
                agent_logger.warning(f"Frontend build failed: {build_result.stderr[:300]}")
            else:
                agent_logger.info(f"Frontend built successfully for preview")
        except Exception as e:
            agent_logger.warning(f"Auto-build failed: {e}")

    slug = _make_preview_slug(result.get("project_name") or os.path.basename(str(project_dir)))
    _previews[slug] = str(Path(project_dir).resolve())

    user = _authenticate_user(x_api_key)
    persisted = _persist_preview(slug, str(project_dir), user["id"] if user else "", req.run_id)

    base = _PREVIEW_BASE_URL or ""
    preview_url = f"{base}/preview/{slug}"
    return {
        "success": True,
        "data": {
            "slug": slug,
            "run_id": req.run_id,
            "preview_url": preview_url,
            "preview_path": str(project_dir),
            "persisted": bool(persisted),
            "deployment": persisted or None,
        },
    }


def _make_preview_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(name)).strip("-").lower()[:48] or "project"
    if slug not in _previews:
        return slug
    n = 2
    while f"{slug}-{n}" in _previews:
        n += 1
    return f"{slug}-{n}"


def _preview_file_path(root: str, rel: str) -> Optional[str]:
    """Resolve a static file within a preview root (traversal-safe), SPA fallback."""
    root_path = Path(root).resolve()
    if rel:
        candidate = (root_path / rel).resolve()
        if not str(candidate).startswith(str(root_path) + os.sep):
            return None
    for base in (root_path, root_path / "frontend" / "dist", root_path / "frontend" / "public"):
        if not base.is_dir():
            continue
        target = base / rel if rel else base
        file_obj = target if target.is_file() else base / (rel + ".html")
        if file_obj.is_file():
            return str(file_obj.resolve())
        if not rel and (base / "index.html").is_file():
            return str((base / "index.html").resolve())
    return None


def _render_preview(slug: str, rel: str):
    root = _previews.get(slug)
    if not root:
        raise HTTPException(status_code=404, detail="Preview not found")
    file_path = _preview_file_path(root, rel.strip("/"))
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/preview/{slug}", tags=["Preview"])
async def preview_root(slug: str):
    return _render_preview(slug, "")


@app.get("/preview/{slug}/{file_path:path}", tags=["Preview"])
async def preview_file(slug: str, file_path: str):
    return _render_preview(slug, file_path)


@app.get("/api/sandbox/{run_id}", tags=["Sandbox"])
async def get_sandbox(run_id: str, _auth: bool = Depends(_verify_api_key)):
    """Return project files as WebContainer-mountable tree for live execution."""
    run = _runs.get(run_id)
    if not run:
        stored = _pipeline_store.get_run(run_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Run not found")
        result = stored.get("result_json") or {}
    else:
        result = run.get("result") or {}
    project_dir = result.get("generated_project_dir") or result.get("project_dir") or ""
    if not project_dir or not os.path.isdir(str(project_dir)):
        raise HTTPException(status_code=404, detail="Project directory not found")
    try:
        from agent.sandbox_service import get_sandbox_payload
        payload = get_sandbox_payload(str(project_dir))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"success": True, "data": payload}


class GitHubSyncRequest(BaseModel):
    run_id: str
    repo_name: str = "lumicore-project"
    description: str = ""
    private: bool = True
    branch_name: str = "lumicore/feature-v1"
    commit_message: str = "feat: initial LumicorePro generation"
    pr_title: str = ""
    pr_body: str = ""


@app.post("/api/github/sync", tags=["GitHub"])
async def github_sync(req: GitHubSyncRequest, request: Request,
                       _auth: bool = Depends(_verify_api_key),
                       x_api_key: Optional[str] = Header(default=None)):
    """Sync a generated project to GitHub: create repo → branch → commit → PR."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    run = _runs.get(req.run_id)
    if not run:
        stored = _pipeline_store.get_run(req.run_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Run not found")
        result = stored.get("result_json") or {}
    else:
        result = run.get("result") or {}
    project_dir = result.get("generated_project_dir") or result.get("project_dir") or ""
    if not project_dir or not os.path.isdir(str(project_dir)):
        raise HTTPException(status_code=404, detail="Project directory not found")
    try:
        from agent.github_service import GitHubService
        svc = GitHubService()
        outcome = svc.sync_project(
            project_dir, req.repo_name, req.description, req.private,
            req.branch_name, req.commit_message, req.pr_title, req.pr_body,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"success": True, "data": outcome}


@app.get("/api/github/user", tags=["GitHub"])
async def github_user(_auth: bool = Depends(_verify_api_key)):
    """Get authenticated GitHub user info."""
    try:
        from agent.github_service import GitHubService
        svc = GitHubService()
        user = svc.get_authenticated_user()
        return {"success": True, "data": {"login": user.get("login"), "avatar_url": user.get("avatar_url")}}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class ProvisionDBRequest(BaseModel):
    project_name: str = "lumicore-project"
    region: str = "us-east-1"


@app.post("/api/provision-db", tags=["Database"])
async def provision_database(req: ProvisionDBRequest, request: Request,
                              _auth: bool = Depends(_verify_api_key),
                              x_api_key: Optional[str] = Header(default=None)):
    """Provision an ephemeral Neon PostgreSQL database and return the connection string."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    try:
        from agent.neon_service import NeonService
        svc = NeonService()
        result = svc.provision_database(req.project_name, req.region)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"success": True, "data": result}


class DeployRequest(BaseModel):
    project_name: str
    run_id: str = ""


@app.post("/api/accounts/deployments", tags=["Accounts"])
async def create_deployment(req: DeployRequest, request: Request, x_api_key: Optional[str] = Header(default=None)):
    """Register a deployment intent and return the deploy URL placeholder."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    try:
        deployment = _accounts.create_deployment(user["id"], req.project_name, req.run_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"success": True, "data": deployment}


@app.get("/api/accounts/deployments", tags=["Accounts"])
async def list_deployments(limit: int = 20, x_api_key: Optional[str] = Header(default=None)):
    user = _authenticate_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing user API key")
    return {"success": True, "data": {"deployments": _accounts.list_deployments(user["id"], limit)}}


class DeployRunRequest(BaseModel):
    run_id: str
    platform: str = "vercel"


class DeployDomainRequest(BaseModel):
    domain: str = Field(..., description="Custom domain to connect, e.g. mybrand.com")
    platform: str = Field("vercel", description="vercel | netlify | railway | vps")
    project_dir: Optional[str] = Field(None, description="Generated project directory (used for Vercel project name)")


@app.post("/api/deploy", tags=["Deploy"])
async def deploy_run(req: DeployRunRequest, request: Request, _auth: bool = Depends(_verify_api_key),
                     x_api_key: Optional[str] = Header(default=None)):
    """Deploy a finished generated project (real API when token present, guide otherwise)."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    user = _authenticate_user(x_api_key)

    run = _runs.get(req.run_id)
    if not run:
        stored = _pipeline_store.get_run(req.run_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Run not found")
        result = stored.get("result_json") or {}
        status = stored.get("status")
    else:
        result = run.get("result") or {}
        status = run["status"]
    if status != "done":
        raise HTTPException(status_code=409, detail=f"Run is not finished (status={status})")

    project_dir = result.get("generated_project_dir") or result.get("project_dir")
    if not project_dir or not os.path.isdir(str(project_dir)):
        raise HTTPException(status_code=404, detail="Generated project directory not found")

    try:
        from agent.deploy_engine import deploy_project
        outcome = deploy_project(str(project_dir), req.platform)
    except Exception as exc:
        agent_logger.error(f"Deploy failed for run {req.run_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    persisted = {}
    if user:
        try:
            persisted = _accounts.create_deployment(
                user["id"],
                Path(project_dir).name,
                run_id=req.run_id,
                platform=outcome.get("platform", req.platform),
                project_dir=str(project_dir),
            )
            if outcome.get("status") == "live":
                _accounts.promote_deployment(persisted.get("id", ""), status="live")
        except Exception:
            agent_logger.warning("Deploy persistence skipped", exc_info=True)

    return {
        "success": True,
        "data": {**outcome, "run_id": req.run_id, "deployment": persisted or None},
    }


@app.post("/api/deploy/domain", tags=["Deploy"])
async def deploy_domain(req: DeployDomainRequest, request: Request, _auth: bool = Depends(_verify_api_key)):
    """Connect a custom domain to a deployed site — automates Vercel when a token is
    set, otherwise returns a precise DNS checklist + Nginx block (VPS)."""
    if not _check_rate_limit(_get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    try:
        from agent.deploy_engine import add_domain
        outcome = add_domain(req.platform, req.domain, req.project_dir)
    except Exception as exc:
        agent_logger.error(f"Domain wizard failed for {req.domain}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    return {"success": True, "data": outcome}


@app.get("/api/themes", tags=["Theme Matrix"])
async def list_themes(_auth: bool = Depends(_verify_api_key)):
    try:
        from agent.theme_matrix import ThemeMatrixEngine
        from config.settings import REGISTRY_DIR
        engine = ThemeMatrixEngine(str(Path(REGISTRY_DIR) / 'templates.json'))
        matrix = engine.build_matrix()
        return {
            "templates": len(engine.templates),
            "styles": len(engine.style_ids),
            "variants": len(matrix),
            "by_category": _theme_summary(engine),
            "matrix": matrix,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/themes/variants", tags=["Theme Matrix"])
async def list_variant(variant_id: str, _auth: bool = Depends(_verify_api_key)):
    """Detail for a single `{template_id}::{style_id}` variant + its quality gate."""
    try:
        from agent.theme_matrix import ThemeMatrixEngine
        from config.settings import REGISTRY_DIR
        engine = ThemeMatrixEngine(str(Path(REGISTRY_DIR) / 'templates.json'))
        for tpl in engine.templates:
            for style in engine.compatible_styles(tpl):
                if f"{(tpl.get('id') or '')}::{style}" == variant_id:
                    gate = engine.quality_gate(tpl, style)
                    return {"variant_id": variant_id, "template": tpl, "style_id": style,
                            "style_name": engine.design.STYLES.get(style, {}).get("name", style),
                            "quality_gate": gate}
        raise HTTPException(status_code=404, detail="Variant not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/download/{run_id}", tags=["Generation"])
async def download_run_zip(run_id: str, _auth: bool = Depends(_verify_api_key)):
    """Download the generated project ZIP file for a given run_id."""
    run = _runs.get(run_id)
    if not run:
        stored = _pipeline_store.get_run(run_id)
        run = {"result": (stored or {}).get("result_json")}
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    result = run.get("result") or {}
    zip_path = result.get("zip_archive_path")
    
    if zip_path:
        try:
            zip_path = str(Path(zip_path).resolve())
            zip_root = GENERATED_PROJECTS_DIR.resolve()
            Path(zip_path).relative_to(zip_root)
        except (OSError, ValueError):
            zip_path = ""

    if not zip_path or not os.path.exists(zip_path):
        project_name = result.get("project_name", run_id)
        candidates = list(GENERATED_PROJECTS_DIR.glob(f"*{project_name}*.zip"))
        if candidates:
            zip_path = str(candidates[0])
            
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Generated ZIP file not found or generation not complete.")
        
    filename = os.path.basename(zip_path)
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
    )


@app.get("/api/history", tags=["Generation"])
async def history(limit: int = 20, _auth: bool = Depends(_verify_api_key)):
    """Return last N generation records."""
    limit = max(1, min(limit, 100))
    if not os.path.exists(AGENT_DB_PATH):
        return {"history": []}
    try:
        conn = sqlite3.connect(str(AGENT_DB_PATH))
        rows = conn.execute(
            "SELECT id, project_name, prompt, status, created_at FROM generation_history ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return {"history": [{"id": r[0], "project_name": r[1], "prompt": r[2][:80], "status": r[3], "created_at": r[4]} for r in rows]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/vision/analyze", tags=["Vision"])
async def vision_analyze(req: VisionAnalyzeRequest, _auth: bool = Depends(_verify_api_key)):
    """
    Analyze an uploaded screenshot/image and return the extracted layout, theme
    tokens, and region→component mapping the generator will use. This powers the
    frontend's "what do you see?" preview before a full generation run.
    """
    if not req.image or not req.image.strip():
        raise HTTPException(status_code=422, detail="image is required (data URI, URL, or local path)")
    if len(req.image) > 15_000_000:
        raise HTTPException(status_code=413, detail="Image payload too large (max ~15MB base64)")

    def _sync_analyze():
        from agent.vision_pipeline import VisionPipeline, LayoutMapper
        from config.providers import instantiate_provider
        from config.settings import VISION_PROVIDER
        provider = None
        try:
            provider = instantiate_provider(req.provider or VISION_PROVIDER)
        except Exception:
            provider = None
        pipe = VisionPipeline(provider=provider)
        layout = pipe.extract_layout(req.image)
        overlays = pipe.to_spec_overlays(layout)
        mapper = LayoutMapper()
        mapped = mapper.map_regions(layout)
        return {
            "success": True,
            "parsed": layout.get("parsed", False),
            "source": layout.get("source", "unknown"),
            "layout": layout.get("layout", {}),
            "element_hierarchy": layout.get("element_hierarchy", []),
            "spacing": layout.get("spacing", {}),
            "typography": layout.get("typography", {}),
            "design_tokens": overlays.get("design_tokens", {}),
            "vision_layout_regions": overlays.get("vision_layout_regions", []),
            "regions_mapped": mapped,
            "raw_vision_hint": layout.get("raw_vision_hint", layout.get("raw_vision", "")),
            "reason": layout.get("reason"),
        }

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_analyze)
    except Exception as exc:
        agent_logger.warning(f"/api/vision/analyze failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat", tags=["Conversation"])
async def chat(req: ChatRequest, _auth: bool = Depends(_verify_api_key)):
    """
    Chat with the LumicorePro assistant.

    Routes through the configured AI provider (with retry) when an API key is
    available; otherwise returns a helpful local reply so the UI never breaks.
    """
    provider = (req.provider or "gemini").lower()

    def _sync_chat():
        from providers.provider_pool import get_pool
        from providers.base_provider import BaseAIProvider
        pool = get_pool()

        # Position pool at requested provider first
        if provider and provider in pool.available:
            try:
                idx = pool._order.index(provider)
                for i in range(idx):
                    pool._current_index = (pool._current_index + 1) % len(pool._order)
            except Exception:
                pass

        instance = pool.get_active()
        if instance is None:
            return None

        active_name = pool.get_current_name()

        def _do_call():
            try:
                return instance._call_api(prompt, system_instruction=system)
            except Exception as exc:
                if BaseAIProvider.is_rate_limited(exc):
                    pool.mark_rate_limited(active_name)
                    # Retry once with next provider
                    nxt = pool.get_active()
                    if nxt and nxt is not instance:
                        agent_logger.info(f"[CHAT] Rate limited on '{active_name}' — retrying with '{pool.get_current_name()}'")
                        return nxt._call_api(prompt, system_instruction=system)
                raise

        vision_context = ""
        document_context = ""
        images_to_analyze = []
        if req.files:
            from agent.file_reader import describe_attachments
            prepared = _prepare_attachments([a.model_dump(exclude_none=True) for a in req.files])
            document_context = describe_attachments(prepared.get("documents", []))
            images_to_analyze = prepared.get("images", [])

        if req.image and req.image.strip():
            images_to_analyze.insert(0, {"filename": "screenshot", "data": req.image})

        if images_to_analyze:
            try:
                from agent.vision_pipeline import VisionPipeline
                from config.providers import instantiate_provider as _vip
                from config.settings import VISION_PROVIDER
                vp_provider = None
                try:
                    vp_provider = _vip(VISION_PROVIDER)
                except Exception:
                    vp_provider = None
                pipe = VisionPipeline(provider=vp_provider)
                parts = []
                for idx, img in enumerate(images_to_analyze[:3]):
                    fname = img.get("filename", "screenshot")
                    try:
                        layout = pipe.extract_layout(img.get("data"))
                        overlays = pipe.to_spec_overlays(layout)
                        regions = ", ".join(overlays.get("vision_layout_regions", [])) or "none"
                        palette = json.dumps(overlays.get("design_tokens", {}).get("palette", {}))
                        parts.append(f"#{idx + 1} '{fname}': layout={regions} palette={palette}")
                    except Exception as exc:
                        parts.append(f"#{idx + 1} '{fname}': could not be analyzed ({exc})")
                vision_context = "[User attached image(s). " + "; ".join(parts) + "]"
                if len(images_to_analyze) > 3:
                    vision_context += f" (plus {len(images_to_analyze) - 3} more image(s) attached)"
            except Exception as exc:
                vision_context = f"[The user attached images but they could not be analyzed: {exc}]"

        history_turns = "\n".join(
            f"{h.get('role', 'user')}: {h.get('content', '')}" for h in (req.history or [])
        )
        system = (
            "You are LumicorePro, an expert senior full-stack engineer and product "
            "consultant. Answer concisely and practically about website generation, "
            "React, Tailwind, Express, PostgreSQL, SEO, payments, and deployment. "
            "If the user attached images or documents, use their layout and content "
            "to inform your answer and propose a concrete site build."
        )
        attachments_used = bool(images_to_analyze or document_context)
        context = "\n\n".join(x for x in (document_context, vision_context) if x)
        prompt = f"{context}\n{history_turns}\nuser: {req.message}".strip() if (history_turns or context) else req.message
        return _do_call()

    try:
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, _sync_chat)
        if not reply or not reply.strip():
            raise RuntimeError("Empty chat response")
        return {
            "reply": reply.strip(),
            "provider": provider,
            "model": getattr(instantiate_provider(provider), "model_name", None),
            "source": "live_provider",
            "vision_used": bool((req.image and req.image.strip()) or req.files),
            "attachments": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        agent_logger.warning(f"/api/chat provider '{provider}' unavailable: {exc}")
        return {
            "reply": (
                f"I can help you build with LumicorePro: try \"Create a restaurant website"
                f" with online ordering\". I have 60 market-ready templates across 12"
                f" industries and a 15-phase generation pipeline. No live AI provider"
                f" key is configured, so I'm running in offline assistant mode."
            ),
            "provider": provider,
            "model": None,
            "source": "offline_fallback",
            "vision_used": bool((req.image and req.image.strip()) or req.files),
            "attachments": True,
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/api/telemetry", tags=["System"])
async def telemetry_summary(since: Optional[float] = None, _auth: bool = Depends(_verify_api_key)):
    """Aggregated pipeline telemetry (event counts, error rate, avg duration)."""
    try:
        return _telemetry.summary(since_ts=since)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/usage", tags=["System"])
async def usage(_auth: bool = Depends(_verify_api_key)):
    """
    Aggregate generation + provider usage statistics from SQLite history and
    provider-call logs. Never raises — returns zeroed stats when missing.
    """
    total_generations = 0
    last_generation = None
    try:
        if os.path.exists(AGENT_DB_PATH):
            conn = sqlite3.connect(str(AGENT_DB_PATH))
            row = conn.execute(
                "SELECT COUNT(*), MAX(created_at) FROM generation_history"
            ).fetchone()
            conn.close()
            if row:
                total_generations = row[0] or 0
                last_generation = row[1]
    except Exception as exc:
        agent_logger.warning(f"/api/usage DB read failed: {exc}")

    providers: Dict[str, Dict[str, Any]] = {}
    total_calls = 0
    total_latency = 0.0
    log_path = AI_AGENT_DIR / "logs" / "provider_calls.jsonl"
    try:
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                p = entry.get("provider", "unknown")
                bucket = providers.setdefault(p, {"calls": 0, "successes": 0, "failures": 0, "latency_seconds": 0.0, "last_call": None})
                bucket["calls"] += 1
                bucket["successes"] += 1 if entry.get("success") else 0
                bucket["failures"] += 0 if entry.get("success") else 1
                bucket["latency_seconds"] += entry.get("latency_seconds", 0.0)
                if entry.get("timestamp") and (bucket["last_call"] is None or entry["timestamp"] > bucket["last_call"]):
                    bucket["last_call"] = entry["timestamp"]
                total_calls += 1
                total_latency += entry.get("latency_seconds", 0.0)
    except Exception as exc:
        agent_logger.warning(f"/api/usage log read failed: {exc}")

    return {
        "generations": {
            "total": total_generations,
            "last_generation": last_generation,
        },
        "provider_calls": {
            "total": total_calls,
            "total_latency_seconds": round(total_latency, 3),
            "avg_latency_seconds": round(total_latency / total_calls, 3) if total_calls else 0.0,
            "by_provider": providers,
        },
        "available_providers": get_available_providers(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/iterate", tags=["Conversation"])
async def iterate(req: IterateRequest, _auth: bool = Depends(_verify_api_key)):
    """
    Post-generation refinement loop.

    Edits only the affected files of an existing generated project (git-style
    unified diff recorded in the manifest), re-runs verification/publishing
    phases, and re-zips. Works with an AI provider or fully offline.
    """
    # Path safety: only allow iterating on projects we generated
    try:
        allowed = os.path.realpath(GENERATED_PROJECTS_DIR)
        target = os.path.realpath(req.project_dir)
        if not target.startswith(allowed + os.sep) and target != allowed:
            raise HTTPException(status_code=400, detail="project_dir must be inside the generated-projects directory")
        if not os.path.isdir(target):
            raise HTTPException(status_code=404, detail="Project directory not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    def _sync_iterate():
        from agent.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator(provider_name=req.provider or None)
        return orchestrator.iterate(
            project_dir=target,
            instruction=req.instruction,
            provider_name=req.provider,
            client_brand=req.client_brand,
        )

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _sync_iterate)
    except Exception as exc:
        agent_logger.error(f"/api/iterate failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Iteration failed. Check agent logs.")
    return result


@app.websocket("/ws/generate/{run_id}")
async def ws_generate(websocket: WebSocket, run_id: str):
    """
    Stream phase events for a given run_id.
    Client receives JSON messages: {"type": "phase_start"|"phase_done"|"complete"|"error", ...}
    """
    if _AGENT_API_KEY:
        provided_key = websocket.headers.get("x-api-key")
        if not provided_key or not secrets.compare_digest(provided_key, _AGENT_API_KEY):
            await websocket.close(code=1008, reason="Invalid or missing API key")
            return

    await websocket.accept()

    if run_id not in _runs:
        await websocket.send_json({"type": "error", "message": f"Run {run_id} not found"})
        await websocket.close()
        return

    run = _runs[run_id]
    sent_idx = 0
    last_frame = time.time()

    async def _pump() -> None:
        """Send all pending phase events, then the terminal summary when done."""
        nonlocal sent_idx
        if run["status"] in ("done", "error", "cancelled"):
            while sent_idx < len(run["events"]):
                await websocket.send_json(run["events"][sent_idx])
                sent_idx += 1
            await websocket.send_json({
                "type": "finished",
                "run_id": run_id,
                "status": run["status"],
                "result": run.get("result"),
                "error": run.get("error"),
            })
            raise _StreamFinished
        while sent_idx < len(run["events"]):
            await websocket.send_json(run["events"][sent_idx])
            sent_idx += 1

    try:
        while True:
            try:
                await _pump()
            except _StreamFinished:
                break

            # Poll for in-band client control messages (cancel / ping). An
            # empty window keeps the pump cadence without blocking disconnect
            # detection — receive_text() raises WebSocketDisconnect promptly.
            last_frame = time.time()
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.15)
            except asyncio.TimeoutError:
                now = time.time()
                if now - last_frame >= 5.0:
                    await websocket.send_json({"type": "ping", "run_id": run_id, "ts": now})
                    last_frame = now
                continue
            except WebSocketDisconnect:
                raise
            try:
                parsed = json.loads(message)
                msg_type = parsed.get("type") if isinstance(parsed, dict) else None
            except Exception:
                continue

            if msg_type == "cancel":
                if _request_cancel(run_id):
                    agent_logger.info(f"Client requested in-band cancellation for run {run_id}")
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "run_id": run_id, "ts": time.time()})

    except WebSocketDisconnect:
        agent_logger.info(f"WebSocket client disconnected from run {run_id}")
        # Free pipeline resources when the only viewer drops the stream.
        if os.getenv("CANCEL_RUN_ON_DISCONNECT", "1").strip().lower() not in ("0", "false", "no"):
            if _request_cancel(run_id):
                agent_logger.info(f"Requested cancellation for run {run_id} after client disconnect")
                await _drain_cancelled_run(run_id)
    except Exception as exc:
        agent_logger.error(f"WebSocket error for run {run_id}: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


# ── Dev entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    except ImportError:
        print("uvicorn not installed. Run: pip install uvicorn[standard]")
