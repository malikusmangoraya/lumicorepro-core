import sys
import os
import json
import shutil
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import patch
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.orchestrator import AgentOrchestrator
from agent.security_engine import SecurityPostureEngine
from agent.global_deployment import GlobalDeploymentEngine

EMPTY_ENV = {
    "GEMINI_API_KEY": "",
    "DEEPSEEK_API_KEY": "",
    "OPENROUTER_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "MISTRAL_API_KEY": "",
    "OPENAI_API_KEY": "",
    "ACTIVE_AI_PROVIDER": "gemini",
}


@contextmanager
def _blanked_provider_keys():
    """Force offline mode by blanking the module-level key constants.

    The orchestrator resolves provider keys from config.settings/config.providers
    module constants (loaded from .env at import time), so patch.dict(os.environ)
    alone cannot disable AI once real keys exist in .env. Blanking every *_API_KEY
    constant reproduces the original empty-environment contract.
    """
    import config.providers as providers_mod
    import config.settings as settings_mod

    def _blanked(cfg):
        return {name: {**entry, "api_key": ""} for name, entry in cfg.items()}

    blank = {k: "" for k in (vars(providers_mod) | vars(settings_mod)) if k.endswith("_API_KEY")}
    with ExitStack() as stack:
        stack.enter_context(patch.dict(vars(providers_mod), blank))
        stack.enter_context(patch.dict(vars(settings_mod), blank))
        stack.enter_context(
            patch.dict(vars(providers_mod), {"PROVIDER_CONFIGS": _blanked(providers_mod.PROVIDER_CONFIGS)})
        )
        # Blanking keys is not enough on its own: the chain also contains
        # keyless gateways (ninerouter/omniroute), so a provider would still
        # resolve and a real hosted call could be attempted. AI_OFFLINE
        # is the explicit, product-level switch that guarantees no AI call, which
        # is what these offline/determinism tests actually assert.
        stack.enter_context(patch.dict(os.environ, {"AI_OFFLINE": "1"}))
        yield


class _FencedProvider:
    """Stands in for a real model that wraps its answer in a markdown fence.

    Deliberately NOT a BaseAIProvider subclass so the router pins it as an
    explicit hand-injected provider and no network call is ever attempted.
    """

    def __init__(self, reply=None):
        self.reply = reply or (
            "Sure! Here is the updated file:\n\n"
            "```jsx\nexport default function Home() {\n  return null;\n}\n```\n\n"
            "Let me know if you need anything else."
        )

    def modify_code(self, original, instruction):
        return self.reply


class TestIterateEngine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="lumicore-iterate-test-")
        self.project_dir = os.path.join(self._tmp, "acme-site")
        os.makedirs(os.path.join(self.project_dir, "frontend", "src"))
        home = os.path.join(self.project_dir, "frontend", "src", "Home.jsx")
        with open(home, "w", encoding="utf-8") as f:
            f.write(DEFAULT_HOME_JSX)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _orch(self):
        with patch.dict(os.environ, EMPTY_ENV), _blanked_provider_keys():
            return AgentOrchestrator()

    def test_offline_iterate_applies_diff_and_writes_manifest(self):
        with patch.dict(os.environ, EMPTY_ENV):
            orch = self._orch()
        result = orch.iterate(
            project_dir=self.project_dir,
            instruction="change the hero heading text and make the color red",
        )
        self.assertTrue(result["success"], result.get("reason"))
        self.assertEqual(result["version"], 1)
        self.assertTrue(any("Home.jsx" in p for p in result["changed_files"]))
        self.assertGreater(result["added_lines"], 0)

        updated = ""
        home = os.path.join(self.project_dir, "frontend", "src", "Home.jsx")
        with open(home, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertIn("text-red-500", updated)
        self.assertIn("lumicore-edit", updated)

        manifest_path = os.path.join(self.project_dir, ".lumicore", "iterate-manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        manifest = json.load(open(manifest_path, "r", encoding="utf-8"))
        self.assertEqual(manifest["version"], 1)
        self.assertEqual(len(manifest["history"]), 1)
        self.assertIn("provider", manifest["history"][0])

    def test_ordinary_iteration_preserves_design_manifest(self):
        with patch.dict(os.environ, EMPTY_ENV), _blanked_provider_keys():
            orch = self._orch()
        design_manifest = os.path.join(self.project_dir, "design-manifest.json")
        original = b'{"design_signature":{"fingerprint":"stable"}}\n'
        with open(design_manifest, "wb") as manifest_file:
            manifest_file.write(original)

        result = orch.iterate(
            project_dir=self.project_dir,
            instruction="change the hero heading text",
        )

        self.assertTrue(result["success"], result.get("reason"))
        self.assertEqual(result["design_update"]["intent"], "preserve_existing")
        self.assertEqual(result["design_update"]["source"], "design_manifest")
        with open(design_manifest, "rb") as manifest_file:
            self.assertEqual(manifest_file.read(), original)

    def test_update_without_manifest_records_source_inferred_preservation(self):
        stylesheet = os.path.join(self.project_dir, "frontend", "src", "design-system.css")
        with open(stylesheet, "w", encoding="utf-8") as css_file:
            css_file.write('.ds-site[data-scaffold="wide_immersive"] { --hero: 88vh; }')

        orch = self._orch()
        result = orch.iterate(self.project_dir, "change the hero heading text")

        self.assertTrue(result["success"], result.get("reason"))
        self.assertEqual(result["design_update"]["intent"], "preserve_existing")
        self.assertEqual(result["design_update"]["source"], "source_inferred")
        with open(stylesheet, "r", encoding="utf-8") as css_file:
            self.assertIn('data-scaffold="wide_immersive"', css_file.read())

    def test_explicit_redesign_is_classified_but_explicit_keep_layout_wins(self):
        from agent.intelligence.design_system_engine import resolve_design_intent

        self.assertEqual(resolve_design_intent({"instruction": "Redesign the layout"}, operation="update"), "redesign_requested")
        self.assertEqual(resolve_design_intent({"instruction": "Redesign but keep the current layout"}, operation="update"), "preserve_existing")

    def test_malformed_design_manifest_is_not_overwritten(self):
        path = os.path.join(self.project_dir, "design-manifest.json")
        original = b'{invalid json\n'
        with open(path, "wb") as manifest_file:
            manifest_file.write(original)

        context = self._orch().iteration_engine._load_existing_design_context(self.project_dir)

        self.assertEqual(context["preservation"], "source_inferred")
        with open(path, "rb") as manifest_file:
            self.assertEqual(manifest_file.read(), original)

    def test_iterate_reruns_verification_and_writes_security_evidence(self):
        with patch.dict(os.environ, EMPTY_ENV):
            orch = self._orch()
        result = orch.iterate(
            project_dir=self.project_dir,
            instruction="change the hero heading text",
        )
        self.assertTrue(result["success"], result.get("reason"))
        self.assertTrue(result["phases_rerun"])

        self.assertTrue(os.path.exists(os.path.join(self.project_dir, "SECURITY-CHECKLIST.md")))
        compliance = os.path.join(self.project_dir, "COMPLIANCE.md")
        self.assertTrue(os.path.exists(compliance))
        with open(compliance, "r", encoding="utf-8") as f:
            self.assertIn("Verification Evidence", f.read())

    def test_iteration_is_deterministic_offline(self):
        # Two pristine copies of the SAME project must produce identical output
        dir_a = os.path.join(self._tmp, "acme-site-a")
        dir_b = os.path.join(self._tmp, "acme-site-b")
        shutil.copytree(self.project_dir, dir_a)
        shutil.copytree(self.project_dir, dir_b)
        # The offline contract must hold for the whole test, not just for
        # orchestrator construction: `.iterate()` resolves the provider lazily,
        # so with the real environment restored it would pick a live provider
        # out of the global pool and two identical runs would diverge.
        with patch.dict(os.environ, EMPTY_ENV), _blanked_provider_keys():
            orch_a = self._orch()
            orch_b = self._orch()
            first = orch_a.iterate(dir_a, "change the hero heading text and make it red")
            second = orch_b.iterate(dir_b, "change the hero heading text and make it red")
            with open(os.path.join(dir_a, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
                content_a = f.read()
            with open(os.path.join(dir_b, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
                content_b = f.read()
        self.assertTrue(first["success"], first.get("reason"))
        self.assertTrue(second["success"], second.get("reason"))
        self.assertEqual(content_a, content_b)
        # Deterministic patch = no AI used
        self.assertFalse(first["ai_used"])
        self.assertFalse(second["ai_used"])
        # Offline rules must never leak markdown fences into a source file.
        self.assertNotIn("```", content_a)


    def test_fenced_model_reply_never_corrupts_source(self):
        """A real model that wraps its reply in ```jsx must not write the fence.

        Regression: the AI branch of `_patch_file` used to persist the reply
        verbatim, so a fenced answer left `Home.jsx` unable to compile.
        `AI_OFFLINE` stays off here on purpose (that is the other test); the
        injected stub is pinned by the router, so no network call is made.
        """
        with patch.dict(os.environ, EMPTY_ENV):
            orch = self._orch()
            orch.iteration_engine.provider = _FencedProvider()
            result = orch.iterate(
                project_dir=self.project_dir, instruction="rewrite the hero section"
            )
        self.assertTrue(result["success"], result.get("reason"))
        home = os.path.join(self.project_dir, "frontend", "src", "Home.jsx")
        with open(home, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertNotIn("```", updated)
        self.assertNotIn("Here is the updated file", updated)
        self.assertIn("export default function Home", updated)

    def test_unparsable_fenced_reply_falls_back_offline(self):
        """Fence markers that survive unwrapping must be refused, not persisted."""
        with patch.dict(os.environ, EMPTY_ENV):
            orch = self._orch()
            orch.iteration_engine.provider = _FencedProvider(
                reply="Here you go:\n```jsx\nunclosed fence and no home component\n"
            )
            result = orch.iterate(
                project_dir=self.project_dir, instruction="change the hero heading text"
            )
        self.assertTrue(result["success"], result.get("reason"))
        home = os.path.join(self.project_dir, "frontend", "src", "Home.jsx")
        with open(home, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertNotIn("```", updated)
        self.assertIn("export default function Home", updated)


class TestSecurityPostureEngine(unittest.TestCase):
    def test_generates_checklist_and_report(self):
        tmp = tempfile.mkdtemp(prefix="lumicore-sec-test-")
        try:
            engine = SecurityPostureEngine()
            report = engine.generate(spec={"website_type": "ecommerce"}, project_dir=tmp)
            self.assertGreater(report.get("controls_verified", 0), 0)
            self.assertTrue(os.path.exists(os.path.join(tmp, "SECURITY-CHECKLIST.md")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCostEstimator(unittest.TestCase):
    def test_estimate_running_cost(self):
        engine = GlobalDeploymentEngine()
        result = engine.estimate_running_cost("ecommerce", "medium", has_payments=True)
        self.assertIn("estimates", result)
        self.assertIn("vercel", result["estimates"])
        self.assertIn("monthly_usd", result["estimates"]["vercel"])
        self.assertTrue(result["recommended_for_type"])


DEFAULT_HOME_JSX = """export default function Home() {
  return (
    <div className="text-primary">
      <h1>Build Your Future</h1>
      <p>Reach us: support@example.com</p>
      <a href="mailto:support@example.com">Contact</a>
    </div>
  );
}
"""


if __name__ == "__main__":
    unittest.main()