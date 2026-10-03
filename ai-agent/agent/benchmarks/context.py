"""Context assembly for the solver, plus the reference-solution leakage guard.

The solver sees: the issue text, the repository layout, ranked candidate files
(embeddings → lexical fallback), the code-graph neighbourhood of those symbols,
and the trimmed contents of the most relevant files. It never sees the gold
patch or the FAIL_TO_PASS ground truth — `assert_no_leakage` proves that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .code_graph import CodeGraph
from .embeddings import CodeSearch, SearchHit
from .workspace import TaskWorkspace

DEFAULT_BUDGET_CHARS = 24_000
MIN_FILE_CHARS = 400


@dataclass
class ContextBundle:
    """Everything the solver is allowed to see for one task."""

    text: str
    files: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    hits: List[SearchHit] = field(default_factory=list)
    graph_lines: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def char_count(self) -> int:
        return len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": self.files,
            "symbols": self.symbols[:20],
            "hits": [h.to_dict() for h in self.hits[:20]],
            "graph_lines": len(self.graph_lines),
            "chars": self.char_count(),
            "warnings": self.warnings,
        }


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    head = text[: limit // 2]
    tail = text[-limit // 2:]
    return f"{head}\n... [{len(text) - limit} chars elided] ...\n{tail}"


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def build_context(
    task: Any,
    workspace: TaskWorkspace,
    search: Optional[CodeSearch] = None,
    graph: Optional[CodeGraph] = None,
    query_vector: Optional[Sequence[float]] = None,
    max_files: int = 6,
    max_context_chars: int = DEFAULT_BUDGET_CHARS,
) -> ContextBundle:
    """Rank files with embeddings/graph, then pack a budgeted context string."""
    warnings: List[str] = []
    graph = graph if graph is not None else CodeGraph()
    search = search or CodeSearch.build(None, graph)

    hits = search.search(task.issue, limit=20, query_vector=query_vector)
    candidate_files: List[str] = list(search.files(task.issue, limit=max_files * 2))

    # Files named verbatim in the issue always rank first.
    for match in re.findall(r"[\w./-]+\.(?:py|pyi|txt|toml|md)", task.issue or ""):
        if workspace.exists(match) and match not in candidate_files:
            candidate_files.insert(0, match)

    graph_nodes: List[str] = []
    for hit in hits[:10]:
        node = graph.node(hit.node_id)
        if node and node.file and node.file not in candidate_files:
            candidate_files.append(node.file)
        if node:
            graph_nodes.append(node.id)

    header = [
        f"# Repository: {task.repo}",
        f"# Task id: {task.id}",
        "",
        "## Issue",
        task.issue.strip() or "(no issue text provided)",
        "",
        "## Repository layout",
        "\n".join(workspace.tree(max_depth=2)),
    ]

    structure = ["", "## Code intelligence"]
    if graph.loaded:
        structure.append(f"graph: {len(graph)} nodes across {len(graph.files())} files")
        structure.extend(graph.to_prompt_lines(graph_nodes, limit=40))
    else:
        structure.append("graph: not available for this repository")
    ranked = [f"- {h.node_id} (score {h.score:.3f}, {h.source})" for h in hits[:12]]
    if ranked:
        structure.append("ranked code nodes:")
        structure.extend(ranked)

    sections: List[str] = ["\n".join(header), "\n".join(structure)]
    used_chars = sum(len(s) for s in sections)

    selected: List[str] = []
    for file_path in candidate_files:
        if len(selected) >= max_files:
            break
        if not workspace.exists(file_path):
            continue
        try:
            content = workspace.read_text(file_path)
        except Exception as exc:  # unreadable file should not kill the run
            warnings.append(f"unreadable {file_path}: {exc}")
            continue
        if not content.strip():
            continue
        allow = max_context_chars - used_chars
        if allow < MIN_FILE_CHARS:
            warnings.append("context budget exhausted before reading more files")
            break
        body = _truncate(content, allow)
        sections.append(f"\n## File: {file_path}\n```\n{body}\n```")
        used_chars += len(body) + len(file_path) + 16
        selected.append(file_path)

    if not selected:
        warnings.append("no readable candidate files found in context")

    return ContextBundle(
        text="\n".join(sections),
        files=selected,
        symbols=graph_nodes,
        hits=hits,
        graph_lines=graph.to_prompt_lines(graph_nodes, limit=40),
        warnings=warnings,
    )


def leakage_signatures(task: Any) -> List[str]:
    """Distinctive fragments of the ground truth that must never appear in context."""
    signatures: List[str] = []
    gold = (task.gold_patch or "").strip()
    if gold:
        for line in gold.splitlines():
            stripped = line[1:].strip() if line[:1] in ("+", "-", " ") else line.strip()
            if len(stripped) >= 25:
                signatures.append(_collapse(stripped))
            if len(signatures) >= 12:
                break
    for test_id in list(task.fail_to_pass)[:12]:
        collapsed = _collapse(test_id)
        if len(collapsed) >= 6:
            signatures.append(collapsed)
    return signatures


def assert_no_leakage(bundle: ContextBundle, task: Any) -> List[str]:
    """Return a list of leakage violations (empty == clean). Proves the guard works."""
    haystack = _collapse(bundle.text)
    haystack += " " + " ".join(bundle.files)
    violations: List[str] = []
    for signature in leakage_signatures(task):
        if signature and signature in haystack:
            violations.append(signature[:80])
    if task.gold_patch and task.gold_patch.strip() in bundle.text:
        violations.append("raw gold patch embedded in context")
    return violations
