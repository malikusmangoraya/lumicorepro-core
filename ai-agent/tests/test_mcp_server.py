import contextlib
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.memory import create_connected_server_and_client_session

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

import mcp_server
from mcp_server import AgentAPI, set_api_client


class FakeAgentAPI:
    """In-memory stand-in for the HTTP bridge."""

    def __init__(self, responses=None, error=None):
        self.responses = responses or {}
        self.error = error
        self.calls = []

    def _get(self, path, params=None, timeout=None):
        self.calls.append(("GET", path, params))
        if self.error:
            raise self.error
        return self.responses.get(path, {})

    def _post(self, path, body, timeout=None):
        self.calls.append(("POST", path, body))
        if self.error:
            raise self.error
        return self.responses.get(path, {})


class TestMcpToolSurface(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.fake = FakeAgentAPI()
        self._original = mcp_server._api
        set_api_client(self.fake)

    async def asyncTearDown(self):
        set_api_client(self._original)

    @contextlib.asynccontextmanager
    async def _session(self):
        """mcp 1.30 yields a single ClientSession; older builds yielded a tuple."""
        async with create_connected_server_and_client_session(
            mcp_server.mcp
        ) as connected:
            client = connected[0] if isinstance(connected, tuple) else connected
            yield client

    async def _call(self, name, arguments=None):
        """Return (is_error, text). ToolError may surface as isError or raise,
        depending on how strict the SDK build is."""
        async with self._session() as client:
            try:
                result = await client.call_tool(name, arguments or {})
            except ToolError as exc:
                return True, str(exc)
        return bool(getattr(result, "isError", False)), result.content[0].text

    async def test_exposes_expected_tools(self):
        async with self._session() as client:
            result = await client.list_tools()
        names = {tool.name for tool in result.tools}
        expected = {
            "generate_website", "get_run", "list_runs", "plan_website",
            "chat_with_agent", "registries_summary", "memory_insights",
        }
        self.assertTrue(expected.issubset(names))

    async def test_generate_website_forwards_body_and_returns_run(self):
        self.fake.responses["/api/generate"] = {
            "run_id": "r-1", "status": "queued",
        }
        is_error, text = await self._call("generate_website", {
            "prompt": "Build a bakery website with online ordering",
            "provider": "gemini",
            "design_style": "minimalism",
            "language": "en",
        })
        self.assertFalse(is_error, text)
        payload = json.loads(text)
        self.assertEqual(payload["run_id"], "r-1")
        method, path, body = self.fake.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/api/generate")
        self.assertEqual(body["prompt"], "Build a bakery website with online ordering")
        self.assertEqual(body["design_style"], "minimalism")
        self.assertEqual(body["language"], "en")

    async def test_generate_website_rejects_short_prompt(self):
        is_error, text = await self._call("generate_website", {"prompt": "hi"})
        self.assertTrue(is_error)
        self.assertIn("at least 5 characters", text)
        self.assertEqual(self.fake.calls, [])

    async def test_get_run_and_list_runs_bridge(self):
        self.fake.responses["/api/runs/r-9"] = {"run_id": "r-9", "status": "done"}
        self.fake.responses["/api/runs"] = {"runs": [], "count": 0}
        is_error, text = await self._call("get_run", {"run_id": "r-9"})
        self.assertFalse(is_error, text)
        self.assertEqual(json.loads(text)["status"], "done")

        is_error, text = await self._call("list_runs", {"limit": 5, "status": "done"})
        self.assertFalse(is_error, text)
        self.assertEqual(json.loads(text)["count"], 0)
        self.assertEqual(self.fake.calls[1], ("GET", "/api/runs", {"limit": 5, "status": "done"}))

    async def test_plan_website_dry_run(self):
        self.fake.responses["/api/dry-run"] = {"project_name": "Bakery", "components_count": 12}
        is_error, text = await self._call("plan_website", {
            "prompt": "Build a bakery website with online ordering",
        })
        self.assertFalse(is_error, text)
        payload = json.loads(text)
        self.assertEqual(payload["project_name"], "Bakery")
        self.assertEqual(self.fake.calls[0][1], "/api/dry-run")

    async def test_server_error_surfaces_as_tool_error(self):
        self.fake.error = ToolError("Agent API unreachable at http://x — start server.py")
        is_error, text = await self._call("registries_summary", {})
        self.assertTrue(is_error)
        self.assertIn("unreachable", text)


class TestAgentAPIClient(unittest.TestCase):
    """The HTTP bridge itself: auth header, unwrap, unreachable mapping."""

    def test_sends_api_key_header_and_unwraps_json(self):
        recorded = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                recorded["path"] = self.path
                recorded["api_key"] = self.headers.get("X-Api-Key")
                body = json.dumps({"templates": 42}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = AgentAPI(
                base_url=f"http://127.0.0.1:{server.server_port}",
                api_key="test-key",
            )
            payload = client._get("/api/registries/summary")
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(payload, {"templates": 42})
        self.assertEqual(recorded["path"], "/api/registries/summary")
        self.assertEqual(recorded["api_key"], "test-key")

    def test_unreachable_server_maps_to_actionable_tool_error(self):
        # Port 1 on loopback refuses connections without dialling out.
        client = AgentAPI(base_url="http://127.0.0.1:1", api_key="")
        with self.assertRaises(ToolError) as ctx:
            client._get("/api/registries/summary")
        message = str(ctx.exception)
        self.assertIn("unreachable", message)
        self.assertIn("server.py", message)


if __name__ == "__main__":
    unittest.main()
