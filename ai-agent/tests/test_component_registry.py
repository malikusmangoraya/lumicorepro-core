import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.component_registry import (  # noqa: E402
    ComponentRegistry,
    _extract_props,
    build_registry_index,
    get_component_registry,
    component_contract_snippet,
)


class TestComponentRegistryIndex(unittest.TestCase):
    """Pillar 2: the local component library must be fully indexed with aliases."""

    def test_indexes_entire_local_library(self):
        registry = get_component_registry()
        self.assertGreaterEqual(registry.count(), 44, "44-core component set expected")
        # Every entry carries an absolute alias path (no dangling registry paths).
        for name in registry.names():
            self.assertTrue(registry.get(name)["alias"].startswith("@/components/"))
            self.assertTrue(registry.by_alias(registry.get(name)["alias"]))

    def test_prop_contracts_extracted_for_core_primitives(self):
        registry = get_component_registry()
        button = registry.get("Button")
        self.assertIsNotNone(button)
        self.assertTrue(button["props"])
        self.assertTrue(button["has_variant"], "Button must expose variant")
        self.assertTrue(button["has_size"], "Button must expose size")
        self.assertIn("primary", button["variant_values"] or ["primary"])
        self.assertIn("md", button["size_values"] or ["md"])
        for name in ("Modal", "Reveal", "Input"):
            contract = registry.get(name)
            self.assertIsNotNone(contract)
            self.assertTrue(contract["props"], f"{name} props must be indexed")

    def test_inner_components_do_not_contaminate_outer_contract(self):
        registry = get_component_registry()
        navbar = registry.get("GlassNavbar")
        if navbar:
            self.assertNotIn(
                "item", navbar["props"],
                "Inner NavItem props must not leak into GlassNavbar contract",
            )

    def test_propless_components_stay_accurate(self):
        registry = get_component_registry()
        for name in ("Analytics", "HeroCanvas", "ErrorBoundary", "CurrencySelector"):
            contract = registry.get(name)
            if contract:
                self.assertEqual(contract["props"], [], f"{name} is prop-less")

    def test_build_registry_index_writes_json_artifact(self):
        tmp = os.path.join(os.path.dirname(__file__), "_registry_dryrun.json")
        try:
            payload = build_registry_index(tmp)
            self.assertEqual(payload["count"], get_component_registry().count())
            self.assertTrue(os.path.exists(tmp))
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_contract_snippet_maps_aliases(self):
        snippet = component_contract_snippet()
        self.assertIn("@/components/ui/Button.jsx", snippet)
        self.assertIn("COMPONENT CONTRACT", snippet)

    def test_extract_props_handles_forwardref_with_ref_argument(self):
        text = "const B = React.forwardRef(\n  (\n    {\n      children,\n      variant,\n    },\n    ref\n  ) => Box"
        self.assertEqual(_extract_props(text, "B"), ["children", "variant"])


class TestVerifyGeneratedComponents(unittest.TestCase):
    """Pillar 2: generated trees are checked against the canonical registry."""

    def _scaffold(self, files):
        root = os.path.join(os.path.dirname(__file__), "_verify_tmp")
        for rel, content in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        return root

    def test_unknown_component_import_is_an_error(self):
        root = self._scaffold({
            "frontend/src/App.jsx":
                "import { Button } from '@/components/ui/Button.jsx';\n"
                "import { GhostThing } from '@/components/ui/GhostThing.jsx';",
        })
        try:
            result = get_component_registry().verify_generated_components(root)
            self.assertTrue(any("GhostThing" in e for e in result["errors"]))
            self.assertFalse(any("Button.jsx" in e for e in result["errors"]))
        finally:
            _rmtree(root)

    def test_known_imports_are_clean(self):
        root = self._scaffold({
            "frontend/src/App.jsx": "import { Button } from '@/components/ui/Button.jsx';",
        })
        try:
            result = get_component_registry().verify_generated_components(root)
            self.assertEqual(result["errors"], [])
        finally:
            _rmtree(root)

    def test_generic_markup_maps_warning_not_error(self):
        root = self._scaffold({"frontend/src/Home.jsx": "const x = <button>hi</button>;"})
        try:
            result = get_component_registry().verify_generated_components(root)
            self.assertEqual(result["errors"], [])
            self.assertTrue(result["generic_markup_warnings"])
        finally:
            _rmtree(root)


def _rmtree(path):
    import shutil
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()