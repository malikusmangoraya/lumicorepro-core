"""Agent Reach routing layer.

`agent-reach` is a capability layer: it selects, installs and health-checks the
most reliable backend per platform, and the agent then calls the ACTIVE upstream
tool directly. This router mirrors that contract:

  1. `agent-reach doctor --json` -> authoritative `active_backend` per channel.
  2. Channel search commands are built for the active upstream tool
     (gh / opencli / twitter / rdt / mcporter) and executed exclusively through
     `agent.reach.process.run_cli` (asyncio.create_subprocess_exec).
  3. Every failure degrades gracefully to an empty search result with a reason —
     a headless server without login-backed channels never hard-fails.

Channel syntax referenced from the upstream Agent Reach docs (install.md /
README_en.md): `gh search code`, `opencli reddit search "q" -f yaml`,
`twitter search "q" -n N` (needs TWITTER_AUTH_TOKEN/TWITTER_CT0),
`mcporter call exa.web_search_exa query="..." numResults=N`.
"""
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.settings import (
    AGENT_REACH_DOCTOR_TIMEOUT,
    AGENT_REACH_SEARCH_TIMEOUT,
    AGENT_REACH_SKILL_DIRS,
    AGENT_REACH_HOME,
)
from utils.logger import agent_logger
from agent.reach.models import ChannelStatus, utc_iso
from agent.reach.process import ProcessResult, resolve_tool, run_cli

DOCTOR_TTL_SECS = 300
_SEARCH_TTL_SECS = 600


@dataclass
class SearchResult:
    """Normalized records returned by a channel search."""

    channel: str
    query: str
    available: bool = False
    reason: str = ""
    records: List[Dict[str, Any]] = field(default_factory=list)
    command: str = ""
    retrieved_at: str = ""


class AgentReachRouter:
    """Probes the Agent Reach footprint and routes searches to active backends."""

    def __init__(self, probe: bool = True):
        self.cli = resolve_tool("agent-reach")
        self._tools: Dict[str, Optional[str]] = {}
        self._doctor_cache: Dict[str, Any] = {
            "at": 0.0,
            "channels": {},
        }
        self._search_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        if probe:
            for name in ("gh", "twitter", "opencli", "rdt", "mcporter", "curl"):
                self._tools[name] = resolve_tool(name)

    # ── Footprint ───────────────────────────────────────────────────────────
    def footprint(self) -> Dict[str, Any]:
        """Structural access parameters (no subprocess, no token scripts)."""
        skill_dirs = [str(d) for d in AGENT_REACH_SKILL_DIRS if d.is_dir()]
        env_flags = {
            name: value
            for name, value in [
                ("AGENT_REACH_CLI", self.cli or ""),
                ("AGENT_REACH_ENV", "auto"),
                ("AGENT_REACH_HOME", str(AGENT_REACH_HOME)),
                ("AGENT_REACH_VERIFY_CMD", "agent-reach install --env=auto"),
            ]
            if value
        }
        return {
            "available": self.cli is not None,
            "cli": self.cli or "",
            "skill_dirs": skill_dirs,
            "upstream_tools": dict(sorted((k, v or "") for k, v in self._tools.items())),
            "env_flags": env_flags,
        }

    # ── Doctor (channel → active_backend) ───────────────────────────────────
    async def doctor_status(self, force: bool = False) -> Dict[str, ChannelStatus]:
        """Consult `agent-reach doctor --json` with a TTL cache.

        Returns a {channel: ChannelStatus} map. Empty when the CLI is missing or
        the probe failed — callers must treat channels as unavailable.
        """
        now = time.time()
        with self._lock:
            cached = self._doctor_cache
            if not force and cached["at"] and (now - cached["at"]) < DOCTOR_TTL_SECS:
                return cached["channels"]
        if not self.cli:
            return {}
        result = await run_cli(
            [self.cli, "doctor", "--json"],
            timeout=AGENT_REACH_DOCTOR_TIMEOUT,
        )
        channels = self._parse_doctor(result)
        with self._lock:
            self._doctor_cache = {"at": now, "channels": channels}
        return channels

    @staticmethod
    def _parse_doctor(result: ProcessResult) -> Dict[str, ChannelStatus]:
        """Tolerant parse: JSON list, JSON dict, or plain-text status lines."""
        payload = result.stdout or result.stderr
        if not payload:
            return {}
        channels: Dict[str, ChannelStatus] = {}
        try:
            data = json.loads(payload)
            if isinstance(data, dict) and "channels" in data:
                items = list(data["channels"].items())
            elif isinstance(data, dict):
                items = list(data.items())
            else:
                items = data
            for item in items or []:
                if isinstance(item, (tuple, list)) and len(item) == 2:
                    ch = str(item[0])
                    raw = item[1] if isinstance(item[1], dict) else {}
                elif isinstance(item, dict):
                    ch = str(item.get("channel") or item.get("name") or "")
                    raw = item
                else:
                    continue
                if not ch or ch in ("channels",):
                    continue
                ok = bool(raw.get("available", raw.get("ok", raw.get("status") == "ready")))
                backend = raw.get("active_backend") or raw.get("backend")
                channels[ch] = ChannelStatus(
                    channel=ch,
                    label=str(raw.get("label") or raw.get("platform") or ch),
                    available=ok,
                    active_backend=str(backend) if backend else None,
                    note=str(raw.get("note") or raw.get("reason") or raw.get("message") or ""),
                )
        except (ValueError, TypeError):
            # Plain-text fallback: '✅ X ...' / '❌ Y ...' lines
            for line in payload.splitlines():
                match = re.match(r"^\s*([✅❌⚠️])\s*([\w/-]+)", line.strip())
                if not match:
                    continue
                ch = match.group(2)
                ok = match.group(1) in ("✅",)
                channels[ch] = ChannelStatus(
                    channel=ch,
                    label=ch,
                    available=ok,
                    active_backend=None,
                    note=line.strip()[:120],
                )
        return channels

    # ── Channel search ──────────────────────────────────────────────────────
    async def search(
        self,
        channel: str,
        query: str,
        num: int = 8,
        subreddit: Optional[str] = None,
        **opts: Any,
    ) -> SearchResult:
        """Search a channel via its active upstream backend (async subprocess)."""
        query = (query or "").strip()
        if not query:
            return SearchResult(channel, query, available=False, reason="empty query")
        cache_key = f"{channel}:{query}:{num}:{subreddit}"
        with self._lock:
            hit = self._search_cache.get(cache_key)
            if hit and (time.time() - hit.get("at", 0)) < _SEARCH_TTL_SECS:
                return SearchResult(
                    channel=channel,
                    query=query,
                    available=hit["available"],
                    reason=hit["reason"],
                    records=hit["records"],
                    command=hit.get("command", ""),
                    retrieved_at=hit.get("retrieved_at", ""),
                )

        builder = self._build_for(channel, query, num, subreddit, opts)
        if not builder:
            reason = self._unavailable_reason(channel)
            return SearchResult(channel, query, available=False, reason=reason)

        args, display = builder
        result = await run_cli(args, env=self._tool_env(channel), timeout=AGENT_REACH_SEARCH_TIMEOUT)
        records = self._parse_records(channel, result, query)
        with self._lock:
            self._search_cache[cache_key] = {
                "at": time.time(),
                "available": bool(records),
                "reason": "" if records else (result.stderr or result.stdout or "no results"),
                "records": records,
                "command": display,
                "retrieved_at": utc_iso(),
            }
        return SearchResult(
            channel=channel,
            query=query,
            available=bool(records),
            reason="" if records else (result.stderr or "no results"),
            records=records,
            command=display,
            retrieved_at=utc_iso(),
        )

    def _unavailable_reason(self, channel: str) -> str:
        if channel in ("reddit", "twitter") and not self._tools.get(channel) and not self._tools.get("opencli"):
            return f"{channel} channel requires login-backed tooling (opencli/twitter-cli) not found; agent-reach reports active_backend=null"
        tool = self._tools.get(channel)
        if not tool:
            base = {
                "github": "gh",
                "reddit": "opencli/rdt",
                "twitter": "twitter-cli",
                "exa": "mcporter",
            }.get(channel, channel)
            return f"{base} executable not found on PATH; agent-reach channel unavailable"
        return f"{channel} channel build failed"

    def _tool_env(self, channel: str) -> Optional[Dict[str, str]]:
        """Propagate Twitter/X session cookies to the `twitter` CLI only (never requests them)."""
        import os

        if channel != "twitter":
            return None
        token, ct0 = os.getenv("TWITTER_AUTH_TOKEN", ""), os.getenv("TWITTER_CT0", "")
        if not token or not ct0:
            return None
        env = dict(os.environ)
        env["TWITTER_AUTH_TOKEN"] = token
        env["TWITTER_CT0"] = ct0
        return env

    # ── Command builders (contract per upstream docs) ───────────────────────
    def _build_for(
        self,
        channel: str,
        query: str,
        num: int,
        subreddit: Optional[str],
        opts: Dict[str, Any],
    ) -> Optional[tuple]:
        if channel == "github":
            tool = self._tools.get("github") or resolve_tool("gh")
            if not tool:
                return None
            args = [tool, "search", "code", query, "--limit", str(num)]
            language = opts.get("language")
            if language:
                args += ["--language", str(language)]
            return args, " ".join(args)
        if channel == "twitter":
            tool = self._tools.get("twitter") or resolve_tool("twitter")
            if not tool:
                tool = self._tools.get("opencli")
                if not tool:
                    return None
                args = [tool, "twitter", "search", query, "-f", "json"]
                return args, " ".join(args)
            args = [tool, "search", query, "-n", str(num)]
            return args, " ".join(args)
        if channel == "reddit":
            tool = self._tools.get("opencli") or resolve_tool("opencli")
            if not tool:
                return None
            args = [tool, "reddit", "search", query, "-f", "json"]
            if subreddit:
                args = [tool, "reddit", "search", subreddit, query, "-f", "json"]
            return args, " ".join(args)
        if channel == "exa":
            tool = self._tools.get("mcporter") or resolve_tool("mcporter")
            if not tool:
                return None
            args = [
                tool, "call", "exa.web_search_exa",
                f"query={query}", f"numResults={num}",
            ]
            return args, " ".join(args)
        return None

    # ── Record extraction (tolerant text/JSON parsing) ──────────────────────
    def _parse_records(self, channel: str, result: ProcessResult, query: str) -> List[Dict[str, Any]]:
        if result.returncode != 0 or not (result.stdout or result.stderr):
            return []
        payload = result.stdout or result.stderr
        record = {
            "platform": channel,
            "title": "",
            "url": "",
            "snippet": "",
            "score": 0.0,
            "query": query,
        }
        try:
            data = json.loads(payload)
            return self._records_from_json(channel, data)
        except (ValueError, TypeError):
            pass
        return self._records_from_text(channel, payload, record)

    @staticmethod
    def _records_from_json(channel: str, data: Any) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        items = data.get("results") if isinstance(data, dict) else data
        if isinstance(items, dict):
            items = [items]
        for item in items or []:
            if not isinstance(item, dict):
                continue
            if channel == "github":
                repo_entry = item.get("repository") or {}
                repo = repo_entry.get("fullName") or repo_entry.get("name") or repo_entry.get("full_name") or ""
                path = item.get("path") or ""
                hits = item.get("textMatches") or item.get("matches") or []
                snippet = ""
                if hits and isinstance(hits[0], dict):
                    snippet = hits[0].get("fragment") or hits[0].get("text") or ""
                url = item.get("htmlUrl") or item.get("html_url") or ""
                if not url:
                    url = f"https://github.com/{repo}" + (f"/blob/HEAD/{path}" if path else "")
                records.append({
                    "platform": "github",
                    "title": f"{repo}/{path}",
                    "url": url,
                    "snippet": snippet,
                    "score": float(item.get("score") or 0),
                })
            else:
                records.append({
                    "platform": channel,
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("url") or item.get("link") or item.get("permalink") or ""),
                    "snippet": str(item.get("snippet") or item.get("text") or item.get("selftext") or ""),
                    "score": float(item.get("score") or item.get("upvotes") or 0),
                })
        return [r for r in records if r["title"] or r["url"] or r["snippet"]][:50]

    @staticmethod
    def _records_from_text(channel: str, payload: str, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        url_re = re.compile(r"https?://[^\s)\]]+")
        for line in payload.splitlines():
            line = line.strip()
            if not line or len(line) < 12:
                continue
            if line.startswith(("(", "[", "{", "OK", "ok", "Fetched", "Searching", "No ", "Error", "error")):
                continue
            urls = url_re.findall(line)
            rec = dict(record)
            rec["snippet"] = line[:300]
            if urls:
                rec["url"] = urls[0]
                rec["title"] = line.replace(urls[0], "").strip(" :,")[:120]
            if channel == "github" and "/" in line and not urls and len(line) < 200:
                rec["title"] = line
            if rec.get("title") or rec.get("url"):
                records.append(rec)
            if len(records) >= 50:
                break
        return records


def infos_for_channel(channel: str) -> str:
    """Human-readable note used by consumer modules for downgraded channels."""
    notes = {
        "reddit": "Reddit requires login-backed tooling (OpenCLI browser session or rdt-cli + cookie); anonymous endpoints are blocked.",
        "twitter": "Twitter/X search requires TWITTER_AUTH_TOKEN/TWITTER_CT0 exported; doctor only verifies presence.",
        "github": "GitHub public code search requires the gh CLI.",
        "exa": "Exa web search requires the mcporter MCP bridge.",
    }
    return notes.get(channel, f"{channel} channel unavailable")