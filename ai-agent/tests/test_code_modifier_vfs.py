import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.code_modifier import CodeModifier, build_diff_prompt, strip_diff_fence, SecurityViolationError


class StubProvider:
    """Emits a fixed git-style unified diff for the requested task."""

    def __init__(self, diff_text):
        self.diff_text = diff_text

    def generate_code(self, prompt, context_files=None):
        self.last_prompt = prompt
        return self.diff_text


SIMPLE_DIFF = (
    "diff --git a/frontend/src/Home.jsx b/frontend/src/Home.jsx\n"
    "index 1111111..2222222 100644\n"
    "--- a/frontend/src/Home.jsx\n"
    "+++ b/frontend/src/Home.jsx\n"
    "@@ -1,4 +1,4 @@\n"
    " import React from 'react';\n"
    "-export default function Home() {\n"
    "+export default function Home({ title = 'X' }) {\n"
    "   return null;\n"
    " }\n"
)


class TestCodeModifierVFS(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="lumicore-mod-vfs-")
        self.project_dir = os.path.join(self._tmp, "site")
        src = os.path.join(self.project_dir, "frontend", "src")
        os.makedirs(src)
        with open(os.path.join(src, "Home.jsx"), "w", encoding="utf-8") as f:
            f.write("import React from 'react';\nexport default function Home() {\n  return null;\n}\n")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_build_prompt_includes_tree_and_task(self):
        prompt = build_diff_prompt("make it red", "PROJECT TREE:\n{}")
        self.assertIn("Unified Diff", prompt)
        self.assertIn("make it red", prompt)
        self.assertIn("PROJECT TREE:", prompt)
        self.assertIn("diff --git", prompt)

    def test_strip_diff_fence(self):
        fenced = "```\n" + SIMPLE_DIFF + "\n```"
        cleaned = strip_diff_fence(fenced)
        self.assertTrue(cleaned.startswith("diff --git"))
        self.assertNotIn("```", cleaned)

    def test_apply_ai_diff_batch_writes_files(self):
        mod = CodeModifier(ai_provider=StubProvider(SIMPLE_DIFF))
        report = mod.apply_ai_diff_batch(self.project_dir, "add default title prop")
        self.assertEqual(report["status"], "applied")
        self.assertIn("frontend/src/Home.jsx", report["files_changed"])
        with open(os.path.join(self.project_dir, "frontend", "src", "Home.jsx"), "r", encoding="utf-8") as f:
            self.assertIn("title = 'X'", f.read())

    def test_apply_ai_diff_batch_rejects_security(self):
        bad = (
            "diff --git a/frontend/src/Home.jsx b/frontend/src/Home.jsx\n"
            "--- a/frontend/src/Home.jsx\n"
            "+++ b/frontend/src/Home.jsx\n"
            "@@ -1,1 +1,2 @@\n"
            " import React from 'react';\n"
            "+eval('pwn')\n"
        )
        mod = CodeModifier(ai_provider=StubProvider(bad))
        with self.assertRaises(SecurityViolationError):
            mod.apply_ai_diff_batch(self.project_dir, "add code")

    def test_fix_from_errors_feeds_blob(self):
        diff = (
            "diff --git a/frontend/src/Home.jsx b/frontend/src/Home.jsx\n"
            "--- a/frontend/src/Home.jsx\n"
            "+++ b/frontend/src/Home.jsx\n"
            "@@ -1,1 +1,1 @@\n"
            "-import React from 'react';\n"
            "+import { useState } from 'react';\n"
        )
        provider = StubProvider(diff)
        mod = CodeModifier(ai_provider=provider)
        report = mod.fix_from_errors(
            self.project_dir,
            "error  Cannot find name 'useState'  Home.jsx:2:3",
            round_idx=0,
        )
        self.assertEqual(report["status"], "applied")
        self.assertIn("ERROR LOG (attempt 1)", provider.last_prompt)
        self.assertIn("Cannot find name 'useState'", provider.last_prompt)


if __name__ == "__main__":
    unittest.main()