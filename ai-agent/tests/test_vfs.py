import os
import sys
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.vfs import ProjectVFS, UnifiedDiffError


def _diff(old_file, new_file, body, old_path=None, new_path=None):
    if old_path is None:
        old_path = new_file
    if new_path is None:
        new_path = new_file
    return (
        f"diff --git a/{old_path} b/{new_path}\n"
        f"index 0000000..0000000 100644\n"
        f"--- a/{old_path}\n"
        f"+++ b/{new_path}\n"
        f"{body}\n"
    )


class TestProjectVFS(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="lumicore-vfs-test-")
        self.project_dir = os.path.join(self._tmp, "site")
        src = os.path.join(self.project_dir, "frontend", "src")
        os.makedirs(src)
        with open(os.path.join(src, "Home.jsx"), "w", encoding="utf-8") as f:
            f.write("export default function Home() {\n  return (\n    <h1>Hi</h1>\n  );\n}\n")
        with open(os.path.join(self.project_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "site", "scripts": {}}\n')

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _vfs(self):
        return ProjectVFS(self.project_dir).load()

    def test_load_and_tree(self):
        vfs = self._vfs()
        self.assertIn("frontend/src/Home.jsx", vfs.files())
        tree = vfs.tree()
        src_node = tree["dirs"]["frontend"]["dirs"]["src"]
        self.assertIn("Home.jsx", src_node["files"])

    def test_apply_single_hunk(self):
        vfs = self._vfs()
        home = vfs.read("frontend/src/Home.jsx")
        diff = _diff(
            "frontend/src/Home.jsx",
            "frontend/src/Home.jsx",
            "@@ -1,5 +1,6 @@\n"
            " export default function Home() {\n"
            "   return (\n"
            '-    <h1>Hi</h1>\n'
            '+    <h1>Hello World</h1>\n'
            "   );\n"
            " }\n",
        )
        report = vfs.apply_unified_diff(diff)
        self.assertIn("frontend/src/Home.jsx", report["applied_files"])
        updated = vfs.read("frontend/src/Home.jsx")
        self.assertIn("<h1>Hello World</h1>", updated)
        self.assertNotIn("<h1>Hi</h1>", updated)

    def test_apply_multi_hunk_with_delta(self):
        vfs = self._vfs()
        content = "".join(f"line{i}\n" for i in range(20))
        vfs._files["multi.js"] = content
        diff = _diff(
            "multi.js",
            "multi.js",
            "@@ -1,2 +1,3 @@\n"
            " line0\n"
            " line1\n"
            "+INSERTED\n"
            "@@ -6,3 +7,3 @@\n"
            " line5\n"
            "-line6\n"
            "+SIX\n"
            " line7\n",
        )
        report = vfs.apply_unified_diff(diff)
        updated = vfs.read("multi.js")
        lines = updated.splitlines()
        self.assertIn("INSERTED", lines)
        self.assertEqual(lines[2], "INSERTED")
        self.assertEqual(lines[7], "SIX")
        self.assertNotIn("line6", lines)

    def test_new_file_hunk_on_existing_target_replaces_not_appends(self):
        # A model emitting a `/dev/null` (new-file) diff for a file that already
        # exists intends a full rewrite. Append would duplicate the component
        # (the CookieConsent corruption bug) — must REPLACE wholesale.
        vfs = self._vfs()
        diff = (
            "diff --git a/frontend/src/Home.jsx b/frontend/src/Home.jsx\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/frontend/src/Home.jsx\n"
            "@@ -0,0 +3 @@\n"
            "+export default function Home() {\n"
            "+  return <section>Replacement</section>;\n"
            "+}\n"
        )
        vfs.apply_unified_diff(diff)
        updated = vfs.read("frontend/src/Home.jsx")
        self.assertIn("Replacement", updated)
        self.assertEqual(updated.count("export default function Home"), 1)
        self.assertNotIn("<h1>Hi</h1>", updated)
        self.assertEqual(len([l for l in updated.splitlines() if l.strip()]), 3)

    def test_all_add_zero_hunk_on_existing_target_rewrites(self):
        # Weaker models reuse the new-file `@@ -0,0 +N @@` all-add shape under a
        # plain "modified" header — same rewrite intent, never append.
        vfs = self._vfs()
        diff = _diff(
            "frontend/src/Home.jsx",
            "frontend/src/Home.jsx",
            "@@ -0,0 +2 @@\n"
            "+export default function Home() {\n"
            "+  return <main>V2</main>;\n"
            "+}\n",
        )
        vfs.apply_unified_diff(diff)
        updated = vfs.read("frontend/src/Home.jsx")
        self.assertIn("V2", updated)
        self.assertEqual(updated.count("export default function Home"), 1)
        self.assertNotIn("<h1>Hi</h1>", updated)

    def test_new_file_creation(self):
        vfs = self._vfs()
        diff = (
            "diff --git a/README.md b/README.md\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/README.md\n"
            "@@ -0,0 +2 @@\n"
            "+# Generated\n"
            "+Second line\n"
        )
        report = vfs.apply_unified_diff(diff)
        self.assertIn("README.md", report["applied_files"])
        self.assertEqual("".join(vfs.read("README.md").splitlines()), "# GeneratedSecond line")

    def test_reject_path_traversal(self):
        vfs = self._vfs()
        diff = _diff(
            "../escape.js",
            "../escape.js",
            "@@ -0,0 +1 @@\n"
            "+pwned\n",
        )
        report = vfs.apply_unified_diff(diff)
        with self.assertRaises(UnifiedDiffError):
            vfs.persist()

    def test_persist_only_changed(self):
        vfs = self._vfs()
        diff = _diff(
            "frontend/src/Home.jsx",
            "frontend/src/Home.jsx",
            "@@ -3,1 +3,1 @@\n"
            "-    <h1>Hi</h1>\n"
            "+    <h1>PERSISTED</h1>\n",
        )
        vfs.apply_unified_diff(diff)
        written = vfs.persist()
        self.assertEqual(written, ["frontend/src/Home.jsx"])
        with open(os.path.join(self.project_dir, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
            self.assertIn("PERSISTED", f.read())

    def test_security_violations_on_added_lines(self):
        violations = ProjectVFS.security_violations(
            "+++ b/x.js\n+import os\n+eval('danger')\n+os.system('rm -rf /')\n"
        )
        self.assertGreaterEqual(len(violations), 1)


if __name__ == "__main__":
    unittest.main()