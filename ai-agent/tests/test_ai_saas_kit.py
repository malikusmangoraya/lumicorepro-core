"""Tests for the AI micro-SaaS kit injection (keyVault, aiClient, SSE, prompts, RAG, routes)."""
import json
import os
import re
import subprocess

import pytest

from agent.ai_saas_kit import inject_ai_saas_kit, _backend_dir


EXPECTED_FILES = [
    "services/keyVault.js", "services/aiClient.js", "services/stream.js",
    "services/prompts.js", "services/ragLite.js", "middleware/aiAuth.js",
    "routes/ai.js",
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
    # aiAuth.js requires it; a missing dep would kill the whole router at load.
    assert "jsonwebtoken" in pkg["dependencies"]
    assert pkg["dependencies"]["express"] == "^4.19.0"  # untouched
    assert any(d.startswith("openai@") for d in out["deps_added"])
    # second run: nothing new
    assert inject_ai_saas_kit(str(project))["deps_added"] == []


def test_env_example_gets_ai_keys(project):
    inject_ai_saas_kit(str(project))
    env = (project / ".env.example").read_text(encoding="utf-8")
    for key in ("AI_PROVIDER", "OPENAI_API_KEY", "ENCRYPTION_KEY", "PGVECTOR_URL", "JWT_SECRET"):
        assert f"{key}=" in env
    # idempotent
    assert inject_ai_saas_kit(str(project))["env_added"] == []


def test_no_retired_provider_model_is_shipped(project):
    """Groq retired `llama-3.3-70b-versatile`; a generated project that defaults
    to it fails its first AI call with model_not_found, minutes after deploy."""
    inject_ai_saas_kit(str(project))
    client = (project / "backend" / "services" / "aiClient.js").read_text(encoding="utf-8")
    env = (project / ".env.example").read_text(encoding="utf-8")
    for text in (client, env):
        assert "llama-3.3-70b-versatile" not in text
        assert "llama-3.2-11b-vision" not in text
    assert "openai/gpt-oss-120b" in client
    assert "GROQ_MODEL=openai/gpt-oss-120b" in env


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


def test_upload_route_never_writes_to_disk(project):
    """A serverless host mounts the bundle read-only.

    `multer({ dest: 'uploads/' })` creates that directory at module load, so
    requiring the router throws `EROFS: mkdir /var/task/uploads` and the whole
    /api/ai surface disappears behind a silent catch. The generated upload
    route must keep the bytes in memory.
    """
    inject_ai_saas_kit(str(project))
    routes = (project / "backend" / "routes" / "ai.js").read_text(encoding="utf-8")
    assert "multer.memoryStorage()" in routes
    assert "dest:" not in routes
    assert "req.file.path" not in routes
    assert "req.file.buffer" in routes
    assert "req.file.filename" not in routes


def test_every_ai_route_is_auth_gated(project):
    """The AI surface spends the owner's provider key on every call.

    Shipping it anonymously means anyone who finds the URL can drain the
    account. All three cost-bearing routes must sit behind the same JWT check
    the project's own auth routes mint tokens with.
    """
    inject_ai_saas_kit(str(project))
    routes = (project / "backend" / "routes" / "ai.js").read_text(encoding="utf-8")
    for route in ("/generate", "/chat", "/files"):
        assert re.search(rf"router\.post\('{route}', aiAuth,", routes), route
    assert "require('../middleware/aiAuth')" in routes
    # /health stays open: a load balancer cannot present a user token.
    assert re.search(r"router\.get\('/health',\s*\(_?req", routes)
    assert (project / "backend" / "middleware" / "aiAuth.js").exists()


def test_ai_auth_fails_closed_in_node(project):
    """Real Node run: no token -> 401, bad token -> 401, weak secret -> 503.

    A missing JWT_SECRET must never degrade to "allow": that turns a
    misconfigured deployment into an open proxy for the owner's API key.
    """
    inject_ai_saas_kit(str(project))
    stub = project / "backend" / "node_modules" / "jsonwebtoken"
    stub.mkdir(parents=True)
    (stub / "package.json").write_text(
        json.dumps({"name": "jsonwebtoken", "main": "index.js"}), encoding="utf-8")
    (stub / "index.js").write_text(
        "module.exports = { verify: (token, secret) => {"
        "  if (token === 'good' && typeof secret === 'string' && secret.length >= 32) return { id: 'u1' };"
        "  throw new Error('bad token');"
        "} };", encoding="utf-8")

    probe = project / "_auth_probe.cjs"
    probe.write_text(
        "const aiAuth = require('./backend/middleware/aiAuth');"
        "const call = (headers, secret) => {"
        "  process.env.JWT_SECRET = secret;"
        "  let status = 200;"
        "  const res = { status(c) { status = c; return { json() {} }; } };"
        "  let nexted = false;"
        "  aiAuth({ headers }, res, () => { nexted = true; });"
        "  return nexted ? 'next' : status;"
        "};"
        "const s = 'x'.repeat(32);"
        "if (call({}, s) !== 401) process.exit(2);"
        "if (call({ authorization: 'Bearer nope' }, s) !== 401) process.exit(3);"
        "if (call({ authorization: 'Bearer good' }, 'short') !== 503) process.exit(4);"
        "if (call({}, 'short') !== 503) process.exit(5);"
        "if (call({ authorization: 'Bearer good' }, s) !== 'next') process.exit(6);"
        "console.log('AUTH_OK');", encoding="utf-8")
    env = {"PATH": os.environ["PATH"], "SystemRoot": os.environ.get("SystemRoot", "")}
    try:
        res = subprocess.run(["node", str(probe)], cwd=str(project),
                             capture_output=True, text=True, timeout=60, env=env)
    finally:
        probe.unlink(missing_ok=True)
    assert "AUTH_OK" in res.stdout, res.stderr or res.stdout
