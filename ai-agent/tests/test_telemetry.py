import os
import sys
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from utils.telemetry import Telemetry


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-telemetry-")
        self.path = os.path.join(self.tmp, "telemetry.jsonl")
        self.t = Telemetry(path=self.path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_record_writes_json_lines(self):
        self.t.record("run-1", "run_start", provider="gemini")
        self.t.record("run-1", "run_done", status="done", duration_secs=3.2, quality_score=90)
        lines = open(self.path, encoding="utf-8").read().strip().splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        self.assertEqual(first["event"], "run_start")
        self.assertEqual(first["run_id"], "run-1")

    def test_disabled_writes_nothing(self):
        t = Telemetry(path=self.path, enabled=False)
        t.record("run-1", "run_start")
        self.assertFalse(os.path.exists(self.path))

    def test_summary_aggregates_counts_and_duration(self):
        self.t.record("r1", "run_start", phase="Phase 1 - Market Analysis")
        self.t.record("r1", "run_done", status="done", duration_secs=2.0)
        self.t.record("r2", "run_error", status="error", error="boom", duration_secs=4.0)
        s = self.t.summary()
        self.assertEqual(s["events"], 3)
        self.assertEqual(s["by_status"]["done"], 1)
        self.assertEqual(s["by_status"]["error"], 1)
        self.assertEqual(s["error_count"], 1)
        self.assertAlmostEqual(s["avg_run_duration_secs"], 3.0)

    def test_summary_since_ts_filters(self):
        self.t.record("r1", "run_start")
        import time
        self.t.record("r2", "run_start")
        older = self.t.summary(since_ts=time.time() - 1)
        # both records are after the threshold window start if produced within 1s
        self.assertGreaterEqual(older["events"], 2)

    def test_thread_safe_concurrent_records(self):
        errors = []

        def writer(i):
            try:
                t = Telemetry(path=self.path)
                for _ in range(20):
                    t.record(f"run-{i}", "phase_done", phase=i)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        n = sum(1 for _ in open(self.path, encoding="utf-8") if _.strip())
        self.assertEqual(n, 100)

    def test_rotation_full(self):
        # Write enough to exceed the rotation size by patching the threshold
        t = Telemetry(path=self.path)
        import utils.telemetry as tel
        old = tel._MAX_BYTES
        tel._MAX_BYTES = 512
        try:
            for i in range(400):
                t.record("r", "run_start", pad="x" * 4)
        finally:
            tel._MAX_BYTES = old
        # After exceeding the size at least once, a rotation file should exist
        self.assertTrue(os.path.exists(self.path + ".1"))


if __name__ == "__main__":
    unittest.main()