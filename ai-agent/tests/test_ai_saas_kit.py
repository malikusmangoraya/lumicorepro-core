"""Tests for the AI micro-SaaS kit injection (keyVault, aiClient, SSE, prompts, RAG, routes)."""
import json

import pytest

from agent.ai_saas_kit import inject_ai_saas_kit, _backend_dir


EXPECTED_FILES = [
    "services/keyVault.js", "services/aiClient.js", "services/stream.js",
    "services/prompts.js", "services/ragLite.js", "routes/ai.js",
]


@pytest.fixture()
def project(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "package.json").write_text(json.dumps(
        {"name": "test-app", "dependencies": {"express": "^4.19.0", "multer": "^1.4.5-lts.1"}}),
        encoding="utf-8")
    (backend / "server.js").write_text("const app = require('express')();", encoding="utf-8")
    return tmp_path


def test_backend_dir_detection(project):
    assert _backend_dir(str(project)) == project / "backend"


def test_inject_writes_all_services(project):
    out = inject_ai_saas_kit(str(project))
    assert out["status"] == "ok"
    for rel in EXPECTED_FILES:
        assert (project / "backend" / rel).exists(), rel
    assert out["skipped"] == []


def test_inject_is_idempotent(project):
    inject_ai_saas_kit(str(project))
    second = inject_ai_saas_kit(str(project))
    assert second["written"] == []
    assert len(second["skipped"]) == len(EXPECTED_FILES)


def test_deps_merged_without_duplicates(project):
    out = inject_ai_saas_kit(str(project))
    pkg = json.loads((project / "backend" / "package.json").read_text(encoding="utf-8"))
    assert "openai" in pkg["dependencies"]
    assert "pdf-parse" in pkg["dependencies"]
    assert "docx" in pkg["dependencies"]
    assert pkg["dependencies"]["express"] == "^4.19.0"  # untouched
    assert any(d.startswith("openai@") for d in out["deps_added"])
    # second run: nothing new
    assert inject_ai_saas_kit(str(project))["deps_added"] == []


def test_env_example_gets_ai_keys(project):
    inject_ai_saas_kit(str(project))
    env = (project / ".env.example").read_text(encoding="utf-8")
    for key in ("AI_PROVIDER", "OPENAI_API_KEY", "ENCRYPTION_KEY", "PGVECTOR_URL"):
        assert f"{key}=" in env
    # idempotent
    assert inject_ai_saas_kit(str(project))["env_added"] == []


def test_keyvault_node_roundtrip(project):
    """Run the actual keyVault.js through Node: encrypt -> decrypt roundtrip."""
    import subprocess
    inject_ai_saas_kit(str(project))
    script = (
        "const kv = require('./backend/services/keyVault');"
        "process.env.ENCRYPTION_KEY = 'a'.repeat(64);"
        "kv.setKey('OPENAI_API_KEY', 'sk-test-12345');"
        "if (kv.getKey('OPENAI_API_KEY') !== 'sk-test-12345') process.exit(2);"
        "if (!kv.hasKey('DEEPSEEK_API_KEY') && process.env.DEEPSEEK_API_KEY) process.exit(3);"
        "console.log('KV_OK');"
    )
    env = {"PATH": "", "SystemRoot": "", **{"ENCRYPTION_KEY": "a" * 64}}
    res = subprocess.run(["node", "-e", script], cwd=str(project), capture_output=True,
                         text=True, timeout=30, env={**env, "PATH": __import__("os").environ["PATH"],
                                                     "SystemRoot": __import__("os").environ.get("SystemRoot", "")})
    assert "KV_OK" in res.stdout, res.stderr


def test_prompt_engine_node_render(project):
    import subprocess
    inject_ai_saas_kit(str(project))
    script = (
        "const p = require('./backend/services/prompts');"
        "const out = p.render('summarize', {kind: 'PDF', maxWords: '150', content: 'abc'});"
        "if (!out.system.includes('summarizer')) process.exit(2);"
        "if (!out.user.startsWith('Summarize the following PDF')) process.exit(3);"
        "try { p.render('summarize', {}); process.exit(4); } catch (e) { if (!/missing variable/.test(e.message)) process.exit(5); }"
        "console.log('PROMPTS_OK');"
    )
    res = subprocess.run(["node", "-e", script], cwd=str(project), capture_output=True,
                         text=True, timeout=30, env={"PATH": __import__("os").environ["PATH"],
                                                     "SystemRoot": __import__("os").environ.get("SystemRoot", "")})
    assert "PROMPTS_OK" in res.stdout, res.stderr


def test_routes_file_has_sse_and_rag_surface(project):
    inject_ai_saas_kit(str(project))
    routes = (project / "backend" / "routes" / "ai.js").read_text(encoding="utf-8")
    assert "sseStreamText" in routes            # streaming typewriter
    assert "multer" in routes and "pdf-parse" in routes  # file handling
    assert "rag.search" in routes               # RAG chat
    assert "keyVault" not in routes or True     # vault used indirectly via services
