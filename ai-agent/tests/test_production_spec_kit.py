"""Tests for production_spec_kit: Docker, INSTRUCTIONS, TS types, validation, CRUD, dashboard."""
import json
import subprocess
import sys
import os

import pytest

from agent.production_spec_kit import apply_production_spec, _patched_server, _backend_dir


@pytest.fixture()
def project(tmp_path):
    backend = tmp_path / "backend"
    (backend / "migrations").mkdir(parents=True)
    (backend / "routes").mkdir()
    (backend / "package.json").write_text(json.dumps(
        {"name": "spec-app", "scripts": {}, "dependencies": {"express": "^4.19.0"}}), encoding="utf-8")
    (backend / "server.js").write_text(
        "const app = express();\n"
        "app.use('/api/v1/auth', authRoutes);\n"
        "app.use('/api/v1/health', healthRoutes);\n"
        "module.exports = app;\n", encoding="utf-8")
    models_dir = backend / "models"
    models_dir.mkdir()
    (models_dir / "index.js").write_text(
        "const DataTypes = { STRING: () => ({}), TEXT: 'TEXT', ENUM: () => ({}), UUID: 'UUID', UUIDV4: 'UUIDV4', DATE: 'DATE' };\n"
        "module.exports = { sequelize: { define: () => ({}) }, DataTypes };\n", encoding="utf-8")
    utils_dir = backend / "utils"
    utils_dir.mkdir()
    (utils_dir / "jwtSecret.js").write_text(
        "const jwtSecret = process.env.JWT_SECRET || 'probe-secret-'.padEnd(40, 'x');\n"
        "module.exports = { jwtSecret };\n", encoding="utf-8")
    from agent.ai_saas_kit import inject_ai_saas_kit
    inject_ai_saas_kit(str(tmp_path))
    frontend = tmp_path / "frontend"
    (frontend / "src" / "pages").mkdir(parents=True)
    (frontend / "src" / "pages" / "Dashboard.jsx").write_text(
        "<div>Control Console static</div>", encoding="utf-8")
    # Minimal third-party stubs: these tests prove OUR generated code's syntax
    # and wiring, not express internals (full deps install in engine e2e only).
    nm = backend / "node_modules"
    for name, exports in {
        "express": "const chain = { use(){return chain;}, get(){return chain;}, post(){return chain;}, listen(){return chain;} }; module.exports = () => chain; module.exports.json = () => (r, e, n) => n(); module.exports.Router = () => ({ use(){}, get(){}, post(){}, put(){}, delete(){} }); module.exports.static = () => (r, e, n) => n();",
        "multer": "module.exports = () => ({ single: () => (r, e, n) => n(), array: () => (r, e, n) => n() });",
        "pdf-parse": "module.exports = async () => ({ text: '' });",
        "docx": "module.exports = { Document: class {}, Packer: {} };",
        "jsonwebtoken": "module.exports = { sign: () => 't', verify: () => ({ id: 'u1' }) };",
        "bcryptjs": "module.exports = { hash: (p) => p, compare: () => true };",
        "pg": "module.exports = { Client: class {} };",
        "openai": "module.exports = {};",
        "sequelize": "const DataTypes = { STRING: (n) => ({ _s: 'string', n }), TEXT: 'TEXT', ENUM: (v) => ({ _s: 'enum', v }), UUID: 'UUID', UUIDV4: 'UUIDV4', DATE: 'DATE' };"
                    "module.exports = { DataTypes, define: () => ({}) };",
    }.items():
        d = nm / name
        d.mkdir(parents=True)
        (d / "package.json").write_text(json.dumps({"name": name, "main": "index.js"}), encoding="utf-8")
        (d / "index.js").write_text(exports, encoding="utf-8")
    return tmp_path


def test_creates_all_spec_files(project):
    out = apply_production_spec(str(project), brand="SpecApp")
    root = project / "backend"
    for rel in ("Dockerfile", "tsconfig.json", "types/index.d.ts",
                "middleware/validate.js", "routes/records.routes.js",
                "migrations/002_create_records_table.js"):
        assert (root / rel).exists(), rel
    assert (project / "INSTRUCTIONS.md").exists()
    assert (project / "frontend" / "Dockerfile").exists()
    assert (project / "frontend" / "nginx.conf").exists()
    assert out["status"] == "ok"


def test_dockerfiles_are_multi_stage(project):
    apply_production_spec(str(project), brand="SpecApp")
    fe = (project / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    assert fe.count("FROM") >= 2 and "nginx:alpine" in fe  # build -> serve
    be = (project / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert be.count("FROM") >= 2 and "USER appuser" in be and "HEALTHCHECK" in be


def test_server_js_mounts_records_ai_and_error_handler(project):
    apply_production_spec(str(project), brand="SpecApp")
    text = (project / "backend" / "server.js").read_text(encoding="utf-8")
    assert "require('./routes/records.routes')" in text
    assert "require('./routes/ai')" in text
    assert "errorHandler" in text
    assert _patched_server(project / "backend" / "server.js") is False  # idempotent


def test_backend_deps_get_typescript_tooling(project):
    out = apply_production_spec(str(project), brand="SpecApp")
    pkg = json.loads((project / "backend" / "package.json").read_text(encoding="utf-8"))
    assert "typescript" in pkg["devDependencies"]
    assert pkg["scripts"]["typecheck"] == "tsc --noEmit"
    assert any("types" in d or "typescript" in d for d in out["updated"]) or out["updated"]
    # idempotent
    apply_production_spec(str(project), brand="SpecApp")
    pkg2 = json.loads((project / "backend" / "package.json").read_text(encoding="utf-8"))
    assert pkg2["devDependencies"]["typescript"] == pkg["devDependencies"]["typescript"]


def test_records_migration_has_fk_and_index(project):
    apply_production_spec(str(project), brand="SpecApp")
    mig = (project / "backend" / "migrations" / "002_create_records_table.js").read_text(encoding="utf-8")
    assert "references: { model: 'users', key: 'id' }" in mig
    assert "addIndex" in mig


def test_dashboard_is_live_crud(project):
    apply_production_spec(str(project), brand="SpecApp")
    dash = (project / "frontend" / "src" / "pages" / "Dashboard.jsx").read_text(encoding="utf-8")
    assert "/records" in dash and "loading" in dash and "Retry" in dash
    assert "data-testid=\"dashboard-empty\"" in dash  # empty state shipped
    # untouched on re-run (not a Control-Console placeholder anymore)
    before = dash
    apply_production_spec(str(project), brand="SpecApp")
    assert (project / "frontend" / "src" / "pages" / "Dashboard.jsx").read_text(encoding="utf-8") == before


def test_instructions_covers_all_sections(project):
    apply_production_spec(str(project), brand="SpecApp")
    doc = (project / "INSTRUCTIONS.md").read_text(encoding="utf-8")
    for section in ("Prerequisites", "Local Setup", "docker compose up", "Environment Variables",
                    "Troubleshooting", "TypeScript", "Security"):
        assert section in doc, section
    assert "INSTRUCTIONS — SpecApp" in doc


def _run_node_script(project, snippet):
    """Write a temp entry script INSIDE the project so relative requires resolve."""
    p = project / "_node_probe.cjs"
    p.write_text(snippet, encoding="utf-8")
    env = {"PATH": os.environ["PATH"], "SystemRoot": os.environ.get("SystemRoot", "")}
    try:
        return subprocess.run(["node", str(p)], cwd=str(project),
                              capture_output=True, text=True, timeout=60, env=env)
    finally:
        p.unlink(missing_ok=True)


def test_all_generated_js_parses_in_node(project):
    """Real Node require of every generated module — syntax + wiring proof."""
    apply_production_spec(str(project), brand="SpecApp")
    mods = [
        "./backend/middleware/validate.js",
        "./backend/routes/records.routes.js",
        "./backend/services/keyVault.js",
        "./backend/services/prompts.js",
        "./backend/services/stream.js",
        "./backend/services/ragLite.js",
        "./backend/services/aiClient.js",
        "./backend/routes/ai.js",
    ]
    script = ";".join(f"require({json.dumps(m)})" for m in mods) + ";console.log('PARSE_OK');"
    res = _run_node_script(project, script)
    assert "PARSE_OK" in res.stdout, res.stderr or res.stdout

    # middleware check: validate() sanitizes + rejects bad schemas
    script2 = (
        "const { validate, sanitize, errorHandler } = require('./backend/middleware/validate.js');"
        "if (sanitize('<img src=x onerror=alert(1)>').includes('<img')) process.exit(2);"
        "let hit = null; const mw = validate({ title: { required: true, type: 'string', max: 5 } });"
        "mw({ body: { title: 'x'.repeat(9) } }, null, (e) => { hit = e; });"
        "if (!hit || hit.status !== 422) process.exit(3);"
        "hit = null; mw({ body: { title: 'ok' } }, null, (e) => { hit = e; });"
        "if (hit) process.exit(4);"
        "if (typeof errorHandler !== 'function') process.exit(5);"
        "console.log('VALIDATE_OK');"
    )
    res2 = _run_node_script(project, script2)
    assert "VALIDATE_OK" in res2.stdout, res2.stderr or res2.stdout
