import sys
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from utils.file_manager import FileManager, PathTraversalError


class TestFileManagerSecurity(unittest.TestCase):
    def test_traversal_is_rejected_without_allowed_base(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / ".." / "outside.txt"
            with self.assertRaises(PathTraversalError):
                FileManager.resolve_safe_path(str(target))


if __name__ == "__main__":
    unittest.main()