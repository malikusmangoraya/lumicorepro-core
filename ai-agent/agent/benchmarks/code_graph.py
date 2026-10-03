"""Loader + query layer for the prebuilt AST call / dependency graphs.

Graph files are per-repository JSON whose exact shape varies (Google's export,
a custom `nodes`/`edges` dump, or a file-keyed map). Everything is therefore
normalised through key probes, so the same query API works for any of them.

Queries used by the solver: locate a symbol, walk callers/callees, and compute
the impact set (transitive callers) that a bug fix is likely to touch.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from utils.logger import agent_logger

KEY_NODE_ID = ("id", "node_id", "key", "qualified_name", "qname", "symbol_id", "name", "symbol")
KEY_NODE_FILE = ("file", "file_path", "path", "module", "source", "filename", "location")
KEY_NODE_KIND = ("kind", "type", "category", "node_type", "class")
KEY_CALLS = ("calls", "callees", "outgoing", "imports", "depends_on", "dependencies", "references", "uses")
KEY_CALLERS = ("callers", "used_by", "referenced_by", "imported_by", "incoming", "dependents")
EDGE_SOURCE = ("from", "source", "src", "caller", "caller_id", "start")
EDGE_TARGET = ("to", "target", "dst", "callee", "callee_id", "end")

MAX_CTX_LINES = 60


def _first(record: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


def _as_str_list(value: Any) -> List[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(v) for v in value.keys()]
    if isinstance(value, (list, tuple, set)):
        out: List[str] = []
        for item in value:
            if isinstance(item, dict):
                name = _first(item, KEY_NODE_ID, "")
                if name:
                    out.append(str(name))
            elif item:
                out.append(str(item))
        return out
    return [str(value)]


@dataclass
class GraphNode:
    """A normalised code entity (function, class, module, file)."""

    id: str
    name: str = ""
    file: str = ""
    kind: str = ""
    calls: List[str] = field(default_factory=list)
    callers: List[str] = field(default_factory=list)
    line: int = 0

    @property
    def short_name(self) -> str:
        return (self.name or self.id).rsplit(".", 1)[-1]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file": self.file,
            "kind": self.kind,
            "line": self.line,
            "calls": self.calls,
            "callers": self.callers,
        }


class CodeGraph:
    """Queryable symbol graph for one repository snapshot."""

    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Set[Tuple[str, str]] = set()
        self.source: Optional[str] = None
        self.loaded = False

    # ── loading ──────────────────────────────────────────────────────────────
    @classmethod
    def load(cls, path: Optional[Path]) -> "CodeGraph":
        graph = cls()
        if not path:
            return graph
        path = Path(path)
        if not path.is_file():
            return graph
        try:
            if path.suffix == ".jsonl":
                payload: Any = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            else:
                payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            agent_logger.warning(f"[BENCH] Graph unreadable ({path.name}): {exc}")
            return graph
        graph._ingest(payload)
        graph._link()
        graph.loaded = bool(graph.nodes)
        graph.source = str(path)
        return graph

    def _ingest(self, payload: Any) -> None:
        nodes_raw: List[Any] = []
        edges_raw: List[Any] = []

        if isinstance(payload, dict):
            nodes_raw = payload.get("nodes") or payload.get("entities") or payload.get("symbols") or []
            edges_raw = payload.get("edges") or payload.get("links") or payload.get("relations") or []
            if not nodes_raw and not edges_raw:
                # file-keyed map: {"src/httpx/_client.py": [ {...}, {...} ]}
                for file_key, value in payload.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item = dict(item)
                                item.setdefault("file", file_key)
                                nodes_raw.append(item)
                    elif isinstance(value, dict):
                        for name, meta in value.items():
                            if isinstance(meta, dict):
                                node = dict(meta)
                                node.setdefault("name", name)
                                node.setdefault("file", file_key)
                                nodes_raw.append(node)
                            else:
                                nodes_raw.append({"id": name, "name": name, "file": file_key})
        elif isinstance(payload, list):
            nodes_raw = [p for p in payload if isinstance(p, dict)]
            edges_raw = [p for p in payload if isinstance(p, (list, tuple))]

        for item in nodes_raw:
            if not isinstance(item, dict):
                continue
            node_id = str(_first(item, KEY_NODE_ID, "") or "").strip()
            if not node_id:
                continue
            self.nodes[node_id] = GraphNode(
                id=node_id,
                name=str(_first(item, ("name", "symbol", "short_name"), node_id) or node_id),
                file=str(_first(item, KEY_NODE_FILE, "") or ""),
                kind=str(_first(item, KEY_NODE_KIND, "") or ""),
                line=int(item.get("line") or item.get("lineno") or 0 or 0),
                calls=_as_str_list(_first(item, KEY_CALLS, [])),
                callers=_as_str_list(_first(item, KEY_CALLERS, [])),
            )

        for item in edges_raw:
            source = target = None
            if isinstance(item, dict):
                source = _first(item, EDGE_SOURCE)
                target = _first(item, EDGE_TARGET)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                source, target = item[0], item[1]
            if source and target:
                self.edges.add((str(source), str(target)))

    def _link(self) -> None:
        """Symmetrise edges and per-node call/caller lists into one adjacency."""
        for source, target in list(self.edges):
            self.nodes.setdefault(source, GraphNode(id=source, name=source))
            self.nodes.setdefault(target, GraphNode(id=target, name=target))
            if target not in self.nodes[source].calls:
                self.nodes[source].calls.append(target)
            if source not in self.nodes[target].callers:
                self.nodes[target].callers.append(source)
        for node in self.nodes.values():
            for callee in node.calls:
                self.nodes.setdefault(callee, GraphNode(id=callee, name=callee))
                if node.id not in self.nodes[callee].callers:
                    self.nodes[callee].callers.append(node.id)
                self.edges.add((node.id, callee))

    # ── queries ──────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self.nodes)

    def files(self) -> List[str]:
        return sorted({n.file for n in self.nodes.values() if n.file})

    def find(self, name: str, exact: bool = False) -> List[GraphNode]:
        if not name:
            return []
        hits = [n for n in self.nodes.values() if n.id == name or n.name == name]
        if hits or exact:
            return hits
        pattern = re.compile(rf"(^|[.:]){re.escape(name)}$")
        return [n for n in self.nodes.values() if pattern.search(n.id) or pattern.search(n.name)]

    def node(self, node_id: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id)

    def callers(self, node_id: str, max_depth: int = 1) -> List[GraphNode]:
        seen: Set[str] = set()
        frontier = [node_id]
        for _ in range(max_depth):
            nxt: List[str] = []
            for current in frontier:
                node = self.nodes.get(current)
                if not node:
                    continue
                for caller in node.callers:
                    if caller not in seen:
                        seen.add(caller)
                        nxt.append(caller)
            frontier = nxt
        return [self.nodes[n] for n in seen if n in self.nodes]

    def callees(self, node_id: str, max_depth: int = 1) -> List[GraphNode]:
        seen: Set[str] = set()
        frontier = [node_id]
        for _ in range(max_depth):
            nxt: List[str] = []
            for current in frontier:
                node = self.nodes.get(current)
                if not node:
                    continue
                for callee in node.calls:
                    if callee not in seen:
                        seen.add(callee)
                        nxt.append(callee)
            frontier = nxt
        return [self.nodes[n] for n in seen if n in self.nodes]

    def nodes_in_file(self, file: str) -> List[GraphNode]:
        target = file.replace("\\", "/")
        return [n for n in self.nodes.values() if n.file.replace("\\", "/") == target]

    def impact_set(self, node_id: str, max_depth: int = 2) -> List[GraphNode]:
        """Transitive callers — the files a fix to `node_id` can break."""
        return self.callers(node_id, max_depth=max_depth)

    def search_symbols(self, query: str, limit: int = 15) -> List[GraphNode]:
        """Rank symbols by token overlap with a free-text query."""
        tokens = {t for t in re.split(r"[^A-Za-z0-9_]+", query.lower()) if len(t) > 2}
        if not tokens:
            return []
        scored: List[Tuple[int, GraphNode]] = []
        for node in self.nodes.values():
            haystack = f"{node.id} {node.name} {node.file}".lower()
            score = sum(haystack.count(token) for token in tokens)
            if score:
                scored.append((score, node))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [node for _, node in scored[:limit]]

    def to_prompt_lines(self, node_ids: Iterable[str], limit: int = MAX_CTX_LINES) -> List[str]:
        """Compact, token-cheap structural context for the solver prompt."""
        lines: List[str] = []
        for node_id in list(dict.fromkeys(node_ids))[:limit]:
            node = self.nodes.get(node_id)
            if not node:
                continue
            location = f"{node.file}:{node.line}" if node.line else (node.file or "?")
            callees = ", ".join(c.rsplit(".", 1)[-1] for c in node.calls[:4])
            callers = ", ".join(c.rsplit(".", 1)[-1] for c in node.callers[:4])
            kind = f" [{node.kind}]" if node.kind else ""
            lines.append(f"- {node.name or node.id}{kind} @ {location}")
            if callers:
                lines.append(f"  called by: {callers}")
            if callees:
                lines.append(f"  calls: {callees}")
        return lines

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loaded": self.loaded,
            "source": self.source,
            "nodes": len(self.nodes),
            "files": len(self.files()),
            "edges": len(self.edges),
        }
