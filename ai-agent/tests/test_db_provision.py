"""Tests — db_provision: per-project databases without leaking a credential.

The factory used to ship every generated product against one shared database,
because provisioning was a manual step I performed outside the pipeline. These
tests pin the automated path: a validated identifier, credentials handed to the
runner as argv (never interpolated into code), and evidence that cannot contain
a connection string.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import agent.db_provision as dbp


def _test_bodies(path: Path):
    """Yield (test name, source body) for every test function in a file.

    Indentation, not the AST, because a `with patch.dict(...)` and the call it
    guards can sit anywhere inside the body and both must be inspected together.
    """
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [(i, len(line) - len(line.lstrip())) for i, line in enumerate(lines)
              if re.match(r"\s*def test_\w+", line)]
    for pos, (start, indent) in enumerate(starts):
        end = len(lines)
        for i in range(start + 1, len(lines)):
            stripped = lines[i].strip()
            current = len(lines[i]) - len(lines[i].lstrip())
            if stripped and current <= indent and re.match(r"(def |class |@)", stripped):
                end = i
                break
        yield lines[start].strip().split("(")[0].replace("def ", ""), "\n".join(lines[start:end])


def _node_result(status="created", database="acme_desk"):
    return {"ok": True, "status": status, "database": database,
            "host": "ep-example.us-east-1.aws.neon.tech"}


TEMPLATE = "postgresql://neondb_owner:npg_synthetic@ep-example.us-east-1.aws.neon.tech/cortexdesk?sslmode=require"


class ProvisionDatabaseTests(unittest.TestCase):
    def test_the_runner_only_ever_receives_a_canonical_name(self):
        """The database name is the one part of CREATE DATABASE that cannot be a bind
        parameter, so every unsafe character has to be gone before SQL is built."""
        runner = Mock(return_value=_node_result())
        with patch.object(dbp, "_run_create", runner):
            for raw in ("Acme;drop table users", 'acme"x', "acme-desk", "acme desk", "ACME_2"):
                dbp.provision_database(raw, TEMPLATE, backend_dir=".")
        self.assertEqual(len(runner.call_args_list), 5)
        for call in runner.call_args_list:
            name = call[0][0]
            self.assertTrue(dbp.DATABASE_NAME_RE.match(name), name)
            for unsafe in (";", '"', " ", "-", "'"):
                self.assertNotIn(unsafe, name)

    def test_a_name_that_cannot_be_made_safe_is_blocked_before_anything_runs(self):
        runner = Mock()
        with patch.object(dbp, "_run_create", runner):
            for bad in ("", "a", "1acme", ";;;", '"""', "x" * 40):
                with self.subTest(bad=bad):
                    result = dbp.provision_database(bad, TEMPLATE, backend_dir=".")
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["status"], "blocked")
        runner.assert_not_called()

    def test_the_name_is_validated_and_lowered(self):
        self.assertEqual(dbp.database_name("CortexDesk"), "cortexdesk")
        self.assertEqual(dbp.database_name("  acme_desk2 "), "acme_desk2")

    def test_evidence_never_carries_the_connection_string(self):
        with patch.object(dbp, "_run_create", return_value={**_node_result(),
                                                             "database_url": TEMPLATE}):
            evidence = dbp.provision_database("acme_desk", TEMPLATE, backend_dir=".")
        blob = json.dumps(evidence)
        self.assertNotIn("npg_synthetic", blob)
        self.assertNotIn("postgresql://", blob)
        self.assertNotIn("postgres://", blob)
        self.assertEqual(evidence["status"], "created")
        self.assertTrue(evidence["ok"])
        self.assertEqual(evidence["database"], "acme_desk")

    def test_an_existing_database_is_reported_as_exists_not_failed(self):
        """Re-running a delivery on the same project must not die on 'already exists'."""
        with patch.object(dbp, "_run_create", return_value=_node_result(status="exists")):
            evidence = dbp.provision_database("acme_desk", TEMPLATE, backend_dir=".")
        self.assertTrue(evidence["ok"])
        self.assertEqual(evidence["status"], "exists")

    def test_a_runner_failure_becomes_failed_with_its_message(self):
        with patch.object(dbp, "_run_create", return_value={"ok": False, "message": "permission denied"}):
            evidence = dbp.provision_database("acme_desk", TEMPLATE, backend_dir=".")
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["status"], "failed")
        self.assertIn("permission denied", evidence["message"])

    def test_a_missing_template_url_is_blocked_with_the_fix(self):
        with patch.object(dbp, "_run_create", Mock()) as runner:
            evidence = dbp.provision_database("acme_desk", "", backend_dir=".")
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["status"], "blocked")
        self.assertIn(dbp.TEMPLATE_ENV_VAR, evidence["message"])
        self.assertIn(dbp.LEGACY_TEMPLATE_ENV_VAR, evidence["message"])
        runner.assert_not_called()

    def test_no_template_configured_yields_the_actionable_reason(self):
        """An empty os.environ is not isolation: template_url() also opens the
        developer's real ai-agent/.env, and the assert below then printed a live
        Neon connection string into the test log."""
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []):
            self.assertEqual(dbp.template_url(), "")
        with patch.dict(os.environ, {dbp.LEGACY_TEMPLATE_ENV_VAR: "  postgres://h/db  "}), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []):
            self.assertEqual(dbp.template_url(), "postgres://h/db")


class ScrubTests(unittest.TestCase):
    def test_a_real_credential_disappears_but_the_prose_survives(self):
        message = f"SCRAM error on {TEMPLATE}: client password must be a string"
        clean = dbp._scrub(message, TEMPLATE)
        self.assertNotIn("npg_synthetic", clean)
        self.assertNotIn("neondb_owner", clean)
        self.assertIn("client password must be a string", clean, "the diagnosis must stay readable")

    def test_a_one_character_password_does_not_mangle_the_message(self):
        url = "postgres://u:p@localhost/db"
        clean = dbp._scrub("Cannot read properties of undefined", url)
        self.assertEqual(clean, "Cannot read properties of undefined")


class NodeRunnerShapeTests(unittest.TestCase):
    def test_the_credential_never_reaches_the_command_line(self):
        """subprocess exceptions echo their argument list — a timeout in exactly this
        shape printed a live Neon connection string into a log, so the URL travels in
        the environment and only the database name is an argument."""
        completed = Mock(return_value=Mock(returncode=0, stdout=json.dumps(_node_result()),
                                          stderr=""))
        with patch.object(subprocess, "run", completed):
            dbp._run_create("acme_desk", TEMPLATE, backend_dir="/tmp/proj/backend")
        cmd = completed.call_args[0][0]
        self.assertTrue(Path(cmd[0]).name.lower().startswith("node"), cmd[0])
        self.assertEqual(completed.call_args[1]["cwd"], "/tmp/proj/backend")
        self.assertEqual(cmd[3:], ["acme_desk"], "only the database name may be an argument")
        self.assertNotIn(TEMPLATE, " ".join(cmd))
        self.assertEqual(completed.call_args[1]["env"]["LUMICORE_DB_TEMPLATE_URL"], TEMPLATE)

    def test_a_server_error_naming_the_url_loses_the_url(self):
        leaked = json.dumps({"ok": False, "message": f"authentication failed for {TEMPLATE}"})
        completed = Mock(return_value=Mock(returncode=1, stdout=leaked, stderr=""))
        with patch.object(subprocess, "run", completed):
            evidence = dbp.provision_database("acme_desk", TEMPLATE, backend_dir=".")
        blob = json.dumps(evidence)
        self.assertNotIn("npg_synthetic", blob)
        self.assertNotIn("neondb_owner", blob)
        self.assertEqual(evidence["status"], "failed")

    def test_unparsable_output_is_failed_not_silently_ok(self):
        completed = Mock(return_value=Mock(returncode=0, stdout="ready in 3s\n", stderr=""))
        with patch.object(subprocess, "run", completed):
            result = dbp._run_create("acme_desk", TEMPLATE, backend_dir=".")
        self.assertFalse(result["ok"])
        self.assertIn("no machine-readable result", result["message"])

    def test_a_missing_node_is_reported_not_raised(self):
        with patch.object(dbp.shutil, "which", return_value=None):
            result = dbp._run_create("acme_desk", TEMPLATE, backend_dir=".")
        self.assertFalse(result["ok"])
        self.assertIn("node", result["message"].lower())


class StubPgRunnerTests(unittest.TestCase):
    """Executes the real Node runner against a stubbed pg module, because the
    argument plumbing of `node -e` (argv starts at 1, not 2) broke silently in a
    live Neon attempt and no mocked subprocess could ever have caught it."""

    SCRIPT = """
const fs = require('fs');
const seen = [];
class Client {
  constructor(cfg) { seen.push({ ctor: cfg.connectionString, ssl: cfg.ssl }); }
  connect() { return Promise.resolve(); }
  query(text, params) {
    seen.push({ text: String(text), params: params || null });
    return Promise.resolve({ rowCount: String(text).startsWith('select') ? 0 : 1 });
  }
  end() {
    fs.writeFileSync(process.env.STUB_OUT, JSON.stringify(seen));
    return Promise.resolve();
  }
}
module.exports = { Client };
"""

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def _run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub = root / "node_modules" / "pg"
            stub.mkdir(parents=True)
            (stub / "package.json").write_text('{"name":"pg","version":"0.0.0","main":"index.js"}',
                                               encoding="utf-8")
            (stub / "index.js").write_text(self.SCRIPT, encoding="utf-8")
            out = root / "seen.json"
            with patch.dict(os.environ, {"STUB_OUT": str(out)}):
                result = dbp.provision_database("Acme Desk", TEMPLATE, backend_dir=str(root))
            seen = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
        return result, seen

    def test_the_template_connects_and_only_the_create_carries_the_new_name(self):
        result, seen = self._run()
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(result["status"], "created")
        self.assertEqual(seen[0]["ctor"], TEMPLATE, "the runner connects with the template as-is")
        self.assertTrue(seen[0]["ssl"]["require"], "provisioning must not downgrade to plaintext")
        queries = [s for s in seen if "text" in s]
        exists = next(s for s in queries if s["text"].startswith("select"))
        self.assertEqual(exists["params"], ["acme_desk"], "the existence check is a bind parameter")
        created = next(s for s in queries if s["text"].startswith("CREATE DATABASE"))
        self.assertEqual(created["text"], 'CREATE DATABASE "acme_desk"')
        self.assertNotIn("npg_synthetic", json.dumps(result), "evidence must stay credential-free")

    def test_an_existing_database_is_reused_without_a_second_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "node_modules" / "pg").mkdir(parents=True)
            (root / "node_modules" / "pg" / "package.json").write_text(
                '{"name":"pg","version":"0.0.0","main":"index.js"}', encoding="utf-8")
            (root / "node_modules" / "pg" / "index.js").write_text(
                self.SCRIPT.replace("? 0 : 1", "? 1 : 1"), encoding="utf-8")
            out = root / "seen.json"
            with patch.dict(os.environ, {"STUB_OUT": str(out)}):
                result = dbp.provision_database("acme_desk", TEMPLATE, backend_dir=str(root))
            seen = json.loads(out.read_text(encoding="utf-8"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "exists")
        self.assertFalse([s for s in seen if "text" in s and s["text"].startswith("CREATE")])

    def test_the_url_for_the_project_points_at_the_new_database(self):
        url = dbp.database_url_for(TEMPLATE, "acme_desk")
        self.assertIn("/acme_desk", url)
        self.assertNotIn("/cortexdesk", url)
        self.assertTrue(url.startswith("postgresql://"))


class TemplateUrlTests(unittest.TestCase):
    """`config.settings` loads the repo-root `.env` first and stops there, so an
    agent-only credential has to be readable from `ai-agent/.env` as well."""

    def test_an_environment_value_wins(self):
        with patch.dict(os.environ, {dbp.TEMPLATE_ENV_VAR: TEMPLATE}), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []):
            self.assertEqual(dbp.template_url(), TEMPLATE)

    def test_the_legacy_neon_spelling_still_resolves(self):
        """Renaming the credential may not brick a server an owner already configured."""
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []), \
             patch.dict(os.environ, {dbp.LEGACY_TEMPLATE_ENV_VAR: TEMPLATE}):
            self.assertEqual(dbp.template_url(), TEMPLATE)

    def test_the_provider_neutral_name_wins_when_both_are_set(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []), \
             patch.dict(os.environ, {dbp.TEMPLATE_ENV_VAR: TEMPLATE,
                                     dbp.LEGACY_TEMPLATE_ENV_VAR: "postgres://legacy:pw@h/db"}):
            self.assertEqual(dbp.template_url(), TEMPLATE)

    def test_the_env_file_is_read_for_either_spelling(self):
        for name in (dbp.TEMPLATE_ENV_VAR, dbp.LEGACY_TEMPLATE_ENV_VAR):
            with self.subTest(var=name), tempfile.TemporaryDirectory() as tmp:
                env_file = Path(tmp) / ".env"
                env_file.write_text(f"{name}={TEMPLATE}\n", encoding="utf-8")
                with patch.dict(os.environ, {}, clear=True), \
                     patch.object(dbp, "_ENV_CANDIDATES", lambda: [env_file]):
                    self.assertEqual(dbp.template_url(), TEMPLATE)

    def test_the_block_message_tells_the_owner_both_names_and_the_server_need(self):
        """A rename that hides the old spelling, or a message that never says what
        the role must be able to do, turns one config gap into a support thread."""
        message = dbp.missing_credential_message()
        self.assertIn(dbp.TEMPLATE_ENV_VAR, message)
        self.assertIn(dbp.LEGACY_TEMPLATE_ENV_VAR, message)
        self.assertLess(message.index(dbp.TEMPLATE_ENV_VAR), message.index(dbp.LEGACY_TEMPLATE_ENV_VAR),
                        "the provider-neutral name is documented first")
        for requirement in ("CREATE DATABASE", "TLS", "ai-agent/.env"):
            self.assertIn(requirement, message)

    def test_the_agent_env_file_is_read_when_the_environment_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "ai-agent" / ".env"
            env_file.parent.mkdir()
            env_file.write_text(f"# comment\r\n{dbp.TEMPLATE_ENV_VAR}={TEMPLATE}\r\nOTHER=1\r\n")
            with patch.dict(os.environ, {}, clear=True), \
                 patch.object(dbp, "_ENV_CANDIDATES", lambda: [env_file]):
                self.assertEqual(dbp.template_url(), TEMPLATE)

    def test_a_missing_configuration_is_not_a_blank_credential(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(dbp, "_ENV_CANDIDATES", lambda: []):
            self.assertEqual(dbp.template_url(), "")

    def test_a_carriage_return_is_never_part_of_the_connection_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(f"{dbp.TEMPLATE_ENV_VAR}={TEMPLATE}\r\n")
            with patch.dict(os.environ, {}, clear=True), \
                 patch.object(dbp, "_ENV_CANDIDATES", lambda: [env_file]):
                self.assertFalse(dbp.template_url().endswith("\r"))


class ClearedEnvironmentIsolationTests(unittest.TestCase):
    """`patch.dict(os.environ, {}, clear=True)` does not isolate a test from the
    developer's real `.env` files, so a failing assert on a value read from disk
    printed a live Neon connection string into the suite output. Any test that
    clears the environment and still resolves a credential must stub the reader."""

    def test_no_test_resolves_a_credential_from_the_real_env_files(self):
        offenders = []
        for path in sorted(Path(__file__).resolve().parent.glob("test_*.py")):
            for name, body in _test_bodies(path):
                if "clear=True" not in body:
                    continue
                reads_real_file = "template_url(" in body or "_from_env_files(" in body
                if reads_real_file and "_ENV_CANDIDATES" not in body:
                    offenders.append(f"{path.name}::{name}")
        self.assertEqual(
            offenders, [],
            "add `patch.object(dbp, \"_ENV_CANDIDATES\", lambda: [])` — clearing os.environ "
            "still lets template_url() open ai-agent/.env and leak a real credential into the log")


class RunMigrationsTests(unittest.TestCase):
    """Creating a database leaves it empty: the product's own schema still has
    to be applied before anything is deployed against it."""

    def _backend(self, root: str, runner: bool = True) -> Path:
        backend = Path(root)
        (backend / "migrations").mkdir(parents=True, exist_ok=True)
        if runner:
            (backend / "migrations" / "run.js").write_text("// generated runner\n", encoding="utf-8")
        return backend

    def _completed(self, returncode=0, stdout="", stderr=""):
        return Mock(return_value=Mock(returncode=returncode, stdout=stdout, stderr=stderr))

    def test_the_url_reaches_the_runner_through_the_environment_only(self):
        """Same rule as creation: subprocess echoes argv, and a re-formatted URL in
        an error message is a credential in a log."""
        run = self._completed(stdout=json.dumps({"ok": True, "applied": 3, "names": ["001.js"]}))
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(tmp)
            with patch.object(subprocess, "run", run):
                dbp.run_migrations(backend, TEMPLATE)
        command = run.call_args[0][0]
        self.assertNotIn(TEMPLATE, " ".join(command))
        self.assertEqual(command[1:], [dbp.MIGRATIONS_ENTRY])
        self.assertEqual(run.call_args[1]["env"]["DATABASE_URL"], TEMPLATE)
        self.assertEqual(run.call_args[1]["cwd"], str(backend))

    def test_the_provisioned_url_overrides_the_file_the_project_ships(self):
        """`backend/.env` may still name an older database; the migrations must land
        on the one this run created, or the delivered product points at a schema
        that was never migrated."""
        run = self._completed(stdout=json.dumps({"ok": True, "applied": 1, "names": ["001.js"]}))
        url = dbp.database_url_for(TEMPLATE, "acme_desk")
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(tmp)
            (backend / ".env").write_text(f"DATABASE_URL={TEMPLATE}\n", encoding="utf-8")
            with patch.object(subprocess, "run", run):
                dbp.run_migrations(backend, url)
        self.assertEqual(run.call_args[1]["env"]["DATABASE_URL"], url)

    def test_nothing_is_spawned_without_a_connection_string(self):
        run = self._completed()
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(tmp)
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(backend, "")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["ok"])
        run.assert_not_called()

    def test_a_project_with_no_migration_entry_point_is_named_not_guessed(self):
        run = self._completed()
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(tmp, runner=False)
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(backend, TEMPLATE)
        self.assertEqual(result["status"], "missing")
        self.assertIn("migrations/run.js", result["message"])
        run.assert_not_called()

    def test_a_database_already_at_the_head_is_success(self):
        """applied: 0 means the schema is current — a redeploy must not read that
        as a failure, or every re-delivery reports a broken database."""
        run = self._completed(stdout=json.dumps({"ok": True, "applied": 0, "names": []}))
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "uptodate")
        self.assertEqual(result["applied"], 0)

    def test_the_applied_migrations_are_counted_from_the_report(self):
        run = self._completed(stdout=json.dumps(
            {"ok": True, "applied": 2, "names": ["001_create_core_tables.js", "002_create_records_table.js"]}))
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertEqual((result["status"], result["applied"]), ("applied", 2))
        self.assertEqual(len(result["names"]), 2)

    def test_a_runner_that_exits_nonzero_after_reporting_success_is_a_failure(self):
        run = self._completed(returncode=1, stdout=json.dumps({"ok": True, "applied": 1, "names": ["001.js"]}))
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("exited 1", result["message"])

    def test_a_migration_error_naming_the_url_loses_the_url(self):
        leaked = json.dumps({"ok": False, "error": f"syntax error near {TEMPLATE}"})
        run = self._completed(returncode=1, stdout=leaked)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertFalse(result["ok"])
        blob = json.dumps(result)
        self.assertNotIn("npg_synthetic", blob)
        self.assertNotIn("neondb_owner", blob)

    def test_a_runner_that_prints_prose_is_not_a_pass(self):
        run = self._completed(stdout="== migrations complete ==\n")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertFalse(result["ok"])
        self.assertIn("no machine-readable result", result["message"])

    def test_a_timeout_is_reported_without_echoing_the_command(self):
        run = Mock(side_effect=subprocess.TimeoutExpired(cmd=["node", "migrations/run.js", TEMPLATE], timeout=1))
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(subprocess, "run", run):
                result = dbp.run_migrations(self._backend(tmp), TEMPLATE)
        self.assertFalse(result["ok"])
        self.assertNotIn("npg_synthetic", json.dumps(result))

    def test_a_missing_node_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(tmp)
            with patch.object(dbp.shutil, "which", return_value=None):
                result = dbp.run_migrations(backend, TEMPLATE)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "failed")


class ScrubbedUrlShapeTests(unittest.TestCase):
    def test_a_url_the_driver_reformatted_is_still_masked(self):
        """Sequelize prints its own connection config, so the exact string we handed
        it never appears in the message — the scheme is what identifies it."""
        message = "connection rejected: postgres://someone:totally-other-secret@other-host:5432/db"
        clean = dbp._scrub(message, TEMPLATE)
        self.assertNotIn("totally-other-secret", clean)
        self.assertIn("connection rejected", clean)


if __name__ == "__main__":
    unittest.main()
