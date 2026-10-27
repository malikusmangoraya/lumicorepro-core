"""Tests — deploy_backend: an Express API is live only with a verified database.

A frontend-only deployment used to be reportable as a full delivery, and the API
half was a manual step outside the pipeline. These tests pin the automated half:
the API project is created and named, its runtime environment is published
without leaking credentials into the evidence, and `live` is refused unless the
hosted health endpoint reports the database reachable.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent.deploy_engine as engine


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


DB_URL = "postgres://neondb_owner:npg_synthetic@ep-sample-pooler.us-east-1.aws.neon.tech/acme?sslmode=require"
API_HEALTHY = {"ok": True, "status": "verified", "url": "https://acme-api.vercel.app/api/v1/health",
               "body": {"status": "healthy", "db": "connected"}, "failures": []}
API_DB_DOWN = {"ok": False, "status": "db-disconnected", "url": "https://acme-api.vercel.app/api/v1/health",
               "body": {"status": "degraded", "db": "disconnected"},
               "failures": ["the hosted API answered but its database is unreachable"]}


def _backend(root: Path, *, with_env: bool = True) -> Path:
    project = root / "acme-desk"
    backend = project / "backend"
    backend.mkdir(parents=True)
    (backend / "package.json").write_text(json.dumps({"name": "acme-desk-api"}))
    (backend / "vercel.json").write_text(json.dumps({"version": 2}))
    (backend / "api").mkdir()
    (backend / "api" / "index.js").write_text("module.exports = () => {};")
    (backend / ".env.example").write_text(
        "NODE_ENV=production\nDATABASE_URL=\nJWT_SECRET=\nENCRYPTION_KEY=\n"
        "BRAND_NAME=Acme Desk\nAPP_URL=https://acme-desk.vercel.app\nCORS_ORIGIN=\nPORT=5000\n"
    )
    if with_env:
        (backend / ".env").write_text(f"DATABASE_URL={DB_URL}\nBRAND_NAME=Acme Desk\n")
    return project


def _fake_cli(captured, deploy_stdout="Production: https://acme-api.vercel.app  dpl_api1"):
    """Record every CLI call, answering the deploy with a production URL."""

    def run(cmd, **kwargs):
        entry = {"cmd": list(cmd), "stdin": kwargs.get("input"), "cwd": kwargs.get("cwd")}
        captured.setdefault("calls", []).append(entry)
        if "deploy" in cmd:
            return _Proc(0, deploy_stdout)
        if "protection" in cmd:
            return _Proc(0, '{"ssoProtection": null}')
        return _Proc(0, "")

    return run


def _run_deploy(project, captured, health=API_HEALTHY, calls=None, deploy_stdout=None,
                health_replies=None):
    """Invoke deploy_backend with the CLI and the network both stubbed out."""
    def run(cmd, **kwargs):
        entry = {"cmd": list(cmd), "stdin": kwargs.get("input"), "cwd": kwargs.get("cwd")}
        captured.setdefault("calls", []).append(entry)
        if "deploy" in cmd:
            return _Proc(0, deploy_stdout or "Production: https://acme-api.vercel.app  dpl_api1")
        if "protection" in cmd:
            return _Proc(0, '{"ssoProtection": null}')
        return _Proc(0, "")

    probe = (patch.object(engine, "verify_api_health", side_effect=health_replies)
             if health_replies else
             patch.object(engine, "verify_api_health", return_value=health))
    with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
         patch.object(engine.subprocess, "run", side_effect=run), \
         probe as verify, \
         patch.dict(engine.os.environ, {"VERCEL_TEAM_SLUG": "lumicorepro"}, clear=False):
        result = engine.deploy_backend(str(project), **(calls or {}))
    result["_verify"] = verify
    return result


def _flatten(captured):
    return [" ".join(c["cmd"]) for c in captured.get("calls", [])]


def _protection_calls(captured):
    return [line for line in _flatten(captured) if "protection" in line]


API_WALL = {"ok": False, "status": "platform-page", "attempts": 1,
            "url": "https://acme-desk-api.vercel.app/api/v1/health", "body": "",
            "failures": ["the API host answered with a platform page instead of the health "
                         "endpoint (platform login wall (sso-protection)) — the deployment is "
                         "not publicly reachable"]}


class BackendProjectNamingTests(unittest.TestCase):
    def test_the_api_project_is_named_after_the_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            self.assertEqual(engine._backend_project_name(str(project)), "acme-desk-api")

    def test_an_override_beats_the_derived_name(self):
        with patch.dict(engine.os.environ, {"VERCEL_BACKEND_PROJECT_NAME": "Custom API!"}):
            self.assertEqual(engine._backend_project_name("/anywhere/acme-desk"), "custom-api")


class BackendEnvPublishingTests(unittest.TestCase):
    def test_every_required_runtime_var_is_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL})
            published = {c["cmd"][c["cmd"].index("add") + 1]
                         for c in captured.get("calls", []) if "add" in c["cmd"]}
            for name in engine.BACKEND_REQUIRED_ENV:
                self.assertIn(name, published, f"{name} was never published")
            self.assertEqual(result["status"], "live")

    def test_a_windows_line_break_never_reaches_a_published_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            # The generated .env is written on Windows: CRLF throughout.
            (project / "backend" / ".env").write_text(
                f"DATABASE_URL={DB_URL}\r\nBRAND_NAME=Acme Desk\r\n"
            )
            captured = {}
            _run_deploy(project, captured, calls={"database_url": DB_URL})
            for call in captured.get("calls", []):
                if "add" in call["cmd"] and call["stdin"] is not None:
                    self.assertNotIn("\r", call["stdin"],
                                     "a CR would be stored as part of the secret")

    def test_no_credential_appears_anywhere_in_the_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL})
            blob = json.dumps({k: v for k, v in result.items() if k != "_verify"}, default=str)
            self.assertNotIn("npg_synthetic", blob)
            self.assertNotIn("postgres://", blob)
            self.assertIn("DATABASE_URL", result["env"]["published"])

    def test_a_secret_missing_from_the_env_file_is_generated_and_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            first = engine.backend_runtime_env(str(project / "backend"), database_url=DB_URL)
            second = engine.backend_runtime_env(str(project / "backend"), database_url=DB_URL)
            self.assertGreaterEqual(len(first["JWT_SECRET"]), 32)
            self.assertNotEqual(first["JWT_SECRET"], first["ENCRYPTION_KEY"])
            self.assertEqual(first["JWT_SECRET"], second["JWT_SECRET"],
                             "a redeploy must not rotate the signing key out from under stored tokens")
            persisted = (project / "backend" / ".env").read_text(encoding="utf-8")
            self.assertIn("JWT_SECRET=", persisted)

    def test_cors_origin_is_published_only_when_a_frontend_url_is_handed_over(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            bare = engine.backend_runtime_env(str(project / "backend"), database_url=DB_URL)
            with_origin = engine.backend_runtime_env(
                str(project / "backend"), database_url=DB_URL,
                cors_origin="https://acme-desk.vercel.app")
            self.assertNotIn("CORS_ORIGIN", bare)
            self.assertEqual(with_origin["CORS_ORIGIN"], "https://acme-desk.vercel.app")

    def test_the_provisioned_database_lands_in_the_delivered_env_file(self):
        """The hosted API is handed the URL as an argument; `npm run db:migrate`
        in the delivered folder only ever reads backend/.env, so a run that
        provisioned a database but left it out of that file ships a project
        whose migrations silently target localhost."""
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp), with_env=False)
            # The real delivered state: the secrets were persisted, the database was not.
            (project / "backend" / ".env").write_text(
                "JWT_SECRET=deadbeef90\nENCRYPTION_KEY=123456\n", encoding="utf-8")
            engine.backend_runtime_env(str(project / "backend"), database_url=DB_URL)
            persisted = engine.read_env_file(project / "backend" / ".env")
            self.assertEqual(persisted.get("DATABASE_URL"), DB_URL)
            self.assertEqual(persisted["JWT_SECRET"], "deadbeef90",
                             "writing the database must not rewrite the secret block")

    def test_locking_the_hosted_cors_never_moves_the_local_dev_origin(self):
        """The CORS lock pass re-deploys with the production origin. Persisting
        that into backend/.env would leave the local server refusing the dev
        client it is supposed to serve."""
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            engine.backend_runtime_env(str(project / "backend"), database_url=DB_URL,
                                       cors_origin="https://acme-desk.vercel.app")
            persisted = engine.read_env_file(project / "backend" / ".env")
            self.assertNotEqual(persisted.get("CORS_ORIGIN"), "https://acme-desk.vercel.app")


class BackendDeployGateTests(unittest.TestCase):
    def test_nothing_is_deployed_without_a_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp), with_env=False)
            captured = {}
            result = _run_deploy(project, captured)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("NEON_TEMPLATE_DATABASE_URL", result["message"])
            self.assertEqual(captured.get("calls", []), [], "the CLI must not run at all")

    def test_live_is_refused_when_the_hosted_database_is_unreachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, health=API_DB_DOWN, calls={"database_url": DB_URL})
            self.assertNotEqual(result["status"], "live")
            self.assertFalse(result["verified"])
            self.assertEqual(result["status"], "api-db-unreachable")
            self.assertIn("database", result["message"].lower())

    def test_a_health_check_never_targets_a_local_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            with patch.object(engine, "verify_api_health", return_value=API_HEALTHY) as verify:
                with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                     patch.object(engine.subprocess, "run", side_effect=_fake_cli(captured)), \
                     patch.dict(engine.os.environ, {"VERCEL_TEAM_SLUG": "lumicorepro"}, clear=False):
                    engine.deploy_backend(str(project), database_url=DB_URL)
                url = verify.call_args[0][0]
            self.assertTrue(url.startswith("https://"), url)
            self.assertNotIn("D:/", url)
            self.assertTrue(url.endswith("api/v1/health"))

    def test_a_missing_backend_directory_is_a_failure_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = engine.deploy_backend(str(Path(tmp) / "no-such-project"), database_url=DB_URL)
            self.assertEqual(result["status"], "failed")
            self.assertIn("backend/", result["message"])

    def test_the_cli_exit_code_alone_never_claims_live(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL})
            deploy_calls = [c for c in captured["calls"] if "deploy" in c["cmd"]]
            self.assertTrue(deploy_calls)
            self.assertIn("--prod", deploy_calls[0]["cmd"])
            self.assertEqual(result["deployment_id"], "dpl_api1")

    def test_a_report_is_written_without_any_secret_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL})
            report = Path(result["report_path"]).read_text(encoding="utf-8")
            self.assertNotIn("npg_synthetic", report)
            self.assertIn("acme-desk-api", report)


class DeploymentProtectionTests(unittest.TestCase):
    """A CLI-created Vercel project inherits "Require Vercel Authentication", so
    every *.vercel.app URL answers with a login page — the API is deployed, yet
    neither a probe nor a client can reach it. The pipeline owns that setting."""

    def test_a_project_the_pipeline_creates_is_opened_for_public_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL})
            calls = _protection_calls(captured)
            self.assertTrue(calls, "deployment protection was never touched")
            self.assertIn("acme-desk-api", calls[0])
            self.assertIn("--sso", calls[0])
            self.assertEqual(result["protection"]["status"], "public")

    def test_a_wall_is_repaired_and_the_health_reprobed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL},
                                 health_replies=[API_WALL, API_HEALTHY])
            self.assertEqual(result["status"], "live", result)
            self.assertTrue(result["verified"])
            self.assertGreaterEqual(len(_protection_calls(captured)), 2,
                                    "the wall must reopen protection before re-probing")

    def test_a_persistent_wall_is_named_rather_than_called_a_broken_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL},
                                 health_replies=[API_WALL] * 6)
            self.assertEqual(result["status"], "deployed-protected")
            self.assertFalse(result["verified"])
            self.assertIn("login wall", result["message"])

    def test_the_cli_created_project_is_opened_before_the_first_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            _run_deploy(project, captured, calls={"database_url": DB_URL})
            order = _flatten(captured)
            self.assertLess(order.index(next(l for l in order if "protection" in l)),
                            order.index(next(l for l in order if "deploy ." in l)),
                            "protecting the project after deploying wastes the whole health budget")


class StableApiDomainTests(unittest.TestCase):
    """The chosen API URL is baked into the shipped bundle, so it has to survive
    the next deployment: `vercel deploy --prod` mints a fresh
    `<name>-<hash>-<team>.vercel.app` for every run and only the `Aliased` domain
    is permanent. Short project domains are global, so one may belong to another
    tenant — a domain the CLI did not print is never guessed."""

    ALIASED_OUTPUT = ("  Production      https://acme-desk-mpruirzo0-lumicorepro.vercel.app\n"
                      "▲ Aliased         https://acme-desk-api-theta.vercel.app\n dpl_api2")

    def test_the_aliased_project_domain_is_the_one_baked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL},
                                 deploy_stdout=self.ALIASED_OUTPUT)
            self.assertEqual(result["url"], "https://acme-desk-api-theta.vercel.app")
            self.assertEqual(result["health_url"],
                             "https://acme-desk-api-theta.vercel.app/api/v1/health")

    def test_a_domain_the_cli_never_printed_is_never_assumed(self):
        """https://acme-desk-api.vercel.app may be some other tenant's protected
        app; baking it would post the client's contact form to a stranger."""
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL},
                                 deploy_stdout="  Production      "
                                               "https://acme-desk-mpruirzo0-lumicorepro.vercel.app dpl_api2")
            blob = json.dumps({k: v for k, v in result.items() if k != "_verify"}, default=str)
            self.assertNotIn("https://acme-desk-api.vercel.app", blob)
            self.assertEqual(result["url"],
                             "https://acme-desk-mpruirzo0-lumicorepro.vercel.app")

    def test_a_bare_domain_is_used_only_when_the_cli_printed_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            result = _run_deploy(project, captured, calls={"database_url": DB_URL},
                                 deploy_stdout="  Production      https://acme-desk-api.vercel.app dpl_api3")
            self.assertEqual(result["url"], "https://acme-desk-api.vercel.app")


class BackendRedeployTests(unittest.TestCase):
    def test_the_cors_pass_reuses_the_linked_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _backend(Path(tmp))
            captured = {}
            _run_deploy(project, captured, calls={"database_url": DB_URL,
                                                  "cors_origin": "https://acme-desk.vercel.app"})
            names = [c for c in captured["calls"] if "link" in c["cmd"]]
            self.assertTrue(names)
            self.assertIn("acme-desk-api", " ".join(names[0]["cmd"]))


if __name__ == "__main__":
    unittest.main()
