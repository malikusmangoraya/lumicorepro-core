import os
import sys
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from database.pipeline_store import PipelineStore


class TestPipelineStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-pipeline-store-")
        self.db_path = os.path.join(self.tmp, "agent_test.db")
        self.store = PipelineStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_and_retrieve_run(self):
        self.store.create_run(
            "run-1", prompt="Build a restaurant site", provider="gemini",
            language="en", region="NA", status="queued",
        )
        run = self.store.get_run("run-1")
        self.assertIsNotNone(run)
        self.assertEqual(run["status"], "queued")
        self.assertEqual(run["prompt"], "Build a restaurant site")
        self.assertEqual(run["provider"], "gemini")
        self.assertEqual(run["events_json"], [])

    def test_create_is_idempotent(self):
        self.store.create_run("run-1", prompt="one", status="queued")
        self.store.create_run("run-1", prompt="two", status="queued")
        run = self.store.get_run("run-1")
        self.assertEqual(run["prompt"], "one")

    def test_status_transitions_persist(self):
        self.store.create_run("run-1", prompt="p")
        self.store.set_status("run-1", "running", started_at=1.0)
        self.store.set_status("run-1", "done", finished_at=2.0,
                              result_json={"project_name": "proj", "score": 90})
        run = self.store.get_run("run-1")
        self.assertEqual(run["status"], "done")
        self.assertEqual(run["result_json"]["project_name"], "proj")

    def test_append_events_bounded_and_replayable(self):
        self.store.create_run("run-1", prompt="p")
        events = [{"run_id": "run-1", "type": "phase_start", "phase": f"Phase {i}"} for i in range(30)]
        self.store.append_events("run-1", events)
        self.store.append_events("run-1", [{"run_id": "run-1", "type": "complete"}])
        run = self.store.get_run("run-1")
        stored = run["events_json"]
        self.assertEqual(len(stored), 31)
        self.assertEqual(stored[-1]["type"], "complete")

    def test_list_runs_ordering_and_filter(self):
        self.store.create_run("run-1", prompt="a", status="done")
        self.store.create_run("run-2", prompt="b", status="running")
        self.store.create_run("run-3", prompt="c", status="error")
        all_runs = self.store.list_runs(limit=10)
        self.assertEqual([r["run_id"] for r in all_runs], ["run-3", "run-2", "run-1"])
        running = self.store.list_runs(status="running")
        self.assertEqual([r["run_id"] for r in running], ["run-2"])

    def test_mark_interrupted_flags_stale_running_runs(self):
        self.store.create_run("run-1", prompt="a")
        self.store.set_status("run-1", "running", started_at=100.0)
        interrupted = self.store.mark_interrupted(started_before_ts=200.0)
        self.assertEqual(interrupted, ["run-1"])
        self.assertEqual(self.store.get_run("run-1")["status"], "interrupted")
        # A run started after the threshold is untouched
        self.store.create_run("run-2", prompt="b")
        self.store.set_status("run-2", "running", started_at=300.0)
        self.assertEqual(self.store.mark_interrupted(started_before_ts=200.0), [])

    def test_prune_keeps_newest(self):
        for i in range(8):
            self.store.create_run(f"run-{i}", prompt=str(i), status="done")
        removed = self.store.prune(keep=3)
        self.assertEqual(removed, 5)
        remaining = self.store.list_runs(limit=10)
        self.assertEqual(len(remaining), 3)
        self.assertEqual({r["run_id"] for r in remaining}, {"run-7", "run-6", "run-5"})

    def test_thread_safe_writes(self):
        errors = []

        def writer(run_id):
            try:
                self.store.create_run(run_id, prompt="p")
                self.store.append_events(run_id, [{"type": "e", "run_id": run_id}] * 5)
                self.store.set_status(run_id, "done")
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(f"run-{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        for i in range(10):
            run = self.store.get_run(f"run-{i}")
            self.assertEqual(run["status"], "done")
            self.assertEqual(len(run["events_json"]), 5)


if __name__ == "__main__":
    unittest.main()