"""Per-task working tree: file IO, patch application, and diff capture.

Each benchmark task gets its own disposable git checkout. The agent edits files
directly (or applies a diff); the harness then captures the exact candidate patch
with `git diff --cached` so untracked new files are included.
"""

from __future__ import annotations

import os
import shutil
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import agent_logger

from .snapshots import GitRepo, GitResult, SnapshotStore

MAX_READ_BYTES = 200_000
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".venv", "venv", "env", "dist", "build", ".eggs",
}
VENV_PYTHONS = (
    ".venv/Scripts/python.exe", ".venv/bin/python",
    "venv/Scripts/python.exe", "venv/bin/python",
    "env/Scripts/python.exe", "env/bin/python",
)


class WorkspaceError(RuntimeError):
    """Raised when a workspace operation cannot be completed safely."""


@dataclass
class TaskWorkspace:
    """Disposable checkout for one task."""

    root: Path
    git: GitRepo
    reused: bool = False
    touched: List[str] = field(default_factory=list)

    # ── construction ─────────────────────────────────────────────────────────
    @classmethod
    def open(cls, root: Path, reused: bool = False) -> "TaskWorkspace":
        root = Path(root).resolve()
        if not root.is_dir():
            raise WorkspaceError(f"workspace root missing: {root}")
        return cls(root=root, git=GitRepo(root), reused=reused)

    @property
    def python_exe(self) -> str:
        """Prefer the snapshot's own virtualenv interpreter when it has one."""
        for rel in VENV_PYTHONS:
            candidate = self.root / rel
            if candidate.is_file():
                return str(candidate)
        return ""

    def uses_own_env(self) -> bool:
        return bool(self.python_exe)

    # ── file IO ──────────────────────────────────────────────────────────────
    def _safe(self, rel_path: str) -> Path:
        candidate = (self.root / rel_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(f"path escapes workspace: {rel_path}") from exc
        return candidate

    def exists(self, rel_path: str) -> bool:
        try:
            return self._safe(rel_path).exists()
        except WorkspaceError:
            return False

    def read_text(self, rel_path: str, max_bytes: int = MAX_READ_BYTES) -> str:
        path = self._safe(rel_path)
        if not path.is_file():
            raise WorkspaceError(f"file not found: {rel_path}")
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")

    def write_text(self, rel_path: str, content: str) -> bool:
        path = self._safe(rel_path)
        if not path.parent.is_dir():
            raise WorkspaceError(f"directory missing for: {rel_path}")
        # newline="" keeps the bytes exactly as given: Path.write_text would
        # rewrite "\n" as "\r\n" on Windows and corrupt every generated diff.
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        return True

    def list_files(self, pattern: str = "*.py", limit: int = 5000) -> List[str]:
        results: List[str] = []
        for path in sorted(self.root.rglob(pattern)):
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            results.append(path.relative_to(self.root).as_posix())
            if len(results) >= limit:
                break
        return results

    def tree(self, max_depth: int = 2, limit: int = 160) -> List[str]:
        lines: List[str] = []
        root_depth = len(self.root.parts)
        for path in sorted(self.root.rglob("*")):
            rel = path.relative_to(self.root)
            if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
                continue
            if len(rel.parts) > max_depth:
                continue
            lines.append(rel.as_posix() + ("/" if path.is_dir() else ""))
            if len(lines) >= limit:
                break
        return lines

    # ── patching ─────────────────────────────────────────────────────────────
    def apply_patch(self, patch_text: str) -> GitResult:
        """Apply a unified diff, falling back to GNU `patch` for imperfect diffs."""
        if not patch_text or not patch_text.strip():
            return GitResult(0, "", "empty patch")
        result = self.git.apply_patch(patch_text)
        if result.ok:
            self._record_changed()
            return result
        fallback = self.git.apply_patch_fallback_program(patch_text)
        if fallback is not None and fallback.ok:
            self._record_changed()
            return fallback
        return result

    def _record_changed(self) -> None:
        for line in self.git.status().splitlines():
            if len(line) > 3:
                self.touched.append(line[3:].strip().strip('"'))

    def capture_patch(self, context: int = 3) -> str:
        """Full candidate diff including untracked files, leaving the tree unstaged."""
        self.git.stage_all()
        patch = self.git.diff_cached(context=context)
        self.git.unstage()
        return patch

    def reset(self) -> None:
        self.git.reset_hard()
        self.touched.clear()

    def restore_from(self, source: Path) -> None:
        """Re-materialise the workspace from a pristine copy (used between attempts)."""
        source = Path(source).resolve()
        if source == self.root:
            self.reset()
            return
        if self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)
        shutil.copytree(source, self.root, symlinks=False)

    def summary(self) -> Dict[str, object]:
        return {
            "root": str(self.root),
            "head": self.git.head()[:12],
            "dirty": self.git.is_dirty(),
            "own_env": self.uses_own_env(),
            "touched": sorted(set(self.touched))[:20],
        }


class WorkspaceManager:
    """Creates per-task checkouts from the read-only snapshot cache."""

    def __init__(self, cache_dir: Path, workspaces_dir: Path, reuse_cache: bool = False):
        self.store = SnapshotStore(cache_dir)
        self.workspaces_dir = Path(workspaces_dir)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        self.reuse_cache = reuse_cache
        self._count = 0

    def create(self, task_id: str, archive: Path) -> TaskWorkspace:
        pristine = self.store.ensure(archive)
        if self.reuse_cache:
            ws = TaskWorkspace.open(pristine, reused=True)
            ws.reset()
            return ws
        self._count += 1
        target = self.workspaces_dir / f"{self._count:04d}-{_safe_name(task_id)}"
        if target.exists():
            force_rmtree(target)
        shutil.copytree(pristine, target, symlinks=False)
        return TaskWorkspace.open(target, reused=False)

    def discard(self, ws: TaskWorkspace) -> None:
        # Only workspaces we copied out under `workspaces_dir` may be deleted; a
        # `reuse_cache` workspace lives inside the pristine cache and must survive.
        if ws.root.exists() and ws.root.parent == self.workspaces_dir:
            force_rmtree(ws.root)

    def cleanup(self) -> int:
        removed = 0
        if not self.workspaces_dir.exists():
            return 0
        for child in self.workspaces_dir.iterdir():
            if child.is_dir():
                force_rmtree(child)
                removed += 1
        agent_logger.info(f"[BENCH] Removed {removed} workspace(s) from {self.workspaces_dir}")
        return removed


def force_rmtree(path: Path) -> None:
    """rmtree that survives read-only git objects and locked files.

    `shutil.rmtree(..., ignore_errors=True)` would silently leave a partially
    deleted tree behind, and the next `copytree` then fails with WinError 183.
    """
    path = Path(path)
    if not path.exists():
        return
    if path.is_file():
        _unlock(path)
        path.unlink(missing_ok=True)
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            _unlock(Path(root) / name)
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():  # last resort: Windows handle still open
        time.sleep(0.05)
        shutil.rmtree(path, ignore_errors=True)


def _unlock(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass


def _safe_name(value: str) -> str:
    import re

    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-")
    return (slug or "task")[:80]
