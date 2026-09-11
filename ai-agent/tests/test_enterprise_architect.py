"""Tests for the Enterprise Project Architect gate (project-rules cross-reference).

Covers: pulling the five canonical specs, the 4-point verification protocol
(PRD scope / engineering standards / design tokens / schema+SRS), routing
violating files to self-healing, blocking ZIP compilation, and the orchestrator
wiring.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.enterprise_architect import enterprise_architect, REQUIRED_SPEC_FILES


def _write(path, content=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content is not None else "")
    return path


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


_APP_JSX = """\
import React from 'react';
import './index.css';

export function App() {
  return (
    <div className="min-h-screen">
      <h1>Hello</h1>
    </div>
  );
}

export default App;
"""

# seo_automation-flavored 7-type structured data (the quality gate tops it up).
_STRUCTURED_DATA_JS = """\
export const organizationSchema = { '@context': 'https://schema.org', '@type': 'Organization' };
export const websiteSchema = { '@context': 'https://schema.org', '@type': 'WebSite' };
export const productSchema = () => ({ '@type': 'Product' });
export const offerSchema = () => ({ '@type': 'Offer' });
export const aggregateRatingSchema = () => ({ '@type': 'AggregateRating' });
export const breadcrumbSchema = () => ({ '@type': 'BreadcrumbList' });
export const faqSchema = () => ({ '@type': 'FAQPage' });
"""

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>App</title>
</head>
<body><div id="root"></div></body>
</html>
"""

_MODEL_TMPL = """const {{ DataTypes }} = require('sequelize');
const sequelize = require('../config/db');
const {name}} = sequelize.define('{{lower}}', {{ id: {{ type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true }} }});
module.exports = {name}};
"""

_ORDER_JS = """const { DataTypes } = require('sequelize');
const sequelize = require('../config/db');
const Order = sequelize.define('Order', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  user_id: { type: DataTypes.INTEGER, allowNull: false },
  total_amount: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
  tracking_status: { type: DataTypes.STRING, allowNull: false, defaultValue: 'pending' },
  createdAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
  },
});
module.exports = Order;
"""

_ORDER_SERVICE_JS = """\
const { sequelize, Product, Order } = require('../models');

async function checkout(userId, items) {
  return sequelize.transaction(async (t) => {
    for (const item of items) {
      const product = await Product.findByPk(item.productId, {
        transaction: t,
        lock: t.LOCK.UPDATE,
      });
      if (!product || product.stock < item.quantity) {
        throw new Error('insufficient stock');
      }
      await product.decrement({ stock: item.quantity }, { transaction: t });
    }
    await Order.create({ userId }, { transaction: t });
  });
}

module.exports = { checkout };
"""

_REDIS_CLIENT_JS = """\
const { createClient } = require('redis');
const memory = { data: new Map(), isMemory: true };
const client = process.env.REDIS_URL ? createClient({ url: process.env.REDIS_URL }) : memory;
module.exports = client;
"""

_QUEUE_SERVICE_JS = """\
const redis = require('../cache/redis.client');
const queue = { isMemory: true };
async function dispatch(job) {
  if (redis.isMemory) { return runInProcess(job); }
  throw new Error('no broker');
}
module.exports = { queue, dispatch };
"""


class _CompliantTree:
    """Builds a generated enterprise project passing all four verification points."""

    MODELS = [
        "User", "Product", "Order", "Payment", "Cart", "CartItem", "Review",
        "Wishlist", "Address", "Coupon", "Subscription", "Notification",
        "AnalyticsEvent", "Category",
    ]

    def __init__(self, root, layout_mode="enterprise"):
        self.root = root
        self.spec = {
            "project_name": "arch-gate",
            "website_type": "ecommerce",
            "layout_mode": layout_mode,
            "runtime_mode": "transactional" if layout_mode == "enterprise" else "static",
        }
        self._scaffold_frontend()
        if self.spec["runtime_mode"] == "transactional":
            self._scaffold_backend()
        self._run_injectors()

    def _scaffold_frontend(self):
        src = os.path.join(self.root, "frontend", "src")
        _write(os.path.join(self.root, "frontend", "package.json"),
               '{"name": "arch-gate", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}, "devDependencies": {"vite": "^5.4.0", "tailwindcss": "^3.4.1"}}')
        _write(os.path.join(src, "index.css"), "@tailwind base;\n@tailwind utilities;\n")
        _write(os.path.join(src, "App.jsx"), _APP_JSX)
        _write(os.path.join(src, "config", "structured-data.js"), _STRUCTURED_DATA_JS)
        _write(os.path.join(self.root, "frontend", "index.html"), _INDEX_HTML)
        _write(os.path.join(src, "components", "common", "Button.jsx"),
               "export default function Button() { return <button className=\"bg-primary\">Go</button>; }\n")
        _write(os.path.join(src, "pages", "HomePage.jsx"),
               "export default function HomePage() { return <h1>Welcome</h1>; }\n")

    def _scaffold_backend(self):
        backend = os.path.join(self.root, "backend")
        models = os.path.join(backend, "models")
        for name in self.MODELS:
            lower = name.lower() + "s"
            _write(os.path.join(models, name + ".js"),
                   _MODEL_TMPL.replace("{name}", name).replace("{lower}", lower))
        # Order fixture lacks coupon_id (structural gap the injector patches).
        _write(os.path.join(models, "Order.js"), _ORDER_JS)
        _write(os.path.join(models, "index.js"), self._index_js())
        _write(os.path.join(backend, "config", "db.js"),
               "const { Sequelize } = require('sequelize');\n"
               "module.exports = new Sequelize(process.env.DATABASE_URL);\n")
        _write(os.path.join(backend, "controllers", "user.controller.js"),
               "exports.getProfile = (req, res) => res.status(200).json({ success: true, data: {} });\n")
        _write(os.path.join(backend, "utils", "response.js"),
               "exports.status = (res, code, data) => res.status(code).json(data);\n")
        _write(os.path.join(backend, "middleware", "errorHandler.js"),
               "module.exports = (err, req, res, next) => res.status(err.status || 500).json({ success: false });\n")
        _write(os.path.join(backend, "services", "orderService.js"), _ORDER_SERVICE_JS)
        _write(os.path.join(backend, "services", "cache", "redis.client.js"), _REDIS_CLIENT_JS)
        _write(os.path.join(backend, "services", "queue", "queue.service.js"), _QUEUE_SERVICE_JS)

    def _index_js(self):
        lines = [
            "const { Sequelize, DataTypes } = require('sequelize');",
            "const sequelize = require('../config/db');",
        ]
        for name in self.MODELS:
            lines.append(f"const {name} = require('./{name}.js');")
        lines.append("")
        fks = [
            ("Product", "category_id", "Category"),
            ("Product", "vendor_id", "User"),
            ("Order", "user_id", "User"),
            ("Payment", "user_id", "User"),
            ("Payment", "order_id", "Order"),
            ("Cart", "user_id", "User"),
            ("CartItem", "cart_id", "Cart"),
            ("CartItem", "product_id", "Product"),
            ("Review", "user_id", "User"),
            ("Review", "product_id", "Product"),
            ("Wishlist", "user_id", "User"),
            ("Wishlist", "product_id", "Product"),
            ("Address", "user_id", "User"),
            ("Coupon", "user_id", "User"),
            ("Subscription", "user_id", "User"),
            ("Notification", "recipient_id", "User"),
            ("AnalyticsEvent", "user_id", "User"),
        ]
        for child, column, parent in fks:
            lines.append(f"{child}.belongsTo({parent}, {{ foreignKey: '{column}' }});")
        lines.append("Order.hasMany(Payment, { foreignKey: 'order_id', as: 'payments' });")
        lines.append("module.exports = { sequelize, " + ", ".join(self.MODELS) + " };")
        return "\n".join(lines) + "\n"

    def _run_injectors(self):
        from agent.generation_matrix import default_matrix
        from agent.platform_injection import platform_injection
        from agent.design_system_injection import design_system_injector
        from agent.schema_contract_injection import schema_contract_injector
        from agent.functional_compliance import functional_compliance
        from agent.component_injection import inject_component_imports

        mode = self.spec["layout_mode"]
        default_matrix.generate(self.spec, self.root, mode)
        platform_injection.generate(self.spec, self.root, mode)
        design_system_injector.generate(self.spec, self.root, mode)
        schema_contract_injector.generate(self.spec, self.root, mode)
        functional_compliance.generate(self.spec, self.root, mode)
        inject_component_imports(self.root)

    def src_path(self, *rel):
        return os.path.join(self.root, "frontend", "src", *rel)


class EnterpriseArchitectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="arch_")
        self.tree = _CompliantTree(os.path.join(self.tmp, "proj"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _enforce(self, **kwargs):
        return enterprise_architect.enforce(self.tree.root, self.tree.spec, **kwargs)

    # ── Phase A: pull + read the project-rules specs ────────────────────────
    def test_load_rules_loaded_with_anchors(self):
        docs = enterprise_architect.load_rules()
        self.assertTrue(docs["all_present"])
        self.assertEqual(docs["loaded"], 5)
        for name in REQUIRED_SPEC_FILES:
            self.assertTrue(docs["files"][name]["loaded"])
            self.assertTrue(all(docs["files"][name]["anchors"].values()), name)

    def test_anchors_present_in_every_doc(self):
        for name in REQUIRED_SPEC_FILES:
            self.assertGreaterEqual(len(enterprise_architect.load_rules()["files"][name]["anchors"]), 2)

    def test_missing_rules_block_build(self):
        rules_dir = os.path.join(self.tmp, "empty-rules")
        os.makedirs(rules_dir)
        report = self._enforce(rules_dir=rules_dir)
        self.assertFalse(report["passed"])
        self.assertTrue(report["blocked_zip"])
        self.assertIn("source-of-truth", report["reason"])

    # ── Compliant project passes all four points ────────────────────────────
    def test_compliant_enterprise_passes(self):
        report = self._enforce()
        self.assertTrue(report["passed"], report["reason"])
        self.assertFalse(report["blocked_zip"])
        self.assertEqual(report["violating_files"], [])
        for point in report["verification"].values():
            self.assertTrue(point["pass"], f"{point['name']} red: {point['checks']}")

    def test_static_runtime_backend_not_applicable(self):
        tree = _CompliantTree(os.path.join(self.tmp, "static"), layout_mode="static")
        report = enterprise_architect.enforce(tree.root, tree.spec)
        bb = report["verification"]["engineering"]["checks"]["backend_blueprint"]
        self.assertFalse(bb["applies"])
        self.assertTrue(bb["pass"])
        self.assertTrue(report["passed"])

    # ── Point 1: PRD scope ──────────────────────────────────────────────────
    def test_prd_scope_red_on_missing_matrix_doc(self):
        os.remove(os.path.join(self.tree.root, "GENERATION-MATRIX.md"))
        report = self._enforce()
        self.assertFalse(report["verification"]["prd"]["pass"])
        self.assertIn("GENERATION-MATRIX.md", report["violating_files"])

    # ── Point 2: engineering standards ──────────────────────────────────────
    def test_engineering_pin_red_on_downgrade(self):
        pkg_path = os.path.join(self.tree.root, "frontend", "package.json")
        pkg = json.loads(_read(pkg_path))
        pkg["dependencies"]["react"] = "^18.2.0"
        pkg["dependencies"]["react-dom"] = "^18.2.0"
        _write(pkg_path, json.dumps(pkg))
        report = self._enforce()
        self.assertFalse(report["verification"]["engineering"]["pass"])
        self.assertFalse(report["verification"]["engineering"]["checks"]["stack_pins"]["pass"])

    # ── Point 3: design tokens ──────────────────────────────────────────────
    def test_design_raw_hex_red(self):
        bad = self.tree.src_path("components", "common", "Button.jsx")
        _write(bad, _read(bad) + "\nconst t = { color: '#ff0000' };\n")
        report = self._enforce()
        design = report["verification"]["design"]
        self.assertFalse(design["pass"])
        self.assertFalse(design["checks"]["raw_hex"]["pass"])
        self.assertTrue(any("Button.jsx" in f for f in report["violating_files"]))

    # ── Point 4: schema contract + SRS ──────────────────────────────────────
    def test_schema_baseline_red_on_missing_model(self):
        os.remove(os.path.join(self.tree.root, "backend", "models", "Wishlist.js"))
        report = self._enforce()
        schema_srs = report["verification"]["schema_srs"]
        self.assertFalse(schema_srs["pass"])
        self.assertFalse(schema_srs["checks"]["baseline"]["pass"])
        self.assertTrue(any("Wishlist.js" in f for f in report["violating_files"]))

    def test_schema_fk_red_on_missing_coupon(self):
        index_path = os.path.join(self.tree.root, "backend", "models", "index.js")
        content = _read(index_path).replace("foreignKey: 'coupon_id'", "foreignKey: 'couponx'")
        _write(index_path, content)
        report = self._enforce()
        self.assertFalse(report["verification"]["schema_srs"]["checks"]["fk_contract"]["pass"])

    def test_srs_jsonld_red_on_gap(self):
        os.remove(self.tree.src_path("config", "structured-data.js"))
        report = self._enforce()
        self.assertFalse(report["verification"]["schema_srs"]["checks"]["jsonld"]["pass"])

    def test_srs_headings_red_on_multiple_h1(self):
        _write(self.tree.src_path("pages", "HomePage.jsx"),
               "export default function P() { return <><h1>A</h1><h1>B</h1></>; }\n")
        report = self._enforce()
        self.assertFalse(report["verification"]["schema_srs"]["checks"]["headings"]["pass"])

    # ── Docs-as-rule-engine (spec-lockfile.json) ────────────────────────────
    def test_schema_rule_lockfile_present_and_pass_on_compliant_tree(self):
        report = self._enforce()
        checks = report["verification"]["schema_srs"]["checks"]
        self.assertIn("rule_lockfile", checks)
        rule_lockfile = checks["rule_lockfile"]
        self.assertTrue(rule_lockfile["pass"], rule_lockfile["detail"])
        self.assertTrue(report["passed"])

    def test_schema_rule_lockfile_red_on_broken_multitenancy(self):
        models = os.path.join(self.tree.root, "backend", "models")
        index_path = os.path.join(models, "index.js")
        content = _read(index_path).rstrip("\n")
        content += "\nProduct.belongsTo(Organization, { foreignKey: 'org_id' });\n"
        _write(index_path, content)
        _write(os.path.join(models, "Organization.js"), "module.exports = {};\n")
        _write(os.path.join(models, "Membership.js"), "module.exports = {};\n")
        # No requireOrg middleware -> multitenancy rule must go red.
        report = self._enforce()
        schema_srs = report["verification"]["schema_srs"]
        self.assertFalse(schema_srs["pass"])
        self.assertFalse(schema_srs["checks"]["rule_lockfile"]["pass"])
        self.assertTrue(any("middleware" in f for f in report["violating_files"]))

    # ── Self-healing loop routes violations (strict constraint) ─────────────
    def test_self_heal_routes_and_repasses(self):
        bad = self.tree.src_path("components", "common", "Button.jsx")
        _write(bad, _read(bad) + "\nconst t = { color: '#00ffff' };\n")
        pkg_path = os.path.join(self.tree.root, "frontend", "package.json")
        pkg = json.loads(_read(pkg_path))
        pkg["dependencies"]["react"] = "^18.2.0"
        pkg["dependencies"]["react-dom"] = "^18.2.0"
        _write(pkg_path, json.dumps(pkg))

        def heal(project_dir, files):
            healed = 0
            for rel in files:
                path = os.path.join(project_dir, rel)
                if not os.path.isfile(path):
                    continue
                content = _read(path)
                if rel.endswith((".jsx", ".js")) and "components/" in rel:
                    cleaned = re.sub(r"#[0-9a-fA-F]{3,8}\b", "var(--t-primary)", content)
                    if cleaned != content:
                        _write(path, cleaned)
                        healed += 1
                elif rel.endswith("package.json"):
                    data = json.loads(content)
                    data["dependencies"]["react"] = "^19.2.0"
                    data["dependencies"]["react-dom"] = "^19.2.0"
                    _write(path, json.dumps(data))
                    healed += 1
            return healed

        report = self._enforce(self_heal=heal, max_rounds=2)
        self.assertTrue(report["passed"], report["reason"])
        self.assertFalse(report["blocked_zip"])
        self.assertGreaterEqual(len(report["self_heal_rounds"]), 1)
        self.assertGreaterEqual(report["self_heal_rounds"][0]["healed"], 2)
        self.assertTrue(any("Button.jsx" in f for f in report["self_heal_rounds"][0]["files"]))


class ArchitectGateWiringTest(unittest.TestCase):
    """Proves the orchestrator policy method works against the real module."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="arch_wire_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_orchestrator_gate_method(self):
        from agent.orchestrator import AgentOrchestrator

        stub = object.__new__(AgentOrchestrator)
        calls = {"n": 0}

        def heal(project_dir, offenders):
            calls["n"] += 1
            return len(offenders or [])
        stub._self_heal_generated = heal

        tree = _CompliantTree(os.path.join(self.tmp, "ok"))
        report = stub._architect_enterprise_gate(tree.root, tree.spec)
        self.assertIsInstance(report, dict)
        self.assertTrue(report["passed"])
        self.assertFalse(report["blocked_zip"])

        bad = os.path.join(tree.root, "frontend", "src", "components", "common", "Button.jsx")
        _write(bad, _read(bad) + "\nconst x = '#123456';\n")
        blocked = stub._architect_enterprise_gate(tree.root, tree.spec)
        self.assertFalse(blocked["passed"])
        self.assertTrue(blocked["blocked_zip"])
        self.assertGreaterEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()