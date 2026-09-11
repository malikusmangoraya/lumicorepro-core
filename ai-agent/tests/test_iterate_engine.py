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
        yield


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
        with patch.dict(os.environ, EMPTY_ENV):
            orch_a = self._orch()
            orch_b = self._orch()
        first = orch_a.iterate(dir_a, "change the hero heading text and make it red")
        second = orch_b.iterate(dir_b, "change the hero heading text and make it red")
        self.assertTrue(first["success"], first.get("reason"))
        self.assertTrue(second["success"], second.get("reason"))
        with open(os.path.join(dir_a, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
            content_a = f.read()
        with open(os.path.join(dir_b, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
            content_b = f.read()
        self.assertEqual(content_a, content_b)
        # Deterministic patch = no AI used
        self.assertFalse(first["ai_used"])
        self.assertFalse(second["ai_used"])


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