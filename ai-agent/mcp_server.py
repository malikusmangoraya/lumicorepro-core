"""
LumicorePro AI Agent — Model Context Protocol (MCP) server
==========================================================
Stdio MCP server that exposes the agent's generation pipeline to any
MCP client (Claude Desktop, Cursor, VS Code, Windsurf, Claude Code).

This is a THIN bridge: every product tool maps 1:1 onto the FastAPI
server in server.py, so the MCP surface can never drift from the HTTP
surface. The 18-phase pipeline, semantic cache, rate limits and durable
runs all stay in server.py — nothing is duplicated here.

Four local read-only repo tools (read_file, search_code, glob_files,
list_directory) close the gap with opencode/Codebuff's file surface.
They read the project directly, are confined to the repository root and
refuse secret files. Shell / write / edit tools are deliberately NOT
exposed — that would be remote code execution on the machine running
this server, not a feature.

Tools
-----
generate_website     Start a generation run (returns run_id; poll get_run)
get_run              Status + result of a run
list_runs            Recent durable runs
plan_website         Dry-run: assembly plan, no files written
chat_with_agent      Conversational assistant (image-aware)
registries_summary   Template / component / asset / backend counts
memory_insights      Adaptive memory usage leaderboards
read_file            Read a project text file (root-confined, paged)
search_code          Regex search across project files (grep parity)
glob_files           Find files by glob pattern
list_directory       List a directory (name / type / size)

Configuration (environment or ai-agent/.env)
--------------------------------------------
AGENT_API_URL   Agent FastAPI base URL   (default http://127.0.0.1:8000)
AGENT_API_KEY   Shared key when the agent server enforces auth

Usage
-----
    cd ai-agent && python server.py          # terminal 1: the agent API
    python mcp_server.py                     # terminal 2: MCP stdio server

Or register it in an MCP client:
    {"command": "<venv>/Scripts/python.exe",
     "args": ["<repo>/ai-agent/mcp_server.py"]}

From project root:  python ai-agent/mcp_server.py
"""

import glob as _glob
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

# ai-agent/.env holds AGENT_API_URL / AGENT_API_KEY alongside the
# provider keys the agent server itself uses.
load_dotenv(Path(__file__).resolve().with_name(".env"))

DEFAULT_API_URL = "http://127.0.0.1:8000"

# Per-call timeouts (seconds). Generation enqueues instantly; dry-run
# and chat execute real work and may take longer.
TIMEOUT_QUICK = 10.0
TIMEOUT_WORK = 60.0


class AgentAPI:
    """Thin authenticated HTTP client for the agent FastAPI server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("AGENT_API_URL") or DEFAULT_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("AGENT_API_KEY", "")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None,
             timeout: float = TIMEOUT_QUICK) -> Any:
        try:
            resp = requests.get(
                f"{self.base_url}{path}", params=params or {},
                headers=self._headers(), timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ToolError(self._unreachable(exc)) from exc
        return self._unwrap(resp)

    def _post(self, path: str, body: Dict[str, Any],
              timeout: float = TIMEOUT_WORK) -> Any:
        try:
            resp = requests.post(
                f"{self.base_url}{path}", json=body,
                headers=self._headers(), timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ToolError(self._unreachable(exc)) from exc
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp: requests.Response) -> Any:
        if resp.status_code == 404:
            raise ToolError(f"Not found: {resp.text[:200]}")
        if resp.status_code == 401:
            raise ToolError(
                "Authentication failed — set AGENT_API_KEY to the agent "
                "server's key (server.py refuses unauthenticated access "
                "when AGENT_API_KEY is configured)."
            )
        if resp.status_code == 429:
            raise ToolError("Rate limit exceeded on the agent server — retry shortly.")
        if resp.status_code >= 500:
            raise ToolError(f"Agent server error {resp.status_code}: {resp.text[:200]}")
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text[:2000]}

    def _unreachable(self, exc: Exception) -> str:
        return (
            f"Agent API unreachable at {self.base_url} ({exc.__class__.__name__}). "
            "Start it first:  cd ai-agent && python server.py"
        )


# Module-level client so tests can inject a fake; FastMCP tools close over it.
_api = AgentAPI()


def set_api_client(client: AgentAPI) -> None:
    """Swap the HTTP client (used by tests and embedders)."""
    global _api
    _api = client


mcp = FastMCP(
    "lumicorepro-agent",
    instructions=(
        "LumicorePro AI Agent — generate, iterate and deploy production "
        "websites through the 18-phase pipeline (18+ engines, vision input, "
        "20 design styles, i18n, compliance, SEO). Includes read-only, "
        "project-root-confined file tools: read_file, search_code, "
        "glob_files, list_directory."
    ),
)


@mcp.tool()
def generate_website(
    prompt: str,
    provider: Optional[str] = "gemini",
    design_style: Optional[str] = None,
    buyer_type: Optional[str] = None,
    language: Optional[str] = "en",
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Start an async website generation run. Returns a run_id — poll
    get_run(run_id) for progress and the final report (project dir, ZIP,
    quality score). Generation typically takes 1-5 minutes.

    prompt: natural-language description (5-2000 chars)
    provider: gemini | grok | openai | mistral | openrouter | deepseek
    design_style: minimalism, maximalism, glassmorphism, cyberpunk, swiss,
                  retro_futurism, editorial, retro, collage, vector,
                  futuristic, handwritten, bohemian, graffiti, aurora,
                  victorian, pixel_art, claymorphism, pop_art, surreal
    buyer_type: 'static' (client-only showcase) or 'enterprise' (full-stack)
    language: UI language code (en, ar, ur, fr, de, es, zh, ...)
    region: target region (NA, EU, SA, MENA, APAC, AF, LATAM)
    """
    prompt = (prompt or "").strip()
    if len(prompt) < 5:
        raise ToolError("prompt must be at least 5 characters")
    if len(prompt) > 2000:
        raise ToolError("prompt must be at most 2000 characters")
    body: Dict[str, Any] = {"prompt": prompt, "provider": provider or "gemini"}
    for key, value in (
        ("design_style", design_style), ("buyer_type", buyer_type),
        ("language", language), ("region", region),
    ):
        if value:
            body[key] = value
    return _api._post("/api/generate", body, timeout=TIMEOUT_QUICK)


@mcp.tool()
def get_run(run_id: str) -> Dict[str, Any]:
    """Fetch a generation run's status (queued | running | done | error |
    cancelled), its event count, and the final result report once finished
    (project directory, ZIP archive path, quality-gate score, providers used).
    """
    run_id = (run_id or "").strip()
    if not run_id:
        raise ToolError("run_id is required")
    return _api._get(f"/api/runs/{run_id}")


@mcp.tool()
def list_runs(limit: Optional[int] = 20, status: Optional[str] = None) -> Dict[str, Any]:
    """List recent durable generation runs (survive server restarts).
    limit: 1-100 (default 20). status: filter by queued/running/done/error/cancelled.
    """
    params: Dict[str, Any] = {"limit": max(1, min(100, int(limit or 20)))}
    if status:
        params["status"] = status
    return _api._get("/api/runs", params=params)


@mcp.tool()
def plan_website(
    prompt: str,
    provider: Optional[str] = "gemini",
    design_style: Optional[str] = None,
) -> Dict[str, Any]:
    """Dry-run: return the full assembly plan (template, components, assets,
    backend, schemas, style) WITHOUT writing any files. Fast and free —
    use it to preview what generate_website would build.
    """
    prompt = (prompt or "").strip()
    if len(prompt) < 5:
        raise ToolError("prompt must be at least 5 characters")
    if len(prompt) > 2000:
        raise ToolError("prompt must be at most 2000 characters")
    body: Dict[str, Any] = {"prompt": prompt, "provider": provider or "gemini"}
    if design_style:
        body["design_style"] = design_style
    return _api._post("/api/dry-run", body, timeout=TIMEOUT_WORK)


@mcp.tool()
def chat_with_agent(
    message: str,
    provider: Optional[str] = "gemini",
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Chat with the agent assistant for guidance, brainstorming or
    debugging. history: optional prior turns as [{role, content}].
    """
    message = (message or "").strip()
    if len(message) < 1:
        raise ToolError("message is required")
    if len(message) > 4000:
        raise ToolError("message must be at most 4000 characters")
    body: Dict[str, Any] = {"message": message, "provider": provider or "gemini"}
    if history:
        body["history"] = history
    return _api._post("/api/chat", body, timeout=TIMEOUT_WORK)


@mcp.tool()
def registries_summary() -> Dict[str, Any]:
    """Counts of the agent's adaptive memory registries: templates,
    components, assets and backends available for selection."""
    return _api._get("/api/registries/summary")


@mcp.tool()
def memory_insights(limit: Optional[int] = 20) -> Dict[str, Any]:
    """Adaptive memory snapshot: usage leaderboards showing which
    templates, components, assets and backends the agent reaches for most.
    limit: number of leaders per category (default 20)."""
    return _api._get(
        "/api/memory/catalog", params={"limit": max(1, min(100, int(limit or 20)))}
    )


# ---------------------------------------------------------------------------
# Local read-only repo tools — opencode/Codebuff file-surface parity.
#
# These do NOT go through the HTTP bridge: they read the project the MCP
# client is working on. Read-only by design — shell/write/edit over MCP is
# remote code execution on this machine, so it is not exposed. Every path
# is resolved and confined to REPO_ROOT (symlink escapes resolve outside
# and are rejected), and secret-bearing files are refused outright.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directory names never traversed or listed-as-match-path components.
_SKIP_DIRS = frozenset({
    ".git", "node_modules", "dist", "build", "venv", ".venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", "coverage", ".artifacts", ".lighthouseci",
    "playwright-report", "test-results", "vendors", "pgdata", "release",
})

# Hard bounds so one call can never flood the client or eat the disk.
_MAX_READ_BYTES = 500_000
_MAX_SEARCH_FILES = 3000

# Secret files are refused even though the tools are read-only — an MCP
# client's transcript is not an appropriate place for private keys.
_ALLOWED_ENV_NAMES = (".env.example", ".env.sample", ".env.template", ".env.defaults")
_SECRET_NAMES = frozenset({
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".netrc", ".npmrc",
    ".pgpass", "credentials.json", "service-account.json",
})
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".ovpn")
_BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".avif", ".pdf",
    ".zip", ".gz", ".tar", ".7z", ".rar", ".woff", ".woff2", ".ttf",
    ".eot", ".otf", ".mp3", ".mp4", ".webm", ".mov", ".exe", ".dll",
    ".so", ".dylib", ".class", ".pyc", ".pyo", ".wasm", ".db", ".sqlite",
})


def _is_secret(path: Path) -> bool:
    """True for files that must never be read through this server."""
    name = path.name
    if name.startswith(".env") and name not in _ALLOWED_ENV_NAMES:
        return True
    if name in _SECRET_NAMES:
        return True
    return name.lower().endswith(_SECRET_SUFFIXES)


def _resolve_inside_root(user_path: str, must_exist: bool = False) -> Path:
    """Resolve a caller-supplied path against the repo root.

    Rejects absolute paths outside the root and any `..` / symlink escape
    (resolve() follows symlinks before the check).
    """
    raw = (user_path or "").strip() or "."
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    if candidate != REPO_ROOT and not candidate.is_relative_to(REPO_ROOT):
        raise ToolError(f"path escapes the project root: {user_path}")
    if must_exist and not candidate.exists():
        raise ToolError(f"not found: {user_path}")
    return candidate


def _rel(path: Path) -> str:
    """Path relative to the repo root, always posix-style."""
    return path.relative_to(REPO_ROOT).as_posix()


def _skips_dir(path: Path) -> bool:
    """True when any parent segment is a cache/build directory."""
    try:
        parts = path.relative_to(REPO_ROOT).parts
    except ValueError:
        return True
    return any(part in _SKIP_DIRS for part in parts[:-1])


@mcp.tool()
def read_file(path: str, offset: int = 1, limit: int = 200) -> Dict[str, Any]:
    """Read a text file from the project (read-only, confined to the repo root).

    path:   path relative to the repository root, e.g. 'src/App.jsx'
    offset: 1-based line number of the first line to return (default 1)
    limit:  max lines to return, 1-400 (default 200). Page long files with offset.
    Returns {path, offset, total_lines, returned, truncated, content}.
    Secret files (.env and friends, private keys, certs) are refused.
    """
    target = _resolve_inside_root(path, must_exist=True)
    if _is_secret(target):
        raise ToolError(f"refusing to read secret file: {_rel(target)}")
    if target.is_dir():
        raise ToolError(f"{path} is a directory — use list_directory instead")
    if not target.is_file():
        raise ToolError(f"not a regular file: {path}")
    size = target.stat().st_size
    if size > _MAX_READ_BYTES:
        raise ToolError(
            f"{_rel(target)} is {size} bytes (limit {_MAX_READ_BYTES}) — "
            "use search_code to look inside large files"
        )
    data = target.read_bytes()
    if b"\0" in data[:8192]:
        raise ToolError(f"binary file, refusing to read: {_rel(target)}")
    lines = data.decode("utf-8", errors="replace").splitlines()
    start = max(1, int(offset or 1))
    page_size = max(1, min(int(limit or 200), 400))
    page = lines[start - 1 : start - 1 + page_size]
    return {
        "path": _rel(target),
        "offset": start,
        "total_lines": len(lines),
        "returned": len(page),
        "truncated": start - 1 + len(page) < len(lines),
        "content": "\n".join(page),
    }


@mcp.tool()
def search_code(
    pattern: str,
    path: str = ".",
    file_glob: str = "",
    max_results: int = 50,
) -> Dict[str, Any]:
    """Regex search across project files (grep parity, read-only).

    pattern:     Python regular expression, matched per line (case-sensitive)
    path:        directory or single file to search, relative to repo root
    file_glob:   optional filename filter, e.g. '*.jsx' or 'src/**/*.jsx'
                 (** matches directories; applied when `path` is a directory)
    max_results: 1-200 matched lines to return (default 50)
    Skips cache/build dirs, binaries, files over 500 KB and secret files.
    Returns {pattern, matches, files_scanned, truncated} where each match
    is {path, line, text}.
    """
    pattern = (pattern or "").strip()
    if not pattern:
        raise ToolError("pattern is required")
    if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
        raise ToolError("pattern must not escape the project root")
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        raise ToolError(f"invalid regular expression: {exc}") from exc
    base = _resolve_inside_root(path, must_exist=True)
    if file_glob and (
        Path(file_glob).is_absolute() or ".." in Path(file_glob).parts
    ):
        raise ToolError("file_glob must not escape the project root")
    cap = max(1, min(int(max_results or 50), 200))

    if base.is_file():
        candidates = [base]
    elif file_glob:
        candidates = [
            Path(p) for p in _glob.glob(str(base / file_glob), recursive=True)
        ]
    else:
        candidates = []
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            candidates.extend(Path(dirpath) / name for name in filenames)

    matches: List[Dict[str, Any]] = []
    scanned = 0
    truncated = False
    for candidate in sorted(candidates):
        if scanned >= _MAX_SEARCH_FILES or len(matches) >= cap:
            truncated = True
            break
        if not candidate.is_file() or _skips_dir(candidate) or _is_secret(candidate):
            continue
        if candidate.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            if candidate.stat().st_size > _MAX_READ_BYTES:
                continue
            data = candidate.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        scanned += 1
        text_lines = data.decode("utf-8", errors="replace").splitlines()
        for lineno, line in enumerate(text_lines, 1):
            if rx.search(line):
                matches.append({
                    "path": _rel(candidate),
                    "line": lineno,
                    "text": line.strip()[:300],
                })
                if len(matches) >= cap:
                    truncated = True
                    break
    return {
        "pattern": pattern,
        "matches": matches,
        "files_scanned": scanned,
        "truncated": truncated,
    }


@mcp.tool()
def glob_files(pattern: str, path: str = ".", max_results: int = 100) -> Dict[str, Any]:
    """Find project files by glob pattern (read-only).

    pattern:     e.g. 'src/**/*.jsx', '*.md', 'backend/routes/*.js'
                 (** matches any number of directories; relative to `path`)
    path:        directory to search from, relative to repo root (default '.')
    max_results: 1-200 file paths to return (default 100)
    Returns {pattern, files, truncated}; cache/build dirs and secret files
    are excluded.
    """
    pattern = (pattern or "").strip()
    if not pattern:
        raise ToolError("pattern is required")
    if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
        raise ToolError("pattern must not escape the project root")
    base = _resolve_inside_root(path, must_exist=True)
    cap = max(1, min(int(max_results or 100), 200))
    found = [
        Path(p) for p in _glob.glob(str(base / pattern), recursive=True)
        if Path(p).is_file()
    ]
    files: List[str] = []
    truncated = False
    for candidate in sorted(found):
        if len(files) >= cap:
            truncated = True
            break
        if _is_secret(candidate):
            continue
        try:
            rel_parts = candidate.resolve().relative_to(REPO_ROOT).parts
        except ValueError:
            continue  # symlink resolving outside the root
        if any(part in _SKIP_DIRS for part in rel_parts[:-1]):
            continue
        files.append("/".join(rel_parts))
    return {"pattern": pattern, "files": files, "truncated": truncated}


@mcp.tool()
def list_directory(path: str = ".", limit: int = 200) -> Dict[str, Any]:
    """List a project directory (read-only): name, type and size per entry.

    path:  directory relative to repo root (default = repository root)
    limit: 1-500 entries to return (default 200; directories first, sorted)
    Returns {path, entries, total_entries, truncated}.
    """
    target = _resolve_inside_root(path, must_exist=True)
    if not target.is_dir():
        raise ToolError(f"not a directory: {path}")
    cap = max(1, min(int(limit or 200), 500))
    entries = []
    for entry in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        is_file = entry.is_file()
        entries.append({
            "name": entry.name,
            "type": "file" if is_file else "dir",
            "size": entry.stat().st_size if is_file else None,
        })
    return {
        "path": _rel(target),
        "entries": entries[:cap],
        "total_entries": len(entries),
        "truncated": len(entries) > cap,
    }


def main() -> None:
    """Run the MCP server on stdio (the desktop-client transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
