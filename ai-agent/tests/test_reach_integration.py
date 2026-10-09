import sys
import os
import json
import asyncio
import unittest
from pathlib import Path
from unittest import mock

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.reach import (
    AgentReachRouter,
    SearchResult,
    build_signal_query,
    cached_github_recovery,
    classify_signal,
    collect_market_signals,
    fire_github_recovery,
    github_recovery_from_error,
    has_react19_vite_marker,
    market_signals_sync,
    register_capability_flags,
    run_cli,
    subreddits_for,
)
from agent.reach.models import MarketSignalReport
from agent.reach.process import ProcessResult


def _unavailable(channel: str, reason: str = "not installed") -> SearchResult:
    return SearchResult(channel=channel, query="q", available=False, reason=reason)


class ReachProcessTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_cli_uses_create_subprocess_exec(self):
        """run_cli must be an awaitable that spawns via asyncio.create_subprocess_exec."""
        coro = run_cli(["echo", "hi"])
        try:
            self.assertTrue(asyncio.iscoroutine(coro))
        finally:
            coro.close()

        process = mock.AsyncMock()
        process.returncode = 0
        process.communicate = mock.AsyncMock(return_value=(b"hello\n", b""))
        with mock.patch(
            "agent.reach.process.asyncio.create_subprocess_exec", new=mock.AsyncMock(return_value=process)
        ) as spawn:
            result = await run_cli(["echo", "hi"])
        spawn.assert_awaited_once_with(
            "echo", "hi", cwd=None, env=None,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout, "hello")

    async def test_run_cli_timeout_kills_process(self):
        process = mock.AsyncMock()
        process.returncode = 1
        process.communicate = mock.AsyncMock(side_effect=asyncio.TimeoutError)
        process.kill = mock.MagicMock()
        with mock.patch(
            "agent.reach.process.asyncio.create_subprocess_exec", new=mock.AsyncMock(return_value=process)
        ):
            result = await run_cli(["slow"], timeout=0.01)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, 124)

    def test_in_worker_loop_returns_none_on_running_loop(self):
        """A running event loop in the current thread must never be blocked."""
        async def probe():
            return "ran"

        with self.assertRaises(RuntimeError):  # no native loop here yet
            asyncio.get_running_loop()

        async def wrapper():
            from agent.reach.process import in_worker_loop

            return in_worker_loop(probe)

        result = asyncio.run(wrapper())
        self.assertIsNone(result)


class ReachRouterTest(unittest.TestCase):
    def test_footprint_degrades_when_cli_missing(self):
        router = AgentReachRouter(probe=False)
        footprint = router.footprint()
        self.assertIn("available", footprint)
        self.assertEqual(footprint["env_flags"]["AGENT_REACH_VERIFY_CMD"], "agent-reach install --env=auto")

    def test_doctor_empty_when_cli_missing(self):
        router = AgentReachRouter(probe=False)
        router.cli = None
        loop = asyncio.new_event_loop()
        try:
            status = loop.run_until_complete(router.doctor_status())
        finally:
            loop.close()
        self.assertEqual(status, {})

    def test_parse_doctor_flat_map_from_live_tool(self):
        """A real `doctor --json` emits a flat channel->status map (no wrapper)."""
        router = AgentReachRouter(probe=False)
        payload = json.dumps({
            "github": {
                "status": "warn", "name": "GitHub", "message": "gh CLI 未安装",
                "tier": 0, "backends": ["gh CLI"], "active_backend": None,
            },
            "reddit": {
                "status": "ready", "name": "Reddit", "message": "ok",
                "tier": 0, "backends": ["OpenCLI"], "active_backend": "OpenCLI",
            },
        })
        channels = router._parse_doctor(ProcessResult("doctor", 1, payload, ""))
        self.assertEqual(set(channels), {"github", "reddit"})
        self.assertFalse(channels["github"].available)
        self.assertIsNone(channels["github"].active_backend)
        self.assertTrue(channels["reddit"].available)
        self.assertEqual(channels["reddit"].active_backend, "OpenCLI")

    @mock.patch("agent.reach.router.run_cli", new=mock.AsyncMock(return_value=ProcessResult(
        "doctor", 1, '{"github": {"status": "warn", "active_backend": null}}', "")))
    def test_doctor_status_parses_with_nonzero_exit(self):
        """doctor exits non-zero on warn/off statuses; output must still be parsed."""
        router = AgentReachRouter(probe=False)
        router.cli = "agent-reach"
        loop = asyncio.new_event_loop()
        try:
            status = loop.run_until_complete(router.doctor_status(force=True))
        finally:
            loop.close()
        self.assertIn("github", status)
        self.assertFalse(status["github"].available)

    def test_twitter_env_requires_tokens(self):
        router = AgentReachRouter(probe=False)
        os.environ.pop("TWITTER_AUTH_TOKEN", None)
        os.environ.pop("TWITTER_CT0", None)
        self.assertIsNone(router._tool_env("twitter"))
        os.environ["TWITTER_AUTH_TOKEN"] = "tok"
        os.environ["TWITTER_CT0"] = "ct"
        env = router._tool_env("twitter")
        self.assertEqual(env["TWITTER_AUTH_TOKEN"], "tok")


class ReachRouterAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_github_search_spawns_gh_and_parses_json(self):
        router = AgentReachRouter(probe=False)
        router._tools["github"] = "C:/bin/gh.cmd"
        payload = json.dumps([
            {
                "repository": {"fullName": "facebook/react"},
                "path": "packages/react/src/index.js",
                "htmlUrl": "https://github.com/facebook/react/blob/HEAD/packages/react/src/index.js",
                "textMatches": [{"fragment": "export function createRoot"}],
            }
        ])
        with mock.patch("agent.reach.router.run_cli", new=mock.AsyncMock(
            return_value=ProcessResult("gh search code", 0, payload, "")
        )):
            result = await router.search("github", "createRoot fix", num=3, language="JavaScript")
        self.assertTrue(result.available)
        self.assertTrue(result.command.startswith("C:/bin/gh.cmd"))
        self.assertEqual(result.records[0]["title"], "facebook/react/packages/react/src/index.js")
        self.assertIn("github.com", result.records[0]["url"])


class React19MarkerTest(unittest.TestCase):
    def test_detects_vite_react_error(self):
        sample = (
            "vite v8.2.0 building for production...\n"
            "[vite:esbuild] Transform failed with 1 error:\n"
            "frontend/src/App.jsx:5:9: ERROR: Unexpected token\n"
            "react-dom tried to render before createRoot was called"
        )
        self.assertTrue(has_react19_vite_marker(sample))

    def test_plain_prettier_fail_is_not_flagged(self):
        self.assertFalse(has_react19_vite_marker("prettier error on line 3"))

    def test_empty_output_is_not_flagged(self):
        self.assertFalse(has_react19_vite_marker(""))


class MarketSignalTest(unittest.IsolatedAsyncioTestCase):
    def test_classify_signal_buckets(self):
        buckets = classify_signal("site is slow and broken, checkout fails, want dark mode and chat")
        self.assertIn("slow", buckets["complaints"])
        self.assertIn("dark mode", buckets["preferred_features"])
        self.assertTrue(buckets["design_topics"])

    def test_query_builder_deduplicates(self):
        spec = {"keywords": ["ai", "ai"], "website_type": "saas", "industry": "fintech"}
        q = build_signal_query(spec)
        self.assertIn("saas", q)
        self.assertIn("fintech", q)
        self.assertEqual(q.count("ai"), 1)

    def test_subreddit_mapping(self):
        subs = subreddits_for("saas", "general")
        self.assertIn("r/saas", subs)
        self.assertIn(subreddits_for("nope", "nope")[0], "r/webdev")

    async def test_collect_market_signals_validates_payload(self):
        router = AgentReachRouter(probe=False)
        router.search = mock.AsyncMock(return_value=SearchResult(
            channel="reddit", query="q", available=True,
            records=[{
                "title": "Checkout is painfully slow",
                "url": "https://reddit.com/r/saas/x",
                "snippet": "Checkout is painfully slow and broken on this SaaS, we want dark mode",
            }],
        ))
        with mock.patch("agent.reach.market_signals._get_router", return_value=router):
            report = await collect_market_signals({
                "website_type": "saas", "industry": "fintech", "keywords": ["ai"]
            })
        self.assertIsInstance(report, MarketSignalReport)
        payload = report.to_dict()
        self.assertEqual(payload["website_type"], "saas")
        self.assertTrue(payload["ok"])
        self.assertTrue(any("dark mode" in c for c in payload["preferred_features"]))
        self.assertTrue(all(isinstance(f, dict) for f in payload["fragments"]))

    def test_market_signals_sync_is_degraded_outside_tooling(self):
        router = AgentReachRouter(probe=False)
        router.search = mock.AsyncMock(side_effect=lambda ch, q, num=8, subreddit=None, **kw: _unavailable(ch))
        with mock.patch("agent.reach.market_signals._get_router", return_value=router):
            payload = market_signals_sync({"website_type": "ecommerce"})
        self.assertIsInstance(payload, dict)
        self.assertIn("complaints", payload)
        self.assertIn("fragments", payload)

    async def test_market_signals_sync_defers_in_running_loop(self):
        """Inside a running loop the sync bridge must return a deferred marker, not block."""
        router = AgentReachRouter(probe=False)
        router.search = mock.AsyncMock(return_value=_unavailable("reddit"))
        with mock.patch("agent.reach.market_signals._get_router", return_value=router):
            payload = market_signals_sync({"website_type": "ecommerce"})
        self.assertFalse(payload["ok"])
        self.assertIn("event-loop-thread", payload["reason"])


class GithubRecoveryTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        import agent.reach.github_recovery as gr
        with gr._CACHE_LOCK:
            gr._RECOVERY_CACHE.clear()
            gr._LAST_FIRE_AT[0] = 0.0

    async def test_recovery_fetches_and_validates_patches(self):
        with mock.patch("agent.reach.router.resolve_tool", side_effect=lambda n: f"C:/bin/{n}.cmd"):
            with mock.patch("agent.reach.router.run_cli", new=mock.AsyncMock(return_value=ProcessResult(
                "gh search code",
                0,
                json.dumps([{
                    "repository": {"fullName": "vitejs/vite"},
                    "path": "packages/vite/src/index.ts",
                    "htmlUrl": "https://github.com/vitejs/vite/pull/123",
                    "textMatches": [{"fragment": "fix: esbuild transform"}],
                }]),
                "",
            ))):
                bundle = await github_recovery_from_error(
                    "vite v8.2.0\n[vite:esbuild] Transform failed\nreact-dom Unexpected token",
                    context="react19-vite-lint",
                )
        self.assertTrue(bundle["applied"])
        self.assertTrue(bundle["patches"])
        self.assertIn("github.com", bundle["patch_url"])
        self.assertEqual(bundle["context"], "react19-vite-lint")
        cached = cached_github_recovery()
        self.assertEqual(cached["patch_title"], bundle["patch_title"])

    async def test_recovery_skipped_without_marker(self):
        bundle = await github_recovery_from_error("prettier version mismatch only")
        self.assertFalse(bundle["applied"])
        self.assertEqual(bundle["patches"], [])

    def test_fire_github_recovery_uses_cache_or_empty(self):
        with mock.patch("agent.reach.router.resolve_tool", side_effect=lambda n: None):
            result = fire_github_recovery("prettier only no react", context="x")
        self.assertIsNone(result)


class MarketAnalyzerIntegrationTest(unittest.TestCase):
    def test_analyze_embeds_social_signals(self):
        from agent.market_analyzer import MarketAnalyzer

        analyzer = MarketAnalyzer()
        signals = {
            "ok": True,
            "fragments": [{"platform": "reddit", "title": "t", "url": "u", "snippet": "s"}],
            "complaints": ["slow"],
            "preferred_features": ["dark mode"],
            "channels_available": {"reddit": True, "twitter": False},
        }
        spec = {"website_type": "saas", "industry": "fintech", "features": ["authentication"]}
        analysis = analyzer.analyze(spec, signals)
        self.assertEqual(analysis["live_trend_signals"], signals)
        self.assertTrue(any(t.startswith("Live community signal:") for t in analysis["market_trends"]))
        self.assertEqual(analysis["live_signal_sources"]["platforms"], ["reddit"])


class PlannerIntegrationTest(unittest.TestCase):
    def test_planner_adds_live_signal_tasks(self):
        from agent.planner import GenerationPlanner

        spec = {
            "website_type": "saas",
            "features": ["auth"],
            "live_signal_summary": {
                "complaints": ["checkout is slow"],
                "preferred_features": ["dark mode"],
                "sources": ["reddit"],
            },
        }
        plan = GenerationPlanner().create_plan(
            spec,
            {"name": "Base", "file_path": "tpl"},
            [{"name": "c", "features": ["auth"]}],
            {"images": [], "icons": [], "animations": []},
            {"name": "Express"},
            [],
        )
        self.assertIn("market_signals", plan)
        self.assertIn("WEBSITE GENERATION DELIVERY CONTRACT", plan["master_prompt"])
        self.assertTrue(any("live community signal" in t for t in plan["ai_tasks_required"]))

    def test_planner_adds_fullstack_baseline_without_optional_saas_features(self):
        from agent.planner import GenerationPlanner

        spec = {"project_name": "local-business", "website_type": "business"}
        plan = GenerationPlanner().create_plan(
            spec, {}, [], {"images": [], "icons": [], "animations": []}, {}, [],
        )

        self.assertEqual(plan["layout_mode"], "enterprise")
        self.assertTrue({"jwt_auth", "users", "contact"}.issubset(set(spec["features"])))
        self.assertFalse(
            {"stripe_payments", "oauth", "multi_factor_auth", "subscriptions", "analytics"}
            .intersection(spec["features"])
        )

    def test_planner_respects_explicit_static_opt_out(self):
        from agent.planner import GenerationPlanner

        spec = {
            "project_name": "static-portfolio",
            "website_type": "portfolio",
            "buyer_type": "static",
        }
        plan = GenerationPlanner().create_plan(
            spec, {}, [], {"images": [], "icons": [], "animations": []}, {}, [],
        )

        self.assertEqual(plan["layout_mode"], "client-static")
        self.assertFalse({"jwt_auth", "users", "contact"}.intersection(spec["features"]))


class CodeModifierRecoveryTest(unittest.TestCase):
    def test_patch_file_appends_verified_recovery_reference(self):
        from agent.code_modifier import CodeModifier

        captured = {}

        class FakeProvider:
            def modify_code(self, content, instruction):
                captured["instruction"] = instruction
                return "export const ok = 1;"

        modifier = CodeModifier(ai_provider=FakeProvider())
        with mock.patch(
            "agent.reach.github_recovery._RECOVERY_CACHE",
            {
                "applied": True,
                "patch_title": "Fix vite transform",
                "patch_url": "https://github.com/vitejs/vite/pull/1",
                "context": "react19-vite-lint",
                "query": "",
                "patches": [],
            },
        ):
            with mock.patch("utils.file_manager.FileManager.read_file", return_value="export const a = 1;"):
                with mock.patch("utils.file_manager.FileManager.write_file", return_value=True):
                    modifier.patch_file("/tmp/app.jsx", "Fix lint issues.")
        self.assertIn("Community-verified fix reference", captured["instruction"])


class QualityGateRecoveryTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from agent.quality_gate import DevOpsQualityGate, CommandResult

        self.gate = DevOpsQualityGate(require_node=False)
        self.project_dir = str(Path(os.environ.get("TEMP", "/tmp")) / "lumicore-reach-test")
        os.makedirs(os.path.join(self.project_dir, "frontend", "src"), exist_ok=True)
        with open(os.path.join(self.project_dir, "frontend", "src", "App.jsx"), "w", encoding="utf-8") as fh:
            fh.write("export const x = 1;\n")

    def tearDown(self):
        root = Path(self.project_dir)
        if root.exists():
            import shutil

            shutil.rmtree(str(root), ignore_errors=True)

    async def test_run_gate_attaches_recovery_when_react_marker_present(self):
        from agent.quality_gate import CommandResult

        bundle = {
            "applied": True,
            "context": "react19-vite-lint",
            "query": "vite transform failed fix",
            "patches": [{"error_signature": "q", "title": "Fix", "url": "https://github.com/x", "repo": "x/y", "language": "JavaScript", "confidence": 0.6}],
            "patch_title": "Fix",
            "patch_url": "https://github.com/x",
            "reference": "Fix (https://github.com/x)",
        }
        with mock.patch.object(
            self.gate, "format_project", new=mock.AsyncMock(return_value=CommandResult("fmt", 0, "", ""))
        ):
            with mock.patch.object(
                self.gate, "lint_project",
                new=mock.AsyncMock(return_value=CommandResult(
                    "lint", 1,
                    "vite v8.2.0\n[vite:esbuild] Transform failed\nreact-dom Unexpected token in App.jsx",
                    "",
                )),
            ):
                with mock.patch.object(
                    self.gate, "_github_recovery_for", new=mock.AsyncMock(return_value=bundle)
                ):
                    report = await self.gate.run_gate(self.project_dir, self_heal=mock.Mock())
        self.assertEqual(report["github_recovery"]["patch_title"], "Fix")
        self.assertEqual(report["self_heal_rounds"][0]["github_recovery"]["applied"], True)

    async def test_github_recovery_probe_skips_without_marker(self):
        """The probe hook must not fetch when output has no React/Vite marker."""
        from agent.quality_gate import CommandResult

        with mock.patch("agent.reach.github_recovery.github_recovery_from_error", new=mock.AsyncMock()) as fetch:
            outcome = await self.gate._github_recovery_for(
                CommandResult("lint", 1, "prettier/eslint generic", ""), fmt_result=None
            )
        self.assertEqual(outcome, {})
        fetch.assert_not_awaited()

    async def test_github_recovery_probe_fetches_on_marker(self):
        from agent.quality_gate import CommandResult

        bundle = {"applied": True, "patch_title": "Fix transform"}
        with mock.patch("agent.reach.github_recovery.github_recovery_from_error", new=mock.AsyncMock(return_value=bundle)):
            outcome = await self.gate._github_recovery_for(
                CommandResult(
                    "lint", 1,
                    "vite v8.2.0 transform failed\nreact-dom Unexpected token in App.jsx",
                    "",
                ),
                fmt_result=None,
            )
        self.assertEqual(outcome["patch_title"], "Fix transform")


class QualityGatesRecoveryHintTest(unittest.TestCase):
    def test_evaluate_attaches_cache_hint(self):
        from agent.quality_gates import QualityGates

        gates = QualityGates()
        with mock.patch(
            "agent.reach.github_recovery._RECOVERY_CACHE",
            {
                "applied": True,
                "context": "react19-vite-lint",
                "patch_title": "Fix vite transform",
                "patch_url": "https://github.com/vitejs/vite/pull/1",
                "query": "",
                "patches": [],
            },
        ):
            result = gates.evaluate("/tmp/nope", {"features": [], "trending_features": []}, {"valid": True, "errors": [], "warnings": []})
        self.assertEqual(result["github_recovery_hint"]["patch_title"], "Fix vite transform")


class CapabilityRegistrationTest(unittest.TestCase):
    def test_registers_structural_access_flags(self):
        footprint = register_capability_flags()
        self.assertIn("available", footprint)
        self.assertEqual(footprint["verify_cmd"], "agent-reach install --env=auto")
        self.assertEqual(os.environ.get("AGENT_REACH_VERIFY_CMD"), "agent-reach install --env=auto")


if __name__ == "__main__":
    unittest.main()