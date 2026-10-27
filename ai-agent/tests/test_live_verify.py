"""Tests — agent/live_verify.py (deployment verification evidence)."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent.live_verify import expected_routes, normalize_url, verify_api_health, verify_contact_write, verify_site


class _Handler(BaseHTTPRequestHandler):
    # Class-level switches so one server can simulate each failure mode.
    mode = "good"

    def log_message(self, *_args):
        pass

    def do_GET(self):  # noqa: N802 — http.server API
        mode = type(self).mode
        path = self.path.split("?")[0]
        if mode in {"good", "api-baked"}:
            if path == "/":
                body = (
                    "<!doctype html><html><head><title>Acme Cloud</title></head>"
                    "<body><div id=\"root\"></div><script src=\"/assets/app.js\"></script>"
                    "<link rel=\"stylesheet\" href=\"/assets/app.css\"></body></html>"
                )
                return self._send(200, body, "text/html")
            if path in {"/assets/app.js", "/assets/app.css"}:
                if mode == "api-baked" and path.endswith(".js"):
                    return self._send(200, 'const a="https://api.acme.test/api/v1"', "application/javascript")
                return self._send(200, "body{}", "application/javascript")
            if path in {"/api/health", "/api/v1/health"}:
                return self._send(200, json.dumps({"status": "healthy", "db": "connected"}), "application/json")
            if path in {"/features", "/pricing"}:
                return self._send(200, "<html><head><title>Acme</title></head><body><div id=\"root\"></div></body></html>", "text/html")
            return self._send(404, "not found", "text/plain")
        if mode == "no-shell":
            return self._send(200, "<html><head><title>Acme</title></head><body>hello</body></html>", "text/html")
        if mode == "platform":
            return self._send(200, "<html><head><title>Login – Vercel</title></head><body>vercel.com/login</body></html>", "text/html")
        if mode == "raw-css":
            if path == "/":
                return self._send(200, "<html><head><title>Acme</title></head><body><div id=\"root\"></div><link rel=\"stylesheet\" href=\"/assets/app.css\"></body></html>", "text/html")
            return self._send(200, "@tailwind base;@tailwind components;@tailwind utilities;", "text/css")
        if mode == "broken-assets":
            if path == "/":
                return self._send(200, "<html><head><title>Acme</title></head><body><div id=\"root\"></div><script src=\"/assets/missing.js\"></script></body></html>", "text/html")
            return self._send(404, "missing", "text/plain")
        if mode == "bad-api":
            if path == "/":
                return self._send(200, "<html><head><title>Acme</title></head><body><div id=\"root\"></div></body></html>", "text/html")
            return self._send(200, json.dumps({"status": "unhealthy"}), "application/json")
        if mode == "api-db-down":
            # A 503 with the database named: the process is up, Postgres is not.
            return self._send(503, json.dumps({"status": "degraded", "db": "disconnected"}), "application/json")
        if mode == "api-static":
            # The old generated health route: pretty JSON, zero queries.
            return self._send(200, json.dumps({"status": "healthy", "uptime": 12}), "application/json")
        if mode == "api-not-json":
            return self._send(200, "<html><head><title>Vercel</title></head><body>Application error</body></html>", "text/html")
        if mode == "api-login-wall":
            # Exactly what a project with "Require Vercel Authentication" answers
            # with: HTTP 200, HTML, and no sign that an API exists behind it.
            return self._send(200, "<html><body>Protected by Vercel Authentication"
                                   "To access this deployment with an authenticated Vercel CLI, "
                                   "run: vercel curl &lt;deployment-url&gt;</body></html>", "text/html")
        if mode == "api-unauthenticated":
            # The other face of the same wall: the short project domain belongs to
            # a different tenant, whose protection answers 400 with JSON that is not
            # a health payload at all.
            return self._send(400, '{"error":{"code":"UNAUTHENTICATED","message":"Authentication required"}}',
                              "application/json")
        return self._send(500, "error", "text/plain")

    def do_POST(self):  # noqa: N802 — http.server API
        mode = type(self).mode
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {}
        if mode == "contact":
            if "/contact" not in self.path:
                return self._send(404, "no route", "text/plain")
            email = str(payload.get("email", ""))
            if "@" not in email or len(str(payload.get("message", ""))) < 10:
                return self._send(422, json.dumps({"success": False, "code": "VALIDATION_ERROR"}), "application/json")
            return self._send(201, json.dumps({"success": True, "data": {"id": "3f9a6c1e-0000-4000-8000-abcdefabcdef"}}), "application/json")
        if mode == "contact-no-id":
            return self._send(201, json.dumps({"success": True, "data": {}}), "application/json")
        if mode == "contact-no-validation":
            return self._send(201, json.dumps({"success": True, "data": {"id": "x"}}), "application/json")
        if mode == "contact-500":
            return self._send(500, json.dumps({"success": False, "message": "db down"}), "application/json")
        return self._send(405, "method not allowed", "text/plain")

    def _send(self, status, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class LiveVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _Handler.mode = "good"

    def test_verified_when_home_assets_routes_and_api_pass(self):
        result = verify_site(
            self.base,
            routes=["/features", "/pricing"],
            marker="Acme Cloud",
            api_health="/api/health",
            timeout=5,
            poll_interval=0.2,
        )
        self.assertTrue(result["verified"])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["title"], "Acme Cloud")
        self.assertEqual(result["checks"]["assets"]["checked"], 2)
        self.assertEqual(result["checks"]["assets"]["ok"], 2)
        self.assertTrue(result["checks"]["api"]["ok"])

    def test_empty_url_is_never_verified(self):
        result = verify_site("", timeout=1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "unreachable")
        self.assertIn("empty or invalid URL", result["failures"][0])

    def test_unreachable_host_reports_unreachable(self):
        result = verify_site("http://127.0.0.1:1", timeout=1, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "unreachable")

    def test_platform_login_page_is_rejected(self):
        _Handler.mode = "platform"
        result = verify_site(self.base, timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "platform-page")

    def test_missing_app_shell_fails(self):
        _Handler.mode = "no-shell"
        result = verify_site(self.base, timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertTrue(any("app shell" in failure for failure in result["failures"]))

    def test_broken_bundle_assets_fail(self):
        _Handler.mode = "broken-assets"
        result = verify_site(self.base, timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "broken-assets")
        self.assertEqual(result["checks"]["assets"]["failed"][0]["status"], 404)

    def test_unprocessed_tailwind_css_is_rejected(self):
        _Handler.mode = "raw-css"
        result = verify_site(self.base, timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "unprocessed-css")
        self.assertEqual(len(result["checks"]["css"]["unprocessed"]), 1)

    def test_bundle_built_without_the_api_origin_is_not_verified(self):
        """Vercel rebuilds from source, so a locally exported VITE_API_URL can be
        missing from what actually ships — and the live site then posts every form
        to the visitor's own localhost while looking perfectly healthy."""
        result = verify_site(self.base, api_origin="https://api.acme.test", timeout=2,
                             poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "api-not-baked")
        self.assertFalse(result["checks"]["api_baked"]["ok"])
        self.assertIn("VITE_API_URL", result["failures"][0])

    def test_bundle_referencing_the_api_origin_passes(self):
        _Handler.mode = "api-baked"
        result = verify_site(self.base, api_origin="https://api.acme.test", timeout=2,
                             poll_interval=0.1)
        self.assertTrue(result["verified"], result["failures"])
        self.assertTrue(result["checks"]["api_baked"]["ok"])

    def test_marker_missing_fails(self):
        result = verify_site(self.base, marker="built-with-lumicorepro", timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "marker-missing")

    def test_degraded_api_health_fails(self):
        _Handler.mode = "bad-api"
        result = verify_site(self.base, api_health="/api/health", timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertFalse(result["checks"]["api"]["ok"])

    def test_a_health_target_that_is_a_local_path_is_named_not_fetched(self):
        """Git Bash rewrites /api/v1/health into D:/Git/api/v1/health and urljoin
        reads the drive letter as a scheme — that run reported "degraded" with no
        hint that the operator's shell, not the deployment, was at fault."""
        result = verify_site(self.base, api_health="D:/Git/api/v1/health", timeout=2, poll_interval=0.1)
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "api-health-target-invalid")
        self.assertFalse(result["checks"]["api"]["ok"])
        self.assertIn("Git Bash", result["failures"][0])

    def test_nothing_but_http_is_ever_fetched(self):
        from agent.live_verify import _fetch

        for target in ("D:/Git/api/v1/health", "\\\\host\\share\\x", "file:///C:/x", "api/health"):
            with self.subTest(target=target):
                result = _fetch(target)
                self.assertFalse(result.ok)
                self.assertEqual(result.status, 0)
                self.assertIn("not an http(s) URL", result.error)

    def test_normalize_url_adds_scheme_and_rejects_junk(self):
        self.assertEqual(normalize_url("example.com"), "https://example.com/")
        self.assertEqual(normalize_url("http://example.com/x"), "http://example.com/x")
        self.assertEqual(normalize_url("   "), "")

    def test_expected_routes_only_lists_pages_that_exist(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp) / "frontend" / "src" / "pages"
            pages.mkdir(parents=True)
            (pages / "Features.jsx").write_text("x")
            (pages / "Contact.jsx").write_text("x")
            routes = expected_routes(tmp)
            self.assertIn("/", routes)
            self.assertIn("/features", routes)
            self.assertIn("/contact", routes)
            self.assertNotIn("/pricing", routes)


class ApiHealthProofTests(unittest.TestCase):
    """`verify_api_health` is what lets a run claim the backend half is live."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def _check(self, mode, path="/api/v1/health"):
        _Handler.mode = mode
        return verify_api_health(f"{self.base}{path}", timeout=4, poll_interval=0.2)

    def test_a_connected_database_is_the_only_thing_that_proves_live(self):
        result = self._check("good")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "verified")

    def test_a_response_that_never_queried_postgres_is_not_proof(self):
        # The retired health route returned {status: healthy} with no SELECT 1,
        # which certified a deployment whose database was dead.
        result = self._check("api-static")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "db-not-proven")
        self.assertIn("db", result["failures"][0])

    def test_a_disconnected_database_is_named_as_the_failure(self):
        result = self._check("api-db-down")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "db-disconnected")
        self.assertIn("database", " ".join(result["failures"]).lower())

    def test_an_html_answer_from_an_api_is_not_a_health_check(self):
        result = self._check("api-not-json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not-json")

    def test_a_vercel_authentication_page_is_named_as_a_wall(self):
        """Reported as `not-json` this looked like a broken backend; the real cause
        is a project setting that hides every URL from the client and the probe."""
        result = self._check("api-login-wall")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "platform-page")
        self.assertIn("login wall", " ".join(result["failures"]).lower())

    def test_another_tenants_protected_domain_is_not_mistaken_for_our_api(self):
        result = self._check("api-unauthenticated")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "platform-page")

    def test_a_wall_is_stopped_instead_of_polled_for_the_whole_budget(self):
        """Protection does not lift by itself, so the probe must not burn 45s on it."""
        _Handler.mode = "api-login-wall"
        result = verify_api_health(f"{self.base}/api/v1/health", timeout=30, poll_interval=0.5)
        self.assertEqual(result["attempts"], 1, result)

    def test_a_local_path_is_refused_before_any_request(self):
        result = verify_api_health(r"D:/Git/api/v1/health", timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target-invalid")

    def test_nothing_listening_is_reported_as_unreachable(self):
        result = verify_api_health("http://127.0.0.1:1/api/v1/health", timeout=2, poll_interval=0.2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unreachable")


class ContactWriteProofTests(unittest.TestCase):
    """A demo is only "full-stack" when a form submission really reaches Postgres."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def _check(self, mode):
        _Handler.mode = mode
        return verify_contact_write(self.base, timeout=6, poll_interval=0.2)

    def test_a_row_id_back_is_the_only_write_proof(self):
        result = self._check("contact")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["id"])

    def test_an_insert_error_is_not_a_working_form(self):
        result = self._check("contact-500")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write-failed")

    def test_a_201_without_an_id_proves_nothing_was_stored(self):
        result = self._check("contact-no-id")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write-unconfirmed")

    def test_a_form_that_accepts_garbage_is_not_a_demo(self):
        result = self._check("contact-no-validation")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "validation-not-enforced")

    def test_a_local_path_is_refused_before_any_post(self):
        result = verify_contact_write(r"D:/Git", timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target-invalid")

    def test_no_route_at_all_is_reported_as_unreachable(self):
        _Handler.mode = "contact-500"
        result = verify_contact_write(f"{self.base}/nope", timeout=3, poll_interval=0.2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write-failed")


if __name__ == "__main__":
    unittest.main()
