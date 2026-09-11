import os
import sys
import unittest
from pathlib import Path

# Add ai-agent to sys.path
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from database.init_db import init_database
from agent.memory_retriever import MemoryRetriever
from config.settings import AGENT_DB_PATH

class TestMemoryRetriever(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.retriever = MemoryRetriever()

    def test_search_templates(self):
        templates = self.retriever.search_templates("ecommerce", "electronics", ["cart", "products"])
        self.assertGreater(len(templates), 0)
        self.assertEqual(templates[0]["category"], "ecommerce")

    def test_search_components(self):
        components = self.retriever.search_components("ecommerce", ["cart"], ["product"])
        self.assertGreater(len(components), 0)
        comp_names = [c["name"] for c in components]
        self.assertIn("ProductCard", comp_names)

    def test_search_backend(self):
        backend = self.retriever.search_backend("ecommerce", ["auth", "cart"])
        self.assertIsNotNone(backend)
        self.assertIn("auth", backend["modules"])

    def test_search_database_schemas(self):
        schemas = self.retriever.search_database_schemas(["products"], "electronics")
        self.assertGreater(len(schemas), 0)

if __name__ == "__main__":
    unittest.main()
