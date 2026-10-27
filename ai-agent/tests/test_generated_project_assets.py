"""Tests — generated projects ship every production asset they rely on.

These are the portability guarantees: a generated frontend must build on a clean
machine/CI (PostCSS config included), the backend must carry its env template,
schema mirror, migrations and tests, and the branding must be brand-derived.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from agent.fullstack_ultra_engine import FullStackUltraEngine, _prune_renumbered_migrations
from agent.generation_contract import resolve_generation_contract


def _generate(root: Path, brand: str, industry: str, prompt: str) -> Path:
    destination = root / brand.lower()
    result = FullStackUltraEngine().generate_project(
        str(destination),
        prompt=prompt,
        brand_name=brand,
        industry=industry,
        generation_contract=resolve_generation_contract({}),
    )
    assert result["success"], result.get("errors")
    return destination


class GeneratedProjectAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.fintech = _generate(root, "Zephyr", "fintech", "Zephyr treasury platform")
        cls.gaming = _generate(root, "NexaPlay", "gaming", "NexaPlay community platform")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_postcss_config_ships_with_the_frontend(self):
        config = self.fintech / "frontend" / "postcss.config.cjs"
        self.assertTrue(config.is_file(), "frontend must build without a parent PostCSS config")
        text = config.read_text(encoding="utf-8")
        self.assertIn("tailwindcss", text)
        self.assertIn("autoprefixer", text)

    def test_tailwind_config_is_brand_derived(self):
        a = (self.fintech / "frontend" / "tailwind.config.js").read_text(encoding="utf-8")
        b = (self.gaming / "frontend" / "tailwind.config.js").read_text(encoding="utf-8")
        self.assertIn("slate: {", a)
        self.assertIn("fontFamily", a)
        self.assertNotEqual(a, b)

    def test_index_html_loads_the_generated_fonts_and_archetype(self):
        html = (self.fintech / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("fonts.googleapis.com", html)
        self.assertIn('data-design="', html)
        self.assertIn("theme-color", html)

    def test_contact_api_migration_schema_and_env_example(self):
        backend = self.fintech / "backend"
        self.assertTrue((backend / "routes" / "contact.routes.js").is_file())
        self.assertTrue((backend / "migrations" / "003_create_contact_messages.js").is_file())
        self.assertTrue((backend / "migrations" / "002_create_records_table.js").is_file())
        self.assertTrue((backend / ".env.example").is_file())
        self.assertTrue((self.fintech / "database" / "schema.sql").is_file())
        schema = (self.fintech / "database" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("contact_messages", schema)
        self.assertIn("records", schema)

    def test_backend_tests_exist_and_cover_validation(self):
        test_file = self.fintech / "backend" / "test" / "smoke.test.js"
        self.assertTrue(test_file.is_file())
        self.assertIn("validate", test_file.read_text(encoding="utf-8"))

    def test_logo_uses_brand_variables(self):
        logo = (self.fintech / "frontend" / "src" / "components" / "common" / "UniqueLogo.jsx").read_text(encoding="utf-8")
        self.assertIn("var(--brand-primary)", logo)
        self.assertIn("var(--brand-accent)", logo)
        self.assertNotIn("#64748b", logo)

    def test_generated_env_example_documents_groq_and_xai(self):
        env = (self.fintech / ".env.example").read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=", env)
        self.assertIn("XAI_API_KEY=", env)
        self.assertIn("AI_PROVIDER=", env)

    def test_serverless_wrapper_and_listen_guard(self):
        backend = self.fintech / "backend"
        wrapper = backend / "api" / "index.js"
        self.assertTrue(wrapper.is_file())
        text = wrapper.read_text(encoding="utf-8")
        self.assertIn("require('../server')", text)
        self.assertIn("sequelize.sync()", text)
        server = (backend / "server.js").read_text(encoding="utf-8")
        self.assertIn("require.main === module", server)
        # An unconditional listen would hang a serverless invocation.
        for line in server.splitlines():
            if "app.listen(" in line:
                self.assertGreater(len(line) - len(line.lstrip()), 0, "listen must be inside a block")
        self.assertIn("CORS_ORIGIN", server)
        vercel = json.loads((backend / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(vercel["rewrites"][0]["destination"], "/api/index.js")
        self.assertTrue((backend / ".vercelignore").is_file())

    def test_backend_env_template_covers_every_var_the_code_reads(self):
        """A var the runtime reads but the template omits is a silent prod outage."""
        import re

        backend = self.fintech / "backend"
        example = (backend / ".env.example").read_text(encoding="utf-8")
        declared = {line.split("=", 1)[0].strip() for line in example.splitlines()
                    if "=" in line and not line.lstrip().startswith("#")}

        reads = set()
        for source in sorted(backend.rglob("*.js")):
            if "node_modules" in source.parts:
                continue
            text = source.read_text(encoding="utf-8", errors="ignore")
            reads.update(re.findall(r"process\.env\.([A-Z][A-Z0-9_]{2,})", text))
            reads.update(re.findall(r"key:\s*'([A-Z][A-Z0-9_]*_API_KEY)'", text))
        reads -= {"NODE_ENV", "PORT", "PATH", "HOME"}

        self.assertTrue(reads, "the backend must read its configuration from env")
        missing = sorted(reads - declared)
        self.assertEqual(missing, [], f"backend/.env.example is missing {missing}")

    def test_backend_connects_with_a_managed_postgres_url(self):
        """Neon/Supabase/Render/Railway are TLS-only and hand you one URL."""
        models = (self.fintech / "backend" / "models" / "index.js").read_text(encoding="utf-8")
        self.assertIn("DATABASE_URL", models)
        self.assertIn("ssl", models)
        self.assertIn("DB_SSL_CA", models)

    def _run_models_against_a_stub_sequelize(self, env_overrides, dotenv_values=None):
        """Execute the generated models file with recording Sequelize/dotenv stubs.

        A substring assertion cannot prove the connection args that actually
        reach the driver, so this runs the file and captures its constructor
        arguments. The dotenv stub only publishes values that a real dotenv
        would read from the project's .env file, never overriding the process
        environment passed in.
        """
        import shutil
        import subprocess

        if shutil.which("node") is None:
            self.skipTest("node is not on PATH")

        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        root = Path(work.name)
        stub = root / "node_modules" / "sequelize"
        stub.mkdir(parents=True)
        (stub.parent / "dotenv").mkdir(parents=True)
        (stub.parent / "dotenv" / "index.js").write_text(
            "module.exports = { config() {\n"
            "  const fromFile = JSON.parse(process.env.DotenvFileValues || '{}');\n"
            "  for (const [k, v] of Object.entries(fromFile)) {\n"
            "    if (process.env[k] === undefined) process.env[k] = v;\n"
            "  }\n"
            "  return { parsed: fromFile };\n"
            "} };\n",
            encoding="utf-8",
        )
        (stub / "index.js").write_text(
            "const fs = require('fs');\n"
            "const captured = [];\n"
            "class Sequelize { constructor(...args) { captured.push(args); } define() { return {}; } }\n"
            "const DataTypes = new Proxy({}, { get: (t, k) => ({ name: String(k) }) });\n"
            "module.exports = { Sequelize, DataTypes };\n"
            "process.on('exit', () => fs.writeFileSync(process.env.CaptureFile,"
            " JSON.stringify(captured)));\n",
            encoding="utf-8",
        )
        shutil.copyfile(self.fintech / "backend" / "models" / "index.js", root / "models.js")
        # Standalone entry point, exactly like `npm run db:migrate`: nothing else
        # has loaded .env before the models module is required.
        (root / "run.js").write_text("require('./models.js');\n", encoding="utf-8")
        capture = root / "captured.json"
        # Start from a bare shell: the database variables come only from what the
        # test declares, so a module that forgets to load .env cannot borrow a
        # value from the developer's own environment.
        env = {k: v for k, v in os.environ.items()
               if k not in {"DATABASE_URL", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"}}
        env["CaptureFile"] = str(capture)
        env.update(env_overrides)
        if dotenv_values is not None:
            env["DotenvFileValues"] = json.dumps(dotenv_values)
        proc = subprocess.run(["node", "run.js"], cwd=str(root), env=env,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(capture.read_text(encoding="utf-8"))

    def test_neon_postgresql_url_reaches_sequelize_as_postgres_scheme(self):
        """Sequelize v6 only parses `postgres:`. Neon issues `postgresql://`, which
        it then reads as a bare database name with no user or password, so the
        first query dies with 'client password must be a string' on a URL that
        `pg` connects with happily. The generated client must normalize it."""
        neon_url = "postgresql://neondb_owner:npg_synthetic@ep-synthetic-sample.us-east-2.aws.neon.tech/cortexdesk?sslmode=require"
        captured = self._run_models_against_a_stub_sequelize({"DATABASE_URL": neon_url})
        self.assertEqual(len(captured), 1)
        first = captured[0][0]
        self.assertIsInstance(first, str, "a connection URL must be passed as a URL, not a name")
        self.assertTrue(first.startswith("postgres://"), f"got {first[:32]!r}")
        self.assertNotIn("postgresql:", first)
        self.assertIn("neondb_owner", first, "normalizing must not drop the credentials")
        self.assertIn("cortexdesk", first)
        self.assertTrue(captured[0][1]["dialectOptions"]["ssl"]["require"])

    def test_migration_scripts_get_the_database_from_the_env_file(self):
        """`npm run db:migrate` requires only ./models, so if that module does not
        load .env the runner silently migrates localhost and the real database is
        never created."""
        neon_url = "postgresql://neondb_owner:npg_synthetic@ep-synthetic-sample.us-east-2.aws.neon.tech/cortexdesk?sslmode=require"
        captured = self._run_models_against_a_stub_sequelize({}, dotenv_values={"DATABASE_URL": neon_url})
        first = captured[0][0]
        self.assertIsInstance(first, str, "the env file value must reach the connection")
        self.assertIn("ep-synthetic-sample", first)
        self.assertTrue(first.startswith("postgres://"), f"got {first[:32]!r}")

    def test_managed_url_keeps_certificate_verification_on(self):
        """`rejectUnauthorized: false` turns TLS into encryption an attacker can
        terminate and read the credentials from, so verification is the default
        and only an explicit opt-out disables it."""
        neon_url = "postgresql://neondb_owner:npg_synthetic@ep-synthetic-sample.us-east-2.aws.neon.tech/cortexdesk?sslmode=require"
        strict = self._run_models_against_a_stub_sequelize({"DATABASE_URL": neon_url})
        self.assertTrue(strict[0][1]["dialectOptions"]["ssl"]["require"])
        self.assertTrue(strict[0][1]["dialectOptions"]["ssl"]["rejectUnauthorized"])

        loose = self._run_models_against_a_stub_sequelize(
            {"DATABASE_URL": neon_url, "DB_SSL_INSECURE": "true"})
        self.assertFalse(loose[0][1]["dialectOptions"]["ssl"]["rejectUnauthorized"],
                         "the opt-out must be honoured for self-signed hosts")

    def test_discrete_db_env_vars_still_build_a_local_connection(self):
        captured = self._run_models_against_a_stub_sequelize(
            {"DATABASE_URL": "", "DB_HOST": "127.0.0.1", "DB_NAME": "app",
             "DB_USER": "postgres", "DB_PASSWORD": "secret"}
        )
        self.assertEqual(len(captured), 1)
        config = captured[0][0]
        self.assertIsInstance(config, dict)
        self.assertEqual(config["host"], "127.0.0.1")
        self.assertIsInstance(config["password"], str)
        self.assertIsNone(config.get("dialectOptions"), "local dev must not force TLS")

    def test_health_endpoint_proves_the_database_is_reachable(self):
        """`status: healthy` from a route that never opened a connection certified
        broken deployments as live — the gate trusts this response."""
        text = (self.fintech / "backend" / "routes" / "health.routes.js").read_text(encoding="utf-8")
        self.assertIn("require('../models')", text)
        self.assertIn("SELECT 1", text)
        self.assertIn("db", text)
        self.assertIn("503", text)
        self.assertIn("degraded", text)

    def test_ai_client_supports_groq_grok_and_custom_base_urls(self):
        client = (self.fintech / "backend" / "services" / "aiClient.js").read_text(encoding="utf-8")
        self.assertIn("groq:", client)
        self.assertIn("grok:", client)
        self.assertIn("OPENAI_BASE_URL", client)
        self.assertIn("GROQ_MODEL", client)


class RenumberedMigrationPruneTests(unittest.TestCase):
    """In-place regeneration must not leave two migrations for one table."""

    def _project(self, root: Path, names: list) -> Path:
        migrations = root / "backend" / "migrations"
        migrations.mkdir(parents=True, exist_ok=True)
        for name in names:
            (migrations / name).write_text("module.exports = {};\n", encoding="utf-8")
        (migrations / "run.js").write_text("// runner\n", encoding="utf-8")
        return root

    def test_the_old_number_of_a_renamed_migration_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(Path(tmp), [
                "001_create_core_tables.js",
                "002_create_contact_messages.js",
                "002_create_records_table.js",
            ])
            removed = _prune_renumbered_migrations(str(root), {
                "backend/migrations/001_create_core_tables.js": "",
                "backend/migrations/002_create_records_table.js": "",
                "backend/migrations/003_create_contact_messages.js": "",
            })
            self.assertEqual(removed, ["002_create_contact_messages.js"])
            self.assertFalse((root / "backend/migrations/002_create_contact_messages.js").exists())
            self.assertTrue((root / "backend/migrations/002_create_records_table.js").exists())
            self.assertTrue((root / "backend/migrations/run.js").exists())

    def test_unrelated_migrations_are_never_touched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(Path(tmp), [
                "004_add_invoice_rows.js",
                "009_backfill_org_id.js",
            ])
            removed = _prune_renumbered_migrations(str(root), {
                "backend/migrations/003_create_contact_messages.js": "",
            })
            self.assertEqual(removed, [])
            self.assertTrue((root / "backend/migrations/004_add_invoice_rows.js").exists())
            self.assertTrue((root / "backend/migrations/009_backfill_org_id.js").exists())

    def test_a_matching_number_keeps_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(Path(tmp), ["003_create_contact_messages.js"])
            removed = _prune_renumbered_migrations(str(root), {
                "backend/migrations/003_create_contact_messages.js": "",
            })
            self.assertEqual(removed, [])
            self.assertTrue((root / "backend/migrations/003_create_contact_messages.js").exists())

    def test_windows_and_absolute_kit_paths_still_protect_their_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(Path(tmp), ["005_create_embeddings.js"])
            removed = _prune_renumbered_migrations(str(root), {
                f"{root}\\backend\\migrations\\005_create_embeddings.js": "",
            })
            self.assertEqual(removed, [])
            self.assertTrue((root / "backend/migrations/005_create_embeddings.js").exists())


if __name__ == "__main__":
    unittest.main()
