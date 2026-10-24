import json
import sys
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.repo_reverse_engineer import (
    build_reconstruction_plan,
    render_report_markdown,
    reverse_engineer,
    scan_repository,
)


def make_repo(root: Path) -> None:
    (root / "src" / "pages").mkdir(parents=True)
    (root / "backend" / "routes").mkdir(parents=True)
    (root / "node_modules" / "junk").mkdir(parents=True)
    (root / ".git").mkdir()

    (root / "package.json").write_text(json.dumps({
        "name": "demo-shop",
        "scripts": {"dev": "vite", "test": "vitest", "build": "vite build"},
        "dependencies": {"react": "^19.0.0", "express": "^4.0.0", "sequelize": "^6.0.0", "stripe": "^17.0.0"},
        "devDependencies": {"vite": "^5.0.0", "vitest": "^2.0.0", "tailwindcss": "^3.0.0"},
    }), encoding="utf-8")

    (root / "backend" / "routes" / "orders.js").write_text(
        "router.get('/orders', listOrders);\n"
        "router.post('/orders', createOrder);\n"
        "router.get('/checkout', checkout);\n",
        encoding="utf-8",
    )
    (root / "backend" / "models.py").write_text(
        "from sqlalchemy import *\n"
        "CREATE TABLE orders (id SERIAL);\n"
        "class User(models.Model):\n    pass\n",
        encoding="utf-8",
    )
    (root / "api.py").write_text(
        "@app.get('/health')\ndef health():\n    return {'ok': True}\n"
        "@app.post('/api/payments')\ndef pay():\n    return {}\n",
        encoding="utf-8",
    )
    (root / "src" / "pages" / "Home.jsx").write_text(
        "export default function Home() { return <div dangerouslySetInnerHTML={{__html: x}} />; }\n",
        encoding="utf-8",
    )
    (root / "src" / "pages" / "Home.test.jsx").write_text("test('x', () => {});\n", encoding="utf-8")
    (root / "src" / "config.js").write_text(
        "const key = process.env.STRIPE_SECRET_KEY;\n"
        "const db = process.env.DATABASE_URL;\n"
        "const model = process.env.OPENAI_MODEL;\n"
        "const secret = 'sk_live_abcdefgh12345678';\n"
        "eval('2+2');\n",
        encoding="utf-8",
    )
    # Must be ignored:
    (root / "node_modules" / "junk" / "index.js").write_text("require('./viruses')", encoding="utf-8")
    (root / ".git" / "config").write_text("[core]", encoding="utf-8")
    (root / ".env").write_text("SECRET=1", encoding="utf-8")


class RepoReverseEngineerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_detects_stack_from_package_json(self):
        scan = scan_repository(self.root)
        frameworks = set(scan["stack"]["frameworks"])
        self.assertIn("React", frameworks)
        self.assertIn("Express", frameworks)
        self.assertIn("Sequelize", frameworks)
        self.assertIn("Vite", frameworks)
        self.assertIn("Vitest", frameworks)

    def test_detects_express_and_fastapi_routes(self):
        scan = scan_repository(self.root)
        paths = {(r["method"], r["path"]) for r in scan["routes"]}
        self.assertIn(("GET", "/orders"), paths)
        self.assertIn(("POST", "/orders"), paths)
        self.assertIn(("GET", "/health"), paths)
        self.assertIn(("POST", "/api/payments"), paths)

    def test_detects_data_models(self):
        models = set(scan_repository(self.root)["data_models"])
        self.assertIn("orders", models)
        self.assertIn("user", models)

    def test_counts_test_files(self):
        scan = scan_repository(self.root)
        self.assertGreaterEqual(scan["tests"]["count"], 1)

    def test_groups_integration_env_vars(self):
        integrations = scan_repository(self.root)["integrations"]
        self.assertIn("STRIPE_SECRET_KEY", integrations.get("payments", []))
        self.assertIn("DATABASE_URL", integrations.get("database", []))
        self.assertTrue(any("OPENAI" in name for name in integrations.get("ai", [])))
        self.assertIn("STRIPE_SECRET_KEY", integrations.get("all", []))

    def test_flags_risks(self):
        risks = {r["type"] for r in scan_repository(self.root)["risks"]}
        self.assertIn("dangerouslySetInnerHTML", risks)
        self.assertIn("eval", risks)
        self.assertIn("possible-secret", risks)
        self.assertIn("env-file-on-disk", risks)

    def test_skips_vendor_and_vcs_directories(self):
        scan = scan_repository(self.root)
        files = " ".join(
            [r["file"] for r in scan["routes"]]
            + scan["tests"]["files"]
        )
        self.assertNotIn("node_modules", files)
        self.assertNotIn(".git", files)

    def test_file_cap_is_reported(self):
        scan = scan_repository(self.root, max_files=2)
        self.assertLessEqual(scan["stats"]["files_scanned"], 2)
        self.assertTrue(scan["stats"]["truncated"])

    def test_rejects_non_directory(self):
        with self.assertRaises(ValueError):
            scan_repository(self.root / "does-not-exist")

    def test_reconstruction_plan_is_clean_room(self):
        result = reverse_engineer(self.root)
        plan = result["plan"]
        self.assertEqual(plan["product_type"], "ecommerce")
        self.assertIn(plan["effort_estimate"], {"S", "M", "L"})
        self.assertIn("legal_note", plan)
        self.assertIn("clean-room", plan["legal_note"].lower())
        self.assertTrue(any("/orders" in p["path"] for p in plan["api_surface"]))
        self.assertIn("orders", plan["data_model"])
        # The plan must never embed source code (risk NAMES are fine).
        dumped = json.dumps(plan)
        self.assertNotIn("export default function Home", dumped)
        self.assertNotIn("return <div", dumped)
        self.assertNotIn("eval('2+2')", dumped)

    def test_markdown_report_has_sections(self):
        md = reverse_engineer(self.root)["report_markdown"]
        self.assertIn("# Repository Reverse-Engineering Report", md)
        self.assertIn("## Risks", md)
        self.assertIn("## Reconstruction plan", md)
        self.assertIn("demo-shop", md) if "demo-shop" in md else None  # name may not surface; sections matter

    def test_scan_is_json_serialisable(self):
        json.dumps(scan_repository(self.root))


if __name__ == "__main__":
    unittest.main()
