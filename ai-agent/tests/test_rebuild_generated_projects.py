import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.rebuild_generated_projects import (
    _revalidate_previous_results,
    build_rebuild_prompt,
    classify_agent_result,
    discover_projects,
    project_context,
    rebuild_projects,
    safe_project_slug,
    free_provider_allowlist,
)
from config.settings import resolve_generated_projects_dir


class _StubProvider:
    """Stand-in for a configured provider instance."""

    def __init__(self, name):
        self.name = name
        self.provider_name = name


class _FakeOrchestrator:
    """Records what the rebuild wired, without running the real pipeline."""

    instances = []
    output_dir = None

    def __init__(self, provider_name=None):
        type(self).instances.append(self)
        self.provider_name = provider_name
        self.ai_provider = None
        self.ai_provider_name = ""
        self.strict_allowlist_during_run = None
        self.extra_spec = None

    def set_provider(self, provider, name=""):
        self.ai_provider = provider
        self.ai_provider_name = name

    def run(self, prompt, interactive=False, progress_callback=None, extra_spec=None):
        from agent import ai_routing

        self.strict_allowlist_during_run = frozenset(ai_routing.get_router()._strict_allowlist)
        self.extra_spec = extra_spec
        target = type(self).output_dir
        (target / "frontend").mkdir(parents=True, exist_ok=True)
        (target / "frontend" / "package.json").write_text("{}", encoding="utf-8")
        return {
            "status": "succeeded",
            "generated_project_dir": str(target),
            "quality_gates": {"overall_score": 90},
            "phase_results": {"qa_release_gate": {"passed": True}},
        }


class TestAgentRebuildCommand(unittest.TestCase):
    def test_free_provider_allowlist_rejects_keyless_gateways_and_paid_vendors(self):
        self.assertEqual(free_provider_allowlist("openrouter"), {"openrouter"})
        self.assertEqual(free_provider_allowlist("openrouter,gemini"), {"openrouter", "gemini"})
        for names in ("grok", "opencode", "ninerouter", "omniroute", "freellmapi", "openai"):
            with self.subTest(names=names), self.assertRaises(ValueError):
                free_provider_allowlist(names)

    def test_safe_project_slug_is_input_safe(self):
        self.assertEqual(safe_project_slug("My Shop / Europe!"), "my-shop-europe")

    def test_discover_projects_requires_frontend_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = root / "valid"
            (valid / "frontend").mkdir(parents=True)
            (valid / "frontend" / "package.json").write_text("{}", encoding="utf-8")
            (root / "not-a-site").mkdir()
            self.assertEqual(discover_projects(root), [valid])

    def test_context_uses_saved_brief_and_page_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pages_root = root / "frontend" / "src" / "pages"
            pages_root.mkdir(parents=True)
            (root / "frontend" / "package.json").write_text(
                json.dumps({"name": "clinic-site", "description": "Clinic services"}),
                encoding="utf-8",
            )
            (root / "generation-report.json").write_text(
                json.dumps({"user_prompt": "A local clinic booking website"}),
                encoding="utf-8",
            )
            (pages_root / "Booking.jsx").write_text(
                "export default function Booking() {}", encoding="utf-8"
            )
            context = project_context(root)
            self.assertEqual(context["original_prompt"], "A local clinic booking website")
            self.assertEqual(context["pages"], ["Booking"])

    def test_prompt_requests_agent_rebuild_and_blocks_deploy(self):
        prompt = build_rebuild_prompt(
            {
                "source_name": "clinic-site",
                "original_prompt": "A clinic booking website",
                "package_name": "clinic-site",
                "description": "Clinic services",
                "pages": ["Home", "Booking"],
            },
            "rebuilt-clinic-site",
        )
        self.assertIn("full planning, international design research", prompt)
        self.assertIn("Required output project slug: rebuilt-clinic-site", prompt)
        self.assertIn("A clinic booking website", prompt)
        self.assertIn("Home, Booking", prompt)
        self.assertIn("Do not deploy or publish", prompt)

    def test_generated_project_root_supports_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            default = resolve_generated_projects_dir(project_root, {})
            configured = resolve_generated_projects_dir(
                project_root,
                {"GENERATED_PROJECTS_DIR": str(project_root / "isolated")},
            )
        self.assertEqual(default, (project_root / "generated-projects").resolve())
        self.assertEqual(configured, (project_root / "isolated").resolve())

    def test_partial_agent_output_requires_review(self):
        self.assertEqual(
            classify_agent_result(True, "partial", 72.7, {"passed": False}),
            "review_required",
        )

    def test_only_fully_passing_agent_output_counts_as_generated(self):
        self.assertEqual(
            classify_agent_result(True, "succeeded", 88, {"passed": True}),
            "generated",
        )

    def test_resume_rechecks_previous_agent_quality_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            frontend = output / "frontend"
            frontend.mkdir(parents=True)
            (frontend / "package.json").write_text("{}", encoding="utf-8")
            (output / "generation-report.json").write_text(
                json.dumps({
                    "status": "partial",
                    "quality_gates": {"overall_score": 72.7},
                    "phase_results": {"qa_release_gate": {"passed": False}},
                }),
                encoding="utf-8",
            )
            result = _revalidate_previous_results([{
                "source_project": "site",
                "output_project": str(output),
                "status": "generated",
            }])
        self.assertEqual(result[0]["status"], "review_required")

    def test_free_only_rebuild_confines_and_restores_provider_routing(self):
        from agent import ai_routing

        ai_routing.reset_router()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "site"
                (source / "frontend").mkdir(parents=True)
                (source / "frontend" / "package.json").write_text("{}", encoding="utf-8")
                output = root / "out"
                _FakeOrchestrator.instances = []
                _FakeOrchestrator.output_dir = output / "rebuilt-site"
                before_router = ai_routing.get_router()
                env_keys = ("GENERATED_PROJECTS_DIR", "AI_PROVIDER", "REASONING_PROVIDER")
                before_env = {key: os.environ.get(key) for key in env_keys}
                fake_module = types.ModuleType("agent.orchestrator")
                fake_module.AgentOrchestrator = _FakeOrchestrator
                with mock.patch.dict(sys.modules, {"agent.orchestrator": fake_module}), mock.patch(
                    "config.providers.instantiate_provider",
                    lambda name: _StubProvider(name) if name == "gemini" else None,
                ):
                    report = rebuild_projects(root, output, free_only=True, provider="gemini")

                orchestrator = _FakeOrchestrator.instances[-1]
                self.assertEqual(report["generated"], 1)
                self.assertEqual(report["provider"], "gemini")
                self.assertEqual(orchestrator.ai_provider_name, "gemini")
                # The lane must be closed to every other vendor for the whole run.
                self.assertEqual(orchestrator.strict_allowlist_during_run, {"gemini"})
                self.assertIs(orchestrator.extra_spec["free_provider_only"], True)
                # Routing and environment must not leak into later work.
                self.assertIs(ai_routing.get_router(), before_router)
                self.assertEqual(ai_routing.get_router()._strict_allowlist, frozenset())
                self.assertEqual({key: os.environ.get(key) for key in env_keys}, before_env)
        finally:
            ai_routing.reset_router()


if __name__ == "__main__":
    unittest.main()