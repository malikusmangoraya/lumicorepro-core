"""Enterprise-lane deterministic repair: canonical models/index.js FK wiring,
multi-tenancy + RBAC middleware — satisfies the architect gate without AI."""
import os
import shutil
import tempfile
import unittest

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.enterprise_repair import repair_transactional_compliance
from agent.schema_contract_injection import FK_CONTRACT

STUB_INDEX = "const User = require('./User');\nmodule.exports = { User };\n"


class TestEnterpriseRepair(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        models = os.path.join(self.tmp, "backend", "models")
        os.makedirs(models)
        for name in ("User", "Product", "Order", "Payment", "Cart", "CartItem", "Review",
                     "Wishlist", "Address", "Coupon", "Subscription", "Notification",
                     "AnalyticsEvent", "Category", "Organization", "Role", "Permission",
                     "Membership"):
            body = (
                "const { DataTypes } = require('sequelize');\nconst { sequelize } = require('../config/database');\n"
                f"const {name} = sequelize.define('{name}', {{ id: {{ type: DataTypes.INTEGER, primaryKey: true }} }});\n"
                f"module.exports = {{ {name} }};\n"
            )
            with open(os.path.join(models, f"{name}.js"), "w") as fh:
                fh.write(body)
        mw = os.path.join(self.tmp, "backend", "middleware")
        os.makedirs(mw)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _stub_index(self):
        with open(os.path.join(self.tmp, "backend", "models", "index.js"), "w") as fh:
            fh.write(STUB_INDEX)

    def test_repair_wires_every_required_fk(self):
        self._stub_index()
        report = repair_transactional_compliance(self.tmp)
        self.assertEqual(report["status"], "ok")
        content = open(os.path.join(self.tmp, "backend", "models", "index.js")).read()
        required = {col for _c, col, parent in FK_CONTRACT if col and parent}
        for column in required:
            self.assertIn(f"foreignKey: '{column}'", content)
        self.assertIn("org_id", content)
        self.assertIn("role_permissions", content)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "backend", "middleware", "org.js")))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "backend", "middleware", "permission.js")))

    def test_repair_is_idempotent(self):
        self._stub_index()
        repair_transactional_compliance(self.tmp)
        first = open(os.path.join(self.tmp, "backend", "models", "index.js")).read()
        second = repair_transactional_compliance(self.tmp)
        self.assertEqual(second["status"], "no-op")
        self.assertFalse(second["patched"])
        self.assertEqual(open(os.path.join(self.tmp, "backend", "models", "index.js")).read(), first)

    def test_conformant_tree_untouched(self):
        self._stub_index()
        repair_transactional_compliance(self.tmp)
        before = open(os.path.join(self.tmp, "backend", "models", "index.js")).read()
        again = repair_transactional_compliance(self.tmp)
        self.assertEqual(open(os.path.join(self.tmp, "backend", "models", "index.js")).read(), before)
        self.assertEqual(again["status"], "no-op")


if __name__ == "__main__":
    unittest.main()