import sys
import os
import shutil
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.validator import ProjectValidator
from utils.file_manager import FileManager

class TestProjectValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ProjectValidator()
        self.test_project_dir = agent_dir / "scratch_test_project"
        os.makedirs(self.test_project_dir / "frontend", exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_project_dir):
            shutil.rmtree(self.test_project_dir)

    def test_broken_project_flagged(self):
        # Intentionally missing App.jsx and backend
        FileManager.write_file(str(self.test_project_dir / "frontend" / "package.json"), '{"name": "test"}')
        report = self.validator.validate_project(str(self.test_project_dir))

        self.assertFalse(report["valid"])
        self.assertGreater(len(report["errors"]), 0)
        self.assertIn("Frontend missing required file: src/App.jsx", report["errors"][0])

if __name__ == "__main__":
    unittest.main()
