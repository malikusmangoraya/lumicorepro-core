"""Tests — factory_pipeline: every stage is a gate, and the report is evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent.factory_pipeline as factory


def _project(root: Path) -> Path:
    frontend = root / "frontend"
    (frontend / "dist").mkdir(parents=True)
    (frontend / "dist" / "index.html").write_text("<html></html>")
    return root


class FactoryPipelineTests(unittest.TestCase):
    def _run(self, **overrides):
        base = {
            "build_project": {"ok": True, "dist": "/tmp/dist", "steps": {}},
            "test_backend": {"ok": True, "code": 0},
            "run_qa": {"ok": True, "status": "passed", "results": {}},
            "deploy_project": {"status": "live", "platform": "vercel", "url": "https://x.vercel.app",
                               "verified": True, "verification": {"verified": True}},
            "generate_demo_video": {"status": "ready", "verified": True, "video": "/tmp/demo.mp4",
                                    "duration_seconds": 120.0, "resolution": "1920x1080"},
        }
        base.update(overrides)
        return base

    def test_delivered_only_when_every_stage_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value=self._run()["build_project"]), \
                 patch.object(factory, "test_backend", return_value=self._run()["test_backend"]), \
                 patch.object(factory, "run_qa", return_value=self._run()["run_qa"]), \
                 patch("agent.deploy_engine.deploy_project", return_value=self._run()["deploy_project"]), \
                 patch("agent.demo_video.generate_demo_video", return_value=self._run()["generate_demo_video"]):
                result = factory.run_factory(str(project), deploy="vercel", video=True, name="Acme")

            self.assertEqual(result["status"], "delivered")
            self.assertTrue(result["verified"])
            report = json.loads((project / ".factory" / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "delivered")
            self.assertTrue((project / ".factory" / "report.md").is_file())

    def test_local_only_run_is_built_never_delivered(self):
        """`delivered` claims a hosted product — --factory-deploy none cannot earn it."""
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value=self._run()["build_project"]), \
                 patch.object(factory, "test_backend", return_value=self._run()["test_backend"]), \
                 patch.object(factory, "run_qa", return_value=self._run()["run_qa"]), \
                 patch("agent.deploy_engine.deploy_project", unittest.mock.Mock()) as deploy:
                result = factory.run_factory(str(project), deploy="none", video=False, name="Acme")

            self.assertEqual(result["status"], "built")
            self.assertFalse(result["verified"])
            self.assertIn("no hosting was requested", result["message"])
            deploy.assert_not_called()

    def test_build_failure_stops_before_deploy(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            deploy = unittest.mock.Mock()
            with patch.object(factory, "build_project", return_value={"ok": False, "message": "build broke"}), \
                 patch("agent.deploy_engine.deploy_project", deploy):
                result = factory.run_factory(str(project), deploy="vercel", video=False)
            self.assertEqual(result["status"], "failed")
            self.assertIn("build broke", result["message"])
            deploy.assert_not_called()

    def test_backend_test_failure_blocks_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": False, "message": "tests failed"}):
                result = factory.run_factory(str(project), deploy="vercel", video=False)
            self.assertEqual(result["status"], "failed")
            self.assertIn("tests failed", result["message"])

    def test_qa_failure_blocks_unless_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": False, "message": "console errors"}):
                blocked = factory.run_factory(str(project), deploy="vercel", video=False)
            self.assertEqual(blocked["status"], "failed")

            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": False, "message": "console errors"}), \
                 patch("agent.deploy_engine.deploy_project", return_value={"status": "live", "verified": True,
                                                                       "url": "https://x"}):
                allowed = factory.run_factory(str(project), deploy="vercel", video=False, allow_qa_fail=True)
            self.assertEqual(allowed["status"], "partial")
            self.assertIn("QA failed (allowed by caller)", allowed["failures"])

    def test_unverified_deploy_is_partial_and_never_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "deployed-unverified", "verified": False,
                     "url": "https://x", "message": "assets missing",
                 }), \
                 patch("agent.demo_video.generate_demo_video", return_value={
                     "status": "ready", "verified": True, "video": "/tmp/demo.mp4",
                 }):
                result = factory.run_factory(str(project), deploy="vercel", video=True)
            self.assertEqual(result["status"], "partial")
            self.assertFalse(result["verified"])
            self.assertTrue(any("deployment not verified" in f for f in result["failures"]))

    def test_video_failure_keeps_the_run_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://x",
                 }), \
                 patch("agent.demo_video.generate_demo_video", return_value={
                     "status": "failed", "verified": False, "failures": ["duration too short"],
                 }):
                result = factory.run_factory(str(project), deploy="vercel", video=True)
            self.assertEqual(result["status"], "partial")
            self.assertIn("demo video not verified", result["failures"])

    def test_backend_present_without_a_hosted_api_is_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            (project / "backend").mkdir()
            (project / "backend" / "package.json").write_text("{}")
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}),                  patch.object(factory, "test_backend", return_value={"ok": True}),                  patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}),                  patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://x",
                 }),                  patch("agent.demo_video.generate_demo_video", return_value={
                     "status": "ready", "verified": True,
                 }):
                result = factory.run_factory(str(project), deploy="vercel", video=True)
            self.assertEqual(result["status"], "partial")
            self.assertIn("api_deployed", result["stages"]["deploy"])
            self.assertFalse(result["stages"]["deploy"]["api_deployed"])

    def test_hosted_api_health_makes_the_run_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            (project / "backend").mkdir()
            (project / "backend" / "package.json").write_text("{}")
            good = {"verified": True, "status": "verified", "checks": {"api": {"ok": True}}}
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}),                  patch.object(factory, "test_backend", return_value={"ok": True}),                  patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}),                  patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://x",
                 }),                  patch("agent.live_verify.verify_site", return_value=good),                  patch("agent.demo_video.generate_demo_video", return_value={
                     "status": "ready", "verified": True,
                 }):
                result = factory.run_factory(
                    str(project), deploy="vercel", video=True,
                    api_url="https://api.example.com/api/v1",
                    api_health="/api/v1/health",
                )
            self.assertEqual(result["status"], "delivered")
            self.assertTrue(result["stages"]["deploy"]["api_deployed"])

    def test_an_api_url_alone_still_probes_the_generated_health_route(self):
        """The generated backend always serves api/v1/health, so naming the API host
        is enough — requiring a second flag is how a run skipped the API proof."""
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            (project / "backend").mkdir()
            (project / "backend" / "package.json").write_text("{}")
            good = {"verified": True, "status": "verified", "checks": {"api": {"ok": True}}}
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://x",
                 }), \
                 patch("agent.live_verify.verify_site", return_value=good) as probe, \
                 patch("agent.demo_video.generate_demo_video", return_value={
                     "status": "ready", "verified": True,
                 }):
                result = factory.run_factory(
                    str(project), deploy="vercel", video=True,
                    api_url="https://api.example.com/api/v1",
                )
            probe.assert_called_once_with(
                "https://x", api_health="https://api.example.com/api/v1/health", timeout=60
            )
            self.assertEqual(result["status"], "delivered")
            self.assertEqual(
                result["stages"]["deploy"]["api_health_url"],
                "https://api.example.com/api/v1/health",
            )

    def test_skip_build_requires_an_existing_dist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "empty"
            project.mkdir()
            result = factory.run_factory(str(project), deploy="none", video=False, skip_build=True)
            self.assertEqual(result["status"], "failed")
            self.assertIn("dist/index.html", result["stages"]["build"]["message"])


class ApiHealthTargetTests(unittest.TestCase):
    """The API lives on its own host, so its health path must not be joined to
    the frontend URL — the SPA rewrites every unknown path to index.html and a 200
    of HTML was previously read as proof the backend was live."""

    def test_path_is_resolved_against_the_api_origin(self):
        self.assertEqual(
            factory.api_health_target("https://cortexdesk-api.vercel.app/api/v1", "/api/v1/health"),
            "https://cortexdesk-api.vercel.app/api/v1/health",
        )

    def test_absolute_health_url_wins(self):
        self.assertEqual(
            factory.api_health_target("https://api.test", "https://other.test/health"),
            "https://other.test/health",
        )

    def test_without_an_api_url_the_path_stays_relative_to_the_verified_site(self):
        self.assertEqual(factory.api_health_target("", "/api/v1/health"), "api/v1/health")

    def test_an_api_host_proves_its_health_route_without_being_told_the_path(self):
        """backend/ generated by this agent always serves api/v1/health, so a run
        that only names the API host must still probe it instead of skipping the
        check — a silent skip is how an offline database shipped as 'delivered'."""
        self.assertEqual(
            factory.api_health_target("https://api.test/api/v1", ""),
            "https://api.test/api/v1/health",
        )

    def test_a_full_health_url_as_the_api_base_is_probed_as_is(self):
        self.assertEqual(
            factory.api_health_target("https://api.test/api/v1/health", ""),
            "https://api.test/api/v1/health",
        )

    def test_a_shell_rewritten_path_falls_back_to_the_generated_contract(self):
        """Git Bash turns /api/v1/health into D:/Git/api/v1/health and urljoin reads
        the drive letter as a scheme — the probe would hit a file, never the API."""
        for mangled in ("D:/Git/api/v1/health", "C:\\msys\\api\\v1\\health"):
            with self.subTest(mangled=mangled):
                self.assertEqual(
                    factory.api_health_target("https://api.test/api/v1", mangled),
                    "https://api.test/api/v1/health",
                )
        self.assertEqual(factory.api_health_target("", "D:/Git/api/v1/health"), "")


if __name__ == "__main__":
    unittest.main()
