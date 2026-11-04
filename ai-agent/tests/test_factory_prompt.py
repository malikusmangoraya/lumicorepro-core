"""Tests — one-prompt delivery: parse intent, generate, then run the factory."""
import sys
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

    def test_brand_after_an_imperative_verb(self):
        plan = factory.parse_delivery_prompt("Build CortexDesk, an AI copilot for support teams")
        self.assertEqual(plan["name"], "CortexDesk")
        self.assertEqual(plan["slug"], "cortexdesk")
        self.assertEqual(plan["industry"], "saas")
        self.assertTrue(plan["video"])

    def test_unnamed_prompt_gets_an_industry_name(self):
        plan = factory.parse_delivery_prompt("create an online course marketplace for teachers")
        self.assertEqual(plan["industry"], "education")
        self.assertEqual(plan["name"], "Education Studio")

    def test_too_short_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            factory.parse_delivery_prompt("hi")


class DeliverFromPromptTests(unittest.TestCase):
    def setUp(self):
        # deliver_from_prompt gates on the live provider before writing anything;
        # these tests cover planning and staging, so pin the gate instead of
        # depending on whichever key/provider config the machine happens to hold.
        patcher = patch.object(
            factory, "provider_health",
            return_value={"usable": True, "provider": "groq", "model": "gpt-oss-120b",
                          "key_present": True, "model_offered": True, "message": "pinned"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

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

    def test_explicit_scene_reaches_the_fullstack_generation_contract(self):
        contracts = []

        def generate(destination, **kwargs):
            contracts.append(kwargs['generation_contract'])
            return {'success': True, 'total_files': 1}

        with tempfile.TemporaryDirectory() as tmp, \
             patch('agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project',
                   side_effect=generate), \
             patch.object(factory, 'run_factory', return_value={'status': 'built', 'verified': False}):
            result = factory.deliver_from_prompt(
                'Build "Prism" a records workspace', dest_root=tmp,
                scene={'archetype': 'cyber_grid'}, platform='none', video=False,
            )
        self.assertEqual(result['status'], 'built')
        self.assertEqual(contracts[0]['scene'], {'archetype': 'cyber_grid'})
        self.assertEqual(contracts[0]['database'], 'postgresql')
        self.assertTrue(contracts[0]['auth'])

    def test_prompt_3d_intent_reaches_the_same_fullstack_lane(self):
        contracts = []

        def generate(destination, **kwargs):
            contracts.append(kwargs['generation_contract'])
            return {'success': True, 'total_files': 1}

        with tempfile.TemporaryDirectory() as tmp, \
             patch('agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project',
                   side_effect=generate), \
             patch.object(factory, 'run_factory', return_value={'status': 'built', 'verified': False}):
            factory.deliver_from_prompt('Build "Prism" a 3D records workspace', dest_root=tmp)
        self.assertEqual(contracts[0]['scene']['archetype'], 'floating_crystal')

    def test_product_viewer_without_model_stops_before_provider_or_files(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(factory, 'provider_health') as health, \
             patch.object(factory, 'run_factory') as run:
            result = factory.deliver_from_prompt(
                'Build "Prism" a product showroom', dest_root=tmp,
                scene={'archetype': 'product_viewer'},
            )
            self.assertEqual(result['status'], 'failed')
            self.assertIn('model', result['message'])
            self.assertEqual(list(Path(tmp).iterdir()), [])
            health.assert_not_called()
            run.assert_not_called()

    def test_app_surfaces_reach_the_generation_contract(self):
        seen = []

        def generate(destination, **kwargs):
            seen.append(kwargs["generation_contract"]["app"])
            return {"success": True, "total_files": 1}

        with tempfile.TemporaryDirectory() as tmp, \
             patch("agent.fullstack_ultra_engine.FullStackUltraEngine.generate_project",
                   side_effect=generate), \
             patch.object(factory, "run_factory", return_value={"status": "built"}):
            factory.deliver_from_prompt("Build a records app", dest_root=tmp,
                                        platform="none", video=False)
        self.assertEqual(seen[0]["web"], "none")
        self.assertEqual(seen[0]["mobile"]["platforms"], ["android"])

    def test_pwa_without_web_surface_fails_before_provider_or_files(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(factory, "provider_health") as health:
            result = factory.deliver_from_prompt(
                "Build a records app", dest_root=tmp,
                app={"web": "none", "pwa": True})
            self.assertEqual(result["status"], "failed")
            self.assertEqual(list(Path(tmp).iterdir()), [])
            health.assert_not_called()


class DeliverCliSurfaceFlagTests(unittest.TestCase):
    def test_orphan_mobile_verify_flag_exits_non_zero_and_never_generates(self):
        import main

        with patch.object(sys, "argv", [
            "main.py", "--deliver", "Build a records app",
            "--deliver-mobile-verify", "none",
        ]), patch("agent.factory_pipeline.deliver_from_prompt") as deliver, \
             patch("builtins.print"):
            with self.assertRaises(SystemExit) as caught:
                main.main()
        self.assertNotEqual(caught.exception.code, 0)
        deliver.assert_not_called()

    def test_normal_mobile_flag_keeps_the_apk_emulator_default(self):
        import main

        seen = {}

        def fake_deliver(prompt, **kwargs):
            seen.update(kwargs)
            return {"status": "built", "verified": False}

        with patch.object(sys, "argv", [
            "main.py", "--deliver", "Build a records app",
            "--deliver-mobile", "android",
        ]), patch("agent.factory_pipeline.deliver_from_prompt",
                  side_effect=fake_deliver), patch("builtins.print"):
            with self.assertRaises(SystemExit) as caught:
                main.main()
        self.assertEqual(caught.exception.code, 0)
        self.assertEqual(seen["app"]["mobile"]["verification"], "apk_emulator")


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
