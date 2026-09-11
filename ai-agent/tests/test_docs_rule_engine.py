"""Tests for the docs-as-rule-engine (spec-lockfile.json gate)."""
import os
import shutil
import tempfile
import unittest

from agent import docs_rule_engine
from agent.docs_rule_engine import (
    LOCKFILE_NAME,
    build_lockfile,
    extract_rules,
    load_lockfile,
    verify_rules,
)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _mini_tree(root, org=True, rbac=True, middleware=True):
    """Minimal generated backend exercising the schema rule verifiers."""
    models = os.path.join(root, "backend", "models")
    os.makedirs(models, exist_ok=True)
    for name in ("User", "Product"):
        _write(os.path.join(models, name + ".js"), f"const M = require('sequelize'); module.exports = {{ name: '{name}' }};\n")
    lines = [
        "Product.belongsTo(User, { foreignKey: 'user_id' });",
    ]
    if org:
        lines.append("Product.belongsTo(Organization, { foreignKey: 'org_id' });")
        _write(os.path.join(models, "Organization.js"), "module.exports = {};\n")
        _write(os.path.join(models, "Membership.js"), "module.exports = {};\n")
    if rbac:
        _write(os.path.join(models, "Role.js"), "module.exports = {};\n")
        _write(os.path.join(models, "Permission.js"), "module.exports = {};\n")
        lines.append("Role.belongsToMany(Permission, { through: 'role_permissions' });")
    _write(os.path.join(models, "index.js"), "\n".join(lines) + "\n")
    if middleware:
        _write(
            os.path.join(root, "backend", "middleware", "rbac.js"),
            "exports.requireOrg = () => {};\nexports.requirePermission = () => {};\n",
        )
    return root


class DocsRuleEngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="docsrule_")
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def test_extract_rules_finds_multitenancy_and_rbac(self):
        repo_rules = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "project-rules"))
        rules = extract_rules(repo_rules, ["BACKEND_SCHEMA_SPEC.md"])
        ids = {r["id"] for r in rules}
        self.assertIn("multitenancy", ids)
        self.assertIn("rbac", ids)
        self.assertTrue(all(r["mode"] == "required" for r in rules))

    def test_build_lockfile_is_idempotent_and_durable(self):
        rules_dir = os.path.join(self.tmp, "rules")
        _write(os.path.join(rules_dir, "BACKEND_SCHEMA_SPEC.md"),
               "LUMIRULE(scope=schema, id=multitenancy, mode=required)\n")
        lock_path = os.path.join(rules_dir, LOCKFILE_NAME)
        first = build_lockfile(rules_dir, ["BACKEND_SCHEMA_SPEC.md"])
        self.assertTrue(os.path.isfile(lock_path))
        self.assertEqual({r["id"] for r in first["rules"]}, {"multitenancy"})
        self.assertEqual(list(first["model_baseline"]), list(docs_rule_engine.MODEL_BASELINE))
        second = build_lockfile(rules_dir, ["BACKEND_SCHEMA_SPEC.md"])
        self.assertEqual(first["contentHash"], second["contentHash"])
        self.assertEqual(load_lockfile(rules_dir)["contentHash"], first["contentHash"])

    def test_verify_rules_pass_on_consistent_multi_tenant_tree(self):
        tree = _mini_tree(os.path.join(self.tmp, "ok"))
        rules_dir = os.path.join(os.path.dirname(__file__), "..", "..", "project-rules")
        lock = build_lockfile(rules_dir)
        verdicts = {v["id"]: v for v in verify_rules(tree, lock, True)}
        self.assertTrue(verdicts["multitenancy"]["pass"])
        self.assertTrue(verdicts["rbac"]["pass"])

    def test_verify_rules_red_when_scaffold_inconsistent(self):
        def red_case(label, expect_applies, expect_red, kwargs):
            tree = _mini_tree(os.path.join(self.tmp, label), **kwargs)
            verdicts = {v["id"]: v for v in verify_rules(tree, _MINI_LOCK, True)}
            for vid in ("multitenancy", "rbac"):
                self.assertEqual(verdicts[vid]["applies"], expect_applies[vid], f"{vid}.applies [{label}]")
            for vid in ("multitenancy", "rbac"):
                if expect_red.get(vid):
                    self.assertFalse(verdicts[vid]["pass"], f"{vid}.pass [{label}]")

        # Opted into multi-tenancy but no requireOrg/requirePermission middleware.
        red_case("no_middleware", {"multitenancy": True, "rbac": True}, {"multitenancy": True, "rbac": True},
                 {"middleware": False})
        # RBAC opted out entirely -> advisory, not red.
        red_case("no_rbac", {"multitenancy": True, "rbac": False}, {}, {"rbac": False})
        # Multi-tenancy opted out -> advisory, not red.
        red_case("single_tenant", {"multitenancy": False, "rbac": False}, {}, {"org": False, "rbac": False})

    def test_verify_rules_optional_and_unknown_ids_are_advisory(self):
        lock = {
            "rules": [
                {"scope": "schema", "id": "multitenancy", "mode": "optional"},
                {"scope": "schema", "id": "unknown_rule", "mode": "required"},
            ]
        }
        tree = _mini_tree(os.path.join(self.tmp, "x"), middleware=False)
        verdicts = verify_rules(tree, lock, True)
        self.assertTrue(all(v["pass"] for v in verdicts))
        self.assertTrue(all(not v["applies"] for v in verdicts))

    def test_verify_rules_skipped_for_static_runtime(self):
        lock = {"rules": [{"scope": "schema", "id": "multitenancy", "mode": "required"}]}
        tree = _mini_tree(os.path.join(self.tmp, "s"), middleware=False)
        verdicts = verify_rules(tree, lock, False)
        self.assertTrue(verdicts[0]["pass"])
        self.assertFalse(verdicts[0]["applies"])


_MINI_LOCK = {
    "rules": [
        {"scope": "schema", "id": "multitenancy", "mode": "required"},
        {"scope": "schema", "id": "rbac", "mode": "required"},
    ]
}

if __name__ == "__main__":
    unittest.main()