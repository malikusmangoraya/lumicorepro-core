"""Tests — factory_pipeline: every stage is a gate, and the report is evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import agent.factory_pipeline as factory

TEMPLATE_FOR_TEST = ("postgres://neondb_owner:npg_synthetic"
                     "@ep-example.us-east-1.aws.neon.tech/cortexdesk?sslmode=require")


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
                 }),                  patch("agent.live_verify.verify_site", return_value=good),                  patch("agent.live_verify.verify_api_health", return_value={"ok": True, "status": "verified"}),                  patch("agent.live_verify.verify_contact_write", return_value={"ok": True, "status": "verified", "id": "row-1"}),                  patch("agent.live_verify.verify_api_surface", return_value={"ok": True, "status": "verified", "proven": ["POST /api/v1/records"], "leftovers": []}),                  patch("agent.live_verify.verify_realtime_feed", return_value={"ok": True, "status": "verified", "latency_ms": 400, "events": ["ready"], "leftovers": []}),                  patch("agent.demo_video.generate_demo_video", return_value={
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
                 patch("agent.live_verify.verify_api_health",
                       return_value={"ok": True, "status": "verified"}), \
                 patch("agent.live_verify.verify_contact_write",
                       return_value={"ok": True, "status": "verified", "id": "row-1"}), \
                 patch("agent.live_verify.verify_api_surface",
                       return_value={"ok": True, "status": "verified", "proven": ["POST /api/v1/records"],
                                     "leftovers": []}), \
                 patch("agent.live_verify.verify_realtime_feed",
                       return_value={"ok": True, "status": "verified", "latency_ms": 400,
                                     "events": ["ready"], "leftovers": []}), \
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


class FullStackHostingTests(unittest.TestCase):
    """A delivery is only complete when the frontend AND the API AND the database
    are all live: the client has to be handed a working demo, not a static page."""

    LIVE_API = {"status": "live", "verified": True, "url": "https://site-api.vercel.app",
                "health_url": "https://site-api.vercel.app/api/v1/health",
                "project_name": "site-api", "env": {"published": ["DATABASE_URL"]},
                "deployment_id": "dpl_api1"}
    PROVISIONED = {"ok": True, "status": "created", "database": "site",
                   "host": "ep-example.us-east-1.aws.neon.tech", "message": ""}
    VERIFIED_SITE = {"verified": True, "status": "verified", "checks": {"api": {"ok": True}}}
    WRITE_OK = {"ok": True, "status": "verified", "id": "3f9a", "url": "https://site-api.vercel.app/api/v1/contact"}
    SURFACE_OK = {"ok": True, "status": "verified", "token": "jwt.secret-signing-output",
                  "proven": ["POST /api/v1/auth/register", "GET /api/v1/records",
                             "DELETE /api/v1/records/:id"],
                  "leftovers": [], "url": "https://site-api.vercel.app"}
    FEED_OK = {"ok": True, "status": "verified", "latency_ms": 412, "id": "row-7",
               "events": ["ready", "record:changed", "cleaned"], "leftovers": []}

    def _project_with_backend(self, tmp: str) -> Path:
        project = _project(Path(tmp) / "site")
        (project / "backend").mkdir()
        (project / "backend" / "package.json").write_text("{}")
        return project

    def _stages(self, project, result, *, api_deploy=None, provision=None, write=None,
                surface=None, feed=None, verify_site_result=None, deploy_result=None, build=None):
        """Run the factory with every external boundary stubbed."""
        site_evidence = verify_site_result or self.VERIFIED_SITE
        frontend = deploy_result or {"status": "live", "verified": True,
                                     "url": "https://site.vercel.app"}
        builds = build or Mock(return_value={"ok": True, "dist": "/tmp"})
        with patch.object(factory, "build_project", builds), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.db_provision.template_url", return_value=TEMPLATE_FOR_TEST), \
                 patch("agent.db_provision.provision_database",
                       provision or Mock(return_value=self.PROVISIONED)) as db_mock, \
                 patch("agent.deploy_engine.deploy_backend",
                       api_deploy or Mock(return_value=self.LIVE_API)) as api_mock, \
                 patch("agent.deploy_engine.deploy_project", return_value=frontend) as front_mock, \
                 patch("agent.live_verify.verify_site", return_value=site_evidence), \
                 patch("agent.live_verify.verify_api_health",
                       return_value={"ok": True, "status": "verified"}), \
                 patch("agent.live_verify.verify_contact_write",
                       write or Mock(return_value=self.WRITE_OK)) as write_mock, \
                 patch("agent.live_verify.verify_api_surface",
                       surface or Mock(return_value=self.SURFACE_OK)) as surface_mock, \
                 patch("agent.live_verify.verify_realtime_feed",
                       feed or Mock(return_value=self.FEED_OK)) as feed_mock, \
                 patch("agent.demo_video.generate_demo_video",
                       return_value={"status": "ready", "verified": True, "duration_seconds": 120.0}):
            out = factory.run_factory(str(project), deploy="vercel", video=False, name="Acme")
        return out, {"db": db_mock, "api": api_mock, "frontend": front_mock,
                     "write": write_mock, "surface": surface_mock, "feed": feed_mock,
                     "build": builds}

    def test_the_database_is_provisioned_before_the_api_is_deployed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            order = []
            db = Mock(side_effect=lambda *a, **k: (order.append("db"), self.PROVISIONED)[1])
            api = Mock(side_effect=lambda *a, **k: (order.append("api"), self.LIVE_API)[1])
            out, _ = self._stages(project, "x", api_deploy=api, provision=db)
            # The API is deployed twice (the second pass locks CORS), but the
            # database always comes first — sync() on the first request needs it.
            self.assertEqual(order[:2], ["db", "api"], out["stages"])
            self.assertEqual(out["status"], "delivered", out.get("failures"))

    def test_the_hosted_api_origin_is_what_the_frontend_is_deployed_against(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, mocks = self._stages(project, "x")
            self.assertEqual(mocks["frontend"].call_args.kwargs.get("api_url"),
                             "https://site-api.vercel.app", out["stages"]["deploy"])

    def test_the_api_is_handed_the_database_and_the_report_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, mocks = self._stages(project, "x")
            handed = mocks["api"].call_args.kwargs
            self.assertIn("/site", str(handed.get("database_url", "")))
            report = (project / ".factory" / "report.json").read_text(encoding="utf-8")
            markdown = (project / ".factory" / "report.md").read_text(encoding="utf-8")
            for evidence in (report, markdown):
                self.assertNotIn("npg_", evidence)
                self.assertNotIn("postgres://", evidence)
            self.assertEqual(out["stages"]["database"]["database"], "site")

    def test_the_cors_pass_locks_the_api_to_the_live_frontend(self):
        """Production CORS must not stay on * once the site has a real origin."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, mocks = self._stages(project, "x")
            origins = [c.kwargs.get("cors_origin", "") for c in mocks["api"].call_args_list]
            self.assertIn("https://site.vercel.app", origins, out["stages"]["api"])
            self.assertEqual(mocks["api"].call_count, 2)

    def test_an_api_behind_a_login_page_names_the_setting_that_blocks_it(self):
        """`deployed-protected` is a platform setting, not a broken backend, and the
        report has to say which switch to turn off."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            protected = {"status": "deployed-protected", "verified": False,
                         "url": "https://site-api.vercel.app", "project_name": "site-api",
                         "message": "the API host answered with a platform page instead of the "
                                    "health endpoint (platform login wall (sso-protection))"}
            out, _ = self._stages(project, "x", api_deploy=Mock(return_value=protected))
            self.assertEqual(out["status"], "partial")
            listed = [f for f in out["failures"] if f.startswith("API not live")]
            self.assertTrue(listed, out["failures"])
            self.assertIn("vercel project protection disable", listed[0])
            self.assertIn("site-api", listed[0])

    def test_an_api_that_changes_domain_after_the_build_is_not_delivered(self):
        """The shipped bundle calls whatever origin was baked at build time; a CORS
        pass that lands on a different production domain means the client's forms
        post somewhere the verifier never proved."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            moved = {**self.LIVE_API, "url": "https://site-api-theta.vercel.app",
                     "health_url": "https://site-api-theta.vercel.app/api/v1/health"}
            out, _ = self._stages(project, "x",
                                  api_deploy=Mock(side_effect=[self.LIVE_API, moved]))
            self.assertEqual(out["status"], "partial", out["failures"])
            self.assertTrue(any("different domain" in f for f in out["failures"]),
                            out["failures"])
            self.assertIn("bundle calls https://site-api.vercel.app",
                          out["stages"]["api"]["cors"]["drift"])

    def test_delivered_requires_the_contact_form_to_have_written_a_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            write = Mock(return_value={"ok": False, "status": "write-failed",
                                       "failures": ["the hosted contact form did not accept a real submission"]})
            out, _ = self._stages(project, "x", write=write)
            self.assertEqual(out["status"], "partial")
            self.assertFalse(out["verified"])
            self.assertTrue(any("contact" in f.lower() for f in out["failures"]), out["failures"])

    def test_a_blocked_database_stops_the_full_stack_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            db = Mock(return_value={"ok": False, "status": "blocked", "database": "site",
                                    "message": "no database server is configured; set NEON_TEMPLATE_DATABASE_URL"})
            api = Mock(return_value={"status": "blocked", "verified": False,
                                     "message": "the API has no database to connect to"})
            out, _ = self._stages(project, "x", api_deploy=api, provision=db)
            self.assertEqual(out["status"], "partial")
            self.assertTrue(any("NEON_TEMPLATE_DATABASE_URL" in f for f in out["failures"]),
                            out["failures"])

    def test_an_operator_hosted_api_is_not_hosted_a_second_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            api = Mock(return_value=self.LIVE_API)
            db = Mock(return_value=self.PROVISIONED)
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.db_provision.provision_database", db), \
                 patch("agent.deploy_engine.deploy_backend", api), \
                 patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://site.vercel.app"}), \
                 patch("agent.live_verify.verify_site", return_value=self.VERIFIED_SITE), \
                 patch("agent.live_verify.verify_api_health",
                       return_value={"ok": True, "status": "verified"}), \
                 patch("agent.live_verify.verify_contact_write",
                       return_value=self.WRITE_OK), \
                 patch("agent.live_verify.verify_api_surface",
                       return_value=self.SURFACE_OK), \
                 patch("agent.live_verify.verify_realtime_feed",
                       return_value=self.FEED_OK), \
                 patch("agent.demo_video.generate_demo_video",
                       return_value={"status": "ready", "verified": True}):
                out = factory.run_factory(str(project), deploy="vercel", video=False,
                                          api_url="https://their-api.example.com")
            db.assert_not_called()
            api.assert_not_called()
            self.assertEqual(out["status"], "delivered", out.get("failures"))
            self.assertEqual(out["stages"]["database"]["status"], "skipped")

    def test_the_report_hands_the_client_every_url_and_names_nothing_unproven(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, _ = self._stages(project, "x")
            text = (project / ".factory" / "report.md").read_text(encoding="utf-8")
            for expected in ("https://site.vercel.app", "https://site-api.vercel.app",
                             "https://site-api.vercel.app/api/v1/health", "site",
                             "ep-example.us-east-1.aws.neon.tech"):
                self.assertIn(expected, text)
            self.assertNotIn("npg_", text)
            self.assertIn("Not proven", text)

    def test_a_delivered_report_never_labels_a_stage_as_failed(self):
        """This markdown is what gets pasted to a client. A provisioned database
        carries no `ok` key, so the renderer fell through to its allowlist and
        printed `## database — FAIL/UNVERIFIED` two lines under `delivered`."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, _ = self._stages(project, "x")
            self.assertEqual(out["status"], "delivered", out.get("failures"))
            text = (project / ".factory" / "report.md").read_text(encoding="utf-8")
            self.assertNotIn("FAIL/UNVERIFIED", text, text)
            self.assertIn("## database — PASS", text)

    def test_a_route_that_breaks_the_client_journey_is_not_delivered(self):
        """`db: connected` and one contact row say nothing about the dashboard's
        own routes: list, create, read-back, update and delete each shipped broken
        on their own at least once, and a tenant that can read another's rows is a
        security bug the health check cannot see."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            broken = {"ok": False, "status": "tenant-isolation-broken",
                      "failures": ["the second account read the first account's row"],
                      "proven": ["POST /api/v1/auth/register"], "leftovers": ["row-1"]}
            out, _ = self._stages(project, "x", surface=Mock(return_value=broken))
            self.assertEqual(out["status"], "partial", out["failures"])
            listed = [f for f in out["failures"] if "client journey" in f]
            self.assertTrue(listed, out["failures"])
            self.assertIn("tenant-isolation-broken", listed[0])
            self.assertIn("second account read", listed[0])

    def test_a_dashboard_that_never_gets_the_push_is_not_delivered(self):
        """The shipped page says "Live updates". A feed that never fires leaves the
        polling fallback, so the page looks alive while the push is dead."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            dead = {"ok": False, "status": "no-event", "events": ["ready"], "latency_ms": 0,
                    "leftovers": [], "failures": ["no `record:changed` frame arrived"]}
            out, _ = self._stages(project, "x", feed=Mock(return_value=dead))
            self.assertEqual(out["status"], "partial", out["failures"])
            listed = [f for f in out["failures"] if "change feed" in f]
            self.assertTrue(listed, out["failures"])
            self.assertIn("no-event", listed[0])

    def test_the_feed_is_opened_with_the_session_the_endpoint_proof_minted(self):
        """The change feed is authenticated and EventSource cannot set headers, so
        the token the surface probe registered has to be the one it connects with."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, mocks = self._stages(project, "x")
            self.assertEqual(mocks["feed"].call_args.args[1], "jwt.secret-signing-output",
                             out["stages"]["handshake"])

    def test_the_handoff_lists_the_routes_proved_and_the_push_latency(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, _ = self._stages(project, "x")
            text = (project / ".factory" / "report.md").read_text(encoding="utf-8")
            self.assertIn("API surface", text)
            self.assertIn("DELETE /api/v1/records/:id", text)
            self.assertIn("Live updates", text)
            self.assertIn("412 ms", text)
            self.assertIn("row `3f9a`", text)

    def test_a_sub_millisecond_push_is_still_reported_as_live(self):
        """The live run measured 0 ms (the frame beat the latency floor) and the
        handoff silently dropped the line, because 0 is falsy in Python."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            fast = {**self.FEED_OK, "latency_ms": 0}
            self._stages(project, "x", feed=Mock(return_value=fast))
            text = (project / ".factory" / "report.md").read_text(encoding="utf-8")
            self.assertIn("Live updates", text)
            self.assertIn("under 1 ms", text)

    def test_the_session_the_probe_signed_with_never_reaches_the_report(self):
        """A report is pasted into a chat with a buyer; the token it carries would
        open the client's own dashboard as that probe user."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            self._stages(project, "x")
            for name in ("report.json", "report.md"):
                evidence = (project / ".factory" / name).read_text(encoding="utf-8")
                self.assertNotIn("jwt.secret-signing-output", evidence, name)
                self.assertNotIn("FactoryProbe", evidence, name)

    def test_a_static_site_without_a_backend_still_delivers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(Path(tmp) / "site")
            api = Mock()
            with patch.object(factory, "build_project", return_value={"ok": True, "dist": "/tmp"}), \
                 patch.object(factory, "test_backend", return_value={"ok": True}), \
                 patch.object(factory, "run_qa", return_value={"ok": True, "status": "passed"}), \
                 patch("agent.deploy_engine.deploy_backend", api), \
                 patch("agent.deploy_engine.deploy_project", return_value={
                     "status": "live", "verified": True, "url": "https://site.vercel.app"}), \
                 patch("agent.demo_video.generate_demo_video",
                       return_value={"status": "ready", "verified": True}):
                out = factory.run_factory(str(project), deploy="vercel", video=False)
            api.assert_not_called()
            self.assertEqual(out["status"], "delivered", out.get("failures"))
            self.assertEqual(out["stages"]["api"]["status"], "skipped")


    def test_the_frontend_is_rebuilt_with_the_origin_the_api_stage_discovered(self):
        """Stage 1 built before the API existed. A host that publishes the local dist
        would ship a bundle still calling localhost, so the build runs again."""
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            out, calls = self._stages(project, Mock(), api_deploy=Mock(return_value=self.LIVE_API))
            self.assertEqual(out["status"], "delivered", out.get("failures"))
            self.assertEqual(calls["build"].call_count, 2)
            self.assertEqual(calls["build"].call_args_list[1][1]["api_url"], "https://site-api.vercel.app")
            self.assertEqual(calls["frontend"].call_args_list[-1][1]["api_url"],
                             "https://site-api.vercel.app")

    def test_a_rebuild_that_breaks_stops_the_run_before_anything_is_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            builds = Mock(side_effect=[{"ok": True, "dist": "/tmp", "steps": {}},
                                       {"ok": False, "message": "vite exploded"}])
            out, calls = self._stages(project, Mock(), api_deploy=Mock(return_value=self.LIVE_API),
                                     build=builds)
            self.assertEqual(out["status"], "failed", out)
            self.assertIn("rebuild", out["message"])
            calls["frontend"].assert_not_called()

    def test_no_rebuild_happens_when_the_first_build_already_knew_the_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project_with_backend(tmp)
            builds = Mock(return_value={"ok": True, "dist": "/tmp", "steps": {
                "build": {"api_url": "https://site-api.vercel.app"}}})
            out, calls = self._stages(project, Mock(), api_deploy=Mock(return_value=self.LIVE_API),
                                      build=builds)
            self.assertEqual(out["status"], "delivered", out.get("failures"))
            self.assertEqual(calls["build"].call_count, 1)


class NativeBinaryPolicyBlockBuildTests(unittest.TestCase):
    """Windows App Control refusing a freshly installed native bundler binary is an
    environment fact, not a defect in the generated site. The build stage restores an
    accepted copy, retries, and says so — an ordinary compile error still stops the run
    after a single attempt."""

    BLOCKED = ("Error: An Application Control policy has blocked this file.\n\n"
               "\\\\?\\D:\\w\\site\\frontend\\node_modules\\@rollup\\rollup-win32-x64-msvc"
               "\\rollup.win32-x64-msvc.node\n    at Object..node (node:internal/modules/cjs/loader)\n"
               "  code: 'ERR_DLOPEN_FAILED'\n")

    def _frontend(self, root: Path) -> Path:
        frontend = root / "frontend"
        (frontend / "node_modules").mkdir(parents=True)
        (frontend / "package.json").write_text(json.dumps({"scripts": {"build": "vite build"}}),
                                               encoding="utf-8")
        return frontend

    def _build(self, frontend: Path, outcomes, repairs):
        runs = []

        def fake_run(cmd, cwd, timeout=900, env=None):
            runs.append(cmd)
            outcome = outcomes[min(len(runs) - 1, len(outcomes) - 1)]
            if outcome["ok"]:
                dist = Path(cwd) / "dist"
                dist.mkdir(parents=True, exist_ok=True)
                (dist / "index.html").write_text("<html></html>", encoding="utf-8")
            return outcome

        def fake_repair(target, stderr, *, repo_root, exclude=()):
            outcome = repairs[len(asked)] if len(asked) < len(repairs) else {"repaired": False}
            asked.append(outcome)
            return outcome

        asked: list = []
        with patch.object(factory, "_run", side_effect=fake_run), \
             patch.object(factory.nbr, "repair", side_effect=fake_repair):
            return factory.build_project(str(frontend.parent), install=False), runs

    def test_the_build_is_retried_once_the_policy_block_is_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend = self._frontend(Path(tmp))
            swapped = {"repaired": True, "blocked_path": "node_modules/x/y.node",
                       "blocked_version": "4.65.1", "source_version": "4.65.1",
                       "source": str(Path(tmp) / "other" / "y.node")}
            report, runs = self._build(
                frontend,
                [{"ok": False, "code": 1, "stdout_tail": "", "stderr_tail": self.BLOCKED, "elapsed_ms": 1},
                 {"ok": True, "code": 0, "stdout_tail": "built", "stderr_tail": "", "elapsed_ms": 1}],
                [swapped])
            self.assertTrue(report["ok"], report.get("message"))
            self.assertEqual(len(runs), 2)
            self.assertEqual(report["environment_repairs"], [swapped])
            self.assertIn("App Control", report["warnings"][0])

    def test_an_ordinary_build_error_is_never_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend = self._frontend(Path(tmp))
            report, runs = self._build(
                frontend,
                [{"ok": False, "code": 1, "stdout_tail": "", "stderr_tail": "SyntaxError: unmatched )",
                  "elapsed_ms": 1}],
                [{"repaired": False, "status": "not-a-policy-block"}])
            self.assertFalse(report["ok"])
            self.assertEqual(len(runs), 1)
            self.assertEqual(report["environment_repairs"], [])
            self.assertNotIn("warnings", report)

    def test_retries_are_bounded_even_if_every_copy_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            frontend = self._frontend(Path(tmp))
            failing = {"ok": False, "code": 1, "stdout_tail": "", "stderr_tail": self.BLOCKED,
                       "elapsed_ms": 1}
            swaps = [{"repaired": True, "blocked_path": "n.node", "blocked_version": "1",
                      "source_version": "1", "source": f"{tmp}/a{index}.node"}
                     for index in range(4)]
            report, runs = self._build(frontend, [failing], swaps)
            self.assertFalse(report["ok"])
            self.assertEqual(len(runs), factory.nbr.MAX_SWAP_ATTEMPTS + 1)
            self.assertEqual(len(report["environment_repairs"]), factory.nbr.MAX_SWAP_ATTEMPTS)


class BackendDependenciesTests(unittest.TestCase):
    """The generated backend's dependencies used to never be installed, so `npm test`
    ran smoke assertions that import nothing and the database runner died on
    `Cannot find module 'pg'` — a green stage that proved nothing (2026-10-27)."""

    def _backend(self, root: Path, *, with_modules=False, with_tests=True) -> Path:
        backend = root / "backend"
        backend.mkdir(parents=True)
        (backend / "package.json").write_text(json.dumps({"scripts": {"test": "node --test"}}),
                                              encoding="utf-8")
        if with_modules:
            (backend / "node_modules").mkdir()
        if with_tests:
            (backend / "test").mkdir()
            (backend / "test" / "smoke.test.js").write_text("test('ok', () => {});", encoding="utf-8")
        return backend

    def _run_stage(self, backend: Path, outcomes):
        calls = []

        def fake_run(cmd, cwd, timeout=900, env=None):
            calls.append((list(cmd), str(cwd), timeout))
            outcome = outcomes[min(len(calls) - 1, len(outcomes) - 1)]
            return {**{"stdout_tail": "", "stderr_tail": "", "elapsed_ms": 1}, **outcome}

        with patch.object(factory, "_run", side_effect=fake_run):
            return factory.test_backend(str(backend.parent)), calls

    def test_dependencies_are_installed_before_the_generated_tests_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp))
            report, calls = self._run_stage(backend, [{"ok": True, "code": 0}])
            self.assertTrue(report["ok"], report)
            self.assertIn("install", calls[0][0])
            self.assertEqual(calls[0][1], str(backend))
            self.assertIn("test", calls[1][0])
            self.assertTrue(report["steps"]["install"]["ok"])

    def test_an_install_failure_fails_the_stage_instead_of_testing_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp))
            report, calls = self._run_stage(
                backend, [{"ok": False, "code": 1, "stderr_tail": "npm ERR! 401"}])
            self.assertFalse(report["ok"])
            self.assertIn("npm install", report["message"])
            self.assertEqual(len(calls), 1)

    def test_an_existing_install_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp), with_modules=True)
            report, calls = self._run_stage(backend, [{"ok": True, "code": 0}])
            self.assertTrue(report["ok"], report)
            self.assertEqual(len(calls), 1)
            self.assertIn("test", calls[0][0])

    def test_a_backend_with_no_test_files_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp), with_tests=False)
            report, calls = self._run_stage(backend, [{"ok": True, "code": 0}])
            self.assertFalse(report["ok"])
            self.assertIn("no test files", report["message"])
            self.assertEqual(calls, [])

    def test_a_dependency_tree_is_not_mistaken_for_the_projects_own_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp), with_tests=False, with_modules=True)
            nested = backend / "node_modules" / "some-dep" / "test"
            nested.mkdir(parents=True)
            (nested / "dep.test.js").write_text("x", encoding="utf-8")
            report, calls = self._run_stage(backend, [{"ok": True, "code": 0}])
            self.assertFalse(report["ok"])
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
