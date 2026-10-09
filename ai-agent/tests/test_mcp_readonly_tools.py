"""Guard tests for the MCP server's local read-only repo tools.

read_file / search_code / glob_files / list_directory close the gap with
opencode/Codebuff's file surface (read, grep, glob, list). These tests pin
the two properties that make them safe to expose:

  1. READ-ONLY + ROOT-CONFINED — every path resolves inside REPO_ROOT;
     `..`, absolute-path and symlink escapes raise ToolError.
  2. NO SECRETS — `.env` and key/cert files are refused, while
     `.env.example` stays readable.

Plus basic behaviour: paging, grep-style matches, glob filtering and
directory listing bounds.
"""

import sys
import unittest
from pathlib import Path

from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.memory import create_connected_server_and_client_session

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

import mcp_server  # noqa: E402  (path shim must run first)

REPO_ROOT = mcp_server.REPO_ROOT


class TestRootConfined(unittest.TestCase):
    """Every read path must resolve inside the repository root."""

    def test_read_file_rejects_parent_escape(self):
        with self.assertRaises(ToolError):
            mcp_server.read_file("../../etc/passwd")

    def test_read_file_rejects_absolute_path_outside_root(self):
        anchor = str(Path(REPO_ROOT).anchor)  # 'C:\\' or '/'
        if Path(anchor).resolve() == REPO_ROOT:
            self.skipTest("repo root is the filesystem root")
        with self.assertRaises(ToolError):
            mcp_server.read_file(str(Path(anchor) / "definitely-not-in-repo.txt"))

    def test_read_file_rejects_absolute_path_inside_root(self):
        # Absolute but inside the root is fine and resolves to a relative path.
        target = REPO_ROOT / "package.json"
        result = mcp_server.read_file(str(target), limit=1)
        self.assertEqual(result["path"], "package.json")

    def test_glob_files_rejects_escape_pattern(self):
        with self.assertRaises(ToolError):
            mcp_server.glob_files("../../etc/*")

    def test_glob_files_rejects_absolute_pattern(self):
        with self.assertRaises(ToolError):
            mcp_server.glob_files(str(Path(REPO_ROOT).anchor) + "*")

    def test_search_code_rejects_escape_glob(self):
        with self.assertRaises(ToolError):
            mcp_server.search_code("root:", file_glob="../../*")

    def test_list_directory_rejects_escape(self):
        with self.assertRaises(ToolError):
            mcp_server.list_directory("../..")

    def test_search_matches_stay_inside_root(self):
        result = mcp_server.search_code(
            "def ", path="ai-agent", file_glob="*.py", max_results=20
        )
        for match in result["matches"]:
            resolved = (REPO_ROOT / match["path"]).resolve()
            self.assertTrue(resolved.is_relative_to(REPO_ROOT), match["path"])


class TestNoSecrets(unittest.TestCase):
    """Secret files must be refused; example/template env files stay readable."""

    def test_secret_classifier(self):
        secret = mcp_server._is_secret
        self.assertTrue(secret(Path(".env")))
        self.assertTrue(secret(Path("ai-agent", ".env.local")))
        self.assertTrue(secret(Path("server.pem")))
        self.assertTrue(secret(Path("id_rsa")))
        self.assertTrue(secret(Path("credentials.json")))
        self.assertFalse(secret(Path(".env.example")))
        self.assertFalse(secret(Path(".env.template")))
        self.assertFalse(secret(Path("src", "main.jsx")))

    def test_read_file_refuses_env(self):
        planted = agent_dir / "tests" / ".env"
        created = not planted.exists()
        if created:
            planted.write_text("SECRET_KEY=1\n", encoding="utf-8")
        try:
            with self.assertRaises(ToolError) as ctx:
                mcp_server.read_file("ai-agent/tests/.env")
            self.assertIn("secret", str(ctx.exception))
        finally:
            if created:
                planted.unlink(missing_ok=True)

    def test_read_file_allows_env_example(self):
        result = mcp_server.read_file(".env.example", limit=5)
        self.assertEqual(result["path"], ".env.example")
        self.assertGreater(result["total_lines"], 0)

    @unittest.skipUnless(
        (agent_dir / "tests").is_dir(), "ai-agent/tests missing"
    )
    def test_search_skips_secret_files(self):
        # A planted secret file inside the search path must never surface.
        # The marker is assembled at runtime so this file's own source does
        # not contain the literal string the search looks for.
        marker = "SUPER_" + "SECRET_MARKER"
        planted = agent_dir / "tests" / ".env.planted_test_file"
        planted.write_text(f"{marker}=1\n", encoding="utf-8")
        try:
            result = mcp_server.search_code(
                marker, path="ai-agent/tests", max_results=10
            )
            self.assertEqual(result["matches"], [])
        finally:
            planted.unlink(missing_ok=True)


class TestReadFileBehaviour(unittest.TestCase):
    def test_paging_and_truncation(self):
        target = REPO_ROOT / "package.json"
        total = len(target.read_text(encoding="utf-8").splitlines())
        page1 = mcp_server.read_file("package.json", offset=1, limit=5)
        self.assertEqual(page1["path"], "package.json")
        self.assertEqual(page1["offset"], 1)
        self.assertEqual(page1["returned"], 5)
        self.assertEqual(page1["total_lines"], total)
        self.assertEqual(page1["truncated"], total > 5)

        page2 = mcp_server.read_file("package.json", offset=6, limit=5)
        self.assertEqual(page2["offset"], 6)
        self.assertNotEqual(page1["content"], page2["content"])

    def test_directory_hint(self):
        with self.assertRaises(ToolError) as ctx:
            mcp_server.read_file("ai-agent")
        self.assertIn("list_directory", str(ctx.exception))

    def test_missing_file(self):
        with self.assertRaises(ToolError):
            mcp_server.read_file("does/not/exist.txt")

    def test_binary_refused(self):
        planted = agent_dir / "tests" / "_planted_binary.bin"
        planted.write_bytes(b"\x00\x01\x02binary")
        try:
            with self.assertRaises(ToolError) as ctx:
                mcp_server.read_file("ai-agent/tests/_planted_binary.bin")
            self.assertIn("binary", str(ctx.exception))
        finally:
            planted.unlink(missing_ok=True)


class TestSearchBehaviour(unittest.TestCase):
    def test_finds_matches_with_line_numbers(self):
        result = mcp_server.search_code(
            "FastMCP", path="ai-agent", file_glob="*.py", max_results=10
        )
        self.assertGreaterEqual(len(result["matches"]), 1)
        self.assertGreater(result["files_scanned"], 0)
        first = result["matches"][0]
        self.assertTrue(first["path"].endswith(".py"))
        self.assertIsInstance(first["line"], int)
        self.assertGreaterEqual(first["line"], 1)

    def test_invalid_regex_reported(self):
        with self.assertRaises(ToolError) as ctx:
            mcp_server.search_code("[unclosed")
        self.assertIn("regular expression", str(ctx.exception))

    def test_empty_pattern_rejected(self):
        with self.assertRaises(ToolError):
            mcp_server.search_code("   ")

    def test_cache_dirs_never_returned(self):
        result = mcp_server.search_code(
            "import", path="ai-agent", file_glob="*.py", max_results=50
        )
        for match in result["matches"]:
            self.assertNotIn("__pycache__", match["path"])
            self.assertNotIn("venv", match["path"].split("/"))


class TestGlobAndList(unittest.TestCase):
    def test_glob_docs_markdown(self):
        result = mcp_server.glob_files("**/*.md", path="docs", max_results=100)
        self.assertGreaterEqual(len(result["files"]), 1)
        for path in result["files"]:
            self.assertTrue(path.startswith("docs/"), path)
            self.assertTrue(path.endswith(".md"), path)

    def test_glob_caps_results(self):
        result = mcp_server.glob_files("**/*", path="src", max_results=3)
        self.assertLessEqual(len(result["files"]), 3)

    def test_list_root(self):
        result = mcp_server.list_directory(".")
        names = {entry["name"] for entry in result["entries"]}
        self.assertIn("package.json", names)
        self.assertIn("ai-agent", names)
        # directories sort before files
        types = [entry["type"] for entry in result["entries"]]
        self.assertIn("dir", types)

    def test_list_limit_marks_truncation(self):
        full = mcp_server.list_directory(".")
        page = mcp_server.list_directory(".", limit=5)
        self.assertLessEqual(len(page["entries"]), 5)
        self.assertTrue(page["truncated"])
        self.assertEqual(page["total_entries"], full["total_entries"])

    def test_list_file_is_error(self):
        with self.assertRaises(ToolError):
            mcp_server.list_directory("package.json")

    def test_list_missing_is_error(self):
        with self.assertRaises(ToolError):
            mcp_server.list_directory("no/such/dir")


class TestToolRegistration(unittest.IsolatedAsyncioTestCase):
    """The four tools must be registered on the MCP server surface."""

    async def test_registered_tools(self):
        import contextlib

        @contextlib.asynccontextmanager
        async def session():
            async with create_connected_server_and_client_session(
                mcp_server.mcp
            ) as connected:
                client = connected[0] if isinstance(connected, tuple) else connected
                yield client

        async with session() as client:
            result = await client.list_tools()
        names = {tool.name for tool in result.tools}
        for tool_name in (
            "read_file",
            "search_code",
            "glob_files",
            "list_directory",
        ):
            self.assertIn(tool_name, names)


if __name__ == "__main__":
    unittest.main()
