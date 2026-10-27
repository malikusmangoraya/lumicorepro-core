"""Tests — deploy_engine: never report `live` without a verified URL."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent.deploy_engine as engine


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


VERIFIED = {
    "verified": True,
    "status": "verified",
    "url": "https://acme-lumicorepro.vercel.app/",
    "title": "Acme",
    "checks": {},
    "failures": [],
}
UNVERIFIED = {
    "verified": False,
    "status": "broken-assets",
    "url": "https://acme-lumicorepro.vercel.app/",
    "title": "Acme",
    "checks": {},
    "failures": ["1/1 bundle assets failed to load"],
}


def _project(root: Path, linked: bool = False) -> Path:
    frontend = root / "frontend"
    frontend.mkdir(parents=True)
    (frontend / "package.json").write_text(json.dumps({"scripts": {"build": "vite build"}}))
    (frontend / "dist").mkdir()
    (frontend / "dist" / "index.html").write_text("<html></html>")
    if linked:
        (frontend / ".vercel").mkdir()
        (frontend / ".vercel" / "project.json").write_text(json.dumps({"projectId": "prj_x"}))
    return root


class VercelCliDeployTests(unittest.TestCase):
    def test_creates_a_project_for_an_unlinked_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            captured = {}

            def fake_run(cmd, **kwargs):
                captured["cmd"] = cmd
                return _Proc(0, "Production: https://acme-site-lumicorepro.vercel.app  dpl_abc123")

            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", side_effect=fake_run), \
                 patch.object(engine, "verify_site", return_value=VERIFIED), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine._vercel_cli_deploy(str(project), "")

            self.assertEqual(result["status"], "live")
            self.assertEqual(result["deployment_id"], "dpl_abc123")
            self.assertIn("--project", captured["cmd"])
            self.assertIn("--create-if-missing", captured["cmd"])

    def test_uses_the_linked_project_without_forcing_a_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site", linked=True)
            captured = {}

            def fake_run(cmd, **kwargs):
                captured["cmd"] = cmd
                captured["cwd"] = kwargs.get("cwd")
                return _Proc(0, "https://acme-lumicorepro.vercel.app")

            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", side_effect=fake_run), \
                 patch.object(engine, "verify_site", return_value=VERIFIED), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine._vercel_cli_deploy(str(project), "")

            self.assertEqual(result["status"], "live")
            self.assertNotIn("--project", captured["cmd"])
            # The CLI must run where .vercel lives (frontend/), not in dist/.
            self.assertEqual(Path(captured["cwd"]).name, "frontend")

    def test_api_url_is_published_before_the_build_and_required_in_verify(self):
        """Vercel rebuilds from source, so VITE_API_URL must exist on the project
        before `vercel deploy` — otherwise the live site silently posts to
        localhost while every page still returns 200."""
        import os

        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site", linked=True)
            calls = []

            def fake_run(cmd, **kwargs):
                calls.append(([str(c) for c in cmd], kwargs.get("input")))
                return _Proc(0, "https://acme-lumicorepro.vercel.app")

            env = {k: v for k, v in os.environ.items() if k != "VERCEL_TEAM_SLUG"}
            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", side_effect=fake_run), \
                 patch.dict(os.environ, env, clear=True), \
                 patch.object(engine, "verify_site", return_value=VERIFIED) as verify, \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine._vercel_cli_deploy(str(project), "", "https://api.acme.test")

            self.assertEqual(result["status"], "live")
            self.assertTrue(result["api_env"]["ok"])
            add_at = next(i for i, (cmd, _v) in enumerate(calls)
                          if cmd[1:4] == ["env", "add", "VITE_API_URL"])
            deploy_at = next(i for i, (cmd, _v) in enumerate(calls) if len(cmd) > 1 and cmd[1] == "deploy")
            self.assertLess(add_at, deploy_at, "the env var must exist before the build runs")
            self.assertEqual(calls[add_at][1], "https://api.acme.test")
            self.assertEqual(verify.call_args.kwargs["api_origin"], "https://api.acme.test")

    def test_unlinked_project_is_created_and_linked_so_env_can_be_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            calls = []

            def fake_run(cmd, **kwargs):
                calls.append([str(c) for c in cmd])
                # The link only "works" once .vercel/project.json exists, which is
                # what the deploy path checks, so write it like the real CLI would.
                if "link" in cmd:
                    (project / "frontend" / ".vercel").mkdir(parents=True, exist_ok=True)
                    (project / "frontend" / ".vercel" / "project.json").write_text("{}")
                return _Proc(0, "https://acme-site-lumicorepro.vercel.app")

            import os

            env = {k: v for k, v in os.environ.items() if k != "VERCEL_TEAM_SLUG"}
            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", side_effect=fake_run), \
                 patch.dict(os.environ, env, clear=True), \
                 patch.object(engine, "verify_site", return_value=VERIFIED), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine._vercel_cli_deploy(str(project), "", "https://api.acme.test")

            verbs = [cmd[1] for cmd in calls]
            self.assertEqual(verbs.index("project") < verbs.index("link"), True)
            self.assertEqual(verbs.index("link") < verbs.index("env"), True)
            self.assertEqual(verbs.index("env") < verbs.index("deploy"), True)
            self.assertTrue(result["api_env"]["ok"])

    def test_no_url_is_a_failure_not_a_live_deployment(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", return_value=_Proc(0, "Deployment complete")):
                result = engine._vercel_cli_deploy(str(project), "")
            self.assertEqual(result["status"], "failed")
            self.assertIn("no deployment URL", result["message"])

    def test_failed_verification_is_deployed_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", return_value=_Proc(0, "https://acme-lumicorepro.vercel.app")), \
                 patch.object(engine, "verify_site", return_value=UNVERIFIED), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine._vercel_cli_deploy(str(project), "")
            self.assertEqual(result["status"], "deployed-unverified")
            self.assertFalse(result["verification"]["verified"])
            self.assertEqual(result["verification"]["status"], "broken-assets")

    def test_spa_config_is_added_once_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            dist.mkdir()
            created = engine._ensure_vercel_spa_config(dist)
            self.assertTrue(created)
            config = json.loads((dist / "vercel.json").read_text(encoding="utf-8"))
            self.assertEqual(config["rewrites"][0]["destination"], "/index.html")
            # Prebuilt dist must not ask Vercel to run npm (no package.json there).
            self.assertNotIn("buildCommand", config)
            self.assertNotIn("framework", config)
            (dist / "vercel.json").write_text('{"custom": true}', encoding="utf-8")
            self.assertIsNone(engine._ensure_vercel_spa_config(dist))
            self.assertEqual(json.loads((dist / "vercel.json").read_text(encoding="utf-8")), {"custom": True})

    def test_vercel_project_name_can_be_overridden(self):
        with patch.dict(engine.os.environ, {"VERCEL_PROJECT_NAME": "Acme Cloud!"}):
            self.assertEqual(engine._vercel_project_name("/tmp/whatever"), "acme-cloud")
        self.assertEqual(engine._vercel_project_name("/tmp/whatever"), "whatever")

    def test_credential_errors_fall_through_to_the_next_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            with patch.object(engine.shutil, "which", side_effect=lambda name: "/usr/bin/vercel" if name == "vercel" else None), \
                 patch.object(engine.subprocess, "run", return_value=_Proc(1, stderr="No credentials found")):
                self.assertIsNone(engine._vercel_cli_deploy(str(project), "token"))

    def test_deploy_project_persists_the_report_and_verified_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            with patch.object(engine, "_store_deploy_gate", return_value={"store_gate": None, "blocked": False}), \
                 patch.object(engine, "_vercel_deploy", return_value={
                     "status": "live", "platform": "vercel", "url": "https://acme.vercel.app",
                     "verification": VERIFIED,
                 }), \
                 patch.object(engine, "_live_audit", return_value={"verification": VERIFIED}), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine.deploy_project(str(project), "vercel")

            self.assertTrue(result["verified"])
            report = json.loads((project / ".factory" / "deploy-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "live")
            self.assertTrue(report["verified"])

    def test_deploy_project_marks_unverified_as_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "acme-site")
            with patch.object(engine, "_store_deploy_gate", return_value={"store_gate": None, "blocked": False}), \
                 patch.object(engine, "_vercel_deploy", return_value={
                     "status": "deployed-unverified", "platform": "vercel",
                     "url": "https://acme.vercel.app", "verification": UNVERIFIED,
                 }), \
                 patch.object(engine, "_live_audit", return_value={"verification": UNVERIFIED}), \
                 patch.object(engine, "expected_routes", return_value=["/"]):
                result = engine.deploy_project(str(project), "vercel")
            self.assertFalse(result["verified"])
            self.assertEqual(result["status"], "deployed-unverified")


if __name__ == "__main__":
    unittest.main()
