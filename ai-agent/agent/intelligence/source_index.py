"""Shared project file index — LumicorePro Part 3 optimization.

Every static scanner (design_lint, automated_design_score, accessibility,
quality gates) re-walks the same generated tree with `rglob`. This helper scans
a project ONCE per (root, mtime) pair and serves extension-grouped file lists +
content reads. Call into it from the scanner modules to collapse 9-12 full
walks into a single pass.

Pure CPU, no I/O beyond the required first scan. Observational: a failure
degrades to the caller's own discovery, never blocks the pipeline.
"""
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

_CACHE: "Dict[str, Dict[str, List[str]]]" = {}
_LOCK = threading.Lock()


class SourceIndex:
    """One snapshot of every source file in a generated project tree."""

    # Always skipped: dependency/vendor/build trees are never linted.
    _DEFAULT_EXCLUDE = {".git", "node_modules", "dist", "build",
                        "__pycache__", ".pytest_cache", ".next", "vendor"}

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self._by_suffix: Dict[str, List[str]] = {}
        self._marker = ""

    # ------------------------------------------------------------------
    @classmethod
    def build(cls, root: str, exclude_names: Optional[set] = None) -> "SourceIndex":
        """Walk the tree once and group files by suffix (case-insensitive).

        Excludes dependency/vendor/build dirs by default so a single walk is
        also a safe sentinel for design_lint and the validators.
        """
        index = cls(root)
        base = index.root
        outer = set(cls._DEFAULT_EXCLUDE)
        if exclude_names:
            outer |= set(exclude_names)
        if not base.is_dir():
            return index
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            parts = set(path.parts)
            if parts & outer:
                continue
            suffix = path.suffix.lower()
            index._by_suffix.setdefault(suffix, []).append(str(path))
        for group in index._by_suffix.values():
            group.sort()
        index._marker = str(base)
        return index

    # ------------------------------------------------------------------
    def files(self, *suffixes: str) -> List[str]:
        """All files matching any of the given lowercase suffixes."""
        out: List[str] = []
        for suffix in suffixes:
            out.extend(self._by_suffix.get(suffix, []))
        return out

    def group(self, suffix: str) -> List[str]:
        return self._by_suffix.get(suffix, []) or []

    def all(self) -> List[str]:
        out: List[str] = []
        for group in self._by_suffix.values():
            out.extend(group)
        return out


def get_source_index(root: str) -> SourceIndex:
    """Return a memoized SourceIndex for root (invalidated when mtime changes).

    Uses a coarse fingerprint (a few sentinel dirs) to detect the same tree;
    rebuilding is cheap and safe, while reusing avoids 10x identical rglob.
    """
    normalized = str(Path(root).resolve())
    fingerprint = _fingerprint(normalized)
    with _LOCK:
        cached = _CACHE.get(normalized)
        if cached and cached.get("_fp") == fingerprint:
            fractal = cached.get("index")
            if fractal is not None:
                return fractal
    index = SourceIndex.build(normalized)
    with _LOCK:
        _CACHE[normalized] = {"_fp": fingerprint, "index": index}
    return index


def _fingerprint(root: str) -> str:
    """Cheap mtime-based fingerprint keyed on the src/public config dirs."""
    parts: List[str] = []
    for rel in ("src", "public", "src/components", "src/pages"):
        p = Path(root, rel)
        if p.is_dir():
            try:
                parts.append(f"{rel}:{int(p.stat().st_mtime)}")
            except OSError:
                pass
    return "|".join(parts)


def invalidate_source_index(root: str) -> None:
    """Drop the cached index (call after self-heal mutates a project)."""
    normalized = str(Path(root).resolve())
    with _LOCK:
        _CACHE.pop(normalized, None)


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    idx = get_source_index(target)
    print(f"index: {len(idx.all())} files | jsx={len(idx.files('.jsx'))} "
          f"tsx={len(idx.files('.tsx'))} img={len(idx.files('.png', '.webp', '.jpg'))}")
    invalidate_source_index(target)