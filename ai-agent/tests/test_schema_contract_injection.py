"""Tests for Database Schema Configuration & Structural Contract (TRD #4).

Covers the 14-model relational baseline, FK-contract verification + the
`Order.coupon_id` structural patch (canonical library stays read-only), the
row-lock checkout concurrency mandate, contract artifacts, and engine wiring
(static runtime → N/A, enterprise → conformant).
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.schema_contract_injection import (
    schema_contract_injector,
    MODEL_BASELINE,
)
from agent.project_mode_engine import (
    ProjectModeEngine,
    MODE_ENTERPRISE,
)

MARKER = "LUMICORE_SCHEMA"

INDEX_JS = """\
import { sequelize } from '../config/database.js';
import User from './User.js';
import Product from './Product.js';
import Order from './Order.js';
import Payment from './Payment.js';
import Review from './Review.js';
import Notification from './Notification.js';
import Category from './Category.js';
import Cart from './Cart.js';
import CartItem from './CartItem.js';
import Wishlist from './Wishlist.js';
import Subscription from './Subscription.js';
import AnalyticsEvent from './AnalyticsEvent.js';
import Coupon from './Coupon.js';
import Address from './Address.js';

User.hasMany(Order, { foreignKey: 'user_id', as: 'orders' });
User.hasMany(Payment, { foreignKey: 'user_id', as: 'payments' });
User.hasMany(Review, { foreignKey: 'user_id', as: 'reviews' });
User.hasMany(Notification, { foreignKey: 'recipient_id', as: 'notifications' });
User.hasOne(Cart, { foreignKey: 'user_id', as: 'cart' });
User.hasMany(Wishlist, { foreignKey: 'user_id', as: 'wishlists' });
User.hasMany(Subscription, { foreignKey: 'user_id', as: 'subscriptions' });
User.hasMany(AnalyticsEvent, { foreignKey: 'user_id', as: 'analyticsEvents' });
User.hasMany(Address, { foreignKey: 'user_id', as: 'addresses' });
User.hasMany(Coupon, { foreignKey: 'user_id', as: 'coupons' });
Product.belongsTo(Category, { foreignKey: 'category_id', as: 'category' });
Product.belongsTo(User, { foreignKey: 'vendor_id', as: 'vendor' });
Product.hasMany(Review, { foreignKey: 'product_id', as: 'reviews' });
Product.hasMany(CartItem, { foreignKey: 'product_id', as: 'cartItems' });
Product.hasMany(Wishlist, { foreignKey: 'product_id', as: 'wishlists' });
Category.hasMany(Product, { foreignKey: 'category_id', as: 'products' });
Order.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Order.belongsTo(Coupon, { foreignKey: 'coupon_id', as: 'coupon' });
Order.hasMany(Payment, { foreignKey: 'order_id', as: 'payments' });
Payment.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Payment.belongsTo(Order, { foreignKey: 'order_id', as: 'order' });
Review.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Review.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Notification.belongsTo(User, { foreignKey: 'recipient_id', as: 'recipient' });
Cart.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Cart.hasMany(CartItem, { foreignKey: 'cart_id', as: 'items' });
CartItem.belongsTo(Cart, { foreignKey: 'cart_id', as: 'cart' });
CartItem.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Wishlist.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Wishlist.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Subscription.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
AnalyticsEvent.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Address.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
"""

MODEL_TEMPLATE = """class {name} extends Model {{}}
{name}.init({{}}, {{ sequelize, modelName: '{name}' }});
export default {name};\n"""

ORDER_NO_COUPON_JS = """\
class Order extends Model {}
Order.init({
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  user_id: { type: DataTypes.INTEGER, allowNull: true },
  createdAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
  },
  updatedAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
  },
}, { sequelize, modelName: 'Order' });
export default Order;
"""

ORDER_WITH_COUPON_JS = ORDER_NO_COUPON_JS.replace(
    "  user_id: { type: DataTypes.INTEGER, allowNull: true },\n",
    "  user_id: { type: DataTypes.INTEGER, allowNull: true },\n"
    "  coupon_id: { type: DataTypes.INTEGER, allowNull: true },\n",
    1,
)

ORDER_SERVICE_LOCKS = """\
export async function createOrder(user, { items }) {
  return sequelize.transaction(async (t) => {
    const product = await Product.findOne({
      where: { id: item.product },
      lock: t.LOCK.UPDATE,
      transaction: t,
    });
    if (!product || product.stock < item.quantity) {
      throw new Error('Insufficient stock');
    }
    await product.update({ stock: product.stock - item.quantity }, { transaction: t });
  });
}
"""


def _write(path, content=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content is not None else "")
    return path


def _read(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as f:
        return f.read()


class _EnterpriseTree:
    """Synthetic generated-backend tree (canonical shapes)."""

    def __init__(self, root, with_order_coupon=True, with_locks=True):
        self.root = root
        b = os.path.join(root, "backend")
        _write(os.path.join(b, "models", "index.js"), INDEX_JS)
        for name in MODEL_BASELINE:
            _write(os.path.join(b, "models", f"{name}.js"), MODEL_TEMPLATE.format(name=name))
        if with_order_coupon:
            _write(os.path.join(b, "models", "Order.js"), ORDER_WITH_COUPON_JS)
        else:
            # simulate canonical copy: Order lacks coupon_id field AND association
            _write(os.path.join(b, "models", "Order.js"), ORDER_NO_COUPON_JS)
            _write(
                os.path.join(b, "models", "index.js"),
                INDEX_JS.replace(
                    "Order.belongsTo(Coupon, { foreignKey: 'coupon_id', as: 'coupon' });\n", ""
                ),
            )
        _write(
            os.path.join(b, "services", "orderService.js"),
            ORDER_SERVICE_LOCKS if with_locks else "export const createOrder = async () => 1;\n",
        )
        self.b = b

    def backend(self, *rel):
        return os.path.join(self.b, *rel)


class SchemaContractTest(unittest.TestCase):
    @staticmethod
    def _spec(website_type="ecommerce"):
        return {"project_name": "trd-test", "website_type": website_type, "project_root": "trd-test"}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="schema_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 1. Model baseline ──────────────────────────────────────────────────
    def test_static_runtime_is_not_applicable(self):
        report = schema_contract_injector.generate(self._spec("portfolio"), self.tmp, "static")
        self.assertFalse(report["applies"])

    def test_missing_models_flagged(self):
        tree = _EnterpriseTree(self.tmp)
        os.remove(tree.backend("models", "Wishlist.js"))
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        self.assertEqual(report["models"]["present"], 13)
        self.assertIn("Wishlist", report["models"]["missing"])
        self.assertFalse(report["models"]["pass"])

    def test_full_baseline_present(self):
        tree = _EnterpriseTree(self.tmp)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        self.assertTrue(report["applies"])
        self.assertEqual(report["models"]["present"], len(MODEL_BASELINE))
        self.assertEqual(report["models"]["missing"], [])

    # ── 2. FK contract ─────────────────────────────────────────────────────
    def test_fk_contract_conformant(self):
        tree = _EnterpriseTree(self.tmp)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        fk = report["fk"]
        self.assertTrue(fk["pass"])
        self.assertGreater(fk["checked"], 15)
        self.assertEqual(fk["missing"], [])

    def test_fk_gap_flagged(self):
        tree = _EnterpriseTree(self.tmp)
        for line in (
            "Product.belongsTo(Category, { foreignKey: 'category_id', as: 'category' });\n",
            "Category.hasMany(Product, { foreignKey: 'category_id', as: 'products' });\n",
        ):
            idx = _read(tree.backend("models", "index.js")).replace(line, "")
            _write(tree.backend("models", "index.js"), idx)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        self.assertFalse(report["fk"]["pass"])
        self.assertTrue(any("Product.category_id" in m for m in report["fk"]["missing"]))

    # ── 3. Order.coupon_id structural patch ────────────────────────────────
    def test_order_coupon_fk_patched_in_generated_copy(self):
        tree = _EnterpriseTree(self.tmp, with_order_coupon=False)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        self.assertEqual(report["order_coupon_fk"]["status"], "ok")
        self.assertEqual(len(report["order_coupon_fk"]["patched"]), 2)
        order = _read(tree.backend("models", "Order.js"))
        self.assertIn("coupon_id", order)
        self.assertIn(MARKER, order)
        idx = _read(tree.backend("models", "index.js"))
        self.assertIn("Order.belongsTo(Coupon, { foreignKey: 'coupon_id', as: 'coupon' })", idx)
        # FK contract now fully wired
        self.assertTrue(report["fk"]["pass"])

    def test_order_coupon_patch_idempotent(self):
        tree = _EnterpriseTree(self.tmp, with_order_coupon=False)
        schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        before = _read(tree.backend("models", "Order.js"))
        second = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        after = _read(tree.backend("models", "Order.js"))
        self.assertEqual(before, after)
        self.assertEqual(second["order_coupon_fk"]["status"], "no-op")
        # no duplicate association
        idx = _read(tree.backend("models", "index.js"))
        self.assertEqual(idx.count("Order.belongsTo(Coupon"), 1)

    # ── 4. Row-lock concurrency mandate ────────────────────────────────────
    def test_row_lock_mandate_conformant(self):
        tree = _EnterpriseTree(self.tmp)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        rl = report["row_lock"]
        self.assertTrue(rl["pass"])
        self.assertEqual(rl["missing"], [])
        for key, check in rl["checks"].items():
            self.assertTrue(check["pass"], key)

    def test_row_lock_gap_flagged(self):
        tree = _EnterpriseTree(self.tmp, with_locks=False)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        rl = report["row_lock"]
        self.assertFalse(rl["pass"])
        self.assertTrue(any(k in rl["missing"] for k in ("transaction", "row_lock", "atomic_decrement")))

    # ── 5. Contract artifacts ──────────────────────────────────────────────
    def test_contract_artifacts_written(self):
        tree = _EnterpriseTree(self.tmp)
        report = schema_contract_injector.generate(self._spec("ecommerce"), self.tmp, MODE_ENTERPRISE)
        doc = _read(os.path.join(self.tmp, "SCHEMA-CONTRACT.md"))
        self.assertIn("14 relational entities", doc)
        self.assertIn("Foreign-Key Contracts", doc)
        self.assertIn("Order.coupon_id", doc)
        self.assertIn("Row Lock & Concurrency Mandate", doc)
        for name in ("User", "Product", "Order"):
            self.assertIn(f"`{name}` | `", doc)
        sql = _read(os.path.join(self.tmp, "database", "schemas", "schema.sql"))
        self.assertIn("CREATE TABLE IF NOT EXISTS products", sql)
        self.assertIn("FOR UPDATE", sql)
        self.assertIn("tracking_status", sql)
        self.assertIn("price_cents", sql)

    # ── 6. Engine integration ──────────────────────────────────────────────
    def test_render_enterprise_injects_schema_contract(self):
        spec = self._spec("ecommerce")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_ent")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertEqual(report["runtime_mode"], "transactional")
        sc = report["schema_contract"]
        self.assertTrue(sc["applies"])
        # canonical overlay ships the full 14-model baseline + locked order service
        self.assertTrue(sc["models"]["pass"])
        self.assertTrue(sc["fk"]["pass"])
        self.assertTrue(sc["row_lock"]["pass"])
        self.assertTrue(os.path.isfile(os.path.join(root, "SCHEMA-CONTRACT.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "database", "schemas", "schema.sql")))
        # Order.coupon_id patched into the generated copy (canonical lacks it)
        order_model = _read(os.path.join(root, "backend", "models", "Order.js"))
        self.assertIn("coupon_id", order_model)

    def test_render_static_reports_schema_not_applicable(self):
        spec = self._spec("portfolio")
        engine = ProjectModeEngine()
        root = os.path.join(self.tmp, "render_static")
        _write(os.path.join(root, "frontend", "src", "services", ".keep"))
        _write(os.path.join(root, "frontend", "src", "App.jsx"),
               "import React from 'react';\nexport function App() { return <div/>; }\nexport default App;\n")
        _write(os.path.join(root, "frontend", "src", "index.css"), "@tailwind base;\n")
        report = engine.render_layout(root, spec)
        self.assertIn("schema_contract", report)
        self.assertFalse(report["schema_contract"]["applies"])


if __name__ == "__main__":
    unittest.main()