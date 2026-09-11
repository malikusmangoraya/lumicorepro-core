"""Surgical Search/Replace Block Parser
========================================
Applies token-efficient search/replace edits to VFS files.
This is the format used by Claude Artifacts / Aider — each block is:
    <<<<<<< SEARCH
    exact text to find
    =======
    replacement text
    >>>>>>> REPLACE

Supports:
  - Multi-file batch edits
  - Multiple blocks per file
  - Undo/redo via snapshot stack
  - Line-number-anchored search for precision
  - Fuzzy matching (whitespace-tolerant) when exact match fails
"""
import re
import copy
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

from utils.logger import agent_logger


class SearchReplaceError(Exception):
    """Raised when a search/replace block cannot be applied."""
    pass


@dataclass
class ReplaceBlock:
    file_path: str
    search: str
    replace: str
    line_start: Optional[int] = None
    applied: bool = False


@dataclass
class EditResult:
    applied_files: List[str] = field(default_factory=list)
    total_blocks: int = 0
    applied_blocks: int = 0
    errors: List[str] = field(default_factory=list)
    undo_token: Optional[str] = None


class SearchReplaceEngine:
    """Applies surgical search/replace blocks to an in-memory file snapshot."""

    BLOCK_PATTERN = re.compile(
        r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE",
        re.DOTALL,
    )
    FILE_HEADER = re.compile(r"^{40}\s+(.+?)\s+{40}$", re.MULTILINE)

    def __init__(self, files: Dict[str, str]):
        """Initialize with a dict of {path: contents}."""
        self._files = dict(files)
        self._undo_stack: List[Dict[str, str]] = []
        self._redo_stack: List[Dict[str, str]] = []
        self._max_undo = 30

    @property
    def files(self) -> Dict[str, str]:
        return self._files

    def apply_edit(self, edit_text: str) -> EditResult:
        """Parse and apply a multi-file search/replace edit.

        Format supports either:
        A) File-header-scoped blocks:
            <<<<<<< path/to/file.jsx
            <<<<<<< SEARCH
            ...
            =======
            ...
            >>>>>>> REPLACE
            >>>>>>> path/to/file.jsx

        B) Standalone blocks (applied to all files in search):
            <<<<<<< SEARCH
            ...
            =======
            ...
            >>>>>>> REPLACE
        """
        self._push_undo()
        result = EditResult()
        blocks = self._parse_blocks(edit_text)
        result.total_blocks = len(blocks)

        for block in blocks:
            try:
                self._apply_block(block)
                block.applied = True
                result.applied_blocks += 1
                if block.file_path not in result.applied_files:
                    result.applied_files.append(block.file_path)
            except SearchReplaceError as exc:
                result.errors.append(f"{block.file_path}: {exc}")

        result.undo_token = str(len(self._undo_stack))
        agent_logger.info(
            f"Search/Replace: {result.applied_blocks}/{result.total_blocks} blocks "
            f"across {len(result.applied_files)} files"
        )
        return result

    def undo(self) -> bool:
        """Undo the last edit batch."""
        if not self._undo_stack:
            return False
        self._redo_stack.append(dict(self._files))
        self._files = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        """Redo the last undone edit."""
        if not self._redo_stack:
            return False
        self._undo_stack.append(dict(self._files))
        self._files = self._redo_stack.pop()
        return True

    def _push_undo(self) -> None:
        """Save current state for undo."""
        self._undo_stack.append(dict(self._files))
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _parse_blocks(self, edit_text: str) -> List[ReplaceBlock]:
        """Extract all search/replace blocks from edit text."""
        blocks: List[ReplaceBlock] = []
        # Check for file-scoped blocks
        file_scope = re.findall(r"<<<<<<<\s+(\S+)\s*\n(.*?)\n>>>>>>>\s+\1", edit_text, re.DOTALL)
        if file_scope:
            for file_path, block_text in file_scope:
                for match in self.BLOCK_PATTERN.finditer(block_text):
                    search = match.group(1).strip("\n")
                    replace = match.group(2).strip("\n")
                    blocks.append(ReplaceBlock(file_path=file_path, search=search, replace=replace))
        else:
            # Standalone blocks — find them and search across all files
            for match in self.BLOCK_PATTERN.finditer(edit_text):
                search = match.group(1).strip("\n")
                replace = match.group(2).strip("\n")
                # Search for which file contains this text
                target_file = self._find_file_containing(search)
                if target_file:
                    blocks.append(ReplaceBlock(file_path=target_file, search=search, replace=replace))
                else:
                    blocks.append(ReplaceBlock(file_path="<unknown>", search=search, replace=replace))
        return blocks

    def _find_file_containing(self, search_text: str) -> Optional[str]:
        """Find the file containing the search text."""
        for path, content in self._files.items():
            if search_text in content:
                return path
        return None

    def _apply_block(self, block: ReplaceBlock) -> None:
        """Apply a single search/replace block to the target file."""
        if block.file_path not in self._files:
            raise SearchReplaceError(f"File not found: {block.file_path}")

        content = self._files[block.file_path]
        search = block.search

        if search in content:
            # Exact match
            count = content.count(search)
            if count > 1:
                agent_logger.warning(f"Ambiguous search in {block.file_path}: {count} matches (using first)")
            self._files[block.file_path] = content.replace(search, block.replace, 1)
            return

        # Fuzzy match: strip trailing whitespace per line, normalize blank lines
        normalized_search = self._normalize(search)
        normalized_content = self._normalize(content)
        if normalized_search in normalized_content:
            # Find the actual lines and replace
            self._fuzzy_replace(block.file_path, search, block.replace)
            return

        # Line-number anchored search
        if block.line_start:
            self._line_anchored_replace(block.file_path, block.line_start, block.search, block.replace)
            return

        raise SearchReplaceError(f"Search text not found in {block.file_path}")

    def _normalize(self, text: str) -> str:
        """Normalize whitespace for fuzzy matching."""
        lines = text.split("\n")
        normalized = []
        for line in lines:
            stripped = line.rstrip()
            if stripped:
                normalized.append(stripped)
        return "\n".join(normalized)

    def _fuzzy_replace(self, file_path: str, search: str, replace: str) -> None:
        """Fuzzy replace matching normalized lines."""
        content = self._files[file_path]
        content_lines = content.split("\n")
        search_lines = [l.rstrip() for l in search.split("\n") if l.strip()]

        for i in range(len(content_lines) - len(search_lines) + 1):
            match = True
            for j, s_line in enumerate(search_lines):
                if content_lines[i + j].rstrip() != s_line:
                    match = False
                    break
            if match:
                replace_lines = replace.split("\n")
                content_lines[i:i + len(search_lines)] = replace_lines
                self._files[file_path] = "\n".join(content_lines)
                return

    def _line_anchored_replace(self, file_path: str, line_start: int, search: str, replace: str) -> None:
        """Replace text anchored at a specific line number."""
        content = self._files[file_path]
        lines = content.split("\n")
        search_lines = search.strip().split("\n")
        start_idx = max(0, line_start - 1)

        if start_idx + len(search_lines) > len(lines):
            raise SearchReplaceError(f"Line range out of bounds in {file_path}")

        match = all(
            lines[start_idx + j].rstrip() == search_lines[j].rstrip()
            for j in range(len(search_lines))
        )
        if not match:
            raise SearchReplaceError(f"Line anchor mismatch at line {line_start} in {block.file_path}")

        replace_lines = replace.split("\n")
        lines[start_idx:start_idx + len(search_lines)] = replace_lines
        self._files[file_path] = "\n".join(lines)

    def to_vfs_snapshot(self) -> Dict[str, str]:
        """Return the current file state as a VFS-compatible snapshot."""
        return dict(self._files)


def apply_search_replace(
    files: Dict[str, str],
    edit_text: str,
) -> Tuple[Dict[str, str], EditResult]:
    """Convenience function: apply search/replace edits to files and return new state."""
    engine = SearchReplaceEngine(files)
    result = engine.apply_edit(edit_text)
    return engine.files, result


def undo_last_edit(engine: SearchReplaceEngine) -> bool:
    """Undo the last edit batch on an existing engine."""
    return engine.undo()


def redo_edit(engine: SearchReplaceEngine) -> bool:
    """Redo the last undone edit."""
    return engine.redo()
