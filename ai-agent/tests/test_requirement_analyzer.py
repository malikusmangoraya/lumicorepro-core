import sys
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.requirement_analyzer import RequirementAnalyzer

class TestRequirementAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RequirementAnalyzer()

    def test_ecommerce_prompt_analysis(self):
        prompt = "Create a modern electronics e-commerce store with 20 categories, cart, and authentication."
        spec = self.analyzer.analyze(prompt)
        self.assertEqual(spec["website_type"], "ecommerce")
        self.assertEqual(spec["industry"], "electronics")
        self.assertIn("authentication", spec["features"])
        self.assertIn("cart", spec["features"])
        self.assertFalse(spec["is_ambiguous"])

    def test_vague_prompt_detection(self):
        prompt = "make app"
        spec = self.analyzer.analyze(prompt)
        self.assertTrue(spec["is_ambiguous"])
        self.assertGreater(len(spec["clarifying_options"]), 0)

    def test_conflicting_prompt_detection(self):
        prompt = "Build a hospital clinic blog store with shopping cart"
        spec = self.analyzer.analyze(prompt)
        self.assertTrue(spec["is_ambiguous"])

if __name__ == "__main__":
    unittest.main()
