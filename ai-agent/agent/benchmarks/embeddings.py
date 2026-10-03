"""Node embeddings + a dependency-free lexical fallback for code search.

Priority: use the dataset's prebuilt vectors when present; otherwise fall back to
a BM25-style lexical index so semantic search is never silently missing.

Supported vector formats (all optional, auto-detected):
  * `embeddings.npy` / `embeddings.npz`  — needs numpy; ids come from a sibling
    `ids.json` / `nodes.json`, or from the graph when only vectors are supplied
  * `embeddings.json` — `{"ids": [...], "vectors": [[...]]}` or `{id: [floats]}`
  * `nodes.json`      — `{"ids": [...], "embeddings": [...]}`

If numpy is unavailable for a binary format the loader reports
`status="numpy_missing"` and the caller degrades to lexical search instead of
failing the benchmark run.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils.logger import agent_logger

try:  # optional — only needed for .npy / .npz vectors
    import numpy as _np
except Exception:  # pragma: no cover - depends on install profile
    _np = None  # type: ignore[assignment]

KEY_IDS = ("ids", "node_ids", "keys", "symbols", "names")
KEY_VECTORS = ("vectors", "embeddings", "data", "matrix")
MAX_DIM_CONTEXT = 0  # vectors are never inlined into prompts


@dataclass
class SearchHit:
    node_id: str
    score: float
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "score": round(float(self.score), 4), "source": self.source}


@dataclass
class NodeEmbeddings:
    """Dense vectors for code nodes, plus optional lexical text per node."""

    ids: List[str] = field(default_factory=list)
    vectors: List[List[float]] = field(default_factory=list)
    text: Dict[str, str] = field(default_factory=dict)
    status: str = "not_loaded"
    source: Optional[str] = None
    backend: str = "none"

    def __len__(self) -> int:
        return len(self.ids)

    @property
    def dim(self) -> int:
        return len(self.vectors[0]) if self.vectors else 0

    @property
    def available(self) -> bool:
        return bool(self.ids and self.vectors and self.dim)

    # ── loading ──────────────────────────────────────────────────────────────
    @classmethod
    def load(
        cls,
        path: Optional[Path],
        text_by_id: Optional[Dict[str, str]] = None,
    ) -> "NodeEmbeddings":
        index = cls(text=dict(text_by_id or {}))
        if not path:
            return index
        path = Path(path)
        if not path.is_file():
            return index
        index.source = str(path)
        try:
            if path.suffix in (".npy", ".npz"):
                index._load_binary(path)
            else:
                index._load_json(path)
        except Exception as exc:
            index.status = f"error: {exc}"
            agent_logger.warning(f"[BENCH] Embeddings unreadable ({path.name}): {exc}")
        if not index.status.startswith("error") and not index.available:
            index.status = "degraded"
        return index

    def _load_json(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        ids: List[str] = []
        vectors: List[List[float]] = []

        if isinstance(payload, dict):
            raw_ids = next((payload[k] for k in KEY_IDS if isinstance(payload.get(k), list)), None)
            raw_vecs = next((payload[k] for k in KEY_VECTORS if isinstance(payload.get(k), list)), None)
            if raw_ids and raw_vecs:
                ids = [str(i) for i in raw_ids]
                vectors = [[float(x) for x in vec] for vec in raw_vecs]
            elif payload and all(isinstance(v, (list, tuple)) for v in payload.values()):
                ids = [str(k) for k in payload.keys()]
                vectors = [[float(x) for x in v] for v in payload.values()]
        elif isinstance(payload, list):
            rows = [r for r in payload if isinstance(r, (list, tuple))]
            if rows:
                vectors = [[float(x) for x in row] for row in rows]
                ids = [str(i) for i in range(len(vectors))]

        if ids and vectors and len(ids) == len(vectors):
            self.ids, self.vectors = ids, vectors
            self.backend = "json"
            self.status = "ok"
        else:
            self.status = "degraded"

    def _load_binary(self, path: Path) -> None:
        if _np is None:
            self.status = "numpy_missing"
            return
        if path.suffix == ".npy":
            matrix = _np.load(str(path), allow_pickle=False)
        else:
            with _np.load(str(path), allow_pickle=False) as data:
                keys = list(data.keys())
                matrix = data[KEY_VECTORS[0]] if KEY_VECTORS[0] in keys else data[keys[0]]
        matrix = _np.atleast_2d(matrix)
        self.vectors = [[float(x) for x in row] for row in matrix]
        self.ids = self._load_sibling_ids(path, len(self.vectors))
        self.backend = "numpy"
        self.status = "ok"

    def _load_sibling_ids(self, path: Path, count: int) -> List[str]:
        sibling = path.parent / "ids.json"
        if not sibling.is_file():
            sibling = path.parent / "nodes.json"
        if sibling.is_file():
            try:
                payload = json.loads(sibling.read_text(encoding="utf-8", errors="replace"))
                if isinstance(payload, list):
                    return [str(i) for i in payload][:count]
                if isinstance(payload, dict):
                    raw = next((payload[k] for k in KEY_IDS if isinstance(payload.get(k), list)), None)
                    if raw:
                        return [str(i) for i in raw][:count]
            except Exception:
                pass
        return [str(i) for i in range(count)]

    # ── search ───────────────────────────────────────────────────────────────
    def search(self, query_vector: Optional[Sequence[float]], limit: int = 15) -> List[SearchHit]:
        if not self.available or not query_vector:
            return []
        dim = self.dim
        if len(query_vector) != dim:
            return []
        qnorm = math.sqrt(sum(float(x) * float(x) for x in query_vector)) or 1.0
        scored: List[Tuple[float, str]] = []
        for node_id, vector in zip(self.ids, self.vectors):
            dot = 0.0
            norm = 0.0
            for a, b in zip(query_vector, vector):
                dot += float(a) * float(b)
                norm += float(b) * float(b)
            denom = (math.sqrt(norm) or 1.0) * qnorm
            scored.append((dot / denom, node_id))
        scored.sort(reverse=True)
        return [SearchHit(node_id, score, self.backend) for score, node_id in scored[:limit] if score > 0]


class LexicalIndex:
    """BM25-ish lexical index over node ids / files — no dependencies, always available."""

    K1 = 1.5
    B = 0.75

    def __init__(self) -> None:
        self.docs: Dict[str, List[str]] = {}
        self.freqs: Dict[str, Counter] = {}
        self.lengths: Dict[str, int] = {}
        self.avg_length = 0.0

    @classmethod
    def from_text(cls, text_by_id: Dict[str, str]) -> "LexicalIndex":
        index = cls()
        for node_id, text in text_by_id.items():
            index.add(node_id, text)
        index.finalise()
        return index

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        parts = re.split(r"[^A-Za-z0-9_]+", str(text).lower())
        tokens: List[str] = []
        for part in parts:
            if len(part) < 2:
                continue
            tokens.append(part)
            if "_" in part:
                tokens.extend(p for p in part.split("_") if len(p) > 2)
        return tokens

    def add(self, node_id: str, text: str) -> None:
        tokens = self._tokenize(text)
        self.docs[node_id] = tokens
        self.freqs[node_id] = Counter(tokens)
        self.lengths[node_id] = len(tokens)

    def finalise(self) -> None:
        total = sum(self.lengths.values())
        self.avg_length = (total / len(self.lengths)) if self.lengths else 0.0

    def search(self, query: str, limit: int = 15) -> List[SearchHit]:
        if not self.docs:
            return []
        tokens = self._tokenize(query)
        if not tokens:
            return []
        n_docs = len(self.docs)
        df: Counter = Counter()
        for node_id in self.docs:
            for token in set(tokens):
                if token in self.freqs[node_id]:
                    df[token] += 1

        scored: List[Tuple[float, str]] = []
        for node_id, freq in self.freqs.items():
            length = self.lengths.get(node_id, 0) or 1
            score = 0.0
            for token in tokens:
                f = freq.get(token, 0)
                if not f:
                    continue
                idf = math.log(1 + (n_docs - df[token] + 0.5) / (df[token] + 0.5))
                denom = f + self.K1 * (1 - self.B + self.B * length / (self.avg_length or 1))
                score += idf * (f * (self.K1 + 1)) / (denom or 1)
            if score > 0:
                scored.append((score, node_id))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [SearchHit(node_id, score, "lexical") for score, node_id in scored[:limit]]


class CodeSearch:
    """Facade: dense vectors when available, lexical otherwise, graph-aware on top."""

    def __init__(
        self,
        embeddings: Optional[NodeEmbeddings] = None,
        lexical: Optional[LexicalIndex] = None,
        graph: Any = None,
    ):
        self.embeddings = embeddings or NodeEmbeddings()
        self.lexical = lexical or LexicalIndex()
        self.graph = graph

    @classmethod
    def build(cls, embedding_file: Optional[Path], graph: Any = None) -> "CodeSearch":
        text_by_id: Dict[str, str] = {}
        if graph is not None and getattr(graph, "nodes", None):
            for node in graph.nodes.values():
                text_by_id[node.id] = f"{node.id} {node.name} {node.file}"
        embeddings = NodeEmbeddings.load(embedding_file, text_by_id)
        lexical = LexicalIndex.from_text(text_by_id) if text_by_id else LexicalIndex()
        return cls(embeddings=embeddings, lexical=lexical, graph=graph)

    def status(self) -> Dict[str, Any]:
        return {
            "embeddings_available": self.embeddings.available,
            "embeddings_backend": self.embeddings.backend,
            "embeddings_status": self.embeddings.status,
            "embeddings_count": len(self.embeddings),
            "lexical_docs": len(self.lexical.docs),
            "graph_loaded": bool(getattr(self.graph, "loaded", False)),
        }

    def search(
        self,
        query: str,
        limit: int = 15,
        query_vector: Optional[Sequence[float]] = None,
    ) -> List[SearchHit]:
        hits = self.embeddings.search(query_vector, limit=limit) if query_vector else []
        seen = {h.node_id for h in hits}
        for hit in self.lexical.search(query, limit=limit * 2):
            if hit.node_id not in seen:
                hits.append(hit)
                seen.add(hit.node_id)
        return hits[:limit]

    def files(self, query: str, limit: int = 8) -> List[str]:
        """Files most likely to hold the bug, ranked by lexical hits + graph symbols."""
        scores: Dict[str, float] = {}
        for hit in self.search(query, limit=limit * 6):
            node = self.graph.node(hit.node_id) if self.graph is not None else None
            file = node.file if node else (hit.node_id if "/" in hit.node_id or hit.node_id.endswith(".py") else "")
            if file:
                scores[file] = scores.get(file, 0.0) + hit.score
        ranked = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
        return [file for file, _ in ranked[:limit]]
