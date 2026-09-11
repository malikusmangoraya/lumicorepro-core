"""
Virtual File System (VFS) & Unified-Diff AST Patching
=====================================================
Frees the agent from the 3-call / 10-file text-replace limit:

  1. An in-memory snapshot of a generated project is built into a JSON tree
     (structure map) + content store, so the AI model only needs 1 request to
     see the whole project and return a *patch*, not N rewritten files.
  2. The model is asked to return pure git-style Unified Diff (or JSON
     structural changes). The local Python `apply_unified_diff` parser then
     injects/overwrites exact hunks across 50+ files safely.
  3. Safety: paths are pinned inside the project dir, security-pattern scans
     run on the added lines, and hunks are bounds-checked before any write.

Design: no full AST dependency (no esprima/babel needed in this Python host) â€”
a lightweight structural map + tight unified-diff machinery is enough and keeps
context windows small.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger

# Vendor/binary dirs we never load into memory.
VFS_VENDOR_DIRS = {
    "node_modules", "dist", "build", ".git", "venv", "__pycache__",
    ".pytest_cache", "coverage", ".history", ".next", "out",
}
VFS_TEXT_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".json", ".md",
    ".env", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".njk",
}
VFS_MAX_FILE_BYTES = 256 * 1024


class UnifiedDiffError(Exception):
    """Raised when a unified diff cannot be parsed or applied safely."""


def _posix(path: str) -> str:
    return path.replace("\\", "/")


class ProjectVFS:
    """In-memory snapshot + safe tree building for a generated project."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self._files: Dict[str, str] = {}
        self._changed: Dict[str, str] = {}

    # â”€â”€ Snapshot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def load(self) -> "ProjectVFS":
        for rel, absolute in self._discover():
            try:
                with open(absolute, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                self._files[rel] = content
                agent_logger.debug(f"VFS loaded: {rel} ({len(content.splitlines())} lines)")
            except OSError as exc:
                agent_logger.warning(f"VFS skip unreadable {rel}: {exc}")
        return self

    def _discover(self) -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = []
        root = Path(self.project_dir)
        if not root.is_dir():
            return result
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            parts = set(path.parts)
            if parts & VFS_VENDOR_DIRS:
                continue
            if path.stat().st_size > VFS_MAX_FILE_BYTES:
                continue
            if path.suffix.lower() in VFS_TEXT_EXTS or path.name == "package.json":
                rel = _posix(os.path.relpath(str(path), self.project_dir))
                result.append((rel, str(path)))
        return sorted(result)

    def files(self) -> List[str]:
        return sorted(self._files)

    def read(self, rel: str) -> Optional[str]:
        return self._files.get(_posix(rel))

    # â”€â”€ JSON tree / prompt context â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def tree(self, max_files: int = None) -> Dict[str, Any]:
        """Nested structure JSON tree: {dir: {dir: {...}, file: {lines: N}}}."""
        max_files = max_files or len(self._files)
        root: Dict[str, Any] = {}
        for rel in self.files()[:max_files]:
            parts = rel.split("/")
            node = root
            for seg in parts[:-1]:
                node = node.setdefault("dirs", {}).setdefault(seg, {})
            node.setdefault("files", {})[parts[-1]] = {
                "lines": self._files[rel].count("\n") + 1,
            }
        return root

    def to_prompt_context(self, max_files: int = 40, max_chars: int = 14000) -> str:
        """Compact structure map + selected file excerpts for the model prompt."""
        lines = ["PROJECT TREE (JSON):", json.dumps(self.tree(max_files=max_files), indent=1)[:6000]]
        sections = ["KEY FILE CONTENT (read+modify only where needed):"]
        budget = max_chars - 7000
        for rel in self.files()[:max_files]:
            content = self._files[rel]
            if len(content) > 3000:
                content = content[:3000] + f"\n// â€¦truncated {rel}"
            section = f"\n### FILE: {rel}\n```\n{content}\n```"
            budget -= len(section)
            if budget < 0:
                break
            sections.append(section)
        return "\n".join(lines) + "\n\n" + "\n".join(sections)

    # â”€â”€ Unified diff application â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def apply_unified_diff(self, diff_text: str) -> Dict[str, Any]:
        """Parse and apply a git-style unified diff across the snapshot.

        Returns {applied_files: [], hunks: N, errors: [message,...]}.
        Raises UnifiedDiffError only for structural parse failures.
        """
        result = {"applied_files": [], "hunks": 0, "errors": []}
        sections = self._split_diff_sections(diff_text)
        if not sections:
            raise UnifiedDiffError("No diff file sections found in model output.")

        for section in sections:
            new_path, old_path, body = section
            try:
                hunks = self._parse_hunks(body)
                current = self._apply_to_file_snapshot(
                    new_path or old_path,
                    new_path == "/dev/null",
                    hunks,
                    result,
                )
                if current is not None:
                    self._files[new_path or old_path] = current
            except UnifiedDiffError as exc:
                result["errors"].append(f"{new_path or old_path}: {exc}")
        return result

    def _split_diff_sections(self, diff_text: str) -> List[Tuple[Optional[str], Optional[str], str]]:
        """Split multi-file diff into (new_path, old_path, hunk_body) tuples."""
        sections: List[Tuple[Optional[str], Optional[str], str]] = []
        current_new = None
        current_old = None
        current_body: List[str] = []
        header_re = re.compile(r"^diff --git .*\ba/(\S+)\s+b/(\S+)")
        ot_re = re.compile(r"^--- (\S+)")
        nt_re = re.compile(r"^\+\+\+ (\S+)")

        for raw in diff_text.splitlines():
            line = raw.rstrip()
            ht = header_re.match(line)
            if ht:
                if current_new is not None and current_body:
                    sections.append((current_new, current_old, "\n".join(current_body)))
                current_new, current_old = ht.group(2), ht.group(1)
                current_body = []
                continue
            if current_new is None:
                prefix = ""
                if not re.match(r"^(@@|[-+ ]|diff |index |--- |\+\+\+ |new file|deleted|similarity|rename)", line):
                    continue
                m = ot_re.match(line)
                if m:
                    current_old = self._clean_path(m.group(1))
                    continue
                m = nt_re.match(line)
                if m:
                    current_new = self._clean_path(m.group(1))
                    continue
                if not line.strip():
                    continue
            current_body.append(line)
        if current_new is not None and current_body:
            sections.append((current_new, current_old, "\n".join(current_body)))
        return sections

    @staticmethod
    def _clean_path(value: str) -> str:
        value = value.strip().lstrip("\\/")
        for prefix in ("a/", "b/"):
            if value.startswith(prefix):
                return value[len(prefix):]
        return value

    def _parse_hunks(self, body: str) -> List[Dict[str, Any]]:
        hunks: List[Dict[str, Any]] = []
        for hunk in re.split(r"(?=^@@ )", body, flags=re.M):
            if not hunk.strip():
                continue
            scope_match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", hunk)
            if not scope_match:
                agent_logger.warning(f"VFS: malformed hunk ignored: {hunk[:120]}")
                continue
            old_pos = int(scope_match.group(1))
            new_pos = int(scope_match.group(2))
            ops: List[Tuple[str, str]] = []
            for line in hunk.splitlines():
                if line.startswith(("+", "-", " ")):
                    ops.append((line[0], line[1:]))
            hunks.append({"old_pos": old_pos, "new_pos": new_pos, "ops": ops})
        return hunks

    def _apply_to_file_snapshot(
        self,
        rel: str,
        is_new_file: bool,
        hunks: List[Dict[str, Any]],
        result: Dict[str, Any],
    ) -> Optional[str]:
        rel = _posix(rel)
        if is_new_file:
            original: List[str] = []
        else:
            original = (self._files.get(rel) or "").splitlines()
        if original is None:
            original = []

        # Apply hunks sequentially, carrying the running line-count delta so
        # later hunks (which reference positions in the ORIGINAL file) stay aligned.
        delta = 0
        for hunk in hunks:
            delta_shift = hunk["old_pos"] - 1 + delta
            updated = self._apply_hunk(original, delta_shift, hunk, rel)
            delta += len(updated) - len(original)
            original = updated
            result["hunks"] += 1

        new_text = "\n".join(original) + ("\n" if original and self._files.get(rel, "").endswith("\n") else "")
        if new_text != self._files.get(rel) or is_new_file:
            result["applied_files"].append(rel)
            self._changed[rel] = new_text
        return new_text

    def _apply_hunk(self, lines: List[str], start_idx: int, hunk: Dict[str, Any], rel: str) -> List[str]:
        idx = start_idx
        out = lines[:idx]
        rest = lines[idx:]
        region = list(hunk["ops"])
        consumed = 0
        for op, text in region:
            if op == " ":
                if consumed < len(rest) and rest[consumed] == text:
                    out.append(rest[consumed])
                    consumed += 1
                else:
                    hunk_ctx = "\n".join(f"{o}{t}" for o, t in region[:6])
                    raise UnifiedDiffError(
                        f"context/line mismatch at old line {start_idx + 1}:\n{hunk_ctx}"
                    )
            elif op == "-":
                if consumed < len(rest) and rest[consumed] == text:
                    consumed += 1
                else:
                    hunk_ctx = "\n".join(f"{o}{t}" for o, t in region[:6])
                    raise UnifiedDiffError(
                        f"deleted line mismatch at old line {start_idx + 1}:\n{hunk_ctx}"
                    )
            elif op == "+":
                # Emit additions inline, exactly where the -/+ block sits.
                out.append(text)
        out.extend(rest[consumed:])
        return out

# ── Persist ──────────────────────────────────────────────────────────────
    def persist(self) -> List[str]:
        """Atomically write changed files, pinned inside the project dir."""
        written: List[str] = []
        for rel, content in self._changed.items():
            safe = self._safe_rel_path(rel)
            abs_path = os.path.join(self.project_dir, safe)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            try:
                with open(abs_path, "w", encoding="utf-8") as fh:
                    fh.write(content)
                written.append(safe)
            except OSError as exc:
                agent_logger.error(f"VFS persist failed for {safe}: {exc}")
        self._changed = {}
        return written

    def _safe_rel_path(self, rel: str) -> str:
        rel = _posix(rel).lstrip("/\\")
        if ".." in rel.split("/"):
            raise UnifiedDiffError(f"Path traversal blocked: {rel}")
        return rel

    @classmethod
    def security_violations(cls, diff_text: str) -> List[str]:
        """Scan the added (+) lines of a diff for forbidden patterns."""
        from agent.code_modifier import CodeModifier
        added = "\n".join(l[1:] for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
        return CodeModifier.validate_code_security(added)
