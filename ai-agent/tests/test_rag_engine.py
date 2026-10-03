"""
Tests for RAG Engine - Retrieval-Augmented Generation.
Run with: pytest ai-agent/tests/test_rag_engine.py -v
"""

import sys, json, pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def rag_engine(tmp_path):
    mock_modules = {
        "chromadb": MagicMock(),
        "chromadb.config": MagicMock(),
        "sentence_transformers": MagicMock(),
    }
    with patch.dict("sys.modules", mock_modules):
        with patch("agent.rag_engine.CHROMADB_AVAILABLE", True):
            from agent.rag_engine import RAGEngine
            engine = RAGEngine(persist_dir=str(tmp_path / "rag_store"))
            engine.enabled = True
            engine.docs_collection = MagicMock()
            engine.code_collection = MagicMock()
            engine.examples_collection = MagicMock()
            engine.docs_collection.count.return_value = 0
            return engine


def _qr(docs, metas, dists=None, ids=None):
    n = len(docs)
    return {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [dists or [0.1] * n],
        "ids": [ids or [str(i) for i in range(n)]],
    }


# _generate_id
def test_generate_id_deterministic(rag_engine):
    assert rag_engine._generate_id("a") == rag_engine._generate_id("a")

def test_generate_id_unique(rag_engine):
    assert rag_engine._generate_id("a") != rag_engine._generate_id("b")

def test_generate_id_md5_length(rag_engine):
    assert len(rag_engine._generate_id("x")) == 32


# add_documentation
def test_add_doc_success(rag_engine):
    assert rag_engine.add_documentation("T", "C", {"cat": "react"}) is True
    kw = rag_engine.docs_collection.add.call_args[1]
    assert kw["metadatas"][0]["title"] == "T"

def test_add_doc_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.add_documentation("T", "C") is False

def test_add_doc_exception(rag_engine):
    rag_engine.docs_collection.add.side_effect = Exception("db")
    assert rag_engine.add_documentation("T", "C") is False


# add_code_snippet
def test_add_snippet_stores_code(rag_engine):
    rag_engine.add_code_snippet("X", "const x=1;", "javascript", "desc", ["tag"])
    kw = rag_engine.code_collection.add.call_args[1]
    assert kw["metadatas"][0]["code"] == "const x=1;"
    assert kw["metadatas"][0]["language"] == "javascript"

def test_add_snippet_minimal(rag_engine):
    assert rag_engine.add_code_snippet("M", "pass", "python") is True

def test_add_snippet_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.add_code_snippet("x", "y", "python") is False


# add_example_project
def test_add_example_success(rag_engine):
    assert rag_engine.add_example_project("S", "d", ["React"], {}, {}) is True

def test_add_example_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.add_example_project("X", "Y", [], {}) is False


# search_documentation
def test_search_doc_returns_results(rag_engine):
    rag_engine.docs_collection.query.return_value = _qr(["Content A"], [{"title": "Doc A"}], [0.1])
    results = rag_engine.search_documentation("react")
    assert len(results) == 1
    assert results[0]["document"] == "Content A"
    assert abs(results[0]["relevance_score"] - 0.9) < 0.001

def test_search_doc_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.search_documentation("q") == []

def test_search_doc_exception(rag_engine):
    rag_engine.docs_collection.query.side_effect = Exception("fail")
    assert rag_engine.search_documentation("q") == []


# search_code
def test_search_code_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.search_code("q") == []

def test_search_code_language_filter(rag_engine):
    rag_engine.code_collection.query.return_value = _qr([], [])
    rag_engine.search_code("q", language="python")
    kw = rag_engine.code_collection.query.call_args[1]
    assert kw.get("where") == {"language": "python"}

def test_search_code_no_filter(rag_engine):
    rag_engine.code_collection.query.return_value = _qr([], [])
    rag_engine.search_code("q")
    kw = rag_engine.code_collection.query.call_args[1]
    assert kw.get("where") is None


# search_examples
def test_search_examples_parses_json(rag_engine):
    struct = {"src": []}
    files = {"App.jsx": "code"}
    rag_engine.examples_collection.query.return_value = _qr(
        ["desc"],
        [{"project_name": "S", "structure": json.dumps(struct), "key_files": json.dumps(files)}]
    )
    results = rag_engine.search_examples("saas")
    assert results[0]["structure"] == struct


# get_context_for_prompt
def test_get_context_disabled(rag_engine):
    rag_engine.enabled = False
    assert rag_engine.get_context_for_prompt("q") == ""

def test_get_context_max_length(rag_engine):
    rag_engine.docs_collection.query.return_value = _qr(["X" * 5000], [{"title": "Long"}], [0.1])
    rag_engine.code_collection.query.return_value = _qr([], [])
    ctx = rag_engine.get_context_for_prompt("q", max_context_length=200)
    assert len(ctx) <= 220

def test_get_context_combines(rag_engine):
    rag_engine.docs_collection.query.return_value = _qr(["Use hooks."], [{"title": "React Guide"}], [0.1])
    rag_engine.code_collection.query.return_value = _qr(
        ["useData fn"], [{"name": "useData", "code": "fn", "description": ""}], [0.2]
    )
    ctx = rag_engine.get_context_for_prompt("React hook")
    assert "React Guide" in ctx
    assert "useData" in ctx


# index_project_files
def test_index_counts(rag_engine, tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.jsx").write_text("fn app()")
    (tmp_path / "src" / "utils.py").write_text("pass")
    cnt = rag_engine.index_project_files(tmp_path, extensions=[".jsx", ".py"])
    assert cnt == 2

def test_index_skips_node_modules(rag_engine, tmp_path):
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "index.js").write_text("exports={}")
    assert rag_engine.index_project_files(tmp_path, extensions=[".js"]) == 0

def test_index_disabled(rag_engine, tmp_path):
    rag_engine.enabled = False
    assert rag_engine.index_project_files(tmp_path) == 0


# seed_best_practices
def test_seed_adds_content(rag_engine):
    rag_engine.seed_best_practices()
    assert rag_engine.docs_collection.add.call_count >= 2
    assert rag_engine.code_collection.add.call_count >= 1

def test_seed_disabled(rag_engine):
    rag_engine.enabled = False
    rag_engine.seed_best_practices()
    rag_engine.docs_collection.add.assert_not_called()
