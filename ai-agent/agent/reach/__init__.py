"""Agent Reach integration for the LumicorePro Python Agent.

open-source package: `agent-reach` (Panniantong/Agent-Reach) — a capability
layer that selects, installs, health-checks and routes the most reliable
platform backends (GitHub/gh, Reddit/OpenCLI-rdt, Twitter/twitter-cli, Exa/
mcporter). This package consumes its footprint natively:

  - environment: CLI/skill registration + structural verification flags.
  - router:     `agent-reach doctor` routing + async upstream searches.
  - market_signals: Reddit + Twitter/X research feeding the planner.
  - github_recovery: self-healing patches for React 19 / Vite 8 lint errors.

All subprocess effort runs through `process.run_cli`
(`asyncio.create_subprocess_exec`) — synchronous system calls are prohibited.
"""
from agent.reach.environment import register_capability_flags, verify_capability, capability_sync
from agent.reach.github_recovery import (
    cached_github_recovery,
    fire_github_recovery,
    github_recovery_from_error,
    has_react19_vite_marker,
)
from agent.reach.market_signals import (
    build_signal_query,
    classify_signal,
    collect_market_signals,
    market_signals_sync,
    subreddits_for,
)
from agent.reach.models import (
    ChannelStatus,
    GithubRecoveryPatch,
    MarketSignalReport,
    ReachFragment,
    RecoveryBundle,
)
from agent.reach.process import in_worker_loop, run_cli
from agent.reach.router import AgentReachRouter, SearchResult

__all__ = [
    "AgentReachRouter",
    "SearchResult",
    "ChannelStatus",
    "GithubRecoveryPatch",
    "MarketSignalReport",
    "ReachFragment",
    "RecoveryBundle",
    "register_capability_flags",
    "verify_capability",
    "capability_sync",
    "cached_github_recovery",
    "fire_github_recovery",
    "github_recovery_from_error",
    "has_react19_vite_marker",
    "build_signal_query",
    "classify_signal",
    "collect_market_signals",
    "market_signals_sync",
    "subreddits_for",
    "in_worker_loop",
    "run_cli",
]