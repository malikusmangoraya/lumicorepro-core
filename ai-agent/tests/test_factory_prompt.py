"""Tests — one-prompt delivery: parse intent, generate, then run the factory."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent.factory_pipeline as factory


class PromptParsingTests(unittest.TestCase):
    def test_quoted_name_is_the_brand(self):
        plan = factory.parse_delivery_prompt('Build "TaskPilot" an AI task manager for remote teams')
        self.assertEqual(plan["name"], "TaskPilot")
        self.assertEqual(plan["industry"], "saas")
        self.assertEqual(plan["deploy"], "vercel")
        self.assertTrue(plan["video"])

    def test_named_brand_and_industry_keyword(self):
        plan = factory.parse_delivery_prompt("Build a restaurant booking site called Bella with no video")
        self.assertEqual(plan["name"], "Bella")
        self.assertEqual(plan["industry"], "restaurant")
        self.assertFalse(plan["video"])

    def test_leading_brand_and_local_only(self):
        plan = factory.parse_delivery_prompt("Acme fintech dashboard with no deploy")
        self.assertEqual(plan["name"], "Acme")
        self.assertEqual(plan["industry"], "fintech")
        self.assertEqual(plan["deploy"], "none")

    def test_railway_intent_and_slug(self):
        plan = factory.parse_delivery_prompt("Nimbus travel platform, deploy to railway")
        self.assertEqual(plan["name"], "Nimbus")
        self.assertEqual(plan["industry"], "travel")
        self.assertEqual(plan["deploy"], "railway")
        self.assertEqual(plan["slug"], "nimbus")

    def test_unnamed_prompt_gets_an_industry_name(self):
        plan = factory.parse_delivery_prompt("create an online course marketplace for teachers")
        self.assertEqual(plan["industry"], "education")
        self.assertEqual(plan["name"], "Education Studio")

    def test_too_short_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            factory.parse_delivery_prompt("hi")


class DeliverFromPromptTests(unittest.TestCase):
    def test_generates_then_runs_the_factory_with_the_plan(self):
        generated = {"success": True, "total_files": 43, "elapsed_ms": 90, "errors": []}
        factory_result = {"status": "delivered", "verified": True, "report_md": "x"}
        events = []
        with tempfile.TemporaryDirectory() as tmp:
            with patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
                       return_value=generated) as generate, \
                 patch.object(factory, "run_factory", return_value=factory_result) as run:
                result = factory.deliver_from_prompt(
                    'Build "CortexDesk" an AI knowledge copilot',
                    dest_root=tmp,
                    progress=events.append,
                )
            destination = Path(result["destination"])
            self.assertEqual(destination.name, "cortexdesk")
            self.assertTrue(destination.is_dir())
            kwargs = generate.call_args.kwargs
            self.assertEqual(kwargs["brand_name"], "CortexDesk")
            self.assertEqual(kwargs["industry"], "saas")
            run_kwargs = run.call_args.kwargs
            self.assertEqual(run_kwargs["name"], "CortexDesk")
            self.assertIn("generation_meta", run_kwargs)
            self.assertTrue(any(e["stage"] == "generate" and e["status"] == "done" for e in events))
            self.assertEqual(result["status"], "delivered")

    def test_existing_slug_gets_a_suffix_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "cortexdesk").mkdir()
            with patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
                       return_value={"success": True, "total_files": 1, "elapsed_ms": 1}), \
                 patch.object(factory, "run_factory", return_value={"status": "partial", "verified": False}):
                result = factory.deliver_from_prompt('Build "CortexDesk" an AI copilot', dest_root=tmp)
            self.assertEqual(Path(result["destination"]).name, "cortexdesk-2")

    def test_reuse_existing_regenerates_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "cortexdesk"
            existing.mkdir()
            (existing / "keep.txt").write_text("old")
            with patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
                       return_value={"success": True, "total_files": 1, "elapsed_ms": 1}),                  patch.object(factory, "run_factory", return_value={"status": "partial", "verified": False}):
                result = factory.deliver_from_prompt(
                    'Build "CortexDesk" an AI copilot', dest_root=tmp, reuse_existing=True
                )
            self.assertEqual(Path(result["destination"]).resolve(), existing.resolve())
            self.assertTrue((existing / "keep.txt").is_file())

    def test_generation_failure_stops_before_building(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
                       return_value={"success": False, "errors": ["disk full"]}), \
                 patch.object(factory, "run_factory") as run:
                result = factory.deliver_from_prompt('Build "Broken" a tool', dest_root=tmp)
            self.assertEqual(result["status"], "failed")
            run.assert_not_called()


class ProgressEventTests(unittest.TestCase):
    def test_a_broken_listener_cannot_fail_the_pipeline(self):
        def explode(_event):
            raise RuntimeError("listener bug")

        factory._emit(explode, "build", "running")  # must not raise

    def test_events_are_plain_dicts(self):
        seen = []
        factory._emit(seen.append, "qa", "done", detail="passed")
        self.assertEqual(seen, [{"stage": "qa", "status": "done", "detail": "passed"}])


if __name__ == "__main__":
    unittest.main()
