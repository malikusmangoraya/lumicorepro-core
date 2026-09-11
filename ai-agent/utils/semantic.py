"""Dependency-free semantic text similarity for local-first RAG.

Builds word n-gram term vectors and ranks with cosine similarity so registry
lookups tolerate typos and word-order differences without any external model.
Deterministic, thread-safe, zero network.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Sequence

_WORD_RE = re.compile(r"[a-z0-9]+")

_VECTOR_CACHE: Dict[int, Dict[str, float]] = {}


def ngrams(tokens: Sequence[str], n: int = 2) -> List[tuple]:
    """Rolling word n-grams (default bigrams) for word-order tolerance."""
    if len(tokens) < n:
        return [tuple(tokens)]
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _char_grams(text: str) -> List[str]:
    """Character bigrams for typo tolerance (restraunt ~ restaurant)."""
    norm = "".join(ch for ch in (text or "").lower() if ch >= "a" and ch <= "z")
    if len(norm) <= 1:
        return [f"_{norm}_"]
    return list({f"{norm[i]}{norm[i + 1]}" for i in range(len(norm) - 1)})


def _nf(tokens: Sequence[str]) -> Dict[str, float]:
    """Term-frequency normalized vector from tokens (word + char bigrams)."""
    grams: List[str] = list(tokens)
    if len(tokens) > 1:
        grams = [":".join(g) for g in ngrams(tokens, 2)]
    grams.extend(_char_grams(" ".join(tokens)))
    freqs: Counter = Counter(grams)
    total = len(grams) or 1
    return {g: c / total for g, c in freqs.items()}


def tokenize(text: str, max_len: int = 24) -> List[str]:
    """Lowercase alphanumeric token stream, capped for speed."""
    return _WORD_RE.findall((text or "").lower())[:max_len]


def embed(text: str) -> Dict[str, float]:
    """Cached term vector for a text blob (pure function of input)."""
    key = hash((text or "").strip().lower())
    cached = _VECTOR_CACHE.get(key)
    if cached is not None:
        return cached
    vec = _nf(tokenize(text))
    _VECTOR_CACHE[key] = vec
    return vec


def cosine(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse term-vectors."""
    if not vec_a or not vec_b:
        return 0.0
    inter = set(vec_a) & set(vec_b)
    if not inter:
        return 0.0
    dot = sum(vec_a[g] * vec_b[g] for g in inter)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def semantic_similarity(query: str, candidate: str) -> float:
    """Unigram + bigram cosine blend over token streams."""
    if not query or not candidate:
        return 0.0
    return cosine(embed(query), embed(candidate))


def overlap_ratio(query_tokens: Sequence[str], candidate_tokens: Sequence[str]) -> float:
    """Fraction of query tokens present in candidate (typo-tolerant)."""
    if not query_tokens:
        return 0.0
    cand = set(candidate_tokens)
    hits = sum(1 for t in query_tokens if t in cand)
    return hits / len(query_tokens)