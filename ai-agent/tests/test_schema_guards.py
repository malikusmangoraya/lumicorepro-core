"""Tests — a generated product's migrations converge, they never collide.

The production bug these pin: the deployed API calls ``sequelize.sync()`` on its
first cold request, so the tables can exist before ``npm run db:migrate`` has
ever run — and a plain ``createTable`` then dies with ``relation already exists``.
A redeployed product would ship a database it cannot migrate.

Every assertion here runs the *generated* migration files under real Node against
a stubbed Postgres interface, because a guard that only looks idempotent in a
template is not a guard.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from agent.schema_guards import GUARD_FILENAME, MIGRATION_GUARDS_JS, write_migration_guards

# Written into the project so `require('sequelize')` resolves the same way the
# deployed app resolves it: these tests prove OUR generated code's behaviour, not
# Sequelize internals (the real driver is exercised by the live delivery proof).
_SEQUELIZE_STUB = ("const DataTypes = { STRING: (n) => ({ _s: 'string', n }), TEXT: 'TEXT', "
                   "ENUM: (v) => ({ _s: 'enum', v }), UUID: 'UUID', UUIDV4: 'UUIDV4', DATE: 'DATE' };"
                   "module.exports = { DataTypes };")

_PROBE_JS = r"""
const path = require('path');
const migration = require(path.resolve(process.argv[2]));
const scenario = process.argv[3];

const tables = new Set();
const indexes = new Set();
let blind = false;  // a concurrent create can win after our existence check said "absent"
const errors = [];
const runs = [];
let current = null;

const clash = (code) => {
  const error = new Error('relation already exists');
  error.parent = { code };
  return error;
};

const queryInterface = {
  sequelize: {
    query: async (sql, options) => {
      const r = (options && options.replacements) || {};
      if (String(sql).includes('to_regclass')) {
        return [[{ reg: !blind && tables.has(r.name) ? r.name : null }]];
      }
      if (String(sql).includes('pg_indexes')) {
        const hit = !blind && indexes.has(`${r.table}.${r.index}`);
        return [hit ? [{ hit: 1 }] : []];
      }
      return [[], {}];
    },
  },
  createTable: async (name) => {
    current.create++;
    if (tables.has(name)) throw clash('42P07');
    tables.add(name);
  },
  addIndex: async (table, columns, options) => {
    current.index++;
    const index = ((options && options.indexName) || `${table}_${[].concat(columns).join('_')}`);
    if (indexes.has(`${table}.${index}`)) throw clash('42P07');
    indexes.add(`${table}.${index}`);
  },
  dropTable: async (name) => {
    current.drop++;
    tables.delete(name);
  },
};

const step = async (label, fn) => {
  current = { label, create: 0, index: 0, drop: 0 };
  try {
    await fn({ context: queryInterface });
  } catch (error) {
    errors.push(`${label}: ${error && error.message}`);
  }
  if (current) runs.push(current);  // null = a setup step, not a measured run
};

(async () => {
  if (scenario === 'twice') {
    await step('up', migration.up);
    await step('up-again', migration.up);
  } else if (scenario === 'sync-first') {
    // Stand in for sequelize.sync(): the tables exist with no migration record,
    // so the migration must create nothing and only add the indexes it owns.
    await step('bootstrap', async ({ context }) => {
      await migration.up({ context });
      current = null;
      indexes.clear();
    });
    await step('up-after-sync', migration.up);
  } else if (scenario === 'race') {
    await step('up', migration.up);
    await step('up-lost-the-race', async ({ context }) => {
      blind = true;  // our existence check answers "absent" while the row is created elsewhere
      await migration.up({ context });
      blind = false;
    });
  } else if (scenario === 'down-empty') {
    await step('down', migration.down);
  } else {
    errors.push(`unknown scenario ${scenario}`);
  }
  console.log('RESULT ' + JSON.stringify({ runs, errors }));
})();
"""


def _install_stub_sequelize(root: Path) -> None:
    package = root / "node_modules" / "sequelize"
    package.mkdir(parents=True, exist_ok=True)
    (package / "package.json").write_text(json.dumps({"name": "sequelize", "main": "index.js"}),
                                          encoding="utf-8")
    (package / "index.js").write_text(_SEQUELIZE_STUB, encoding="utf-8")


def _probe(project: Path, migration: Path, scenario: str) -> dict:
    """Run one generated migration through one scenario under real Node."""
    script = project / "_migration_probe.cjs"
    script.write_text(_PROBE_JS, encoding="utf-8")
    try:
        completed = subprocess.run(["node", str(script), str(migration), scenario],
                                   cwd=str(project), capture_output=True, text=True,
                                   timeout=90, encoding="utf-8", errors="replace")
    finally:
        script.unlink(missing_ok=True)
    assert completed.returncode == 0, f"node exited {completed.returncode}: {completed.stderr[-400:]}"
    lines = [line for line in (completed.stdout or "").splitlines() if line.startswith("RESULT ")]
    assert lines, f"the probe printed no result: {completed.stdout[-400:]}{completed.stderr[-400:]}"
    return json.loads(lines[-1][len("RESULT "):])


@pytest.fixture(scope="module")
def generated_backend():
    """One real generated project, shared by the idempotency tests."""
    if shutil.which("node") is None:
        pytest.fail("node is required to prove the generated migrations run")
    from agent.fullstack_ultra_engine import FullStackUltraEngine
    from agent.generation_contract import resolve_generation_contract

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "converge"
        result = FullStackUltraEngine().generate_project(
            str(root), prompt="Converge payroll platform", brand_name="Converge",
            industry="fintech", generation_contract=resolve_generation_contract({}),
        )
        assert result["success"], result.get("errors")
        backend = root / "backend"
        (backend / "migrations" / GUARD_FILENAME).write_text(MIGRATION_GUARDS_JS, encoding="utf-8")
        _install_stub_sequelize(backend)
        yield backend


def _migrations(backend: Path):
    files = sorted(p for p in backend.glob("migrations/0*.js") if p.name != GUARD_FILENAME)
    assert files, "a generated product must ship numbered migrations"
    return files


def test_the_guards_file_sits_beside_the_migrations(tmp_path):
    path = write_migration_guards(tmp_path / "backend" / "migrations")
    assert path.name == GUARD_FILENAME
    assert path.read_text(encoding="utf-8") == MIGRATION_GUARDS_JS


def test_the_runner_never_treats_the_guards_as_a_migration(generated_backend):
    """The runner globs `00*.js`; a guard named like a migration would run as one."""
    runner = (generated_backend / "migrations" / "run.js").read_text(encoding="utf-8")
    assert "00*.js" in runner
    assert not GUARD_FILENAME[0].isdigit(), GUARD_FILENAME
    assert (generated_backend / "migrations" / GUARD_FILENAME).is_file()


def test_the_spec_kit_ships_the_guards_on_an_existing_repo(tmp_path):
    """apply_production_spec also runs on projects the engine never generated."""
    from agent.production_spec_kit import apply_production_spec

    backend = tmp_path / "backend"
    (backend / "migrations").mkdir(parents=True)
    (backend / "routes").mkdir()
    (backend / "package.json").write_text(json.dumps(
        {"name": "legacy", "scripts": {}, "dependencies": {}}), encoding="utf-8")
    apply_production_spec(str(tmp_path), brand="Legacy")
    assert (backend / "migrations" / GUARD_FILENAME).is_file()


def test_every_generated_migration_goes_through_the_guards(generated_backend):
    """A single plain `createTable` left in any template reintroduces the collision."""
    for migration in _migrations(generated_backend):
        text = migration.read_text(encoding="utf-8")
        assert "_guards.js" in text, f"{migration.name} does not require the guards"
        for dangerous in ("queryInterface.createTable(", "queryInterface.dropTable("):
            assert dangerous not in text, f"{migration.name} still calls {dangerous} directly"
        assert "queryInterface.addIndex(" not in text.replace("addIndexIfMissing", ""), \
            f"{migration.name} still calls addIndex directly"


_GENERATORS_DIR = Path(__file__).resolve().parents[1] / "agent"
_BARE_DDL = ("queryInterface.createTable(", "queryInterface.dropTable(", "queryInterface.addIndex(")


def test_no_generator_module_writes_a_migration_that_is_not_guarded():
    """The engine is not the only thing that emits migrations.

    Every generator module (the API generator, the payment scaffolder, any extension
    added later) is scanned, because one unguarded template is enough to ship a
    product whose database cannot be migrated twice. Only `schema_guards.py` itself
    may name the raw calls — that is where the guards implement them.
    """
    offenders = []
    for source in sorted(_GENERATORS_DIR.glob("**/*.py")):
        if source.name == "schema_guards.py":
            continue
        text = source.read_text(encoding="utf-8")
        offenders.extend(f"{source.relative_to(_GENERATORS_DIR)}: {call}"
                         for call in _BARE_DDL if call in text)
    assert offenders == [], "unguarded DDL in a generator template: " + "; ".join(offenders)


def test_the_api_generator_ships_guarded_migrations_and_a_machine_readable_runner(tmp_path):
    from agent.api_generator import APIGenerator

    APIGenerator()._generate_migrations(tmp_path)
    migrations = tmp_path / "migrations"
    assert (migrations / GUARD_FILENAME).is_file()

    core = (migrations / "001_create_core_tables.js").read_text(encoding="utf-8")
    assert "_guards.js" in core, core[:200]
    for call in _BARE_DDL:
        assert call not in core, call

    runner = (migrations / "run.js").read_text(encoding="utf-8")
    assert "JSON.stringify" in runner, "the runner must answer the pipeline, not just a human"
    for key in ("ok: true", "applied", "names", "pending"):
        assert key in runner, f"runner contract is missing {key!r}"
    assert r"/^\d+_.*\.js$/" in runner, "numbered files only, so _guards.js is never a migration"
    if shutil.which("node"):
        for js in sorted(migrations.glob("*.js")):
            check = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            assert check.returncode == 0, f"{js.name}: {check.stderr[:200]}"


def test_the_payment_scaffolder_guards_a_migration_it_previously_shipped_bare(tmp_path):
    from agent.extensions.checkout_stripe import CheckoutScaffolder

    project = tmp_path / "shop"
    backend = project / "backend"
    (backend / "migrations").mkdir(parents=True)
    (project / "generation-report.json").write_text(json.dumps(
        {"industry": "ecommerce", "features": ["catalog", "stripe_payments"]}), encoding="utf-8")
    stale = backend / "migrations" / "002_payment_events.js"
    stale.write_text("module.exports = { up: async ({ queryInterface }) => "
                     "{ await queryInterface.createTable('orders', {}); } };\n", encoding="utf-8")

    CheckoutScaffolder(str(project)).scaffold()

    assert (backend / "migrations" / GUARD_FILENAME).is_file()
    text = stale.read_text(encoding="utf-8")
    assert "_guards.js" in text, "a delivered project kept its unguarded payment migration"
    assert "queryInterface.createTable(" not in text
    if shutil.which("node"):
        assert subprocess.run(["node", "--check", str(stale)], capture_output=True).returncode == 0, \
            "the rewritten payment migration is not valid JavaScript"


_UMZUG_STUB = r"""
// Stands in for umzug's bookkeeping: it lists the files the generated runner's
// own glob matches (so the glob is proved under Node), and remembers what it
// applied in a fake SequelizeMeta so the second run is a real no-op.
const fs = require('fs');
const path = require('path');

const escape = (part) => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

class SequelizeStorage {}

class Umzug {
  constructor(config) {
    this.config = config;
    this.dir = process.cwd();
    const [folder, base] = String(config.migrations.glob).split('/');
    this.folder = folder;
    this.pattern = new RegExp('^' + base.split('*').map(escape).join('.*') + '$');
    this.meta = path.join(this.dir, '.meta.json');
  }
  _files() {
    return fs.readdirSync(path.join(this.dir, this.folder))
      .filter((name) => this.pattern.test(name))
      .sort()
      .map((name) => ({ name }));
  }
  _executed() {
    try { return JSON.parse(fs.readFileSync(this.meta, 'utf8')); } catch { return []; }
  }
  async executed() { return this._executed().map((name) => ({ name })); }
  async pending() {
    const done = this._executed();
    return this._files().filter((migration) => !done.includes(migration.name));
  }
  async up() {
    const applying = await this.pending();
    for (const migration of applying) {
      const step = require(path.join(this.dir, this.folder, migration.name));
      await step.up({ context: this.config.context });
    }
    fs.writeFileSync(this.meta, JSON.stringify([...this._executed(), ...applying.map((m) => m.name)]));
    return applying;
  }
}

module.exports = { Umzug, SequelizeStorage };
"""

_MODELS_STUB = """
// The runner only needs a query interface and a close(); the guards do the rest.
const tables = new Set();
const indexes = new Set();
const queryInterface = {
  sequelize: {
    query: async (sql, options) => {
      const r = (options && options.replacements) || {};
      if (String(sql).includes('to_regclass')) return [[{ reg: tables.has(r.name) ? r.name : null }]];
      if (String(sql).includes('pg_indexes')) return [indexes.has(`${r.table}.${r.index}`) ? [{ hit: 1 }] : []];
      return [[], {}];
    },
    close: async () => {},
    getQueryInterface: () => queryInterface,
  },
  createTable: async (name) => { tables.add(name); },
  addIndex: async (table, columns, options) => {
    const index = (options && options.indexName) || `${table}_${[].concat(columns).join('_')}`;
    indexes.add(`${table}.${index}`);
  },
  dropTable: async (name) => { tables.delete(name); },
};
module.exports = { sequelize: queryInterface.sequelize };
"""


def _runner_project(generated_backend: Path, tmp: Path) -> Path:
    """Copy the generated runner into a project whose deps are stubbed."""
    backend = tmp / "backend"
    (backend / "migrations").mkdir(parents=True)
    (backend / "models").mkdir(parents=True)
    (backend / "node_modules" / "umzug").mkdir(parents=True)
    shutil.copyfile(generated_backend / "migrations" / "run.js", backend / "migrations" / "run.js")
    for migration in _migrations(generated_backend):
        shutil.copyfile(migration, backend / "migrations" / migration.name)
    guards = generated_backend / "migrations" / GUARD_FILENAME
    if guards.is_file():
        shutil.copyfile(guards, backend / "migrations" / GUARD_FILENAME)
    (backend / "models" / "index.js").write_text(_MODELS_STUB, encoding="utf-8")
    umzug = backend / "node_modules" / "umzug"
    (umzug / "package.json").write_text(json.dumps({"name": "umzug", "main": "index.js"}),
                                        encoding="utf-8")
    (umzug / "index.js").write_text(_UMZUG_STUB, encoding="utf-8")
    _install_stub_sequelize(backend)  # the migrations themselves require DataTypes
    return backend


def _run_runner(backend: Path) -> dict:
    completed = subprocess.run(["node", "migrations/run.js"], cwd=str(backend),
                               capture_output=True, text=True, timeout=120,
                               encoding="utf-8", errors="replace")
    assert completed.returncode == 0, f"{completed.stderr[-500:]} / {completed.stdout[-500:]}"
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert lines, "the migration runner printed nothing on stdout"
    return json.loads(lines[-1])


def test_the_migration_runner_reports_one_machine_readable_line(generated_backend, tmp_path):
    """The pipeline gates on this line: a runner that only prints prose cannot
    prove a schema landed, and `applied: 0` must be distinguishable from a crash."""
    backend = _runner_project(generated_backend, tmp_path)
    first = _run_runner(backend)
    assert first["ok"] is True, first
    assert first["applied"] == len(first["names"]) >= 1, first
    assert GUARD_FILENAME not in first["names"], \
        f"the glob ran {GUARD_FILENAME} as a migration: {first['names']}"
    second = _run_runner(backend)
    assert second["ok"] is True and second["applied"] == 0, second


def test_db_provision_reports_the_migrations_it_applied(generated_backend, tmp_path):
    """run_migrations() must read the runner's line, not the process exit code."""
    from agent.db_provision import run_migrations

    backend = _runner_project(generated_backend, tmp_path)
    result = run_migrations(backend, "postgresql://owner:npg_synthetic@ep-x.neon.tech/probe?sslmode=require")
    assert result["ok"] is True, result
    assert result["status"] == "applied" and result["applied"] >= 1, result
    again = run_migrations(backend, "postgresql://owner:npg_synthetic@ep-x.neon.tech/probe?sslmode=require")
    assert again["ok"] is True and again["status"] == "uptodate", again
    for evidence in (result, again):
        assert "npg_synthetic" not in json.dumps(evidence), evidence


@pytest.mark.parametrize("scenario", ["twice", "sync-first", "race", "down-empty"])
def test_a_generated_migration_survives_being_run_again(generated_backend, scenario):
    """The whole point: run order is not under our control, the schema still lands."""
    for migration in _migrations(generated_backend):
        report = _probe(generated_backend, migration, scenario)
        assert report["errors"] == [], f"{migration.name} under {scenario}: {report['errors']}"
        if scenario == "twice":
            first, second = report["runs"]
            assert first["create"] >= 1, f"{migration.name} created nothing on its first run"
            assert second["create"] == 0, f"{migration.name} re-created a table that exists"
            assert second["index"] == 0, f"{migration.name} re-added an index that exists"
        if scenario == "sync-first":
            assert report["runs"][-1]["create"] == 0, \
                f"{migration.name} tried to create a table sequelize.sync() already made"
        if scenario == "down-empty":
            assert report["runs"][-1]["drop"] == 0, \
                f"{migration.name} dropped a table that was never created"
