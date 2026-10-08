"""SQLite persistence tests for the design portfolio registry."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.intelligence.design_registry import DesignRegistry


class TestDesignRegistry(unittest.TestCase):
    def test_registry_initializes_and_round_trips_design_signatures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = DesignRegistry(Path(temp_dir) / "designs.sqlite3")
            registry.initialize()
            registry.record(
                "claim-desk",
                "fingerprint-1",
                {"hero": "data_metrics", "navigation": "workspace_sidebar"},
            )

            rows = registry.list_signatures()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project"], "claim-desk")
        self.assertEqual(rows[0]["fingerprint"], "fingerprint-1")
        self.assertEqual(rows[0]["dimensions"]["hero"], "data_metrics")

    def test_recording_same_project_updates_its_signature(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = DesignRegistry(Path(temp_dir) / "designs.sqlite3")
            registry.initialize()
            registry.record("claim-desk", "old", {"hero": "editorial_image"})
            registry.record("claim-desk", "new", {"hero": "data_metrics"})

            rows = registry.list_signatures()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["fingerprint"], "new")

    def test_list_signatures_can_exclude_a_project_without_mutating_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = DesignRegistry(Path(temp_dir) / "designs.sqlite3")
            registry.initialize()
            registry.record("one", "fp-1", {"hero": "editorial_image"})
            registry.record("two", "fp-2", {"hero": "typographic"})

            filtered = registry.list_signatures(exclude_project="one")
            all_rows = registry.list_signatures()

        self.assertEqual([row["project"] for row in filtered], ["two"])
        self.assertEqual(len(all_rows), 2)


if __name__ == "__main__":
    unittest.main()