"""Safe extraction + git lifecycle for frozen repository snapshots.

Snapshots arrive as `.tgz` archives of real upstream repositories frozen at one
commit. Extraction is hostile-input safe (absolute paths, `..` traversal, links
and device nodes are all rejected), and each extracted tree is a real git repo so
`git status` / `git log` / `git diff` work exactly as an agent expects.

Archives are extracted once into a cache directory and reused, so a 129-task run
does not re-unpack the same FastAPI tree 40 times.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from utils.logger import agent_logger

SAFE_MEMBER_TYPES = (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
_SKIP_DIR_NAMES = {".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
REPO_ROOT_MARKERS = (
    ".git", "setup.py", "setup.cfg", "pyproject.toml", "MANIFEST.in", "requirements.txt",
    "tox.ini", "Makefile", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
)
REPO_ROOT_PREFIXES = ("README", "LICENSE", "COPYING", "NOTICE", "AUTHORS", "CHANGELOG")


class UnsafeArchiveError(RuntimeError):
    """Raised when an archive member would escape the destination directory."""


def _normalise_newlines(data: bytes) -> bytes:
    """Convert CRLF -> LF for text payloads.

    Upstream patches and the git object store are LF, so a CRLF worktree makes
    every context line mismatch and turns any diff into a whole-file rewrite.
    Binary payloads (NUL bytes) and non-UTF-8 files are left untouched.
    """
    if b"\x00" in data[:4096] or b"\r" not in data:
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n")


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.stdout.strip()


def file_sha256(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def _resolve_member_path(base: Path, member: tarfile.TarInfo) -> Optional[Path]:
    name = member.name.replace("\\", "/").strip()
    if not name or name in (".", "./"):
        return None
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise UnsafeArchiveError(f"path traversal in member '{member.name}'")
    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        raise UnsafeArchiveError(f"absolute path in member '{member.name}'")
    target = (base / Path(*parts)).resolve()
    if not _is_within(base, target):
        raise UnsafeArchiveError(f"member '{member.name}' escapes destination")
    return target


def safe_extract(archive: Path, dest: Path, normalise_newlines: bool = True) -> int:
    """Extract `archive` into `dest` rejecting traversal, links and device nodes.

    Returns the number of extracted entries. Callers should follow up with
    `normalise_extracted_root` to unwrap a single wrapping directory.
    """
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:*") as tar:
        members = [m for m in tar.getmembers() if _resolve_member_path(dest, m) is not None]
        if not members:
            return 0

        for member in members:
            if member.type not in SAFE_MEMBER_TYPES:
                agent_logger.warning(f"[BENCH] Skipping non-regular member '{member.name}'")
                continue
            if any(part in _SKIP_DIR_NAMES for part in member.name.split("/")):
                continue
            name = member.name.replace("\\", "/").strip("/")
            parts = [p for p in name.split("/") if p not in ("", ".")]
            if not parts:
                continue
            target = dest / Path(*parts)
            if not _is_within(dest.resolve(), target.resolve()):
                raise UnsafeArchiveError(f"member '{member.name}' escapes destination")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            if normalise_newlines:
                data = _normalise_newlines(data)
            with open(target, "wb") as out:
                out.write(data)
            try:
                os.chmod(target, member.mode & 0o777)
            except OSError:
                pass
    return len(members)


def looks_like_repo_root(path: Path) -> bool:
    """True when `path` is the top of a real repository checkout."""
    if not path.is_dir():
        return False
    for marker in REPO_ROOT_MARKERS:
        if (path / marker).exists():
            return True
    for child in path.iterdir():
        if child.name.upper().startswith(REPO_ROOT_PREFIXES):
            return True
    return False


def normalise_extracted_root(dest: Path) -> Path:
    """Unwrap a single wrapping directory (e.g. `repo/`) when it is not a repo root.

    Archives produced by `tar czf x.tgz repo/` wrap everything in one directory,
    while `git archive` writes the tree at the top level. Guessing from the member
    list alone misfires on repositories that legitimately have one top folder, so
    the decision is made after extraction using repo-root markers.
    """
    dest = Path(dest)
    if looks_like_repo_root(dest):
        return dest
    children = [c for c in sorted(dest.iterdir()) if c.is_dir() and c.name not in _SKIP_DIR_NAMES]
    if len(children) != 1:
        return dest
    inner = children[0]
    if not looks_like_repo_root(inner):
        return dest
    for item in list(inner.iterdir()):
        target = dest / item.name
        if target.exists():
            continue
        shutil.move(str(item), str(target))
    shutil.rmtree(inner, ignore_errors=True)
    agent_logger.info(f"[BENCH] Unwrapped single-root archive at {inner.name}/")
    return dest


def _git_config_args() -> List[str]:
    # Extraction already normalises text to LF (see `_normalise_newlines`), so git
    # must not convert anything: any CRLF rewrite here would make `git apply`
    # search for line endings the worktree does not have.
    return [
        "-c", "core.autocrlf=false",
        "-c", "core.safecrlf=false",
        "-c", "core.quotepath=false",
        "-c", "core.fileMode=false",
        "-c", "core.longpaths=true",
        "-c", "commit.gpgsign=false",
        "-c", "init.defaultBranch=main",
        "-c", "advice.detachedHead=false",
        "-c", "protocol.ext.allow=never",
    ]


class GitRepo:
    """Thin, dependency-free git wrapper bound to one working tree."""

    def __init__(self, root: Path, timeout: int = 120):
        self.root = Path(root).resolve()
        self.timeout = timeout

    def run(self, *args: str, timeout: Optional[int] = None) -> GitResult:
        cmd = ["git", "-C", str(self.root), *_git_config_args(), *args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
            )
            return GitResult(proc.returncode, proc.stdout, proc.stderr)
        except FileNotFoundError:
            return GitResult(127, "", "git executable not found on PATH")
        except subprocess.TimeoutExpired:
            return GitResult(124, "", f"git {' '.join(args)} timed out")

    def is_repo(self) -> bool:
        return (self.root / ".git").exists() and self.run("rev-parse", "--git-dir").ok

    def init(self) -> GitResult:
        if self.is_repo():
            return GitResult(0, "", "existing repository")
        result = self.run("init", "-q")
        if result.ok:
            self.run("add", "-A")
            self.run("-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-q", "-m", "snapshot")
        return result

    def head(self) -> str:
        result = self.run("rev-parse", "HEAD")
        return result.output if result.ok else ""

    def status(self) -> str:
        return self.run("status", "--porcelain").output

    def log(self, count: int = 20) -> str:
        return self.run("log", f"-{count}", "--oneline", "--no-decorate").output

    def is_dirty(self) -> bool:
        return bool(self.status())

    def reset_hard(self) -> GitResult:
        result = self.run("reset", "--hard", "-q")
        self.run("clean", "-fdq", "-e", "*.pyc")
        return result

    def stage_all(self) -> GitResult:
        return self.run("add", "-A")

    def unstage(self) -> GitResult:
        return self.run("reset", "-q")

    def diff_cached(self, context: int = 3) -> str:
        return self.run("diff", "--cached", f"-U{context}", "--no-color").stdout

    def diff(self, context: int = 3, paths: Optional[List[str]] = None) -> str:
        args = ["diff", f"-U{context}", "--no-color"]
        if paths:
            args += ["--", *paths]
        return self.run(*args).stdout

    def apply_patch(self, patch_text: str, three_way: bool = True) -> GitResult:
        """Apply a unified diff, falling back through 3-way / lenient modes.

        The patch is passed as raw bytes on purpose: text mode would rewrite every
        "\n" as "\r\n" on Windows, and git would then search for CR-terminated
        context lines that the LF worktree does not contain.
        """
        if not patch_text.strip():
            return GitResult(0, "", "empty patch")
        attempts: List[Tuple[str, ...]] = [("apply", "--whitespace=nowarn", "-")]
        if three_way:
            attempts.append(("apply", "-3", "--whitespace=nowarn", "-"))
        attempts.append(("apply", "--reject", "--whitespace=nowarn", "-"))
        last = GitResult(0, "", "")
        for args in attempts:
            last = self._run_bytes(list(args), patch_text.encode("utf-8"))
            if last.ok:
                return last
        return last

    def _run_bytes(self, args: List[str], payload: bytes) -> GitResult:
        cmd = ["git", "-C", str(self.root), *_git_config_args(), *args]
        try:
            proc = subprocess.run(cmd, input=payload, capture_output=True, timeout=self.timeout)
        except FileNotFoundError:
            return GitResult(127, "", "git executable not found on PATH")
        except subprocess.TimeoutExpired:
            return GitResult(124, "", f"git {' '.join(args)} timed out")
        return GitResult(
            proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"),
        )

    def apply_patch_fallback_program(self, patch_text: str) -> Optional[GitResult]:
        """Use GNU `patch` when git refuses (common for truncated diffs)."""
        if shutil.which("patch") is None:
            return None
        try:
            proc = subprocess.run(
                ["patch", "-p1", "-N", "--fuzz=3", "--reject-file=-"],
                cwd=str(self.root),
                input=patch_text.encode("utf-8"),
                capture_output=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return GitResult(124, "", "patch timed out")
        return GitResult(
            proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"),
        )


class SnapshotStore:
    """Extract-once cache of `*.tgz` repository snapshots."""

    def __init__(self, cache_dir: Path, keep_extracted: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.keep_extracted = keep_extracted

    def cache_key(self, archive: Path) -> Path:
        stat = archive.stat()
        return self.cache_dir / f"{archive.stem}-{stat.st_size}-{int(stat.st_mtime)}"

    def has(self, archive: Path) -> bool:
        key = self.cache_key(archive)
        return (key / ".extracted").is_file()

    def ensure(self, archive: Path) -> Path:
        """Return a ready-to-use git working tree for `archive` (cached)."""
        archive = Path(archive).resolve()
        key = self.cache_key(archive)
        marker = key / ".extracted"
        if marker.is_file():
            repo = GitRepo(key)
            if repo.is_repo():
                return key
            marker.unlink(missing_ok=True)
            shutil.rmtree(key, ignore_errors=True)

        shutil.rmtree(key, ignore_errors=True)
        key.mkdir(parents=True, exist_ok=True)
        entries = safe_extract(archive, key)
        normalise_extracted_root(key)
        (key / ".extracted").write_text(
            f"archive={archive.name}\nsha256={file_sha256(archive)}\nentries={entries}\n",
            encoding="utf-8",
        )
        repo = GitRepo(key)
        if not repo.is_repo():
            repo.init()
        agent_logger.info(f"[BENCH] Extracted {archive.name} -> {key} ({entries} entries)")
        return key
