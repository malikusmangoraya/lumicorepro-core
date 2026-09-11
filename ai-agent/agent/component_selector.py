from typing import Dict, Any, List
from utils.logger import agent_logger
from utils.helpers import extract_keywords
from .memory_retriever import MemoryRetriever

class ComponentSelector:
    """Selects matching reusable React components from local component library."""

    def __init__(self, memory_retriever: MemoryRetriever):
        self.retriever = memory_retriever

    def select_components(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select all components matching required features and tags."""
        agent_logger.info("Searching local component library...")
        category = spec.get("website_type", "ecommerce")
        features = spec.get("features", [])
        keywords = extract_keywords(spec.get("original_prompt", ""))

        matched_components = self.retriever.search_components(category, features, keywords)
        
        # Deduplicate components by name
        unique_components = {}
        for comp in matched_components:
            name = comp["name"]
            if name not in unique_components or comp.get("score", 0) > unique_components[name].get("score", 0):
                unique_components[name] = comp

        selected = list(unique_components.values())
        for comp in selected:
            self.retriever.bump_usage("component", comp["name"])
        agent_logger.info(f"Selected {len(selected)} local components: {[c['name'] for c in selected]}")
        return selected

    def select_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """Select components by exact name match (for trending feature injection)."""
        if not names:
            return []
        all_components = self.retriever.search_components("", [], [])
        name_set = set(names)
        matched = [c for c in all_components if c.get("name") in name_set]
        for comp in matched:
            self.retriever.bump_usage("component", comp["name"])
        agent_logger.info(f"Selected {len(matched)} trending-linked components: {[c['name'] for c in matched]}")
        return matched
