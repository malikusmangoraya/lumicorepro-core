"""Tests — native_binary_repair: a Windows policy block must not brick delivery.

On 2026-10-27 a fresh `npm install` wrote rollup's native binary at a hash the
machine's Application Control policy had never seen, so `npm run build` died with
`ERR_DLOPEN_FAILED` on generated code that was never the problem. The repair
restores an identical-version binary that already loads on this machine, retries the
build once, and records exactly what it swapped — it never downloads anything and
never hides the substitution.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import agent.native_binary_repair as nbr

BLOCKED_PATH = ("D:\\work\\site\\frontend\\node_modules\\@rollup\\rollup-win32-x64-msvc"
                "\\rollup.win32-x64-msvc.node")
STDERR = (
    "Error: An Application Control policy has blocked this file.\n"
    "\n"
    "\\\\?\\D:\\work\\site\\frontend\\node_modules\\@rollup\\rollup-win32-x64-msvc"
    "\\rollup.win32-x64-msvc.node\n"
    "    at Object..node (node:internal/modules/cjs/loader:2029:18)\n"
    "  code: 'ERR_DLOPEN_FAILED'\n"
)


def _native(root: Path, version: str, payload: bytes, rel: str) -> Path:
    pkg = root / "node_modules" / Path(rel).parent
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "package.json").write_text(json.dumps({"name": Path(rel).parent.name,
                                                  "version": version}), encoding="utf-8")
    binary = root / "node_modules" / rel
    binary.write_bytes(payload)
    return binary


class ExtractTests(unittest.TestCase):
    def test_the_blocked_path_is_recovered_from_the_policy_error(self):
        self.assertEqual(nbr.blocked_binary(STDERR).replace("\\", "/"),
                         BLOCKED_PATH.replace("\\", "/"))

    def test_an_ordinary_build_error_is_not_a_policy_block(self):
        self.assertEqual(nbr.blocked_binary("SyntaxError: missing ) after argument list"), "")

    def test_a_dlopen_failure_without_a_path_is_not_guessed_at(self):
        self.assertEqual(nbr.blocked_binary("ERR_DLOPEN_FAILED with no file named"), "")


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.rel = "@rollup/rollup-win32-x64-msvc/rollup.win32-x64-msvc.node"
        self.frontend = self.tmp / "site" / "frontend"
        self.frontend.mkdir(parents=True)
        self.blocked = _native(self.frontend, "4.65.1", b"blocked-by-policy", self.rel)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _report(self, version, payload, project="other"):
        return _native(self.tmp / "generated-projects" / project / "frontend",
                       version, payload, self.rel)

    def test_the_exact_version_is_preferred_over_a_neighbour(self):
        near = self._report("4.65.0", b"same-minor")
        exact = self._report("4.65.1", b"exact-match", project="exact")
        found = [path.resolve() for path, _ in nbr.candidates(self.blocked, self.tmp, self.frontend)]
        self.assertEqual(found[0], exact.resolve())
        self.assertIn(near.resolve(), found)

    def test_a_different_minor_is_never_used(self):
        self._report("5.0.0", b"major-drift")
        self._report("4.64.9", b"older-minor")
        self.assertEqual(nbr.candidates(self.blocked, self.tmp, self.frontend), [])

    def test_a_candidate_is_skipped_when_its_own_binary_is_absent(self):
        pkg = self.tmp / "generated-projects" / "empty" / "frontend" / "node_modules" / "@rollup" / "rollup-win32-x64-msvc"
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text(json.dumps({"version": "4.65.1"}), encoding="utf-8")
        self.assertEqual(nbr.candidates(self.blocked, self.tmp, self.frontend), [])

    def test_the_project_being_built_never_supplies_its_own_blocked_file(self):
        found = nbr.candidates(self.blocked, self.tmp, self.frontend)
        self.assertNotIn(self.blocked, [p for p, _ in found])


def _policy_stderr(path) -> str:
    """The refusal Windows writes, with the blocked file named the way it names it."""
    return ("Error: An Application Control policy has blocked this file.\n\n"
            f"\\\\?\\{str(path).replace('/', chr(92))}\n"
            "    at Object..node (node:internal/modules/cjs/loader:2029:18)\n"
            "  code: 'ERR_DLOPEN_FAILED'\n")


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.rel = "@rollup/rollup-win32-x64-msvc/rollup.win32-x64-msvc.node"
        self.frontend = self.tmp / "site" / "frontend"
        self.frontend.mkdir(parents=True)
        self.blocked = _native(self.frontend, "4.65.1", b"blocked-by-policy", self.rel)
        self.source = _native(self.tmp / "generated-projects" / "other" / "frontend",
                              "4.65.1", b"known-good", self.rel)
        self.stderr = _policy_stderr(self.blocked)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_blocked_binary_is_replaced_by_the_one_that_already_loads(self):
        evidence = nbr.repair(self.frontend, self.stderr, repo_root=self.tmp)
        self.assertTrue(evidence["repaired"], evidence)
        self.assertEqual(self.blocked.read_bytes(), b"known-good")
        self.assertEqual(evidence["source_version"], "4.65.1")

    def test_the_evidence_names_both_versions_so_the_swap_is_auditable(self):
        evidence = nbr.repair(self.frontend, self.stderr, repo_root=self.tmp)
        self.assertEqual((evidence["blocked_version"], evidence["source_version"]),
                         ("4.65.1", "4.65.1"))
        self.assertIn("Application Control", evidence["message"])

    def test_a_path_outside_this_project_is_never_written_to(self):
        elsewhere = self.tmp.parent / "somewhere-else" / "frontend" / "node_modules" / self.rel
        evidence = nbr.repair(self.frontend, _policy_stderr(elsewhere), repo_root=self.tmp)
        self.assertFalse(evidence["repaired"])
        self.assertEqual(evidence["status"], "not-in-project")
        self.assertEqual(self.blocked.read_bytes(), b"blocked-by-policy")

    def test_with_no_compatible_copy_the_block_is_named_instead_of_guessed_at(self):
        shutil.rmtree(self.tmp / "generated-projects")
        evidence = nbr.repair(self.frontend, self.stderr, repo_root=self.tmp)
        self.assertFalse(evidence["repaired"])
        self.assertEqual(evidence["status"], "no-compatible-copy")
        self.assertIn("Windows Security", evidence["message"])

    def test_an_unrelated_failure_is_not_reported_as_a_policy_block(self):
        evidence = nbr.repair(self.frontend, "vite: Rollup failed to resolve import", repo_root=self.tmp)
        self.assertFalse(evidence["repaired"])
        self.assertEqual(evidence["status"], "not-a-policy-block")

    def test_a_refusal_that_names_no_file_is_never_guessed_at(self):
        evidence = nbr.repair(self.frontend, "ERR_DLOPEN_FAILED", repo_root=self.tmp)
        self.assertFalse(evidence["repaired"])
        self.assertEqual(evidence["status"], "policy-block-without-path")

    def test_a_source_already_tried_is_skipped_so_the_retry_uses_the_next_copy(self):
        second = self._report_copy("4.65.0", b"second-choice", project="third")
        evidence = nbr.repair(self.frontend, self.stderr, repo_root=self.tmp, exclude=(self.source,))
        self.assertTrue(evidence["repaired"], evidence)
        self.assertEqual(self.blocked.read_bytes(), b"second-choice")
        self.assertEqual(Path(evidence["source"]).resolve(), second.resolve())

    def _report_copy(self, version, payload, project):
        return _native(self.tmp / "generated-projects" / project / "frontend",
                       version, payload, self.rel)


class BlockedMarkerTests(unittest.TestCase):
    def test_both_spellings_of_the_same_block_are_recognised(self):
        self.assertTrue(nbr.is_policy_block("... ERR_DLOPEN_FAILED"))
        self.assertTrue(nbr.is_policy_block("An Application Control policy has blocked this file"))
        self.assertFalse(nbr.is_policy_block("out of memory"))


if __name__ == "__main__":
    unittest.main()
