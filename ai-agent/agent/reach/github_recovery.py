"""GitHub channel self-healing via Agent Reach.

Binds the error exception hooks of `quality_gate.py`, `quality_gates.py` and
`code_modifier.py` to the open-source GitHub channel: when a Node subprocess
returns React 19 compliance warnings or Vite 8.x breaking linter errors, an
open-repo code search (`gh search code`, routed via agent-reach) extracts
verified community solution patches and hands them to the healer.

`github_recovery_from_error` is fully async (asyncio.create_subprocess_exec
under the hood). `cached_github_recovery` is cache-only and never blocks;
`fire_github_recovery` schedules the fetch without stalling a running loop.
"""
import asyncio
import re
import threading
import time as _time
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger
from agent.reach.models import GithubRecoveryPatch, RecoveryBundle
from agent.reach.process import in_worker_loop

_REACT_MARKERS = re.compile(r"(?i)(react(-dom)?|createRoot|render\s*\(|ReactDOM)", re.MULTILINE)
_VITE_MARKERS = re.compile(r"(?i)\bvite\.config|from ['\"\`]vite|esbuild|vite pre-bundling|\bvite\b", re.MULTILINE)
_ERROR_MARKERS = re.compile(
    r"(?i)(parsing error|unexpected token|syntax error|unexpected end|unknown directive"
    r"|failed to (parse|resolve|load)|module not found|transform failed|build failed"
    r"|error:|cannot find module|reference error|is not defined)",
    re.MULTILINE,
)

_RECOVERY_CACHE: Dict[str, Any] = {}
_CACHE_LOCK = threading.RLock()
_LAST_FIRE_AT: List[float] = [0.0]


def has_react19_vite_marker(output: str) -> bool:
    """True when CLI output combines a React/Vite tech marker with a build/parse error."""
    if not output:
        return False
    tech = bool(_REACT_MARKERS.search(output)) or bool(_VITE_MARKERS.search(output))
    error = bool(_ERROR_MARKERS.search(output))
    return tech and error


def _clean_query(error_output: str, limit: int = 140) -> str:
    """Derive a compact search query from the CLI error tail."""
    lines = [ln.strip() for ln in (error_output or "").splitlines() if ln.strip()]
    tail = " ".join(lines[-6:]) or " ".join(lines[:6])
    tail = re.sub(r"\s+", " ", tail)[:limit]
    sig = tail.strip(".:; ")
    return f"{sig} react 19 vite fix" if sig else "react 19 vite fix"


async def github_recovery_from_error(
    error_output: str,
    context: str = "react19-vite-lint",
    num: int = 4,
) -> Dict[str, Any]:
    """Search GitHub for verified community patches matching a CLI error.

    Returns a validated RecoveryBundle dict. `applied=False` (never raising)
    when the CLI/tooling is unavailable or no relevant patch is found.
    """
    empty = RecoveryBundle(applied=False, context=context, query="").to_dict()
    if not has_react19_vite_marker(error_output):
        return empty

    from agent.reach.router import AgentReachRouter

    router = AgentReachRouter(probe=True)
    query = _clean_query(error_output)
    result = await router.search("github", query, num=num, language="JavaScript")
    patches: List[GithubRecoveryPatch] = []
    for rec in result.records[:num]:
        url = rec.get("url") or ""
        title = rec.get("title") or ""
        if not url and not title:
            continue
        repo = ""
        if url and "github.com/" in url:
            parts = url.split("github.com/", 1)[1].split("/")
            if parts:
                repo = "/".join(parts[:2])
        if not repo and "/" in title:
            repo = title.split("/")[0] if title.count("/") == 1 else title.split(" ")[0]
        patches.append(
            GithubRecoveryPatch(
                error_signature=query,
                title=title[:200],
                url=url[:400],
                repo=repo[:200],
                language="JavaScript",
                confidence=0.6,
            )
        )

    bundle = RecoveryBundle(
        applied=bool(patches),
        context=context,
        query=query,
        patches=patches,
        patch_title=(patches[0].title if patches else None),
        patch_url=(patches[0].url if patches else None),
        reference=(f"{patches[0].title} ({patches[0].url})" if patches else ""),
    )
    with _CACHE_LOCK:
        _RECOVERY_CACHE.update(bundle.to_dict())
    return bundle.to_dict()


def cached_github_recovery() -> Optional[Dict[str, Any]]:
    """Return the latest RecoveryBundle dict from the in-process cache (non-blocking)."""
    with _CACHE_LOCK:
        if not _RECOVERY_CACHE:
            return None
        return dict(_RECOVERY_CACHE)


def _fire_marker_hint() -> bool:
    """Rate-limit background recovery probes: at most one per 30s."""
    now = _time.time()
    with _CACHE_LOCK:
        if now - _LAST_FIRE_AT[0] < 30.0:
            return False
        _LAST_FIRE_AT[0] = now
        return True


def fire_github_recovery(error_output: str, context: str = "code-modifier-hook") -> Optional[Dict[str, Any]]:
    """Non-blocking GitHub recovery hook for sync exception handlers.

    Never blocks the caller: cache returns immediately, a running loop schedules
    the probe as a background task, and loop-less threads (sync tests, worker
    bridges) hand the bounded fetch to a daemon thread. Probes are rate-limited
    to one per 30s to avoid subprocess bursts on repeated lint failures.
    """
    cached = cached_github_recovery()
    if cached and cached.get("applied"):
        return cached
    if not has_react19_vite_marker(error_output):
        return cached
    if not _fire_marker_hint():
        return cached

    async def _probe():
        return await asyncio.wait_for(
            github_recovery_from_error(error_output, context=context), timeout=20.0
        )

    try:
        asyncio.get_running_loop()
        background = False
    except RuntimeError:
        background = True

    if background:
        def _runner():
            try:
                in_worker_loop(_probe)
            except Exception as exc:  # never let recovery break healing
                agent_logger.warning(f"[AGENT REACH] GitHub recovery hook degraded: {exc}")

        threading.Thread(target=_runner, name="agent-reach-recovery", daemon=True).start()
        return cached

    try:
        future = asyncio.ensure_future(_probe())
        agent_logger.debug(f"[AGENT REACH] scheduled background GitHub recovery ({future!r})")
    except Exception as exc:
        agent_logger.warning(f"[AGENT REACH] GitHub recovery scheduling failed: {exc}")
    return cached