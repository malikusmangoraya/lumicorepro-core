"""Tests — agent/live_verify.py (deployment verification evidence)."""
import json
import queue
import threading
import time
import unittest
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent.live_verify import (
    expected_routes,
    normalize_url,
    verify_api_health,
    verify_api_surface,
    verify_contact_write,
    verify_realtime_feed,
    verify_site,
)


class _Handler(BaseHTTPRequestHandler):
    # Class-level switches so one server can simulate each failure mode.
    mode = "good"
    # A miniature of the generated backend, so the proofs are tested against the
    # contract the shipped routes actually implement: users, their rows, the
    # tokens issued, and the frames the change feed has queued for its stream.
    users: dict = {}
    rows: dict = {}
    tokens: dict = {}
    frames: queue.Queue = queue.Queue()
    stream_query = ""

    @classmethod
    def reset_store(cls):
        cls.users, cls.rows, cls.tokens = {}, {}, {}
        cls.frames = queue.Queue()
        cls.stream_query = ""

    def log_message(self, *_args):
        pass

    def do_GET(self):  # noqa: N802 — http.server API
        mode = type(self).mode
        path = self.path.split("?")[0]
        if mode.startswith(("surface", "feed")):
            return self._surface_get(self.path)
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
        if mode.startswith(("surface", "feed")):
            return self._surface_post(self.path)
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

    def do_PUT(self):  # noqa: N802 — http.server API
        if type(self).mode.startswith(("surface", "feed")):
            return self._surface_put(self.path)
        return self._send(405, "method not allowed", "text/plain")

    def do_DELETE(self):  # noqa: N802 — http.server API
        if type(self).mode.startswith(("surface", "feed")):
            return self._surface_delete(self.path)
        return self._send(405, "method not allowed", "text/plain")

    # -- the miniature generated backend ------------------------------------
    # Each `surface-*` / `feed-*` mode breaks exactly one of the claims
    # verify_api_surface() and verify_realtime_feed() have to make, so a test
    # fails when a proof stops looking at the thing it is named for.

    def _json(self, status, payload):
        self._send(status, json.dumps(payload), "application/json")

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            return json.loads(raw) or {}
        except ValueError:
            return {}

    def _subject(self):
        auth = self.headers.get("Authorization") or ""
        token = auth[7:] if auth.startswith("Bearer ") else ""
        return type(self).tokens.get(token)

    def _owned_rows(self, user_id):
        return [row for row in type(self).rows.values() if row["userId"] == user_id]

    def _surface_get(self, full_path):
        mode = type(self).mode
        path = full_path.split("?")[0]
        user = self._subject()
        if path == "/api/v1/events":
            return self._stream(full_path)
        if path == "/api/v1/records":
            if mode == "surface-open":
                user = user or {"id": "anyone"}  # a guard that never guarded
            if not user:
                return self._json(401, {"success": False, "message": "Login required"})
            if mode == "surface-no-list":
                return self._json(500, {"success": False, "message": "db down"})
            rows = [] if mode == "surface-no-readback" else self._owned_rows(user["id"])
            return self._json(200, {"success": True, "data": rows})
        if path.startswith("/api/v1/records/"):
            row = type(self).rows.get(path.rsplit("/", 1)[1])
            if row and user and row["userId"] != user["id"]:
                # Another tenant's row: readable only on the broken mode.
                if mode != "surface-idor":
                    return self._json(404, {"success": False, "message": "Not found"})
                return self._json(200, {"success": True, "data": row})
            if not row or not user:
                return self._json(404, {"success": False, "message": "Not found"})
            return self._json(200, {"success": True, "data": row})
        return self._json(404, {"success": False, "message": "no route"})

    def _surface_post(self, full_path):
        mode = type(self).mode
        path = full_path.split("?")[0]
        body = self._body()
        if mode == "surface-down":
            return self._json(500, {"success": False, "message": "db down"})
        if path == "/api/v1/auth/register":
            email = str(body.get("email", ""))
            if not body.get("name") or "@" not in email or len(str(body.get("password", ""))) < 8:
                return self._json(400, {"success": False, "message": "Missing fields"})
            if mode == "surface-no-second-user" and type(self).users:
                return self._json(500, {"success": False, "message": "db down"})
            if email in type(self).users:
                return self._json(409, {"success": False, "code": "EMAIL_TAKEN"})
            user = {"id": f"user-{len(type(self).users) + 1}", "name": body["name"], "email": email}
            type(self).users[email] = user
            token = f"tok-{user['id']}"
            type(self).tokens[token] = user
            if mode == "surface-no-token":
                return self._json(201, {"success": True, "user": user})
            return self._json(201, {"success": True, "token": token, "user": user})
        if path == "/api/v1/auth/login":
            user = type(self).users.get(str(body.get("email", "")))
            if not user:
                return self._json(401, {"success": False, "message": "Invalid credentials"})
            token = f"tok-{user['id']}"
            type(self).tokens[token] = user
            if mode == "surface-no-token":
                return self._json(200, {"success": True, "user": user})
            return self._json(200, {"success": True, "token": token, "user": user})
        if path == "/api/v1/records":
            user = self._subject()
            if not user:
                return self._json(401, {"success": False, "message": "Login required"})
            if mode == "surface-no-create":
                return self._json(500, {"success": False, "message": "db down"})
            if not str(body.get("title", "")).strip() and mode != "surface-no-validation":
                return self._json(422, {"success": False, "code": "VALIDATION_ERROR"})
            row = {"id": f"row-{len(type(self).rows) + 1}", "title": str(body.get("title", "")),
                   "userId": user["id"], "status": body.get("status", "draft"),
                   "updatedAt": "2026-10-27T09:00:00.000Z"}
            type(self).rows[row["id"]] = row
            type(self).frames.put({"id": row["id"], "feed": "records", "at": row["updatedAt"]})
            return self._json(201, {"success": True, "data": row})
        return self._json(404, {"success": False, "message": "no route"})

    def _surface_put(self, full_path):
        path = full_path.split("?")[0]
        user = self._subject()
        row = type(self).rows.get(path.rsplit("/", 1)[1])
        if not user:
            return self._json(401, {"success": False, "message": "Login required"})
        if not row or (row["userId"] != user["id"] and type(self).mode != "surface-idor"):
            return self._json(404, {"success": False, "message": "Not found"})
        if type(self).mode == "surface-no-update":
            return self._json(500, {"success": False, "message": "db down"})
        row.update({key: value for key, value in self._body().items() if key in {"title", "status"}})
        return self._json(200, {"success": True, "data": row})

    def _surface_delete(self, full_path):
        path = full_path.split("?")[0]
        row_id = path.rsplit("/", 1)[1]
        user = self._subject()
        row = type(self).rows.get(row_id)
        if not user:
            return self._json(401, {"success": False, "message": "Login required"})
        if not row or (row["userId"] != user["id"] and type(self).mode != "surface-idor"):
            return self._json(404, {"success": False, "message": "Not found"})
        if type(self).mode == "surface-no-delete":
            return self._json(500, {"success": False, "message": "db down"})
        type(self).rows.pop(row_id)
        return self._json(200, {"success": True, "data": {"deleted": 1}})

    def _frame(self, fields):
        self.wfile.write("".join(f"{key}: {value}\n" for key, value in fields.items()).encode() + b"\n")
        self.wfile.flush()

    def _stream(self, full_path):
        mode = type(self).mode
        query = urllib.parse.parse_qs(full_path.split("?")[1] if "?" in full_path else "")
        token = (query.get("token") or [""])[0]
        # Recorded so a test can pin the transport an EventSource is able to use:
        # the credential has to arrive in the query string, never a header.
        type(self).stream_query = full_path.partition("?")[2]
        if mode == "feed-unauthorized" or token not in type(self).tokens:
            return self._json(401, {"success": False, "message": "Login required"})
        if mode == "feed-not-stream":
            return self._json(200, {"success": True, "data": []})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.end_headers()
        if mode == "feed-closed":
            return
        self._frame({"retry": "3000"})
        if mode != "feed-no-ready":
            self._frame({"id": "2026-10-27T09:00:00.000Z", "event": "ready",
                         "data": json.dumps({"ok": True, "feeds": ["record:changed"]})})
        # A subscription belongs to one connection: bind the queue now, or a stream
        # a previous test abandoned would drain this one's frames and the write
        # would never arrive.
        subscribed = type(self).frames
        stop_at = time.time() + 20
        while time.time() < stop_at:
            try:
                signal = subscribed.get(timeout=0.2)
            except queue.Empty:
                continue
            if mode == "feed-no-event":
                continue
            if mode == "feed-slow":
                time.sleep(1.2)  # past the caller's event budget
            if mode == "feed-pii":
                signal = {**signal, "email": "buyer@example.test", "message": "private body"}
            try:
                self._frame({"id": "2026-10-27T09:00:01.000Z", "event": "record:changed",
                             "data": json.dumps(signal)})
            except OSError:
                return  # the client hung up; a real feed stops pushing here

    def _send(self, status, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _mint_token(base: str) -> str:
    """Register through the fixture's own auth route and return its token."""
    body = json.dumps({"name": "Feed probe", "email": "feed-probe@test",
                       "password": "FactoryProbe!2026"}).encode()
    request = urllib.request.Request(base + "/api/v1/auth/register", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return str(json.loads(response.read().decode())["token"])


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


class EndpointSurfaceProofTests(unittest.TestCase):
    """`db: connected` plus one form is not "the API works".

    A client demo walks the dashboard: sign in, list, create, edit, delete. Every
    one of those is a separate generated route, and each has shipped broken on its
    own, so `delivered` now has to answer each one over the public origin.
    """

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

    def setUp(self):
        _Handler.reset_store()

    def _check(self, mode):
        _Handler.mode = mode
        return verify_api_surface(self.base, timeout=4, poll_interval=0.2)

    def test_every_generated_endpoint_answers_to_a_real_client(self):
        result = self._check("surface")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "verified")
        for label in ("POST /api/v1/auth/register", "POST /api/v1/auth/login",
                      "GET /api/v1/records", "POST /api/v1/records",
                      "GET /api/v1/records/:id", "PUT /api/v1/records/:id",
                      "DELETE /api/v1/records/:id"):
            self.assertIn(label, result["proven"], result["proven"])
        # The proof signs in as two different tenants, so a leaked row is caught.
        self.assertIn("second tenant cannot read the row", result["proven"])
        self.assertIn("records are unreachable without a token", result["proven"])
        self.assertEqual(_Handler.rows, {}, "the probe must leave no demo data behind")
        self.assertEqual(result["leftovers"], [])

    def test_a_backend_that_never_boots_is_not_an_api(self):
        result = self._check("surface-down")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "auth-failed")

    def test_an_auth_that_hands_back_no_token_proves_nothing(self):
        result = self._check("surface-no-token")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "auth-failed")

    def test_a_list_route_that_errors_is_a_broken_dashboard(self):
        result = self._check("surface-no-list")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "list-failed")

    def test_a_create_that_errors_never_reaches_the_database(self):
        result = self._check("surface-no-create")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "create-failed")

    def test_a_write_that_is_never_read_back_is_not_stored(self):
        """A 201 and an id only prove the process answered; the row has to come
        back out of Postgres on the next list, or the client's save is a lie."""
        result = self._check("surface-no-readback")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "read-back-failed")

    def test_an_update_that_errors_is_a_broken_edit(self):
        result = self._check("surface-no-update")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "update-failed")

    def test_a_delete_that_errors_leaves_the_demo_dirty(self):
        result = self._check("surface-no-delete")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "delete-failed")
        self.assertEqual(len(result["leftovers"]), 1)

    def test_records_reachable_without_a_token_is_a_security_failure(self):
        result = self._check("surface-open")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "auth-not-enforced")

    def test_a_row_another_tenant_can_read_is_a_security_failure(self):
        result = self._check("surface-idor")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "tenant-isolation-broken")
        self.assertIn(result["leftovers"], ([], ["row-1"]))

    def test_an_endpoint_that_stores_an_empty_title_is_not_a_demo(self):
        result = self._check("surface-no-validation")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "validation-not-enforced")

    def test_an_unprovable_second_tenant_is_not_a_pass(self):
        """Isolation cannot be claimed when a second account cannot be created:
        an unproven guardrail ships as an unproven guardrail, never as verified."""
        result = self._check("surface-no-second-user")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "tenant-isolation-unproven")
        self.assertNotIn("records are unreachable without a token", result["proven"])

    def test_a_local_path_is_refused_before_any_request(self):
        result = verify_api_surface(r"D:/Git", timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target-invalid")

    def test_each_product_gets_its_own_probe_identity(self):
        """Two delivered projects sharing one hosted database must not share the
        probe user, or the second one reads the first one's rows."""
        from agent.live_verify import probe_email_for

        self.assertNotEqual(probe_email_for("https://shipsignal-api.vercel.app"),
                            probe_email_for("https://ledgerline-api.vercel.app"))
        self.assertIn("shipsignal", probe_email_for("https://shipsignal-api.vercel.app"))
        self.assertEqual(probe_email_for("https://acme.test").split("@")[0], "factory-probe.owner")
        self.assertEqual(probe_email_for("https://acme.test", tag="other").split("@")[0],
                         "factory-probe.other")

    def test_the_probe_credential_never_appears_in_the_evidence(self):
        result = self._check("surface")
        self.assertNotIn("FactoryProbe", json.dumps(result))
        self.assertTrue(result["probe"]["email"].startswith("factory-probe."))


class RealtimeFeedProofTests(unittest.TestCase):
    """The dashboard badge that says "Live updates" is a claim, so it gets proven."""

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

    def setUp(self):
        _Handler.reset_store()
        _Handler.mode = "surface"
        # A token minted straight from the fixture's own auth route: what the
        # feed proof needs is a credential the shipped backend accepts.
        self.token = _mint_token(self.base)

    def _check(self, mode, **kwargs):
        _Handler.mode = mode
        args = {"timeout": 6, "event_timeout": 3}
        args.update(kwargs)
        return verify_realtime_feed(self.base, self.token, **args)

    def test_a_write_on_an_open_stream_arrives_as_an_event(self):
        result = self._check("feed")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "verified")
        self.assertIn("record:changed", result["events"])
        self.assertLessEqual(result["latency_ms"], 3000)
        self.assertEqual(_Handler.rows, {}, "the feed probe must clean up after itself")

    def test_the_token_travels_as_a_query_parameter(self):
        # An EventSource cannot set headers, so a feed that only accepted Bearer
        # would be invisible to the shipped client.
        self._check("feed")
        self.assertIn("token=", _Handler.stream_query)

    def test_a_stream_that_closes_before_ready_is_not_a_feed(self):
        result = self._check("feed-closed")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no-stream")

    def test_an_endpoint_that_answers_json_is_not_a_stream(self):
        result = self._check("feed-not-stream")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "not-event-stream")

    def test_a_stream_that_never_says_ready_is_not_a_feed(self):
        result = self._check("feed-no-ready", timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no-ready")

    def test_a_write_that_never_becomes_an_event_is_a_dead_feed(self):
        result = self._check("feed-no-event", event_timeout=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no-event")
        self.assertEqual(_Handler.rows, {})

    def test_a_feed_that_lags_is_not_live(self):
        """A frame that arrives after the budget is a dashboard that updates late
        while the badge still says Live — the bound is the claim."""
        result = self._check("feed-slow", event_timeout=0.4)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "no-event")
        self.assertIn("budget 400 ms", result["failures"][0])

    def test_a_feed_that_demands_a_token_says_so(self):
        result = self._check("feed-unauthorized")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "unauthorized")

    def test_the_feed_never_carries_customer_text(self):
        """The signal is an id and a timestamp; rows are refetched with the
        tenant's own scoped read. A frame carrying an email means the feed is
        broadcasting other people's inquiries."""
        result = self._check("feed-pii")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "pii-in-feed")

    def test_a_local_path_is_refused_before_any_request(self):
        result = verify_realtime_feed(r"D:/Git", self.token, timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target-invalid")

    def test_an_empty_token_is_named_instead_of_sent(self):
        result = verify_realtime_feed(self.base, "", timeout=2)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "target-invalid")
        self.assertIn("token", result["failures"][0])


if __name__ == "__main__":
    unittest.main()
