import json
import sys
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.rebuild_generated_projects import (
    _revalidate_previous_results,
    build_rebuild_prompt,
    classify_agent_result,
    discover_projects,
    project_context,
    safe_project_slug,
)
from config.settings import resolve_generated_projects_dir


class TestAgentRebuildCommand(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()