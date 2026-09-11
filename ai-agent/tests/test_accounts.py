import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from database.accounts_store import AccountStore


class TestAccountStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-accounts-")
        db = os.path.join(self.tmp, "platform.db")
        self.store = AccountStore(path=db)
        self.dup_db = db

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_user_returns_key_once_and_resolves(self):
        user = self.store.create_user("test@example.com", "Test User")
        self.assertTrue(user["api_key"])
        self.assertEqual(user["email"], "test@example.com")
        resolved = self.store.resolve_api_key(user["api_key"])
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["email"], "test@example.com")

    def test_email_lowercased_and_required(self):
        user = self.store.create_user("  Foo@Bar.com ")
        self.assertEqual(user["email"], "foo@bar.com")
        with self.assertRaises(ValueError):
            self.store.create_user("not-an-email")

    def test_wrong_key_rejected(self):
        self.assertIsNone(self.store.resolve_api_key("nope"))

    def test_duplicate_email_raises(self):
        self.store.create_user("dup@example.com")
        with self.assertRaises(Exception):
            self.store.create_user("DUP@example.com")

    def test_projects_roundtrip(self):
        user = self.store.create_user("owner@example.com")
        p1 = self.store.create_project(user["id"], "My Store", "ecommerce", "run-abc")
        # Same name for same user is ignored → returns existing row
        p2 = self.store.create_project(user["id"], "My Store", "ecommerce", "run-xyz")
        self.assertEqual(p1["id"], p2["id"])
        projects = self.store.list_projects(user["id"])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["run_id"], "run-abc")

    def test_project_unknown_user_raises(self):
        with self.assertRaises(ValueError):
            self.store.create_project("ghost", "X")

    def test_credits_topup_spend_refund_roundtrip(self):
        user = self.store.create_user("credits@example.com")
        self.store.topup(user["id"], 5.0)
        self.assertEqual(self.store.get_credits(user["id"])["credits_balance"], 5.0)
        self.assertTrue(self.store.spend(user["id"], 1.0, run_id="r1"))
        bal = self.store.get_credits(user["id"])
        self.assertEqual(bal["credits_balance"], 4.0)
        self.assertEqual(bal["credits_used"], 1.0)
        self.assertTrue(self.store.refund(user["id"], 1.0, run_id="r1", reason="failed"))
        self.assertEqual(self.store.get_credits(user["id"])["credits_balance"], 5.0)

    def test_spend_insufficient_balance_rejected(self):
        user = self.store.create_user("poor@example.com")
        self.assertFalse(self.store.spend(user["id"], 1.0))
        self.assertEqual(self.store.get_credits(user["id"])["credits_balance"], 0.0)

    def test_refund_unreserved_noop(self):
        user = self.store.create_user("nomatch@example.com")
        self.assertFalse(self.store.refund(user["id"], 1.0))
        self.assertEqual(self.store.get_credits(user["id"])["credits_used"], 0.0)

    def test_deployment_flow(self):
        user = self.store.create_user("deploy@example.com")
        d = self.store.create_deployment(user["id"], "Acme Store", run_id="run-1")
        self.assertEqual(d["status"], "preparing")
        self.assertTrue(d["deploy_url"].startswith("https://acme-store."))
        self.assertEqual(d["slug"], "acme-store")
        # Same name twice → unique slug
        d2 = self.store.create_deployment(user["id"], "Acme Store", run_id="run-2")
        self.assertNotEqual(d["slug"], d2["slug"])
        # Promote + list
        live = self.store.promote_deployment(d["id"], "live")
        self.assertEqual(live["status"], "live")
        listed = self.store.list_deployments(user["id"])
        self.assertEqual(len(listed), 2)

    def test_deployment_requires_name(self):
        user = self.store.create_user("deploy2@example.com")
        with self.assertRaises(ValueError):
            self.store.create_deployment(user["id"], "  ")


class TestAccountsEndpoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-accounts-api-")
        from fastapi.testclient import TestClient
        import server as srv

        # Isolate the account store + disable run-store persistence noise
        self._orig_accounts = srv._accounts
        srv._accounts = AccountStore(path=os.path.join(self.tmp, "platform.db"))
        self._orig_api_key = srv._AGENT_API_KEY
        srv._AGENT_API_KEY = ""  # keep endpoint tests open; X-API-KEY still gates /me + projects
        self.client = TestClient(srv.app)
        self._srv = srv

    def tearDown(self):
        self._srv._accounts = self._orig_accounts
        self._srv._AGENT_API_KEY = self._orig_api_key
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_register_me_and_project_flow(self):
        r = self.client.post("/api/accounts/register", json={"email": "api@example.com", "display_name": "API"})
        self.assertEqual(r.status_code, 200, r.text)
        key = r.json()["data"]["api_key"]
        headers = {"X-API-KEY": key}

        me = self.client.get("/api/accounts/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["data"]["user"]["email"], "api@example.com")

        self.client.post("/api/accounts/register", json={"email": "run@example.com", "display_name": "R"})
        run_key = self.client.post(
            "/api/accounts/register", json={"email": "run2@example.com", "display_name": "R2"}
        ).json()["data"]["api_key"]

        proj = self.client.post(
            "/api/accounts/projects",
            headers={"X-API-KEY": run_key},
            json={"project_name": "Acme", "website_type": "saas", "run_id": "run-123"},
        )
        self.assertEqual(proj.status_code, 200, proj.text)
        self.assertEqual(proj.json()["data"]["run_id"], "run-123")

    def test_me_requires_valid_key(self):
        self.assertEqual(self.client.get("/api/accounts/me", headers={"X-API-KEY": "bad"}).status_code, 401)

    def test_register_validates_email(self):
        r = self.client.post("/api/accounts/register", json={"email": "nope"})
        self.assertEqual(r.status_code, 422)

    def test_duplicate_register_conflict(self):
        self.client.post("/api/accounts/register", json={"email": "same@example.com"})
        r = self.client.post("/api/accounts/register", json={"email": "same@example.com"})
        self.assertEqual(r.status_code, 409)

    def test_credits_endpoint_flow(self):
        key = self.client.post(
            "/api/accounts/register", json={"email": "rich@example.com", "display_name": "R"}
        ).json()["data"]["api_key"]
        headers = {"X-API-KEY": key}

        bal0 = self.client.get("/api/accounts/credits", headers=headers)
        self.assertEqual(bal0.json()["data"]["credits_balance"], 0.0)

        topup = self.client.post("/api/accounts/credits/topup", headers=headers, json={"amount": 10})
        self.assertEqual(topup.status_code, 200, topup.text)
        self.assertEqual(topup.json()["data"]["credits_balance"], 10.0)

        bad = self.client.get("/api/accounts/credits", headers={"X-API-KEY": "nope"})
        self.assertEqual(bad.status_code, 401)

    def test_deployment_endpoints(self):
        key = self.client.post(
            "/api/accounts/register", json={"email": "deployapi@example.com", "display_name": "D"}
        ).json()["data"]["api_key"]
        headers = {"X-API-KEY": key}

        r = self.client.post(
            "/api/accounts/deployments", headers=headers,
            json={"project_name": "My SaaS", "run_id": "run-9"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["data"]["slug"], "my-saas")

        listed = self.client.get("/api/accounts/deployments", headers=headers)
        self.assertEqual(len(listed.json()["data"]["deployments"]), 1)

        denied = self.client.get("/api/accounts/deployments", headers={"X-API-KEY": "nope"})
        self.assertEqual(denied.status_code, 401)


class TestPreviewEndpoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-preview-")
        self.agent_tmp = tempfile.mkdtemp(prefix="lumicore-agent-tmp-")
        from fastapi.testclient import TestClient
        import server as srv

        self._orig_accounts = srv._accounts
        self._orig_api_key = srv._AGENT_API_KEY
        self._orig_previews = srv._previews

        srv._accounts = AccountStore(path=os.path.join(self.agent_tmp, "platform.db"))
        srv._AGENT_API_KEY = ""
        srv._previews = {}

        # Fake a finished run with a generated project dir
        project_dir = os.path.join(self.tmp, "acme-store")
        os.makedirs(os.path.join(project_dir, "frontend", "public"))
        with open(os.path.join(project_dir, "frontend", "public", "index.html"), "w", encoding="utf-8") as f:
            f.write("<h1>Acme Live</h1>")
        with open(os.path.join(project_dir, "frontend", "public", "about.html"), "w", encoding="utf-8") as f:
            f.write("<h1>About Acme</h1>")
        with open(os.path.join(project_dir, "SECRET.md"), "w", encoding="utf-8") as f:
            f.write("sensitive")

        run_id = "run-preview-1"
        srv._runs[run_id] = {
            "status": "done",
            "result": {"project_name": "Acme Store", "generated_project_dir": project_dir},
        }
        self.client = TestClient(srv.app)
        self._srv = srv
        self.run_id = run_id
        self.project_dir = project_dir

    def tearDown(self):
        self._srv._accounts = self._orig_accounts
        self._srv._AGENT_API_KEY = self._orig_api_key
        self._srv._previews = self._orig_previews
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.agent_tmp, ignore_errors=True)

    def test_preview_register_and_serve(self):
        r = self.client.post("/api/preview", json={"run_id": self.run_id})
        self.assertEqual(r.status_code, 200, r.text)
        slug = r.json()["data"]["slug"]
        self.assertEqual(slug, "acme-store")

        page = self.client.get(f"/preview/{slug}")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Acme Live", page.text)

        nested = self.client.get(f"/preview/{slug}/about")
        self.assertEqual(nested.status_code, 200)
        self.assertIn("About Acme", nested.text)

        missing = self.client.get(f"/preview/{slug}/nope")
        self.assertEqual(missing.status_code, 404)

    def test_preview_prefers_built_dist_over_public(self):
        dist = os.path.join(self.project_dir, "frontend", "dist")
        os.makedirs(dist, exist_ok=True)
        with open(os.path.join(dist, "index.html"), "w", encoding="utf-8") as f:
            f.write('<html><body id="built-app">Built Dist Live</body></html>')
        r = self.client.post("/api/preview", json={"run_id": self.run_id})
        self.assertEqual(r.status_code, 200, r.text)
        slug = r.json()["data"]["slug"]
        page = self.client.get(f"/preview/{slug}")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Built Dist Live", page.text)

    def test_sandbox_endpoint_mount_tree(self):
        import json as _json
        project_dir = os.path.join(self.tmp, "sb-project")
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        with open(os.path.join(project_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write(_json.dumps({"name": "sb-project", "scripts": {"dev": "vite"}}))
        with open(os.path.join(project_dir, "src", "App.jsx"), "w", encoding="utf-8") as f:
            f.write("export default () => <h1>Hi</h1>;")
        run_id = "run-sandbox-1"
        self._srv._runs[run_id] = {
            "status": "done",
            "result": {"generated_project_dir": project_dir},
        }
        r = self.client.get(f"/api/sandbox/{run_id}")
        self.assertEqual(r.status_code, 200, r.text)
        tree = r.json()["data"]["mount_tree"]
        self.assertIn("package.json", tree)
        self.assertIn("src", tree)
        self.assertIn("App.jsx", tree["src"]["directory"])
        self.assertIn("contents", tree["src"]["directory"]["App.jsx"]["file"])

    def test_preview_rejects_unfinished_and_traversal(self):
        unfinished = "run-x"
        self._srv._runs[unfinished] = {"status": "queued", "result": None}
        r = self.client.post("/api/preview", json={"run_id": unfinished})
        self.assertEqual(r.status_code, 409)

        ok = self.client.post("/api/preview", json={"run_id": self.run_id}).json()["data"]["slug"]
        evil = self.client.get(f"/preview/{ok}/../../../SECRET.md")
        self.assertIn(evil.status_code, (404, 400))


if __name__ == "__main__":
    unittest.main()